# Salt Lake City (Salt Lake County) — Civic Data Recon

**Date:** 2026-07-02 (**RETROSPECTIVE** — SLC was the original, pre-template city; this
recon is reconstructed after the fact from the project docs and working pipelines so the
repo carries the same portal/vendor map its 12 clones got up front. The clones' recon.md
files were written *before* their builds; this one documents sources that are already
proven in production.)
**Scope:** data 2020–present · **Repo:** `/Users/tysonwelsh/civic-data/slc_city_council/`

City: Salt Lake City, Utah · Salt Lake County · state capital, pop. ~210k.
Council: **7 geographic districts**, staggered 4-year terms; Mayor elected separately
(strong-mayor form; the Mayor does not sit on or vote with the Council).

---

## 1. Council meeting minutes — two portals

**Primary portal vendor: PrimeGov** — host `slc.primegov.com` (current agenda/minutes
system). **Secondary/archival: Laserfiche WebLink** — host `webdme.slcgov.com/AgendasMinutes`.

| | PrimeGov (slc.primegov.com) | Laserfiche (webdme.slcgov.com) |
|---|---|---|
| Minutes format | born-digital **HTML** → clean Markdown | scanned images + **OCR text layer** |
| Coverage | minutes **2021–present** (agendas 2018+) | 1982–present |
| Currency | current, incl. pending/unapproved | lags ~3 months |
| Access | plain JSON API, no auth | cookie/session dance |

### PrimeGov retrieval pattern (verified, in production — `meeting_minutes/scrape_primegov.py`)
- List meetings: `GET /api/v2/PublicPortal/ListArchivedMeetings?year=YYYY` → JSON; each
  meeting has `title`, `dateTime`, `documentList`.
- A meeting's minutes = the `documentList` entry with `templateName == "HTML Minutes"`;
  take its `templateId` and `GET /Portal/Meeting?meetingTemplateId=<id>` — the page embeds
  the compiled minutes HTML (sliced and converted to Markdown; layout tables linearized).
- **PrimeGov has NO minutes before 2021** (agendas only) — don't hunt for them there.

### Laserfiche retrieval pattern (verified — `meeting_minutes/scrape_laserfiche.py`)
- JS/cookie app, but the data API works with a session cookie:
  `FolderListingService.aspx/GetFolderListing2` (folder tree; City Council folder id
  2877637) → `DocumentService.aspx/GetBasicDocumentInfo` (page count) →
  `DocumentService.aspx/GetTextHtmlForPage` (per-page OCR text). No Vision cost.
- Used for **2020** (68 files). 2018–2019 could be added the same way if scope expands.

### Roll-call votes in minutes? — **YES** (2021+ Markdown)
PrimeGov minutes carry inline bold vote blocks per motion — mover/seconder, then
`**AYE:** …` member lists and a `Final Result: 7-0` line. Extracted with Claude
(`meeting_minutes/extract_votes.py`, LLM-batch; spot-verified in the 2026-07-02 audit).
The 2020 OCR text is too messy for reliable roll-call parsing → votes are 2021+ only.

## 2. Multi-body structure — one interleaved vote stream (SLC quirk)

The Council adjourns/reconvenes **in-session** as three sibling bodies — **RDA**
(Redevelopment Agency), **CRA** (Community Reinvestment Agency), and **LBA** (Local
Building Authority) — so one PrimeGov minutes document can interleave four bodies'
motions. Body is recovered per motion from the minutes' ALL-CAPS section headers
(`SALT LAKE CITY COUNCIL MEETING`, `LBA OPENING CEREMONY`, `…reconvene as the City
Council`, …); that derivation feeds both `db/civic.db` and (since the 2026-07-02
retrofit) the `body` column in `meeting_minutes/all_votes.csv`.

## 3. Planning Commission

Same PrimeGov portal, own meeting series ("Planning Commission"). Minutes 2020–2026;
votes are **pure-regex** extractable (`planning_commission/extract_votes.py` —
deterministic, unlike the LLM-extracted council votes). PC motions encode a
recommendation-vs-final-action taxonomy in the `result` string.

## 4. Public comments — slcdocs.com weekly PDFs (rich; rare among Utah cities)

- The Council publishes written public comments as **weekly PDF compilations** on
  `slcdocs.com` under `…/Public_Comments/{year}/` — one file per council week
  (Wednesday → the following Tuesday, the Tuesday being meeting night); holiday/recess
  bundles span 2–5 weeks. Pre-~2020-07 files are per *meeting date* instead.
- PDFs are scans/exports of comment tables → extracted page-by-page with **Claude
  Vision Batch API** (`public_comments/vision_extract.py`), cleaned by
  `clean_comments.py`. Incremental refresh: `check_new_comments.py` probes the site
  forward from the newest local file (the `/check-slc-comments` skill wraps this).
- This is one of only two substantive public-comment corpora in the repo
  (13,334 clean comments 2020–2026).

## 5. Elections — run by **Salt Lake County**

- County-wide municipal results (precinct × contest × candidate), 2007–2025. *(2026-07-19
  re-point: the per-year `election_results/{year}_municipal_{primary|general}.csv` raw
  copies described here were proven byte-identical slices of the county canonical
  `salt_lake_county/elections/slco_municipal_results_long.csv` and deleted; the pipeline
  now filters the canonical directly. SLC's coverage is far deeper than the clones' 2019+.)*
- Contest-name normalization is the hard part (`SALT LAKE CITY COUNCIL DISTRICT 1` /
  `… CNCL DIST 1` / `SLC Council 6` / `… COUNCIL #4`, and SOUTH SALT LAKE must be
  excluded) — handled in `election_results/clean_elections.py`. 59 SLC races (2019
  primary adopted 2026-07-19).

## 6. GIS / boundaries

- **7 geographic council districts.** Salt Lake County precinct boundaries
  (`geo/slco_precincts_current.geojson`, PrecinctID) + a precinct→district lookup
  **derived from the election data itself** (each council contest lists its precincts)
  → no separate council-boundary file needed. Address → district via the free U.S.
  Census geocoder + point-in-polygon (`geo/address_to_district.py`).

## Risks / notes (as experienced in production)
- PrimeGov nests HTML tables purely for layout — converting them to Markdown tables
  makes garbage; linearize cells first (done in `extract_minutes()`).
- Laserfiche 2020 text is OCR: typos preserved verbatim; no vote extraction attempted.
- Vision extraction: ~8 unrecoverable comment pages (5 content-filter blocks, 3 JSON
  edge cases) — documented in `public_comments/CLAUDE.md`; don't keep retrying.
- 68 of 457 minutes files (the 2020 Laserfiche set) have no `source_url` in
  `minutes_index.csv`; per-document provenance for them lives in
  `meeting_minutes/index_laserfiche.csv` (entry_id + DocView URL).
