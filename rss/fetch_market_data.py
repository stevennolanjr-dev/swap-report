#!/usr/bin/env python3
"""
fetch_market_data.py — Auto-populate the SWAP Report markets ticker.

Replaces hand-typed values that were drifting daily. Uses yfinance (unofficial
Yahoo Finance scraper). Failure mode is benign: if Yahoo breaks the endpoint,
the script falls back to the last successful fetch from cache so the brief
ships with stale-but-not-fabricated values rather than crashing the build.

Output: market_data.json in the same directory as this script.
Schema:
    {
      "fetched_at_utc": "2026-05-10T19:45:23Z",
      "stale": false,             # true if we fell back to cache
      "session": "weekend",       # "weekend" | "afterhours" | "regular"
      "instruments": [
        {
          "label": "S&P 500",
          "symbol": "^GSPC",
          "value": 7398.93,
          "value_formatted": "7,399",
          "change_pct": 0.84,
          "change_pct_formatted": "+0.84%",
          "direction": "up",      # "up" | "dn" | "flat"
          "session_marker": ""    # "(Fri close)" on weekends, etc.
        },
        ...
      ]
    }

The morning build reads this JSON and renders the ticker block. SWAP no longer
hand-types prices; the only manual cadence is reviewing the resulting HTML.

Usage:
    python3 fetch_market_data.py [--out path/to/market_data.json]
Exit 0 on success (live OR cached). Exit 1 only if cache also unreadable.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from typing import Any

# Ordered as the ticker renders left-to-right.
TICKERS: list[tuple[str, str, str]] = [
    # (label, yahoo_symbol, format_template)
    ("S&P 500",  "^GSPC",     "{:,.0f}"),
    ("DOW",      "^DJI",      "{:,.0f}"),
    ("NASDAQ",   "^IXIC",     "{:,.0f}"),
    ("VIX",      "^VIX",      "{:.1f}"),
    ("WTI",      "CL=F",      "${:,.2f}"),
    ("BRENT",    "BZ=F",      "${:,.2f}"),
    ("GOLD",     "GC=F",      "${:,.0f}"),
    ("10Y UST",  "^TNX",      "{:.2f}%"),
    ("DXY",      "DX-Y.NYB",  "{:.1f}"),
    ("BTC",      "BTC-USD",   "${:,.0f}"),
]


def session_label(now_utc: dt.datetime) -> tuple[str, str]:
    """Returns (session_name, marker_to_show). Times in ET (NYSE)."""
    # Convert UTC -> ET (UTC-5 standard, UTC-4 daylight). Approximation OK.
    et_offset = -4 if (3 < now_utc.month < 12) else -5  # crude DST
    et = now_utc + dt.timedelta(hours=et_offset)
    weekday = et.weekday()  # 0=Mon
    if weekday >= 5:  # Sat/Sun
        return ("weekend", "(Fri close)")
    open_min = 9 * 60 + 30
    close_min = 16 * 60
    cur_min = et.hour * 60 + et.minute
    if cur_min < open_min:
        return ("premarket", "(prev close)")
    if cur_min > close_min:
        return ("afterhours", "(today close)")
    return ("regular", "")


def fetch_live() -> list[dict[str, Any]]:
    """Hit Yahoo. Returns instrument list. Raises on total failure."""
    import yfinance as yf  # local import — keeps script importable for tests

    syms = " ".join(t[1] for t in TICKERS)
    bundle = yf.Tickers(syms)
    out: list[dict[str, Any]] = []
    failures = []
    for label, sym, fmt in TICKERS:
        try:
            fi = bundle.tickers[sym].fast_info
            last = float(fi.last_price)
            prev = float(fi.previous_close)
            chg_pct = (last - prev) / prev * 100 if prev else 0.0
            direction = "up" if chg_pct > 0.05 else ("dn" if chg_pct < -0.05 else "flat")
            chg_str = f"{chg_pct:+.2f}%"
            out.append({
                "label": label,
                "symbol": sym,
                "value": round(last, 4),
                "value_formatted": fmt.format(last),
                "change_pct": round(chg_pct, 3),
                "change_pct_formatted": chg_str,
                "direction": direction,
            })
        except Exception as e:
            failures.append((label, sym, str(e)))
    if not out:
        raise RuntimeError(f"yfinance returned zero usable instruments. Failures: {failures}")
    if failures:
        # Partial success is OK — log to stderr, ship what we have.
        sys.stderr.write(f"WARN: {len(failures)} instrument(s) missing: {failures}\n")
    return out


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    default_out = os.path.join(here, "market_data.json")

    ap = argparse.ArgumentParser(description="Auto-fetch SWAP ticker data.")
    ap.add_argument("--out", default=default_out, help="JSON output path")
    ap.add_argument("--force-cache", action="store_true",
                    help="Skip live fetch; emit cache as-is. Diagnostic.")
    args = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc)
    session, marker = session_label(now)

    # Load cache for fallback
    cache: dict[str, Any] | None = None
    if os.path.exists(args.out):
        try:
            cache = json.load(open(args.out))
        except Exception:
            cache = None

    if args.force_cache:
        if not cache:
            sys.stderr.write("FAIL: --force-cache requested but no cache exists.\n")
            return 1
        print(json.dumps(cache, indent=2))
        return 0

    try:
        instruments = fetch_live()
        for inst in instruments:
            inst["session_marker"] = marker
        payload = {
            "fetched_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stale": False,
            "session": session,
            "instruments": instruments,
        }
        with open(args.out, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"OK: {len(instruments)} instruments fetched live ({session}). Wrote {args.out}")
        return 0
    except Exception as e:
        sys.stderr.write(f"WARN: live fetch failed: {e}\n")
        if cache:
            cache["stale"] = True
            cache["stale_reason"] = str(e)[:200]
            cache["fetched_at_utc"] = cache.get("fetched_at_utc", "unknown")
            with open(args.out, "w") as f:
                json.dump(cache, f, indent=2)
            sys.stderr.write(f"FALLBACK: shipped cache from {cache['fetched_at_utc']}\n")
            return 0
        sys.stderr.write("FAIL: no cache available; build will have no ticker data.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
