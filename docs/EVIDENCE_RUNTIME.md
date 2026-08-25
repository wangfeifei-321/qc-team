# QC-Team evidence runtime

`qc_evidence.py` supplies the state and evidence layer that the original
single-pass script did not have. It records four things for every run:

- a frozen input file and its SHA-256;
- every legal task transition in `events.jsonl`;
- gate decisions with an evidence locator;
- copied output artifacts and their SHA-256 values.

At completion, `seal.json` records the SHA-256 of both `manifest.json` and
`events.jsonl`. Verification therefore detects later edits to the result or its
timeline. This is tamper-evident, not a cryptographic signature; a trusted CI or
human should retain the seal separately for stronger provenance.

A run cannot become `COMPLETED` while any task is unfinished or any required
gate is blocked. A completed run is immutable. `python3 qc_evidence.py verify
RUN_DIR` recalculates the baseline and artifact hashes and exits non-zero if a
file has changed.

The runtime does not claim that an Agent Team ran merely because entries exist
in the ledger. Native Agent Team messages, shared tasks, and member state must
be captured separately. Likewise, `claude agents` proves that background
sessions are observable; it does not prove team collaboration.

## Failure-and-recovery acceptance test

The automated test exercises this exact sequence:

```text
READY -> RUNNING -> BLOCKED
                    |
                    v
                 READY -> RUNNING -> COMPLETED
```

It first attempts completion while a task and gates are blocked. The runtime
records `COMPLETION_REJECTED`. After a source locator is supplied, the task is
rerun, its artifact is hashed, both gates pass, and the run records
`RUN_COMPLETED`.

Run the complete package test suite:

```bash
python3 -m unittest discover -s tests -v
```

Create a deterministic, explicitly labelled demonstration run without calling
external models or APIs:

```bash
python3 qc_evidence.py demo samples/demo_稿件样例.txt \
  --run-id classroom-failure-recovery
```

The resulting manifest has `"mode": "demonstration"`. It must not be presented
as evidence that Claude, Codex, MiniMax, DIP, or an Agent Team actually ran. Its
purpose is to prove the controller's blocking and recovery behavior before a
live workflow uses the same ledger.

## Audited production adapter

`scripts/run_audited_qc.py` wraps the current Crossref, Claude, Codex, and
MiniMax calls. Claude and Codex receive the same frozen manuscript and reference
evidence, but neither receives the other's first-pass review. Their two hashed
outputs meet only at the synthesis step.

For a DIP handoff, provide the frozen upstream manifest explicitly:

```bash
python3 scripts/run_audited_qc.py manuscript.docx \
  --upstream-manifest /path/to/frozen-dip-run/manifest.json
```

Use `--standalone` only when the input did not come from DIP. The manifest then
records that provenance choice instead of implying a DIP handoff occurred.
