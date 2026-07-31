# packets/ — Salt Lake County agenda packets & land-use staff reports (Legistar API)

Additive dataset: County **agenda PDFs** (stored, text-extracted) + a catalog of **land-use
matter attachments** (staff reports stored + text-extracted; the rest index-only) + the
**§9 primary-document doc_class layer** (2026-07-16 taxonomy backfill, see below). Built from
the Granicus **Legistar Web API** (`webapi.legistar.com/v1/slco`) by `../db/harvest_packets.py`,
NOT HTML scraping. The county is the ONE other Legistar entity besides Sandy. Read
`AVAILABILITY.md` for the coverage ledger. **As-of 2026-07-16.**

## Layout
```
packets/
  index.csv          454 rows: 310 agenda (stored) + 49 staff_report + 95 matter_attachment
  raw/               359 stored PDFs (310 agendas + 49 staff-report raws); no _fetch_log
  text/              358 extracted text sidecars (310 agendas + 48 staff reports)
  classify_attachments.py   deterministic §9 doc_class classifier (rerunnable; see below)
  AVAILABILITY.md    coverage, the doc_class gates, and the honest-empty boundary decisions
  CLAUDE.md          this file
```
Matter attachment BINARIES other than staff reports are **not** on disk — fetch them live
from the `source_url` in index.csv. The GP-draft exhibits are deliberately index-only
(13–52 MB each); their authoritative text lives in the county **`plans/`** module.

## index.csv columns
County-native prefix (predates the SCHEMA_SPEC §9 packets contract — see the validator note):
`date, body, packet_kind, title, matter_id, path, text_path, format, source_url,
stored_locally` + the 2026-07-16 §9 pilot extension columns **APPENDED** at the end:
`doc_class, fetch_status, sha256, text_chars`.
- `packet_kind` ∈ `agenda` (meeting agenda PDF, stored) | `staff_report` (matter attachment
  whose name contains "staff report" — stored + text-extracted) | `matter_attachment`
  (all other land-use-matter attachments — INDEX-ONLY, `stored_locally=no`).
- `body`: populated for agendas (`County Council` 259 / `Redevelopment Agency` 35 /
  `Municipal Building Authority` 16); **blank on attachment rows** (they hang off a matter,
  not a single meeting — resolve their meeting via `matter_id`).
- `matter_id`: Legistar MatterId. Join to the county db via `application.app_key = 'matter:'||matter_id`.
- `format`: `pdf` throughout (a county convention; NOT the city §9 format vocab).
- `text_path`: dataset-relative text sidecar (the searchable artifact; fed into `fts_packet`).

## §9 doc_class layer (2026-07-16 primary-docs rollout, county adaptation)

The attachment rows were classified into the §9 controlled vocabulary. On the county's
ON-DISK (stored, federated) packet corpus only ONE class occurs — `staff_report`:

| doc_class | rows | ok | no_extractor | what it is |
|---|---|---|---|---|
| staff_report | 44 | 43 | 1 | LAND-USE staff reports (rezone / Title 9·17·18·19 zoning-code / annexation / general-plan adoption-amendment / subdivision / code revision), across 40 County Council land-use matters 2020–2025 |
| member_memo | 0 | — | — | **HONEST EMPTY** — county has no council-member proposal memos (its "Council Briefing Memo" items are STAFF memos) |
| plan_amendment | 0 | — | — | **HONEST EMPTY in packets/** — the county's GP/township-plan exhibits are large index-only rows AND live authoritatively in the `plans/` module |
| development_agreement | 0 | — | — | **HONEST EMPTY in the stored corpus** — the sole instrument (matter 6980, Olympia Hills MDA Amendment No. 2) is an index-only row with no on-disk text |

- **Classifier**: `classify_attachments.py` — deterministic. The county's Legistar matter
  metadata (`EventItemMatterName/Type`) is blank/coarse, so instead of Sandy's matter-title
  join the classifier joins `matter_id` → the county db **motion text** (the agenda action
  title) READ-ONLY and applies a land-use regex, with a general-government EXCLUSION that
  wins (blanks budget adjustments, committee appointments). Rerun: `python3 classify_attachments.py`
  (idempotent; `--dry-run` reports counts only). Blank doc_class = honestly unclassified.
- **5 staff_report rows stay BLANK (general-government, not land-use)** — the harvest's
  `%annex%` land-use filter false-matched the "Clark Planetarium **Annex**" building: matters
  9529 / 9868 / 10048 (Annex-remodel budget adjustments), 11430 (budget adjustment funding a
  GP water-element contractor — a funding action, not a land-use analysis), 6062 (West GP
  Steering Committee **appointment**). All 5 ground-truthed against their stored text.
- **`fetch_status`** (classified rows only, §9 CLOSED vocab): `ok` (text on disk, 43 rows) |
  `no_extractor` (matter 4700 — the attachment is an **RTF saved with a `.pdf` extension**;
  the PDF-only extractor produced no text. Its raw is retained and sha256'd; a future
  textutil/striprtf pass can upgrade it to `ok`). Blank on unclassified rows.
- **`sha256`**: of the stored raw binary (provenance), computed for all 44 classified rows.
- **Boundary decisions (documented, not bugs)**: (1) county general-government staff reports
  stay blank; (2) `plan_amendment` — the West / Sandy Hills / Wasatch Canyons GP drafts are
  the GP documents themselves (a full new GP is `general_plan`, not an `amendment`) and are
  oversize index-only rows federated via `plans/`, so they are NOT re-classified here; (3)
  `development_agreement` — a "Master Development **Plan**" is a plan, not an agreement; only
  matter 6980's MDA amendment is a true instrument, and it is index-only.
- **Index-only content-doc candidates for a future fetch-and-classify pass** (13 rows, all
  documented, none silently dropped): 9 plan-amendment-family (GP drafts/exhibits), 3
  staff-report-family (e.g. `Public Hearing_Council_StaffReport_SHGeneralPlan`;
  `31038_CoStaffReport(Revised)_Neff.docx`), 1 dev-agreement-family (6980 Amendment No 2).

## Validator note (SCHEMA_SPEC §9 / expand-city-sources)
`validate_dataset.py salt_lake_county/packets/` **FAILs by design** — the county packets
dataset predates the §9 packets contract and uses its OWN header + `format='pdf'` convention
(NOT the city vocab). Both FAIL categories (header-prefix mismatch; `format 'pdf'` not in the
city format vocab) are **pre-existing** and identical in the pre-change backup — the
doc_class backfill introduced ZERO new failures (it only appended 4 trailing columns). Per
the rollout rule, county datasets keep their conventions; the header was NOT restructured.

## Linkage to the rest of the repo
- **By matter → db/votes**: `matter_id` → `application.app_key='matter:'||matter_id` →
  `motion`/`vote` in `db/salt_lake_county.db`. A classified staff report joins the enacting
  County Council motion + its named roll call (Legistar names members even on unanimous votes).
- **By meeting date → minutes**: agenda-row `date` joins `legislative/minutes_index.csv` and
  the council/RDA/MBA vote layer.
- **Federation**: `text_path` → `fts_packet`; `doc_class` → `document.doc_class` /
  `fts_packet.doc_class` (federation is orchestrator-side; not run here).
- This dataset never regenerates or edits `db/`, `legislative/`, `plans/`, or `weeks/`.
