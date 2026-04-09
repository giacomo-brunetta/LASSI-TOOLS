import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from LASSI_mcp import compare_csv_outputs, diff_csv_outputs, summarize_csv
from lassi.csv_tools import (
    compare_csv_outputs_impl,
    diff_csv_outputs_impl,
    summarize_csv_impl,
)


class CsvToolHarness(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_csv(self, name: str, data: np.ndarray) -> Path:
        path = self.tmp / name
        np.savetxt(path, data, delimiter=",", fmt="%.18g")
        return path

    async def call_mcp_tool(self, tool, /, *args, **kwargs) -> str:
        return await tool.fn(*args, **kwargs)

    async def test_summarize_csv_impl_reports_expected_stats(self) -> None:
        csv_path = self.write_csv(
            "matrix.csv",
            np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64),
        )

        result = json.loads(await summarize_csv_impl(str(csv_path)))

        self.assertEqual(result["path"], str(csv_path.resolve()))
        self.assertEqual(result["shape"], [2, 2])
        self.assertEqual(result["size"], 4)
        self.assertEqual(result["min"], 1.0)
        self.assertEqual(result["max"], 4.0)
        self.assertAlmostEqual(result["mean"], 2.5)
        self.assertAlmostEqual(result["std"], float(np.std([[1.0, 2.0], [3.0, 4.0]])))
        self.assertFalse(result["has_nan"])
        self.assertFalse(result["has_inf"])

    async def test_summarize_csv_wrapper_handles_single_column_shape(self) -> None:
        csv_path = self.write_csv(
            "column.csv",
            np.array([5.0, 6.0, 7.0], dtype=np.float64),
        )

        result = json.loads(await self.call_mcp_tool(summarize_csv, str(csv_path)))

        self.assertEqual(result["shape"], [3, 1])
        self.assertEqual(result["size"], 3)
        self.assertEqual(result["min"], 5.0)
        self.assertEqual(result["max"], 7.0)

    async def test_compare_csv_outputs_impl_classifies_identical(self) -> None:
        golden = self.write_csv(
            "golden_identical.csv",
            np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64),
        )
        candidate = self.write_csv(
            "candidate_identical.csv",
            np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64),
        )

        result = json.loads(
            await compare_csv_outputs_impl(str(golden), str(candidate), expected_shape=[2, 2])
        )

        self.assertTrue(result["shape_match"])
        self.assertTrue(result["exact_match"])
        self.assertTrue(result["allclose"])
        self.assertEqual(result["classification"], "IDENTICAL")
        self.assertTrue(result["expected_shape_match"])
        self.assertEqual(result["max_abs_error"], 0.0)
        self.assertEqual(result["first_max_abs_mismatch_index"], [0, 0])

    async def test_compare_csv_outputs_wrapper_classifies_tolerated_drift(self) -> None:
        golden = self.write_csv(
            "golden_drift.csv",
            np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64),
        )
        candidate = self.write_csv(
            "candidate_drift.csv",
            np.array([[1.0, 2.0], [3.0, 4.0000005]], dtype=np.float64),
        )

        result = json.loads(
            await self.call_mcp_tool(
                compare_csv_outputs,
                str(golden),
                str(candidate),
                rtol=1e-6,
                atol=1e-6,
                expected_shape=[2, 2],
            )
        )

        self.assertTrue(result["shape_match"])
        self.assertFalse(result["exact_match"])
        self.assertTrue(result["allclose"])
        self.assertEqual(result["classification"], "ACCEPTABLE_NUMERIC_DRIFT")
        self.assertGreater(result["max_abs_error"], 0.0)
        self.assertEqual(result["first_max_abs_mismatch_index"], [1, 1])

    async def test_compare_csv_outputs_reports_shape_mismatch(self) -> None:
        golden = self.write_csv(
            "golden_shape.csv",
            np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64),
        )
        candidate = self.write_csv(
            "candidate_shape.csv",
            np.array([1.0, 2.0, 3.0], dtype=np.float64),
        )

        result = json.loads(await compare_csv_outputs_impl(str(golden), str(candidate)))

        self.assertFalse(result["shape_match"])
        self.assertFalse(result["exact_match"])
        self.assertFalse(result["allclose"])
        self.assertEqual(result["error"], "Shape mismatch")

    async def test_diff_csv_outputs_impl_reports_and_persists_mismatches(self) -> None:
        golden = self.write_csv(
            "golden_diff.csv",
            np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64),
        )
        candidate = self.write_csv(
            "candidate_diff.csv",
            np.array([[1.0, 9.0], [8.0, 4.0]], dtype=np.float64),
        )
        report_path = self.tmp / "reports" / "diff_report.json"

        result = json.loads(
            await diff_csv_outputs_impl(
                str(golden),
                str(candidate),
                output_path=str(report_path),
                max_rows=1,
            )
        )

        self.assertTrue(result["shape_match"])
        self.assertEqual(result["mismatch_count"], 2)
        self.assertEqual(result["max_rows"], 1)
        self.assertEqual(len(result["reported_mismatches"]), 1)
        self.assertEqual(result["reported_mismatches"][0]["index"], [0, 1])
        self.assertEqual(result["output_path"], str(report_path.resolve()))

        persisted = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["mismatch_count"], 2)
        self.assertEqual(len(persisted["reported_mismatches"]), 1)

    async def test_diff_csv_outputs_wrapper_handles_shape_mismatch(self) -> None:
        golden = self.write_csv(
            "golden_wrapper_shape.csv",
            np.array([[1.0, 2.0]], dtype=np.float64),
        )
        candidate = self.write_csv(
            "candidate_wrapper_shape.csv",
            np.array([[1.0], [2.0], [3.0]], dtype=np.float64),
        )

        result = json.loads(
            await self.call_mcp_tool(diff_csv_outputs, str(golden), str(candidate))
        )

        self.assertFalse(result["shape_match"])
        self.assertEqual(result["error"], "Shape mismatch")

    async def test_summarize_csv_impl_rejects_empty_file(self) -> None:
        empty_csv = self.tmp / "empty.csv"
        empty_csv.write_text("", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "CSV file is empty"):
            await summarize_csv_impl(str(empty_csv))

    async def test_compare_csv_outputs_impl_rejects_missing_file(self) -> None:
        golden = self.write_csv("golden_present.csv", np.array([[1.0]], dtype=np.float64))
        missing_candidate = self.tmp / "missing.csv"

        with self.assertRaisesRegex(FileNotFoundError, "CSV file not found"):
            await compare_csv_outputs_impl(str(golden), str(missing_candidate))


if __name__ == "__main__":
    unittest.main()
