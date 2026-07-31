# planning_commission/ — Magna Planning Commission (MSD-staffed)

Planning Commission minutes (markdown) + extracted votes for the **Magna Planning Commission**,
`body=PlanningCommission`. Magna runs its **own** PC, **staffed by Greater Salt Lake MSD**
planners; it recommends on Magna land use up to the City Council. Conforms to `SCHEMA_SPEC.md`.

## Contents
```
minutes/<year>/<date>_planningcommission_<id>.md   80 files, 2019-03-14 → 2026-06-11
raw/                                               retained source PDFs (never deleted)
votes/<year>/*.json                                per-meeting extracted-vote records
all_votes.csv                                      13-col standard flat table (315 rows, 314 motions)
motions_std.csv                                    normalized layer (314 rows; ~151 land-use-typed)
minutes_index.csv                                  one row per file on disk (80)
minutes_unrecovered.csv                            57 township-era meetings, agenda/audio only
roster.csv                                         commissioners with first/last seen
extract_votes.py / validate_votes.py               extraction + conformance
```

## Source & format
- **Portal:** **Utah PMN body 1559** (`www.utah.gov/pmn/files/<id>.pdf` — **use the `www.` host**).
  CivicPlus does **not** carry a Magna PC tab; PMN 1559 is the authoritative source.
- **Format:** all **80 born-digital `pdf-text`**. Corpus screen: **0 outliers**, weird_char median
  **0.0003** — the cleanest corpus in the repo.

## Vote model
- **Recommendation body.** PC motions "recommend approval/denial of application #REZ####-###### to
  the Magna Council" (a recommendation) or take a final action (plats, conditional uses). Land-use
  cases are keyed **`REZ####-######`** (rezones), plus subdivision plats, conditional uses, site-
  plan/design reviews, and text amendments — ~**151** of 314 motions carry a land-use type in
  `motions_std.csv`.
- **Tally style.** Unanimous motions print "Commissioners voted unanimous in favor (of
  commissioners present)" — **no per-member Aye list**; only dissenters/abstainers are named
  (**19** named rows total, max 2 named voters on a motion). A blank member list is source style.
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
