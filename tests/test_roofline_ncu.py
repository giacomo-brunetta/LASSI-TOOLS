"""Exercise real Nsight CSV conventions without requiring CUDA counters locally."""

from __future__ import annotations

import csv
import json

import pytest

from lassi_x.roofline_ncu import import_ncu


def make_inputs(tmp_path, rows):
    capture = tmp_path / "capture.json"
    capture.write_text(
        json.dumps(
            {
                "forward_invocations": 1,
                "scope": "device_forward",
                "source_sha256": "abc",
                "dataset": "large",
                "precision": "fp16",
                "memory_tier": "HBM2",
            }
        )
    )
    path = tmp_path / "ncu.csv"
    with path.open("w", newline="") as handle:
        handle.write("==PROF== Connected to process 123\n")
        writer = csv.writer(handle)
        writer.writerow(
            ["ID", "Process ID", "Device", "Metric Name", "Metric Unit", "Metric Value"]
        )
        writer.writerows(rows)
    return path, capture


def test_import_sums_kernel_launches_and_si_units(tmp_path):
    path, capture = make_inputs(
        tmp_path,
        [
            [0, 123, 0, "dram__bytes_read.sum", "byte", "1,024"],
            [0, 123, 0, "dram__bytes_write.sum", "byte", "512"],
            [1, 123, 0, "dram__bytes_read.sum", "Kbyte", "2"],
            [1, 123, 0, "dram__bytes_write.sum", "Kbyte", "1"],
        ],
    )
    report = import_ncu(path, capture)
    assert report["bytes"] == 1024 + 512 + 2000 + 1000
    assert report["kernel_launches"] == 2
    assert report["source_sha256"] == "abc"
    assert report["ncu_csv_sha256"]


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([[0, 123, 0, "dram__bytes_read.sum", "byte", "1"]], "both read and write"),
        (
            [
                [0, 123, 0, "dram__bytes_read.sum", "byte", "1"],
                [0, 123, 0, "dram__bytes_read.sum", "byte", "1"],
            ],
            "duplicate",
        ),
        ([[0, 123, 0, "dram__bytes_read.sum", "byte", "nan"]], "finite"),
        ([[0, 123, 0, "dram__bytes_read.sum", "KiB", "2"]], "unit"),
        ([], "exactly one GPU"),
    ],
)
def test_import_rejects_ambiguous_or_incomplete_counters(tmp_path, rows, message):
    path, capture = make_inputs(tmp_path, rows)
    with pytest.raises(ValueError, match=message):
        import_ncu(path, capture)
