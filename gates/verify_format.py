#!/usr/bin/env python3
"""
verify_format.py — Pre-push compliance gate for SWAP Report index.html.

Purpose: block any build that violates FORMAT_LOCK.md structural rules from
reaching production. This exists because automated/scheduled builds have
repeatedly regressed to pre-FORMAT_LOCK templates (static weather cards,
static market strip, github.io leaks, wrong CSS class names).

The gate is structure-only. Content quality is not checked here; that's what
verify_links.py handles. verify_format.py is about the SHELL.

Checks — each maps to a FORMAT_LOCK section:
  §0  — <div class="page"> wrapper exists
  §1  — body has data-theme="warm"
  §2  — <div class="masthead"> (NOT .mast) and .masthead-title
  §3  — .edition-bar is NOT crimson (`background: var(--accent)` forbidden)
  §3a — No stevennolanjr-dev.github.io anywhere visible; theswap.report footer
  §4  — Ventusky iframe present; NO static .wx (city weather cards); NO .metar-card
  §5  — .ticker-wrap present; .market-strip (static) forbidden
  §8  — Forbidden legacy CSS variables (--masthead-bg, --strip-bg, etc.)

Usage:
    python3 verify_format.py path/to/index.html
    cat index.html | python3 verify_format.py -
Exit 0 = pass. Exit 1 = one or more violations (listed on stderr).
"""
from __future__ import annotations

import re
import sys
from typing import List, Tuple

Check = Tuple[str, str, bool, str]  # (section, label, passed, detail)


def check(html: str) -> List[Check]:
    results: List[Check] = []

    def add(section: str, label: str, passed: bool, detail: str = ""):
        results.append((section, label, passed, detail))

    # §0 — .page wrapper
    has_page = bool(re.search(r'<div[^>]*class=["\']page["\']', html))
    add("§0", "960px .page container wraps content", has_page,
        "missing <div class=\"page\">" if not has_page else "")

    # §1 — data-theme="warm" default
    has_warm = bool(re.search(r'<body[^>]*data-theme=["\']warm["\']', html))
    add("§1", "body[data-theme=\"warm\"] default", has_warm,
        "body tag missing data-theme=\"warm\"" if not has_warm else "")

    # §2 — .masthead class (not .mast)
    has_masthead = bool(re.search(r'class=["\']masthead["\']', html))
    has_mast_only = bool(re.search(r'class=["\']mast["\']', html)) and not has_masthead
    add("§2", ".masthead class (not .mast)", has_masthead and not has_mast_only,
        ("uses .mast instead of .masthead" if has_mast_only
         else "missing .masthead class" if not has_masthead else ""))

    has_masthead_title = bool(re.search(r'class=["\']masthead-title["\']', html))
    add("§2", ".masthead-title element", has_masthead_title,
        "missing .masthead-title" if not has_masthead_title else "")

    # §3 — edition-bar must NOT be crimson
    crimson_editionbar = bool(re.search(
        r'\.edition-bar\s*\{[^}]*background:\s*var\(--accent\)', html))
    add("§3", ".edition-bar is neutral (not crimson)", not crimson_editionbar,
        ".edition-bar uses var(--accent) background" if crimson_editionbar else "")

    # §3a — no github.io leak; theswap.report present
    github_io_leak = re.findall(
        r'stevennolanjr-dev\.github\.io[^"\'\s<>]*', html)
    add("§3a", "no stevennolanjr-dev.github.io leak", not github_io_leak,
        f"found {len(github_io_leak)} github.io reference(s): {github_io_leak[:3]}"
        if github_io_leak else "")

    has_theswap = bool(re.search(r'theswap\.report', html))
    add("§3a", "theswap.report referenced (footer/OG)", has_theswap,
        "no theswap.report reference found" if not has_theswap else "")

    # §4 — Ventusky required; static weather cards forbidden
    has_ventusky = bool(re.search(r'ventusky\.com/\?p=', html))
    add("§4", "Ventusky iframe embedded", has_ventusky,
        "missing Ventusky iframe" if not has_ventusky else "")

    # Static city weather cards: <div class="wx"> followed by Altus/Charleston <h3>
    # This is the specific regression pattern — a top-row of city cards.
    static_wx_cards = re.findall(
        r'<div[^>]*class=["\']wx["\'][^>]*>\s*<h3[^>]*>(?:Altus|Charleston|[A-Z][a-z]+,\s*[A-Z]{2})',
        html, re.IGNORECASE)
    add("§4", "no static city weather cards", not static_wx_cards,
        f"found {len(static_wx_cards)} static city weather card(s)"
        if static_wx_cards else "")

    # METAR cards — an earlier regression
    has_metar_card = bool(re.search(r'class=["\'][^"\']*metar-card', html))
    add("§4", "no .metar-card blocks", not has_metar_card,
        "metar-card class present" if has_metar_card else "")

    # §5 — scrolling ticker required; static market-strip forbidden
    has_ticker = bool(re.search(r'class=["\']ticker-wrap["\']', html))
    add("§5", "scrolling .ticker-wrap present", has_ticker,
        "missing .ticker-wrap (scrolling ticker)" if not has_ticker else "")

    has_static_strip = bool(re.search(r'class=["\']market-strip["\']', html))
    add("§5", "no static .market-strip", not has_static_strip,
        "static .market-strip present (use scrolling ticker instead)"
        if has_static_strip else "")

    # §8 — forbidden legacy variables
    forbidden_vars = ["--masthead-bg", "--masthead-text", "--strip-bg", "--strip-text"]
    for v in forbidden_vars:
        present = v in html
        add("§8", f"no legacy CSS var {v}", not present,
            f"{v} is still defined" if present else "")

    # §2 — IBM Plex Mono font loaded
    has_plexmono = bool(re.search(r'IBM\+Plex\+Mono', html))
    add("§2", "IBM Plex Mono font loaded", has_plexmono,
        "IBM Plex Mono not loaded" if not has_plexmono else "")


    # §13/§14/§15 — reader-visible content checks. Strip <style>, <script>,
    # and HTML comments first so CSS/JS/internal-notes don't false-positive.
    import re as _re
    reader = _re.sub(r'<style[^>]*>.*?</style>', '', html, flags=_re.DOTALL)
    reader = _re.sub(r'<script[^>]*>.*?</script>', '', reader, flags=_re.DOTALL)
    reader = _re.sub(r'<!--.*?-->', '', reader, flags=_re.DOTALL)

    # §13 — no em dashes in reader-visible content
    em_dash_hits = [m.start() for m in _re.finditer(r'—|&mdash;', reader)]
    add("§13", "no em dashes in reader content", not em_dash_hits,
        f"found {len(em_dash_hits)} em dash(es), use comma, semicolon, colon, or rewrite"
        if em_dash_hits else "")

    # §14 — no third-person self-reference. The brand is not a third party.
    # Patterns: "SWAP said/says/claimed/claims/noted/notes/posited/posits/argued/argues/asserted/asserts/wrote/writes/reported/reports"
    # Plus "the (SWAP )?Report (said|claimed|...)" and "this site (said|claimed|...)" with the wrong verb pairings.
    # Allowed: "SWAP's Take" (signed-attribution heading) is fine.
    third_person_re = _re.compile(
        r'\b(?:SWAP|SWAP Report|the SWAP Report|the Report)\s+'
        r'(?:said|says|claimed|claims|noted|notes|posited|posits|'
        r'argued|argues|asserted|asserts|wrote|writes|reported|reports|'
        r'observed|observes|warned|warns|predicted|predicts)\b',
        _re.IGNORECASE)
    third_person_hits = third_person_re.findall(reader)
    # Also catch "we previously asserted/claimed/argued" — same offense, different mask
    we_prev_re = _re.compile(
        r'\bwe\s+(?:previously|earlier|already)\s+'
        r'(?:said|claimed|noted|posited|argued|asserted|wrote|reported|observed|warned|predicted)\b',
        _re.IGNORECASE)
    third_person_hits += we_prev_re.findall(reader)
    add("§14", "no third-person self-reference", not third_person_hits,
        f"found {len(third_person_hits)} third-person construction(s): {third_person_hits[:3]}"
        if third_person_hits else "")

    # §15 — no skill-plumbing / process language in reader content.
    # Build a list of banned phrases (case-insensitive substring match in reader).
    plumbing_terms = [
        "auto-pull", "automated grok pull", "automated pull", "manual pull",
        "scheduled pull",
        "gmail tool path", "tool channel", "email channel", "the runner",
        "build runner", "this run executed", "today's run",
        "structurally parseable", "html-only", "parseable", "parse failure",
        "extraction was", "thin parse", "tool-channel artifact",
        "feed failure", "feed unavailable", "feed availability",
        "structural markers (signal, category, handle)",
        "structural markers are present",
        "noreply@x.ai", "the create_draft tool", "the gmail tool",
        "the mcp", "mcp tool",
    ]
    plumbing_lower = reader.lower()
    plumbing_hits = [t for t in plumbing_terms if t in plumbing_lower]
    # Also catch raw Z-timestamps in prose-ish positions (e.g. "0503Z").
    # Skip <a> hrefs by stripping them first.
    prose_only = _re.sub(r'<a[^>]*href=["\'][^"\']*["\']', '', reader)
    z_ts_hits = _re.findall(r'\b\d{3,4}Z\b', prose_only)
    if z_ts_hits:
        plumbing_hits.append(f"{len(z_ts_hits)} Zulu timestamp(s) in prose: {z_ts_hits[:3]}")
    add("§15", "no plumbing language in reader content", not plumbing_hits,
        f"found {len(plumbing_hits)} plumbing reference(s): {plumbing_hits[:5]}"
        if plumbing_hits else "")

    return results


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write(f"usage: {sys.argv[0]} <path|->\n")
        return 2

    src = sys.argv[1]
    if src == "-":
        html = sys.stdin.read()
    else:
        with open(src, "r", encoding="utf-8") as f:
            html = f.read()

    results = check(html)
    fails = [r for r in results if not r[2]]

    print(f"Checked {len(results)} FORMAT_LOCK rules.\n")
    for section, label, passed, detail in results:
        mark = "  OK  " if passed else "  FAIL"
        line = f"{mark}  {section:<4} {label}"
        if detail:
            line += f" — {detail}"
        print(line)

    print()
    if fails:
        print(f"FAIL: {len(fails)} FORMAT_LOCK violation(s). Push blocked.",
              file=sys.stderr)
        for section, label, _, detail in fails:
            print(f"  [{section}] {label}: {detail}", file=sys.stderr)
        return 1

    print("PASS: FORMAT_LOCK compliant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
