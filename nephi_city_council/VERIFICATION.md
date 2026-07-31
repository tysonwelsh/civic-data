# Verification — Nephi City Council data repo

> **Addendum (2026-07-02, audit-driven repair — wrong 2021-02-23 minutes recovered):** The
> repo-wide duplicate-body screen found `2021-02-23_city-council-meeting.md` byte-identical
> (body md5 `ca068aa6…`) to the 2021-02-16 minutes. Verified at source: the city's own
> AgendaCenter Minutes link for Feb 23, 2021
> (https://www.nephi.utah.gov/AgendaCenter/ViewFile/Minutes/_02232021-156) is a **city-side
> mis-upload** — its PDF's extracted text is md5-identical (`63f24e44…`) to the Feb 16 PDF
> (`…/_02162021-155`), and the AgendaCenter Feb-2021 listing carries no other Minutes file for
> that date. The **real Feb 23, 2021 work-session minutes were recovered from the Utah Public
> Notice Website** (notice 661433 "Nephi City Council Work Session Minutes", event
> 2021-02-23 7:00 PM → attachment https://www.utah.gov/pmn/files/691883.docx, md5
> `3dc7a3a1…`), converted with `textutil` per the corpus's .docx convention (corpus is now
> 226 PDF + 17 .docx), and the source .docx retained at
> `meeting_minutes/raw/2021/2021-02-23_work-session-minutes_pmn-691883.docx` (kept because the
> AgendaCenter `source_url` cannot regenerate it; index row re-pointed to `source=pmn`).
> **Vote-table delta:** `all_votes.csv` 1,094 → **1,090** rows / 922 → **918** motions (−5
> wrong rows double-counting Feb 16's motions under Feb 23, +1 real motion — the work session's
> executive-session motion, Seely/Ostler, unanimous). All other rows verified byte-identical
> pre/post; contested stays 22, named-roll-call motions stay 46, body split Council 1,089 / CRA 1.
> **db rebuilt:** 1,253 → **1,249** motions (Council 921 → 917); votes 259, meetings 258,
> persons 24, applications 225 all reproduce exactly on stable keys; **referrals unchanged at
> 18 links** (every link re-verified field-by-field via `app_key`; application_ids did not
> shift, so `referral_overrides.csv` needed no remap). `weeks/` regenerated (241 bundles).
> Originals in `_backups/2026-07-02/nephi_city_council/`. Post-repair duplicate-body screen: 0.

**Date:** 2026-06-26
**Method:** data-integrity numbers independently RECOMPUTED from disk (csv-aware Python). Election
winners externally cross-checked at build time (Deseret News / Mid-Utah Radio / Ballotpedia +
council roster — see `election_results/CLAUDE.md`). (An independent verification agent reconciled
the contested count and counts before an infra stall; this is the completed QA pass.)

## Summary table

| Dataset | Status | Recomputed | Notes |
|---|---|---|---|
| Minutes | **PASS** | 243 index = 243 disk = 243 JSONs | 2020–2026; **0 iCloud dataless files**; born-digital (227 PDF + 16 .docx) |
| Votes | **PASS** | 922 motions · 1,094 rows · 22 contested | narrative format — 46 named, rest tally-only (no guessed members) |
| — body | **PASS** | Council 1,093 / CRA 1 (rows) | the 2021-07-27 Community Reinvestment Agency meeting tagged CRA |
| — mayor roster | **PASS** | no leak | Seely's 19 vote rows are all 2020–21 (councilmember); 0 once Mayor (2022+). Mayor tie-breaks (2x) noted in result strings, not as member rows |
| Elections | **PASS (w/ documented caveat)** | 7 races · 26 candidates · 80 precinct rows | **independently re-confirmed 2026-06-26** — 6/6 winners match external sources (Deseret News 2019; Mid-Utah Radio 2021/23/25); two Worwoods distinct; **2019 & 2021 unofficial** winners hold up despite Juab portal only ≥2023. See `election_results/ELECTION_VERIFICATION.md` |
| Comments | **PASS** | clean CSV = 0 rows; speaker log = 116 | in-minutes-only; speaker log labeled NOT comments |
| Geo | **PASS** | city polygon + 5 precincts | true EPSG:4326; City Hall → INSIDE |

**Overall verdict: PASS.** (Nephi is a small rural city — most motions are narrative "passed
unanimously" with no per-member roll-call; this is faithfully recorded, not fabricated, and is the
correct outcome.)

## Detail
- **Minutes ↔ index ↔ JSON** reconcile exactly (243 each). 0 dataless stubs.
- **Votes:** 922 motions / 1,094 rows; every motion carries mover + seconder. Only 46 motions name
  individual voters (Nephi has no roll-call grid) → the rest are `names_recorded:false` with empty
  aye/nay (no guessing). **22 contested** (20 nay + 1 abstain + 1 recuse), concentrated in 2020–21
  and largely driven by one councilmember (Kent Jones); includes 2 mayoral tie-breaks (2020 beer
  license; 2021 biennial budget) and one outright failure (2020-03-03 ordinance, 2-3).
- **Mayor non-voting confirmed:** Justin Seely votes only 2020–2021 (councilmember); 0 votes once
  Mayor (2022+). Tie-break votes by the sitting mayor are recorded in the result string.
- **Elections:** 7 races; winners externally confirmed. Honest gap clearly documented: Juab County's
  results portal only covers 2023+, so 2019 & 2021 totals are unofficial news-archive figures
  (winners/seat-counts solid; exact vote totals caveated; no per-precinct data those years).
- **Comments:** correctly in-minutes-only; `all_comments_clean.csv` empty by design; 116 in-person
  speakers in the speaker log, kept out of the comments CSV.

## 2026-07-02 addendum — duplicate member-vote adjudication (plan item 3.1 prep)

The repo validator flagged 1 duplicate `(source, motion_no, date, member)` pair in
`planning_commission/all_votes.csv`: PC 2024-01-10 m7 (chair election), **Ann Peterson
recorded both Abstain and Absent**. Source check: the minutes record "Abstained: 1,
Chairman Ann Peterson … Absent or Not Voting: 2, Commissioner Alan Hancock, Commissioner
Fran Peterson" — exactly one Abstain and two Absent. The extra `Ann Peterson,Absent` row
was an **extractor artifact**: the form-2 roll-call scan read past the outcome
declaration into narrative prose ("Outcome: Motion Passes, Chairman Ann Peterson will
serve for the 2024 year as the Chairman") and fabricated a vote from the re-mention.
`extract_votes.py` (`parse_rollcall`) now stops the form-2 name-list scan at the first
outcome declaration ("Motion Passes/is approved/…"); roll calls written inside the
Outcome block before that phrase (e.g. 2024-12-11 m4) are preserved. Verified end-to-end:
old code reproduced the old CSV byte-identically under `--force`; fixed code changes
exactly the one row (361 → 360 rows; roster unchanged; Fran Petersen's genuine Absent row
kept). db rebuilt: 1,249 motions · 259 votes · 18 referrals (all unchanged — the db's
UNIQUE had already collapsed the duplicate to the correct Abstain). Validator h.db: PASS
(delta 0, no overrides needed).

**2026-07-02 (3.1) council-vote validation:** shared validator installed as `meeting_minutes/validate_votes.py` and run — 1,090 rows / 918 motions (46 named, 872 tally-only — the documented narrative-vote style); 0 defects in all checks; tally-vs-counted 46/46; 0 unexplained mismatches.
