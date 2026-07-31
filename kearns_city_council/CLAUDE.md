# Kearns City Council — how to answer questions with this repo

Canonical datasets about the **City of Kearns** (Salt Lake County, Utah) — City
Council + Planning Commission votes/minutes, elections, geo. Modeled on the SLC
reference repo + the Taylorsville/South Jordan templates; conforms to
`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (`scripts/validate_city.py`).
**Data floor: 2017** (Kearns Metro Township took effect 2017-01-01 — full history).
Read `README.md` for the human overview, `VERIFICATION.md` + `_audits/` for QA.

## The structural facts that make Kearns different

1. **TWO governing regimes, one hard seam (city conversion 2024-05-01 / first city
   election Nov 2025).**
   - **Metro-township era (2017 – 2025):** a **5-member council** (seats 1–5, later
     districts 1–5) that **elected its own Chair**, styled "**Mayor**" in the
     minutes (e.g. "Mayor Kelly Bush, Chair, presided"). **No separately-elected
     mayor.** A `Mayor <Name>, Chair` in a township-era roll is one of the five
     councilmembers, not a distinct executive. Max roll = 5 (the five members).
   - **City era (Jan 2026 →):** a **directly-elected Mayor + 4 district
     councilmembers**. **⚠ THE MAYOR VOTES.** City-era full-council motions tally
     **5-0** while only 4 councilmembers exist, so the 5th vote is the mayor's
     (verified on the `2026-05-11` rolls; Mayor **Jesse Valdez**, Utah's first
     Hispanic mayor). **Max city-era roll = 5 INCLUDING the voting mayor.** This is
     the OPPOSITE of Taylorsville (mayor doesn't vote) and matches Millcreek.
   Both eras top out at 5 but with different composition — mind the seam when
   attributing votes or computing a denominator.

2. **Narrative-tally minutes (Millcreek / South-Jordan-like).** Motions record
   **mover + seconder + a numeric tally** ("Vote was 5-0, unanimous in favor"), NOT
   a per-member roll call. The majority is **honestly unnamed**; only
   **dissenters/abstainers are named** ("…with Council Member Colby abstaining").
   `COUNCIL MEMBERS PRESENT:` gives attendance. → a blank `member`/`vote` on a
   unanimous motion is a source limit, **not** missing extraction. **Exception:** some
   2018-2023 township minutes print a *full named roll call* ("Roll was called…Council
   Member Schaeffer 'Nay,' …Mayor Bush 'Aye'"); those per-member Ayes/Nays ARE captured
   verbatim. So **36 named vote rows** now exist (32 council — 22 Aye / 8 Nay / 2
   Abstain, all from named roll calls + the Colby abstain; 4 PC abstains). **5 contested
   council motions** (up from 1): the 2019-09-09 3-2 pass, the 2019-10-14 2-3 fail, an
   Alan Peterson abstain (2023-08-14), and the Colby 4-0 abstain (R2026-12).

3. **Portal = Utah PMN; the city site is Cloudflare-blocked.** `kearns.utah.gov`
   serves a JS challenge to every bot (browser UA included) → not scrapable. The
   canonical acquisition source is **Utah Public Notice**: **council body 5823**,
   **PC body 1561**. Minutes attach to the NEXT meeting's notice
   (`/pmn/sitemap/notice/<id>.html` → `/pmn/files/<fileId>.pdf`).

4. **The Planning Commission is Kearns's own body but MSD-staffed.** Minuted by
   Greater Salt Lake **MSD Planning & Development** ("MEETING MINUTE SUMMARY"
   letterhead, recorder Wendy Gurr). Land-use cases key **`OAM<YYYY>-<NNNNNN>`**
   (e.g. `OAM2021-000388`) — the cross-body referral bridge; the PC recommends to
   the Council. Meets **1st Monday**; council meets **2nd Monday** (both Monday).

5. **OCR seam in the council record.** 22 of the 117 council files are `format=ocr`
   (2024-era + scattered township/2025 scans); 95 are born-digital text (incl. 1 `.docx`
   converted via `textutil`); PC is all born-digital. OCR is faithful — only the
   source's decorative `♦♦♦` separators garble (cosmetic).

## Coverage — the township council back-catalog was harvested (2026-07-12)

Council-family text minutes on disk now run **2018-07-09 → 2026-05** (119 files, 501
motions: 117 Council files / 492 motions + **2 CRA files / 9 motions**, promoted
2026-07-16 — see below).
The original build wrongly logged the 2017-2023 township era as "audio-only / genuinely
absent"; the 2026-07-12 audit disproved that (written "Meeting Minutes" attachments ARE
on PMN body 5823), and the back-catalog was harvested: enumerating all 255 body-5823
notices found 111 township meetings with a Meeting-Minutes attachment, of which **85
were pulled** (2018-07 → 2023; 84 `.pdf` + 1 `.docx`; OCR where scanned) and carved.
`minutes_unrecovered.csv` now holds **41 genuine gaps**, each with an accurate reason:
**25 township meetings 2017-01 → 2018-06** whose minutes WERE published but whose PMN
file blob is **purged** (pre-~July-2018 `file_id` < ~450000 now 404; notice link stale;
not on the Internet Archive) → a file-rot gap, recoverable only if PMN restores them;
**7** meetings with only agenda + MP3 audio (never minuted); **9** recent
not-yet-posted. **The PC 2017-2018 gap IS genuine** (agenda+packet only, confirmed) —
but the PC **2019-04-08** row was FALSE (minutes were on PMN under a non-"Minutes"
filename): recovered, promoted 2026-07-16, row removed (PC now 44 docs / 199 motions,
`minutes_unrecovered.csv` 23 rows).
✅ **The CRA is no longer an empty body (2026-07-16):** the Kearns **Community
Reinvestment Agency** (Utah 17C, created by Ord 2025-O-06; the council sits as the
board, **Chair Bush votes**) has its own PMN body **9273** — its 2 real 2025 meetings
(2025-07-14, 2025-09-08; the other 5 noticed were cancellations) are promoted into
`meeting_minutes/` as **`body=CRA`** (9 motions, all unanimous tally-only,
`provenance=pmn_minutes`). Both `all_votes.csv` files carry a documented trailing
14th **`provenance`** column since 2026-07-16 (`minutes` = audited primary;
`pmn_minutes` = the 3 promoted PMN-backfill docs).
Note: some 2018-2023 minutes print a full named roll call — those per-member Ayes/Nays
are captured verbatim (so contested council motions = 5, not 1), and the township
roster adds **Ruby Brown** (a township-era 5th seat).

## Elections — from RAW SOVC (canonical file is corrupt for Kearns)

`election_results/kearns_races.csv` is **authoritative**, parsed directly from the
raw Salt Lake County SOVC workbooks — NOT from the shared
`salt_lake_county/elections/slco_municipal_results_long.csv`, which is **corrupted
for Kearns** (2019 dropped; the 2025 `SheetNN→contest` map merged other cities'
candidates under "CITY OF KEARNS MAYOR"). Kearns is intentionally excluded from the
county `CITY_PATTERNS`, so the federated county-grain `election_result` tag for
Kearns is unreliable — use `kearns_races.csv`. (Logged in repo-root `TODO.md`.) The
2025 mayor result (Valdez 1,932 / 57.64% def. Snow 1,420) is externally verified.
Exclude the Oquirrh Park / Kearns Improvement (water) District / Kearns MSD decoys.

## Which artifact for which question

- **Aggregate / time-series** → `meeting_minutes/all_votes.csv` +
  `planning_commission/all_votes.csv` (+ `motions_std.csv` for normalized
  outcome/tallies/`motion_type_std`; `result`/`motion_type` are city-verbatim —
  cross-city comparison goes through `motions_std.csv` + repo-root `crosswalks/`).
  Remember the tally-only style (§2 above).
- **Cross-body / project** → `db/civic.db` (read `db/SCHEMA.md`; views
  `v_referral_chain`, `v_project_timeline`, `v_member_record`, `v_contested`). The
  OAM case number is the referral bridge; the Council keys to ordinance/resolution
  numbers, so PC→Council links fall to subject + date (2 medium links today).
- **Meeting context** → `weeks/<Monday-week>/summary.md`.
- **By member** → join `election_results/kearns_races.csv` winners ↔ votes on
  person + year + district (normalize the UPPER-CASE election names).
- **By address** → `geo/address_to_district.py` (District 1–4, city-era only; the
  mayor is citywide and never returned). D2/D4 are authoritative from the 2025 SOVC;
  D1/D3 are an honest unsplit residual.

## Honesty rules (collection cardinal rules apply)

- **Never fabricate.** Blank `member`/`vote` = tally-only motion; header-only
  `all_comments_clean.csv` = city publishes none; `minutes_unrecovered.csv` = meeting
  real, minutes not on disk (⚠ but for 2017-2023 council, minutes ARE recoverable —
  see Coverage).
- **City-faithful values are never overwritten.** `result`/`motion_type` are
  verbatim; normalized fields live alongside (`motions_std.csv`, crosswalks).
  Corrections go through documented override files, never in-place edits.
- **Derived layers (`db/`, `weeks/`) are regenerated, never hand-edited.**

## Regenerate

```
python3 build_weeks.py                                   # weeks/ (MEETING_WEEKDAY = Monday)
python3 db/build_db.py && python3 db/build_referrals.py  # db/ (idempotent)
python3 scripts/validate_city.py kearns_city_council     # 23 PASS / 3 WARN / 0 FAIL
                                                         # (2 WARNs = the documented
                                                         # provenance extension column)
python3 fetch_new.py                                     # probe PMN 5823 / 1561
```

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join by `date` (+ `body`). ⚠ City site `kearns.utah.gov` is
Cloudflare-blocked — most sources route through PMN + the MSD site + MunicipalCodeOnline S3.
- **`packets/`** — **80 packets STORED (584 MB)** from PMN (council body 5823, PC 1561): Council
  26 + **CRA 1** + PC 52; 2019→2026. 41 PC packets 2011→2018 are PMN blob-purged (`file_id
  <~457000`); township council packets were never bundled (loose per-ordinance PDFs). One GET
  per body via `notices.html?id=<body>&page=400` enumerates the whole attachment inventory.
  - **doc_class layer** (2026-07-16): 10 staff reports classified (9 broken-out + 1 mis-shelved
    recall catch; containers honestly unlabeled) — see packets/CLAUDE.md.
- **`housing_plans/`** — **8 rows**: 2020 General Plan + Resilience element, 2022 MIH Plan +
  adopting Res 2023-01-02, + 4 state excerpts. Kearns reports every state year ("Metro Township"
  → "Kearns city"). All city docs from the MSD CivicPlus site (`msd.utah.gov/DocumentCenter/`),
  found via the state report's "Link to Plan/Ordinance" fields.
- **`ordinances/`** — **223 instruments (94 ord + 129 res, 2017–2026; 56 land-use)** from the
  **MunicipalCodeOnline S3 bucket** (`municipalcodeonline.com-new/kearns/`). Linkage **74 high**
  / 7 medium / 142 none (26 minute-cited numbers not yet posted — the not-yet-codified 2025-26
  city era). 104/223 scanned → tesseract. Shared-MSD screened clean (no neighbor ordinances
  mis-filed); excluded county hazard-plan attachments + a "COP TEST" placeholder.
- **`pmn_backfill/`** — PMN entity **1321** (council 5823, PC 1561, **CRA 9273 [found]**). **3
  recovered**: the 2 real CRA minutes (2025-07-14 + 2025-09-08) lighting up the core's empty CRA
  + a bonus PC 2019-04-08 (was on PMN but mis-logged unrecovered — filename lacked the "Minutes"
  token). ✅ **All 3 PROMOTED into the audited layer 2026-07-16** (`body=CRA` in
  meeting_minutes, PC doc into planning_commission; `provenance=pmn_minutes`; false PC
  unrecovered row removed). Council superset CONFIRMED; the 25-meeting 2017-01→2018-06
  township purge VERIFIED genuine (all objects 404, zero Wayback). CRA's other 5 noticed
  meetings were cancellations.
- **`transcripts/`** — HYBRID: the city YouTube `@KearnsCity` has **11 ASR-captioned city-era
  council streams (2026, all fetched)** + a deep PMN meeting-audio archive (**276 MP3s
  2016→2026; 218 live / 58 purged** — the 2017-18 blob purge again). 218 Whisper candidates,
  township-era (2019–2025) highest-value (no pre-2026 video transcript; narrative-tally minutes
  leave the majority unnamed). Gotcha: the channel has only a `/streams` tab, no `/videos`.
- **`campaign_finance/`** — **38 township filings (2016–2021) COMPLETE** from the SLCo Clerk
  static metro-township-councils archive. **2023 + 2025 are honest-empty-BLOCKED**: 2023 moved
  to an auth-gated EasyVote SPA; 2025 city-era filings live only on the Cloudflare-blocked city
  site (11 in `unrecovered.csv`; 2025 PROVEN to exist via a Wayback landing-page capture). 38
  scanned; acquisition only. Excluded the Kearns Improvement (water) District decoy.
