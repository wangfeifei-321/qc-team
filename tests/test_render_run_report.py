import tempfile
import unittest
from pathlib import Path

from qc_evidence import EvidenceRun
from scripts.render_run_report import render


class RunReportTests(unittest.TestCase):
    def test_renders_verified_run_and_escapes_content(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            source = root / "source.md"
            source.write_text("source", encoding="utf-8")
            run = EvidenceRun.create(
                source,
                root / "runs",
                task_names=["review<script>"],
                required_gates=["release"],
                run_id="report-test",
                mode="demonstration",
            )
            run.transition("review<script>", "RUNNING")
            run.transition("review<script>", "COMPLETED")
            run.set_gate("release", "PASS", "events.jsonl")
            run.finalize()

            page = render(run.paths.root)

            self.assertIn("report-test", page)
            self.assertIn("DEMONSTRATION", page)
            self.assertIn("1/1", page)
            self.assertIn("READY → RUNNING", page)
            self.assertIn("review&lt;script&gt;", page)
            self.assertNotIn("review<script>", page)


if __name__ == "__main__":
    unittest.main()
