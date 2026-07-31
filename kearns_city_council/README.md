# Kearns City Council — civic data repository

Canonical datasets about the **City of Kearns** (Salt Lake County, Utah): City
Council + (MSD-staffed) Planning Commission meeting minutes as markdown, extracted
roll-call votes, municipal election results, and an address→district tool. Modeled
on the Salt Lake City reference repo, conforming to the collection standard
(`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md`; check with `scripts/validate_city.py`).
Built by the `build-city-data-repo` skill. **Data floor: 2017** (Kearns Metro
Township took effect 2017-01-01 — 2017-present is full history, not a gap).

## The one thing to know: two governing regimes

Kearns was a **metro township 2017 → 2024**, converted to a **CITY on 2024-05-01**
(Utah H.B. 35), and held its **first city election Nov 2025** (officials seated
Jan 2026). This creates a hard structural seam:

- **Township era (2017 – 2025):** a **5-member council** (seats 1–5) that **elected
  its own Chair** (styled "Mayor" in the minutes); **no separately-elected mayor**;
  municipal services from the Greater Salt Lake **MSD**.
- **City era (Jan 2026 →):** a **directly-elected Mayor + 4 district councilmembers**.
  **⚠ THE MAYOR VOTES** — full-council rolls tally **5-0** with only 4 councilmembers,
  so the 5th vote is the mayor's (max council roll = **5**, mayor included). Mayor
  **Jesse Valdez** (elected 2025) is Utah's first Hispanic mayor. (Contrast
  Taylorsville, mayor does not vote; this matches Millcreek's voting-mayor form.)

## Layout

```
meeting_minutes/      City Council minutes (markdown) + votes (all_votes.csv,
                      motions_std.csv) + raw/ PDFs + fetch_new.py
planning_commission/  SAME schemas for the Kearns Planning Commission (MSD-run)
public_comments/      AVAILABILITY.md — HONEST-EMPTY (submit-only; no published archive)
election_results/     SLCo results filtered to Kearns council+mayor (from RAW SOVC)
geo/                  precinct-derived District 1–4 polygons + address→district tool
db/                   relational SQLite (build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles (Monday grid) tying minutes + votes
recon.md              provenance map written before acquisition
SOURCES.md/.csv       per-document source index
VERIFICATION.md       independent QA + external election cross-check
_audits/              graded audit reports
```

## Coverage

| Dataset | On disk | Range | Source / format | Notes |
|---|---|---|---|---|
| Council minutes | **117 meetings, 492 motions** | 2018-07 → 2026-05 | Utah PMN body 5823 · OCR + born-digital (incl. 1 .docx) | township back-catalog harvested 2026-07-12; see gaps below |
| CRA (body=CRA, in meeting_minutes/) | **2 meetings, 9 motions** | 2025-07 → 2025-09 | Utah PMN body 9273 · 1 OCR + 1 text | promoted from pmn_backfill 2026-07-16; provenance=pmn_minutes |
| Planning Commission | **44 meetings, 199 motions** | 2019-03 → 2026-06 | Utah PMN body 1561 (MSD) · born-digital | OAM land-use case keys; 2019-04-08 promoted 2026-07-16 |
| Elections | 18 races | 2016 → 2025 | raw SLCo SOVC | canonical file corrupt for Kearns → raw parse |
| Public comments | 0 (honest zero) | — | — | submit-only; not published |
| Geo | 4 districts | 2025+ | precinct-derived | D2/D4 authoritative; D1/D3 residual |

### Council coverage (township back-catalog harvested 2026-07-12)

Council text minutes on disk now **run 2018-07-09 → 2026-05**. The 2026-07-12 audit
disproved the earlier build note that the 2017-2023 township council was "audio-only /
genuinely absent" — written **"Meeting Minutes"** attachments *are* published to PMN
body 5823 across the township era. Enumerating the full body found 111 township
meetings carrying a Meeting-Minutes attachment; **85 were harvested** (2018-07 → 2023,
84 PDF + 1 .docx; format=text/ocr) and added to disk. What genuinely remains
unrecovered (now 41 rows in `meeting_minutes/minutes_unrecovered.csv`, each with an
accurate reason):

- **25 township meetings, 2017-01 → 2018-06** — the Meeting-Minutes attachment WAS
  published, but PMN has **purged the file blob** from its pre-~July-2018 store
  (`file_id` < ~450000 now 404; the notice link is stale; not on the Internet Archive
  either). Recoverable only if PMN restores those old files.
- **7 township meetings** that posted only an agenda + MP3 audio — no minutes ever
  published (a genuine honest gap).
- **9 recent meetings** not yet approved/posted at retrieval.

(The PC 2017-2018 gap, separately, is genuine — those notices carry agenda + packet
only.) See `_audits/audit_2026-07-12.md`.

### Other honest gaps

- ~~**CRA** … 0 CRA rows~~ **RESOLVED 2026-07-16**: the CRA's own PMN body (9273) held
  2 real meetings' minutes (its other 5 noticed 2025 meetings were cancellations) —
  both promoted into `meeting_minutes/` as `body=CRA` (9 motions,
  `provenance=pmn_minutes`).
- **Comments** are submit-only (in-meeting 3-min input + email to the MSD recorder);
  no published archive exists — an honest zero.

## Which artifact for which question

- **Aggregates / time series** → the flat CSVs `meeting_minutes/all_votes.csv` and
  `planning_commission/all_votes.csv` (+ `motions_std.csv` for normalized fields).
  These are **narrative-tally** minutes: on a unanimous motion only the mover +
  seconder (and any dissenter/abstainer) are named — a blank member list on a
  unanimous motion is NOT missing extraction.
- **Cross-body / project questions** → `db/civic.db` (read `db/SCHEMA.md` first;
  views `v_referral_chain`, `v_project_timeline`, `v_member_record`, `v_contested`).
- **Meeting context** → the `weeks/<Monday-week>/` bundles (`summary.md` first).
- **By member** → join election winners (`election_results/`) ↔ votes on person +
  year + district (election names are UPPER-CASE).
- **By address** → `geo/address_to_district.py` (District 1–4; city-era only).

## Regenerate

```
python3 build_weeks.py                                   # weeks/ (Monday grid)
python3 db/build_db.py && python3 db/build_referrals.py  # db/ (idempotent)
python3 scripts/validate_city.py kearns_city_council     # conformance
python3 fetch_new.py                                     # probe PMN 5823/1561 for new docs
```

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers (own CLAUDE.md/AVAILABILITY.md; all validate PASS; core untouched).
City site is Cloudflare-blocked → sources route through PMN + MSD + MunicipalCodeOnline S3.
- **`packets/`** — 80 STORED (584 MB), Council 26 / CRA 1 / PC 52; 41 pre-2018 PC packets purged.
  doc_class (2026-07-16): 10 staff reports classified (9 broken-out + 1 mis-shelved recall catch).
- **`housing_plans/`** — 8 rows; 2020 GP + 2022 MIH plan (MSD-hosted); reports every state year.
- **`ordinances/`** — 223 instruments (94 ord + 129 res, 56 land-use) from MunicipalCodeOnline S3;
  74 high-linkage.
- **`pmn_backfill/`** — 3 recovered: 2 CRA minutes + 1 bonus PC (**all 3 promoted into the
  audited layer 2026-07-16**, `provenance=pmn_minutes`); the 2017-18 township purge verified
  genuine.
- **`transcripts/`** — hybrid: 11 ASR-captioned 2026 YouTube streams + 276 PMN MP3s (218 live);
  Whisper candidates.
- **`campaign_finance/`** — 38 township filings (2016–2021) complete; 2023 (EasyVote) + 2025
  (Cloudflare) honest-empty-blocked, proven to exist.
