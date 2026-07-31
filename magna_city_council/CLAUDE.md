# Magna City Council — data repository

Canonical datasets about the **Magna City Council** (with its in-recess **Community Reinvestment
Agency, CRA**) and its **MSD-staffed Planning Commission**, modeled on the Salt Lake City
reference repo and conforming to the collection-wide standard at
`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with `scripts/validate_city.py`). Built by
the `build-city-data-repo` skill. **Data floor: 2017** (Magna was seated as a Salt Lake County
metro township on 2017-01-01 — full history from incorporation, not a gap), though the on-disk
**council record begins 2018-07-17** and **PC 2019-03-14** because the earlier minutes were never
published or were purged (see "Known gaps").

```
meeting_minutes/      Council + CRA minutes (markdown) + extracted votes (all_votes.csv,
                      motions_std.csv) + retained raw/ originals
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md — comments are HONEST-EMPTY (submit-only; no published
                      written-comment archive) — all_comments_clean.csv is header-only by design
election_results/     Salt Lake County results filtered to Magna council+mayor races
geo/                  precinct boundaries + address/point -> council district tool
db/                   relational SQLite civic.db (build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Tuesday = 1)
fetch_new.py          incremental refresh probe (CivicPlus catID 3 + PMN bodies 5803/1559)
recon.md              provenance map written BEFORE acquisition; portal vendor, URL patterns,
                      the honest-gap record. ⚠ its "Trustee" member-noun guess was WRONG —
                      the minutes say "Council Member" in ALL eras.
SOURCES.md            human-readable source catalog (companion: sources.csv)
VERIFICATION.md       independent QA + external election cross-check (REQUIRED)
```

## The structural facts that make Magna different

1. **The presiding officer's vote flips at a form-of-government seam.** Magna was a metro
   **township (2017)** and became a **CITY on 2024-05-01** (Utah **H.B. 35**). The vote extractor
   keys off the **meeting date** because the presiding officer changed KIND:
   - **2017 – 2025 (township + early city):** a 5-member district council with **no separately
     elected mayor**; the council elected its own **Chair, titled "Mayor"** (Dan Peay through 2023,
     then Eric Barney 2024–25). **That Chair-"Mayor" is one of the five and VOTES** (verified
     2024-12-10: "AYE: … Mayor Barney … FINAL RESULT: 4-0").
   - **2026+ (city with elected executive):** first directly-elected **Mayor Mick Sudbury**
     **presides but does NOT vote** (verified 2026-05-26: a `4-0` tally excludes the Mayor).
   - **Net:** **max council roll = 5 in BOTH eras** (0 motions with >5 named voters), but a voting
     Chair (≤2025) becomes a non-voting Mayor (2026+). **Members are "Council Member" in all eras**
     (the recon's "Trustee" was wrong). **Mick Sudbury is the seam in one biography** — a D3
     councilmember who voted through 2025, then the non-voting Mayor from 2026 (so he has both
     voting rows and, post-seam, none). Join member records with the seam in mind.
2. **CRA is an in-record body — and, since 2026-07-16, ALSO a standalone-meeting body.** The
   Council sits as the **Community Reinvestment Agency** (RDA-equivalent) two ways: in-recess/
   one-off captures inside the audited layer (13 motions, `provenance=minutes`) PLUS **standalone
   CRA meetings filed on PMN body 6925** — 7 approved minutes docs (2024-11-12 → 2025-09-23,
   19 motions) recovered into `pmn_backfill/` and **promoted 2026-07-16** with
   `provenance=pmn_minutes` (the CRA regularly met at 5:30 PM before the 6:00 PM council meeting;
   those docs were never on CivicPlus). **CRA total: 32 motions** in `meeting_minutes/
   all_votes.csv` tagged `body=CRA`; members appear as "Board Member <Name>". An 8th recovered
   CRA doc (2025-11-18) is a DRAFT and stays an unpromoted sidecar. (db body table: CRA /
   Council / PlanningCommission.)
3. **Two portals feeding one council dataset.** CivicPlus AgendaCenter (`magna.utah.gov`, catID 3)
   covers **2022+**; **Utah PMN body 5803** covers the township years **2018–2021**.
   **⚠ Fetch PMN files from `www.utah.gov/pmn/files/<id>.pdf`** — the `pmn.utah.gov` host
   302-redirects to the PMN home HTML.
4. **MSD-staffed Planning Commission.** Magna runs its **own** PC (records on **PMN body 1559**),
   staffed by Greater Salt Lake MSD planners; it recommends on Magna land use (rezones keyed
   `REZ####-######`, subdivision plats, conditional uses, text amendments) up to the Council.
5. **Mild PMN-era garble + an OCR seam.** The 2018–2023 PMN PDFs carry systematic
   character-substitution garble (`quonrm`→quorum, `Hoffrnan`→Hoffman) normalized during
   extraction; **21** Apr–Dec-2024 / early-2025 council minutes are signed image scans **OCR'd**
   (`format=pdf-ocr`). Corpus screen: **0 outliers** across both.

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,body,slug,path,source,source_url,format` — one row per
  document on disk; unrecoverable meetings live in `minutes_unrecovered.csv`, never as
  stub/wrong-doc rows. `source` = `civicplus` / `pmn`; `format` ∈ `pdf-text`/`pdf-ocr`/`docx-text`.
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`)
  **+ a documented trailing 14th `provenance` column since 2026-07-16** (`minutes` = audited doc;
  `pmn_minutes` = PMN-promoted doc merged by `meeting_minutes/extract_backfill_votes.py`, whose
  `source` paths point into `pmn_backfill/text/`; run order: `extract_votes.py` THEN
  `extract_backfill_votes.py`);
  `result` and `motion_type` are city-verbatim — **cross-city comparison goes through
  `motions_std.csv`** (normalized outcome/tallies/motion_type_std/land_use_type) and the repo-root
  `crosswalks/` tables. `vote` ∈ Aye/Nay/Abstain/Recuse/Absent (source "EXCUSED" → `Absent`).
- Raw originals are retained under each dataset's `raw/` and are never deleted.

## The join key
Everything keys to the **council meeting weekday (Tuesday** — 2nd & 4th Tuesday, 6:00 PM, Webster
Center). Township-era cadence varied (a few Wednesday meetings). The **PC meets 2nd Thursday**;
its records join on their own date. `build_weeks.py` buckets every record onto the Tuesday grid
(`MEETING_WEEKDAY = 1`). Elections are point-in-time (Nov, odd years) and are NOT in the weekly
bundles — they join by **person + year + district** (normalize names first; election names are
UPPER-CASE, some `(NP)` suffixes).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables — `meeting_minutes/all_votes.csv`
  (+ `motions_std.csv`) and `planning_commission/all_votes.csv`. Remember these are
  **narrative-tally** minutes: on a unanimous motion the majority is honestly **unnamed** (only
  mover + seconder + dissenters/absentees are named). Do NOT read a blank member list as a miss.
- **Relational / cross-body** (PC recommendation → council outcome; CRA co-actions; member
  records): `db/civic.db` — read `db/SCHEMA.md` first; start from `v_referral_chain`,
  `v_project_timeline`, `v_member_record`, `v_contested`. The `referral` layer is reconstructed +
  scored (**3 links, all `medium`, as-rebuilt 2026-07-16** — 2 Council←PC ordinance chains
  surfaced by the promoted 2024-02-27 / 2024-11-26 council minutes + 1 same-night Council←CRA
  Broadway-project-area pair; an earlier "6 links" claim was stale vs the built db) — respect
  the confidence column; the case-number bridge is one-sided (PC cites `REZ…`; Council is
  ordinance/resolution-keyed).
- **Meeting-level / contextual**: the `weeks/<Tuesday-week>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/`) ↔ votes on **person + year +
  district** — and mind the seam (Sudbury councilmember→Mayor; Peay/Barney as voting Chairs).
- **By geography**: `geo/address_to_district.py` resolves an address to District 1–5 (the Mayor is
  citywide, never returned). **Mixed-vintage** — see caveat below.

## public_comments — HONEST-EMPTY (submit-only)
Magna publishes **no** written-comment archive / eComment / correspondence page. Comment is taken
**in person** (sign-up form at the entrance, 2-min limit) plus a QR code to staff; PMN posts only a
meeting **audio MP3**. `all_comments_clean.csv` is **header-only by design**. The clerk's paraphrase
of in-person speakers in the minutes is a **speaker log** (meeting-record notes), **not** genuine
written comments. Treat as a legitimate honest zero — see `public_comments/AVAILABILITY.md`.

## Known gaps / caveats (read before quantitative claims)
- **2017 + Jan–Jun 2018 council minutes (36 meetings) are 404-unrecoverable** on PMN → council
  votes start **2018-07-17**. **PC 2017–2018 (57 meetings) are agenda/audio only** → PC votes
  start **2019-03-14**. Both logged in the respective `minutes_unrecovered.csv`, never stubbed.
- **Board-of-Canvassers certification motions are deliberately excluded** from the vote datasets
  (a distinct statutory body — the council sitting as canvassers to certify an election — not a
  legislative vote). This is why some indexed canvass/work-session files carry 0 motions.
- **Geo is precinct-derived, MIXED-VINTAGE** (D2/D4 2025-high; D1/D3/D5 2019-medium; 4 precincts
  `confidence=none`). Pre-2022 addresses near a moved boundary may mis-assign.
- **Cross-city:** aggregate only via `motions_std.csv` + repo-root `crosswalks/`, never raw
  `result`/`motion_type`.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`. Canonical
sources of truth are the dataset folders (flat CSVs + minutes markdown + retained `raw/`); never
edit files under `weeks/` or the `.db`. Rebuild weeks/ after ANY change to the canonical CSVs.

## Keeping it current
`python3 fetch_new.py --probe` (read-only) lists CivicPlus AgendaCenter (catID 3) and PMN
(bodies 5803 council / 1559 PC) documents newer than the index max, excluding dates already
indexed or logged in `minutes_unrecovered.csv`. `--fetch` downloads new dates' minutes into
`raw/`, converts (OCR-aware) → markdown → `minutes_index.csv`, then runs the dataset's
`extract_votes.py` + `validate_votes.py`. Rebuild db + motions_std + weeks afterward. Idempotent.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join by `date` (+ `body`). Dual-portal city: CivicPlus
(`magna.utah.gov`, accessible) for 2022+ + PMN (bodies 5803 council / 1559 PC / **6925 CRA**;
⚠ fetch from `www.utah.gov/pmn/files/`) for the township era.
- **`packets/`** — **297 packets STORED (1.33 GB)**: Council 161 + **CRA 19** + PC 117; 2019→2026.
  MANDATORY dual-portal — CivicPlus `?packet=true` payloads are THIN AGENDAS; the assembled
  staff-report bundles live only on PMN (a CivicPlus-only harvest would miss the substance). 52
  PC 2017-2018 packets are the confirmed blob purge. Classify PMN packets by filename
  (packet>supporting>staff-report>agenda), not the noisy type-label.
  - **packet SECTION-CUT layer** (2026-07-16): 204 MSD staff-report sections cut (PC 186 /
    Council 18; CRA honest zero) across three template eras, 204/204 boundary-verified — see
    packets/CLAUDE.md.
- **`housing_plans/`** — **9 rows**: 2021 General Plan + appendices, 2022 MIH Plan + adopting
  Ord 22-O-08 (PMN), prior 2019 MIH element — all on the MSD DocumentCenter. Magna present every
  state year ("Magna Metro township" → "Magna city"). The state report's "Link to..." fields
  give the exact MIH-element + adoption URLs (fastest MSD-city discovery path).
- **`ordinances/`** — **239 instruments (86 ord + 153 res, 2017–2026; 55 land-use)** from
  MunicipalCodeOnline S3 (`municipalcodeonline.com-new/magna/` — 3rd confirmed MSD city).
  Linkage **131 high** (all verified) / 10 medium / 98 none. ⚠ Magna numbered township ordinances
  AND resolutions in PARALLEL month-seq sequences — linkage must honor the ord/res word, not the
  bare number. 150/241 sidecars OCR. Excluded county hazard-plan + a scooter-contract decoy.
- **`pmn_backfill/`** — PMN entity **1323** (council 5803, PC 1559, **CRA 6925 [found]**). **20
  recovered** (13 in the 2026-07-16 build + **7 added 2026-07-17 wave-2**: 3 special-workshop +
  **4 Aug–Dec 2020 COVID-era regular council minutes**): missing council minutes (never on
  CivicPlus, missed by the core PMN pull) + **8 CRA minutes — more than TRIPLING the CRA record**
  (repo had 5 dates). PC is a complete superset. The SSL `ArchivedMinutes` slot does NOT apply
  here. The 2017–mid-2018 purge re-confirmed genuine (survivors 404).
  ✅ **PROMOTED**: **16 of 20 docs** merged with `provenance=pmn_minutes` (**67 motions / 67
  rows**; Council 48 + CRA 19) via `meeting_minutes/extract_backfill_votes.py` — the 3 workshop
  docs are zero-motion, the 2025-11-18 CRA doc is a DRAFT (re-checked 2026-07-17: still
  draft-only). **5 Aug–Dec 2020 council dates stay genuine publish gaps** (agenda/audio only →
  `minutes_unrecovered.csv`); the two CRA agency leads resolved — **2024-12-10 CANCELLED**,
  **2026-05-12 minutes-pending** (`pmn_exceptions.csv`); `fetch_new.py` now also probes CRA
  body 6925. Earlier promotion repaired the audited grammar ("passed BY A unanimous vote").
- **`transcripts/`** — AUDIO-ONLY (no YouTube — handles collapse to a Cyprus HS decoy; video is
  live-only Zoom, unarchived). PMN MP3 archive: **457 files 2016→2026; 370 live / 87 purged**
  (all 2016-2018 audio gone, 2019+ fully live). Highest-value Whisper set in the repo — Magna has
  NO video transcript in any era, so the audio is the only verbatim record of the narrative-tally
  meetings (incl. the voting-Chair→non-voting-Mayor seam).
- **`campaign_finance/`** — **63 filings**: township 2016–2021 (SLCo static archive) + **2025
  city-era COMPLETE** (Magna's CivicPlus city site is NOT Cloudflare-blocked, unlike Kearns — so
  the 2025 cycle was fully retrievable). Only 2023 is an honest gap (EasyVote blocked). 56
  scanned / 7 text; acquisition only. Year-attribution OCR-verified from form headers.
  Cross-source flag: 2023 D1/D3/D5 is missing from BOTH finance AND the election layer.
