# Project Notes — Backlink Live-URL Validator (poori kahani + current state)

> Ye file is skill ka complete context hai — koi bhi (Ankush, Manu, ya koi
> Claude session) ise padh kar bina purani chat ke kaam continue kar sakta hai.
> Last updated: 2026-09-04.

## Kya hai ye

FameNinja off-page team jo backlinks sheets mein report karti hai, unko
logged-out visitor ki tarah verify karne wali Claude Code skill. Verdict
sheet mein wapas likhti hai, Google-index status batati hai, SEO manager ke
liye Issues list banati hai, domain quality (DA/toxic) track karti hai.

## Sheets & IDs (sab kuch yahin hai)

| Kya | ID / Link |
|---|---|
| Content backlinks sheet | `1eCIq46EgNmx77uBXwx3HIOdtd6T39KDx31w0nBscrrg` (tab `Daily work report`) |
| Local citations sheet | `1X0ig5ZqryO_LtY2bSdX92bhNq2Mu9bJ63AiIocs6F7c` (tab `Tracker`; registry tab `Target listing URL`) |
| **Central QA sheet** (Run Log + Issues + Domains tabs) | `1AU_sykyWYAD8chcqfMI6OHs5rNJgBgQmIJpTt8lpo84` |
| GitHub repo (ye) | github.com/agag13/backlink-check (private; GitHub sirf **agag13** account — Ankush ka standing rule) |
| Composio googlesheets account | `googlesheets_eyah-myron` (ankush@fameninja) — default rankkking wala use NAHI karna |
| SerpApi (index checks) | Composio `serpapi_moony-chaja` |

## Ab tak ke runs (history)

| Date | Run | Result |
|---|---|---|
| Sep 2 | Dry run 18 rows (S1) | pipeline proof; duplicate-reporting pakdi |
| Sep 3 | Full dry run 345 rows | 77 found; 403=Cloudflare finding; Apify limit hit |
| Sep 4 | **Official run #1 (writeback)** | 413 rows: S1 64 SUCCESS/44 missing/17 access/122 RECHECK; S2 45 SUCCESS (31+14 Fortis-profile)/39 missing/24 access/58 RECHECK. **Index: 107 links mein sirf 5 Google-indexed (4.7%).** Issues tab: 124 rows. Fortis:LDC = 14:0 |

## Bade decisions (kyun aisa hai)

1. **Sushrut dual-target rule**: Dr. Sushrut / Fortis Noida / Gaur City ke liye
   acceptable = `liverdigestivecare.com` (PREFERRED) ya exact profile page
   `fortishealthcare.com/doctors/dr-sushrut-singh-9218`. Fortis home/koi aur
   page = WRONG_TARGET. Har run mein **Fortis:LDC ratio** report hota hai —
   goal majority LDC (Fortis already rank karta hai, juice LDC ko chahiye).
2. **RECHECK ≠ FAIL**: 403/JS wale rows provisional hain; Tavily/browser se
   dheere-dheere final hote hain. Tavily 6-sample: 0 PASS nikle the — zyada
   tar fails asli hain.
3. **Index check = info, kabhi FAIL nahi** (naye links ko 1-2 hafte lagte hain).
4. **Passwords**: sheets ke Email/Password columns + per-client tabs FORBIDDEN.
   Skill kabhi accounts nahi banati, CAPTCHA bypass nahi karti.
5. **Nofollow = report-only**; redirects follow karke final page par judge.
6. **Team data-hygiene finding**: kai "Live URLs" asal mein logged-in dashboard
   links the (adpost4u/user/dashboard, fliphtml5/dashboard, 4shared/account,
   archive.org/editxml) — Issues tab mein action ke saath listed.

## Features (Sep 4 tak)

- 4 gates: access (404/login-wall) → target-link + rel (dofollow/nofollow) →
  content score (70% threshold, `references/content-checklists.md`) → NAP
  (registry ground truth; phone digits-only, address = PIN + 2 tokens)
- Google index check (SerpApi `site:` queries)
- Domain metrics free-first: **OpenPageRank API** (30k/mo free, env
  `OPR_API_KEY`) → Apify `maximedupre` fallback ($0.0018/domain); `Domains`
  tab cache (30 din)
- **Link quality guard**: Toxic RED (deindexed domain) / AMBER (OPR≤1,
  link-network template, 100+ outbound); disavow file sirf manager-confirm par
- **Citation coverage %** vs `references/citation-directories.md` (43 dirs,
  5 tiers — India-focused); Tier-1 gaps → assembly-line queue
- Writeback + central QA Run Log + Issues tab (manager action list)

## Parked (round 2 — decided but not built)

- #5 DA/OPR trend history, #6 link velocity, #2 anchor-text distribution
- Bing index check (SerpApi bing engine ya Apify limit reset par)
- Content-score full pass (columns abhi blank hain)

## Pending inputs (Ankush)

1. **OPR_API_KEY** — free signup: domcop.com/openpagerank
2. **Registry NAP fill** — `Target listing URL` tab mein 5on clients ka
   Name + Address + **Phone** (GBP se exact copy)
3. **Daily routine ka go** — subah ~8 baje naye rows auto-check + summary
   (Telegram token/chat_id ya Google Chat webhook bhi tabhi)
4. Manu ko repo collaborator invite (GitHub par manual)

## Related skills (alag, par jude hue)

- `backlink-assembly-line` (+ children: saas-listing-pack, infographic-backlink,
  ppt-pdf-backlink, competitor-link-gap) — links BANANE ki side; validator
  QA karta hai. Dono independent.
- Skill C (50-60k domain vetting engine) — design frozen, build baad mein.
- SEO Signal Watcher (YouTube→validate→digest) — approved idea, channels pending.
