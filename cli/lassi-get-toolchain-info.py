#!/usr/bin/env python3
"""Report effective Python/torch/torch-mlir/LLVM toolchain info."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async
setup_path()


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    from lassi.integrations.toolchain_info import get_toolchain_info_impl
    return run_async(get_toolchain_info_impl(), title="Toolchain info")


if __name__ == "__main__":
    raise SystemExit(main())
