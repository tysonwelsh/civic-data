# ordinances/ — Orem adopted ordinances index + linkage (built 2026-07-05; re-derived 2026-07-19)

Additive dataset built by the `expand-city-sources` skill (Source 3). **Read-only** on
every existing dataset — nothing here modifies `meeting_minutes/`,
`planning_commission/`, `public_comments/`, `db/`, or `weeks/`.

## What this is
An index of **adopted Orem City ordinances** (100 rows, 2020-01-14 → 2026-07-14), each
mapped — where a vote row exists — to the council **motion** that adopted it in
`meeting_minutes/all_votes.csv`, with a confidence label. Emphasis is **zoning /
land-use** (Orem City Code **Title 22 = the Development / Land-Use code**): **51 of 100
(51%)** are land-use.

**2026-07-19 re-derivation (Q3 refresh).** Re-run over the 5 new OCR'd council minutes
(2026-05-12 … 2026-06-23) plus a re-crawl of the orem.gov ordinance posts (which added a
new **2026-07-14** post, ordinances `O-2026-0018`/`0019`). The minutes-derived backbone
grew 89 → **92** within_source rows, and — for the first time — the independent orem.gov
posts now overlap the vote layer, yielding the dataset's first cross-source tier:
**4 `medium` rows** (`O-2026-0014`…`0017`) where a numbered orem.gov post uniquely matches
a 2026-06-23 council adoption motion by distinctive code-section / subject tokens. See
"Linkage method" below.

## Code host & where the data comes from
- **Codified code host = EnCodePlus / GovOS** — `https://online.encodeplus.com/regs/orem-ut/`
  (linked from `https://orem.gov/recorders/`). *Current consolidated* code only; **not** a
  number→date→subject adoption history, and no per-ordinance documents. (Municode does
  **not** host Orem — `library.municode.com/ut/orem` is a generic shell.)
- **Independent adopted-ordinance publication = orem.gov WordPress "City Council
  Ordinance" posts** — a practice begun **mid-2026**. **3 posts** now covered: the
  **2026-06-23** meeting (2 posts, 6 ordinances `O-2026-0012`…`0017`) and the
  **2026-07-14** meeting (1 post, `O-2026-0018`/`0019`) — number format `O-YYYY-NNNN`,
  full text embedded (the 07-14 post prints them OCR-style as `0-2026-00NN`, normalized
  here). Retained in `raw/` with `_fetch_log.jsonl` (polite_fetch: url, status, bytes,
  sha256, retrieved_utc); text extracts in `text/`. (R-series resolutions in the
  "Resolutions and Ordinances" post are intentionally NOT indexed — this is an ordinances
  dataset.)
- **Backbone = the council minutes themselves.** Orem minutes **never print an ordinance
  number**, but every adoption is a roll-call motion in `meeting_minutes/all_votes.csv`
  ("approve, by ordinance, to amend …") carrying date + subject + vote. 89 of the 95 rows
  are reconstructed from those motions. This dataset is therefore primarily a **derived
  index**, not a cache of downloaded ordinance texts.

## index.csv columns
Minimum provenance (`date`,`title`,`source_url`,`retrieved_date`,`format`,
`extraction_method`) plus:
- `ordinance_no` — `O-YYYY-NNNN` for the 8 independent-post rows (4 `medium` + 4 `none`);
  **empty** for the 92 minutes-derived `within_source` rows (Orem assigns a number but does
  not restate it in minutes).
- `adoption_date` (= `date`) — meeting date the adopting motion passed / the post's date.
- `title` — ordinance subject, verbatim from the motion (minutes rows) or the ordinance
  caption "AN ORDINANCE …" (independent rows).
- `source_url` — the orem.gov post URL (independent rows) or the **repo-relative minutes
  markdown** that recorded the adoption (minutes rows; Orem publishes no per-ordinance URL).
- `format` — `html` (independent posts) / `text` (born-digital minutes) / `scanned`
  (OCR'd minutes, the 68 2022–2026 files).
- `extraction_method` — reconstructed-from-motion vs extracted-from-WordPress-post.
- `path` — `raw/<post>.html` for independent rows; empty for minutes-derived rows.
- `land_use` — yes/no, regex on the subject (Title 22 / rezone / zoning map / SLU /
  general plan / moratorium / vacate). Informational.
- `result` — Pass/Fail of the adopting motion (minutes rows + `medium` cross-matched rows);
  empty for `none` rows.
- `matched_motion_date`, `matched_motion_no`, `match_confidence` — the linkage (below).
- `linkage_note` — free text (independence caveat, audit-signal note).
- `minutes_source` — the repo minutes markdown recording the adoption vote (join target).

## Linkage method + INDEPENDENCE CAVEAT
Join rule: adoption date + the ordinance's subject/number ↔ the adopting council motion.
- `within_source` (**92**) — the row was reconstructed **from** the motion, so date +
  subject are present by construction. This is a strong join but **NOT an independent
  cross-match** — do not read these as corroborated. `matched_motion_date/no` point back
  to the very motion the row came from. `ordinance_no` is empty (Orem minutes print none).
- `medium` (**4**) — `O-2026-0014`…`0017`. **A genuine CROSS-SOURCE match**: the ordinance
  number + full caption come from the independent orem.gov post, and the roll-call adoption
  comes from `meeting_minutes/all_votes.csv`. The join is made only when a post's ordinance
  **uniquely** matches a single council motion **on the post's meeting date** by distinctive
  code-section / subject tokens (rules in `build_index.py` `MATCH_TOKENS`, hand-verified
  2026-07-19). The duplicate number-less `within_source` row for that motion is suppressed,
  so there is no double count. Notably `O-2026-0014` links the 2026-06-23 **budget
  amendment** motion, whose text omits the word "ordinance" and which the keyword backbone
  therefore never captured — the independent post is what reveals it is an ordinance. (Still
  not `high`: Orem has no *signed* independent PDF archive; the WP post is a born-digital
  caption, so `medium` is the ceiling.)
- `none` (**4**) — `O-2026-0012`, `O-2026-0013`, `O-2026-0018`, `O-2026-0019`, each an
  **AUDIT SIGNAL** (genuine adopted ordinance, no linkable vote row), logged, **not forced**,
  vote layer **not** edited:
  - `O-2026-0012` (Flood Damage, Chapter 10) and `O-2026-0013` (355 W University Pkwy rezone,
    R8→C2) were adopted on the **2026-06-23 consent agenda** — a single blanket motion
    ("approve the consent items", m2, 7-0), not individually rolled — so no distinct vote row
    exists to link. (Do NOT confuse `O-2026-0013` with the 2026-05-12 m5 rezone: that is a
    *different* property — 92 South 800 East, R8→C1 assisted living.)
  - `O-2026-0018`/`0019` were adopted **2026-07-14**, beyond the current vote coverage
    (`all_votes.csv` ends 2026-06-23) — they will link on the next minutes refresh.

To go from an ordinance to its full vote: read `minutes_source` (the exact minutes
markdown), or filter `meeting_minutes/all_votes.csv` on `matched_motion_date` +
`matched_motion_no`.

## Known limits / how to extend
- **No full ordinance texts pre-2026** — only the adopting-motion subject. Full texts
  live at the Recorder's Office / Utah Public Notice (Source 4, PMN) / CivicClerk agenda
  packets (Source 1). Reuse any PMN "Notice of Ordinance" as an independent corroborator
  to upgrade `within_source` rows toward `medium`/`high`.
- **Number-less pre-2026** — `ordinance_no` empty for the 92 minutes `within_source` rows.
- The 4 `none` rows expose that the minutes/votes layer trails the recorder's publishing by
  ~1 meeting (0018/0019 adopted 2026-07-14) and that consent-agenda ordinances (0012/0013)
  are not individually rolled — refresh / consent-agenda audit signals, not defects here.
- **To upgrade `within_source` → `medium`/`high`:** add the ordinance's independent
  number-bearing source. Two channels exist for Orem: (a) more orem.gov WP ordinance posts
  as the city keeps publishing them (add to `POSTS` + a `MATCH_TOKENS` rule in
  `build_index.py`); (b) a PMN "Notice of Ordinance". The `medium` cross-match rule requires
  a UNIQUE distinctive-token hit on the ordinance's meeting date — keep it conservative so a
  consent-agenda or ambiguous ordinance honestly stays `none`.

Rebuild: `python3 ordinances/build_index.py` (idempotent; regenerates `index.csv` +
`text/`; prints the within_source / medium / none split + the 3 excluded non-adopting
motions). To extend after a new orem.gov ordinance post: drop the raw HTML in `raw/`, add
its `(file, url, meeting_date)` tuple to `POSTS`, and (if a numbered ordinance was
individually rolled) a hand-verified `MATCH_TOKENS` rule.
