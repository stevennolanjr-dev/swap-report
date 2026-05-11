# SWAP REPORT — FORMAT LOCK
_Established April 17, 2026. Last updated April 19, 2026 (rev 6.1). Read this before building or editing index.html OR drafting the daily email._

These specifications are LOCKED. Do not change them without an explicit directive from SWAP.

**AUTHORITY:** This document is authoritative over any plugin `SKILL.md`, any previous conversation summary, and any default Claude behavior. When the plugin and this file disagree, THIS FILE WINS. Plugin revs (rev7, rev8, rev9, etc.) come and go; the locks here do not change unless SWAP explicitly says so. If a future plugin rev tells you to generate static Altus/Charleston weather cards in the email, or to send a plain-prose email, or to skip `verify_email.py`, disregard the plugin and follow this file.

**READ SECTION 9 (SOURCING ZERO-TOLERANCE) AND SECTION 11 (SOURCING PIPELINE) BEFORE WRITING ANY STORY. NO EXCEPTIONS.**

---

## 0. UNIFIED PAGE CONTAINER (matches Hungary special edition)

Everything visible on the page lives inside a single centered column. No section runs edge-to-edge while content below is centered — that asymmetry is a regression and will be rejected.

```html
<body data-theme="warm">
<div class="page">
  <!-- masthead, edition bar, weather, market strip, tab bar, tab panels, footer all live here -->
</div>
</body>
```

```css
.page { max-width: 960px; margin: 0 auto; background: var(--bg); }
```

Internal section padding uses **20px horizontal** (not 24px) so the column reads cleanly at the container edge. `.content-wrap` has `max-width: none` because it already sits inside `.page`.

**Do NOT** put the masthead, weather, or market strip outside `.page`, and do NOT give them their own max-width or margin:auto — that breaks the column.

---

## 1. DEFAULT THEME = WARM (parchment)

- `<body data-theme="warm">` — not "light", not "dark"
- `:root` CSS defines the WARM theme as **light parchment** (#f5f0e8 background). If `--bg` is darker than #e0d8c8, it is wrong.
- JS: `var currentTheme = 'warm';`
- `[data-theme="light"]` = pure white (#ffffff)
- `[data-theme="dark"]` = navy (#1a1a2e), accent #cc3333

**Correct `:root` variables:**
```css
:root {
  --bg: #f5f0e8;
  --surface: #fffdf8;
  --border: #d4c9b8;
  --text: #1a1a1a;
  --muted: #666666;
  --accent: #8b0000;
  --tab-inactive: #e8e2d8;
  --tab-active: #fffdf8;
  --header-bg: #ede8df;
  --tab-bg: #e8e2d8;
  --tag-bg: #8b0000;
  --tag-text: #ffffff;
  --watch-bg: #fff8f0;
  --watch-border: #c8a06a;
  --card-bg: #fffdf8;
  --hover-bg: rgba(139,0,0,0.06);
  --footer-bg: #ede8df;
  --footer-text: #666666;
}
```

**Theme toggle buttons:** Icons only — ☀ (&#9728;) / ⚜ (&#128305;) / ☽ (&#9790;) — NO text labels. Warm button has `.active` class on load.

---

## 2. MASTHEAD — LIGHT BACKGROUND, CRIMSON TITLE

```css
.masthead { background: var(--bg); padding: 24px 24px 16px; border-bottom: 2px solid var(--accent); }
.masthead-title { font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 22px;
                  letter-spacing: 4px; text-transform: uppercase; color: var(--accent); }
.masthead-meta { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--muted); margin-top: 4px; }
.masthead-epigraph { font-style: italic; font-size: 13px; color: var(--muted); margin-top: 4px; font-family: Georgia, serif; }
```

- NO `--masthead-bg` dark variable. NO separate dark band. Masthead IS the page background.
- Title: "THE SWAP REPORT" — entire title in `color: var(--accent)` (crimson). No `<span>` split.
- Epigraph: short analytical observation tied to the day's lead story. Not boilerplate. Appears below the meta line.
- Theme buttons: `background: var(--tab-bg); border: 1px solid var(--border); color: var(--text)` — styled against light background. Active: `background: var(--accent); color: #fff`.

---

## 3. EDITION BAR — NEUTRAL, NOT CRIMSON

```css
.edition-bar { background: var(--header-bg); color: var(--muted); border-bottom: 1px solid var(--border);
               font-family: 'IBM Plex Mono', monospace; font-size: 11px; padding: 5px 20px;
               display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.edition-bar a { color: var(--accent); text-decoration: underline; text-underline-offset: 2px; }
```

- NEVER `background: var(--accent)` — that is a crimson band and is wrong.
- The GitHub Pages URL (stevennolanjr-dev.github.io/swap-report) MUST NOT appear anywhere in the visible report.

### 3a. PUBLIC URL IS theswap.report — NEVER LINK TO GITHUB

The report is served from the custom domain `https://theswap.report/` (CNAME file in the repo enforces this). Every reader-visible link to the live site — whether in the HTML itself, the OG meta tags, or the email footer "Read the full interactive version" link — MUST use `https://theswap.report/`.

Specifically:
- `<meta property="og:url" content="https://theswap.report/">` — not the github.io URL
- Email footer: `View the full interactive version: https://theswap.report/`
- Any share card, preview, or inline reference: theswap.report

The skill's `GITHUB_PAGES_URL` config value MUST be `https://theswap.report/`. If an older cached version of the skill hard-codes `https://stevennolanjr-dev.github.io/swap-report/`, correct it before generating the report or email.

---

## 4. WEATHER — VENTUSKY INTERACTIVE MAP ONLY

**Single component.** SWAP explicitly rejected METAR observation cards. Do not reintroduce them. The weather section contains one thing: the Ventusky embedded interactive map with search and layer toggles.

### 4a. Ventusky embedded interactive map

```html
<iframe class="wx-iframe" src="https://www.ventusky.com/?p={lat};{lon};{zoom}&l={layer}"></iframe>
```

Layer toggle buttons call `wxLayer(btn, 'LAYER_NAME')` and rebuild the iframe src. Supported layers (use the exact Ventusky layer codes): `temperature-2m`, `wind-10m`, `rain-3h`, `clouds`, `radar`, `gust`.

Search box accepts three input types:
1. **Direct lat,lon** (regex `^-?\d+\.?\d*,\s*-?\d+\.?\d*$`) — jumps the map immediately
2. **ICAO code** (e.g. `KDEN`, `EGLL`) — resolved from a local lookup table for common airports
3. **Free text** — geocoded via `https://geocoding-api.open-meteo.com/v1/search?name={q}&count=1`

**Default view:** CONUS overview at `p=37;-95;4` with `l=temperature-2m`.

### 4b. Aviation METAR/TAF link-outs (not embedded)

Below the map, a single `.wx-credit` line includes external links to the full decoded METAR and TAF for the two SWAP-relevant fields. `aviationweather.gov` is CORS-blocked so it cannot be inline-fetched; it can only be opened in a new tab:

```
https://aviationweather.gov/data/metar/?id=KLTS&taf=true
https://aviationweather.gov/data/metar/?id=KCHS&taf=true
```

**Locations and wing designations (verified with SWAP — do not alter without confirmation):**
- Altus AFB, OK: ICAO KLTS · **97th Air Mobility Wing** (C-17 / KC-46 FTU). NOT 586th FW, NOT 14th FTW (14 FTW is at Columbus AFB, Mississippi).
- Joint Base Charleston, SC: ICAO KCHS · 437th Airlift Wing (host) / 315th AW (reserve associate).

### 4c. Do NOT regress

- Do NOT reintroduce `.metar-card` blocks above the map. The map is the entire weather section.
- Do NOT replace the map with static Altus/Charleston temperature cards.
- Do NOT use Open-Meteo `/v1/forecast` as a weather display source (it is fine only for geocoding lookups).
- Do NOT hard-code a daily high/low.
- Do NOT add error messaging like "Severe Wx Risk" absent verified NWS/aviation data.

---

## 5. MARKET DATA — SCROLLING TICKER TAPE ABOVE FOOTER

The static `.market-strip` under the edition bar was removed on SWAP's directive. Market data lives in a single scrolling ticker tape positioned immediately above the footer. Dark background, seamless loop, pauses on hover, respects `prefers-reduced-motion`.

**Structure:**
```html
<div class="ticker-wrap" aria-label="Market ticker">
  <div class="ticker-track" id="ticker-track">
    <span class="ticker-group">
      <!-- ticker-item blocks separated by ticker-sep bullets -->
    </span>
  </div>
</div>
```

The `.ticker-group` span is duplicated at load time by a small IIFE (so the CSS translate(-50%) loop is seamless). Do not hard-code two groups in HTML — let the script clone the first.

**CSS (locked):**
```css
.ticker-wrap { background: #111; color: #e8e8e8; overflow: hidden; padding: 8px 0;
               font-family: 'IBM Plex Mono', monospace; font-size: 12px; white-space: nowrap; }
.ticker-track { display: inline-block; animation: ticker-slide 90s linear infinite; will-change: transform; }
.ticker-wrap:hover .ticker-track { animation-play-state: paused; }
@keyframes ticker-slide { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
@media (prefers-reduced-motion: reduce) { .ticker-track { animation: none; white-space: normal; display: block; } }
```

**Required tickers (minimum):** S&P 500, DOW, NASDAQ, RUSSELL 2K, VIX, NIKKEI 225, FTSE 100, DAX, HANG SENG, WTI, BRENT, GOLD, 10Y UST, FED FUNDS, DXY, BTC.

**Do NOT:**
- Do NOT put a static `.market-strip` at the top of the page under the edition bar. That was the old format. Ticker tape is the only place market data appears.
- Do NOT use bright green (#6dcc6d) or bright red (#ff6b6b) on light backgrounds. On the dark ticker, use `#3dcc5a` / `#ff5a5a`.
- Do NOT omit `prefers-reduced-motion` — accessibility requirement.

---

## 6. FOOTER

```html
<div style="background:var(--footer-bg);color:var(--footer-text);font-family:'IBM Plex Mono',monospace;
            font-size:10px;padding:16px 24px;margin-top:32px;border-top:1px solid var(--border);
            display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
  <div>THE SWAP REPORT · [Date] · Morning Edition</div>
  <div style="opacity:0.6;">For SWAP · Distribution restricted · Not for public release</div>
</div>
```

No reference to `--masthead-bg` or `--strip-text` — those variables no longer exist.

---

## 7. NO TOOL ATTRIBUTION IN READER-FACING CONTENT

- Do NOT name Claude, Grok, Gemini, Perplexity, Cowork, or any AI tool in any reader-visible element
- Multi-source stories: "triangulated across multiple sources" or "cross-corroborated"
- Single-source stories: "single source — tracking" or "sourcing confidence: limited"

---

## 8. VARIABLES THAT NO LONGER EXIST

These CSS variables appeared in the old broken format and must not reappear:
- `--masthead-bg` (was #1a1a1a black — replaced by using `var(--bg)` directly)
- `--masthead-text` (replaced by `var(--text)`)
- `--strip-bg` (was #2a2a2a dark — replaced by `var(--header-bg)`)
- `--strip-text` (replaced by `var(--footer-text)`)

---

## 9. SOURCING — ZERO TOLERANCE FOR FABRICATION

This is the most important section of this document. A fabricated story or a fabricated URL in a product meant for senior military readership is a career-level failure.

### 9a. The rule

**Every story must be traceable to a real, verifiable event, and every hyperlink must resolve to a page whose content matches the claim being made.** If you cannot satisfy both, the story does not appear.

### 9b. What fabrication looks like (and has already happened once)

Past failures to avoid:

- **The 14th FTW / T-7A story (April 17, 2026 morning edition).** A story appeared on the Local → Altus section claiming "14th FTW sortie ops continue amid budget uncertainty; T-7A transition timeline holds," linked to `altustimes.com/2026/04/17/14th-flying-training-wing-update/`. This was fabricated end to end: the 14th Flying Training Wing is at Columbus AFB, Mississippi (not Altus); Altus is the 97th Air Mobility Wing (C-17/KC-46 FTU); the T-7A is a UPT aircraft and has no Altus footprint; the linked Altus Times article does not exist. SWAP flagged this as "pretty dangerous" and was correct to do so.
- **Dated URL slugs that 404.** Publications like Reuters, Politico, Stripes, Defense News, NYT, AP were linked with invented paths of the form `/{year}/{mo}/{day}/{plausible-slug}/`. These returned 404s (or 401/403 bot walls over fabricated paths) and broke SWAP's trust in every outbound link in the product.
- **Altus wing designation drift.** A previous revision labeled Altus as "586th FW" on the METAR card. 586th FW does not exist as an Altus unit. Cite tenant and host wings only from verified sources; when uncertain, omit the unit designation.

### 9c. Link construction rules

**Core principle: NO HYPERLINK is better than a MISLEADING HYPERLINK.** A link that points somewhere other than the article it claims to cite is worse than no link at all. This is the rule SWAP explicitly called out after the April 17 rev 3 post-mortem.

1. **Do not replace a fabricated dated article URL with the publication's section page.** A reader clicking "Russia's Window: NATO Overextension" who lands on foreignaffairs.com/ is being deceived twice: once by the headline that does not match the destination, and once by the pretense that a link exists. Strip the `<a>` tag entirely; leave the headline text in place as plain prose; cite the publication name in plain text.
2. **Never construct a URL by pattern-matching.** Do not take one real URL and synthesize other URLs "in that shape."
3. **When a specific article is the basis of a claim and its URL cannot be verified, cite the publication by name in plain text, not as a hyperlink.** Use `<span>Reuters</span>` or just the word `Reuters` with no anchor, not `<a href="https://www.reuters.com/world/middle-east/">Reuters</a>` and especially not `<a href="https://www.reuters.com/world/middle-east/fabricated-slug/">Reuters</a>`.
4. **Hyperlink authority — feeds_latest.json.** As of rev 5, outbound article-level hyperlinks are back in the report, but every one must be traceable to the current RSS pool. The source of truth is `SWAP-Report/rss/output/feeds_latest.json`, produced by `pull_feeds.py` and canonicalized by `gnews_resolve.py`. An article URL appears in the report if, and only if, it appears in that file (field: `link` after canonicalization, or `original_link` for the GNews wrapper form).
   
   Infrastructure links remain allowlisted independent of the RSS pool:
   - `https://www.ventusky.com` (interactive map credit)
   - `https://aviationweather.gov/data/metar/?id=KLTS&taf=true` and `...id=KCHS...`
   - `https://fonts.googleapis.com/...` (stylesheet load, not reader-visible)
   - Internal relative links under `special-editions/`

   A URL not in feeds_latest.json and not on the infrastructure allowlist is presumed fabricated and must be stripped.
5. **Before publishing, run the link audit.** Every outbound `href` in `index.html` must either (a) match a `link` or `original_link` field in `feeds_latest.json`, or (b) be on the infrastructure allowlist above. Use `verify_links.py` (see Section 11) — it fails the push on any unrecognized URL.
6. **URL slugs dated with today's date on sites you have not actually read are a red flag.** The publication may exist; the article probably does not. `grep -nE '/20(25|26)/[0-9]{2}/[0-9]{2}/' index.html` must return zero matches.
7. **Specifically prohibited past-failure patterns:**
   - `reddit.com/r/<made-up-subreddit>/<made-up-thread>/` — do not invent subreddit names or viral thread references. r/WarPowers (referenced in the April 17 rev 2 lighter fare) is not a real subreddit and the cited thread did not exist.
   - `youtube.com/watch?v=<random-id>` cited as a Pentagon/DoD briefing. Link to `defense.gov/News/Transcripts/` or strip the href.
   - `twitter.com` / `x.com` homepages as a "source" for a cited tweet. If the tweet cannot be verified and screenshotted, do not cite it.
   - `<publication>.com` or `<publication>.com/` bare homepages as citations. If the best available URL is the homepage, strip the href and cite in plain text instead.

### 9d. Story construction rules

1. **Every story must name the real unit, real command, real ship, real system, real person.** When unsure, use "U.S. official familiar with" or "according to open-source tracking" — never invent a unit or a name.
2. **Local beat stories require concrete verification** (recent Altus Times headline, recent Post and Courier headline). If no verified local story exists, use a placeholder labeled `OSINT — single source, tracking` or skip the local card entirely. Do not write the story first and then invent a URL to justify it.
3. **Military unit designations are non-negotiable.** Altus = 97th AMW. Columbus = 14th FTW. Vance = 71st FTW. Laughlin = 47th FTW. Sheppard = 80th FTW. Randolph = 12th FTW. Do not confuse mobility units with training units.
4. **Pentagon briefings.** Do not link to a random YouTube video ID as "the briefing." Link to `defense.gov/News/Transcripts/` or skip the hyperlink.
5. **BLUF and section synopses may summarize multiple real sources** but must not invent quotes, force-structure numbers, budget figures, or casualty counts.

### 9e. Self-audit before pushing to GitHub

Run this checklist before every push. This is not optional.

1. **Link verification check.** Run `python3 rss/verify_links.py index.html`. Every outbound `href` must either appear in `rss/output/feeds_latest.json` or be on the infrastructure allowlist. The script exits non-zero on any mismatch and blocks the push.
2. **Dated-slug check.** `grep -nE '/20(25|26)/[0-9]{2}/[0-9]{2}/' index.html` must return zero matches.
3. **Military unit check.** Cross-check every named military unit (wing, BCT, battalion, fleet, carrier strike group, squadron) against the authoritative DoD/service-level unit list. No unit appears without verification.
4. **Named-figure quote check.** No named living public figure is quoted unless the quote is taken from a real, verifiable source. If you can't produce the verbatim source within 30 seconds, strip the quote.
5. **Reader-test.** Would a reader who clicks any headline get to the content implied by that headline? If no, the headline should not be a link.
6. **15-second check.** If a fact cannot survive a 15-second Google check by SWAP, it does not go in the report.
7. **Pool freshness.** `feeds_latest.json` must be ≤ 12 hours old at build time. If older, re-run `pull_feeds.py` and `gnews_resolve.py` before generating the report. The pipeline is the authority; do not hand-cite URLs that bypass it.

**If any of the above fails, the report does not ship.**

---

## 10. MARKET DATA SHAPE

Ticker values are auto-fetched from Yahoo Finance via `rss/fetch_market_data.py`. Hand-typing prices is prohibited. The build sequence:

1. Run `python3 rss/fetch_market_data.py` before assembling HTML. It writes `rss/market_data.json` with all instruments, formatted values, change percentages, and a session marker (`(prev close)`, `(Fri close)`, etc.).
2. Read the JSON. Render each instrument into a `.ticker-item` using the `value_formatted` and `change_pct_formatted` fields verbatim.
3. Apply the `direction` field as the CSS class on the change span: `up` → `#3dcc5a`, `dn` → `#ff5a5a`, `flat` → no color class.
4. The `session_marker` field, when non-empty, renders next to the value (e.g., "7,399 (Fri close)").

Failure mode: if Yahoo breaks the endpoint, the script falls back to the last successful fetch from cache and sets `stale: true` in the JSON. The build proceeds with the stale data; do not crash the brief over a market-data outage.

Banned: typing any numeric value into the ticker by hand. If `market_data.json` is missing or `degraded: true` in a way that produces zero instruments, OMIT the ticker from the build entirely. A missing ticker is preferable to fabricated values.

### 10a. Federal Register integration

Run `python3 rss/fetch_federal_register.py` before assembling the Domestic Politics tab. It writes `rss/federal_register.json` with the last 24 hours of entries from defense, state, treasury, homeland security, justice, EOP, OMB, and NSC. EOs and proclamations are flagged with `is_executive_order` and `is_proclamation` so they elevate to top of the section. Routine notices below.

### 10b. FRED macro data (optional)

Run `python3 rss/fetch_fred.py` before the Domestic tab. Requires a free FRED API key in `FRED_API_KEY` env var or `SWAP-Report/.fred-key`. If absent, script writes `degraded: true` and the build skips the macro line. Never write `.fred-key` into git.

---

## 11. SOURCING PIPELINE (RSS → feeds_latest.json → report)

The verified-source system lives in `SWAP-Report/rss/`. It exists for one reason: every hyperlink in the published report must be traceable to a real RSS entry from a curated 69-feed pool.

### 11a. Components

```
SWAP-Report/rss/
├── swap-report-feeds.opml   # 69 curated RSS feeds (defense, strategic, national, intl, local, opinion)
├── pull_feeds.py            # Parallel fetcher; dedupes, filters by time window
├── gnews_resolve.py         # Canonicalizes Google News wrapper URLs to publisher URLs
├── validate_feeds.py        # Health check — run monthly to catch dead feeds
├── verify_links.py          # Pre-publish gate: every href in index.html must be in feeds_latest.json
└── output/
    ├── feeds_latest.json    # Authoritative story pool — THE source of truth for links
    ├── feeds_digest.md      # Human-readable browseable scan
    ├── resolved_urls.json   # Cache of GNews → publisher URL mappings (speeds repeat runs)
    ├── seen_urls.json       # URLs cited in prior SWAP Reports (14-day retention)
    └── run_log.txt          # Fetch diagnostics per run
```

### 11b. Daily workflow

1. **Pull.** `cd rss && python3 pull_feeds.py --hours 24` — fetches all 69 feeds in parallel (~5s), dedupes, writes `feeds_latest.json`.
2. **Canonicalize.** `python3 gnews_resolve.py` — replaces Google News wrapper URLs with real publisher URLs (cached across runs; first run ~10 min, subsequent runs ~1 min for new URLs only).
3. **Synthesize.** Generate the SWAP Report using Claude + Grok + Gemini + Perplexity as today, with one hard constraint: every outbound article hyperlink must appear in `feeds_latest.json`.
4. **Verify.** `python3 verify_links.py index.html` — the gate. Fails the push on any href not in the pool or on the infrastructure allowlist.
5. **Push.** `push-to-github.sh` — commits and pushes `index.html` to the theswap.report deployment.
6. **Mark seen.** For each URL cited in the published report, `python3 pull_feeds.py --mark-seen URL` so tomorrow's run doesn't re-cite the same story.

### 11c. Rules of use

1. **The pool is the authority, not a suggestion.** If a story matters editorially but no URL for it exists in `feeds_latest.json`, cite the publication in plain text and omit the hyperlink. Do not synthesize a URL to match.
2. **Prefer direct publisher URLs over Google News wrappers.** After `gnews_resolve.py` runs, every entry's `link` field is the canonical publisher URL. The original wrapper URL is preserved at `original_link` for audit purposes; it is not published.
3. **Multi-model synth is editorial, not sourcing.** Grok, Gemini, and Perplexity help with analysis, theme correlation, and narrative construction. They are not allowed to introduce URLs the RSS pool does not already contain.
4. **Local (Charleston) coverage.** The Charleston feed is 99% Google News-wrapped. After canonicalization most links resolve to Post and Courier, Live 5 News, The State. If canonicalization fails for a Charleston story, cite the publication in plain text; do not ship the wrapper URL.
5. **Feed health.** Run `validate_feeds.py` monthly. Replace dead feeds. Never silently drop a publication.

### 11d. What this replaces

Rev 4's four-URL allowlist was an emergency cordon in response to the April 17 fabrication incident. Rev 5 replaces the cordon with a verified-source pipeline. Hyperlinks are back in the report — honestly this time — because every one is now traceable to a live RSS pull.

---

---

## 12. EMAIL FORMAT LOCK — RICH INLINE HTML, NOT PLAIN PROSE

The daily email IS the product's front door. It is NOT regular correspondence. The "emails should be extremely short" preference does NOT apply to the SWAP Daily Brief email.

SWAP raised this regression on April 19, 2026 after earlier drafts that day came back as "just words and links." This section exists so that regression does not recur.

### 12a. What the email must look like

The email is a standalone, inline-styled HTML product that visually mirrors the web report. It is read on mobile first. It is read by senior readers. It gets the same design language as the page:

1. **Masthead.** "THE SWAP REPORT" in IBM Plex Mono (fallback `'Courier New', monospace`), 22px, weight 600, letter-spacing 4px, uppercase, color `#8b0000`. Bordered bottom 2px solid `#8b0000`. Below the title: "Daily Brief | [Weekday, Month Day, Year] | Morning Edition" in IBM Plex Mono 10px, muted gray, letter-spacing 2px, uppercase.
2. **Edition bar.** Light-parchment background (`#efe7d6`). IBM Plex Mono 11px, muted gray. Contains the same compact edition-note line the web report uses (Day X of the Iran War · key status flags · next event-horizon trigger).
3. **Weather — NWS national temperature map, NO static cards.** The email weather component is a single embedded NWS national-temperature map image wrapped in an `<a>` linking back to `https://www.weather.gov/forecastmaps/`. It is NOT two inline city cards. It is NOT hand-curated Altus/Charleston temperature values. It is NOT a live widget. **HARD BAN on static city weather cards in the email — SWAP has rejected this three times. Do not reintroduce them.**

   **Locked image URL:** `https://graphical.weather.gov/images/conus/MaxT1_conus.png` (NDFD CONUS max-temp forecast). Verified live and hotlinkable — the map on the landing page of `weather.gov/forecastmaps/` is served from this exact URL. Do NOT substitute `weather.gov/images/forecastmaps/today-hilo.png` (404) or any other guess. If the image URL needs to change, scrape the current `<img src=>` off `weather.gov/forecastmaps/` and update both this section AND `email-template.html`.

   **Link-wrap destination:** `https://www.weather.gov/forecastmaps/` (landing page, not the direct image).
4. **Market ticker bar.** Full-width black strip (`#111` bg, `#e8e8e8` text), IBM Plex Mono 11px. Contains the same Sunday-pre-open / market-hours values shown in the web report's ticker. At minimum: S&P FUT, DOW FUT, NDX FUT, VIX, WTI, BRENT, GOLD, 10Y UST, FED FUNDS, DXY, BTC. Green `#3dcc5a` / red `#ff5a5a` for up/down.
5. **BLUF block.** Background `rgba(139,0,0,0.05)`, left border `4px solid #8b0000`. Header "BOTTOM LINE UP FRONT" in IBM Plex Mono 10px, letter-spacing 3px, uppercase, crimson. Five bullets with a bolded lead clause, then the analytical hook.
6. **Through-Line section.** One-paragraph analytical thread tying the lead stories together. Same crimson mono header style.
7. **How It Aged section.** Displays the claims-ledger review verdict for the day. Badge: inline-block green `#2d7a3d` / yellow / red pill with white mono text, vertically aligned middle. Short prose after explaining the call, the resolution, and the lesson.
8. **In the Brief.** Compact table listing the tabs (Defense, Strategic, Domestic, Deep Reads, Social/Signal, Local, Lighter Fare) with one-sentence previews. Tab label in bold crimson.
9. **CTA button.** Solid `#8b0000` background, white text, IBM Plex Mono 12px, letter-spacing 3px, uppercase, "Read the full brief →". Links to `https://theswap.report/`.
10. **Footer.** Centered. IBM Plex Mono 10px muted. Report title · date · edition + `theswap.report` link + generation timestamp.

### 12b. Inline-style constraint

Gmail strips `<style>` blocks and external stylesheets. Every visual property must be inline via `style=""` attributes. No class-based styling will render. Use `<table>` for layout — flexbox and CSS grid are unreliable in email clients. Width 640px max, wrapped in an outer table centering on `#f4efe6` page background.

### 12c. What the email is NOT

- NOT a wall of plain prose.
- NOT a five-bullet BLUF pasted into `<p>` tags.
- NOT just "here is the link, go read it."
- NOT a replacement for the web report — it is the doorway to it.

### 12d. Distribution — load from JSON, never hand-type

The recipient list lives in **`email-distribution.json`** (vault root). The morning task and any manual draft step MUST load the list from that file. Hand-typing the BCC list is the exact failure mode that on May 2, 2026 produced a draft sent to a single recipient because a transcription pass dropped the BCC array.

**Authoritative loader:** `python3 rss/compose_email.py` prints the operational JSON view (from / to / cc / bcc / subject_prefix). Pipe it, parse it, paste from it. Do not retype any address.

**Sanity gate before sending:** `python3 rss/compose_email.py --check N` confirms the BCC list still contains exactly N addresses. If you expect 9 BCCs and the file has 8, the gate fails and the send stops. This catches accidental deletions in the JSON before they cost you a recipient.

- `To:` from `email-distribution.json` (currently `steven.nolan.jr@gmail.com`)
- `Cc:` from `email-distribution.json` (currently empty)
- `Bcc:` from `email-distribution.json` (currently 9 addresses — family/professional distribution)
- `Subject:` `[SWAP] Daily Brief — [Month Day, Year] AM · [3-4 lead-story teaser fragments joined with ·]`
- Plain-text body MUST be provided as fallback alongside `htmlBody` so non-HTML mail clients get a usable version.

To add or remove a recipient: edit `email-distribution.json` and add a `_change_log` entry. Either SWAP or Claude can do this.

### 12e. Change control

This email format is LOCKED. Changes require explicit SWAP directive. Do not "simplify" it back to prose on the basis of the general "keep emails short" preference. That preference governs one-off correspondence; the SWAP Daily Brief is a published product.

### 12f. Pre-publish verification gate — MANDATORY

Every daily brief draft MUST pass `rss/verify_email.py` before the Gmail draft is created. No exceptions.

**What the gate catches:**

1. Broken image URLs (the April 19 NWS map failure — guessed `weather.gov/images/forecastmaps/today-hilo.png`, shipped as a broken-image icon to the draft inbox).
2. Broken outbound link destinations (anything `theswap.report` or NWS-related that returns non-2xx/3xx).
3. Images that return a non-image content-type.
4. NWS map URL drift — if `weather.gov/forecastmaps/` reorganizes and the map is served from a new path, the gate surfaces candidate replacements rather than silently shipping a stale URL.

**How to run:**

```bash
python3 rss/verify_email.py path/to/email.html
# or pipe:
cat email.html | python3 rss/verify_email.py -
```

Exit code 0 = pass. Non-zero = fail. If the gate fails, fix the URL and re-run. Do NOT create the Gmail draft from HTML that has not passed this gate.

**Workflow contract (LOCKED) — uses `compose_and_draft.py` as a single chokepoint:**

The May 2 BCC-drop incident proved that "remember to load from JSON" doesn't survive contact with reality. `compose_and_draft.py` enforces every check at one chokepoint and refuses to bless the draft args if anything fails.

1. Render the email HTML from `email-template.html` to a file.
2. Render the plain-text fallback body to a file.
3. Run `python3 rss/compose_and_draft.py --html email.html --plain email.txt --subject "[SWAP] Daily Brief — ..."`. If exit non-zero, STOP. Fix the failure (verify_email mismatch, distribution.bcc empty, subject prefix wrong) and re-run.
4. Use the returned `draft_args` JSON VERBATIM in the `create_draft` MCP call. Do not retype the BCC list. Do not modify the subject. Use the exact body and htmlBody.
5. After the draft exists, fetch it back (e.g., via `gmail_search_messages` or `list_drafts`) and run `compose_and_draft.py --verify-draft --bcc "<comma-joined>" --subject "<subject>" --body-len N --expected-fingerprint <fp>`. The fingerprint must match. If it doesn't, the draft has drifted from what was blessed; delete and recreate.

This two-step contract makes BCC drops impossible without an explicit tampering step. The fingerprint binds bcc + subject + body length together at compose time and re-checks at draft time.

**Rule of thumb for all embedded URLs (email, report, and everywhere else):**

If you did not scrape or curl the URL within the current session, it is not verified. Do not construct URLs by pattern-matching ("the NWS map probably lives at /images/forecastmaps/today-hilo.png"). Scrape the authoritative page, take the `src=` attribute directly, and confirm HTTP 200 before embedding. This rule was already in §9c for report hyperlinks; §12f extends it to email images and email hrefs.

---

---

## 13. EM DASHES — HARD BAN

Em dashes (`—`, `&mdash;`, `&#8212;`) are **prohibited** in all reader-visible content: headlines, synopses, BLUF paragraphs, SWAP's Takes, tooltips, section headers, ticker labels, and the email.

**Why this rule exists:** April 26, 2026 — 66 em dashes found in a single published edition. All had to be manually scrubbed after the fact.

**What to use instead:**

| Em dash usage | Replacement |
|---|---|
| Parenthetical aside `X — detail — Y` | Commas `X, detail, Y` or parentheses `X (detail) Y` |
| Clause pivot `X — Y` (abrupt turn) | Semicolon `X; Y` |
| Introductory label `Watch — Iran` | Colon `Watch: Iran` |
| Appositive `X — the Y — Z` | Commas `X, the Y, Z` |
| Contrast/restatement `not X — it's Y` | Semicolon `not X; it's Y` |
| Sentence pivot `not just X — and Y` | Period or semicolon: `not just X. Y` |

**Rewrite the sentence** rather than find a mechanical substitute when the structure itself depends on the em dash.

`verify_format.py §13` catches any `—` or `&mdash;` outside `<style>` and `<script>` blocks and fails the push. The gate error reads:

```
FAIL  §13  no em dashes in reader content — found N em dash(es) — use comma, semicolon, colon, or rewrite
```

This rule also applies to the email draft. `verify_email.py` does not currently gate on em dashes in prose, but the same prohibition holds editorially.

---

## 14. THIRD-PERSON SELF-REFERENCE — HARD BAN

The site does not narrate itself in the third person. Constructions like "SWAP said," "SWAP claimed," "SWAP noted," "the report argued," "this site posited," "we previously asserted" are prohibited in reader-visible content. They read as bureaucratic, distance the writer from the writing, and make the product sound like a press release about itself.

**Why this rule exists:** Multiple editions used "SWAP said / claimed / posited" as the framing verb when referencing prior coverage. The construction creates an artificial third party between the writer and the reader and undermines the analytical voice.

**What to use instead:** Anchor self-reference to a date and let the date do the speaking. The reader knows what site they're on. Restating the brand name as a narrator is redundant.

| Banned | Use instead |
|---|---|
| "SWAP said the ceasefire was theater." | "On April 17, this site reported the ceasefire was theater." |
| "SWAP claimed the Hormuz reopening would not hold." | "Tuesday's brief argued the Hormuz reopening would not hold." |
| "SWAP noted the depletion math." | "Last week's coverage flagged the depletion math." |
| "We previously asserted X." | "On April 22, the brief made the case for X." |
| "The SWAP Report posited Y." | "An April 22 entry posited Y." |

The fix is structural, not cosmetic. Make the date the subject of the sentence; make the prior coverage the verb's object. The voice becomes first-person editorial ("on Tuesday we reported," "yesterday's edition flagged") or anchored-third ("the April 22 brief noted") — never "SWAP" as a third-party narrator.

**The "How It Aged" section is the most common offender.** Rewrite every "SWAP said X — verdict Y" line as "[Date] call: 'X' — Verdict: Y."

`verify_format.py §14` catches the banned constructions in reader-visible content and fails the push.

---

## 15. NO PLUMBING LANGUAGE IN READER-FACING CONTENT — HARD BAN

The reader does not need to know how the brief is built. References to the build pipeline, MCP tools, scheduled tasks, parsing failures, email-channel artifacts, or feed-availability diagnostics MUST NOT appear in the published product.

**Why this rule exists:** The Social/Signal SIGNAL SUMMARY repeatedly shipped paragraphs like *"Today's automated Grok pull rendered as HTML-only and surfaced a single parseable lead entry... The Gmail tool path used by the build runner returned only the email snippet rather than the full HTML body for this run, so the secondary entries and the TWITTER SIGNAL SUMMARY were not extractable through the email channel."* The reader has no idea what any of that means and shouldn't have to. Process commentary belongs in `run_log.txt`, not on theswap.report.

**Banned terms in reader-visible content:**

- "auto-pull", "automated Grok pull", "scheduled pull", "manual pull"
- "Gmail tool path", "tool channel", "email channel", "MCP", "MCP tool"
- "build runner", "the runner", "this run executed", "the run", "today's run"
- "structurally parseable", "HTML-only", "parseable", "parse failure", "extraction"
- "feed failure", "feed unavailable", "thin parse", "tool-channel artifact"
- "SIGNAL/CATEGORY/HANDLE structural markers", "structural markers... present"
- "Source A", "Source B", references to `noreply@x.ai`, scraping mechanics
- Timestamps with `Z` suffix in body prose ("0503Z", "1022Z") — convert to local time or omit
- "the Gmail tool", "the create_draft tool", names of any MCP tool

**Substitution rules:**

1. **If a feed produced thin output, OMIT the section.** Do not write a paragraph about why it's thin. Either you have signal worth publishing or you don't.
2. **If a feed produced no output, the section header does not appear.** No "Signal Summary unavailable today." That's a non-event; treat it as one.
3. **Cross-source convergence is editorial, not procedural.** "Multiple sources converged on Indo-Pacific tempo" is fine. "Cross-source convergence with the Defense and Strategic web sweep is high" is fine, just barely. "...is high on the Indo-Pacific tempo and on the Hormuz transit signal, suggesting today's thin parse is artifactual rather than substantive" is the failure mode — that's the writer talking to the writer, not to the reader.
4. **The SIGNAL SUMMARY paragraph, when it runs, is a 2-3 sentence editorial read of the day's social-feed signal.** Same voice as a Defense or Strategic synopsis. Not a status report on the collection pipeline.

**Good vs. bad SIGNAL SUMMARY:**

> **BAD:** "Today's automated Grok pull arrived in inbox at 0503Z and the email subject and snippet (lead entry: WhiteHouse, Conflict and Crisis, Iran ripples) confirm the run executed and the body is structurally parseable. The Gmail tool path used by the build runner returned only the email snippet..."

> **GOOD:** "Institutional accounts converged Wednesday on Indo-Pacific tempo (Balikatan, Sulu Sea presence, distributed live-fire) and on Hormuz transit volume. The pattern is concrete distributed exercises building real interoperability at a pace the wider press cycle is treating as routine. USNI News and Military Times confirm the read; this is a multi-source signal."

`verify_format.py §15` catches the banned terms in `<body>` content (excluding `<style>`, `<script>`, and HTML comments) and fails the push.

---

_Last updated: April 26, 2026 (rev 6.2) — hardened §12 after second regression on April 19: (a) rewrote §12.3 banning static Altus/Charleston weather cards in the email (third rejection logged) and mandating the NWS national temperature map with a LOCKED verified URL; (b) added §12f pre-publish verification gate (`rss/verify_email.py`) that checks every image and link in the email HTML before draft creation, with NWS drift detection. The gate caught the exact failure pattern that shipped a broken-image map earlier in the day._

_Rev 6.3 (May 2, 2026) — added §14 THIRD-PERSON SELF-REFERENCE BAN ("SWAP said / claimed / posited") and §15 NO PLUMBING LANGUAGE BAN (auto-pull, Gmail tool path, parse failure, structurally parseable, etc.). Both enforced by verify_format.py. Anchor self-reference to a date; omit feed-status commentary entirely if a parse failed._

_Rev 6.2 (April 26, 2026) — added §13 EM DASH HARD BAN after 66 em dashes found in the April 26 morning edition. Added §13 check to `verify_format.py` (18th rule). Gate blocks push on any `—` or `&mdash;` in reader content. Replacement rules documented above._

_Prior rev 6 (April 19) — added Section 12 EMAIL FORMAT LOCK after first regression on April 19 where draft emails were plain prose instead of rich inline-styled HTML product. Locks masthead, weather treatment, ticker bar, BLUF block, Through-Line, How It Aged, In the Brief, CTA, and footer spec. "Emails should be extremely short" preference does NOT override this section._

_Prior rev 5 (April 18) — added RSS sourcing pipeline (Section 11). Replaced rev 4's four-URL allowlist with feeds_latest.json as hyperlink authority. Removed visible sourcing-note requirement (headlines can carry real hyperlinks again). Added verify_links.py as pre-publish gate._

_Prior rev 4 (April 17 PM) — stripped all article-level hyperlinks after SWAP reported they pointed to publication homepages rather than the cited articles; deleted fabricated r/WarPowers Reddit item; added visible sourcing note to Overview tab; hardened Section 9 with explicit hyperlink allowlist and "no hyperlink is better than a misleading hyperlink" rule._
