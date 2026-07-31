# campaign_finance — source availability (Park City)

As-of **2026-07-05**. Every host/URL checked for Park City municipal candidate
campaign-finance disclosures, what each had, and the honest gaps. Polite GET-only
(`scripts/polite_fetch.py`, browser UA, ≥1.2 s delay). Additive dataset — nothing in
`../election_results/` or any parent doc was modified.

## Bottom line
**Park City self-hosts every filing on its own CivicPlus site (`www.parkcity.gov`).**
All disclosures for **2017, 2019, 2021, 2023, 2025** (primary + general + final) — plus
2025/2026 conflict-of-interest statements — are linked from one page:

> `https://www.parkcity.gov/government/elections/campaign_disclosures.php`

The PDFs are plain document-tree URLs, **not** `showpublisheddocument/<id>` deep links
(that pattern is used for the canvass resolutions in `../election_results/`, not for
finance). Example:
`…/Documents/Government/Elections/Campaign%20Disclosures/2019%20Final%20Campaign%20Disclosures/Nann%20Worel.pdf`.
Spaces **must** be `%20`-encoded or the CMS returns HTTP 000/404 (same quirk noted in
`../election_results/CLAUDE.md`). No Wayback or third-party host was needed — the live
site carries the full run back to 2017.

## Hosts checked

| Host / endpoint | Result |
|---|---|
| `parkcity.gov/government/elections/campaign_disclosures.php` | **PRIMARY SOURCE.** 136 filing PDFs, cycles 2017–2025 + COI. Retrieved in full. |
| `parkcity.gov/government/elections/election_results.php` | Canvass/results only (already in `../election_results/`); links to the disclosures page. |
| `parkcity.gov/departments/executive/election-information` | **404** (path in the task brief no longer exists; the working page is `campaign_disclosures.php`). |
| `parkcity.easyvotecampaignfinance.com` / `parkcityut.easyvotecampaignfinance.com` | **DNS does not resolve** — Park City does not use EasyVote. |
| `disclosures.utah.gov` | Root loads (200) but the municipal tree is a JS/POST link directory; Utah's state site does **not** host Park City municipal filings (city self-hosts, confirmed by the complete parkcity.gov run). Not needed. |
| Summit County clerk | Not required — the city runs its own elections and posts its own filings; county hosts county/state races only. |
| Wayback Machine (`web.archive.org` CDX) | Not needed for coverage (live site complete). Queried only to look for the one 404'd link below — no capture existed; recovered directly from the live site instead. |

## Coverage by cycle (campaign filings; COI listed separately)

**136 PDFs total = 126 campaign filings + 10 conflict-of-interest statements. 103 MB.**
Format: **91 born-digital text / 45 OCR'd scans** (`format` in `index.csv`).

| Cycle | Primary | General | Final (own folder) | Total | Notes |
|---|---|---|---|---|---|
| 2017 | 4 | 9 | 6 | 19 | Mayor (Beerman, Williams, Armstrong) + Council. **No 2017 rows in `../election_results/`** (archive starts 2019) — 2017 filings join only if the filer reappears in a later cycle. |
| 2019 | 8 | 7 | 5 | 20 | Council only (no mayor race). Has a dedicated "Final" folder. |
| 2021 | 15 | 13 | — | 28 | Mayor (Worel/Beerman/Dobkin) + Council. Final reports live *inside* the General folder (→ `reporting_period=General`, `filing_type=summary`). |
| 2023 | 11 | 19 | — | 30 | Council only. Finals inside the General folder. |
| 2025 | 13 | 16 | — | 29 | Council + the 2025 mayor cycle. Finals inside the General folder. |

COI (conflict-of-interest officeholder statements — **not** campaign finance): **2025 = 4,
2026 = 6.** Retained for completeness (same page, same officials) and labeled
`filing_type=conflict_of_interest`.

## Join to `../election_results/park_city_results_by_candidate.csv`
**112 of 126 campaign filings (89%) join** to an election candidate: 101 `exact`
(same name + same cycle), 11 `firstlast` (surname-only filenames — Zegarra/Whitesides/
Dobkin — or a filer who appears in a different cycle). The **14 unmatched** are the
honest gap below. (COI rows join separately: 8 of 10 to a sitting official
`coi-officeholder`, 2 none.)

## Known gaps / discrepancies (honest data — not filled)

1. **One dead link on the city page, recovered.** The page links
   `…/2025 Primary…/Zegarra Final_Redacted.pdf` (`?t=202605132037200`) which **404s**.
   The same filer's 2025 primary statement exists un-suffixed at
   `…/2025 Primary…/Diego Zegarra.pdf` (HTTP 200, 4 pp.) and was retrieved as
   `raw/2025/2025_primary_Diego_Zegarra.pdf`. Both the broken link and the recovery are
   recorded in `batch/manifest.json`.
2. **13 × 2017 filings have no election-record counterpart** (Dana Williams, Josh Hobson,
   Mark Blue, Steve Joyce, Roger Armstrong). `../election_results/` begins at 2019, so these
   join to nothing. **Election-record coverage gap — flagged, election dataset NOT edited.**
   (2017 filers Andy Beerman and Tim Henney *do* match, via their later 2021 election rows.)
3. **A 2023 filer absent from the election record: `Betsy Wallace` (2023 primary).** She
   filed a campaign statement but is **not** in `../election_results/`' 2023 primary roster
   (candidacy withdrawn — the filename says so). This is exactly the "finance data surfaces
   an election-record question" case the skill warns about: **flagged here, elections NOT
   edited.**
4. **4 duplicate document bodies (not a defect).** `screen_corpus` flags 2 pairs whose text
   is identical: `2023 general Bill Ciraco 11.14.23` ≡ `…Final`, and `2025 primary Tana Toly`
   ≡ `…Amended`. The city posted the same content under two filenames; both raw PDFs are
   retained verbatim (we never dedupe raw).
5. **OCR quality on the 45 scans is form-grade, not clean prose** — handwritten/typed
   financial forms at 200–300 dpi. Text sidecars exist for every filing (Source-6) and are
   honestly labeled `format=scanned`; `screen_corpus` split-word/weird-char flags all fall on
   these scans (signals, not defects).
