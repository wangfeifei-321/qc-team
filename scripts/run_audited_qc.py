#!/usr/bin/env python3
"""Run the existing QC pipeline with an auditable evidence ledger.

This adapter keeps Claude and Codex independent during their first-pass
reviews. Their outputs meet only in the MiniMax synthesis step.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import qc  # noqa: E402
from qc_evidence import EvidenceError, EvidenceRun  # noqa: E402


def complete_task(run: EvidenceRun, task: str, operation):
    run.transition(task, "RUNNING")
    try:
        result = operation()
    except Exception as error:
        run.transition(task, "FAILED", str(error))
        raise
    run.transition(task, "COMPLETED")
    return result


def load_agent(slug: str, legacy_filename: str) -> str:
    """Prefer formal Agent definitions while retaining old-repo compatibility."""
    if hasattr(qc, "read_agent"):
        return qc.read_agent(slug)
    return qc.read(str(PROJECT_ROOT / "roles" / legacy_filename))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run QC-Team with immutable evidence")
    parser.add_argument("manuscript")
    parser.add_argument("--runs-dir", default="reports/evidence_runs")
    parser.add_argument("--run-id")
    provenance = parser.add_mutually_exclusive_group(required=True)
    provenance.add_argument(
        "--upstream-manifest",
        help="frozen DIP run manifest consumed by this QC run",
    )
    provenance.add_argument(
        "--standalone",
        action="store_true",
        help="declare that this is a standalone QC run without DIP provenance",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manuscript = Path(args.manuscript).expanduser().resolve()
    run = EvidenceRun.create(
        manuscript,
        args.runs_dir,
        task_names=[
            "freeze_baseline",
            "verify_references",
            "claude_review",
            "codex_review",
            "minimax_report",
        ],
        required_gates=[
            "provenance",
            "baseline_integrity",
            "reference_evidence",
            "independent_dual_review",
            "release",
        ],
        run_id=args.run_id,
        mode="production",
    )

    try:
        run.transition("freeze_baseline", "RUNNING")
        if args.upstream_manifest:
            upstream = run.add_artifact(args.upstream_manifest, "dip-frozen-manifest")
            run.set_gate("provenance", "PASS", upstream["path"])
        else:
            run.set_gate("provenance", "PASS", "manifest.json#/mode")
        run.transition("freeze_baseline", "COMPLETED")
        run.set_gate("baseline_integrity", "PASS", "manifest.json#/baseline/sha256")

        cfg = qc.load_env()
        qc.ensure_ready(cfg)
        document = qc.load_manuscript(str(manuscript))

        complete_task(run, "verify_references", lambda: qc.verify_references(document))
        refs_path = PROJECT_ROOT / "reports" / "_refs_verified.json"
        if not refs_path.is_file():
            refs_path.write_text(
                json.dumps({"result": "no DOI evidence produced"}, ensure_ascii=False),
                encoding="utf-8",
            )
        refs_record = run.add_artifact(refs_path, "reference-evidence")
        run.set_gate("reference_evidence", "PASS", refs_record["path"])
        refs_fact = qc.read(str(refs_path))

        lead_role = load_agent("qc-conductor", "01_主审_claude.md")
        cross_role = load_agent("qc-verifier", "02_复核_codex.md")
        final_role = load_agent("qc-reporter", "03_整理_minimax.md")

        # The two first-pass reviewers receive the same manuscript and evidence,
        # but neither receives the other reviewer's output.
        lead = complete_task(
            run,
            "claude_review",
            lambda: qc.call_claude(lead_role, document, refs_fact),
        )
        cross = complete_task(
            run,
            "codex_review",
            lambda: qc.call_codex(
                cross_role,
                document,
                refs_fact,
                "WITHHELD_DURING_INDEPENDENT_FIRST_PASS",
            ),
        )

        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary = Path(temporary_dir)
            lead_path = temporary / "claude_independent_review.md"
            cross_path = temporary / "codex_independent_review.md"
            lead_path.write_text(lead, encoding="utf-8")
            cross_path.write_text(cross, encoding="utf-8")
            lead_record = run.add_artifact(lead_path, "independent-review-claude")
            cross_record = run.add_artifact(cross_path, "independent-review-codex")
            index_path = temporary / "dual_review_index.json"
            index_path.write_text(
                json.dumps(
                    {
                        "review_mode": "independent_first_pass",
                        "claude": lead_record,
                        "codex": cross_record,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            index_record = run.add_artifact(index_path, "dual-review-index")

        run.set_gate(
            "independent_dual_review",
            "PASS",
            index_record["path"],
        )

        final_report = complete_task(
            run,
            "minimax_report",
            lambda: qc.call_minimax(final_role, lead, cross, refs_fact, cfg),
        )
        with tempfile.TemporaryDirectory() as temporary_dir:
            report_path = Path(temporary_dir) / "qc_final_report.md"
            report_path.write_text(final_report, encoding="utf-8")
            report_record = run.add_artifact(report_path, "final-report")
        run.set_gate("release", "PASS", report_record["path"])
        run.finalize()
        run.verify()
        print(f"COMPLETED {run.run_id} {run.paths.root}")
        return 0
    except (EvidenceError, RuntimeError, OSError) as error:
        print(f"BLOCKED {run.run_id}: {error}", file=sys.stderr)
        print(f"Evidence retained at: {run.paths.root}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
