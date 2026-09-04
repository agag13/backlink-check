# backlink-check — Backlink Live-URL Validator (Claude Code skill)

FameNinja off-page team ke reported backlinks ko **logged-out visitor** ki tarah
verify karta hai, verdict sheet mein likhta hai, Google-index status batata hai,
aur SEO manager ke liye Issues list banata hai.

> **Note:** Yeh sirf **QA/checker** skill hai. Backlink *banane* wali skill
> (`backlink-pack-generator`) alag hai — dono independent chalti hain.
> Yeh skill kabhi accounts nahi banati, passwords enter nahi karti, CAPTCHA
> bypass nahi karti.

## Install

```bash
# is repo ko clone karke skill folder copy karo:
cp -r backlink-live-validator ~/.claude/skills/
```

Phir Claude Code mein bolo: **"backlink validator chalao"** (ya "dry run karo").

## Zaroori cheezein (requirements)

| Cheez | Kis liye | Kahan se |
|---|---|---|
| **Claude Code** + yeh skill folder | runner | anthropic.com/claude-code |
| **Composio MCP** connected | Sheets + SerpApi tools | composio.dev — apps: `googlesheets`, `serpapi` |
| Google account (Composio `googlesheets`) | dono sheets par **edit** access | abhi: ankush@fameninja (`googlesheets_eyah-myron`) |
| **SerpApi** (Composio `serpapi`) | Google index check (`site:` queries) | ~1 search/link/run — free plan 250/mo |
| Tavily MCP (optional) | bot-blocked pages ka recheck | tavily.com |
| Apify (optional fallback) | index-check fallback | monthly limit ka dhyan |

**Koi bhi password/credential NAHI chahiye** — sheets ke Email/Password columns
skill ke liye FORBIDDEN hain (SKILL.md dekho).

## Sheets

- Content backlinks: `1eCIq46EgNmx77uBXwx3HIOdtd6T39KDx31w0nBscrrg` (tab `Daily work report`)
- Local citations: `1X0ig5ZqryO_LtY2bSdX92bhNq2Mu9bJ63AiIocs6F7c` (tab `Tracker` + `Target listing URL` registry)
- **Results/QA central sheet**: `1AU_sykyWYAD8chcqfMI6OHs5rNJgBgQmIJpTt8lpo84`
  ("Backlink QA Results") — har run ka log + Issues tab (manager yahan se
  team ko fixes karwaye)

## Files

- `SKILL.md` — poora workflow, verdict taxonomy, sheet profiles, rules
- `scripts/check_links.py` — deterministic checker (stdlib-only, koi pip
  install nahi): 404/login gates, target-link + dofollow/nofollow, content
  signals. `python3 scripts/check_links.py --selftest` se test karo
- `references/content-checklists.md` — activity-type ke content scoring
  checklists

## Naya client add karna ho to

`Target listing URL` registry tab mein uski row daalo (project, website url,
address) — bina registry row ke uske links `CONFIG_MISSING` aayenge.
