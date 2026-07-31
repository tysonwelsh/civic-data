# summit_county / development — the land-use development pipeline

`applications.csv` — one row per **land-use application item** heard by either Planning
Commission, reconstructed from the `land_use/` minutes (agenda-item detail + the item's
motion outcome). Summit County's growth pipeline for housing/development research. Built by
`build_applications.py` (idempotent; reads `land_use/minutes/` + the extracted motions).
**As-of 2026-07-20.** 571 applications.

## Row model (SLCo development model + Summit-native application detail)
Columns: `date, body, body_slug, item_no, dev_type, title, location, parcel, applicant,
owner, project, session, pc_recommendation, outcome, tally, names_recorded, link_confidence,
minutes_path, motion_id`.
- `motion_id` (added by the closing pass — `db/link_applications.py`) = the per-county
  `summit_county.db` PC motion_id this application's action was uniquely resolved to (the
  repo-root federation loader offsets it into `development_application.motion_id`). **70 of
  the 224 outcome-bearing rows** carry a unique link; the rest are blank because Summit PC
  minutes key the agenda item by parcel # but the enacting motion by project NAME, and
  multiple items per meeting make most links ambiguous — never forced (honest gap).
- `names_recorded` is `1`/`0` (federation-readable; the closing pass normalized the module's
  original `true`/`false`).
- `dev_type` (read from the item body, not its label): `subdivision` 230 · `conditional_use_
  permit` 153 · `rezone` 47 · `plat_amendment` 41 · `specially_planned_area` 41 · `master_
  planned_development` 27 · `low_impact_permit` 16 · `code_amendment` 13 · `general_plan_
  amendment` 3.
- `location` / `parcel` (387 rows) / `applicant` (174) / `project` (Summit project #, 225) —
  parsed from the modern minutes' structured item sentence (`located at … ; Parcel … ;
  Applicant: … ; Project #…`). **Blank = the minutes didn't print it** (older-era items
  carry less structure), never inferred.
- `session` = `work_session` vs `regular` (an item often appears in both; the row kept is
  the one with the recorded action — see dedup below).
- `pc_recommendation` = the disposition of the item's motion (`approve` 187 / `continue` 27 /
  `deny` 4 / blank). `outcome` = did that motion CARRY (`Pass` 223 / `Fail` 1 / blank).
  `tally` = the `(N-M)` count. These are ORTHOGONAL (a matter can be *denied* on a motion
  that *carries*) — compose at query time.
- `link_confidence`: `in_block` (193 — the motion sat inside the item's text) | `motion_
  matched` (35 — linked to a verified motion by shared parcel/project/type keys) | blank
  (343 — **no PC action recovered**: work-session/site-visit/presentation items, items
  continued to a later meeting, or the action fell outside the parsed block). Quote outcomes
  from `in_block`/`motion_matched` rows; treat blank-outcome rows as "heard, no action here".

## Honest notes / limits
- **224 of 571 rows (39%) carry an outcome.** The rest are honestly blank — many PC agenda
  items are discussions/work sessions/continuances with no vote at that meeting. Not a defect.
- Dedup: raw 633 item-rows → 571, collapsing the work-session/regular duplicate of the same
  matter (keyed on `date + body + project|parcel|title`), preferring the row with an action.
- Coverage inherits `land_use/` — the Snyderville-2021 / Eastern-2022 / 14 image-only minutes
  gaps mean applications from those meetings are absent (see `land_use/CLAUDE.md`).
- Older AgendaCenter minutes carry occasional page-header bleed inside `title` (verbatim
  extraction artifact) — the request substance is intact; normalize downstream if needed.
- Regenerate with `python3 build_applications.py` **then** `python3 ../db/link_applications.py`
  (the latter re-adds `motion_id` + normalizes `names_recorded` after reading the built db);
  never hand-edit (corrections belong in a future `overrides` file, per repo convention).
