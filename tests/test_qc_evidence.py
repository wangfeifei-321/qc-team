import json
import tempfile
import unittest
from pathlib import Path

from qc_evidence import EvidenceError, EvidenceRun


class EvidenceRunTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "manuscript.md"
        self.source.write_text("frozen source", encoding="utf-8")
        self.run = EvidenceRun.create(
            self.source,
            self.root / "runs",
            task_names=["freeze", "review"],
            required_gates=["baseline", "review"],
            run_id="test-run",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_records_blocked_recovery_and_completion(self):
        self.run.transition("freeze", "RUNNING")
        self.run.transition("freeze", "COMPLETED")
        self.run.transition("review", "RUNNING")
        self.run.transition("review", "BLOCKED", "missing source locator")

        with self.assertRaisesRegex(EvidenceError, "completion rejected"):
            self.run.finalize()

        self.run.transition("review", "READY", "source locator supplied")
        self.run.transition("review", "RUNNING")
        artifact = self.root / "review.md"
        artifact.write_text("locator: paragraph 2", encoding="utf-8")
        record = self.run.add_artifact(artifact, "review")
        self.run.transition("review", "COMPLETED")
        self.run.set_gate("baseline", "PASS", "manifest.json#/baseline/sha256")
        self.run.set_gate("review", "PASS", record["path"])
        self.run.finalize()
        self.run.verify()

        manifest = json.loads(self.run.paths.manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "COMPLETED")
        event_names = [
            json.loads(line)["event"]
            for line in self.run.paths.events.read_text(encoding="utf-8").splitlines()
        ]
        self.assertIn("COMPLETION_REJECTED", event_names)
        self.assertIn("RUN_COMPLETED", event_names)

    def test_rejects_illegal_state_jump(self):
        with self.assertRaisesRegex(EvidenceError, "invalid transition"):
            self.run.transition("review", "COMPLETED")

    def test_detects_artifact_tampering(self):
        artifact = self.root / "review.md"
        artifact.write_text("original", encoding="utf-8")
        record = self.run.add_artifact(artifact, "review")
        stored = self.run.paths.root / record["path"]
        stored.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(EvidenceError, "artifact hash mismatch"):
            self.run.verify()

    def test_completed_run_is_immutable(self):
        for task in ("freeze", "review"):
            self.run.transition(task, "RUNNING")
            self.run.transition(task, "COMPLETED")
        for gate in ("baseline", "review"):
            self.run.set_gate(gate, "PASS", "events.jsonl")
        self.run.finalize()
        with self.assertRaisesRegex(EvidenceError, "immutable"):
            self.run.set_gate("review", "BLOCKED", "late change")
        with self.assertRaisesRegex(EvidenceError, "immutable"):
            self.run.finalize()

    def test_rejects_gate_evidence_outside_run(self):
        with self.assertRaisesRegex(EvidenceError, "inside the run directory"):
            self.run.set_gate("review", "PASS", "../../manuscript.md")

    def test_detects_event_log_tampering_after_completion(self):
        for task in ("freeze", "review"):
            self.run.transition(task, "RUNNING")
            self.run.transition(task, "COMPLETED")
        for gate in ("baseline", "review"):
            self.run.set_gate(gate, "PASS", "events.jsonl")
        self.run.finalize()
        with self.run.paths.events.open("a", encoding="utf-8") as handle:
            handle.write('{"event":"FORGED"}\n')
        with self.assertRaisesRegex(EvidenceError, "event log seal mismatch"):
            self.run.verify()


if __name__ == "__main__":
    unittest.main()
