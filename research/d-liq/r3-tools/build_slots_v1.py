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
    "OUTCOME_BEFORE_ANCHOR", "OUTCOME_FOR_NONE_SLOT", "OUTCOME_TIMING", "OUTCOME_MISMATCH",
    "OUTCOME_UNLINKED", "CANDLE_CONFLICT", "CANDLE_NOT_LIVE", "SLOT_MISMATCH",
}


class BuildError(Exception):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_journal(path):
    with open(path, "rb") as stream:
        raw = stream.read()
    if raw and not raw.endswith(b"\n"):
        raise BuildError("journal has a torn final line; repair and re-verify first")
    events = []
    head = hashlib.sha256(GENESIS).digest()
    for n, line in enumerate(raw.splitlines(), 1):
        try:
            ev = json.loads(line.decode("ascii"))
            canonical = json.dumps(ev, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=True, allow_nan=False).encode("ascii")
        except Exception as exc:
            raise BuildError("invalid journal line %d: %s" % (n, exc))
        if not isinstance(ev, dict) or canonical != line:
            raise BuildError("journal line %d is not a canonical JSON object" % n)
        if ev.get("seq") != n:
            raise BuildError("journal sequence is not contiguous at line %d" % n)
        head = hashlib.sha256(head + line).digest()
        events.append(ev)
    return raw, events, head.hex()


def load_report(path, journal_head, event_count):
    with open(path, "rb") as stream:
        raw = stream.read()
    try:
        report = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise BuildError("invalid verifier report %s: %s" % (path, exc))
    if not isinstance(report, dict):
        raise BuildError("verifier report %s must be a JSON object" % path)
    if report.get("head_hex") != journal_head:
        raise BuildError("verifier report %s does not match journal head" % path)
    if report.get("n_events") != event_count:
        raise BuildError("verifier report %s has wrong event count" % path)
    if not isinstance(report.get("slots"), dict):
        raise BuildError("verifier report %s has no slots map" % path)
    if not isinstance(report.get("hard"), list) or any(not isinstance(x, str) for x in report["hard"]):
        raise BuildError("verifier report %s has an invalid hard list" % path)
    if not isinstance(report.get("findings"), list) or any(
            not isinstance(f, list) or not f or not isinstance(f[0], str)
            for f in report["findings"]):
        raise BuildError("verifier report %s has invalid findings" % path)
    if not isinstance(report.get("missing", []), list):
        raise BuildError("verifier report %s has an invalid missing list" % path)
    if report.get("verdict") not in ("PASS", "FAIL"):
        raise BuildError("verifier report %s has an invalid verdict" % path)
    return report, sha256(raw)


def normalize_map(value):
    out = {}
    for key, status in value.items():
        if not isinstance(key, str):
            raise BuildError("verifier slots map keys must be strings")
        try:
            tau = int(key)
        except Exception:
            raise BuildError("verifier slots map has a non-integer tau key")
        if str(tau) != key:
            raise BuildError("verifier slots map has a non-canonical tau key")
        if status not in ("OK", "LATE", "UNANCHORED", "PENDING"):
            raise BuildError("unknown verifier slot status %r" % status)
        if tau in out:
            raise BuildError("duplicate tau in verifier slots map")
        out[tau] = status
    return out


def normalize_missing(value):
    if not isinstance(value, list):
        raise BuildError("verifier missing list is invalid")
    out = []
    for x in value:
        if not isinstance(x, int) or isinstance(x, bool):
            raise BuildError("verifier missing entries must be integers")
        out.append(x)
    if out != sorted(out) or len(out) != len(set(out)):
        raise BuildError("verifier missing list must be sorted and unique")
    return out


def decimal_value(value, label):
    if not isinstance(value, str):
        raise BuildError("%s must be a decimal string" % label)
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise BuildError("%s is not a decimal" % label)
    if not result.is_finite():
        raise BuildError("%s is not finite" % label)
    return result


def first_candles(events):
    candles = {}
    for ev in events:
        if ev.get("t") == "CANDLE":
            ot, op = ev.get("open_time_ms"), ev.get("open")
            if isinstance(ot, int) and isinstance(op, str) and ot not in candles:
                candles[ot] = op
    return candles


def prior_sign(tau, candles):
    before = candles.get(tau - PRIOR_WINDOW_MS)
    at = candles.get(tau)
    if before is None or at is None:
        return 0
    p0 = decimal_value(before, "prior candle open")
    p1 = decimal_value(at, "decision candle open")
    return 1 if p1 > p0 else (-1 if p1 < p0 else 0)


def build(journal_path, primary_report_path, independent_report_path):
    raw, events, head = read_journal(journal_path)
    primary, primary_hash = load_report(primary_report_path, head, len(events))
    independent, independent_hash = load_report(independent_report_path, head, len(events))
    primary_slots = normalize_map(primary["slots"])
    independent_slots = normalize_map(independent["slots"])
    if primary_slots != independent_slots:
        raise BuildError("verifiers disagree on per-SLOT anchoring status")
    primary_missing = normalize_missing(primary.get("missing", []))
    independent_missing = normalize_missing(independent.get("missing", []))
    if primary_missing != independent_missing:
        raise BuildError("verifiers disagree on missing grid points")

    hard = set(primary.get("hard", [])) | set(independent.get("hard", []))
    finding_hard = {
        f[0] for report in (primary, independent)
        for f in report.get("findings", [])
        if isinstance(f, list) and f and f[0] in HARD_NAMES
    }
    hard |= finding_hard
    reported_hard = set(primary.get("hard", [])) | set(independent.get("hard", []))
    if reported_hard != finding_hard:
        hard.add("VERIFIER_HARD_LIST_MISMATCH")
    for report in (primary, independent):
        expected = "FAIL" if report.get("hard") else "PASS"
        if report.get("verdict") != expected:
            hard.add("VERIFIER_REPORT_INCONSISTENT")

    slot_events, outcomes = {}, {}
    candles = first_candles(events)
    for ev in events:
        typ = ev.get("t")
        if typ == "SLOT":
            tau = ev.get("tau_ms")
            if not isinstance(tau, int):
                hard.add("BUILDER_BAD_SLOT_TAU")
            elif tau in slot_events:
                hard.add("BUILDER_DUPLICATE_SLOT")
            else:
                slot_events[tau] = ev
        elif typ == "OUTCOME":
            tau = ev.get("tau_ms")
            if not isinstance(tau, int) or tau in outcomes:
                hard.add("BUILDER_DUPLICATE_OR_BAD_OUTCOME")
            else:
                outcomes[tau] = ev

    if not slot_events:
        raise BuildError("journal contains no SLOT events")
    for tau in outcomes:
        source_slot = slot_events.get(tau)
        if source_slot is None:
            hard.add("BUILDER_OUTCOME_ORPHAN")
        elif source_slot.get("status") != "VALID":
            hard.add("BUILDER_OUTCOME_FOR_NONE_SLOT")
    taus = sorted(slot_events)
    if any(t % GRID_MS != 0 for t in taus):
        hard.add("BUILDER_SLOT_OFF_GRID")
    first, last = taus[0], taus[-1]
    if (last - first) % GRID_MS:
        hard.add("BUILDER_GRID_RANGE_INVALID")
    grid = list(range(first, last + 1, GRID_MS))
    grid_set = set(grid)
    if set(taus) - grid_set:
        hard.add("BUILDER_SLOT_OUTSIDE_GRID")
    missing = sorted(grid_set - set(slot_events))
    if missing != primary_missing:
        hard.add("VERIFIER_GRID_MISMATCH")

    primary_rows, control_rows, diagnostics = [], [], []
    pending, n_unanch = [], 0
    for index, tau in enumerate(grid):
        ev = slot_events.get(tau)
        anchor = primary_slots.get(tau)
        prior = ""
        reason = ""
        if ev is None:
            row = [index, "NONE", "", ""]
            reason = "MISSING"
        elif anchor is None:
            hard.add("BUILDER_SLOT_NOT_IN_VERIFIER")
            row = [index, "NONE", "", ""]
            reason = "UNVERIFIED_SLOT"
        elif anchor in ("LATE", "UNANCHORED"):
            if ev.get("status") == "VALID":
                n_unanch += 1
            elif ev.get("status") != "NONE":
                hard.add("BUILDER_UNKNOWN_SLOT_STATUS")
            row = [index, "NONE", "", ""]
            reason = "UNANCHORED"
        elif ev.get("status") == "NONE":
            row = [index, "NONE", "", ""]
            reason = "SIGNAL_NONE"
        elif ev.get("status") != "VALID":
            hard.add("BUILDER_UNKNOWN_SLOT_STATUS")
            row = [index, "PENDING", "", ""]
            reason = "BAD_SLOT_STATUS"
        elif anchor == "PENDING":
            pending.append(tau)
            row = [index, "PENDING", "", ""]
            reason = "PENDING_ANCHOR"
        elif anchor == "OK":
            outcome = outcomes.get(tau)
            if outcome is None:
                pending.append(tau)
                row = [index, "PENDING", "", ""]
                reason = "PENDING_OUTCOME"
            elif outcome.get("status") == "NO_PRICE":
                side = ev.get("side")
                if side not in (-1, 1):
                    hard.add("BUILDER_BAD_SIGNAL_SIDE")
                    row = [index, "PENDING", "", ""]
                    reason = "BAD_SIGNAL_SIDE"
                else:
                    row = [index, "NO_PRICE", side, ""]
                    reason = "NO_PRICE"
            elif outcome.get("status") == "EVAL":
                side, r_bps = ev.get("side"), outcome.get("r_bps")
                if side not in (-1, 1) or not isinstance(r_bps, str):
                    hard.add("BUILDER_BAD_EVAL_FIELDS")
                    row = [index, "PENDING", "", ""]
                    reason = "BAD_EVAL_FIELDS"
                else:
                    try:
                        rv = float(r_bps)
                    except Exception:
                        rv = float("nan")
                    if rv != rv or rv in (float("inf"), float("-inf")):
                        hard.add("BUILDER_NONFINITE_RETURN")
                        row = [index, "PENDING", "", ""]
                        reason = "BAD_RETURN"
                    else:
                        prior = prior_sign(tau, candles)
                        row = [index, "EVAL", side, r_bps]
                        reason = "EVAL"
            else:
                hard.add("BUILDER_UNKNOWN_OUTCOME_STATUS")
                row = [index, "PENDING", "", ""]
                reason = "BAD_OUTCOME_STATUS"
        else:
            hard.add("BUILDER_UNKNOWN_ANCHOR_STATUS")
            row = [index, "PENDING", "", ""]
            reason = "BAD_ANCHOR_STATUS"

        primary_rows.append(row)
        control_rows.append(row + [prior])
        diagnostics.append({
            "slot": index, "tau_ms": tau, "anchor_state": anchor,
            "source_status": ev.get("status") if ev else None,
            "source_reasons": ev.get("reasons", []) if ev else [],
            "reason": reason, "status": row[1],
            "prior_sign": prior if row[1] == "EVAL" else None,
        })

    n_eval = sum(r[1] == "EVAL" for r in primary_rows)
    n_noprice = sum(r[1] == "NO_PRICE" for r in primary_rows)
    n_none = sum(r[1] == "NONE" for r in primary_rows)
    summary = {
        "builder": "build_slots_v1.py DRAFT",
        "journal_sha256": sha256(raw),
        "journal_head_hex": head,
        "event_count": len(events),
        "primary_verifier_report_sha256": primary_hash,
        "independent_verifier_report_sha256": independent_hash,
        "verifier_verdicts": [primary.get("verdict"), independent.get("verdict")],
        "registry_ok": not hard,
        "hard_findings": sorted(hard),
        "N_grid": len(grid), "N_none": n_none,
        "N_valid_signal": n_eval + n_noprice, "N_eval": n_eval,
        "N_noprice": n_noprice, "N_unanch": n_unanch,
        "N_missing": len(missing), "N_pending": len(pending),
        "missing_tau_ms": missing, "pending_tau_ms": pending,
        "diagnostics": diagnostics, "analysis_csv_written": False,
        "note": "This builder does not compute a verdict. Do not run analysis unless registry_ok=true and N_pending=0.",
    }
    return summary, primary_rows, control_rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("journal")
    ap.add_argument("primary_verifier_json")
    ap.add_argument("independent_verifier_json")
    ap.add_argument("--out-prefix", default="slots")
    args = ap.parse_args()
    try:
        summary, primary_rows, control_rows = build(
            args.journal, args.primary_verifier_json, args.independent_verifier_json)
    except BuildError as exc:
        print("BUILD ERROR: %s" % exc, file=sys.stderr)
        return 2

    summary_path = args.out_prefix + ".summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    if summary["hard_findings"] or summary["N_pending"]:
        print(json.dumps({
            "registry_ok": summary["registry_ok"],
            "hard_findings": summary["hard_findings"],
            "N_pending": summary["N_pending"],
            "N_unanch": summary["N_unanch"],
            "N_missing": summary["N_missing"],
        }, sort_keys=True))
        print("Refusing analysis CSV: resolve hard findings and pending slots first.", file=sys.stderr)
        return 2

    with open(args.out_prefix + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["slot", "status", "side", "r_bps"])
        w.writerows(primary_rows)
    with open(args.out_prefix + "_with_prior.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["slot", "status", "side", "r_bps", "prior_sign"])
        w.writerows(control_rows)
    summary["analysis_csv_written"] = True
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({
        "registry_ok": summary["registry_ok"], "N_grid": summary["N_grid"],
        "N_eval": summary["N_eval"], "N_noprice": summary["N_noprice"],
        "N_none": summary["N_none"], "N_unanch": summary["N_unanch"],
        "N_missing": summary["N_missing"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
