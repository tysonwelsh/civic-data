# Magna City Council — data repository

A Salt Lake City-style civic-data repository for the **Magna City Council** (with its in-recess
**Community Reinvestment Agency, CRA**) and its **MSD-staffed Planning Commission** (Salt Lake
County, Utah; ~29k pop.), built 2026-07-12 by the `build-city-data-repo` skill. Council + CRA + PC
minutes (as markdown), extracted roll-call votes, a relational cross-body db, public-comment
availability, municipal election results, and an address→district tool — all as markdown/CSV. See
`CLAUDE.md` for analysis guidance and each subfolder's own `CLAUDE.md`; independent QA in
`VERIFICATION.md` (**21 PASS / 4 WARN / 0 FAIL**, 0 FAIL on every built dataset).

**Magna is a metro township that became a city mid-record.** It was a Salt Lake County **metro
township seated 2017** and converted to a **CITY on 2024-05-01** (Utah **H.B. 35**). The 2025
election created its first directly-elected executive **Mayor**. This drives the single most
important structural fact — the presiding officer's vote flips across the seam (see below).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council + CRA minutes | 2018-07-17 → 2026-05-26 | **173 md** (== 173 index) | CivicPlus AgendaCenter (catID 3, 2022+) + Utah PMN body 5803 (2017–2021) | ✅ 151 `pdf-text` + 21 `pdf-ocr` + 1 `docx-text`; **2017 + Jan–Jun 2018 (36 mtgs) 404-UNRECOVERABLE** — logged, not stubbed |
| Council + CRA votes | 2018–2026 | **988 motions** (Council 956 · CRA 32) · **1,033 vote rows** (156 named) — incl. **67 motions promoted from `pmn_backfill/` (`provenance=pmn_minutes`; +16 Aug–Dec 2020 COVID-cluster 2026-07-17)** | extracted from minutes (audited + PMN-promoted sidecars) | ✅ verified; **presiding officer's vote flips at the seam**, max roll **5 both eras**; narrative-tally (unanimous majorities honestly unnamed) |
| PC minutes | 2019-03-14 → 2026-06-11 | **76 md** (== 76 index) | Utah PMN body 1559 (MSD-staffed) | ✅ all `pdf-text`; **2017–2018 (57 mtgs) agendas-only** — logged; **4 PHANTOM meetings de-ingested 2026-07-31** (PMN draft-copy trap — see below) |
| PC votes | 2019–2026 | **302 motions** (143 land-use-typed) · **303 rows** (18 named) | extracted from minutes | ✅ verified; recommends to Council; rezones keyed `REZ####-######` |
| Relational db (`db/civic.db`) | 2018–2026 | **1,290 motions** · **174 votes** · **248 meetings** · **3 cross-body referrals** (all medium) | standard cross-city schema | ✅ reconciles exactly (174 named CSV rows == 174 db votes; 0 orphan FKs); see `db/SCHEMA.md` |
| Public comments | — | **AVAILABILITY.md** + header-only CSV | n/a — SUBMIT-ONLY | ⚠ **HONEST-EMPTY** — in-person sign-up + QR only; no published/eComment archive |
| Election results | 2016 → 2025 | **18 races** + candidate & precinct tables | Salt Lake County SOVC (raw retained) | ✅ verified; 2016 founding + 2019 D1/D3/D5 **recovered from raw SOVC**, 2021 de-suppressed, 2025 primary+general; Water-District decoys EXCLUDED |
| Geo (address→district) | mixed vintage | **18 precincts → Districts 1–5**; derived polygons | precinct-derived (no official layer; UGRC CountyID 18) | ✅ tool + geojson; **MIXED-VINTAGE** — D2/D4 2025-high, D1/D3/D5 2019-medium, 4 precincts honestly unresolved |
| Weekly bundles | 2018–2026 | **177 week bundles** | derived (`build_weeks.py`, Tuesday grid) | ✅ regenerable; weekly vote sum 1,033 == flat total (council + CRA only — the PC is NOT in the weekly grid) |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (Council 988 / PC 302 rows) and the repo-root `crosswalks/`.

## The structural fact that makes Magna different — the form-of-government seam

Magna's presiding officer changed **kind** mid-record, and the vote extractor keys off the
**meeting date** to handle it:

- **Metro township + early city (2017 – 2025):** a **5-member district council** with **no
  separately-elected mayor**. The council elected its own **Chair, styled "Mayor"** — Dan Peay
  (through 2023), then Eric Barney (2024–25). **That Chair-titled-"Mayor" is one of the five and
  VOTES** (verified: `2024-12-10`, "AYE: … Mayor Barney … FINAL RESULT: 4-0"). Services
  (roads, planning, engineering) are delivered by the Salt Lake County **Greater Salt Lake
  Municipal Services District (MSD)**.
- **City with elected Mayor (2026+):** the 2025 election seated Magna's first directly-elected
  executive **Mayor Mick "Mickey" Sudbury**, who **presides but does NOT vote** (verified:
  `2026-05-26`, a `4-0` tally with the four councilmembers present and the Mayor excluded).

**Net:** the **maximum council roll-call tally is 5 in both eras** (verified: 0 motions with >5
named voters), but the presiding officer flips from a **voting Chair** to a **non-voting Mayor**.
Members are styled **"Council Member" in all eras** (the recon's "Trustee" guess was wrong — the
minutes say "Council Member" throughout). Mick Sudbury embodies the seam: a **District 3
councilmember who voted** through 2025, then the **non-voting Mayor** from 2026.

### CRA — an in-record body AND a standalone-meeting body (since 2026-07-16)
The Council sits as the **Community Reinvestment Agency** (Magna's RDA-equivalent) two ways:
in-recess/one-off captures in the audited layer (13 motions) PLUS **standalone CRA meetings
filed on PMN body 6925** — 7 approved minutes docs (2024-11-12 → 2025-09-23, 19 motions)
recovered into `pmn_backfill/` and promoted with `provenance=pmn_minutes`. **32 CRA motions**
total in `meeting_minutes/all_votes.csv` tagged `body=CRA`; the same members appear as
"Board Member <Name>". The 2025-11-18 CRA doc is a DRAFT (unpromoted honest sidecar).

## Distinctive Magna facts (read before quantitative claims)
- **Two portals, one seam year.** Council minutes come from **CivicPlus AgendaCenter (catID 3)**
  for 2022+ and **Utah PMN body 5803** for the township years (2018–2021). **⚠ Fetch PMN files
  from `www.utah.gov/pmn/files/<id>.pdf`** — `pmn.utah.gov/…` 302-redirects to the PMN home HTML.
- **Narrative-tally minutes — unanimous majorities are honestly UNNAMED.** A motion records mover
  + seconder + a numeric tally ("vote was 4-0, unanimous in favor with Council Member Pierce
  absent"); a real roll call is taken but the printed minutes give the tally, not each Aye. Only
  **156 of 1,033** council+CRA rows (and **18 of 303** PC rows) are named — the dissenters, abstainers,
  and absentees. A blank member list on a unanimous motion is source style, not an extraction miss.
- **Mild PMN-era text garble + an OCR seam.** The 2018–2023 PMN PDFs carry systematic
  character-substitution garble (`quonrm`→quorum, `Hoffrnan`→Hoffman) that the extractor
  normalizes; 21 Apr–Dec-2024 / early-2025 council minutes were image-only signed scans, **OCR'd**
  (`format=pdf-ocr`). The corpus screen found **0 outliers** across both.
- **CivicPlus wrong-doc slot.** The AgendaCenter sometimes serves an agenda/spreadsheet/
  correspondence file in the "Minutes" slot; real minutes were recovered from PMN where they
  existed, and no wrong-doc was fabricated into a stub.
- **MSD-staffed Planning Commission.** Magna runs its **own** PC (records on PMN body 1559),
  staffed by MSD planners; it recommends on Magna land use (rezones `REZ####-######`, subdivision
  plats, conditional uses, text amendments) up to the Council.
- **Comments are honest-empty (submit-only)** — see `public_comments/AVAILABILITY.md`.

## Known gaps / caveats
- **2017 + Jan–Jun 2018 council minutes (36 meetings) are 404-unrecoverable** on PMN (attachment
  purged; no Wayback). Logged in `meeting_minutes/minutes_unrecovered.csv`, never stubbed →
  council record starts **2018-07-17**. **PC 2017–2018 (57 meetings) are agenda/audio only** (no
  minutes published) → PC record starts **2019-03-14**.
- **The PMN draft-copy trap — 4 PHANTOM PC meetings removed 2026-07-31.** PMN body 1559 attaches
  minutes to a notice two ways: `YYMMDD_MagnaPC_MinutesApproved.pdf` (that notice's OWN meeting)
  and `<Month> minutes.pdf` (the **DRAFT of the PREVIOUS meeting**, posted with this meeting's
  agenda because this meeting will approve it). On the four notices where MSD never posted an
  approved copy, the original ingest took the draft and stamped it with the notice date, creating
  duplicate meetings that double-counted 12 motions: **2023-08-10** (= a draft of 2023-07-13),
  **2023-10-12** (= 2023-09-14), **2024-08-08** (= 2024-07-11), **2025-10-16** (= 2025-09-11).
  All four were de-ingested; the retained PDFs sit in
  `planning_commission/raw/_duplicate_drafts/`. **All four vacated dates are REAL meetings whose
  approved minutes PMN never published** — they are logged in
  `planning_commission/minutes_unrecovered.csv` (their agenda packets and audio, correctly dated,
  remain in `packets/` and `transcripts/`). Guard:
  `python3 planning_commission/validate_votes.py --check-dates` fails if any indexed document's
  in-body header date disagrees with its index date.
- **Elections:** county-administered; only Magna council + mayor races (the **Magna Water
  District** and its variants — ~95% of raw "magna" rows — plus the 2015 MSD/incorporation ballot
  questions are EXCLUDED). 2016 founding + 2019 D1/D3/D5 **re-parsed from the raw SOVC** (the
  shared archive dropped them); 2025 primary + general both captured.
- **Geo is precinct-derived, MIXED-VINTAGE** — no official city district layer exists. D2/D4 use
  2025 high-confidence precinct assignments; D1/D3/D5 fall back to 2019 pre-2022 lines (medium);
  4 precincts are honestly unresolved (`confidence=none`). Pre-2022 addresses near a moved
  boundary may mis-assign. See `geo/CLAUDE.md`.
- **Cross-city:** `result`/`motion_type` are Magna-native — aggregate only via `motions_std.csv`
  + the repo-root `crosswalks/`, never the raw strings.

## Regenerate each derived layer
```
python3 build_weeks.py                                   # weeks/ (Tuesday grid)
python3 db/build_db.py && python3 db/build_referrals.py  # db/civic.db (idempotent)
python3 scripts/validate_city.py magna_city_council      # conformance report
python3 fetch_new.py --probe                             # read-only: list new portal docs
```
Canonical truth is the flat CSVs + minutes markdown + retained `raw/`; never hand-edit
`weeks/` or the `.db`.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers (own CLAUDE.md/AVAILABILITY.md; all validate PASS; core untouched).
Dual-portal: CivicPlus (2022+) + PMN (bodies 5803/1559/CRA 6925, township era).
- **`packets/`** — 297 STORED (1.33 GB), Council 161 / CRA 19 / PC 117; dual-portal mandatory
  (CivicPlus = thin agendas, PMN = the real bundles). Section-cut (2026-07-16): 204 MSD staff-report
  sections cut (PC 186 / Council 18; CRA honest zero) across three template eras, 204/204 boundary-verified.
- **`housing_plans/`** — 9 rows; 2021 GP + 2022 MIH plan (MSD-hosted); reports every state year.
- **`ordinances/`** — 239 instruments (86 ord + 153 res, 55 land-use) from MunicipalCodeOnline S3;
  131 high-linkage (mind the parallel ord/res numbering).
- **`pmn_backfill/`** — 20 recovered: council (incl. **4 Aug–Dec 2020 COVID-era regular** added
  2026-07-17 + 3 special-workshop) + 8 CRA minutes (CRA record tripled, body 6925).
  ✅ **16 promoted into the vote layer** (67 motions, `provenance=pmn_minutes`; the 3 workshops
  are zero-motion, the 2025-11-18 CRA DRAFT stays a sidecar — re-checked 2026-07-17, still
  draft-only). 5 Aug–Dec 2020 council dates are genuine publish gaps (`minutes_unrecovered.csv`);
  the 2024-12-10 CRA was CANCELLED, 2026-05-12 CRA minutes pending (`pmn_exceptions.csv`).
- **`transcripts/`** — audio-only: 457 PMN MP3s (370 live / 87 purged), 0 captions; no video any era.
- **`campaign_finance/`** — 63 filings; township 2016–2021 + 2025 city complete (site not
  Cloudflare-blocked); 2023 EasyVote-blocked gap. **13 scanned 2021+2025 filings transcribed to
  `vision/*.json` 2026-07-17 (Read-tool, $0 API); no structured layer (owner-gated).**
