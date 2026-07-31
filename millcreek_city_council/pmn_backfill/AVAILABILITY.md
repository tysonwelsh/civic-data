# PMN backfill — availability & what was checked

**As-of:** 2026-07-06 · **Source:** Utah Public Notice (`https://www.utah.gov/pmn`)

## What this dataset is

A **date-level set-difference** of PMN's Millcreek minutes holdings against the already-audited
`meeting_minutes/` (Council + CRA) and `planning_commission/` layers, plus the minutes files
PMN holds that the repo did not. It is **additive and separate** — the audited minutes layer
was not touched. See `coverage.md` for the full per-year table and `CLAUDE.md` for method.

## What was checked

- **PMN bodies** discovered via the entity chain (Municipality entities → Millcreek entity
  `id=1279` → publicBodies): **City Council = 5741, Planning Commission = 5815, CRA = 6367**
  (ids not guessed; the city's older `fetch_new.py` reference to "body 1031" is stale — 5741
  is authoritative).
- **Every PMN minutes date** for all three bodies (Council 298, PC 145, CRA 59 minutes
  notices) cross-checked ±4 days against the repo minutes indices.

## What exists / result

- The repo minutes layer is a **near-total superset** of PMN. PMN surfaced exactly **two**
  council-body dates not in the repo; PC and CRA had **zero** gaps in every year.
- **1 recovered:** 2017-11-21 Board of Canvassers general-election canvass (scanned →
  OCR'd). See `index.csv`.
- **1 unrecoverable:** 2018-03-20 City Council Budget Work Meeting — the PMN attachment
  (and its handout) are **dead 404s**; the AgendaCenter version is a budget spreadsheet only.
  Already in `meeting_minutes/minutes_unrecovered.csv`. See `unrecovered.csv`.

## What does NOT exist here (honest gaps)

- **No standalone per-city PMN advantage.** Millcreek posts its minutes to both AgendaCenter
  and PMN and the AgendaCenter harvest already captured essentially everything. PMN's value
  for Millcreek is one recovered 2017 canvass; it is not a large backfill source for this city.
- The recovered file is a **scanned image PDF** (0-byte text layer) — read the OCR sidecar
  in `text/`, expecting occasional OCR noise. Roll call is tally-only (source format, not an
  extraction miss).

## Do NOT

- Do not merge these into `meeting_minutes/` in place. This dataset is for the user to review
  and merge deliberately.
- Do not treat the 2018-03-20 dead PMN file as a fresh gap — it is verified unrecoverable at
  both sources.
