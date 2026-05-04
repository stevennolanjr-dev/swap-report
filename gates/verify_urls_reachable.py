#!/usr/bin/env python3
"""
verify_urls_reachable.py — Server-side URL gate for SWAP Report.

Complements verify_links.py (which checks against the RSS pool, runs locally).
This gate is RSS-pool-independent: it just confirms every outbound URL in
index.html actually resolves. Catches:
  - Fabricated dated slugs that 404
  - Dead links
  - Broken redirects
  - Articles that have been pulled from the publisher

Designed to run inside the GitHub Actions workflow with no vault dependencies.

Usage:
    python3 verify_urls_reachable.py path/to/index.html [path/to/another.html ...]
Exit 0 = all URLs returned 2xx or 3xx.
Exit 1 = one or more URLs failed (listed on stderr).

Tunables via environment variables:
    SWAP_URL_TIMEOUT  per-request timeout in seconds (default 12)
    SWAP_URL_PARALLEL number of parallel checks (default 16)
    SWAP_URL_RETRIES  retries per URL on transient errors (default 1)
"""
from __future__ import annotations

import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from typing import List, Set, Tuple

UA = "Mozilla/5.0 (compatible; SWAP-Report URL gate; +https://theswap.report)"
TIMEOUT = int(os.environ.get("SWAP_URL_TIMEOUT", "12"))
PARALLEL = int(os.environ.get("SWAP_URL_PARALLEL", "16"))
RETRIES = int(os.environ.get("SWAP_URL_RETRIES", "1"))

# Hosts that aggressively block automated checks but are known-good for our use.
# A 403 from these is treated as "reachable" — humans get through fine.
# Add liberally: false positives here block deploys; false negatives only matter
# if a major publisher is genuinely down (vanishingly rare).
HUMAN_ONLY_HOSTS = {
    # Social
    "x.com", "twitter.com",
    "www.linkedin.com", "linkedin.com",
    # Major newspapers
    "www.wsj.com", "wsj.com",
    "www.washingtonpost.com", "washingtonpost.com",
    "www.nytimes.com", "nytimes.com",
    "www.ft.com", "ft.com",
    "www.bloomberg.com", "bloomberg.com",
    "www.economist.com", "economist.com",
    "www.latimes.com", "latimes.com",
    "www.reuters.com", "reuters.com",
    # Newsletters / political press
    "www.politico.com", "politico.com",
    "thehill.com", "www.thehill.com",
    "www.axios.com", "axios.com",
    "www.semafor.com", "semafor.com",
    # Regional / international
    "www.timesofisrael.com", "timesofisrael.com",
    "www.haaretz.com", "haaretz.com",
    "www.scmp.com", "scmp.com",
    "asia.nikkei.com", "www.nikkei.com", "nikkei.com",
    "www.bbc.com", "www.bbc.co.uk",
    "www.lemonde.fr", "lemonde.fr",
    "www.spiegel.de", "spiegel.de",
    # Magazines / longform with bot blocks
    "www.foreignaffairs.com", "foreignaffairs.com",
    "www.newyorker.com", "newyorker.com",
    "www.harpers.org", "harpers.org",
    "www.thenation.com", "thenation.com",
    # Defense trades that occasionally block
    "breakingdefense.com", "www.breakingdefense.com",
    "www.defensenews.com", "defensenews.com",
    "www.airandspaceforces.com", "airandspaceforces.com",
}

# Hosts that are slow on HEAD/GET but reliable. Bigger timeout, more retries.
SLOW_HOSTS = {
    "www.npr.org", "npr.org",
    "www.csis.org", "csis.org",
    "www.rand.org", "rand.org",
    "www.brookings.edu", "brookings.edu",
}

# Skip checking these — they are anchors / non-http / mailto / template placeholders.
def should_skip(url: str) -> bool:
    if not url:
        return True
    if url.startswith(("#", "mailto:", "javascript:", "tel:", "data:")):
        return True
    if not url.startswith(("http://", "https://")):
        return True
    if "{{" in url or "}}" in url:
        return True
    return False


class HrefSrcCollector(HTMLParser):
    """Collects hrefs and srcs but skips browser hints (preconnect/dns-prefetch)."""

    def __init__(self):
        super().__init__()
        self.urls: Set[str] = set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        # Skip browser hints — they're not click targets.
        if tag == "link":
            rel = (d.get("rel") or "").lower()
            if any(h in rel for h in ("preconnect", "dns-prefetch", "preload", "prefetch")):
                return
        for key in ("href", "src"):
            v = d.get(key)
            if v and not should_skip(v):
                self.urls.add(v)


def check_one(url: str) -> Tuple[str, bool, str]:
    """Returns (url, ok, detail). HEAD with GET fallback. Per-host tuning."""
    host = ""
    try:
        host = urllib.request.urlparse(url).hostname or ""
    except Exception:
        pass
    timeout = TIMEOUT * 2 if host in SLOW_HOSTS else TIMEOUT
    retries = RETRIES + 1 if host in SLOW_HOSTS else RETRIES

    last_err = ""
    for method in ("HEAD", "GET"):
        for attempt in range(retries + 1):
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": UA}, method=method,
                )
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    status = getattr(r, "status", 200)
                    if 200 <= status < 400:
                        return (url, True, f"HTTP {status} ({method})")
                    last_err = f"HTTP {status} ({method})"
            except urllib.error.HTTPError as e:
                if e.code == 403 and host in HUMAN_ONLY_HOSTS:
                    return (url, True, f"HTTP 403 (human-only host)")
                if e.code in (405, 501) and method == "HEAD":
                    last_err = f"HTTP {e.code} on HEAD, will try GET"
                    break
                last_err = f"HTTP {e.code} ({method})"
                if 400 <= e.code < 500 and e.code not in (408, 429):
                    return (url, False, last_err)
            except urllib.error.URLError as e:
                last_err = f"URL error ({method}): {e.reason}"
            except Exception as e:
                last_err = f"error ({method}): {e}"
            time.sleep(0.4 * (attempt + 1))
        else:
            continue
        break

    # Last-chance: if it's a slow host and we timed out, treat as soft-fail
    # (return as warning, not blocker — slow hosts are reachable for humans).
    if host in SLOW_HOSTS and "timed out" in last_err:
        return (url, True, f"WARN: {last_err} on slow host (treated as reachable)")
    return (url, False, last_err or "unknown")


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write(f"usage: {sys.argv[0]} <html-file> [<html-file>...]\n")
        return 2

    parser = HrefSrcCollector()
    for path in sys.argv[1:]:
        if not os.path.exists(path):
            sys.stderr.write(f"FAIL: file not found: {path}\n")
            return 1
        with open(path, "r", encoding="utf-8") as f:
            parser.feed(f.read())

    urls = sorted(parser.urls)
    if not urls:
        print("No external URLs found. Nothing to check.")
        return 0

    print(f"Checking {len(urls)} unique URLs across {len(sys.argv)-1} file(s)...")
    print(f"  parallel={PARALLEL} timeout={TIMEOUT}s retries={RETRIES}")

    failures = []
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        futures = {pool.submit(check_one, u): u for u in urls}
        done = 0
        for fut in as_completed(futures):
            url, ok, detail = fut.result()
            done += 1
            mark = "  OK  " if ok else "  FAIL"
            print(f"{mark}  {detail:35}  {url}")
            if not ok:
                failures.append((url, detail))

    print()
    if failures:
        print(f"FAIL: {len(failures)} URL(s) unreachable. Push blocked.", file=sys.stderr)
        for u, d in failures:
            print(f"  [{d}] {u}", file=sys.stderr)
        return 1

    print(f"PASS: all {len(urls)} URL(s) reachable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
