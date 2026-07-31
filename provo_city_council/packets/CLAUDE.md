# packets/ — agenda packets & staff reports (INDEX-ONLY) — as-of 2026-07-03

Built by `expand-city-sources` (Source 1). The staff analysis (fiscal notes, zoning
analysis, alternatives, correspondence, staff recommendation) behind each Provo **Municipal
Council** and **Planning Commission** agenda item — the "why" behind a motion in
`../meeting_minutes/all_votes.csv` (body Council) and `../planning_commission/all_votes.csv`
(body PlanningCommission). Join by `date` (+ `body`, `meeting_type` for same-day Work vs
Regular council meetings).

> **Primary-document classes (doc_class rollout, 2026-07-16): honest no.** The four
> attachment-borne classes (`staff_report`/`member_memo`/`plan_amendment`/
> `development_agreement`) are **not separable across either portal** — 391 INDEX-ONLY
> bundles; the council side is OnBase session-gated + chunked (no sizes), and PC 2022–24 rows
> are thin agendas (staff-report packets 2025+ only). Nothing fetched/classified/section-cut.
> See `AVAILABILITY.md` § Primary-document classes.

## Two portals, two document models (READ THIS FIRST)
Provo splits the two bodies across **two different portals** — this is not a bug:

### Council packets → Hyland OnBase "Agenda Online" (`agendas.provo.gov`), documentType=5
The OnBase portal at `agendas.provo.gov` is **Municipal-Council-only** in practice (Council
Meeting, Work Meeting, plus council one-offs: budget/priorities retreats, Truth-in-Taxation,
Board of Canvassers, joint meetings). **Planning Commission, RDA, and Stormwater are NOT in
this portal** (recon.md's claim that they share it is not borne out live — PC appears only as
council "Joint Meeting with Planning Commission"). Each council meeting exposes an
**Agenda Packet** document, `documentType=5` — a single **bundled whole-meeting PDF**
(agenda + every staff report + all correspondence/exhibits).

**Access flow (CSRF + cookie + DownloadFileBytes):**
1. `GET https://agendas.provo.gov/Meetings` with a browser UA → keep the session cookie jar
   (`ASP.NET_SessionId`, `__RequestVerificationToken`) and scrape the
   `__RequestVerificationToken` hidden-input value.
2. `POST https://agendas.provo.gov/Meetings` (same session) with
   `__RequestVerificationToken`, `Keywords=`, `DateRangeOptionID=11`,
   `DateRangeCustomStartDate=MM/DD/YYYY`, `DateRangeCustomEndDate=MM/DD/YYYY`,
   `Referer: https://agendas.provo.gov/Meetings` → results HTML. **Strip HTML comments
   (`<!-- ... -->`) first** — OnBase hides unpublished-doc links inside comments.
3. Each Agenda-Packet anchor is `/Documents/DownloadFile/<Filename>_Agenda_Packet_...pdf?documentType=5&meetingId=<id>`.
   **Rewrite `DownloadFile` → `DownloadFileBytes`** and `GET` the bytes with the **session
   cookie + `Referer: https://agendas.provo.gov/Meetings`**. The plain `DownloadFile` URL
   returns a JS "Downloading, please wait…" interstitial, not the PDF.

The repo's existing `../fetch_new.py` already implements this session flow and stores each
council meeting's docType=5 packet URL in `../meeting_minutes/minutes_index.csv` `packet_url`
column — **this dataset's council rows are derived from that column** (no re-scrape needed to
rebuild; the `source_url` here is that `DownloadFileBytes` URL verbatim).

**OnBase serves packets with `Transfer-Encoding: chunked` and NO `Content-Length`** — on
HEAD, on streaming GET, everywhere. So a council packet's byte size is **unobtainable without
a full body download** (which this index-only run avoids). `content_length_bytes`/`size_mb`
are therefore populated for **only the 26 council packets already on disk** from the earlier
`public_comments` harvest (`../public_comments/raw/packets/<date>_packet.pdf`, measured from
disk — no new fetch); every other council row has empty size with
`size_source=unknown_chunked_no_content_length`. Those 26 samples characterize the set:
**min 18.2 MB, median 36.7 MB, mean 51.9 MB, max 148.2 MB → the full 306-packet council set
is ≈ 16 GB.**

### PC packets → CivicPlus AgendaCenter (`www.provo.gov/AgendaCenter`)
Provo publishes PC agendas/packets on the CivicPlus AgendaCenter (category **"Planning
Commission"** — the separate **"Planning Commission Administrative Hearings"** category is a
different body and is excluded). The packet is the **`ViewFile/Agenda/<ref>`** document,
where `ref = _MMDDYYYY-<docId>`. Provo serves the **full packet AS the agenda** — appending
`?packet=true` returns byte-identical content, so one URL per meeting. **CivicPlus returns a
real `Content-Length` on HEAD**, so PC packets are HEAD-sized (all 85 have measured
`content_length_bytes`, `size_source=head_content_length`).

Enumerate PC refs by GET-ing `AgendaCenter/Search/?term=&CIDs=all&startDate=MM/DD/YYYY&endDate=MM/DD/YYYY`
per year, isolating the `<h2>Planning Commission</h2>` section, and reading
`ViewFile/Agenda/_MMDDYYYY-<id>` hrefs there. **Do not blindly regex refs across the whole
page** — the same numeric `docId` is reused across dates in JS-templated hrefs and a
mismatched date+id resolves to a wrong ~2.6 KB stub PDF. Scope refs to the PC section.

## This is a LINK INDEX, not a document store — by deliberate design
Both bodies' packets are **bundled one-PDF-per-meeting** (agenda + all staff reports +
exhibits), image/map/plat/site-plan-heavy → **not born-digital text; reading one requires
vision or OCR, not `pdftotext`.** Council packets alone are ≈16 GB. Per the repo owner's
disk-constrained decision (same as St. George / West Jordan), **no packet PDF is stored
locally.** `index.csv` catalogs all 391 packets with a live `source_url` so any one can be
fetched on demand. This is the documented, scoped retention exception (files are public +
re-fetchable); `raw/_fetch_log.jsonl` retains the provenance of the 85 PC HEAD probes plus a
note on why council packets were not probed. The normal "retain every raw original" rule
still applies to every *other* dataset in this repo.

## How an LLM/agent should fetch ONE on demand
1. Find the meeting in `index.csv` by `date` + `body` (+ `meeting_type` for same-day council
   Work vs Regular).
2. **Council** (`source_url` on `agendas.provo.gov/Documents/DownloadFileBytes/...`): you MUST
   carry an OnBase session — `GET /Meetings` first to mint the cookie, then `GET source_url`
   with that cookie + `Referer: https://agendas.provo.gov/Meetings`. `../fetch_new.py`'s
   `OnBaseSession` class does exactly this; reuse it. A bare `polite_fetch.py` GET (no cookie)
   may return the JS interstitial, not the PDF. Size unknown up front (chunked) — expect
   10–150 MB.
   **PC** (`source_url` on `www.provo.gov/AgendaCenter/ViewFile/Agenda/...`): a plain polite
   GET works (no session needed); check `size_mb` first.
3. Extract with **vision or OCR**, not `pdftotext` (image-heavy). Label whatever you produce.

## index.csv columns
`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format(=na),
extraction_method(=not_retrieved), path, doc_type_code, meeting_id, content_length_bytes,
size_mb, size_source, stored_locally(=no), probe_status`
- `body` ∈ `Council` (306) / `PlanningCommission` (85). Council votes → `../meeting_minutes/all_votes.csv`;
  PC votes → `../planning_commission/all_votes.csv`.
- `meeting_type` ∈ `regular` / `work` (Work Meeting/Session) / `special` (retreats,
  Truth-in-Taxation, Board of Canvassers, joint meetings, budget/priorities). Part of the join
  key so same-day Work vs Regular council packets stay distinct.
- `doc_type_code` = `5` for council (OnBase documentType=5) / `civicplus_agenda` for PC.
- `meeting_id` = OnBase numeric `meetingId` (council) / CivicPlus `_MMDDYYYY-id` ref (PC).
- `packet_kind` = `full_packet` (bundled staff-report packet) for all council + 2025–26 PC;
  `agenda_packet` (thin ~100 KB agenda outline, no staff reports) for 2022–24 PC + a few
  transitional 2025 PC — Provo's CivicPlus PC packets only became full staff-report bundles in
  mid-2025 (which is also when PC minutes first appear in this repo).
- `size_source` ∈ `head_content_length` (all PC) / `measured_on_disk_public_comments_harvest`
  (26 council) / `unknown_chunked_no_content_length` (280 council — OnBase gives no size).
- `format=na` / `stored_locally=no` because nothing is stored; the row is a pointer.

## Coverage & join
- **391 packets: Council 306 (2020–2026) · Planning Commission 85 (2022–2026).**
- **100% packet coverage of every recorded vote date, both bodies:** Council **147/147**
  vote dates (2020–2026), PC **26/26** (2025–2026). Packet date = meeting date, exact match.
- See `AVAILABILITY.md` for the year table, size math, and the 5 council meetings + 2022–24
  PC-thin-packet gaps.

## Regenerate / refresh
- **Council:** re-derive from `../meeting_minutes/minutes_index.csv` `packet_url` column (kept
  current by `../fetch_new.py`), or re-scrape OnBase directly (POST `/Meetings`,
  DateRangeOptionID=11, docType=5 Agenda_Packet anchors). Rewrite `DownloadFile`→`DownloadFileBytes`.
- **PC:** re-enumerate the AgendaCenter "Planning Commission" section per year and HEAD-size
  each `ViewFile/Agenda/<ref>`.
- Rebuild `index.csv` with the same columns. Sizes: HEAD works for PC; council stays
  size-unknown (chunked) except any packet already on disk.
