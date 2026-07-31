# planning_commission/ — Cottonwood Heights Planning Commission

Planning Commission minutes (markdown) and extracted roll-call votes — the **same schemas** as
`meeting_minutes/`, with `body=PlanningCommission`.

```
minutes/<year>/<week>/<date>_planning-commission.md   canonical minutes markdown
raw/                                                  retained source PDFs/.docx
minutes_index.csv                                     date,year,title,slug,path,source,source_url,format
all_votes.csv                                         13-col standard vote rows (body=PlanningCommission)
motions_std.csv                                       normalized layer (keyed (source,motion_no))
extract_votes.py / validate_votes.py                  PC vote extractor + tally cross-check
votes/<year>/…                                        per-meeting extracted-vote JSON
```

## Provenance — portal ∪ PMN
- **78 documents, 2020-01-08 → 2026-02-04.** Source split: **`civicplus` 18** (Granicus /
  CivicEngage Central portal) + **`pmn` 60** (Utah Public Notice, **PC body 2148** + Admin
  Hearings **body 3287**). Same decayed-portal-window backfill as the council dataset (portal
  PC coverage is even thinner — ~2024+ — so most of the corpus is PMN).
- **Formats:** `pdf-text` 77 + `docx-text` 1. **Born-digital — no OCR** (screener: 0
  dict/split/encoding outliers, all years stable).
- **16 docs promoted 2026-07-16 from `../pmn_backfill/`** (see `PROMOTED_PMN_BACKFILL` in
  `extract_votes.py`): 15 Administrative Hearing sessions 2020–2023 (extends the existing
  `slug=administrative-hearing` convention backward — the dataset previously carried only
  2021-10-06 + 2024+) and the 2022-07-06 PC doc (ONE combined PDF holding both the 5:00 pm
  Work Meeting AND the 6:00 pm Business Meeting — kept as one doc, as the city published it;
  Approved: August 3, 2022). Their vote rows carry **`provenance=pmn_minutes`** (the
  documented trailing 14th column; audited-primary rows = `minutes`) — filter
  `provenance='minutes'` for an audited-only cut. ⚠ The 2023-03-01 admin-hearing doc's
  in-body header misprints "March 1, **2022**" — the footer ("APPROVED … 03/01/23"), the
  CUP-23-xxx case numbers, and the Wednesday check all prove **2023-03-01** (a clerk
  header-year typo, retained verbatim in the text).

## Vote schema + PC facts
> **2026-07-17 PMN-leads recovery:** 4 more docs promoted from `../pmn_backfill/` (missing_minutes
> crosscheck leads) — **2021-03-03 & 2023-03-08 PC** (docx business meetings, named rolls) +
> **2021-01-27 & 2022-12-07 Administrative Hearings** (0-motion officer decisions). Stems added to
> `PROMOTED_PMN_BACKFILL` (`provenance=pmn_minutes`). ✅ The bare-"Name-Aye" PAIR_RE follow-up is
> **RESOLVED (same day, wave 2):** `ch_vote_lib.py` PAIR_RE's role token is now optional (roster-
> guarded, vote-block-anchored, + a ≥2-member blockless fallback) — the 2021-03-03 SPL-21-002 roll
> carries all 7 ayes, and the fix recovered +59 PC / +71 council named rows corpus-wide (incl. a
> previously tally-only **4-to-1 Mayor-Weichers-Nay** council vote, 2024-03-05; all changes
> ground-truthed, 0 motion-level fields changed).
>
> **2026-07-17 (wave 2) agenda-grade recovery — the 2024 PC hole is CLOSED:** 20 more docs
> recovered (16 live from the city CMS via Wayback-archived listing anchors — the documents were
> DELISTED but still served by ID — + 1 council doc from Wayback bytes + 3 scattered 2022 docs):
> all 9 hole PC meetings 2024-02-07→2024-10-02 + their paired Administrative Hearings +
> 2022-03-09 AH + 2022-10-19 PC (a NEW contested 5-to-1, Ebbeler Nay, source-verified).
> ⚠ The 2024-03-06 AH header misprints "March 6, 2023" (Wednesday check + CUP-24 cases prove
> 2024 — same clerk header-year-typo class as 2023-03-01, retained verbatim). The 2024-03-06 PC
> doc is a transcript-style work meeting — genuinely 0 formal motions. 8 dates (2020-02-05,
> 2020-03-12, 2020-08-12, 2021-02-03, 2021-02-17, 2021-06-02, 2021-07-07, 2021-10-20) are purged
> from the CMS and never Wayback-captured — honest gaps in `minutes_unrecovered.csv`, GRAMA-only.
> 2019 minutes exist on Wayback but sit below the city's 2020 data floor (not ingested).

- `all_votes.csv` is the 13-col standard **+ the trailing `provenance` column** (2026-07-16),
  `body=PlanningCommission`. **263 distinct motions · 700 vote rows (521 named)**;
  `result`/`motion_type` city-verbatim.
- The PC uses **named-inline rolls** ("Commissioner Steinman-Aye; Commissioner Anderson-Aye;
  …"), so named coverage is high; blank-member rows are unanimous-consent procedural motions.
- The PC is a **recommending body** — its land-use votes are `pc_recommendation` (41 in the db)
  or `pc_final_action` (222); a recommendation to the Council is not the Council's final vote
  (join the two through date/subject, not an exact key — see `../db/SCHEMA.md`, the referral
  layer is empty by design).
- **Administrative-hearing-officer sessions carry no roll-call votes** — those are legitimate
  0-motion minutes files, not extraction failures. The hearing officer (CED Director Michael
  Johnson throughout 2020–2023) "moves to APPROVE/CONTINUE" his own decisions with no roll
  call or printed result — officer decisions, not commission votes; the minutes text stays
  searchable via the federated FTS layer. Coverage: **21 admin-hearing docs, 2020-03-11 →
  2026-01-07** (the 2020–2023 sessions were PMN-recovered, promoted 2026-07-16).
- The PC roster (~17 commissioners across 2020–2026) is disjoint from the council roster and its
  members are their own `person` rows in the db.

## Cadence + join
The **Planning Commission meets Wednesday**; it joins the weekly grid on its own meeting date
(`build_weeks.py` buckets on the council Tuesday grid, so a PC Wednesday lands in the same
week-ending bundle). PC votes are NOT part of the council `weeks/` vote total.

## Rebuild
`python3 extract_votes.py` then `python3 validate_votes.py`. Refresh with `../fetch_new.py`
(probes PC body 2148). Rebuild `../db/` + `../weeks/` after any change.
