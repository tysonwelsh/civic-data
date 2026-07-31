# pmn_backfill — Utah Public Notice minutes recovery (additive)

Recovers council/PC meeting minutes **missing from the audited `meeting_minutes/` and
`planning_commission/` layers** by crawling the Utah Public Notice repository (utah.gov/pmn).
**Purely additive and separate** — it does NOT modify the existing minutes layer. The user
merges recovered docs into the canonical layer deliberately (see `coverage.md` §Reconciliation).

Built by `expand-city-sources` §4, 2026-07-06.

## Layout
```
raw/              13 recovered minutes PDFs (verbatim) + _fetch_log.jsonl (sha256 provenance)
text/             pdftotext -layout sidecars, one per PDF
index.csv         provenance table (schema below)
coverage.md       per-year repo/PMN/recovered/still-missing, per body; reconciliation flag
AVAILABILITY.md   what was checked / exists / not recovered / genuine gaps
unrecovered.csv   council Mar–Jun 2020 meetings held but minutes never posted to PMN
_disco/           crawl artifacts: entities.html, bodies.html, notices_<id>.html,
                  pmn_minutes_all.csv (all 711 Meeting-Minutes attachments parsed), batch.csv
```

## index.csv schema
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method,text_path`
— the §9 pmn_backfill contract (the `minutes_index.csv` standard plus `body`, PMN provenance
`notice_url,pmn_body_id,pmn_file_id`, `retrieved_date`, `extraction_method`) plus `text_path`.
- `path` — dataset-relative to the raw PDF (`raw/<file>.pdf`); `text_path` → the sidecar.
- `format` = `text` (born-digital; validator vocab). All PDFs are born-digital text — verified
  with `pdftotext -layout` and the corpus screener (no dict/split/weird-char outliers, 0 read
  errors). Native format is `pdf-text`, recorded via `extraction_method=pdftotext-layout`.
- `source` = `pmn`; `source_url` = the opaque `utah.gov/pmn/files/<file_id>.pdf`.

## Discovery / crawl method (reproducible, GET-only)
1. `list/entities.html?id=3` (govType 3 = Municipality) → **South Jordan entity 269**.
2. `list/publicBodies.html?id=269` → body ids: **Council 1031, PC 1032, RDA 3901, MBA 5015**
   (Board of Adjustments 1033 exists; out of scope).
3. `list/notices.html?id=<body>&page=300` — cumulative single-GET full history (the 6-month
   list view the base build used is why it missed the Jan–Jul 2020 council minutes).
4. Parse `(Meeting Minutes)` attachment labels per `<tr>`; date from filename (`MM-DD-YYYY`),
   falling back to the notice date td.
5. Set-difference PMN minutes dates vs repo `minutes_index.csv` dates, **±4-day tolerance**.
6. Fetch only missing dates via `scripts/polite_fetch.py` (throttled, sha256-logged).

## Key findings
- **RDA (3901) / MBA (5015) 2020+ are all *Combined CC & RDA/MBA* meetings** = the council
  minutes; they resolve to council dates already in the repo. No standalone 2020+ gap.
- **PC 2020+ has no genuine gap**; two PMN "PC-body" docs (2023-03-07, 2024-09-17) are combined
  CC&PC meetings already on disk under `meeting_minutes/`.
- **All 13 recoveries are City Council**, filling the documented Jan–Jul 2020 gap (minus the
  Mar–Jun electronic meetings that never had minutes) plus a 2023-01-24 budget meeting.
- Recoveries **contradict** two rows of `meeting_minutes/minutes_unrecovered.csv` — left in
  place per instructions; reconciliation is the user's call.

## Re-run / refresh
Re-fetch `notices_<id>.html?page=300` for the four bodies, re-parse, re-diff against the
current `minutes_index.csv`. Idempotent: existing `raw/` files are re-fetched only if absent.

## 2026-07-17 — final PMN-crosscheck flag verification (7 flags -> 2)

Verified all 7; appended 5 exceptions; re-run (--cached) 7 -> **2**.
- **Recovery leads (2):** PC 2024-05-14 (body 1032) — '05-14-2024 PC Meeting Minutes - FINAL.pdf'
  is a real FINAL minutes doc the repo lacks (repo has 05-28, 06-25, not 05-14) — STRONG lead;
  council 2020-02-25 (body 1031) City Council Budget Meeting — agenda-grade (PC held same date,
  council budget meeting not).
- **Exceptions (other x5):** 2020-06-02 (RDA 3901) + 2020-06-02 (MBA 5015) + 2020-06-16 (RDA 3901)
  = redundant RDA/MBA postings of combined electronic meetings already logged under council 1031;
  2021-09-13 (RDA 3901) Taxing Entity Committee = foreign body on RDA list; 2023-03-29 (council 1031)
  Architectural Review Committee = foreign body on council list.


## 2026-07-17 — crosscheck-lead disposition (1 promoted, 1 agenda-only)

- **PC 2024-05-14 — PROMOTED** into `planning_commission/` (the '05-14-2024 PC Meeting Minutes
  - FINAL.pdf', file 1128177, notice 912655). Content-verified genuine FINAL SJ Planning
  Commission minutes; canonical raw stored `planning_commission/raw/2024-05-14_planning-commission.pdf`
  (SJ's PMN-PC convention keeps PC raw in the PC dataset, not here — the fetch is logged in
  `raw/_fetch_log.jsonl`). Extract added 6 PC motions (5-0 unanimous, Commissioner Wimmer absent —
  matching SJ PC dissent/absent-only naming). validate_votes: no new failures.
- **Council 2020-02-25 — NOT promoted (agenda-only).** PMN notice 588535 carries ONLY
  '02-25-20 CC Budget Meeting Agenda #2.pdf' — no minutes attachment exists. Honest gap; reported.
