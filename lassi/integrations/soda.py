from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path


VALID_SODA_STAGES = {
    "tosa",
    "linalg",
    "llvm-mlir",
    "llvm-ll",
    "llvm-mode-mlir",
    "llvm-mode-ll",
    "bambu-verilog",
    "bambu-sim",
}
VALID_SODA_MODES = {"baseline", "transformed"}


async def synthesize_tosa_with_soda_impl(
    output_dir: str,
    stage: str = "bambu-verilog",
    build_mode: str = "transformed",
) -> str:
    resolved_output_dir = Path(output_dir).resolve()
    tosa_path = resolved_output_dir / "01_tosa.mlir"
    log_path = resolved_output_dir / "log.txt"
    makefile_path = Path(__file__).resolve().parents[2] / "soda-tools" / "Makefile"

    if not resolved_output_dir.is_dir():
        return f"Synthesis failed: output directory not found at {resolved_output_dir}"

    if not tosa_path.exists():
        return f"Synthesis failed: expected TOSA MLIR at {tosa_path}"

    if stage not in VALID_SODA_STAGES:
        return f"Synthesis failed: unsupported stage '{stage}'. Valid values: {', '.join(sorted(VALID_SODA_STAGES))}"

    if build_mode not in VALID_SODA_MODES:
        return f"Synthesis failed: unsupported build_mode '{build_mode}'. Valid values: baseline, transformed"

    if not makefile_path.exists():
        return f"Synthesis failed: soda-tools Makefile not found at {makefile_path}"

    transform_path = resolved_output_dir.parent / "transform.mlir"
    if build_mode == "transformed" and not transform_path.exists():
        alternate_transform_path = resolved_output_dir / "transform.mlir"
        if alternate_transform_path.exists():
            transform_path = alternate_transform_path
        else:
            return (
                "Synthesis failed: transformed mode requires transform.mlir. "
                f"Tried {transform_path} and {alternate_transform_path}"
            )

    cmd = [
        "make",
        "-f",
        str(makefile_path),
        f"ODIR={resolved_output_dir}",
        f"STOP_STAGE={stage}",
        f"BUILD_MODE={build_mode}",
    ]
    if build_mode == "transformed":
        cmd.append(f"TRANSFORM_PATH={transform_path}")

    def _run_make() -> subprocess.CompletedProcess:
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            cmd,
            cwd=str(resolved_output_dir),
            capture_output=True,
            text=True,
        )
        combined_output = [f"$ {' '.join(cmd)}"]
        if completed.stdout:
            combined_output.append(completed.stdout)
        if completed.stderr:
            combined_output.append(completed.stderr)
        log_path.write_text("\n".join(combined_output), encoding="utf-8")
        return completed

    try:
        completed = await asyncio.to_thread(_run_make)
    except Exception as exc:
        return f"Synthesis failed with internal error: {str(exc)}"

    status = "Success" if completed.returncode == 0 else f"Failed (Code {completed.returncode})"
    return (
        f"--- Synthesis {status} ---\n"
        f"output_dir: {resolved_output_dir}\n"
        f"stage: {stage}\n"
        f"build_mode: {build_mode}\n"
        f"log_path: {log_path}"
    )
