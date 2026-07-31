# meeting_minutes/ — Ogden City Council vote extraction

Pipeline that turns 504 council-minutes markdown files into structured roll-call
vote data. Entry point: **`extract_votes.py`**; QA via **`validate_votes.py`**.

## What's here

| Path | Role |
|------|------|
| `minutes/<year>/<week-monday>/<date>_<slug>.md` | Source minutes (text-layer PDF → markdown; 2022 is a scan, re-OCR'd with tesseract 2026-07-02). Immutable input. |
| `minutes_index.csv` | Index of the 504 files (`date,year,title,slug,path,source,source_url,format,from_compilation`). `from_compilation=Y` means the meeting was carved out of a multi-meeting yearly compilation PDF. |
| `extract_votes.py` | Parser. Reads each minutes file, emits one JSON per meeting, rebuilds `all_votes.csv`. |
| `validate_votes.py` | Per-member tally vs result cross-check; rosters; body counts. Writes `votes/_validation_report.txt`. |
| `votes/<year>/<week>/<date>_<slug>.json` | Structured intermediate, one per meeting. |
| `votes/_validation_report.txt` | Validation output (counts, per-year observed voters, mismatches with explanation). |
| `all_votes.csv` | Long format, one row per member-vote, rebuilt from the JSONs. Authoritative analysis table. |

## Run

```bash
python3 meeting_minutes/extract_votes.py            # full re-parse, rebuilds all_votes.csv
python3 meeting_minutes/extract_votes.py --rebuild  # rebuild CSV from existing JSONs only
python3 meeting_minutes/validate_votes.py           # writes votes/_validation_report.txt
```

`all_votes.csv` and the report are always rebuilt from **all** JSONs on disk.

## Schemas

`all_votes.csv`: `date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`
— one row per (motion × member). `vote` ∈ {Aye, Nay, Abstain, Absent, Recuse}. A
tally-only motion (`names_recorded:false`) emits **one** row with empty `member`/`vote`
so the motion is still represented.

## Ogden specifics (why the parser looks the way it does)

- **Council = 4 districts + 3 at-large = 7 voting seats. The Mayor does NOT vote**
  (strong-mayor form). But the people who later became Mayor (Caldwell, Nadolski) were
  earlier *council members/chairs who did vote*. So the mayor is excluded **per-year via
  the roster** (`ROSTER`/`MAYOR` in `extract_votes.py`), never by name globally. Caldwell =
  Mayor 2020–2023; Nadolski = voting council chair 2020–2023, then Mayor from 2024-01-02.
- **Vote phrasings handled:** named roll-call (`VOTING AYE - COUNCIL MEMBERS A, B … AND
  CHAIR Y. VOTING NO - NONE.`), inline `ALL VOTING AYE` / `MOTION CARRIED` (tally-only, no
  names → `names_recorded:false`), and `ON A MOTION BY … AND SECONDED BY …` for mover/seconder.
- **2022 minutes are OCR'd** (the 2022 compilation is a scan; re-OCR'd cleanly with tesseract
  2026-07-02 — an earlier version of this doc wrongly said 2023 was the OCR year). OCR'd names
  can carry stray spaces (`HY ER`, `RICH EY`, `CHA IR`) and merged words
  (`CHAIRLOPEZ,ANDCHAIRNADOLSKI`). Matching is space-insensitive + fuzzy over a
  known-surname list (`canon_name`). "Lopez" resolves by year (Luis ≤2023, Flor ≥2026).
- **Roll-call parsing (`parse_named_rollcall`):** anchors on the named form (`(?<!ALL\s)VOTING
  AYE[-:]`), captures the AYE and NO segments **independently** and across line wraps (`[\s\S]`):
  AYE runs up to the next `VOTING NO` / blank line; **NO runs up to the first sentence period**.
  Two bugs fixed here: (1) a `(?<!ALL\s)` lookbehind + blank-line bound stop a trailing
  signature block (`… Ogden City Mayor`) leaking into AYE; (2) the NO list previously used
  `[^\n]`, which silently dropped every line-wrapped dissent — the systematic Nay-undercount.
- **Subject enrichment (2026-07-02, plan item 3.5):** motions matching a bare adoption
  formula ("…ADOPTED AS OGDEN CITY ORDINANCE 20xx-N…", "ORDINANCE 20xx-N WAS ADOPTED",
  "MOVED THE RESOLUTION BE ADOPTED…") get the item's **verbatim** statutory long-title
  (`scan_subjects` finds every `…, entitled:` block) or agenda heading appended to the
  motion text inside `[ENTITLED: "…"]` / `[AGENDA ITEM: "…"]` delimiters — matched by
  instrument number (zero-padding/dash/OCR normalized) or, for the no-number resolution
  form, the nearest preceding introduction of the same kind. 500 motions carry a subject
  (488 long-title / 12 heading), all verified verbatim substrings of their minutes; 1
  honest miss (2025-08-19 adopts "2025-23" while the meeting introduced only 2025-26 — a
  source number mismatch, never guessed). Native `motion_type` still comes from the bare
  clerk sentence; the enriched text is what `scripts/normalize_motions.py` classifies
  (74 motions → Land-Use, 96 → Budget, …). JSONs carry `subject` + `subject_source`.

### `body` column — governing body that took the vote
`body` ∈ {`Council` (default), `RDA`, `MBA`}. **Unlike some cities, Ogden holds RDA and MBA
as SEPARATE meetings with their own minutes files**, identified by slug:
`redevelopment-agency` / `redevelopment-agency-special` (28 files) → `RDA`;
`municipal-building-authority` (6 files) → `MBA`. The same 7 council members sit as the
Agency/Authority board (role words "Board Member"/"Chair" map to the same members). A rare
in-meeting "convened/reconvened as the … " transition is also detected. Filter `body=Council`
for council-only analysis; `body=RDA` is the TIF / project-area / developer-subsidy subset.

## Coverage + validation (last run: 2026-07-02)

- **504 meetings · 1,506 motions · 4,992 member-vote rows · 2020–2026.**
- Motions by body: **Council 1,377 · RDA 111 · MBA 18.**
- Vote distribution: Aye 3,835 · Nay 155 · Absent 108 · Recuse 1 · Abstain 2. **87 contested
  motions** (any Nay/Abstain/Recuse) — see the full list in `votes/_validation_report.txt`.
- Per-year observed voters = clean 7-member rosters with **no mayor leak** (Nadolski absent as
  a voter 2024–26; Caldwell never appears). 4 tally/result flags remain: 2 year-boundary
  artifacts (2026 handover) + 2 source clerk typos — the Jan 2022 chair/vice-chair election
  roll calls print departed member **STEPHENS** (preserved verbatim; Richey was the sitting
  member).

### 2022 repair (2026-07-02)
The 2022 yearly compilation (`raw/minutes/compilation_CC_2022.pdf`, 296 pp) is a **scan**, and
the original build used its garbled embedded OCR layer as-is AND mis-carved the meeting
boundaries (files ran across meeting starts). Repaired from the retained raw PDF: re-rendered
at 300 dpi, re-OCR'd with tesseract 5.5, re-carved on the "Minutes of the … held on <date>"
openings, cross-checked against every page's running header (0 mismatches). Result: 42 → **73
2022 files** covering **38 meeting dates** (was 30; recovered 2022-01-11 ×2, 02-03, 03-01 ×3
more, 04-05 work session, 05-10, 05-31, 07-12 ×2, 09-20 ×2, 09-21, 11-15 ×2, 12-13 ×2, and
others); 2022 named roll calls 66 → 95; roll calls capturing ≤5 of 7 voters 41% → 12% (the
remaining 11 all match "Excused:" attendance lines — genuine absences); ~33 Council motions
mis-tagged `body=RDA` by the old boundary bleed were corrected to Council. Old files/rows are
in `_backups/2026-07-02/`. Two clerk typos preserved verbatim (2022-03-01 opening prints
"March 1, 2021"; 2022-06-07 work session prints "June 2, 2022" — both dated per running
header + stated weekday). No pages were illegible; nothing was left unrecovered from the
compilation.

### 2026-07-17 — Council reverse-combined siblings integrated
`extract_backfill_votes.py` (the `pmn_backfill` → `all_votes.csv` merge step) now also
integrates `body=Council` recovered docs, not just RDA/MBA. Ogden filed CC + Joint Work
Session (+ special/closed) as separate per-body minutes some nights; the audited layer kept
one and dropped the siblings. Two recovered Council meetings carried real roll calls and are
now in `all_votes.csv` with `provenance=pmn_minutes` (**+44 rows, 153 → 197 pmn_minutes**):
**2024-01-09** City Council Special (7 motions, incl. a 5-1 contested — Choberka Nay) and
**2025-01-07** City Council Regular (7 motions, three 7-0). Council dedup keys on the recovered
slug (siblings share `(body,date)` with the audited doc); RDA/MBA dedup unchanged. Run order is
still `extract_votes.py` then `extract_backfill_votes.py`. Details: `pmn_backfill/CLAUDE.md`
(2026-07-17). NB re-running `extract_votes.py` alone drops the `provenance` column / all
`pmn_minutes` rows — always follow with `extract_backfill_votes.py`.

### Known gap (honest)
The separate **RDA and MBA meeting sets for 2022 and 2023** were not acquired: Ogden's
Document Center holds a 2023 RDA compilation (DocCenter id **29548**) and a 2023 MBA
compilation (id **29549**), and the 2022 council minutes reference separate "Special
Redevelopment Agency meetings" whose minutes are likewise not in the CC compilation — an
estimated **~20–25 RDA + ~5–8 MBA meetings per year** are missing for 2022–2023 (0 RDA/MBA
motions those years; 2021 RDA motions come from in-meeting transitions). Documented here
rather than papered over; re-acquisition is tracked as the separate-RDA follow-up item.
