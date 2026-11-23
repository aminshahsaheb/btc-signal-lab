#!/usr/bin/env python3
"""Strategy tester: a TradingView-style report (trade list, profit/loss, equity, drawdown) computed outside TradingView, on public Binance spot data.

Part A  Exact replay of btc-decision-engine ALERT_RULES_v1 "Alert B" (BREAK20D) on BTCUSDT 1h/1d spot history: every alert the rule would have sent (24 h cooldown per side),
        its outcome (stop 1R / target 2R / 168 h limit, stop first if both in one bar, cost 0.16% of the reference price), per-side statistics, an equity curve at fixed
        risk, a same-exit-rules baseline with entries unrelated to the signal, and a reproduction check against the alerts the live bot actually sent.
Part B  The FROZEN Trend Setup v0 rule (trendsetup.py, unchanged): trade episodes per coin (a trade = a run of non-zero weight) and the equal-weight portfolio equity for
        BTC alone, the 7 first coins and all 26 coins, against holding.
Part C  Today's table for the 7 coins and the signal changes of the last 60 days.

Everything here is description of the past. The rules were seen on (parts of) this history, so a good past is not evidence; a bad past can reject a rule. Nothing is certified.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import math
import sys
import time
import urllib.error
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backtest_report as B  # noqa: E402
import robustness_report as RB  # noqa: E402
import trendsetup as T  # noqa: E402

H_MS = 3_600_000
DAY = T.DAY_MS
COOLDOWN_MS = 24 * H_MS
LIMIT_H = 168
COST_FRAC = 0.0016  # ALERT_RULES_v1: cost 0.16 percent of the reference price
RISK_FRAC = 0.005  # the alert message tells the user: risk per trade at most 0.5%
LIVE_START_MS = int(calendar.timegm((2026, 11, 15, 0, 0, 0)) * 1000)  # rules v1 frozen 2026-11-15, before the first live alert
FROM_2023_MS = int(calendar.timegm((2023, 1, 1, 0, 0, 0)) * 1000)
COINS7 = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "LTCUSDT", "TRXUSDT")  # the first 7 of T.UNIVERSE
BASELINE_STEP_H = 24  # baseline: one entry every 24 hours, sides alternating

# Alerts that the live bot actually sent (public alert-log branch of btc-decision-engine, and the owner's Telegram screenshot, read by eye).
LIVE_ALERTS = (
    dict(name="alert-log row (sent 2026-11-20T18:30:59Z)", side="SHORT", bar_open_ms=1795186800000, ref=59475.47, level=61428.26, atr=2642.3393215803358,
         stop=62117.80932158034, target=54190.79135683933, tol=1e-4, source="alerts.csv on the alert-log branch"),
    dict(name="Telegram screenshot (not in the public log)", side="SHORT", bar_open_ms=None, ref=61542.0, level=None, atr=None, stop=64183.6, target=56258.9, tol=0.5,
         source="owner's screenshot, numbers read by eye (1 decimal)"),
)


# ----------------------------------------------------------------------------- data
def _page_iv(symbol, interval, start_ms, end_ms, http_get, hosts, retries, sleep):
    last = None
    for host in hosts:
        url = f"https://{host}/api/v3/klines?symbol={symbol}&interval={interval}&startTime={start_ms}&endTime={end_ms - 1}&limit=1000"
        for attempt in range(retries):
            try:
                data = json.loads(http_get(url))
                if isinstance(data, list):
                    return data
                last = f"{host}: unexpected payload {str(data)[:80]}"
            except (urllib.error.URLError, OSError, ValueError) as e:
                last = f"{host}: {type(e).__name__} {e}"
            sleep(1.0 * (attempt + 1))
    raise T.DataError(f"{symbol} {interval}: all hosts failed ({last})")


def fetch_interval(symbol, interval, ms, start_ms, end_ms, now_ms, http_get=T.default_http_get, hosts=T.HOSTS, retries=3, sleep=time.sleep):
    """Closed bars only (close time before now_ms). Returns arrays t (open), o, h, l, c, close_ms, plus the number of missing bars."""
    rows, cur = [], start_ms
    while cur < end_ms:
        page = _page_iv(symbol, interval, cur, end_ms, http_get, hosts, retries, sleep)
        if not page:
            break
        rows += [r for r in page if start_ms <= int(r[0]) < end_ms]
        last_open = int(page[-1][0])
        if len(page) < 1000 or last_open < cur:
            break
        cur = last_open + ms
        sleep(0.1)
    return validate_bars(symbol, rows, ms, now_ms)


def validate_bars(symbol, rows, ms, now_ms):
    if not rows:
        raise T.DataError(f"{symbol}: no rows")
    try:
        t = np.array([int(r[0]) for r in rows], dtype=np.int64)
        o, h, l, c = (np.array([float(r[k]) for r in rows]) for k in (1, 2, 3, 4))
    except (TypeError, ValueError, IndexError) as e:
        raise T.DataError(f"{symbol}: malformed row ({e})")
    keep = t + ms - 1 < now_ms
    t, o, h, l, c = t[keep], o[keep], h[keep], l[keep], c[keep]
    if len(t) == 0:
        raise T.DataError(f"{symbol}: no closed bars")
    if not np.all(np.isfinite([o, h, l, c])) or (np.minimum.reduce([o, h, l, c]) <= 0).any():
        raise T.DataError(f"{symbol}: non-positive or non-finite price")
    if (h < np.maximum(o, c)).any() or (l > np.minimum(o, c)).any():
        raise T.DataError(f"{symbol}: inconsistent OHLC bar")
    dt = np.diff(t)
    if (dt < ms).any() or (t % ms != 0).any():
        raise T.DataError(f"{symbol}: duplicate, unordered or misaligned timestamps")
    return dict(symbol=symbol, t=t, o=o, h=h, l=l, c=c, close_ms=t + ms - 1, missing=int(((dt // ms) - 1).sum()))


def array_hash(d):
    hh = hashlib.sha256()
    for k in ("t", "o", "h", "l", "c"):
        hh.update(np.ascontiguousarray(d[k]).tobytes())
    return hh.hexdigest()


def iso_ms(ms):
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(int(ms) / 1000))


# ----------------------------------------------------------------------------- Part A: exact replay of Alert B
def atr14(h, l, c):
    """Wilder ATR14 exactly as scripts/alerts.py: TR[0] = high-low; first value at index 14 = mean(TR[1..14]); then (13*ATR + TR)/14."""
    n = len(c)
    out = np.full(n, np.nan)
    if n <= 14:
        return out
    tr = [float(h[0] - l[0])]
    for i in range(1, n):
        pc = float(c[i - 1])
        tr.append(max(float(h[i] - l[i]), abs(float(h[i]) - pc), abs(float(l[i]) - pc)))
    a = sum(tr[1:15]) / 14.0
    out[14] = a
    for i in range(15, n):
        a = (a * 13.0 + tr[i]) / 14.0
        out[i] = a
    return out


def replay_alert_b(h1, d1, cooldown_ms=COOLDOWN_MS):
    """Every BREAK20D alert the frozen rules would have sent over the whole history, assuming the bot sees every closed 1h bar.
    20 daily bars = the last 20 daily bars whose close time is before the 1h bar's close time; R = ATR14 of the daily bars completed at that time."""
    atr = atr14(d1["h"], d1["l"], d1["c"])
    done = np.searchsorted(d1["close_ms"], h1["close_ms"], side="left")
    last_sent = {"LONG": None, "SHORT": None}
    events = []
    for j in range(1, len(h1["c"])):
        k = int(done[j])
        if k < 21:
            continue
        a = atr[k - 1]
        if not np.isfinite(a) or a <= 0:
            continue
        hi, lo = float(d1["h"][k - 20:k].max()), float(d1["l"][k - 20:k].min())
        prev, cur = float(h1["c"][j - 1]), float(h1["c"][j])
        if prev <= hi < cur:
            side, level = "LONG", hi
        elif prev >= lo > cur:
            side, level = "SHORT", lo
        else:
            continue
        opn = int(h1["t"][j])
        ls = last_sent[side]
        if ls is not None and 0 < opn - ls < cooldown_ms:
            continue
        last_sent[side] = opn
        a = float(a)
        stop = cur - a if side == "LONG" else cur + a
        target = cur + 2 * a if side == "LONG" else cur - 2 * a
        events.append(dict(j=j, side=side, bar_open_ms=opn, close_ms=int(h1["close_ms"][j]), ref=cur, level=level, atr=a, stop=stop, target=target))
    return events


def resolve(ev, h1, cost_frac=COST_FRAC, limit_h=LIMIT_H):
    """Outcome from the 1h bars after the alert bar: first touch of stop or target (stop first if both in one bar), else exit at the close 168 h after the reference close.
    Entry at the reference price. r_net = (pnl - cost_frac * ref) / R. PENDING while the 168 h window is not complete and nothing was touched."""
    j, side, ref, R, stop, target = ev["j"], ev["side"], ev["ref"], ev["atr"], ev["stop"], ev["target"]
    t0 = int(h1["t"][j])
    end_open = t0 + limit_h * H_MS
    n = len(h1["t"])
    lo_i = j + 1
    hi_i = int(np.searchsorted(h1["t"], end_open, side="right"))
    out = dict(ev)
    out["gap"] = False
    for i in range(lo_i, hi_i):
        hh, ll = float(h1["h"][i]), float(h1["l"][i])
        if side == "LONG":
            hit_stop, hit_target = ll <= stop, hh >= target
        else:
            hit_stop, hit_target = hh >= stop, ll <= target
        if hit_stop or hit_target:
            if hit_stop:
                status, px, pnl = "STOP", stop, -R
                out["both_touched"] = bool(hit_target)
            else:
                status, px, pnl = "TARGET", target, 2 * R
                out["both_touched"] = False
            return _fill(out, status, px, pnl, int(h1["t"][i]), (int(h1["t"][i]) - t0) / H_MS, ref, R, cost_frac)
    window_done = hi_i < n or (hi_i > lo_i and int(h1["t"][hi_i - 1]) == end_open)
    if not window_done or hi_i <= lo_i:
        out.update(status="PENDING", exit_ms=None, exit_price=None, hours=None, r_gross=None, r_net=None, both_touched=False)
        return out
    i = hi_i - 1
    px = float(h1["c"][i])
    pnl = px - ref if side == "LONG" else ref - px
    out["gap"] = int(h1["t"][i]) != end_open
    out["both_touched"] = False
    return _fill(out, "EXPIRED", px, pnl, int(h1["close_ms"][i]), (int(h1["close_ms"][i]) + 1 - (t0 + H_MS)) / H_MS, ref, R, cost_frac)


def _fill(out, status, px, pnl, exit_ms, hours, ref, R, cost_frac):
    out.update(status=status, exit_price=float(px), exit_ms=int(exit_ms), hours=float(hours), r_gross=float(pnl / R), r_net=float((pnl - cost_frac * ref) / R))
    return out


def baseline_events(h1, d1, step_h=BASELINE_STEP_H):
    """Entries unrelated to any signal: every step_h-th 1h bar, sides alternating, same R definition (daily ATR14 of completed daily bars), same stop/target/limit.
    It shows what the exit rules and costs alone give, so the alert result can be read against it."""
    atr = atr14(d1["h"], d1["l"], d1["c"])
    done = np.searchsorted(d1["close_ms"], h1["close_ms"], side="left")
    ev, k_side = [], 0
    for j in range(1, len(h1["c"]), step_h):
        k = int(done[j])
        if k < 21 or not np.isfinite(atr[k - 1]) or atr[k - 1] <= 0:
            continue
        side = "LONG" if k_side % 2 == 0 else "SHORT"
        k_side += 1
        ref, a = float(h1["c"][j]), float(atr[k - 1])
        ev.append(dict(j=j, side=side, bar_open_ms=int(h1["t"][j]), close_ms=int(h1["close_ms"][j]), ref=ref, level=None, atr=a,
                       stop=ref - a if side == "LONG" else ref + a, target=ref + 2 * a if side == "LONG" else ref - 2 * a))
    return ev


def trade_stats(trades, risk_frac=RISK_FRAC):
    """TradingView-like numbers over the completed trades (PENDING excluded). Equity: risk_frac of equity risked per trade, trades applied in exit order (overlap not capped)."""
    done = [t for t in trades if t["status"] != "PENDING"]
    n = len(done)
    out = dict(n=n, pending=len(trades) - n)
    if n == 0:
        return out
    r = np.array([t["r_net"] for t in done])
    wins, losses = r[r > 0], r[r <= 0]
    streak = best = 0
    for x in r:
        streak = streak + 1 if x <= 0 else 0
        best = max(best, streak)
    order = sorted(done, key=lambda t: t["exit_ms"])
    eq, peak, maxdd = 1.0, 1.0, 0.0
    for t in order:
        eq *= 1.0 + risk_frac * t["r_net"]
        peak = max(peak, eq)
        maxdd = max(maxdd, (peak - eq) / peak)
    out.update(
        target=sum(t["status"] == "TARGET" for t in done), stop=sum(t["status"] == "STOP" for t in done), expired=sum(t["status"] == "EXPIRED" for t in done),
        pct_profitable=float(len(wins) / n), mean_r=float(r.mean()), median_r=float(np.median(r)), sum_r=float(r.sum()),
        avg_win_r=float(wins.mean()) if len(wins) else None, avg_loss_r=float(losses.mean()) if len(losses) else None,
        profit_factor=float(wins.sum() / -losses.sum()) if len(losses) and losses.sum() < 0 else None,
        best_r=float(r.max()), worst_r=float(r.min()), max_losing_streak=int(best), avg_hours=float(np.mean([t["hours"] for t in done])),
        equity_end=float(eq), equity_maxdd=float(maxdd), risk_frac=risk_frac)
    return out


def sub(trades, lo_ms=None, hi_ms=None, side=None):
    return [t for t in trades if (lo_ms is None or t["bar_open_ms"] >= lo_ms) and (hi_ms is None or t["bar_open_ms"] < hi_ms) and (side is None or t["side"] == side)]


def by_year(trades):
    out = {}
    for y in sorted({time.gmtime(t["bar_open_ms"] / 1000).tm_year for t in trades}):
        ts = [t for t in trades if time.gmtime(t["bar_open_ms"] / 1000).tm_year == y]
        row = {}
        for side in ("LONG", "SHORT"):
            s = trade_stats(sub(ts, side=side))
            row[side] = dict(n=s["n"], sum_r=s.get("sum_r"), mean_r=s.get("mean_r"))
        out[str(y)] = row
    return out


def equity_curve(trades, risk_frac=RISK_FRAC, max_points=400):
    order = sorted([t for t in trades if t["status"] != "PENDING"], key=lambda t: t["exit_ms"])
    pts, eq = [], 1.0
    for t in order:
        eq *= 1.0 + risk_frac * t["r_net"]
        pts.append((int(t["exit_ms"]), eq))
    if len(pts) > max_points:
        idx = np.unique(np.linspace(0, len(pts) - 1, max_points).round().astype(int))
        pts = [pts[i] for i in idx]
    return [[iso_ms(a)[:10], round(b, 5)] for a, b in pts]


def _match(events, live):
    tol = live["tol"]
    near = lambda x, y: abs(x - y) <= (tol * y if tol < 0.01 else tol)
    for e in events:
        if e["side"] != live["side"]:
            continue
        if live["bar_open_ms"] is not None and e["bar_open_ms"] != live["bar_open_ms"]:
            continue
        if near(e["ref"], live["ref"]) and near(e["stop"], live["stop"]) and near(e["target"], live["target"]):
            return e
    return None


def reproduction(events, trades_by_start, raw_events=None, raw_trades_by_start=None):
    """Compare the replay with what the live bot sent. reproduced = a replayed alert (with the 24 h cooldown applied to the replay's own sent alerts) matches the logged numbers
    within tolerance. reproduced_raw = the break itself is found when the cooldown is switched off (a break the replay would have suppressed because of an earlier alert).
    The earlier alert that suppresses it is reported as blocked_by (its bar open), so a missing row in the live log can be told apart from a wrong replay."""
    rows = []
    sent_by_side = {}
    for e in events:
        sent_by_side.setdefault(e["side"], []).append(e["bar_open_ms"])
    for live in LIVE_ALERTS:
        match = _match(events, live)
        raw = _match(raw_events, live) if raw_events is not None else None
        row = dict(name=live["name"], source=live["source"], live_ref=live["ref"], live_stop=live["stop"], live_target=live["target"], reproduced=match is not None,
                   reproduced_raw=(match is not None) or (raw is not None))
        hit, trs = (match, trades_by_start) if match is not None else (raw, raw_trades_by_start)
        if hit is not None and trs is not None:
            tr = trs[hit["bar_open_ms"]]
            row.update(bar_open=iso_ms(hit["bar_open_ms"]) + " UTC", replay_ref=hit["ref"], replay_level=hit["level"], replay_atr=hit["atr"], replay_stop=hit["stop"], replay_target=hit["target"],
                       status=tr["status"], exit_time=iso_ms(tr["exit_ms"]) + " UTC" if tr["exit_ms"] else None, r_net=tr["r_net"], hours=tr["hours"], r_gross=tr["r_gross"])
            if match is None:
                earlier = [x for x in sent_by_side.get(hit["side"], []) if 0 < hit["bar_open_ms"] - x < COOLDOWN_MS]
                row["blocked_by"] = iso_ms(earlier[-1]) + " UTC" if earlier else None
                row["blocked_gap_hours"] = (hit["bar_open_ms"] - earlier[-1]) / H_MS if earlier else None
        rows.append(row)
    return rows


def recent_alerts(trades, since_ms, h1_last_close):
    out = []
    for t in sub(trades, lo_ms=since_ms):
        out.append(dict(bar_open=iso_ms(t["bar_open_ms"]) + " UTC", side=t["side"], ref=t["ref"], level=t["level"], stop=t["stop"], target=t["target"], status=t["status"],
                        exit_time=iso_ms(t["exit_ms"]) + " UTC" if t["exit_ms"] else None, r_net=t["r_net"]))
    return out


def part_a(h1, d1):
    events = replay_alert_b(h1, d1)
    trades = [resolve(e, h1) for e in events]
    by_start = {t["bar_open_ms"]: t for t in trades}
    raw_events = replay_alert_b(h1, d1, cooldown_ms=0)  # every break, no cooldown: only used to explain differences from the live bot
    raw_by_start = {e["bar_open_ms"]: resolve(e, h1) for e in raw_events}
    base = [resolve(e, h1) for e in baseline_events(h1, d1)]
    span_weeks = (int(h1["t"][-1]) - int(d1["t"][0]) + H_MS) / (7 * DAY)
    last365 = int(h1["t"][-1]) - 365 * DAY
    cuts = {"all": (None, None), "before_live": (None, LIVE_START_MS), "since_live": (LIVE_START_MS, None), "from_2023": (FROM_2023_MS, None), "last_365d": (last365, None)}
    stats = {}
    for name, (lo, hi) in cuts.items():
        stats[name] = {side: trade_stats(sub(trades, lo, hi, side)) for side in (None, "LONG", "SHORT")}
        stats[name]["both"] = stats[name].pop(None)
    base_stats = {"all": trade_stats(base), "LONG": trade_stats(sub(base, side="LONG")), "SHORT": trade_stats(sub(base, side="SHORT")), "from_2023": trade_stats(sub(base, FROM_2023_MS))}
    clean = [{k: (v if not isinstance(v, (np.floating, np.integer)) else v.item()) for k, v in t.items() if k != "j"} for t in trades]
    return dict(
        rules="ALERT_RULES_v1 Alert B (BREAK20D), spot BTCUSDT, 1h bars + completed daily bars, 24 h cooldown per side, stop 1R / target 2R / 168 h limit, cost 0.16% of ref, stop first on a shared bar",
        h1=dict(bars=int(len(h1["t"])), first=iso_ms(h1["t"][0]), last=iso_ms(h1["t"][-1]), missing=h1["missing"], sha256=array_hash(h1)[:16]),
        d1=dict(bars=int(len(d1["t"])), first=iso_ms(d1["t"][0])[:10], last=iso_ms(d1["t"][-1])[:10], missing=d1["missing"], sha256=array_hash(d1)[:16]),
        weeks=float(span_weeks), alerts_total=len(trades), alerts_per_week=dict(all=len(trades) / span_weeks, LONG=sum(t["side"] == "LONG" for t in trades) / span_weeks,
                                                                           SHORT=sum(t["side"] == "SHORT" for t in trades) / span_weeks),
        stats=stats, baseline=base_stats, by_year=by_year(trades), equity={"LONG": equity_curve(sub(trades, side="LONG")), "SHORT": equity_curve(sub(trades, side="SHORT")),
                                                                      "both": equity_curve(trades)},
        reproduction=reproduction(events, by_start, raw_events, raw_by_start), raw_breaks=len(raw_events), recent=recent_alerts(trades, int(h1["t"][-1]) - 21 * DAY, int(h1["close_ms"][-1])), trades=clean)


# ----------------------------------------------------------------------------- Part B: trend episodes and equity
def episodes(d, c_side=T.C_SIDE):
    """Trade episodes of the frozen rule for one coin. Position over bar j (open j to open j+1) = weight decided at the close of j-1. An episode = consecutive bars with a
    non-zero weight; its return is the compounded net return on the coin's own capital slice (including the cost of every weight change and of the exit). The last bar has
    no next open: it is marked to its close and an episode still running is reported OPEN. Also returns the per-bar net returns (index j, NaN where not defined)."""
    cc = T.coin_calc(d)
    W, ready = cc["w"], cc["ready"]
    o, c, t = d["o"], d["c"], d["t"]
    n = len(o)
    bar_r = np.full(n, np.nan)
    eps, cur = [], None
    for j in range(2, n):
        w1, w2 = float(W[j - 1]), float(W[j - 2])
        nxt = float(o[j + 1]) if j + 1 < n else float(c[j])
        r = w1 * (nxt / float(o[j]) - 1.0) - c_side * abs(w1 - w2)
        if ready[j - 1] and j + 1 < n:
            bar_r[j] = r
        if w1 > 0:
            if cur is None:
                cur = dict(symbol=d["symbol"], entry_ms=int(t[j]), entry_price=float(o[j]), prod=1.0, wsum=0.0, wmax=0.0, bars=0)
            cur["prod"] *= 1.0 + r
            cur["wsum"] += w1
            cur["wmax"] = max(cur["wmax"], w1)
            cur["bars"] += 1
        elif cur is not None:
            cur["prod"] *= 1.0 + r  # exit cost (weight goes to zero at the open of j)
            eps.append(_close_ep(cur, exit_ms=int(t[j]), exit_price=float(o[j]), status="CLOSED"))
            cur = None
    if cur is not None:
        eps.append(_close_ep(cur, exit_ms=int(t[-1]) + DAY, exit_price=float(c[-1]), status="OPEN"))
    return eps, bar_r


def _close_ep(cur, exit_ms, exit_price, status):
    return dict(symbol=cur["symbol"], entry=iso_ms(cur["entry_ms"])[:10], exit=iso_ms(exit_ms)[:10], status=status, days=cur["bars"], avg_size=cur["wsum"] / cur["bars"], max_size=cur["wmax"],
                entry_price=cur["entry_price"], exit_price=exit_price, price_move=exit_price / cur["entry_price"] - 1.0, ret=cur["prod"] - 1.0, entry_ms=cur["entry_ms"])


def ep_stats(eps):
    done = [e for e in eps if e["status"] == "CLOSED"]
    out = dict(n=len(done), open=len(eps) - len(done))
    if not done:
        return out
    r = np.array([e["ret"] for e in done])
    wins, losses = r[r > 0], r[r <= 0]
    out.update(pct_profitable=float(len(wins) / len(r)), mean_ret=float(r.mean()), avg_win=float(wins.mean()) if len(wins) else None, avg_loss=float(losses.mean()) if len(losses) else None,
               profit_factor=float(wins.sum() / -losses.sum()) if len(losses) and losses.sum() < 0 else None, best=float(r.max()), worst=float(r.min()),
               avg_days=float(np.mean([e["days"] for e in done])), median_days=float(np.median([e["days"] for e in done])))
    return out


def sample_curve(t, r, hold, step=7):
    m = np.isfinite(r) & np.isfinite(hold)
    tt, rr, hh = t[m], r[m], hold[m]
    eq, eh = np.cumprod(1.0 + rr), np.cumprod(1.0 + hh)
    idx = sorted(set(range(0, len(tt), step)) | {len(tt) - 1})
    return [[B.date_of(tt[i]), round(float(eq[i]), 4), round(float(eh[i]), 4)] for i in idx]


def part_b(datas, asof_ms):
    G = T.grid(datas)
    names = G["names"]
    out = dict(baskets={})
    sets = {"BTC": ("BTCUSDT",), "7 coins": tuple(s for s in COINS7 if s in names), "all 26": tuple(names)}
    for label, syms in sets.items():
        cols = [names.index(s) for s in syms]
        R, Hd, E = RB.port(G, cols, min_active=1 if len(cols) == 1 else T.MIN_ACTIVE)
        t = G["t"]
        row = dict(coins=len(cols), symbols=list(syms), full=RB.brief(t, R), hold_full=RB.brief(t, Hd), curve=sample_curve(t, R, Hd), exposure_avg=float(np.nanmean(E)))
        tt, rr = RB.cut(t, R, FROM_2023_MS)
        _, hh = RB.cut(t, Hd, FROM_2023_MS)
        row.update(from_2023=RB.brief(tt, rr), hold_from_2023=RB.brief(tt, hh), yearly=B.yearly(t, R), hold_yearly=B.yearly(t, Hd))
        out["baskets"][label] = row
    all_eps = {s: episodes(datas[s])[0] for s in names}
    out["episodes_btc"] = [{k: v for k, v in e.items() if k != "entry_ms"} for e in all_eps["BTCUSDT"]]
    out["episode_stats"] = {"BTC": ep_stats(all_eps["BTCUSDT"]), "7 coins": ep_stats([e for s in sets["7 coins"] for e in all_eps[s]]), "all 26": ep_stats([e for s in names for e in all_eps[s]])}
    out["episode_stats_by_coin"] = {s: ep_stats(all_eps[s]) for s in sets["7 coins"]}
    out["episodes_7_all"] = [{k: v for k, v in e.items() if k != "entry_ms"} for s in sets["7 coins"] for e in all_eps[s]]
    out["episodes_7_open"] = [{k: v for k, v in e.items() if k != "entry_ms"} for s in sets["7 coins"] for e in all_eps[s] if e["status"] == "OPEN"]
    out["episodes_7_recent"] = sorted(({k: v for k, v in e.items() if k != "entry_ms"} for s in sets["7 coins"] for e in all_eps[s] if e["entry_ms"] >= asof_ms - 120 * DAY), key=lambda e: e["entry"], reverse=True)
    out["episodes_csv_rows"] = [{k: v for k, v in e.items() if k != "entry_ms"} for s in names for e in all_eps[s]]
    return out


# ----------------------------------------------------------------------------- Part C: today
def part_c(datas, asof_ms, days=60):
    syms = [s for s in COINS7 if s in datas]
    sub7 = {s: datas[s] for s in syms}
    rows, n = T.table_rows(sub7, asof_ms)
    table = [dict(symbol=r["symbol"], close=r["close"], states=r["states"], sig=r["sig"], prev_sig=r["prev_sig"], scale=r["scale"], w_eq=r["w_eq"], fresh=r["fresh"], ready=r["ready"],
                  changed=bool(r["ready"] and abs(r["sig"] - r["prev_sig"]) > 1e-9)) for r in rows]
    changes = []
    for s in syms:
        d = datas[s]
        cc = T.coin_calc(d)
        sig, ready = cc["sig"], cc["ready"]
        for i in range(max(1, len(sig) - days), len(sig)):
            if ready[i] and abs(sig[i] - sig[i - 1]) > 1e-9:
                changes.append(dict(symbol=s, decided_at_close=iso_ms(d["t"][i] + DAY - 1)[:10], from_sig=float(sig[i - 1]), to_sig=float(sig[i]), close=float(d["c"][i])))
    changes.sort(key=lambda x: (x["decided_at_close"], x["symbol"]), reverse=True)
    return dict(asof=iso_ms(asof_ms), last_closed_bar=iso_ms(asof_ms - DAY)[:10], active=n, table=table, changes_last_60d=changes)


# ----------------------------------------------------------------------------- driver
def build(h1, d1, datas, asof_ms, notes=None, code_sha=None):
    return dict(version="strategy_tester v1", note="Description of the past on public spot data. The rules were seen on (parts of) this history; nothing here is evidence of future returns.",
                code_sha256=code_sha, asof_ms=int(asof_ms), asof=iso_ms(asof_ms), data_notes=notes, A=part_a(h1, d1), B=part_b(datas, asof_ms), C=part_c(datas, asof_ms))


def summary_md(rep):
    A, Bb, C = rep["A"], rep["B"], rep["C"]
    f = lambda x, p=3: "n/a" if x is None else f"{x:+.{p}f}"
    L = [f"# Strategy tester ({rep['version']}), data to {rep['asof']} UTC", "", "**Description of the past; not evidence. Nothing here is certified.**", "",
         "## A. Alert B replay (BTCUSDT)", f"alerts: {A['alerts_total']} in {A['weeks']:.0f} weeks ({A['alerts_per_week']['all']:.2f}/week; LONG {A['alerts_per_week']['LONG']:.2f}, SHORT {A['alerts_per_week']['SHORT']:.2f})", "",
         "| period | side | n | % profitable | mean R net | sum R | profit factor | equity at 0.5% risk | max DD |", "|---|---|---|---|---|---|---|---|---|"]
    for per, d in A["stats"].items():
        for side in ("LONG", "SHORT", "both"):
            s = d[side]
            if s["n"]:
                L.append(f"| {per} | {side} | {s['n']} | {s['pct_profitable']:.0%} | {f(s['mean_r'])} | {f(s['sum_r'], 1)} | {f(s['profit_factor'], 2)} | {s['equity_end']:.2f} | {s['equity_maxdd']:.0%} |")
    b = A["baseline"]["all"]
    L += ["", f"baseline (same exits, entries unrelated to any signal): n {b['n']}, mean R net {f(b.get('mean_r'))}, % profitable {b.get('pct_profitable', float('nan')):.0%}", "", "### reproduction of the live alerts"]
    for r in A["reproduction"]:
        L.append(f"- {r['name']}: reproduced={r['reproduced']}" + (f", {r['bar_open']}, outcome {r['status']} r_net {f(r['r_net'])} at {r['exit_time']}" if r["reproduced"] else ""))
    L += ["", "## B. Trend rule (frozen)", "| basket | period | CAGR | Sharpe | max DD | hold CAGR | hold max DD |", "|---|---|---|---|---|---|---|"]
    for k, v in Bb["baskets"].items():
        for per, a, h in (("full", v["full"], v["hold_full"]), ("from 2023", v["from_2023"], v["hold_from_2023"])):
            L.append(f"| {k} | {per} | {f(a.get('cagr'))} | {f(a.get('sharpe'), 2)} | {f(a.get('maxdd'))} | {f(h.get('cagr'))} | {f(h.get('maxdd'))} |")
    L += ["", "## C. Today (7 coins)", f"last closed bar {C['last_closed_bar']}; active coins {C['active']}", "| coin | states | signal | prev | % of 7-coin equity |", "|---|---|---|---|---|"]
    for r in C["table"]:
        L.append(f"| {r['symbol']} | {r['states']} | {r['sig']:.1f} | {r['prev_sig']:.1f} | {r['w_eq'] * 100:.1f}% |")
    return "\n".join(L) + "\n"


def encode_chunks(obj, width=3000):
    """gzip + base64 of the JSON, split into lines of `width` characters (a log line of several hundred kB is dropped by the Actions log service)."""
    import base64
    import gzip
    raw = base64.b64encode(gzip.compress(json.dumps(obj, separators=(",", ":")).encode("utf-8"), 9, mtime=0)).decode("ascii")
    return [raw[i:i + width] for i in range(0, len(raw), width)]


def decode_chunks(chunks):
    import base64
    import gzip
    return json.loads(gzip.decompress(base64.b64decode("".join(chunks))).decode("utf-8"))


def write_csv(path, rows):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(",".join(keys) + "\n")
        for r in rows:
            fh.write(",".join("" if r.get(k) is None else str(r.get(k)) for k in keys) + "\n")


def main(argv):
    opts = dict(zip(argv[1::2], argv[2::2]))
    outdir = Path(opts.get("--out", "strategy_tester_out"))
    outdir.mkdir(parents=True, exist_ok=True)
    now_ms = int(opts.get("--now-ms", int(time.time() * 1000)))
    asof = int(opts.get("--asof-ms", now_ms // DAY * DAY))
    h1 = fetch_interval("BTCUSDT", "1h", H_MS, T.START_MS, now_ms, now_ms)
    d1 = fetch_interval("BTCUSDT", "1d", DAY, T.START_MS, now_ms, now_ms)
    datas, notes = T.load_universe(asof)
    rep = build(h1, d1, datas, asof, notes, T.code_sha256())
    rep["run_utc"] = iso_ms(now_ms)
    rep["now_ms"] = now_ms
    trades_csv = rep["A"]["trades"]
    eps_csv = rep["B"].pop("episodes_csv_rows")
    (outdir / "strategy_tester.json").write_text(json.dumps(rep, separators=(",", ":")), encoding="utf-8")
    write_csv(outdir / "alertB_trades.csv", trades_csv)
    write_csv(outdir / "trend_episodes.csv", eps_csv)
    chunks = encode_chunks(rep)
    print(f"TESTER_JSON_BEGIN lines={len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"TJ|{i:04d}|{c}")
    print("TESTER_JSON_END")
    md = summary_md(rep)
    (outdir / "strategy_tester.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
