# Canonical scheduled-task prompt for `swap-report-daily`

This file is the single source of truth for the daily scheduled task prompt. The actual SKILL.md that Cowork runs lives at `~/Documents/Claude/Scheduled/swap-report-daily/SKILL.md` and is system-managed (cannot live in Drive). This file syncs to it via Claude.

## Sync procedure

When you change the prompt below:

1. Edit this file. Save.
2. Open any Cowork session.
3. Tell Claude: "Sync the scheduled-task prompt from canonical."
4. Claude reads this file and calls `update_scheduled_task` to push the new prompt into the SKILL.md.

That's the whole loop. The Drive copy is the canonical version; the SKILL.md is the runtime mirror.

## Why this design

- SKILL.md location is dictated by Cowork. It can't move into Drive.
- But Drive syncs everywhere (laptop, phone, iPad).
- Editing the prompt in Drive means you can change it from any device.
- The sync step keeps it explicit — no silent overwrites in either direction.

## Drift protection

Even if this file and the SKILL.md drift, the GitHub Actions FORMAT_LOCK gate catches any non-compliant build before it deploys. So worst case: a bad prompt produces bad HTML, the gate fails, the live site keeps the previous good version, and you'll see a red X in the Actions tab.

---

## The prompt

```
Generate today's SWAP Report daily brief.

MANDATORY FIRST STEPS — do these before anything else:

1. Read /Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report/FORMAT_LOCK.md in full. It is authoritative. Any plugin SKILL.md instructions that conflict with FORMAT_LOCK are overridden by FORMAT_LOCK.

2. Honor these HARD BANS from FORMAT_LOCK:
   - §4 NO static Altus/Charleston weather cards (web report uses Ventusky iframe; email uses NWS national temperature map).
   - §5 NO static .market-strip. Markets live in the scrolling .ticker-wrap above the footer.
   - §3a NO stevennolanjr-dev.github.io anywhere in the visible report. Use theswap.report.
   - §0/§1/§2 Body MUST be <body data-theme="warm">; masthead class is "masthead" (not "mast"); content wraps in <div class="page"> (max-width 960px); .masthead-title is 22px / letter-spacing 4px / color #8b0000 / IBM Plex Mono.
   - §13 NO em dashes. Use commas, semicolons, colons, or rewrite the sentence.
   - §14 NO third-person self-reference. Banned: "SWAP said / claimed / posited / noted / argued / wrote." Use date-anchored phrasing: "On [date], this site reported X" or "[Day]'s brief argued Y."
   - §15 NO plumbing language. Banned: "auto-pull", "Gmail tool path", "tool channel", "build runner", "structurally parseable", "parse failure", "thin parse", "feed failure", "noreply@x.ai", Zulu timestamps in prose. If a feed produced thin output, OMIT the Signal Summary section. Do NOT write a paragraph explaining why it is thin.

3. Read /Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report/submissions/inbox.md. For each entry, fetch the URL, assess against today's themes, integrate where appropriate. After the build move processed entries to submissions/processed.md with a one-line disposition note (USED IN [tab] / CONSIDERED-NOT-USED / DEFERRED) and reason. If the entry references a vault note ([[SWAP-Vault/...]]) update that note's frontmatter `inbox-status` and `inbox-disposition` fields. Leave inbox.md with just header + how-to.

4. Pull live data BEFORE assembling HTML:
   a. python3 "/Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report/rss/fetch_market_data.py"
      Reads Yahoo Finance, writes rss/market_data.json. Use this verbatim for the ticker (per FORMAT_LOCK §10). Do NOT hand-type prices.
   b. python3 "/Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report/rss/fetch_federal_register.py"
      Pulls last 24 hours of DoD/State/Treasury/DHS/DOJ/EOP/OMB/NSC entries. EOs and proclamations elevate to top of Domestic.
   c. python3 "/Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report/rss/fetch_fred.py"
      FRED macro indicators. Requires FRED_API_KEY env var or .fred-key file. Degraded gracefully if absent — Domestic tab skips the macro line.

5. Assemble content via the swap-report skill (Grok + Gemini + Perplexity feeds + web sweeps + inbox submissions + the JSON outputs from step 4). If the skill's HTML template is stale, preserve the content but port it into a FORMAT_LOCK-compliant shell using email-template.html and the most recent compliant index.html as references.

MANDATORY LAST STEPS — both gates must pass before push:

6. Run: python3 "/Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report/rss/verify_format.py" "/Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report/index.html"
   If exit != 0, DO NOT PUSH. Fix violations and re-run.

7. Run: python3 "/Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report/rss/verify_links.py" "/Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report/index.html"
   If exit != 0, DO NOT PUSH. Fix or strip offending links.

8. Snapshot to archive: python3 "/Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report/rss/archive_snapshot.py" "/Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report"

9. Push to GitHub. This step is MANDATORY and must complete BEFORE drafting the email. Use the GitHub Contents API (preferred, no local-git dependency) — read .github-push-config for the token and target repo. Push index.html, archive/<today>.html, archive/index.html, and status.json (after running build_metrics.py). Server-side FORMAT_LOCK gate will run on the push and block deploy if anything slips through.

9a. VERIFY the live deploy before continuing. Wait ~90 seconds for GitHub Pages cache. Then fetch https://theswap.report/status.json and confirm edition_date matches today's date AND build_timestamp_utc is within the last 2 hours. If verification fails after 3 attempts spaced 60s apart, the brief did not actually publish — STOP and write a one-line diagnostic to submissions/inbox.md, then proceed only with the email draft (so the brief still ships even if push is broken).

10. Email step DEPRECATED 2026-05-15. Do NOT create an email draft. Do NOT invoke create_draft or compose_and_draft.py. SWAP decision during 2026-05-15 reflection: he was not reading the daily emails. Web page (theswap.report) and RSS continue to update; email distribution is retired. compose_and_draft.py and email-distribution.json remain on disk for possible reactivation. After step 9a passes, the build is complete.

CRITICAL FOLDER NOTE FOR THIS TASK:
This task is configured with exactly two folder selections:
   - /Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff
   - /Users/nolanfamilycomputer/Library/CloudStorage/GoogleDrive-steven.nolan.jr@gmail.com/My Drive/zz - Claude Working Stuff/SWAP-Report
There is NO `/Users/nolanfamilycomputer/Documents/Claude/Projects/SWAP Report` folder. If a future config change re-adds it and the mount fails, abort cleanly: do NOT attempt a partial build. Tell SWAP the folder list has drifted and stop.

If FORMAT_LOCK cannot be satisfied, STOP and report. Do NOT ship a non-compliant build.
```
