#!/usr/bin/env python3
"""Retrieve GPU information using available SMI tools."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async
setup_path()


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    from lassi.integrations.hardware_info import get_gpu_info_impl
    return run_async(get_gpu_info_impl(), title="GPU info")


if __name__ == "__main__":
    raise SystemExit(main())
