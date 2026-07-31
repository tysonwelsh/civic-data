# mag_mpo.db — schema (authoritative for this db)

Standard civic-data relational schema (SCHEMA_SPEC §5), built by `build_db.py` from the
harvested minutes markdown (`legislative/minutes_index.csv` → `legislative/minutes/`).
DERIVED + idempotent; never hand-edit. Federates unchanged into repo-root `gov.db` via
`scripts/build_cities_db.py` (`gov_level='regional'`, fed_index 202).

## Tables (8 — the standard set)

| table | rows | notes |
|---|---|---|
| `body` | 2 | `MPO Board` (kind=council), `MPO TAC` (kind=commission) |
| `person` | 169 | movers/seconders, resolved by **full name** (`name_key` UNIQUE) |
| `meeting` | 151 | one per minutes doc; `source_file` = the minutes markdown path |
| `application` | 0 | **empty** — no structured matter keys (project pipeline = sibling `projects/`) |
| `motion` | 635 | one per extracted motion; see columns below |
| `vote` | 0 | **empty by ceiling** — minutes record no roll call / per-member vote |
| `role` | 0 | **empty** — derived from votes, of which there are none |
| `referral` | 0 | **empty but present** — the federator hard-fails without the table |

## motion columns (match the federator's SELECT exactly)

`city, motion_id, meeting_id, body_id, motion_no, motion_text, motion_type, result_raw,
outcome, stage, recommendation, disposition, disposition_method, disposition_confidence,
application_id, app_match_method, app_confidence, mover_person_id, seconder_person_id,
names_recorded, source_file, provenance`

- **motion_text** — the verbatim action clause ("approve … RTP Amendment 3 …", "the TIP
  be modified to transfer $6,542,749 …"); kept information-rich.
- **result_raw** — verbatim tally result ("the motion passed all in favor",
  "the motion failed").
- **outcome** — CHECK ∈ Pass/Fail/Unknown (632 Pass, 3 Fail).
- **disposition** — keyword-derived approve | procedural | continue | deny; NULL =
  honestly unclassified (58). `disposition_method='keyword'`, `disposition_confidence='medium'`.
- **motion_type** — blank (minutes label no native motion types).
- **mover_person_id / seconder_person_id** — full-name person links (633/635 each).
- **names_recorded** — 0 on every motion (the tally-only ceiling).
- **application_id** — NULL (no matter keys); **provenance** — `magutah_site`.

## Gates (checked every build)
`PRAGMA foreign_key_check` empty · `PRAGMA integrity_check` = ok · rebuild byte-stable /
count-idempotent · zero orphan mover/seconder/meeting/body references.
