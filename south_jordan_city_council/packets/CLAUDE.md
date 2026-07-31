# packets/ — agenda packets & staff reports (INDEX-ONLY) — as-of 2026-07-06

Built by `expand-city-sources` (Source 1). The staff analysis (fiscal notes, zoning
analysis, alternatives, staff recommendation) behind each South Jordan **City Council** and
**Planning Commission** agenda item — the "why" behind a motion in
`../meeting_minutes/all_votes.csv` / `../planning_commission/all_votes.csv`.

> **Primary-document classes (doc_class rollout, 2026-07-16): honest no.** The four
> attachment-borne classes (`staff_report`/`member_memo`/`plan_amendment`/
> `development_agreement`) are **not separable for this Municode portal** — 169 whole-meeting
> INDEX-ONLY bundles, generic meeting-level titles, no per-attachment rows or matter metadata.
> Nothing fetched/classified/section-cut. See `AVAILABILITY.md` § Primary-document classes.

## This is a LINK INDEX, not a document store — by deliberate design
South Jordan's **Municode Meetings** portal bundles each meeting into **one whole-meeting
PDF** (`MEET-Packet-<uid>.pdf`: agenda + every staff report + all exhibits), median **19.8
MB**, up to **195 MB** (full 169-packet set = **5.32 GB**; 40 are >50 MB, 7 >100 MB). The
staff-report pages are born-digital text but the **exhibits (maps, plats, site plans,
traffic/engineering studies) are images**, so a packet is only partly text-convertible and
reading one end-to-end needs **vision/OCR**. Per the repo-owner disk budget and the low
whole-file text yield, **the PDFs are not stored locally**; `index.csv` catalogs all 169
with a **live `source_url` + exact byte size** so any packet is fetchable on demand.

The retention exception is intentional and scoped to this dataset: the packet PDFs are
public and re-fetchable from `source_url`; `raw/_fetch_log.jsonl` retains the provenance
(URL → HTTP 200 / Content-Length / retrieved_utc) of the 2026-07-06 HEAD-probe discovery.
(The normal "retain every raw original" rule still applies to every *other* dataset here.)

## How an LLM/agent should use this
1. Find the meeting in `index.csv` by `date` + `body` (+ `meeting_type` for a same-day
   study vs regular vs budget session). Each row has `source_url`, `size_mb`, `packet_uid`.
2. To read it, **fetch `source_url`** (public Azure-blob GET). Check `size_mb` first — some
   are >100 MB.
3. Extract: `pdftotext -layout` recovers the agenda + staff-report memo text; use
   **vision/OCR** for the map/plat exhibits. Label whatever you produce.
4. To bulk re-hydrate: feed the `source_url` column to `polite_fetch.py --batch` **uncapped**
   (~5.32 GB for all 169).

## index.csv columns
`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format(=na),
extraction_method(=not_retrieved), path, meeting_title_raw, packet_uid, content_length_bytes,
size_mb, stored_locally(=no)`
- `body` ∈ `Council` / `PlanningCommission` (matches the vote datasets' `body`).
- `meeting_type` derived from the title: `regular` (166), `study` (2), `canvassers` (1).
  Municode attaches a single "Agenda Packet" to a meeting, so `packet_kind=full_packet` for
  every row.
- `title` = cleaned meeting name; `meeting_title_raw` = the verbatim Municode title
  (retains its `- ARCHIVED` status marker and `Combined City Council & Redevelopment Agency`
  wording — kept alongside, never overwritten).
- `packet_uid` = the Municode meeting UID (the same UID also addresses that meeting's
  `MEET-Agenda-<uid>.pdf` and `MEET-Minutes-<uid>.pdf` on the blob store).
- `format=na` / `stored_locally=no` because nothing is stored; each row is a pointer.

## Coverage & join
- **169 packets: Council 87 (2022–2026), Planning Commission 82 (2022–2026).** 2020–2021
  predate Municode packet publication for both bodies (a zero-result date-filter query, not a
  scraper miss — see `AVAILABILITY.md`).
- **Join key `(date, body [, meeting_type])`.** Council packet dates cover **82/100** of
  2022+ council vote dates; PC **80/82** of 2022+ PC vote dates (the ~18 council non-matches
  are study/special/budget sessions with no separate packet). 4 packet dates (2 per body)
  run ahead of the current minutes floor (repo minutes stop 2026-05-19) — meetings not yet
  minuted, not errors.

## Provenance & regenerate
- **Source portal:** Municode `southjordan-ut.municodemeetings.com/meetings3`, meeting-group
  filter `field_microsite_tid_selective` = **27 (City Council)** / **481 (Planning
  Commission)**; the meeting-listing table is a Drupal view (date + title + Agenda/Packet
  links). **The host speaks HTTP/2 only** (Python `requests`/HTTP-1.1 is disconnected — the
  listing HTML was enumerated with `curl --http2`; the Azure blob store works fine with
  `polite_fetch.py`). The default infinite-scroll caps at ~5 pages, so full history requires
  the `date_filter[value][…]` + `date_filter_1[value][…]` + `op=Apply` GET range params,
  paged per ~6–12-month window; that filter is **cache-flaky** (an identical query returns
  data or 0 on different hits) so windows were retried and unioned by UID until stable.
- **CivicPlus AgendaCenter is not used** (its `?packet=true` links are empty stub PDFs — see
  `AVAILABILITY.md`).
- To refresh: re-enumerate both meeting groups on Municode for dates > max(`index.csv.date`),
  HEAD-probe each new `MEET-Packet-<uid>.pdf`, append rows with the same columns. Nothing to
  extract unless a specific packet is fetched. `validate_dataset.py` must PASS.
