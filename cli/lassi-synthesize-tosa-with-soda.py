#!/usr/bin/env python3
"""Run the shared soda-tools Makefile from an output folder containing 01_tosa.mlir."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async
setup_path()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", required=True,
                   help="Output folder that already contains 01_tosa.mlir.")
    p.add_argument("--stage", default="bambu-verilog",
                   help="Makefile STOP_STAGE: linalg, llvm-mode-ll, bambu-verilog, bambu-sim.")
    p.add_argument("--build-mode", default="transformed",
                   choices=["baseline", "transformed"])
    a = p.parse_args()
    from lassi.integrations.soda import synthesize_tosa_with_soda_impl
    return run_async(synthesize_tosa_with_soda_impl(
        output_dir=a.output_dir,
        stage=a.stage,
        build_mode=a.build_mode,
    ), title="SODA synthesis")


if __name__ == "__main__":
    raise SystemExit(main())
