# meeting_minutes/ — Cottonwood Heights City Council + CDRA

City Council minutes (markdown) and extracted roll-call votes. The Council also convenes
in-session as the **Community Development & Renewal Agency (CDRA)**; those motions live in the
same files/CSV tagged `body=CDRA`.

```
minutes/<year>/<week>/<date>_<slug>.md   canonical minutes markdown (provenance header + body)
raw/                                     retained source PDFs/.docx (never deleted)
minutes_index.csv                        one row per doc: date,year,title,slug,path,source,source_url,format
all_votes.csv                            13-col standard vote rows (Council + CDRA)
motions_std.csv                          normalized layer (motion_type_std/outcome/tallies) — keyed (source,motion_no)
roster.csv                               observed members: name,role,first_seen,last_seen,meetings_present,n_vote_rows
extract_votes.py                         minutes markdown -> all_votes.csv (+ motions_std)
validate_votes.py                        tally-vs-named cross-check (writes votes/_validation_report.txt)
votes/<year>/…                           per-meeting extracted-vote JSON (audit trail)
```

## Provenance — portal ∪ PMN (decayed-window backfill)
- **181 documents, 2020-01-06 → 2026-06-16.** Source split: **`civicplus` 87** (Granicus /
  CivicEngage Central portal, `showpublisheddocument` URLs) + **`pmn` 94** (Utah Public Notice,
  `utah.gov/pmn/files/<id>.pdf`, **council body 2147**). The portal keeps only a rolling ~5-year
  window and it has **decayed** (the 2022 column is down to 4 docs), so 2020–2024 was backfilled
  from PMN; on a `(date, meeting-type)` collision the born-digital portal doc wins.
- **Formats:** `pdf-text` 180 + `docx-text` 1 (some CivicEngage "Minutes" anchors serve Word —
  `extract` unzips `word/document.xml`). **Born-digital throughout — no OCR**; the corpus
  screener found 0 dict/split-word/encoding outliers across all years.
- The site sits behind an **Akamai-style edge that 403s bare UAs** — every portal fetch uses the
  full browser header set (see `../recon.md` / `../fetch_minutes.py`). PMN files download with a
  plain UA.

## Vote schema + the structural facts
> **2026-07-31 duplicate-ingest removal — the phantom "2025-05-06" council meeting.** The portal's
> **May 6, 2025** row links Minutes doc **9961**, but that document IS the **May 20, 2025** minutes
> (byte-identical, md5 `bf08f345181e6598b90f0619215bc5a7`, to doc **10171** on the May 20 row;
> in-body header "HELD TUESDAY, MAY 20, 2025" + every page footer "Minutes for May 20, 2025";
> re-fetched live 2026-07-31 — the city mis-upload is still there). The ingest therefore carried the
> **same meeting under two dates**, double-counting **7 motions / 23 vote rows** (incl. the CDRA
> motion 5). The 2025-05-06 doc + index row were removed, the markdown filed in
> `../_removed_duplicates/` (so `fetch_new.py --ingest` can never re-add it), and the phantom's
> vote JSON deleted. **The May 6, 2025 meeting itself is REAL** — portal Agenda doc 9809, Ordinance
> **438** adopted 2025-05-06, two city YouTube recordings, and the May 20 minutes approve the
> "Meetings of May 6, 2025" — so its minutes are an **honest gap**: a row was added to
> `minutes_unrecovered.csv` (PMN body 2147 publishes no 2025 minutes at all; last minutes
> attachment 2024-11-12 — GRAMA / corrected-repost lead). The retained raw
> `raw/civicplus_2025-05-06_work-session-and-business-meeting.pdf` is kept (raws are never deleted)
> and is byte-identical to the May 20 raw. Post-fix totals: **184 docs · 1,154 motions · 3,275 vote
> rows** (db: 1,461 motions / 3,351 votes / 284 meetings).

> **2026-07-17 PMN-leads recovery:** the **2022-01-25 Council Retreat** (PMN file 828275) was
> promoted from `../pmn_backfill/` (a missing_minutes crosscheck lead — consensus/direction
> retreat; 1 unanimous-consent adjourn). Being the **first council doc PMN-promoted**, the council
> `all_votes.csv` gained the documented trailing 14th **`provenance`** column here (`minutes` =
> audited primary; `pmn_minutes` = the retreat's 1 row). Stem in `PROMOTED_PMN_BACKFILL` /
> `provenance_for` in `extract_votes.py`; filter `provenance='minutes'` for an audited-only cut.
> New totals: **181 docs · 1,146 motions · 3,210 vote rows**. See `../pmn_backfill/CLAUDE.md`.

- `all_votes.csv` columns: `date,year,title,body,motion_no,motion,motion_type,result,mover,
  seconder,member,vote,source` **+ trailing `provenance`** (added 2026-07-17). `body ∈
  Council/CDRA`. `result`/`motion_type` are **city-verbatim**.
- **The MAYOR VOTES — max roll = 5** (4 district members + the Mayor). Three voting mayors:
  Peterson (2020–21), Weichers (2022–25), Bennion (2026–). **No motion has >5 named members**
  (swept). Do NOT apply a Taylorsville/South Jordan "mayor non-voting, max 5 districts" model.
- **Named-roll city.** Most motions print "Vote on Motion: Member-Aye; …", so named coverage is
  high. The **579 blank-member rows** are **unanimous-consent procedural** motions (adjourn /
  open-closed session / reconvene) where no roll is printed — a source style, not a miss.
- **CDRA** = 70 motions / 128 rows / 41 meetings, `body=CDRA` ("Board Member <Name>" =
  councilmembers). In-session only; no separate portal files.
- **Mid-term appointment:** Matt Holton first votes **2023-05-16**; Douglas Petersen last votes
  **2023-04-04** (District 1 vacancy fill).

## Faithful clerk errors (retained verbatim — do NOT "fix" the CSV)
`validate_votes.py` flags where a printed tally disagrees with the named roll. Three are genuine
**source** errors, kept as-is:
- **2023-11-21** — Ordinance 405: 4 members named, clerk printed "passed **4-to-1**".
- **2026-05-19 ×2** — Ordinance 464: clerk duplicated "Hyland" as a phantom "**Highland**",
  printed "failed **4-to-2**"; the extractor kept the 5 real members and dropped the phantom.

These are the only three; every other validator flag reconciles. Corrections, if ever needed, go
through a documented override + rebuild — never in-place edits.

## Rebuild
`python3 extract_votes.py` (writes all_votes.csv + motions_std.csv + votes/ JSON) then
`python3 validate_votes.py`. Refresh new meetings with `../fetch_new.py` (probe) / `--fetch`.
After any change rebuild `../db/` and `../weeks/`.
