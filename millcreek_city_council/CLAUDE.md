# Millcreek City Council — data repository

Canonical datasets about the Millcreek City Council, Planning Commission, and Community
Reinvestment Agency (CRA), modeled on the Salt Lake City reference repo and conforming to
the collection-wide standard at `/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with
`scripts/validate_city.py`). Built by the `build-city-data-repo` skill. **Data floor: 2016**
— Millcreek incorporated **Dec 28, 2016**, so the short history (council from 2016-12, PC
from 2017-02) is the city's *entire* record, **not a 2020-floor gap**.

```
meeting_minutes/      City Council + CRA minutes (markdown) + extracted votes (all_votes.csv,
                      motions_std.csv) + retained raw/ originals + fetch_new.py refresh
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md — comments are IN-PACKETS (a Provo-style harvest is a
                      documented pending follow-up, NOT an honest-empty result)
election_results/     Salt Lake County results filtered to Millcreek council+mayor races
geo/                  precinct boundaries + address/point -> council district tool
db/                   relational SQLite (build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying minutes + votes (+ comments) together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Monday = 0)
recon.md              map of this city's data sources (provenance) — written BEFORE
                      acquisition; portal vendor, URL patterns, and the honest-gap record
VERIFICATION.md       independent QA + external election cross-check (REQUIRED; extended
                      with dated addenda whenever the data is repaired or re-audited)
```

## The three structural facts that make Millcreek different
1. **The MAYOR VOTES.** Millcreek is a five-member council-mayor form: **4 district members
   (D1–D4) + a citywide Mayor who is a full voting member.** A complete council roll call
   therefore tops out at **5** (not 4). Treat a 5-vote tally as complete; the mayor appears
   in the roll ("… and Mayor Silvestrini voted yes"). This is unlike most cities in the
   collection (e.g. South Jordan, where the mayor is uncounted). See `meeting_minutes/CLAUDE.md`.
2. **Named roll-call: 2017 (recovered) + ~2022→present; 2018–2021 is tally-only by source.**
   Most early minutes use collective phrasing (*"All Council Members voted yes. The motion
   passed unanimously"*) naming **no** individual voters; per-member prose roll calls (*"Member
   X voted yes, Member Y voted yes…"*) begin ~2022. **Exception — 2017 was RECOVERED
   (2026-07-19):** 2017 minutes DO name every voter in a **tabular en-dash roll call after the
   outcome** (*"…voting as follows: Councilmember Uipi – Aye / … / Mayor Silvestrini – Aye"*),
   which the prose parser had missed → they were tally-only. The `parse_endash_votes` grammar
   recovered **362 named Aye rows across 77 motions** (all unanimous, only the five seated
   members, excused members correctly omitted; 2018+ byte-stable). **2018–2021 remains genuinely
   tally-only** (the tabular roll was dropped after 2017). This is a **source-format change, not
   an extraction miss** — never fabricated. **Member-level vote analysis is meaningful for 2017
   and 2022→present.** Named-vs-tally-only motions by year: 2017 [77/97] 2018 [0/259] 2019
   [4/235] 2020 [5/253] 2021 [6/255] 2022 [70/158] 2023 [222/0] 2024 [236/1] 2025 [253/0] 2026
   [139/0].
3. **CRA is an in-record body, not a separate portal.** The Council convenes as the Millcreek
   Community Reinvestment Agency (Utah 17C). CRA files live in `meeting_minutes/` and every
   CRA motion is tagged `body=CRA` (58 files · 246 motions); the same 5 people appear as
   "Board Member <Name>" / "Chair <Name>" = the councilmembers / mayor.

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per
  document on disk; unrecoverable meetings live in `minutes_unrecovered.csv`, never as
  stub/wrong-doc rows. `source` = `civicplus` (AgendaCenter) for every file. `format` is
  `text`/`scanned` (council) or `pdf-text`/`ocr` (PC) — even the "text" PDFs are OCR-derived
  (see below).
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`);
  `result` and `motion_type` are city-verbatim — **cross-city comparison goes through
  `motions_std.csv`** (normalized outcome/tallies/motion_type_std) and the repo-root
  `crosswalks/` tables.
- Raw originals are retained under each dataset's `raw/` and are never deleted.

## The OCR caveat (applies to the WHOLE corpus)
The AgendaCenter PDFs are **scanned / bad-text-layer**, so `pdftotext` output carries
systematic garble (`Councn Member`, `TTipi voterl yes`, `Coinmission`, `01son`). The vote
extractors **fuzzy-match** garbled surnames against the fixed roster and never invent a name;
the corpus screener + verification confirmed the garble did **not** propagate into fabricated
data (distinct named voters == exactly the roster). Read the raw text expecting corruption.

## The join key
Everything keys to the **council meeting weekday (Monday** — 2nd & 4th Monday, Work Meeting
5 p.m. + Regular 7 p.m., one combined minutes doc per meeting-day). The **PC meets Wednesday**;
its records join on their own date. `build_weeks.py` buckets every record onto the Monday
grid (`MEETING_WEEKDAY = 0`). Elections are point-in-time (Nov, odd years — plus the founding
Nov 2016) and are NOT in the weekly bundles — they join by **person + year + district**
(normalize names first; election names are UPPER-CASE with `(NON)`/`(NP)` suffixes).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables — `meeting_minutes/all_votes.csv`
  (+ `motions_std.csv`) and `planning_commission/all_votes.csv`. Remember the 2022 named-vote
  seam: do not read pre-2022 blank-member motions as missing extraction.
- **Relational / cross-body** (PC recommendation → council outcome; CRA co-actions; member
  records): `db/millcreek.db` — read `db/SCHEMA.md` first; start from views `v_referral_chain`,
  `v_project_timeline`, `v_member_record`, `v_contested`. The `referral` layer is reconstructed
  + scored (34 links: 10 high / 19 medium / 5 low) — respect the confidence column.
- **Meeting-level / contextual**: the `weeks/<Monday-date>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/`) ↔ votes. Mind the roster drift —
  **Marchant → DeSirant (D2, Jan 2022)** and **Jackson (D3 → Mayor) + Handy (→ D3), both by
  Nov 2025 appointment.**
- **By geography**: `geo/address_to_district.py` resolves an address to District 1–4 (the
  Mayor is citywide, never returned). ⚠ The district layer is the **2022–2032 redistricting
  vintage**; pre-2022 addresses near a moved boundary may mis-assign.

## Elections — three genuinely unusual facts (all verified against outside sources)
- **RCV in 2021 & 2023** (Utah municipal pilot): by-candidate/by-precinct counts are
  *first-choice*; the seat `winner` is the *final-round* winner. **2021 D2 diverges** — Clark
  led first choice but DeSirant won the runoff (negative first-choice margin, flagged
  `voting_method='ranked choice (RCV)'`).
- **2025 Mayor Jackson was APPOINTED, not elected** — the council selected sitting D3 member
  Jackson to finish Silvestrini's term (Nov 2025); there is **no 2025 mayoral race row** (not
  a gap).
- **2023 Mayor + D1 were cancelled-uncontested** (only the incumbent filed → Utah cancelled
  the races): blank vote fields, `voting_method='uncontested (election cancelled)'`, no
  precinct rows — **no counts fabricated**.

## public_comments — IN-PACKETS harvest BUILT 2026-07-19; `?packet=true` ceiling CLOSED same day
Millcreek publishes **genuine verbatim resident comments**, but only bundled **inside the PC
packet PDFs** (forwarded resident emails, the FormCenter "Public Comments" web-form submissions,
and standalone "Public Comments from Residents" letters). No standalone comments page / eComment
archive exists. `all_comments_clean.csv` = **27 genuine written comments** (`source=agenda_packet`,
SLC 14-col schema, 100% dated) — by year **2020 ×12, 2021 ×5, 2022 ×2, 2024 ×5, 2026 ×3**; by
channel web-form 10 / letter 6 / email 2 / Minutes-view 9. **Two waves:** (1) the 9 from the
retained AgendaCenter **Minutes-view** docs (`harvest_packets.py` + `extract_packet_comments.py`);
(2) **+18** from the large **`?packet=true`** land-use packets — a *different, much larger* PDF
whose staff-report appendices the Minutes-view omits. Wave 2 = `harvest_packet_true.py` (fetched
all 100 PC `?packet=true`, ~4.8 GB, **99 ok / 1 not_pdf**, sha256'd, **binaries DISCARDED per
SCHEMA_SPEC §9** — ledger `packet_true_fetch.csv`) → `extract_packet_true_comments.py` (3 channels,
strict resident-only gates; **180 dropped**: applicants/developers, consultants, staff, the
Community-Council recs, forwarder wrappers, un-signed/OCR) → `build_comments.py` (merge +
content-dedup + prune). **Residual honest ceiling:** un-signable OCR letters, image-only pages,
doc757 (2023-12-20 no combined packet), pre-2018 agenda-only era. Clerk in-minutes speaker
paraphrase is deliberately EXCLUDED (not written comments). Comments feed `weeks/` — rebuild after
changes. See `public_comments/AVAILABILITY.md` + `public_comments/CLAUDE.md`. Do NOT treat as
honest-empty.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`.
Canonical sources of truth are the dataset folders (flat CSVs + minutes markdown + retained
`raw/`); never edit files under `weeks/` or the .db. Rebuild weeks/ after ANY change to the
canonical CSVs. Each subfolder has its own CLAUDE.md/SCHEMA.md with build details.

## Keeping it current
`python3 fetch_new.py --probe` (default; read-only) lists AgendaCenter Minutes items newer
than the index max for each dataset (council = cat3 + CRA cat7; PC = cat2) plus a read-only
PMN (Millcreek City Council body 5741; PC 5815 / CRA 6367) cross-check. `--fetch [--dataset meeting_minutes|
planning_commission]` downloads new Minutes PDFs → `raw/` → markdown (OCR-aware) →
`minutes_index.csv`, then runs the dataset's `extract_votes.py` + `validate_votes.py` (PC
routes through the authoritative `convert.py` + `_pc_links.json`). Rebuild db + motions_std +
weeks afterward (the CLI prints the reminder). Idempotent + resumable (skips docs already on disk).

## Analysis guidance
- Councils are high-consensus — **contested votes (any Nay/Abstain/Recuse) are the signal**;
  Millcreek records rich named roll calls (4,672 named vote rows, incl. the recovered 2017
  en-dash rolls) so the contested signal (7 contested motions) is legible where members are
  named. `summary.md` surfaces them per week.
- Motion types: city-native taxonomy in `all_votes.csv` (see `meeting_minutes/CLAUDE.md`);
  standardized categories in `motions_std.csv`.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`, and
  `VERIFICATION.md` — read those before quantitative claims (especially the 2022 named-vote
  seam and the 2022-vintage geo boundary).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-06)
Six new source layers, each with its own `CLAUDE.md` + `AVAILABILITY.md` and each passing
`validate_dataset.py`. **None modify the core minutes/votes/comments/elections layer.** Join
to `all_votes.csv`/minutes by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **552 documents, INDEX-ONLY** (340 `full_packet` Council 186 / CRA 54 / PC
  100, 2018–2026 + 212 thin `agenda_packet`). Millcreek's AgendaCenter serves the combined
  **Agenda + Packet** PDF at the same `docId` as the Minutes view, so those PDFs **already live
  on disk** in `meeting_minutes/raw/` + `planning_commission/raw/`; each `full_packet` row points
  there via `path` (`stored_locally=yes`, 335/340) instead of re-storing ~1.2 GB.
  **PC `full_packet` rows carry verbatim resident-comment letters — the IN-PACKETS comment corpus**
  (`public_comments/` marks it a pending Provo-style harvest; this index only flags where they
  live). Join `(date, body[, meeting_type])`; `body ∈ Council/CRA/PlanningCommission`.
- **`housing_plans/`** — **7 docs**: **Millcreek Together General Plan** (`View/3193`, MIH element
  **embedded**, no standalone PDF) + adopting **Ordinance 22-44** (2022-09-26 — the MIH element of
  record, **joins `all_votes.csv`** at that council meeting + an upstream PC recommendation) + city
  **Aug-2024 Housing Report** + state HCD MIH compilations **2023/24/25** + **SB 34** summary
  (Millcreek page ranges). Born-digital/clean. Caveats: GP cover "Amended December 12, 2026" is a
  placeholder (cite in-text content); 2023/24 state compilations bleed **Murray** text. Not joined
  to `db/`.
- **`ordinances/`** — **550 adopted ordinances 2016–2026** (`ORD YY-NN`) from the
  **municipalcodeonline.com S3 back-catalog** (bucket `municipalcodeonline.com-new`, us-west-2,
  path-style) — an independent second source per ordinance NUMBER. **~39% land-use** (213).
  `match_confidence` **346 high** (number cited in a council motion AND the PDF month+year match) /
  **84 medium** (number-only match) / **120 none** (no motion cites it — mostly 2016–18 pre-seam
  procedural). 13 cited-but-no-document numbers in `citations_without_document.csv`. **⚠ Ordinance
  17-99 is an inauthentic test/template doc** (John Doe voters, "(joke)" clause) — flagged, exclude
  from analysis. Join by ordinance number cited in `all_votes.csv` motion text.
- **`pmn_backfill/`** — Utah PMN cross-check. **Bodies (live entity chain, municipality id=1279):
  Council 5741 · PC 5815 · CRA 6367** (corrects the base `fetch_new.py`'s stale **1031** council
  id). PMN is thin (city double-posts to AgendaCenter → repo is a near-total superset). **1
  recovered** (2017-11-21 Board of Canvassers, tally-only) + **1 dead** (2018-03-20, already in
  `minutes_unrecovered.csv`).
- **`transcripts/`** — **92 meeting videos mapped** (58 Council + 34 PC, 2025-01-06 → 2026-06-22),
  **10 ASR captions sampled** (SAMPLE-ONLY). **Real meeting video EXISTS** via the third-party
  **`@UtahRecord` / `millcreek.openutah.org`** mirror; **the city's own YouTube is PR-only**.
  **2025+ only** (pre-2025 = minutes-PDF only). **Whisper NOT run**; ASR is contextual/color only,
  never authoritative; `body` label is the mirror's (unverified — some "CityCouncil" videos are
  URCA). Join by meeting date.
- **`campaign_finance/`** — **ACQUISITION LAYER ONLY** (`extraction_method=none`; 31 text + 10
  scanned). **41 filings / 4 cycles** (2019/2021/2023/2025), Mayor + D1–D4; **2019 via Wayback**.
  **39/41 filings join `election_results`**; the 2 non-joins are **appointment artifacts** (Jackson
  2025 Mayor + Handy 2025 D3, both appointed Nov 2025 — `in_election_results=no`). 2023 Mayor +
  D1 cancelled-uncontested → correctly no filing. **DOUBLE-COUNT TRAP: do NOT sum filings** (2021 =
  one combined bundle per candidate; other cycles interim + summary). Some 2025 filings city-
  redacted. **2016/17 unpublished** (pre-online paper era).
