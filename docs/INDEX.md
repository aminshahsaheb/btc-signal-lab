# Documentation index and maintenance rules

This page says which document is the source of truth for what, which documents are historical records, and how drift is prevented.
It is checked by `scripts/check_docs.py` (every top-level file under the repository root and `docs/` must have a row here).

## Rules that keep the documents consistent

1. **Current state lives in one place: [`STATUS.md`](STATUS.md).** README, ROADMAP and every other living document link to it. They do not copy commit SHAs, tree or inventory counts, or PR heads, because each of those is stale after the next merge.
2. **The master checklist is [`ROADMAP.md`](ROADMAP.md).** An item is ticked only with evidence: the exact commit SHA and a CI run on that commit (or a linked review). Implemented-but-not-independently-reviewed work is marked `[~]`, never `[x]`.
3. **Dated records are never rewritten, only superseded.** A document that describes an old state gets a `HISTORICAL` banner in its first lines and a pointer to `STATUS.md`; its body stays as it was.
4. **A snapshot that cannot be avoided is dated and lives in a record** (`docs/reviews/`, the ledger), not in a living document.
5. **Run the checks before every push:** `bash scripts/check_all.sh` (integrity manifests, inventory, archive screening, docs structure, mirror equality, and the synthetic D-LIQ suites). CI runs the same repository-level checks.
6. **Nothing here is research evidence.** Passing a check confirms file identity, structure, or the tested synthetic fixtures. It does not establish a trading edge, a TradingView compile, a live-feed property, or rights clearance.

## Classes

| Class | Meaning |
|---|---|
| LIVING | Maintained; must agree with `STATUS.md`. |
| HISTORICAL | A dated state that has been superseded. Banner required; body preserved. |
| RECORD | A dated review, decision, or audit that is accurate for its date. Never edited except to add a correction note. |
| GENERATED | Produced by a script; do not edit by hand. |

## Top-level files

| Path | Class | Role |
|---|---|---|
| `README.md` | LIVING | Front door (English): what the project is, layout, how to verify. |
| `README_FA.md` | LIVING | Front door (Persian). |
| `CONTRIBUTING.md` | LIVING | Rules for changing research artifacts. |
| `SECURITY.md` | LIVING | What must never be committed. |
| `docs/INDEX.md` | LIVING | This page. |
| `docs/STATUS.md` | LIVING | **Single source of truth for current state and blockers.** |
| `docs/ROADMAP.md` | LIVING | **Master checklist with evidence and owner decisions.** |
| `docs/RESEARCH_RULES.md` | LIVING | The ten research rules. |
| `docs/DATA_POLICY.md` | LIVING | What data and artifacts are included or excluded. |
| `docs/PUBLISHING.md` | LIVING | Public visibility safeguards and verification commands. |
| `docs/PROJECT_MAP.md` | LIVING | The four separate layers (Move-Odds, D-LIQ, Risk-First, Execution). |
| `docs/ARTIFACT_REGISTER.md` | LIVING | Register of archived artifacts and their caveats. |
| `docs/FILE_INVENTORY_SHA256.csv` | GENERATED | `python3 scripts/generate_inventory.py` (every file except itself). |
| `artifacts/SHA256SUMS.txt` | GENERATED | Pinned source hashes; update only when a pinned file changes. |
| `docs/EXECUTION_LEDGER_2026-11-04.md` | HISTORICAL | Append-only dated ledger of the 2026-11-03..05 audit and PR queue. Its counts are snapshots. |
| `docs/EXECUTION_PLAN_2026-11-03.md` | HISTORICAL | First repository-wide plan; superseded by `ROADMAP.md`. |
| `docs/REMOTE_SYNC_CHECKLIST.md` | HISTORICAL | 2026-11-03 sync audit (states the repository was Private; it is Public). |
| `docs/UPLOAD_MANIFEST.md` | HISTORICAL | 2026-10-30 upload manifest (27-file state). |
| `docs/PROJECT_AUDIT_2026-10-30.md` | RECORD | Source inventory and exclusions at the time of the first audit. |
| `docs/ATLAS_REPRODUCIBILITY_RUN_2026-10-30.md` | RECORD | Atlas pipeline reproduction record. |
| `docs/BTCUSDT_5M_DATA_AUDIT_2026-10-30.md` | RECORD | Dataset identity and structure audit. |
| `docs/STRATEGY_RESEARCH_PROGRAM_2026-10-30.md` | RECORD | Strategy research program v1 (Persian). |
| `docs/STRATEGY_RESEARCH_PROGRAM_UPDATE_2026-11-03.md` | RECORD | Status amendment to the program. |
| `docs/VISIBILITY_CORRECTION_2026-11-04.md` | RECORD | Records that the repository is Public. Still accurate. |
| `docs/A3_FILE_CLASSIFICATION_2026-11-04.csv` | RECORD | Path classification for the A3 screening (2 of 6 steps complete). |

## Directories

| Path | Class | Role |
|---|---|---|
| `docs/reviews/*` | RECORD | Independent reviews, blocker lists, status records (dated). |
| `docs/decisions/*` | RECORD | Dated path decisions. |
| `docs/archive/*` | RECORD | Historical context and the Persian Atlas report. |

## Where each kind of file lives (canonical locations)

| Kind | Canonical location | Legacy mirror (guarded, to be retired by owner decision D-STRUCT-1 in `ROADMAP.md`) |
|---|---|---|
| Protocol / spec drafts | `specs/` | `research/d-liq/`, `research/forward-journal/` |
| Decisions, reviews, archive notes | `docs/decisions/`, `docs/reviews/`, `docs/archive/` | `research/decisions/`, `research/reviews/`, `research/archive/` |
| Pine sources and Move-Odds package | `tools/` | `pine/` |
| Experimental code packages (synthetic) | `research/d-liq/r*/` (for example `r4-draft/`) | none |
| Integrity and maintenance scripts | `scripts/` | none |

`scripts/check_mirrors.py` fails if a mirrored copy drifts from its canonical copy, or if a new file appears in a legacy mirror tree without being registered. Edit the canonical copy only.
