---
name: backlink-live-validator
description: Validate team-reported backlinks from the backlinks Google Sheet — open each live URL logged-out, run 4 gates (404/login wall, target-URL presence + dofollow/nofollow, content score, listing NAP), check Google/Bing indexing, write categorized verdicts back to the sheet, append a Run Tracker row, and post a summary. Use when the user says "backlink validator chalao", "check backlinks", "validate links", "backlink QA", or asks to verify the backlinks sheet.
---

# Backlink Live-URL Validator

Checks whether backlinks the team reports as "created" actually exist, are
complete, and are getting indexed. Writes verdicts back to the sheet so each
row shows proof.

## Config (defaults — user can override per run)

Global: Composio googlesheets account `googlesheets_eyah-myron` (ankush@fameninja) — NOT the default rankkking account. Dates appear in mixed formats (17-08-2026 / 18-8-2026) — normalize dd-m[m]-yyyy. **Run log goes to the central results spreadsheet `1AU_sykyWYAD8chcqfMI6OHs5rNJgBgQmIJpTt8lpo84` ("Backlink QA Results")** — append one row per sheet per run (columns: Run Date · Sheet · Rows Checked · SUCCESS · Target Missing · Access Fail · RECHECK Pending · Success Rate % (decided) · Indexed (Google) · Fortis:LDC · Notes). If the user names a sheet, run only that one; otherwise ask which (or "dono").

**Profile 1 — Content backlinks sheet** `1eCIq46EgNmx77uBXwx3HIOdtd6T39KDx31w0nBscrrg`:

| Setting | Value |
|---|---|
| Data tab | `Daily work report` |
| READ | A Date · B URL = **target_url** (their published article) · C Target keywords · D Activity = activity_type · E Live URL = **live_url** |
| WRITE | F Indexing Status (G:Y/N · B:Y/N) · G Live Status = verdict · J Category · K Reason · L Rel · M Content Score · N Checked At |
| FORBIDDEN | **H Email ID, I Password — never read, never write, never quote** |
| Row filter | E non-empty and G empty (+ user's date filter) |
| Out of scope tabs | `Backlinks Sites`, `Summary work report`, `Keywords` |

**Profile 2 — Local citations sheet** `1X0ig5ZqryO_LtY2bSdX92bhNq2Mu9bJ63AiIocs6F7c`:

| Setting | Value |
|---|---|
| Data tab | `Tracker` |
| READ | A Date · B Website · C Keyword · F Live Link = **live_url** · G = client/project name; activity_type is always business listing |
| target_url + NAP ground truth | Look up client (col G, fallback C) in tab **`Target listing URL`** → `website url` = target_url, `Address` = expected NAP for Gate 4. Confirmed by Ankush (Sep 4, 2026): **SKY7 Academy → `https://sky7academy.com/`** · **Dr. Rahul Manchanda → `https://gynaeendoscopy.com/`** · **Fortis Hospital Noida / Gaur City / Dr. Sushrut Singh → dual-target rule below**. A client outside this mapping AND missing from the registry → `CONFIG_MISSING`, do not guess |
| Sushrut dual-target rule | Acceptable links: `liverdigestivecare.com` (**PREFERRED** — build more here) OR the exact Fortis profile page `https://www.fortishealthcare.com/doctors/dr-sushrut-singh-9218` (acceptable; SerpApi-verified as his official page). A link to fortishealthcare.com **home page or any other Fortis page = `WRONG_TARGET` (FAIL)**. Record which target each row linked (`LDC` / `FORTIS_PROFILE`) and report the **Fortis:LDC ratio** in every run summary + QA Run Log — Fortis already ranks; the goal is majority LDC |
| WRITE | H Index status (G:Y/N · B:Y/N) · I Verdict · J Category · K Reason · L Rel · M Content Score · N Checked At |
| FORBIDDEN | **D Email, E Login Password — never read, never write, never quote.** Per-client tabs (`Fortis Hospital Noida`, `Gaur City`, `SKY7 Academy`, `Dr. Rahul Manchanda`, `Sheet5/11/12`) also hold passwords — do not open them |
| Row filter | F non-empty and I empty (+ user's date filter) |
| Out of scope tabs | everything except `Tracker` (write) and `Target listing URL` (read-only) |
| Content threshold | 70% (see `references/content-checklists.md`) |
| Nofollow | **Report only, not a FAIL** (record in J) |
| Redirects | Followed; PASS if the final page contains the target (note "redirected" in Reason) |
| Index check | Info status, never a FAIL — new links commonly take 1–2 weeks |

## Workflow

1. **Read the sheet** via the connected Google Sheets tool (Composio; fallback:
   `gws-sheets` CLI). Select rows per the row filter. Extract: row number,
   Activity Type, Live URL, Target URL, Anchor Text.
2. **Build input** — write the rows as JSON (`row, live_url, target_url,
   activity_type`) to a scratch file.
3. **Run the checker** (deterministic gates, logged-out, raw HTML):
   ```bash
   python3 "$SKILL_DIR/scripts/check_links.py" input.json > output.json
   ```
   Each result carries: `access` (OK / 404_NOT_FOUND / LOGIN_WALL /
   LOGIN_WALL_SUSPECT / INVALID_URL), `link_verdict` (LINK_FOUND /
   MENTION_ONLY / TARGET_URL_MISSING), `rel`, `word_count`, `images`,
   `title`, `snippet`, `redirected`, `js_render_suspect`.
4. **Browser fallback** — for rows with `js_render_suspect: true`,
   `LOGIN_WALL_SUSPECT`, or `LOGIN_WALL` from HTTP 403 (often Cloudflare
   bot-blocking, not a real login wall — e.g. Behance, Pinterest, Kickstarter,
   Redbubble render fine for logged-out humans), open the URL in the in-app
   browser (logged-out context) and re-judge Gates 1–2 from the rendered
   page. Only a 403 that ALSO shows a login wall in the browser is
   `LOGIN_WALL`. Never use the user's real Chrome for this (it is logged in).
5. **Content score (Gate 3)** — for rows that passed Gates 1–2, score the
   page against the activity-type checklist in
   `references/content-checklists.md`. Use `snippet`/`word_count`/`images`
   first; fetch the full page when the snippet is not enough. Below
   threshold → `CONTENT_INCOMPLETE` with the score in Reason.
6. **Listing NAP (Gate 4)** — if Activity Type is a business listing, verify
   the business address appears in the page content → else `ADDRESS_MISSING`.
7. **Index check** — for rows that passed Gates 1–2, run
   `SERPAPI_GOOGLE_LIGHT_SEARCH` via Composio (connected account
   `serpapi_moony-chaja`) with `q: "site:<live URL>"`. Organic result whose
   link matches the live URL → Google indexed YES; `organic_results_state:
   "Fully empty"` → NO. Throttle ~1–2 req/s (batch in groups, back off on
   429). Bing column: leave pending unless a Bing engine is available
   (Apify actor is the fallback once its monthly limit resets). Never fail
   a row on index status. (Validated Sep 4, 2026: freead1 ad indexed;
   mixcloud/fliphtml5 profiles not indexed.)
8. **Writeback** — update columns G–N for every checked row:
   - G Verdict: `SUCCESS` or the failing verdict
   - H Category: ACCESS / LINK / CONTENT / LISTING / OK
   - I Reason: one exact line (e.g. "HTTP 404", "target URL content mein
     nahi mila", "score 4/7 = 57%", "address missing", "redirected → final
     URL ok"). `MENTION_ONLY` = verdict `TARGET_URL_MISSING`, Reason "URL
     text mein hai par link nahi bana"
   - J Rel, K Content Score, L Google Indexed, M Bing Indexed,
     N Checked At (ISO timestamp)
9. **Run Tracker append** — one row: Run Date · Time · Links Checked ·
   Duration · Success · Fail:Access · Fail:Link · Fail:Content ·
   Fail:Listing · Success Rate % · Indexed (G) · Index Rate % · Notes.
10. **Manager issues list** — for every actionable fail (TARGET_URL_MISSING /
    404_NOT_FOUND / INVALID_URL / confirmed LOGIN_WALL), append a row to the
    central results spreadsheet's **`Issues` tab**: Run Date · Sheet · Row ·
    Client/Activity · Live URL · Issue · Action (e.g. "link add karwao",
    "text ko hyperlink banwao", "page dobara banwao", "sahi live URL daalo",
    "public visibility check karwao"). RECHECK rows are NOT issues yet.
11. **Summary + manager prompt** — report in chat: counts per category,
    success rate, index rate, Fortis:LDC ratio, and a short prompt message
    addressed to the SEO manager: "In sheets mein in rows par issues hain —
    Issues tab dekho aur theek karwao" with the top counts. If a Telegram bot
    token + chat_id or a Google Chat webhook is configured, POST the same
    summary there (plain HTTPS call); otherwise skip silently.

## Verdict taxonomy

| Category | Verdict | Meaning |
|---|---|---|
| ACCESS | `404_NOT_FOUND` | page missing (HTTP 404/410) |
| ACCESS | `LOGIN_WALL` | login/sign-up wall or 401/403 |
| ACCESS | `INVALID_URL` | malformed URL, dead domain, or other HTTP error |
| LINK | `TARGET_URL_MISSING` | page live but our link absent (incl. mention-only) |
| CONTENT | `CONTENT_INCOMPLETE` | checklist score below threshold |
| LISTING | `ADDRESS_MISSING` | business listing without NAP/address |
| OK | `SUCCESS` | all gates passed |

## Rules

- Always browse logged-out (checker script and in-app browser only).
- One row = one verdict; info fields (Rel, Indexed) never change the verdict.
- If the sheet or a column is missing, stop and tell the user exactly what is
  missing — do not guess a different sheet.
- Dry-run mode: if the user asks for a dry run, do everything except the
  writeback (steps 8–9) and show the would-be verdicts in chat.
