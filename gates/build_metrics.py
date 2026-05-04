#!/usr/bin/env python3
"""
build_metrics.py — Per-build metrics summary for SWAP Report deploys.

Runs in the GitHub Actions workflow after both structural and URL gates pass.
Emits a markdown table to stdout — designed to be piped into $GITHUB_STEP_SUMMARY
so the metrics show up in the Actions UI without needing to open files.

Also writes status.json to the deploy artifact so theswap.report/status.json
becomes a polling endpoint for at-a-glance build health.

Metrics emitted:
  - Edition date (parsed from index.html title or masthead)
  - Story count (count of .story divs)
  - Deep Reads count (count of .deep-card divs)
  - Outbound link count (unique http(s) hrefs)
  - Image count
  - Archive snapshot count
  - BCC count from email-distribution.json (if accessible)
  - Build timestamp

Usage:
    python3 build_metrics.py path/to/index.html
        Markdown table to stdout. Also writes ./status.json.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser


class Counter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False
        self.story_count = 0
        self.deep_card_count = 0
        self.aged_card_count = 0
        self.signal_card_count = 0
        self.hrefs = set()
        self.imgs = set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        cls = (d.get("class") or "").split()
        if tag == "title":
            self._in_title = True
        if "story" in cls:
            self.story_count += 1
        if "deep-card" in cls:
            self.deep_card_count += 1
        if "aged-card" in cls or "aged-body" in cls:
            self.aged_card_count += 1
        if any(c.startswith("sig-card") for c in cls):
            self.signal_card_count += 1
        if tag == "a":
            href = d.get("href") or ""
            if href.startswith(("http://", "https://")):
                self.hrefs.add(href)
        if tag == "img":
            src = d.get("src") or ""
            if src.startswith(("http://", "https://")):
                self.imgs.add(src)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def archive_count(repo_root: str) -> int:
    archive_dir = os.path.join(repo_root, "archive")
    if not os.path.isdir(archive_dir):
        return 0
    return sum(1 for f in os.listdir(archive_dir)
               if re.match(r'\d{4}-\d{2}-\d{2}\.html$', f))


def bcc_count(repo_root: str) -> int:
    # Look in vault path first (when run locally); fall back to repo path.
    candidates = [
        os.path.normpath(os.path.join(repo_root, "..", "email-distribution.json")),
        os.path.join(repo_root, "email-distribution.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p) as f:
                    d = json.load(f)
                return len(d.get("bcc", []))
            except Exception:
                pass
    return -1  # not available in this context (e.g., GH Actions without vault)


def parse_edition_date(title: str) -> str:
    # Title format: "THE SWAP REPORT — May 4, 2026 (AM)" or similar
    m = re.search(r'(\w+\s+\d{1,2},\s+\d{4})', title or "")
    return m.group(1) if m else "unknown"


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write(f"usage: {sys.argv[0]} <index.html>\n")
        return 2

    html_path = sys.argv[1]
    if not os.path.exists(html_path):
        sys.stderr.write(f"FAIL: {html_path} not found\n")
        return 1

    repo_root = os.path.dirname(os.path.abspath(html_path))

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    p = Counter()
    p.feed(html)

    archives = archive_count(repo_root)
    bccs = bcc_count(repo_root)
    edition = parse_edition_date(p.title)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    file_size_kb = round(len(html.encode("utf-8")) / 1024, 1)

    status = {
        "build_timestamp_utc": now,
        "edition_date": edition,
        "html_size_kb": file_size_kb,
        "story_count": p.story_count,
        "deep_reads_count": p.deep_card_count,
        "aged_card_count": p.aged_card_count,
        "signal_card_count": p.signal_card_count,
        "outbound_link_count": len(p.hrefs),
        "image_count": len(p.imgs),
        "archive_snapshot_count": archives,
        "bcc_count": bccs if bccs >= 0 else None,
        "gate_results": {
            "format_lock": "PASS",
            "url_reachability": "PASS",
        },
    }

    # Write status.json next to index.html so it gets deployed with the artifact.
    status_path = os.path.join(repo_root, "status.json")
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    # Markdown summary for $GITHUB_STEP_SUMMARY
    bcc_display = str(bccs) if bccs >= 0 else "n/a (vault not accessible)"
    print("## SWAP Report build metrics")
    print()
    print(f"**Edition:** {edition}  ·  **Build:** {now}")
    print()
    print("| Metric | Value |")
    print("|---|---|")
    print(f"| HTML size | {file_size_kb} KB |")
    print(f"| Top-level stories | {p.story_count} |")
    print(f"| Deep Reads cards | {p.deep_card_count} |")
    print(f"| How-It-Aged cards | {p.aged_card_count} |")
    print(f"| Social/Signal cards | {p.signal_card_count} |")
    print(f"| Outbound links | {len(p.hrefs)} |")
    print(f"| Images | {len(p.imgs)} |")
    print(f"| Archive snapshots in repo | {archives} |")
    print(f"| BCC list size | {bcc_display} |")
    print()
    print("**Gates:** FORMAT_LOCK pass, URL reachability pass.")
    print()
    print(f"**Status JSON:** [theswap.report/status.json](https://theswap.report/status.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
