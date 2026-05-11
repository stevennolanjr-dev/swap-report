#!/usr/bin/env python3
"""
fetch_fred.py — Pull the macro indicators SWAP Report references in
the Domestic Politics tab and ticker context.

Series fetched (Fed Funds, 10Y UST, CPI, PCE, Unemployment, Initial
Jobless Claims, Industrial Production, ISM-equivalent). Each series'
latest two observations let us compute period-over-period delta and
flag whether a NEW print landed since the last build.

Output: fred_data.json in this script's directory.
Schema:
    {
      "fetched_at_utc": "...",
      "series": [
        {
          "id": "DFF",
          "label": "Fed Funds Rate",
          "frequency": "Daily",
          "value": 4.33,
          "value_formatted": "4.33%",
          "as_of": "YYYY-MM-DD",
          "previous_value": 4.33,
          "previous_as_of": "YYYY-MM-DD",
          "delta": 0.0,
          "delta_formatted": "+0.00",
          "is_new_print": false,
          "unit": "%",
          "fred_url": "https://fred.stlouisfed.org/series/DFF"
        },
        ...
      ]
    }

API KEY SETUP (one-time, ~2 minutes):
    1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
    2. Create a free account, request an API key (instant approval).
    3. Save the 32-character key in one of:
         a. Environment variable FRED_API_KEY
         b. File at SWAP-Report/.fred-key (chmod 600)
       The script checks env first, then the file.

If no key is configured, the script exits with an actionable message and
the daily build proceeds without macro data (graceful degradation).

Usage:
    python3 fetch_fred.py [--out path]
Exit 0 on success OR no-key (degraded). Exit 1 on network/API failure with key set.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

# Series SWAP Report cares about. Ordered by display priority.
# https://fred.stlouisfed.org/docs/api/fred/series.html
SERIES = [
    # (id, label, format_template, unit_label)
    ("DFF",        "Fed Funds Rate",          "{:.2f}%",  "%"),
    ("DGS10",      "10Y UST",                 "{:.2f}%",  "%"),
    ("DGS2",       "2Y UST",                  "{:.2f}%",  "%"),
    ("CPIAUCSL",   "CPI (headline, SA)",      "{:.1f}",   "Index 1982-84=100"),
    ("CPILFESL",   "Core CPI",                "{:.1f}",   "Index 1982-84=100"),
    ("PCEPI",      "PCE Price Index",         "{:.1f}",   "Index 2017=100"),
    ("UNRATE",     "Unemployment Rate",       "{:.1f}%",  "%"),
    ("ICSA",       "Initial Jobless Claims",  "{:,.0f}",  "Persons"),
    ("INDPRO",     "Industrial Production",   "{:.1f}",   "Index 2017=100"),
    ("DEXUSEU",    "USD/EUR",                 "{:.4f}",   "Rate"),
]


def load_api_key(here: str) -> str | None:
    key = os.environ.get("FRED_API_KEY", "").strip()
    if key:
        return key
    keyfile = os.path.join(os.path.dirname(here), ".fred-key")
    if os.path.exists(keyfile):
        try:
            return open(keyfile).read().strip()
        except Exception:
            return None
    return None


def fetch_series(series_id: str, key: str) -> list[dict]:
    """Get the last 2 observations for delta calculation."""
    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 2,
    }
    url = f"https://api.stlouisfed.org/fred/series/observations?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "SWAP-Report/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r).get("observations", [])


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    default_out = os.path.join(here, "fred_data.json")

    ap = argparse.ArgumentParser(description="Pull FRED macro indicators.")
    ap.add_argument("--out", default=default_out)
    ap.add_argument("--last-build-date", help="ISO date; sets is_new_print flag")
    args = ap.parse_args()

    key = load_api_key(here)
    if not key:
        sys.stderr.write(
            "WARN: no FRED_API_KEY set. Brief will ship without macro indicators.\n"
            "      One-time setup: register a free key at\n"
            "      https://fred.stlouisfed.org/docs/api/api_key.html\n"
            "      then either:\n"
            "        export FRED_API_KEY=<32-char key>\n"
            "      or write it to SWAP-Report/.fred-key (chmod 600).\n"
        )
        # Write empty payload so downstream consumers can detect degraded state.
        with open(args.out, "w") as f:
            json.dump({
                "fetched_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "degraded": True,
                "reason": "no_api_key",
                "series": [],
            }, f, indent=2)
        return 0

    last_build = args.last_build_date  # ISO date string
    out = []
    failures = []
    for sid, label, fmt, unit in SERIES:
        try:
            obs = fetch_series(sid, key)
            if not obs:
                failures.append((sid, "no observations"))
                continue
            cur = obs[0]
            prev = obs[1] if len(obs) > 1 else None
            cur_val = float(cur["value"]) if cur["value"] not in (".", "") else None
            prev_val = float(prev["value"]) if prev and prev["value"] not in (".", "") else None
            if cur_val is None:
                failures.append((sid, "missing current value"))
                continue
            delta = (cur_val - prev_val) if prev_val is not None else None
            is_new = bool(last_build and cur["date"] > last_build)
            entry = {
                "id": sid,
                "label": label,
                "value": cur_val,
                "value_formatted": fmt.format(cur_val),
                "as_of": cur["date"],
                "previous_value": prev_val,
                "previous_as_of": prev["date"] if prev else None,
                "delta": round(delta, 3) if delta is not None else None,
                "delta_formatted": (f"{delta:+.2f}" if delta is not None else None),
                "is_new_print": is_new,
                "unit": unit,
                "fred_url": f"https://fred.stlouisfed.org/series/{sid}",
            }
            out.append(entry)
        except Exception as e:
            failures.append((sid, str(e)[:120]))

    payload = {
        "fetched_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "degraded": False,
        "series_count": len(out),
        "failures": failures,
        "series": out,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)

    if not out:
        sys.stderr.write(f"FAIL: zero series fetched. Failures: {failures}\n")
        return 1
    print(f"OK: {len(out)} series fetched ({len(failures)} failed). Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
