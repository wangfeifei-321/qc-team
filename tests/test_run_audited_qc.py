import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import run_audited_qc as audited


class AuditedQcAdapterTests(unittest.TestCase):
    def test_production_run_links_upstream_and_keeps_first_pass_independent(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            project = root / "project"
            reports = project / "reports"
            roles = project / "roles"
            reports.mkdir(parents=True)
            roles.mkdir()
            for name in (
                "01_主审_claude.md",
                "02_复核_codex.md",
                "03_整理_minimax.md",
            ):
                (roles / name).write_text(name, encoding="utf-8")
            manuscript = root / "manuscript.md"
            manuscript.write_text("source", encoding="utf-8")
            upstream = root / "dip_manifest.json"
            upstream.write_text('{"status":"frozen"}\n', encoding="utf-8")

            def fake_verify(_document):
                (reports / "_refs_verified.json").write_text("[]\n", encoding="utf-8")

            codex_inputs = []

            def fake_codex(_role, _document, _refs, lead_review):
                codex_inputs.append(lead_review)
                return "codex review"

            with (
                patch.object(audited, "PROJECT_ROOT", project),
                patch.object(audited.qc, "load_env", return_value={"key": "test"}),
                patch.object(audited.qc, "ensure_ready"),
                patch.object(audited.qc, "load_manuscript", return_value="source"),
                patch.object(audited.qc, "verify_references", side_effect=fake_verify),
                patch.object(audited.qc, "call_claude", return_value="claude review"),
                patch.object(audited.qc, "call_codex", side_effect=fake_codex),
                patch.object(audited.qc, "call_minimax", return_value="final report"),
            ):
                exit_code = audited.main(
                    [
                        str(manuscript),
                        "--runs-dir",
                        str(root / "runs"),
                        "--run-id",
                        "production-test",
                        "--upstream-manifest",
                        str(upstream),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                codex_inputs, ["WITHHELD_DURING_INDEPENDENT_FIRST_PASS"]
            )
            manifest = json.loads(
                (root / "runs" / "production-test" / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["status"], "COMPLETED")
            kinds = {artifact["kind"] for artifact in manifest["artifacts"]}
            self.assertIn("dip-frozen-manifest", kinds)
            self.assertIn("dual-review-index", kinds)
            self.assertIn("final-report", kinds)


if __name__ == "__main__":
    unittest.main()
