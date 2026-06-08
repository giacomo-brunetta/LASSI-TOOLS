#!/usr/bin/env python3
"""Report the CPU and RAM info of this machine."""
from __future__ import annotations
import argparse
from _lassi_common import setup_path, run_async
setup_path()


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    from lassi.integrations.hardware_info import get_machine_info_impl
    return run_async(get_machine_info_impl(), title="Machine info")


if __name__ == "__main__":
    raise SystemExit(main())
