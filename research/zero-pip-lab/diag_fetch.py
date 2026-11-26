#!/usr/bin/env python3
"""READ-ONLY fetch diagnostic for the Zero-Pip Lab. It is NOT part of the frozen analysis code and computes no outcome, feature or result.

Run 1 of the scoring workflow stopped with "BTCUSDT unavailable" without printing why (the exclusion reason is only recorded in memory).
This script fetches klines with the frozen fetcher (zeropip.fetch_klines, imported unchanged) and prints, per coin, why the frozen
validation (zeropip.build_series / parse_rows) accepts or rejects the data: counts per failed condition, a few raw rows, ordering and
gap statistics. Usage: python -I -B research/zero-pip-lab/diag_fetch.py [SYMBOL ...]  (default: BTCUSDT ETHUSDT)."""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zeropip as Z  # noqa: E402

H = Z.HOUR_MS


def classify(r):
    t, ct = int(r[0]), int(r[6])
    o, h, l, c, v = (float(r[i]) for i in (1, 2, 3, 4, 5))
    tb = float(r[9])
    why = []
    if t % H:
        why.append("open_time_not_on_the_hour")
    if ct != t + H - 1:
        why.append("close_time_not_open_plus_3599999")
    if not l > 0:
        why.append("low_not_positive")
    if not l <= min(o, c):
        why.append("low_above_min_open_close")
    if not h >= max(o, c):
        why.append("high_below_max_open_close")
    if not v >= 0:
        why.append("negative_volume")
    if not (0 <= tb <= v * (1 + 1e-9) + 1e-12):
        why.append("taker_buy_volume_exceeds_volume")
    return why


def main(symbols):
    for s in symbols:
        print(f"== {s}", flush=True)
        try:
            rows = Z.fetch_klines(s)
        except Exception as e:  # noqa: BLE001  (diagnostic: show anything)
            print("FETCH ERROR:", type(e).__name__, e, flush=True)
            continue
        print("rows:", len(rows), "| first:", json.dumps(rows[0][:7]), "| last:", json.dumps(rows[-1][:7]), flush=True)
        ts = [int(r[0]) for r in rows]
        print("non-increasing steps:", sum(1 for a, b in zip(ts[:-1], ts[1:]) if b <= a),
              "| steps larger than one hour:", sum(1 for a, b in zip(ts[:-1], ts[1:]) if b - a > H),
              "| expected bars from first to END:", (Z.END_MS - ts[0]) // H, flush=True)
        print("open-time remainder mod 1h:", dict(collections.Counter(t % H for t in ts).most_common(3)),
              "| close-open deltas:", dict(collections.Counter(int(r[6]) - int(r[0]) for r in rows).most_common(4)), flush=True)
        reasons = collections.defaultdict(list)
        for r in rows:
            for w in classify(r):
                reasons[w].append(r)
        print("rows failing each condition:", {k: len(v) for k, v in reasons.items()} or "none", flush=True)
        for k, v in reasons.items():
            for r in v[:3]:
                print(f"  example [{k}]:", json.dumps(r), flush=True)
        try:
            S = Z.build_series(s, rows)
            print(f"build_series OK: bars={S['bars']} missing={S['missing']} missing_frac={S['missing'] / len(S['c']):.5f} "
                  f"(limit {Z.CFG['max_missing_frac']})", flush=True)
        except Z.DataError as e:
            print("build_series DataError:", e, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["BTCUSDT", "ETHUSDT"]))
