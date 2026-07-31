# salt_lake_county/ordinances — how to use this module

**Adopted Salt Lake County ordinances** as a searchable plain-text corpus, each linked to
the **County Council motion that enacted it**. This fills the "adopted-ordinance catalog"
follow-on named in `salt_lake_county/CLAUDE.md`. Self-contained: raw PDFs, extracted text,
a manifest, and an honest gap log. Nothing here writes to the db.

## Layout

- `raw/<stem>.pdf` — the ordinance PDF (the District Attorney's "approved as to form /
  ready for adoption" ordinance attached to the adopting matter in Legistar). All 67 are
  born-digital and <50 MB, so all are stored (nothing link-only).
- `text/<stem>.txt` — `pypdf`-extracted text of every ordinance. **This is the searchable
  layer — read/grep these.**
- `index.csv` — the manifest, one row per **distinct adopted ordinance**. Columns:
  `ordinance_no, title, adoption_date, land_use_type, matter_id, motion_id,
  match_confidence, path, text_path, format, source_url, notes`.
- `gaps.csv` — every candidate matter that is **not** a catalogued ordinance, with a
  reason (`gap_type`): resolutions/leg-intents, procedural/duplicate lifecycle stages,
  no-attachment matters. Honest gaps, not fabricated rows. See SOURCES.md §2–3.
- `SOURCES.md` — provenance, retrieval method, and the four honest gaps.

## The vote linkage (the point of this module)

`motion_id` is the **enacting Council vote**. Join it to the roll call:

    -- who adopted ordinance <stem>, from the county db (READ-ONLY)
    SELECT v.person_id, v.vote_value
    FROM vote v WHERE v.motion_id = <motion_id>;
    -- or in gov.db: motion/vote WHERE city='salt_lake_county'

`match_confidence`: `high` (64) = the ordinance draft matches exactly one adoption motion
on the matter. `medium` (3) = 4659 (two adoption motions, Jan 7 + Jan 14 2020 — linked to
the earlier), and 4646/4682 (early-2020 substantive ordinance items adopted before the
"Formal Adoption" title convention). No `low` rows. Every row links to a real `Pass`
motion in `salt_lake_county.db`.

## Which ordinance for which question

- **Land-use / growth / housing** (`land_use_type='land_use'`, 23 rows): rezones (Title 19
  reclassifications), Title 18 subdivisions rewrite (matter 9914), ADU ordinances
  (7035, 10418, 11348), FCOZ/foothill (10662), flood/hydrology (8378, 8905, 8910), the
  unincorporated **MIH plan** adoption (8158), Olympia Hills MDA amendment (6980).
- **Governance / non-land-use** (44 rows): ethics, procurement, budget-process, board
  membership, holidays (Juneteenth), health, RDA project-area dissolutions.
- **Full text of what an ordinance did**: open `text/<stem>.txt` (or `raw/` PDF).
- **Who voted for it**: `motion_id` → `vote` (see above).

## Cardinal rules (inherited from repo root)

- **Never fabricate — especially ordinance numbers.** `ordinance_no` is **blank for all
  67 rows** because the Legistar attachment is the pre-signature draft (`ORDINANCE NO.
  ______`); the assigned number lives only on the signed/recorded copy the county does not
  attach. Do **not** infer or backfill numbers without the Clerk/Recorder signed-ordinance
  register. See SOURCES.md §1.
- **One row per adopted ordinance.** SLCo files set-hearing / public-hearing / first-reading
  / adoption as separate Legistar matters that re-attach the same draft; only the
  **enacting adoption vote** is catalogued. The other stages are in `gaps.csv`
  (`procedural_or_duplicate_stage`) with a pointer to the adopting matter — never a second
  ordinance row. See SOURCES.md §3.
- **Text is derived; the PDF + `source_url` are canonical.** Regenerate text with pypdf
  on the raw PDF (command in SOURCES.md).

## Scope / follow-ups

- Coverage is the born-digital Legistar era (**2020-01-07 → 2025-05-06**). Pre-2020
  ordinances predate this Legistar record set — a logged gap, not a fabricated zero.
- **Assigned ordinance numbers** (Clerk/Recorder register or Municode cross-reference) and
  the 3 Word-document ordinances captured via their staff-report PDF (matters 7036, 7695,
  9287) are the two open follow-ups.
