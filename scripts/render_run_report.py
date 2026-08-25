#!/usr/bin/env python3
"""Render a sealed QC evidence run as a dependency-free read-only HTML report."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from qc_evidence import EvidenceError, EvidenceRun  # noqa: E402


def escaped(value: object) -> str:
    return html.escape(str(value if value is not None else "—"))


def event_detail(event: dict) -> str:
    if event["event"] == "TASK_TRANSITION":
        detail = f"{event.get('from_state')} → {event.get('to_state')}"
        if event.get("reason"):
            detail += f" · {event['reason']}"
        return detail
    if event["event"] == "GATE_DECISION":
        return f"{event.get('status')} · {event.get('evidence')}"
    if event["event"] == "COMPLETION_REJECTED":
        return (
            f"tasks: {', '.join(event.get('incomplete_tasks', [])) or 'none'} · "
            f"gates: {', '.join(event.get('blocked_gates', [])) or 'none'}"
        )
    if event["event"] == "ARTIFACT_REGISTERED":
        return f"{event.get('kind')} · {event.get('path')}"
    return event.get("baseline_sha256") or "run"


def render(run_dir: Path | str) -> str:
    run = EvidenceRun(run_dir)
    run.verify()
    manifest = json.loads(run.paths.manifest.read_text(encoding="utf-8"))
    events = [
        json.loads(line)
        for line in run.paths.events.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    completed_tasks = sum(
        task["state"] == "COMPLETED" for task in manifest["tasks"].values()
    )
    passed_gates = sum(gate["status"] == "PASS" for gate in manifest["gates"].values())

    task_cards = "".join(
        f'<article class="card"><span>{escaped(name)}</span>'
        f'<strong class="state {escaped(task["state"].lower())}">'
        f'{escaped(task["state"])}</strong></article>'
        for name, task in manifest["tasks"].items()
    )
    gate_rows = "".join(
        "<tr>"
        f"<td>{escaped(name)}</td>"
        f'<td><span class="pill {escaped(gate["status"].lower())}">'
        f'{escaped(gate["status"])}</span></td>'
        f"<td><code>{escaped(gate['evidence'])}</code></td>"
        "</tr>"
        for name, gate in manifest["gates"].items()
    )
    artifact_rows = "".join(
        "<tr>"
        f"<td>{escaped(artifact['kind'])}</td>"
        f"<td><code>{escaped(artifact['path'])}</code></td>"
        f"<td><code>{escaped(artifact['sha256'][:16])}…</code></td>"
        "</tr>"
        for artifact in manifest["artifacts"]
    ) or '<tr><td colspan="3">No artifacts registered</td></tr>'
    timeline = "".join(
        "<li>"
        f'<time>{escaped(event["at"])}</time>'
        f'<span class="dot"></span><div><strong>{escaped(event["event"])}</strong>'
        f'<small>{escaped(event.get("task") or event.get("gate") or "run")} · '
        f'{escaped(event_detail(event))}</small></div>'
        "</li>"
        for event in events
    )

    warning = ""
    if manifest["mode"] != "production":
        warning = (
            '<div class="warning">DEMONSTRATION — controller behavior only. '
            "This is not evidence of a live Agent Team or model run.</div>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QC Run {escaped(manifest['run_id'])}</title>
<style>
:root {{ color-scheme: dark; --bg:#071018; --panel:#101d28; --line:#253746;
  --text:#edf5fa; --muted:#91a6b5; --cyan:#36d7d0; --green:#6ee7a0;
  --amber:#ffc857; --red:#ff6b6b; }}
* {{ box-sizing:border-box }} body {{ margin:0; background:radial-gradient(circle at 85% 0,#153443 0,transparent 35%),var(--bg); color:var(--text); font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace }}
main {{ width:min(1180px,94vw); margin:32px auto 72px }}
header {{ display:flex; justify-content:space-between; gap:24px; align-items:end; border-bottom:1px solid var(--line); padding-bottom:22px }}
h1 {{ margin:4px 0 0; font:700 clamp(28px,5vw,56px)/1 ui-sans-serif,system-ui }}
.eyebrow,.muted,small,time {{ color:var(--muted) }} .status {{ color:var(--green); font-size:18px }}
.warning {{ margin:20px 0; padding:12px 16px; border:1px solid var(--amber); color:var(--amber); background:#2a2311 }}
.metrics,.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin:24px 0 }}
.metric,.card,section {{ background:color-mix(in srgb,var(--panel) 92%,transparent); border:1px solid var(--line); border-radius:12px }}
.metric {{ padding:18px }} .metric strong {{ display:block; font-size:30px; color:var(--cyan) }}
section {{ margin-top:18px; padding:22px }} h2 {{ margin:0 0 16px; font:700 20px ui-sans-serif,system-ui }}
.cards {{ margin:0 }} .card {{ padding:14px; display:flex; justify-content:space-between; gap:10px }}
.state,.pill {{ font-size:12px; padding:2px 8px; border-radius:999px }} .completed,.pass {{ color:var(--green); background:#123824 }}
.blocked,.failed {{ color:var(--red); background:#401a1a }} .ready,.running {{ color:var(--amber); background:#3a3014 }}
table {{ width:100%; border-collapse:collapse }} th,td {{ padding:11px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top }}
th {{ color:var(--muted); font-weight:500 }} code {{ color:#b9e8ff; word-break:break-all }}
ol {{ list-style:none; padding:0; margin:0 }} li {{ display:grid; grid-template-columns:190px 14px 1fr; gap:12px; min-height:54px }}
.dot {{ width:9px; height:9px; margin-top:6px; border-radius:50%; background:var(--cyan); box-shadow:0 0 14px var(--cyan) }}
li div {{ border-bottom:1px solid var(--line); padding-bottom:12px }} li small {{ display:block }}
@media(max-width:650px) {{ header {{ align-items:start; flex-direction:column }} li {{ grid-template-columns:1fr }} .dot {{ display:none }} table {{ font-size:12px }} }}
</style>
</head>
<body><main>
<header><div><div class="eyebrow">QC-TEAM / SEALED RUN EVIDENCE</div><h1>{escaped(manifest['run_id'])}</h1></div>
<div><div class="status">● {escaped(manifest['status'])}</div><div class="muted">mode: {escaped(manifest['mode'])}</div></div></header>
{warning}
<div class="metrics">
<div class="metric"><strong>{completed_tasks}/{len(manifest['tasks'])}</strong>tasks completed</div>
<div class="metric"><strong>{passed_gates}/{len(manifest['gates'])}</strong>gates passed</div>
<div class="metric"><strong>{len(manifest['artifacts'])}</strong>hashed artifacts</div>
<div class="metric"><strong>{len(events)}</strong>timeline events</div>
</div>
<section><h2>Frozen baseline</h2><code>{escaped(manifest['baseline']['sha256'])}</code><div class="muted">{escaped(manifest['baseline']['frozen_path'])}</div></section>
<section><h2>Task state</h2><div class="cards">{task_cards}</div></section>
<section><h2>Release gates</h2><table><thead><tr><th>Gate</th><th>Status</th><th>Evidence locator</th></tr></thead><tbody>{gate_rows}</tbody></table></section>
<section><h2>Artifact ledger</h2><table><thead><tr><th>Kind</th><th>Path</th><th>SHA-256</th></tr></thead><tbody>{artifact_rows}</tbody></table></section>
<section><h2>Execution timeline</h2><ol>{timeline}</ol></section>
</main></body></html>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a QC evidence run as HTML")
    parser.add_argument("run_dir")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render(args.run_dir), encoding="utf-8")
        print(output)
        return 0
    except (EvidenceError, OSError, ValueError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
