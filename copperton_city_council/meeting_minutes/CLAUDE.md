# meeting_minutes/ — Town of Copperton Council

Council minutes (markdown) + extracted roll-call votes for the **Town of Copperton** (body
`Council`). ~800 residents; ~11–12 meetings/year (3rd Wednesday, 6:30 PM, Bingham Canyon Lions
Club). **106 minutes docs, 2018-07-18 → 2026-05-20; 431 motions; 458 vote rows.**

## Provenance

- **Sources (two portals):** the town **GoDaddy site** `copperton.utah.gov` (Agendas-&-Minutes
  year pages, **2023+**; docs on opaque `img1.wsimg.com` GUIDs; the TLS cert covers
  `secureserversites.net`, so fetch with **`curl -k` + a browser UA**) **and** Utah **PMN body
  5831** (`utah.gov/pmn/files/<id>.pdf`, the enumerable mirror for **≤2022**). `source` in the
  index = `godaddy` / `pmn`.
- **Format:** `text` (91, born-digital `pdftotext`), `ocr` (14 — town-era 2024-H2→2025 RICOH
  scans, per-page tesseract), `text+ocr` (1). Every minutes markdown carries a provenance header
  (`Source`, `Source URL`, `Source label`, `Format`, `In-body date match`, `Raw file`,
  `Raw sha256(16)`, `Provenance`); the raw original is retained under `raw/<year>/`.
- `minutes_index.csv` is the 8-col standard (`date,year,title,slug,path,source,source_url,format`);
  unrecoverable meetings live in `minutes_unrecovered.csv`, never as stub rows.

## The 2017-02 → 2018-06 gap (29 meetings — genuine, verified)

The earliest surviving doc is **2018-07-18** (PMN 459667). All 29 meetings from **2017-02-15 →
2018-06-20** are logged in `minutes_unrecovered.csv`: PMN body 5831 still lists their notices (the
meetings happened) but every referenced attachment PDF file-ID returns **HTTP 404** (retention
purge of everything older than ~mid-2018; audio gone too), and the GoDaddy site only reaches 2023.
Re-verified 2026-07-12 (see repo `VERIFICATION.md §Gap`) — a genuine purge, not a harvest miss.

## Votes — narrative-tally; the Mayor/Chair VOTES (max tally 5, both eras)

`all_votes.csv` is the 13-column standard. Copperton minutes are **narrative-tally**: a motion
names the **mover + seconder** and records a collective outcome or a numeric tally
("**vote was 5-0, unanimous in favor**"). The presiding **Mayor/Chair is counted in every roll
call** — township-era "Mayor Clayton voted 'Nay'" (2020-03-18) and town-era 5-0 tallies
(2025-07-16) both put him in the 5. So:

- **Max roll-call tally = 5** in BOTH the township (2018–2024) and town (2024-05-01+) eras.
- **Per-member rows exist for only ~10 motions** (`member`/`vote` populated): the 2020-03-18 UFA
  agreement + resolution (two 3-2 splits), the 2023-11-15 SLVLESA tax-rate 0-4 rejection, and
  named abstentions (2020, 2024–2026). **Everything else is tally-only** — `member`/`vote` blank,
  the count living in `result`. A blank member list is the SOURCE FORMAT, not an extraction miss;
  the parser never Present-fills an unnamed unanimous majority.
- `result`/`motion_type` are **city-verbatim**; normalized outcome/tallies/motion_type_std live
  alongside in `motions_std.csv` (joinable on `(source, motion_no)`), feeding the repo-root
  `crosswalks/` and `cities.db`.

## Regenerate (deterministic, no LLM, no network)

```
python3 extract_votes.py     # votes/*.json -> all_votes.csv + roster.csv
python3 validate_votes.py    # votes/_validation_report.txt (RESULT: PASS)
```

`extract_votes.py` re-derives `all_votes.csv` + `roster.csv` from the per-meeting `votes/*.json`;
`validate_votes.py` re-checks the tally-vs-named invariants (currently **PASS** — 0 dup-voter
motions, 0 rolls > 5, 0 tally mismatches). Rebuild `db/` + `weeks/` after any change.
