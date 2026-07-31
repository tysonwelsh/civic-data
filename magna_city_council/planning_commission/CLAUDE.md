# planning_commission/ — Magna Planning Commission (MSD-staffed)

Planning Commission minutes (markdown) + extracted votes for the **Magna Planning Commission**,
`body=PlanningCommission`. Magna runs its **own** PC, **staffed by Greater Salt Lake MSD**
planners; it recommends on Magna land use up to the City Council. Conforms to `SCHEMA_SPEC.md`.

## Contents
```
minutes/<year>/<date>_planningcommission_<id>.md   76 files, 2019-03-14 → 2026-06-11
raw/                                               retained source PDFs (never deleted)
raw/_duplicate_drafts/                             4 quarantined PMN draft copies + README
                                                   (the de-ingested phantoms — see below)
votes/<year>/*.json                                per-meeting extracted-vote records
all_votes.csv                                      13-col standard flat table (303 rows, 302 motions)
motions_std.csv                                    normalized layer (302 rows; 143 land-use-typed)
minutes_index.csv                                  one row per file on disk (76)
minutes_unrecovered.csv                            63 rows: 57 township-era (agenda/audio only) +
                                                   2 from 2019 + the 4 vacated 2023-2025 dates
roster.csv                                         commissioners with first/last seen — DERIVED,
                                                   regenerate with build_roster.py
build_roster.py                                    rebuilds roster.csv (documented rule)
extract_votes.py / validate_votes.py               extraction + conformance
                                                   (validate_votes.py --check-dates = date guard)
```

## Source & format
- **Portal:** **Utah PMN body 1559** (`www.utah.gov/pmn/files/<id>.pdf` — **use the `www.` host**).
  CivicPlus does **not** carry a Magna PC tab; PMN 1559 is the authoritative source.
- **Format:** all **76 born-digital `pdf-text`**. Corpus screen: **0 outliers**, weird_char median
  **0.0003** — the cleanest corpus in the repo.
- **⚠ THE DRAFT-COPY TRAP — the single most important source fact for this dataset.** A PMN
  notice carries minutes in **two** different roles:
  - `YYMMDD_MagnaPC_MinutesApproved.pdf` — the **APPROVED** minutes of **that notice's own**
    meeting. Ingest under the notice date. ✅
  - `<Month> minutes.pdf` (e.g. `July minutes.pdf`) — the **DRAFT of the PREVIOUS meeting**,
    posted with this meeting's agenda packet because this meeting is the one that will APPROVE
    them. Its date is **one meeting earlier** than the notice. ❌ **Never ingest under the
    notice date.**

  Approved copies carry a `**Meeting minutes approved on <later date>**` stamp; drafts do not.
  Ingesting a draft under the notice date manufactures a **phantom meeting** that double-counts
  the previous meeting's motions — which is exactly what happened on the four notices (of 112
  minutes attachments on body 1559) where MSD never posted an approved copy. Guard every ingest
  with `python3 validate_votes.py --check-dates`.

## Vote model
- **Recommendation body.** PC motions "recommend approval/denial of application #REZ####-###### to
  the Magna Council" (a recommendation) or take a final action (plats, conditional uses). Land-use
  cases are keyed **`REZ####-######`** (rezones), plus subdivision plats, conditional uses, site-
  plan/design reviews, and text amendments — **143** of 302 motions carry a land-use type in
  `motions_std.csv`.
- **Tally style.** Unanimous motions print "Commissioners voted unanimous in favor (of
  commissioners present)" — **no per-member Aye list**; only dissenters/abstainers are named
  (**18** named rows total, max 2 named voters on a motion). A blank member list is source style.
- **Vote values:** `Nay`/`Abstain` appear as named dissent; the passing majority is unnamed.

## Roster & a name-resolution caveat
Long-serving commissioners: **Richards, Cripps, Weight, Elieson, VanRoosendaal, Taylor**; earlier
**Collard, Lockwood, Sudbury**; a fresh 2026 cohort (**White, Larson, Shaw**). PC minutes record
**surnames only** ("Commissioner <Name>"). **⚠ The PC "Sudbury" (commissioner 2019–2020) is kept
as a SEPARATE `person` from council "Mick Sudbury"** — the surname-only PC record cannot be
resolved to the councilmember with certainty (surnames collide; Magna has had more than one
Sudbury in local politics). Do not merge them without external confirmation.

## Honest gaps
- **PC 2017–2018 (57 meetings) are agenda/audio only** — PMN posts agendas + audio for the
  township-era PC and General Plan Steering Committee, but **no minutes documents were published**
  for those years. All 57 are logged in `minutes_unrecovered.csv` → PC vote record begins
  **2019-03-14**. This is a publishing gap at the source, not a build miss.
- **Four PHANTOM meetings removed 2026-07-31** — `2023-08-10`, `2023-10-12`, `2024-08-08`,
  `2025-10-16` were never meetings *in this dataset*: each was a PMN **draft copy** of the
  PREVIOUS meeting (`2023-07-13`, `2023-09-14`, `2024-07-11`, `2025-09-11` respectively) ingested
  under its notice date (the draft-copy trap above), double-counting **12 motions**. De-ingested;
  the PDFs are retained in `raw/_duplicate_drafts/` with the full evidence chain.
  **All four dates ARE real meetings** — PMN posts a notice, an agenda packet and an audio
  recording for each, and each was the meeting that approved its predecessor's minutes — but
  **PMN never published their approved minutes**. They are now logged in
  `minutes_unrecovered.csv`, not left silent. Their packets (`../packets/`) and audio
  (`../transcripts/`) are correctly dated and untouched.
- **The post-2018 side of `minutes_unrecovered.csv` is NOT a complete gap ledger.** It carries the
  57 township-era meetings, 2 from 2019, and the 4 dates vacated in 2026-07-31. Other modern
  no-minutes dates visible on PMN body 1559 (e.g. 2024-02/03/04, 2025-04, 2025-06, 2025-11-13,
  2026-01/02, 2026-05) are **not yet ledgered** — treat the modern ledger as partial.
