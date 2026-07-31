# White City — `meeting_minutes/` (Council)

Council minutes (markdown) + the extracted vote table for White City. **All rows here are
`body=Council`** — the Planning Commission is a SEPARATE dataset since 2026-07-16
(`../planning_commission/`, recovered from PMN body 5879; its own CLAUDE.md is
authoritative).

## Files
- `minutes/<YYYY>/<week-start>/<date>_<slug>.md` — one markdown file per meeting (122 files,
  2018-01-04 → 2026-05-07). Each carries an injected provenance header (source URL, date, format).
- `minutes_index.csv` — `date,year,title,slug,path,source,source_url,format`, one row per file.
  `source` ∈ `streamline` (117) / `pmn` (5 — 2019-11-14, 2022-03-03, 2022-08-18, 2023-10-05,
  2023-11-02, recovered from PMN body 5805 via `../pmn_backfill/`, promoted 2026-07-16);
  `format` ∈ `text` (110, born-digital) / `ocr` (12, mid/late-2024 scans).
- `minutes_unrecovered.csv` — meetings known to exist whose minutes are not on disk: **20
  rows** — 18 meetings of the **2017 council year** + 2018-02-01 + 2018-09-06, all proven by
  PMN notices whose Meeting-Minutes attachments were **purged from the pre-~2019 PMN file
  store** (the same blob purge that hit kearns/magna/copperton; Streamline holds only
  agendas for 5 of these dates). A GENUINE gap — recoverable only if PMN restores the blobs.
- `all_votes.csv` — the 13-column standard vote table **+ the trailing `provenance`
  column** (`minutes` = Streamline-published, 762 rows; `pmn_minutes` = PMN-recovered, 13
  rows): **653 motions · 775 rows** (188 named + 587 tally-only/placeholder). The 2022-08-18
  PMN-recovered meeting is a genuine zero-motion MIH work session.
- `motions_std.csv` — the normalized layer (joins to `all_votes.csv` on `(source, motion_no)`).
- `roster.csv` — OBSERVED roster (10 people; `member,role,first_seen,last_seen,n_meetings`).
- `extract_votes.py` — the White-City-specific extractor. `validate_votes.py` — its hard checks.
- `raw/` — retained source PDFs (never deleted).

## How votes were extracted — three eras, one extractor

White City's vote-recording grammar changed twice inside the window; `extract_votes.py` handles
all three (verified in `../VERIFICATION.md`):

1. **Narrative-tally (2018–2025)** — `Council Member X, seconded by Council Member Y, moved to …
   The motion passed unanimously.` → one **tally-only** motion row (mover/seconder captured,
   `member`/`vote` blank). 587 of 775 rows. Names are **never inferred**.
2. **Narrative-named-dissent (2020–2022, + 2024-06-06)** — a prose tally (`… passed 3 to 1,
   showing Council Member Little voting "Nay"` / `… passed unanimously, with Council Member Huish
   abstaining`) with **one named non-Aye**; the majority stays unnamed. The single dissenter row is
   captured verbatim. This is why the `f.tally` validator check reports 53.6% (a "unanimous" string
   can carry a named Abstain/Nay row) — **by design, not a defect.**
3. **Full named roll call (2026+)** — `Mayor Allan Perry — Aye; Council Member … — Aye; …` → one
   `Aye`/`Nay` row per member **including the Mayor** (max 5). 150 named rows.

## Voting rules to respect
- **The Chair (township era) / Mayor (city era) VOTES.** Max roll-call tally = **5**. A
  `Mayor <Name> — Aye` roll entry is a real voting member (Millcreek model, not the non-voting-mayor
  form). Verified: 0 motions exceed 5 named voters; 0 members vote twice on one motion.
- **Vote-value ceiling: `Aye`/`Nay`/`Abstain` only.** Absences appear only as narrative prose, never
  as a vote row. Do not read the absence of `Absent`/`Recuse`/`Excused` as behavior.
- **12 indexed minutes carry 0 motions** — genuine no-action work/continued/adjourn sessions and the
  2019-11-19 Board-of-Canvassers session (whose single certification motion is out of the
  Council-scope extractor; see `../VERIFICATION.md §3.6`). These correctly produce no vote rows.

## Regenerate
`python3 extract_votes.py && python3 validate_votes.py` (from this directory). Then rebuild
`../db/` + `../weeks/` + `motions_std.csv`. Canonical truth = these CSVs + the minutes markdown +
`raw/` originals; never hand-edit — corrections go through documented override files.
