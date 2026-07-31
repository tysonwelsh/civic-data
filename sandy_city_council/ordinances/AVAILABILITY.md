# ordinances/ — availability & gaps (as-of 2026-07-05)

Adopted Sandy City ordinances (zoning/land-use + all other titles), 2020–2026, built
**independently from the Legistar Web API** and linked to the existing vote layer
(`meeting_minutes/all_votes.csv`). Unlike the scrape-only expansion cities, Sandy's
Legistar API is a genuine second source: it supplies the authoritative
number→date→subject→status index and the signed enacted-ordinance PDFs.

## Source
- **Legistar Web API** — `https://webapi.legistar.com/v1/sandyutah/` (GET-only, no key).
  Ordinance matters are `MatterTypeId eq 53`. Adoption dates come from each matter's
  `histories` (City Council `Pass`/`adopted`/`approved` action); enacted-ordinance PDFs
  and the real ordinance numbers come from each matter's `attachments`. See `CLAUDE.md`
  for the exact endpoints and method.
- **Codified code (context only)** — Municode `https://library.municode.com/ut/sandy`
  (HTTP 200; browsable current Land Development Code / Title 21). The SPA mirror
  `https://sandy.municipal.codes` is **HTTP 403** to the polite fetcher (bot-blocked) —
  avoid. Municode gives only the current consolidated text, not a per-adoption history,
  so it is **not** the join backbone and is not mirrored here.

## What this dataset contains
`index.csv` has **170 rows = every `MatterTypeId 53` ("Ordinance") matter introduced
2020-01-01 → 2026-06-19**, each with `adopted` (yes/no), status, land-use flag, and (for
adopted ones) the ordinance number, adoption date, retained PDF path, and the vote-layer
link.

- **Adopted by City Council: 87** (`adopted=yes`). By adoption year:
  2020 = 5, 2021 = 9, 2022 = 9, 2023 = 16, 2024 = 19, 2025 = 21, 2026 = 8.
- **Land-use ordinances (adopted): 65** — rezones (~20), Title 21 Land Development Code
  amendments (~23), annexations (~13), general-plan amendments (3), easement/street
  vacations (2), plus subdivision/site-plan/CUP items. The other **22** adopted are
  non-land-use (elections, fire code, animal services, business/alcohol licensing, HR).
- **Enacted-ordinance PDFs retained: 83 of 87 adopted** (`raw/ordinances/`, ~194 MB,
  signed ordinance preferred, unsigned adopted-ordinance PDF as fallback).
- **83 not adopted** (`adopted=no`): Planning-Commission-only recommendations,
  City-Council **denied** (3) or **tabled** (1), and **63 matters with no recorded
  history action** (agenda placeholders / superseded duplicate PC-vs-CC records). These
  are kept for completeness and clearly flagged; they are **not** counted as adopted.

## Linkage to the vote layer (`match_confidence`)
Each adopted ordinance is joined to a motion in `meeting_minutes/all_votes.csv` by
adoption date + the ordinance number cited in the motion text:
- **high = 73** — exact ordinance number cited in a motion on the adoption date.
- **medium = 7** — date + subject match, number not cleanly confirmed (see audit findings).
- **low = 6** — adoption meeting held but the ordinance rode the **Consent Calendar** /
  no standalone numbered motion (5 land-use/GPA/rezone + 1 resolution-enacted).
- **none = 1** — `26-50` (adopted 2026-06-23), **after the votes coverage window**
  (`all_votes.csv` currently ends 2026-06-02). Not a defect — a coverage lag.

**Every adopted ordinance with adoption date ≤ 2026-06-02 falls on a real council meeting
that already has vote rows** — i.e. no ordinance was adopted on a date missing from the
vote layer. The only "missing from votes" case is the single post-coverage-window one.

## Audit findings (flagged, NOT fixed — additive dataset)
1. **5 Legistar-vs-minutes ordinance-number discrepancies** (medium): the enacted-ordinance
   PDF/number in Legistar differs from the number the minutes motion cites —
   `22-07`↔minutes "22-08", `24-03`↔"23-04", `24-17`↔"24-18", `24-25`↔"2-25" (minutes OCR
   garble), `25-07`↔"25-10". Each may be a minutes typo/OCR error, a renumber, or a
   sibling ordinance adopted the same meeting. **The Legistar signed PDF is the enacted
   document; the minutes number is the likely error.** Logged in `linkage_note`; the vote
   layer is left untouched (fix belongs in a minutes remediation pass, not here).
2. **2 medium enactment-form notes**: matters filed as "Ordinance" type but **enacted as a
   resolution** (`2021-06-01` CDBG action-plan amendment → Res 21-17C; `2024-05-07` Council
   policy booklet → Res 24-17C) — no ordinance number exists.
3. **1 matter-status/flag gap in Legistar**: `21-034` (2021-01-26) shows action "adopted"
   with `PassedFlagName=Fail` → treated as **not adopted** (the adopting motion failed).
   Conversely `22-18` and `25-21` (Kershaw Annexation) had a **null** pass-flag but are
   genuine adoptions (confirmed by signed PDF + matching vote motion) → **included**.

## Gaps / not obtained
- **4 adopted ordinances have no retained enacted-text PDF**: `2020-02-04` (condemnation,
  enacted as Res 20-05C), `20-01` (animal code — no ordinance PDF attached), `21-15` &
  `22-02` (fireworks-restriction — only maps/memos attached). Metadata + Legistar links
  retained. (2 further land-use signed-PDF CDN links, `23-21` and `24-03`, returned **404**;
  the unsigned adopted-ordinance PDF was retained instead — see `linkage_note`.)
- **Full codified Title 21 text** — browsable at Municode (not mirrored; current-state,
  not per-adoption).
- **Ordinance matters before 2020** — out of the repo's 2020 data floor (not pulled).
