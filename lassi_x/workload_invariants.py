"""Independent numerical checks for the native workload reference profiles."""

from __future__ import annotations

import itertools
from typing import Any

import numpy as np


def cfd_step(inputs: dict[str, Any]) -> Any:
    """Vectorized Euler flux and RK equations, independent of the C++ traversal."""
    old = inputs["state"].astype(np.float64)
    areas = inputs["areas"].astype(np.float64)
    neighbors, normals = inputs["neighbors"], inputs["normals"].astype(np.float64)

    def physical(state: Any) -> tuple[Any, Any, Any]:
        velocity = state[1:4] / state[0]
        pressure = 0.4 * (state[4] - 0.5 * state[0] * np.square(velocity).sum(axis=0))
        speed = np.linalg.norm(velocity, axis=0)
        sound = np.sqrt(1.4 * pressure / state[0])
        flux = np.empty((3, 5, state.shape[-1]))
        flux[:, 0] = state[1:4]
        flux[:, 1:4] = velocity[:, None] * state[None, 1:4]
        for axis in range(3):
            flux[axis, axis + 1] += pressure
        flux[:, 4] = velocity * (state[4] + pressure)
        return flux, speed, sound

    far = np.array([1.4, 1.68, 0, 0, 3.508])[:, None]
    far_flux, _, _ = physical(far)
    _, speed, sound = physical(old)
    step = 0.5 / (np.sqrt(areas) * (speed + sound))
    current = old.copy()
    for stage in range(3):
        flux, speed, sound = physical(current)
        accumulated = np.zeros_like(current)
        for face in range(4):
            nb = neighbors[face]
            interior = nb >= 0
            index = np.maximum(nb, 0)
            other_flux = np.where(interior[None, None], flux[:, :, index], far_flux[:, :, None, 0])
            normal = normals[:, face]
            centered = 0.5 * (normal[:, None] * (flux + other_flux)).sum(axis=0)
            wall = nb == -1
            pressure = 0.4 * (current[4] - 0.5 * np.square(current[1:4]).sum(axis=0) / current[0])
            centered[:, wall] = 0
            centered[1:4, wall] = normal[:, wall] * pressure[wall]
            accumulated += centered
            factor = (
                -0.1
                * np.linalg.norm(normal, axis=0)
                * (speed + speed[index] + sound + sound[index])
            )
            accumulated[:, interior] += (factor * (current - current[:, index]))[:, interior]
        current = old + (step / (4 - stage)) * accumulated
    return current


def check_native(kind: str, inputs: dict[str, Any], outputs: dict[str, Any]) -> dict[str, Any]:
    """Raise on scientific failure; return bounded metrics for the case report."""
    metrics: dict[str, Any] = {}

    def require(condition: bool, label: str) -> None:
        if not condition:
            raise ValueError(f"{kind}: independent check failed: {label}")
        metrics[label] = True

    def close(
        actual: Any, expected: Any, label: str, rtol: float = 1e-6, atol: float = 1e-7
    ) -> None:
        require(bool(np.allclose(actual, expected, rtol=rtol, atol=atol)), label)

    require(all(np.isfinite(v).all() for v in outputs.values()), "finite_outputs")
    if kind == "npb-cg":
        solution, rhs = outputs["solution"], inputs["rhs"]
        rows = inputs["rows"] - 1
        product = np.add.reduceat(inputs["values"] * solution[inputs["columns"] - 1], rows[:-1])
        residual = float(np.linalg.norm(product - rhs))
        relative = residual / float(np.linalg.norm(rhs))
        metrics["relative_linear_system_residual"] = relative
        require(relative < 1e-8, "sparse_system_solution")
        close(outputs["residual"], residual, "reported_residual", atol=1e-10)
    elif kind == "npb-mg":
        solution, rhs = outputs["solution"], inputs["rhs"]
        padded = np.pad(solution, 1, mode="wrap")
        product = -8.0 / 3.0 * solution
        for offsets in itertools.product((-1, 0, 1), repeat=3):
            nonzero = sum(v != 0 for v in offsets)
            if nonzero < 2:
                continue
            slices = tuple(
                slice(1 + v, 1 + v + n) for v, n in zip(offsets, solution.shape, strict=True)
            )
            product += padded[slices] / (6 if nonzero == 2 else 12)
        relative = float(np.linalg.norm(product - rhs) / np.linalg.norm(rhs))
        metrics["residual_reduction_ratio"] = relative
        require(relative < 0.8, "multigrid_reduces_residual")
    elif kind == "npb-ft":
        field = inputs["field"][..., 0] + 1j * inputs["field"][..., 1]
        spectrum = outputs["spectrum"][..., 0] + 1j * outputs["spectrum"][..., 1]
        close(
            np.sum(np.abs(spectrum) ** 2),
            field.size * np.sum(np.abs(field) ** 2),
            "parseval",
            rtol=1e-10,
        )
        close(spectrum[0, 0, 0], field.sum(), "dc_coefficient", rtol=1e-9, atol=1e-7)
        if field.size <= 2**20:
            close(
                spectrum, np.fft.ifftn(field) * field.size, "independent_fft", rtol=1e-10, atol=1e-8
            )
    elif kind == "lavamd":
        force, charge = outputs["forces"], inputs["charges"]
        require(bool((force[:, 0] > 0).all()), "positive_interaction_potential")
        weighted = force[:, 1:] * charge[:, None]
        require(
            float(np.linalg.norm(weighted.sum(axis=0))) < 1e-10 * float(np.abs(weighted).sum()),
            "balanced_pair_forces",
        )
    elif kind == "myocyte":
        trajectory = outputs["trajectory"]
        close(trajectory[:, 0], inputs["initial"], "ode_initial_state", rtol=0, atol=0)
        require(bool((trajectory[:, :, 31:38] > 0).all()), "positive_ion_concentrations")
        require(not np.array_equal(trajectory[:, 0], trajectory[:, -1]), "nontrivial_ode_evolution")
    elif kind == "cfd":
        updated = outputs["updated"]
        require(bool((updated[0] > 0).all()), "positive_density")
        pressure = 0.4 * (updated[4] - 0.5 * np.square(updated[1:4]).sum(axis=0) / updated[0])
        require(bool((pressure > 0).all()), "positive_pressure")
        close(inputs["normals"].sum(axis=1), 0, "closed_tetrahedral_faces", atol=1e-7)
        require(
            bool(
                (inputs["neighbors"] == -1).any()
                and (inputs["neighbors"] == -2).any()
                and (inputs["neighbors"] >= 0).any()
            ),
            "interior_wall_and_farfield_coverage",
        )
        close(updated, cfd_step(inputs), "independent_euler_rk_update", rtol=2e-5, atol=2e-6)
    elif kind == "mutual-information":
        first = np.floor((inputs["image1"].astype(float) + 0.5) * 255 / 256).astype(np.int64)
        second = np.floor((inputs["image2"].astype(float) + 0.5) * 255 / 256).astype(np.int64)
        histogram = np.bincount((first + 255 * second).ravel(), minlength=255**2).reshape(255, 255)
        close(outputs["histogram"], histogram, "independent_joint_histogram", rtol=0, atol=0)
        probability = histogram / histogram.sum()

        def entropy(p: Any) -> float:
            positive = p[p > 0]
            return float(-np.sum(positive * np.log2(positive)))

        joint, h1, h2 = (
            entropy(probability),
            entropy(probability.sum(axis=0)),
            entropy(probability.sum(axis=1)),
        )
        close(
            outputs["statistics"],
            [h1 + h2 - joint, joint, h1, h2],
            "independent_entropies",
            rtol=1e-10,
            atol=1e-10,
        )
    elif kind == "randomized-svd":
        singular = outputs["singular_values"]
        approximation, matrix = outputs["reconstruction"], inputs["matrix"]
        require(
            bool((singular >= 0).all() and (np.diff(singular) <= 0).all()),
            "ordered_nonnegative_singular_values",
        )
        relative = float(np.linalg.norm(matrix - approximation) / np.linalg.norm(matrix))
        metrics["relative_reconstruction_error"] = relative
        require(relative < 0.05, "low_rank_reconstruction")
        close(
            np.linalg.norm(approximation),
            np.linalg.norm(singular),
            "factor_norm_consistency",
            rtol=1e-5,
        )
        if min(matrix.shape) <= 64:
            exact = np.linalg.svd(matrix, compute_uv=False)
            optimum = float(np.linalg.norm(exact[len(singular) :]))
            require(
                float(np.linalg.norm(matrix - approximation)) <= 1.5 * optimum,
                "near_optimal_rank_k_error",
            )
    elif kind == "mri-gridding":
        samples, side = inputs["samples"], int(inputs["side"])
        coordinates = samples[:, 2:5].astype(np.float64)
        base = np.floor(coordinates).astype(np.int64)
        expected = np.zeros(side**3, dtype=np.float64)
        for offset in itertools.product((-1, 0, 1, 2), repeat=3):
            cell = base + offset
            distance = np.square(cell - coordinates).sum(axis=1)
            mask = (distance < 2.25) & (cell >= 0).all(axis=1) & (cell < side).all(axis=1)
            chosen = cell[mask]
            index = chosen[:, 0] + side * chosen[:, 1] + side**2 * chosen[:, 2]
            expected += np.bincount(index, minlength=side**3)
        close(outputs["density"], expected, "independent_scatter_counts", rtol=0, atol=0)
        require(bool((np.abs(outputs["grid"][expected > 0]) > 0).any()), "nonzero_complex_grid")
    else:
        raise ValueError(f"No independent checks for native profile {kind}")
    return metrics
