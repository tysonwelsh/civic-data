# planning_commission/ — Town of Alta Planning Commission vote pipeline

Same schemas as `meeting_minutes/`, `body=PlanningCommission`. Alta's PC is the town's
**Land Use Authority** + General Plan author; it meets **4th Wednesday as-needed** and is
frequently cancelled → a **sparse but real** record (17 audited docs, 2022-06 → 2025-12,
**+1 PMN-promoted 2024-04-24** since 2026-07-16; **none 2020-21** — an honest gap proven
real by PMN cancellation notices, the PC produced no minutes then, not a miss).

## What's here
- `raw/` — **17** retained PDFs (Utah PMN body **1602**). `raw_text/` — OCR cache for the
  **13 scanned** docs (4 are born-digital).
- `minutes/<year>/<week-monday>/…md` (+ provenance header), `minutes_index.csv`
  (`source=pmn`; `pdf-text` 4 / `ocr` 13), `minutes_unrecovered.csv` (**1 row** — see
  the 2023-11-28 draft decision below).
- **+1 PMN-promoted PC doc** (2026-07-16): **2024-04-24** (born-digital, in
  `../pmn_backfill/text/`), merged into `all_votes.csv` by
  **`extract_backfill_votes.py`** with a documented trailing 14th **`provenance`**
  column (`minutes` = audited docs, `pmn_minutes` = promoted). It was posted under a
  "Public Information Handout" label (invisible to the label-based harvest) beneath the
  2024-05-22 PC notice; the audited 2024-05-22 minutes record it approved UNAMENDED
  (item 2). Its header prints "Tuesday, April 24th, 2024" — 2024-04-24 was a
  **Wednesday** (clerk day-name typo; the date itself is printed four times in-body and
  confirmed by the 2024-05-22 approval item).
- **NOT promoted — the 2023-11-28 DRAFT decision (2026-07-16):** PMN's only copy of the
  2023-11-28 PC minutes carries a **DRAFT watermark on every page**, and its PDF was
  authored **2024-02-23 — four days BEFORE** the "Minutes Approved on February 27,
  2024" line pre-printed in it (the line names the *scheduled* approval meeting; it
  cannot attest approval). Drafts are never promoted: the file stays a
  `../pmn_backfill/` sidecar, and the meeting is logged in `minutes_unrecovered.csv`
  (the meeting is real; its minutes WERE approved unamended at the audited 2024-02-27
  meeting, but the approved version was never posted — the draft is the only surviving
  record of the meeting's content).
- `extract_votes.py` / `validate_votes.py` — run with the `pc` arg:
  `python3 extract_votes.py pc [--force]`, `python3 validate_votes.py pc`, then
  `python3 extract_backfill_votes.py` (LAST — restores the pmn rows idempotently).
  `validate_votes.py` covers the MERGED record (audited JSONs + `pmn_minutes` rows).

## PC vote grammar — NARRATIVE, tally-only by source
The PC prints **no per-member roll call**. Motions are narrative — `<Name> motioned/moved/
introduced a motion to <action> … <Name> seconded … the motion was passed/carried with
unanimous consent of the commission` (or `All in favor`). The extractor anchors on the
narrative motion verb (there is **no** uppercase `MOTION:` label like the Council) and
captures mover/seconder, but every recorded PC vote is **unanimous consent → tally-only**
(`member`/`vote` blank). Staff who "recommended" in discussion (Cawley, McLean, Platt, …)
are **never** captured as movers — only `<Name> (motioned|moved|introduced/made a motion)
to <action>` anchors a motion.

Commissioners observed: Nepstad (Chair), Niermeyer, Askins, Moxley, Abraham, Voye; Mayor
Bourke sits **ex officio**.

## Coverage (measured, post-promotion 2026-07-16)
**18 meetings (17 audited + 1 promoted)** · **49 motions** · 49 rows · **0 named** (all
tally-only unanimous — a source ceiling, not an extraction loss) · **0 contested** ·
0 ceiling breaches. Land-use actions (e.g. the 2022-06-02 Wyssen Towers conditional-use
permit, plat amendments, the 2025 WUI code recommendation) are captured as
`Land-Use/Zoning` / `Ordinance` motions. The promoted 2024-04-24 doc contributes 2
procedural motions (minutes approval + adjourn, both unanimous consent) and — more
importantly — the substantive **Shallow Shaft Base-Facilities-Zone text-amendment
presentation** narrative (no vote taken; feedback stage).
