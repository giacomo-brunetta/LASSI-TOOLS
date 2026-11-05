"""Seeded, domain-valid application inputs for the ten native suite adapters."""

from __future__ import annotations

import hashlib
import itertools
from functools import lru_cache
from typing import Any

import numpy as np

FIELDS = {
    "lavamd": ["positions", "charges"],
    "myocyte": ["initial"],
    "dwt2d": ["image"],
    "cfd": ["state", "areas", "neighbors", "normals"],
    "mutual-information": ["image1", "image2"],
    "randomized-svd": ["matrix"],
    "mri-gridding": ["samples"],
    "npb-cg": ["rows", "columns", "values", "rhs"],
    "npb-mg": ["rhs"],
    "npb-ft": ["field"],
}


@lru_cache(maxsize=2)
def tetrahedral_mesh(side: int) -> tuple[Any, Any, Any]:
    """Conforming tetrahedra with Rodinia's internal inward-normal convention."""
    origins = np.indices((side, side, side)).reshape(3, -1).T
    tets = []
    for axes in itertools.permutations(range(3)):
        offsets = np.zeros((4, 3), dtype=np.int64)
        for j, axis in enumerate(axes):
            offsets[j + 1] = offsets[j]
            offsets[j + 1, axis] += 1
        tets.append(origins[:, None, :] + offsets)
    coordinates = np.concatenate(tets, axis=0)
    n = len(coordinates)
    vertices = (coordinates[:, :, 0] * (side + 1) + coordinates[:, :, 1]) * (
        side + 1
    ) + coordinates[:, :, 2]
    faces = np.array([[j for j in range(4) if j != i] for i in range(4)])
    face_vertices = np.sort(vertices[:, faces], axis=2).reshape(-1, 3)
    _, inverse, counts = np.unique(face_vertices, axis=0, return_inverse=True, return_counts=True)
    if not np.all((counts == 1) | (counts == 2)):
        raise ValueError("Nonmanifold synthetic tetrahedral mesh")
    order = np.argsort(inverse)
    starts = np.cumsum(counts) - counts
    first = order[starts[counts == 2]]
    second = order[starts[counts == 2] + 1]
    neighbor = np.full(n * 4, -2, dtype=np.int32)
    neighbor[first] = second // 4
    neighbor[second] = first // 4
    points = coordinates[:, faces, :].astype(np.float64)
    normals = np.cross(points[:, :, 1] - points[:, :, 0], points[:, :, 2] - points[:, :, 0]) * 0.5
    centers = coordinates.mean(axis=1)
    outward = points.mean(axis=2) - centers[:, None, :]
    normals *= np.where((normals * outward).sum(axis=2) >= 0, 1, -1)[:, :, None]
    # Rodinia's reader negates the file face normals before compute_flux.
    # Use slip walls on transverse channel faces, far field at x inlet/outlet.
    boundary = neighbor.reshape(n, 4) < 0
    walls = boundary & (normals[:, :, 0] == 0)
    neighbor.reshape(n, 4)[walls] = -1
    normals = -normals
    return (
        np.full(n, 1.0 / 6.0, dtype=np.float32),
        neighbor.reshape(n, 4).T,
        normals.transpose(2, 1, 0).astype(np.float32),
    )


def random_inputs(kind: str, arrays: dict[str, Any], seed: int) -> dict[str, Any]:
    stream = int.from_bytes(hashlib.sha256(kind.encode()).digest()[:4], "little")
    rng = np.random.default_rng(np.random.SeedSequence([seed, stream]))
    result = dict(arrays)
    if kind == "lavamd":
        position = np.empty_like(arrays["positions"])
        position[:, 1:] = rng.uniform(-0.5, 0.5, size=position[:, 1:].shape)
        position[:, 0] = np.square(position[:, 1:]).sum(axis=1)
        result["positions"] = position
        result["charges"] = rng.uniform(0.25, 2.0, size=arrays["charges"].shape)
    elif kind == "myocyte":
        result["initial"] = arrays["initial"] * rng.uniform(
            0.999, 1.001, size=arrays["initial"].shape
        )
    elif kind == "dwt2d":
        result["image"] = rng.uniform(0, 1, size=arrays["image"].shape)
    elif kind == "mri-gridding":
        samples = np.empty_like(arrays["samples"])
        samples[:, :2] = rng.standard_normal(samples[:, :2].shape)
        samples[:, 2:5] = rng.uniform(0, int(arrays["side"]) - 1, size=samples[:, 2:5].shape)
        samples[:4, 2:5] = [
            [0, 0, 0],
            [int(arrays["side"]) - 1] * 3,
            [0.1, 1.3, 2.6],
            [2.6, 1.3, 0.1],
        ]
        samples[:, 5] = rng.uniform(0.25, 2.0, size=len(samples))
        result["samples"] = samples
    elif kind == "mutual-information":
        first = rng.integers(0, 256, size=arrays["image1"].shape, dtype=np.uint8)
        noise = rng.integers(-20, 21, size=first.shape)
        second = np.clip(first.astype(np.int32) + noise, 0, 255).astype(np.uint8)
        independent = rng.random(first.shape) < (0.1 + 0.15 * (seed % 5))
        second[independent] = rng.integers(0, 256, size=int(independent.sum()), dtype=np.uint8)
        result["image1"], result["image2"] = first, second
    elif kind == "randomized-svd":
        m, n = arrays["matrix"].shape
        components = min(2 * int(arrays["rank"]), m, n)
        left_basis = np.linalg.qr(rng.standard_normal((m, components)))[0]
        right_basis = np.linalg.qr(rng.standard_normal((n, components)))[0]
        spectrum = np.geomspace(1.0, 1e-4, components)
        result["matrix"] = (left_basis * spectrum) @ right_basis.T + 1e-9 * rng.standard_normal(
            (m, n)
        )
    elif kind == "npb-cg":
        n = int(arrays["n"])
        permutation = rng.permutation(n)
        inverse = np.argsort(permutation)
        lengths = 3 - (permutation == 0).astype(int) - (permutation == n - 1).astype(int)
        rows = np.concatenate(([1], 1 + np.cumsum(lengths)))
        starts = rows[:-1] - 1
        columns = np.empty_like(arrays["columns"])
        values = np.empty_like(arrays["values"])
        diagonal = rng.uniform(4, 5, size=n)
        off_diagonal = rng.uniform(-1.5, -0.5, size=n - 1)
        columns[starts] = np.arange(n) + 1
        values[starts] = diagonal[permutation]
        left = permutation > 0
        columns[starts[left] + 1] = inverse[permutation[left] - 1] + 1
        values[starts[left] + 1] = off_diagonal[permutation[left] - 1]
        right = permutation < n - 1
        positions = starts[right] + 1 + left[right].astype(int)
        columns[positions] = inverse[permutation[right] + 1] + 1
        values[positions] = off_diagonal[permutation[right]]
        result.update(rows=rows, columns=columns, values=values, rhs=rng.standard_normal(n))
    elif kind == "npb-mg":
        rhs = rng.standard_normal(arrays["rhs"].shape)
        result["rhs"] = rhs - rhs.mean()  # Periodic Poisson compatibility.
    elif kind == "npb-ft":
        result["field"] = rng.standard_normal(arrays["field"].shape)
    elif kind == "cfd":
        n = int(arrays["n"])
        side = round((n / 6) ** (1 / 3))
        if 6 * side**3 != n:
            raise ValueError("CFD fixture size must comprise complete tetrahedral cubes")
        areas, neighbors, normals = tetrahedral_mesh(side)
        permutation = rng.permutation(n)
        inverse = np.argsort(permutation)
        reordered = neighbors[:, permutation].copy()
        interior = reordered >= 0
        reordered[interior] = inverse[reordered[interior]]
        density = rng.uniform(1.386, 1.414, size=n)
        velocity = rng.uniform(-0.005, 0.005, size=(3, n))
        velocity[0] += 1.2
        pressure = rng.uniform(0.99, 1.01, size=n)
        state = np.empty((5, n))
        state[0] = density
        state[1:4] = density * velocity
        state[4] = pressure / 0.4 + 0.5 * density * np.square(velocity).sum(axis=0)
        result.update(
            state=state,
            areas=areas[permutation],
            neighbors=reordered,
            normals=normals[:, :, permutation],
        )
    else:
        raise ValueError(f"Unknown native random-input profile: {kind}")
    for field in FIELDS[kind]:
        result[field] = np.asarray(result[field], dtype=arrays[field].dtype)
        if result[field].shape != arrays[field].shape:
            raise ValueError(f"Random profile changed native shape for {field}")
    return result
