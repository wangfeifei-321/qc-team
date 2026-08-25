#!/usr/bin/env python3
"""Auditable run ledger for QC-Team.

The ledger is deliberately model-agnostic: callers record task transitions,
gate decisions, and produced artifacts.  Completion is derived from evidence,
not from an agent's self-report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


TASK_STATES = {"READY", "RUNNING", "BLOCKED", "FAILED", "COMPLETED"}
GATE_STATES = {"PASS", "BLOCKED"}
ALLOWED_TRANSITIONS = {
    "READY": {"RUNNING"},
    "RUNNING": {"BLOCKED", "FAILED", "COMPLETED"},
    "BLOCKED": {"READY"},
    "FAILED": {"READY"},
    "COMPLETED": set(),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


@dataclass(frozen=True)
class RunPaths:
    root: Path

    @property
    def manifest(self) -> Path:
        return self.root / "manifest.json"

    @property
    def events(self) -> Path:
        return self.root / "events.jsonl"

    @property
    def baseline(self) -> Path:
        return self.root / "baseline"

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    @property
    def seal(self) -> Path:
        return self.root / "seal.json"


class EvidenceError(RuntimeError):
    """Raised when an evidence or state invariant would be violated."""


class EvidenceRun:
    def __init__(self, run_dir: Path | str):
        self.paths = RunPaths(Path(run_dir).resolve())
        if not self.paths.manifest.exists():
            raise EvidenceError(f"run manifest not found: {self.paths.manifest}")

    @classmethod
    def create(
        cls,
        source: Path | str,
        runs_dir: Path | str,
        task_names: Iterable[str],
        required_gates: Iterable[str],
        run_id: str | None = None,
        mode: str = "production",
    ) -> "EvidenceRun":
        source_path = Path(source).resolve()
        if not source_path.is_file():
            raise EvidenceError(f"source is not a file: {source_path}")

        resolved_run_id = run_id or (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            + "-"
            + uuid.uuid4().hex[:8]
        )
        root = Path(runs_dir).resolve() / resolved_run_id
        if root.exists():
            raise EvidenceError(f"run already exists: {root}")
        paths = RunPaths(root)
        paths.baseline.mkdir(parents=True)
        paths.artifacts.mkdir()

        frozen_source = paths.baseline / source_path.name
        shutil.copy2(source_path, frozen_source)
        tasks = {name: {"state": "READY", "updated_at": utc_now()} for name in task_names}
        if not tasks:
            raise EvidenceError("at least one task is required")
        gates = {
            name: {"status": "BLOCKED", "evidence": None, "updated_at": utc_now()}
            for name in required_gates
        }
        if not gates:
            raise EvidenceError("at least one required gate is required")

        manifest = {
            "schema_version": 1,
            "run_id": resolved_run_id,
            "mode": mode,
            "status": "RUNNING",
            "created_at": utc_now(),
            "completed_at": None,
            "baseline": {
                "original_name": source_path.name,
                "frozen_path": str(frozen_source.relative_to(root)),
                "sha256": sha256_file(frozen_source),
            },
            "tasks": tasks,
            "gates": gates,
            "artifacts": [],
        }
        write_json(paths.manifest, manifest)
        run = cls(root)
        run._append_event("RUN_CREATED", baseline_sha256=manifest["baseline"]["sha256"])
        return run

    def _load(self) -> dict:
        return json.loads(self.paths.manifest.read_text(encoding="utf-8"))

    def _save(self, manifest: dict) -> None:
        write_json(self.paths.manifest, manifest)

    def _append_event(self, event: str, **details: object) -> None:
        record = {"at": utc_now(), "event": event, **details}
        with self.paths.events.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    @property
    def run_id(self) -> str:
        return self._load()["run_id"]

    def transition(self, task: str, new_state: str, reason: str | None = None) -> None:
        if new_state not in TASK_STATES:
            raise EvidenceError(f"unknown task state: {new_state}")
        manifest = self._load()
        if manifest["status"] == "COMPLETED":
            raise EvidenceError("completed runs are immutable")
        if task not in manifest["tasks"]:
            raise EvidenceError(f"unknown task: {task}")
        current = manifest["tasks"][task]["state"]
        if new_state not in ALLOWED_TRANSITIONS[current]:
            raise EvidenceError(f"invalid transition for {task}: {current} -> {new_state}")
        manifest["tasks"][task] = {
            "state": new_state,
            "updated_at": utc_now(),
            "reason": reason,
        }
        self._save(manifest)
        self._append_event(
            "TASK_TRANSITION", task=task, from_state=current, to_state=new_state, reason=reason
        )

    def add_artifact(self, artifact: Path | str, kind: str) -> dict:
        manifest = self._load()
        if manifest["status"] == "COMPLETED":
            raise EvidenceError("completed runs are immutable")
        source = Path(artifact).resolve()
        if not source.is_file():
            raise EvidenceError(f"artifact is not a file: {source}")
        destination = self.paths.artifacts / source.name
        if destination.exists():
            raise EvidenceError(f"artifact name already registered: {source.name}")
        shutil.copy2(source, destination)
        record = {
            "kind": kind,
            "path": str(destination.relative_to(self.paths.root)),
            "sha256": sha256_file(destination),
            "registered_at": utc_now(),
        }
        manifest["artifacts"].append(record)
        self._save(manifest)
        self._append_event("ARTIFACT_REGISTERED", **record)
        return record

    def set_gate(self, gate: str, status: str, evidence: str) -> None:
        if status not in GATE_STATES:
            raise EvidenceError(f"unknown gate status: {status}")
        manifest = self._load()
        if manifest["status"] == "COMPLETED":
            raise EvidenceError("completed runs are immutable")
        if gate not in manifest["gates"]:
            raise EvidenceError(f"unknown gate: {gate}")
        if not evidence.strip():
            raise EvidenceError("gate decisions require an evidence locator")
        locator_path = evidence.split("#", 1)[0]
        resolved_locator = (self.paths.root / locator_path).resolve()
        try:
            resolved_locator.relative_to(self.paths.root)
        except ValueError as error:
            raise EvidenceError("gate evidence must stay inside the run directory") from error
        if not resolved_locator.is_file():
            raise EvidenceError(f"gate evidence does not exist: {locator_path}")
        manifest["gates"][gate] = {
            "status": status,
            "evidence": evidence,
            "updated_at": utc_now(),
        }
        self._save(manifest)
        self._append_event("GATE_DECISION", gate=gate, status=status, evidence=evidence)

    def finalize(self) -> None:
        manifest = self._load()
        if manifest["status"] == "COMPLETED":
            raise EvidenceError("completed runs are immutable")
        incomplete = [
            name for name, task in manifest["tasks"].items() if task["state"] != "COMPLETED"
        ]
        blocked = [
            name for name, gate in manifest["gates"].items() if gate["status"] != "PASS"
        ]
        if incomplete or blocked:
            self._append_event("COMPLETION_REJECTED", incomplete_tasks=incomplete, blocked_gates=blocked)
            raise EvidenceError(
                "completion rejected; "
                f"incomplete tasks={incomplete or 'none'}, blocked gates={blocked or 'none'}"
            )
        manifest["status"] = "COMPLETED"
        manifest["completed_at"] = utc_now()
        self._save(manifest)
        self._append_event("RUN_COMPLETED")
        write_json(
            self.paths.seal,
            {
                "sealed_at": utc_now(),
                "manifest_sha256": sha256_file(self.paths.manifest),
                "events_sha256": sha256_file(self.paths.events),
            },
        )

    def verify(self) -> None:
        manifest = self._load()
        baseline = self.paths.root / manifest["baseline"]["frozen_path"]
        if sha256_file(baseline) != manifest["baseline"]["sha256"]:
            raise EvidenceError("baseline hash mismatch")
        for artifact in manifest["artifacts"]:
            path = self.paths.root / artifact["path"]
            if sha256_file(path) != artifact["sha256"]:
                raise EvidenceError(f"artifact hash mismatch: {artifact['path']}")
        if manifest["status"] == "COMPLETED":
            if not self.paths.seal.is_file():
                raise EvidenceError("completed run seal is missing")
            seal = json.loads(self.paths.seal.read_text(encoding="utf-8"))
            if sha256_file(self.paths.manifest) != seal["manifest_sha256"]:
                raise EvidenceError("manifest seal mismatch")
            if sha256_file(self.paths.events) != seal["events_sha256"]:
                raise EvidenceError("event log seal mismatch")


def cli() -> int:
    parser = argparse.ArgumentParser(description="QC-Team evidence ledger")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify", help="verify baseline and artifact hashes")
    verify_parser.add_argument("run_dir")

    demo_parser = subparsers.add_parser(
        "demo", help="create a labelled failure-and-recovery demonstration run"
    )
    demo_parser.add_argument("source")
    demo_parser.add_argument("--runs-dir", default="reports/evidence_runs")
    demo_parser.add_argument("--run-id")

    args = parser.parse_args()
    try:
        if args.command == "verify":
            run = EvidenceRun(args.run_dir)
            run.verify()
            print(f"VERIFIED {run.run_id}")
            return 0
        if args.command == "demo":
            run = EvidenceRun.create(
                args.source,
                args.runs_dir,
                task_names=["freeze_baseline", "evidence_review", "release_report"],
                required_gates=["baseline_integrity", "evidence_locator", "release"],
                run_id=args.run_id,
                mode="demonstration",
            )
            run.transition("freeze_baseline", "RUNNING")
            run.transition("freeze_baseline", "COMPLETED")
            run.set_gate(
                "baseline_integrity", "PASS", "manifest.json#/baseline/sha256"
            )
            run.transition("evidence_review", "RUNNING")
            run.transition(
                "evidence_review", "BLOCKED", "required source locator is absent"
            )
            run.set_gate(
                "evidence_locator", "BLOCKED", "events.jsonl#TASK_TRANSITION"
            )
            try:
                run.finalize()
            except EvidenceError:
                pass
            run.transition("evidence_review", "READY", "source locator supplied")
            run.transition("evidence_review", "RUNNING")
            with tempfile.TemporaryDirectory() as temporary_dir:
                recovery_path = Path(temporary_dir) / "recovery_evidence.md"
                recovery_path.write_text(
                    "# Recovery evidence\n\n"
                    "The missing source locator was supplied.\n\n"
                    "Locator: baseline/" + Path(args.source).name + "\n",
                    encoding="utf-8",
                )
                record = run.add_artifact(recovery_path, "recovery-evidence")
            run.transition("evidence_review", "COMPLETED")
            run.set_gate("evidence_locator", "PASS", record["path"])
            run.transition("release_report", "RUNNING")
            run.transition("release_report", "COMPLETED")
            run.set_gate("release", "PASS", "events.jsonl#release_report:COMPLETED")
            run.finalize()
            run.verify()
            print(f"COMPLETED {run.run_id} {run.paths.root}")
            return 0
    except EvidenceError as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(cli())
