#!/usr/bin/env python3
"""Build D-LIQ r3 slots.csv from a v2 journal and two verifier reports.

DRAFT implementation for review only. It does not connect to an exchange or anchor.
It refuses analysis CSV output when the verifier registry is hard-failed, when
verifiers disagree, or when any grid slot is still pending.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from decimal import Decimal, InvalidOperation

GRID_MS = 4 * 60 * 60 * 1000
ENTRY_DELAY_MS = 5 * 60 * 1000
PRIOR_WINDOW_MS = 15 * 60 * 1000
GENESIS = b"DLIQ-JOURNAL-v2-GENESIS"
HARD_NAMES = {
    "BAD_ENCODING", "NOT_CANONICAL", "BAD_EVENT", "RAW_HASH_MISMATCH",
    "SEQ_GAP", "HEAD_MISMATCH", "RECEIPT_INVALID", "CHECKPOINT_ORDER",
    "TRUNCATION_OR_REPLACEMENT", "SLOT_OFF_GRID", "SLOT_HAS_OUTCOME_FIELDS",
    "DUPLICATE_SLOT", "DUPLICATE_OUTCOME", "OUTCOME_ORPHAN",
    "OUTCOME_BEFORE_ANCHOR", "OUTCOME_TIMING", "OUTCOME_MISMATCH",
    "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH",
}


class BuildError(Exception):
    pass


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _read_journal(path):
    raw = open(path, "rb").read()
    if raw and not raw.endswith(b"\n"):
        raise BuildError("journal has a torn final line; repair and re-verify first")
    lines = raw.splitlines()
    events = []
    head = hashlib.sha256(GENESIS).digest()
    for n, line in enumerate(lines, 1):
        try:
            ev = json.loads(line.decode("ascii"))
        except Exception as exc:
            raise BuildError("journal line %d is not valid ASCII JSON: %s" % (n, exc))
        if not isinstance(ev, dict):
            raise BuildError("journal line %d is not an object" % n)
        canonical = json.dumps(ev, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
        if canonical != line:
            raise BuildError("journal line %d is not canonical" % n)
        if ev.get("seq") != n:
            raise BuildError("journal sequence is not contiguous at line %d" % n)
        head = hashlib.sha256(head + line).digest()
        events.append(ev)
    return raw, events, head.hex()


def _load_report(path, journal_head, event_count):
    raw = open(path, "rb").read()
    try:
        report = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise BuildError("invalid verifier report %s: %s" % (path, exc))
    if report.get("head_hex") != journal_head:
        raise BuildError("verifier report %s does not match journal head" % path)
    if report.get("n_events") != event_count:
        raise BuildError("verifier report %s has wrong event count" % path)
    if not isinstance(report.get("slots"), dict):
        raise BuildError("verifier report %s has no slots map" % path)
    return report, _sha256(raw)


def _normalize_map(value):
    out = {}
    for key, status in value.items():
        try:
            tau = int(key)
        except Exception:
            raise BuildError("verifier slots map has a non-integer tau key")
        if status not in ("OK", "LATE", "UNANCHORED", "PENDING"):
            raise BuildError("unknown verifier slot status %r" % status)
        if tau in out:
            raise BuildError("duplicate tau in verifier slots map")
        out[tau] = status
    return out


def _normalize_missing(value):
    try:
        return sorted(set(int(x) for x in value))
    except Exception:
        raise BuildError("verifier missing list is invalid")


def _decimal(value, label):
    if not isinstance(value, str):
        raise BuildError("%s must be a decimal string" % label)
    try:
        d = Decimal(value)
    except InvalidOperation:
        raise BuildError("%s is not a decimal" % label)
    if not d.is_finite():
        raise BuildError("%s is not finite" % label)
    return d


def _first_candles(events):
    candles = {}
    for ev in events:
        if ev.get("t") == "CANDLE":
            ot = ev.get("open_time_ms")
            op = ev.get("open")
            if isinstance(ot, int) and isinstance(op, str) and ot not in candles:
                candles[ot] = op
    return candles


def _prior_sign(tau, candles):
    p0 = candles.get(tau - PRIOR_WINDOW_MS)
    p1 = candles.get(tau)
    if p0 is None or p1 is None:
        return 0
    a, b = _decimal(p0, "prior candle open"), _decimal(p1, "decision candle open")
    return 1 if b > a else (-1 if b < a else 0)


def build(journal_path, primary_report_path, independent_report_path):
    raw, events, head = _read_journal(journal_path)
    p, p_hash = _load_report(primary_report_path, head, len(events))
    i, i_hash = _load_report(independent_report_path, head, len(events))
    p_slots, i_slots = _normalize_map(p["slots"]), _normalize_map(i["slots"])
    if p_slots != i_slots:
        raise BuildError("verifiers disagree on per-SLOT anchoring status")
    p_missing, i_missing = _normalize_missing(p.get("missing", [])), _normalize_missing(i.get("missing", []))
    if p_missing != i_missing:
        raise BuildError("verifiers disagree on missing grid points")

    hard_names = set(p.get("hard", [])) | set(i.get("hard", []))
    finding_names = {f[0] for r in (p, i) for f in r.get("findings", []) if isinstance(f, list) and f}
    hard_names |= finding_names & HARD_NAMES
    if (p.get("verdict") == "FAIL") != bool(p.get("hard")):
        hard_names.add("VERIFIER_REPORT_INCONSISTENT")
    if (i.get("verdict") == "FAIL") != bool(i.get("hard")):
        hard_names.add("VERIFIER_REPORT_INCONSISTENT")

    slot_events, outcomes = {}, {}
    candles = _first_candles(events)
    for ev in events:
        typ = ev.get("t")
        if typ == "SLOT":
            tau = ev.get("tau_ms")
            if not isinstance(tau, int):
                hard_names.add("BUILDER_BAD_SLOT_TAU")
                continue
            if tau in slot_events:
                hard_names.add("BUILDER_DUPLICATE_SLOT")
            slot_events[tau] = ev
        elif typ == "OUTCOME":
            tau = ev.get("tau_ms")
            if not isinstance(tau, int) or tau in outcomes:
                hard_names.add("BUILDER_DUPLICATE_OR_BAD_OUTCOME")
            else:
                outcomes[tau] = ev

    if not slot_events:
        raise BuildError("journal contains no SLOT events")
    taus = sorted(slot_events)
    if any(t % GRID_MS != 0 for t in taus):
        hard_names.add("BUILDER_SLOT_OFF_GRID")
    first, last = taus[0], taus[-1]
    if (last - first) % GRID_MS:
        hard_names.add("BUILDER_GRID_RANGE_INVALID")
    grid = list(range(first, last + 1, GRID_MS))
    grid_set = set(grid)
    if set(taus) - grid_set:
        hard_names.add("BUILDER_SLOT_OUTSIDE_GRID")
    missing_from_grid = sorted(grid_set - set(slot_events))
    if missing_from_grid != p_missing:
        hard_names.add("VERIFIER_GRID_MISMATCH")

    rows, diagnostics = [], []
    n_unanch = 0
    pending = []
    for idx, tau in enumerate(grid):
        ev = slot_events.get(tau)
        anchor_state = p_slots.get(tau)
        if ev is None:
            row = [idx, "NONE", "", ""]
            ctrl = row + [""]
            reason = "MISSING"
        elif anchor_state is None:
            hard_names.add("BUILDER_SLOT_NOT_IN_VERIFIER")
            row = [idx, "NONE", "", ""]
            ctrl = row + [""]
            reason = "UNVERIFIED_SLOT"
        elif ev.get("status") == "NONE":
            row = [idx, "NONE", "", ""]
            ctrl = row + [""]
            reason = "SIGNAL_NONE"
        elif ev.get("status") != "VALID":
            hard_names.add("BUILDER_UNKNOWN_SLOT_STATUS")
            row = [idx, "NONE", "", ""]
            ctrl = row + [""]
            reason = "BAD_SLOT_STATUS"
        elif anchor_state in ("LATE", "UNANCHORED"):
            n_unanch += 1
            row = [idx, "NONE", "", ""]
            ctrl = row + [""]
            reason = "UNANCHORED"
        elif anchor_state == "PENDING":
            pending.append(tau)
            row = [idx, "PENDING", "", ""]
            ctrl = row + [""]
            reason = "PENDING_ANCHOR"
        elif anchor_state == "OK":
            out = outcomes.get(tau)
            if out is None:
                pending.append(tau)
                row = [idx, "PENDING", "", ""]
                ctrl = row + [""]
                reason = "PENDING_OUTCOME"
            elif out.get("status") == "NO_PRICE":
                side = ev.get("side")
                if side not in (-1, 1):
                    hard_names.add("BUILDER_BAD_SIGNAL_SIDE")
                    row = [idx, "PENDING", "", ""]
                    ctrl = row + [""]
                    reason = "BAD_SIGNAL_SIDE"
                else:
                    row = [idx, "NO_PRICE", side, ""]
                    ctrl = row + [""]
                    reason = "NO_PRICE"
            elif out.get("status") == "EVAL":
                side = ev.get("side")
                r_bps = out.get("r_bps")
                if side not in (-1, 1) or not isinstance(r_bps, str):
                    hard_names.add("BUILDER_BAD_EVAL_FIELDS")
                    row = [idx, "PENDING", "", ""]
                    ctrl = row + [""]
                    reason = "BAD_EVAL_FIELDS"
                else:
                    try:
                        rv = float(r_bps)
                    except Exception:
                        rv = float("nan")
                    if rv != rv or rv in (float("inf"), float("-inf")):
                        hard_names.add("BUILDER_NONFINITE_RETURN")
                        row = [idx, "PENDING", "", ""]
                        ctrl = row + [""]
                        reason = "BAD_RETURN"
                    else:
                        ps = _prior_sign(tau, candles)
                        row = [idx, "EVAL", side, r_bps]
                        ctrl = row + [ps]
                        reason = "EVAL"
            else:
                hard_names.add("BUILDER_UNKNOWN_OUTCOME_STATUS")
                row = [idx, "PENDING", "", ""]
                ctrl = row + [""]
                reason = "BAD_OUTCOME_STATUS"
        else:
            hard_names.add("BUILDER_UNKNOWN_ANCHOR_STATUS")
            row = [idx, "PENDING", "", ""]
            ctrl = row + [""]
            reason = "BAD_ANCHOR_STATUS"
        rows.append(row)
        diagnostics.append({"slot": idx, "tau_ms": tau, "anchor_state": anchor_state,
                            "reason": reason, "status": row[1]})

    n_eval = sum(r[1] == "EVAL" for r in rows)
    n_noprice = sum(r[1] == "NO_PRICE" for r in rows)
    n_none = sum(r[1] == "NONE" for r in rows)
    n_valid = n_eval + n_noprice
    summary = {
        "builder": "build_slots_v1.py DRAFT",
        "journal_sha256": _sha256(raw),
        "journal_head_hex": head,
        "event_count": len(events),
        "primary_verifier_report_sha256": p_hash,
        "independent_verifier_report_sha256": i_hash,
        "verifier_verdicts": [p.get("verdict"), i.get("verdict")],
        "registry_ok": not hard_names,
        "hard_findings": sorted(hard_names),
        "N_grid": len(grid), "N_none": n_none, "N_valid_signal": n_valid,
        "N_eval": n_eval, "N_noprice": n_noprice, "N_unanch": n_unanch,
        "N_missing": len(missing_from_grid), "N_pending": len(pending),
        "missing_tau_ms": missing_from_grid, "pending_tau_ms": pending,
        "diagnostics": diagnostics,
        "analysis_csv_written": False,
        "note": "No verdict is computed by this builder. Run analysis only after registry_ok=true and N_pending=0.",
    }
    return summary, rows, [r + [c[-1]] for r, c in zip(rows, [r + [""] for r in rows])], hard_names, pending


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("journal")
    ap.add_argument("primary_verifier_json")
    ap.add_argument("independent_verifier_json")
    ap.add_argument("--out-prefix", default="slots")
    args = ap.parse_args()
    try:
        summary, primary_rows, _, hard, pending = build(
            args.journal, args.primary_verifier_json, args.independent_verifier_json)
    except BuildError as exc:
        print("BUILD ERROR:", exc, file=sys.stderr)
        return 2
    summary_path = args.out_prefix + ".summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    if hard or pending:
        print(json.dumps({k: summary[k] for k in ("registry_ok", "hard_findings", "N_pending", "N_unanch", "N_missing")}, sort_keys=True))
        print("Refusing analysis CSV: resolve hard findings and pending slots first.", file=sys.stderr)
        return 2
    primary_path = args.out_prefix + ".csv"
    control_path = args.out_prefix + "_with_prior.csv"
    with open(primary_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["slot", "status", "side", "r_bps"]); w.writerows(primary_rows)
    # Rebuild control rows from the primary CSV plus prior-sign diagnostics.
    with open(control_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["slot", "status", "side", "r_bps", "prior_sign"])
        for d, r in zip(summary["diagnostics"], primary_rows):
            prior = ""
            if r[1] == "EVAL":
                # Prior sign is stored in the per-slot diagnostics by build().
                prior = d.get("prior_sign", 0)
            w.writerow(r + [prior])
    summary["analysis_csv_written"] = True
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True); f.write("\n")
    print(json.dumps({k: summary[k] for k in ("registry_ok", "N_grid", "N_eval", "N_noprice", "N_none", "N_unanch", "N_missing")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
