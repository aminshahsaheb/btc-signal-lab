"""r4 patch 12: builder delta on the CURRENT PR #15 head builder (sha 505ffdcc...): per-OUTCOME coverage cross-check (contract 6.4), mandatory SLOT replay,
pinned message contract, coverage-lag report (OPEN-22). Re-pins the verifiers to the r4 files. usage: python3 p12_builder_delta.py <src builder> <dst builder> <primary_verifier.py> <independent_verifier.py> <msg_contract.py>"""
import hashlib, sys
src, dst, pv, iv, mc = sys.argv[1:6]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
s = open(src, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:90], s.count(a))
    s = s.replace(a, b)

rep('''"""Build D-LIQ r3 slots.csv from a v2 journal and two verifier reports.

DRAFT implementation for review only. It does not connect to an exchange or anchor.
It refuses analysis CSV output when the verifier registry is hard-failed, when
verifiers disagree, or when any grid slot is still pending.
"""''', '''"""Build D-LIQ slots.csv from a v2 journal and two verifier reports (r4-draft delta on the PR #15 builder).

DRAFT implementation for review only. It does not connect to an exchange or anchor.
It refuses analysis CSV output when the verifier registry is hard-failed, when
verifiers disagree, or when any grid slot is still pending.
r4 delta (GPT r3 audit orders 1-3):
  * per-OUTCOME coverage (journal contract 6.4): both verifier reports carry the same `outcomes` map, the builder re-derives the coverage from the raw journal and compares;
    an UNCOVERED OUTCOME is never an EVAL row (PENDING, blocks the CSV; owner decision 2026-11-05);
  * the primary verifier is run WITH the mandatory SLOT replay (`replayed: true`), and the message contract that the replay uses is pinned by hash like the verifiers;
  * the summary reports the coverage status and the lag distribution per OUTCOME (OPEN-22; informative, no cap).
"""''')
rep("import sys\nfrom decimal", "import statistics\nimport sys\nfrom decimal")
rep('PRIMARY_VERIFIER_SHA256 = "816f8d9fd37cc3cfa9001badc6af5a9a69ed025f41ba32a4e5be4b4ef9cbffa5"', 'PRIMARY_VERIFIER_SHA256 = "%s"' % sha(pv))
rep('INDEPENDENT_VERIFIER_SHA256 = "f967c77c825f278961ab361a2d844a561d886c14a57c51938901d87bc84b0650"', 'INDEPENDENT_VERIFIER_SHA256 = "%s"\nMSG_CONTRACT_SHA256 = "%s"' % (sha(iv), sha(mc)))
rep('INDEPENDENT_VERIFIER_PATH = os.path.join(os.path.dirname(__file__), "verifiers", "independent", "verify_indep.py")',
    'INDEPENDENT_VERIFIER_PATH = os.path.join(os.path.dirname(__file__), "verifiers", "independent", "verify_indep.py")\nMSG_CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "verifiers", "primary", "dliq_msg_contract_v1.py")')
rep('"CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH",', '"CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH", "SLOT_EARLY_WRITE",') if '"CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH",' in s else None

# load_report: outcomes map required
rep('''    if report.get("verdict") not in ("PASS", "FAIL"):
        raise BuildError("verifier report %s has an invalid verdict" % path)''', '''    if report.get("verdict") not in ("PASS", "FAIL"):
        raise BuildError("verifier report %s has an invalid verdict" % path)
    if not isinstance(report.get("outcomes"), dict):
        raise BuildError("verifier report %s has no per-OUTCOME coverage map (`outcomes`): produced by a pre-r4 verifier?" % path)''')

rep('''def normalize_missing(value):''', '''def normalize_outcomes(value):
    out = {}
    for key, status in value.items():
        if not isinstance(key, str):
            raise BuildError("verifier outcomes map keys must be strings")
        try:
            tau = int(key)
        except Exception:
            raise BuildError("verifier outcomes map has a non-integer tau key")
        if str(tau) != key:
            raise BuildError("verifier outcomes map has a non-canonical tau key")
        if status not in ("COVERED", "UNCOVERED"):
            raise BuildError("unknown verifier outcome coverage status %r" % (status,))
        if tau in out:
            raise BuildError("duplicate tau in verifier outcomes map")
        out[tau] = status
    return out


def normalize_missing(value):''')

# pinned message contract + replay on
rep('''def run_pinned_verifiers(journal_path, anchor_snapshot_path):
    snapshot, snapshot_hash, anchor = load_anchor_snapshot(anchor_snapshot_path)''', '''def _check_pinned_file(path, expected_hash):
    with open(path, "rb") as stream:
        if sha256(stream.read()) != expected_hash:
            raise BuildError("pinned source hash mismatch: %s" % path)


def run_pinned_verifiers(journal_path, anchor_snapshot_path):
    snapshot, snapshot_hash, anchor = load_anchor_snapshot(anchor_snapshot_path)
    _check_pinned_file(MSG_CONTRACT_PATH, MSG_CONTRACT_SHA256)      # r4: the SLOT replay imports this file from the primary verifier's directory''')
rep('''    primary = primary_module.verify(
        journal_path, anchor, snapshot["journal_id"], snapshot["verify_time_ms"])
    independent = independent_module.verify(''', '''    primary = primary_module.verify(
        journal_path, anchor, snapshot["journal_id"], snapshot["verify_time_ms"], replay_slots=True)   # r4: the replay is mandatory (contract 7.1)
    if primary.get("replayed") is not True:
        raise BuildError("the pinned primary verifier did not run the mandatory SLOT replay")
    independent = independent_module.verify(''')

# outcomes agreement
rep('''    if primary_missing != independent_missing:
        raise BuildError("verifiers disagree on missing grid points")
''', '''    if primary_missing != independent_missing:
        raise BuildError("verifiers disagree on missing grid points")
    primary_outcomes = normalize_outcomes(primary["outcomes"])
    if primary_outcomes != normalize_outcomes(independent["outcomes"]):
        raise BuildError("verifiers disagree on per-OUTCOME coverage")
''')

# own coverage derivation: collect checkpoints
rep('''    slot_events, outcomes = {}, {}
    max_checkpoint_anchored_seq = 0''', '''    slot_events, outcomes = {}, {}
    cps = []                                   # r4: (line, anchored_seq, receipt time_ms or None) of every well-formed checkpoint
    max_checkpoint_anchored_seq = 0''')
rep('''                previous_checkpoint_anchored_seq = anchored_seq
''', '''                previous_checkpoint_anchored_seq = anchored_seq
                rc = ev.get("receipt") if isinstance(ev.get("receipt"), dict) else {}
                cps.append((event_seq, anchored_seq, rc.get("time_ms") if isinstance(rc.get("time_ms"), int) else None))
''')
rep('''    if not slot_events:
        raise BuildError("journal contains no SLOT events")''', '''    # r4: per-OUTCOME coverage derived from the raw journal (contract 6.4) and compared with BOTH verifier reports
    own_cov, coverage_rows = {}, []
    for tau, (j, oev) in sorted(outcomes.items()):
        cover = next(((c, t) for c, k, t in cps if c > j and k >= j), None)
        own_cov[tau] = "COVERED" if cover is not None else "UNCOVERED"
        row = {"tau_ms": tau, "outcome_seq": j, "status": own_cov[tau], "covering_checkpoint_seq": cover[0] if cover else None,
               "lag_events": (cover[0] - j) if cover else None, "lag_ms": None}
        if cover and isinstance(cover[1], int) and isinstance(oev.get("rec_ms"), int):
            row["lag_ms"] = cover[1] - oev["rec_ms"]       # anchor receipt time minus the collector's OUTCOME time (two clocks; informative only)
        coverage_rows.append(row)
    if primary_outcomes != own_cov:
        hard.add("BUILDER_OUTCOME_COVERAGE_MISMATCH")
    lags = [r["lag_ms"] for r in coverage_rows if r["lag_ms"] is not None]
    lag_summary = {"n_covered": sum(r["status"] == "COVERED" for r in coverage_rows),
                   "n_uncovered": sum(r["status"] == "UNCOVERED" for r in coverage_rows),
                   "lag_events_max": max([r["lag_events"] for r in coverage_rows if r["lag_events"] is not None], default=None),
                   "lag_ms_min": min(lags) if lags else None, "lag_ms_median": statistics.median(lags) if lags else None, "lag_ms_max": max(lags) if lags else None}

    if not slot_events:
        raise BuildError("journal contains no SLOT events")''')
rep('''                if outcome_seq > max_checkpoint_anchored_seq:
                    pending.append(tau)''', '''                if own_cov.get(tau) != "COVERED":
                    pending.append(tau)''')
rep('''        "independent_verifier_source_sha256": INDEPENDENT_VERIFIER_SHA256,''', '''        "independent_verifier_source_sha256": INDEPENDENT_VERIFIER_SHA256,
        "message_contract_source_sha256": MSG_CONTRACT_SHA256,
        "primary_replayed": primary.get("replayed") is True,
        "outcome_coverage": coverage_rows, "coverage_lag": lag_summary,''')
rep('"builder": "build_slots_v1.py DRAFT",', '"builder": "build_slots_v2.py DRAFT (r4 delta)",')
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s.splitlines()))
