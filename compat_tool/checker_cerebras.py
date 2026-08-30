"""Cerebras CSX compile-only checker for compatibility probes."""

# Cerebras and PyTorch must remain lazy imports so the wiki is usable off-system.
# ruff: noqa: PLC0415, TC003

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from compat_tool.checker_base import CheckerUnavailableError, CompileChecker, named_wrapper


class CerebrasChecker(CompileChecker):
    """Compile one canonical operator graph with the Cerebras CSX backend."""

    def _modules(self) -> tuple[Any, Any]:
        try:
            import cerebras.pytorch as cstorch
            import torch
        except ImportError as error:
            raise CheckerUnavailableError(f"Cerebras PyTorch is unavailable: {error}") from error
        return torch, cstorch

    def metadata(self) -> dict[str, Any]:
        torch, cstorch = self._modules()
        metadata = super().metadata()
        try:
            cerebras_version = version("cerebras-pytorch")
        except PackageNotFoundError:
            cerebras_version = getattr(cstorch, "__version__", "unknown")
        metadata.update(
            {
                "torch": torch.__version__,
                "compiler": "cerebras-pytorch",
                "cerebras_pytorch": cerebras_version,
                "compile_mode": "compile_only",
                "precision_optimization_level": int(
                    self.options.get("precision_optimization_level", 1)
                ),
                "available": True,
            }
        )
        return metadata

    def compile(
        self,
        module: Any,
        inputs: tuple[Any, ...],
        *,
        op_name: str,
        precision: str,
        case_hash: str,
        work_dir: Path,
    ) -> dict[str, Any]:
        del precision, case_hash
        torch, cstorch = self._modules()

        # The CSX backend traces one static graph per process. The shared probe already
        # isolates every operator in its own worker process, matching that restriction.
        cstorch.backends.csx.precision.optimization_level = int(
            self.options.get("precision_optimization_level", 1)
        )

        cluster_config = cstorch.distributed.ClusterConfig(
            num_csx=int(self.options.get("num_csx", 1)),
            max_wgt_servers=int(self.options.get("max_wgt_servers", 1)),
            max_act_per_csx=int(self.options.get("max_act_per_csx", 1)),
            num_workers_per_csx=int(self.options.get("num_workers_per_csx", 1)),
            job_time_sec=int(self.options.get("job_time_sec", 1800)),
            job_labels=["name=lassi-compat"],
        )
        backend_kwargs: dict[str, Any] = {
            "artifact_dir": str(work_dir / "cerebras_logs"),
            "compile_only": True,
            "cluster_config": cluster_config,
        }
        compile_dir = self.options.get("compile_dir")
        if compile_dir:
            backend_kwargs["compile_dir"] = str(compile_dir)
        backend = cstorch.backend("CSX", **backend_kwargs)

        inner = named_wrapper(module, len(inputs)).eval()

        class BatchSqueezeModule(torch.nn.Module):
            """Restore canonical shapes after the loader adds batch size one."""

            def __init__(self, wrapped: Any) -> None:
                super().__init__()
                self.wrapped = wrapped

            def forward(self, *batched_inputs: Any) -> Any:
                return self.wrapped(*(value.squeeze(0) for value in batched_inputs))

        compiled_model = cstorch.compile(BatchSqueezeModule(inner).eval(), backend)

        # Cerebras input tensors must originate from its DataLoader and share a leading
        # batch dimension. A one-item torch loader supplies that dimension; the wrapper
        # above removes it before invoking the canonical operator case.
        class FixedInputDataset(torch.utils.data.Dataset):
            def __len__(self) -> int:
                return 1

            def __getitem__(self, _index: int) -> tuple[Any, ...]:
                return inputs

        def dataloader_factory() -> Any:
            return torch.utils.data.DataLoader(FixedInputDataset(), batch_size=1, shuffle=False)

        dataloader = cstorch.utils.data.DataLoader(dataloader_factory)
        executor = cstorch.utils.data.DataExecutor(
            dataloader,
            num_steps=1,
            checkpoint_steps=None,
            activation_steps=1,
        )

        @cstorch.trace
        def forward_step(*batch: Any) -> Any:
            return compiled_model(*batch)

        @cstorch.step_closure
        def mark_output(_output: Any) -> None:
            # compile_only skips closure execution, but registering the closure keeps
            # the returned tensors live as graph outputs during tracing.
            return None

        steps = 0
        for batch in executor:
            mark_output(forward_step(*batch))
            steps += 1
        if steps != 1:
            raise RuntimeError(f"Cerebras compile-only executor produced {steps} steps")

        return {
            "status": "compiled",
            "compile_trigger": (
                "one traced DataExecutor step completed with CSX compile_only=True; "
                "no wafer execution requested"
            ),
            "op_name": op_name,
            "precision_optimization_level": int(
                self.options.get("precision_optimization_level", 1)
            ),
        }
