#!/usr/bin/env python3
"""
fetch_federal_register.py — Pull today's Federal Register entries from
defense, state, treasury, justice, homeland security, and presidential
documents. Output drives a small "In the Federal Register" line in the
Domestic Politics tab and surfaces EOs that RSS often misses.

No API key. Truly unlimited rate per the federalregister.gov docs.

Output: federal_register.json in this script's directory.
Schema:
    {
      "fetched_at_utc": "...",
      "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
      "count": N,
      "entries": [
        {
          "title": "...",
          "type": "Rule|Proposed Rule|Notice|Presidential Document",
          "agency": "Defense Department",
          "publication_date": "YYYY-MM-DD",
          "html_url": "...",
          "is_executive_order": bool,
          "is_proclamation": bool
        },
        ...
      ]
    }

Default window: last 24 hours. EOs and proclamations are flagged so the
build can elevate them above routine rules/notices.

Usage:
    python3 fetch_federal_register.py [--days N] [--out path]
Exit 0 on any successful fetch (even zero results). Exit 1 only on network failure.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

API_BASE = "https://www.federalregister.gov/api/v1/documents.json"
UA = "SWAP-Report/1.0 (+https://theswap.report)"

# Agencies SWAP cares about. Federal Register slug list:
# https://www.federalregister.gov/agencies
AGENCIES = [
    "defense-department",
    "state-department",
    "treasury-department",
    "homeland-security-department",
    "justice-department",
    "executive-office-of-the-president",
    "management-and-budget-office",
    "national-security-council",
]

FIELDS = [
    "title", "type", "html_url", "publication_date",
    "agencies", "presidential_document_number",
    "executive_order_number", "proclamation_number",
]


def fetch(start: str, end: str) -> list[dict]:
    params = [
        ("conditions[publication_date][gte]", start),
        ("conditions[publication_date][lte]", end),
        ("per_page", "100"),
        ("order", "newest"),
    ]
    for a in AGENCIES:
        params.append(("conditions[agencies][]", a))
    for f in FIELDS:
        params.append(("fields[]", f))
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r).get("results", [])


def normalize(raw: list[dict]) -> list[dict]:
    out = []
    for r in raw:
        agencies = r.get("agencies") or []
        agency_name = agencies[0].get("name") if agencies and agencies[0].get("name") else "Unknown"
        eo = r.get("executive_order_number")
        proc = r.get("proclamation_number")
        out.append({
            "title": r.get("title", "").strip(),
            "type": r.get("type", "Notice"),
            "agency": agency_name,
            "publication_date": r.get("publication_date"),
            "html_url": r.get("html_url"),
            "is_executive_order": bool(eo),
            "is_proclamation": bool(proc),
            "executive_order_number": eo,
            "proclamation_number": proc,
        })
    # EOs first, then proclamations, then by publication date (newest first)
    out.sort(key=lambda e: (
        not e["is_executive_order"],
        not e["is_proclamation"],
        e.get("publication_date") or "",
    ), reverse=False)
    # newest pub date should still come first within each tier — re-sort within tiers
    out.sort(key=lambda e: e.get("publication_date") or "", reverse=True)
    out.sort(key=lambda e: (not e["is_executive_order"], not e["is_proclamation"]))
    return out


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    default_out = os.path.join(here, "federal_register.json")

    ap = argparse.ArgumentParser(description="Pull today's Federal Register entries.")
    ap.add_argument("--days", type=int, default=1, help="Lookback window in days (default 1)")
    ap.add_argument("--out", default=default_out)
    args = ap.parse_args()

    today = dt.date.today()
    start = (today - dt.timedelta(days=args.days)).isoformat()
    end = today.isoformat()

    try:
        raw = fetch(start, end)
    except Exception as e:
        sys.stderr.write(f"FAIL: federalregister.gov fetch error: {e}\n")
        return 1

    entries = normalize(raw)
    payload = {
        "fetched_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": {"start": start, "end": end},
        "count": len(entries),
        "entries": entries,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)

    eos = sum(1 for e in entries if e["is_executive_order"])
    procs = sum(1 for e in entries if e["is_proclamation"])
    print(f"OK: {len(entries)} entries ({eos} EOs, {procs} proclamations) in window {start}..{end}. Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
