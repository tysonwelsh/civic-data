# packets/ — agenda packets & staff reports (as-of 2026-07-05)

Built by `expand-city-sources` (Source 1). The staff analysis (fiscal notes, zoning /
land-use analysis, alternatives, staff recommendation) behind each Salt Lake City
**City Council** (sitting as Council / RDA / CRA / LBA) and **Planning Commission**
agenda item — the "why" behind a motion in `../meeting_minutes/all_votes.csv` (Council)
and `../planning_commission/all_votes.csv` (Planning Commission).

**Two different sources — SLC is asymmetric.** The Council packet is a bundled
whole-meeting PDF from **PrimeGov** (INDEX-ONLY, too large to store). The Planning
Commission has **no PrimeGov presence at all**; its packet is *separable per-item*
staff-report / motion-sheet / agenda PDFs on **slcdocs.com**, of which only the current
year (2026) is machine-discoverable — those born-digital PDFs ARE stored. See
`AVAILABILITY.md` for the full gap log.

## Council side — PrimeGov (INDEX-ONLY)
SLC runs **PrimeGov** (`slc.primegov.com`). The archive API returns, per meeting, a
`documentList` of typed documents:
```
GET https://slc.primegov.com/api/v2/PublicPortal/ListArchivedMeetings?year=YYYY
  -> [ { id (meetingId), committeeId, dateTime, title, documentList:[ {templateId, templateName, compileOutputType, ...} ] } ]
```
- The **Council family is `committeeId == 5`** (Council / RDA / CRA / LBA meetings are all
  interleaved in this one committee — the 4-body split lives in the *minutes*, not the
  packet, so every Council row is keyed **`body=Council`**). `committeeId == 30`
  (Redistricting Advisory Commission, 6 meetings) is a minor board — skipped.
- The **packet doc = `templateName == "Meeting Materials"`** (the compiled whole-meeting
  PDF: agenda + all staff reports + all exhibits). Where a meeting has no Meeting
  Materials, the thin **`Agenda`** is the fallback (`packet_kind=agenda_only`).
  `HTML Minutes` / `Minutes` are **excluded** (already in `../meeting_minutes/`).

**Download URL (stable, same family as WJ + the minutes scraper):**
```
GET https://slc.primegov.com/Public/CompiledDocument?meetingTemplateId=<templateId>
```
where `<templateId>` is the **packet document's** `templateId`. It **302-redirects to a
time-limited Azure blob** `https://pgwest.blob.core.windows.net/slc/Meetings/<meetingId>/<file>.pdf?<SAS>`.
The **SAS token expires ~2 days** — always fetch via `CompiledDocument` (mints a fresh SAS
each call), never cache a blob URL. Browser UA required (`polite_fetch.py` sends one).

> **Quirk — `Agenda` and `HTML Agenda` share one `templateId`.** For an `agenda_only`
> meeting, `CompiledDocument?meetingTemplateId=<that id>` serves the **HTML** agenda, not a
> PDF — hence `agenda_only` rows carry `format=html`. `Meeting Materials` has its own
> unique `templateId` and always resolves to a clean PDF (`format=na`, index-only).

**Why INDEX-ONLY.** SLC packets are even larger than West Jordan's: a per-year sample
probe (43 packets, Content-Length only, body never downloaded) gave **median 31 MB, mean
62 MB, max 438 MB**; the full 504-packet corpus is an estimated **15–30 GB**. Per the
disk-constrained Source-1 mode, **no Council PDF is stored**; `index.csv` catalogs every
meeting with a live `source_url` (fresh SAS on each fetch). To read one: fetch `source_url`
(follow the 302) and extract with **vision or OCR** — packets are site-plan/plat-heavy,
not `pdftotext`-friendly. `size_mb` is populated only on the sampled rows (`probe_status`
distinguishes `200 application/pdf` from `not_probed`).

## Planning Commission side — slcdocs.com (STORED, 2026 only)
The Planning Commission is **not in PrimeGov**. Its agendas + staff reports live on
`slcdocs.com` under `Planning/Planning Commission/<year>/PC <M.DD.YYYY>/` as **separable
per-agenda-item PDFs** (`…Staff Report…`, `…Motion Sheet…`, `…Agenda…`), surfaced by
`https://www.slc.gov/planning/planning-commission-agendas-minutes/` — which only lists the
**current year**. So PC packet coverage here is **2026 only** (11 meeting dates). These are
small **born-digital text** PDFs (median 0.18 MB), so — unlike Council — the skill's
"download small reports, cap the exhibits" branch applies: **files ≤ 10 MB are stored**
(`raw/pc/`, 39 files, 47.8 MB, 38 text / 1 scanned per `pdftotext`); the 13 large
map/plat-heavy exhibits (>10 MB, up to 221 MB) are index-only. Older PC years (2020–2025)
have **no discoverable packet index** and slcdocs held those meetings minutes-only — a real
gap, logged in `AVAILABILITY.md`.

## index.csv columns
`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format,
extraction_method, path, doc_kind, template_name, meeting_id, content_length_bytes,
size_mb, stored_locally, probe_status`
- **`body`** ∈ `Council` (530) / `PlanningCommission` (52). Council rows join to
  `../meeting_minutes/all_votes.csv` by `date`; PC rows to
  `../planning_commission/all_votes.csv` by `date`.
- **`meeting_type`** (Council) ∈ `work` / `formal` / `special` — derived from `title`
  (work session, formal meeting, or oath/limited/retreat/open-house). Same-day work vs
  formal packets stay distinct. PC rows are `regular`.
- **`packet_kind`**: Council ∈ `full_packet` (504, = the Meeting Materials bundle) /
  `agenda_only` (26, thin HTML agenda fallback). PC ∈ `staff_report` (24) / `motion_sheet`
  (18) / `agenda` (10) — the per-item slcdocs doc type.
- **`template_name`** = exact PrimeGov type (`Meeting Materials` / `Agenda`); blank for PC.
- **`format`** ∈ `na` (Council full_packet, not retrieved) / `html` (Council agenda_only) /
  `text` or `scanned` (PC, from `pdftotext`) / `na` (large PC exhibit, index-only).
- **`stored_locally`** = `yes` only for the 39 small PC files (`path` → `raw/pc/…`); `no`
  for all Council rows and large PC exhibits.
- **`size_mb`** = exact for PC and for the 43 sampled Council rows; blank for un-probed
  Council rows (`probe_status=not_probed`).
- **`doc_class, fetch_status, sha256, text_path, text_chars`** (appended 2026-07-16) — the
  §9 primary-document text-layer columns; populated only on the 11 verified PC staff reports
  (see the *Primary-document TEXT layer* section below). Blank everywhere else.

## Primary-document TEXT layer (`doc_class`, PRIMARY_DOCS_ROLLOUT 2026-07-16)
The five §9 text-layer columns (`doc_class, fetch_status, sha256, text_path, text_chars`)
are appended after the city extras. SLC is the **A-lite** case of the rollout: the only
per-item, separable, on-disk primary documents are the **Planning Commission 2026 slice**
on slcdocs.com. `classify_attachments.py` (deterministic, rerunnable) labels only the PC
`staff_report`-kind rows.

| doc_class | rows | fetch_status | what it is |
|---|---|---|---|
| staff_report | **11** | ok | SLC Planning Division land-use staff reports (rezone / zoning-map & text amendment / alley-vacation / planned-development extension / petition-initiation) — the 11 stored (`format=text`) PC staff reports, whole-class verified against their own sidecar text (100%, n=11: Planning-Commission recipient + Planning-Division letterhead + a land-use action token) |
| *(blank)* | 13 | — | the **>10 MB map/plat-heavy PC staff-report exhibits** — never fetched (store-cap, `format=na`, index-only); no on-disk text to verify, no stored binary to hash → honestly unclassified (the same index-only exhibit set logged in AVAILABILITY.md) |

- **Verification.** All 11 stored staff reports were ground-truthed (whole-class, n=11):
  every one is an SLC Planning Division land-use staff report. **0 misses, 0 gate-failures.**
  None is a GP / master-plan **amendment exhibit** (`plan_amendment`) — the ones that cite a
  master/community plan (Sugar House, Plan Salt Lake, Northpoint Small Area Plan) do so in the
  staff report's `MASTER PLAN:` context field, not as the plan-amendment substance. Four rows
  are titled "Memorandum" (PD time-extension requests + a staff-report addendum) but function
  as the item's land-use staff report and make a recommendation — classified `staff_report`.
- **`motion_sheet` (18) / `agenda` (10)** PC rows and all **Council `full_packet` / `agenda_only`**
  rows are NOT target classes → `doc_class` blank by design.
- **Council side is out of scope** (B-no ruling): monolithic PrimeGov `Meeting Materials`
  bundles, index-only, 15–30 GB, vision/OCR-heavy — the four attachment classes are NOT
  separable/extractable for this portal (see AVAILABILITY.md → "Council portal").
- Rerun idempotently: `python3 classify_attachments.py` (`--dry-run` reports counts, writes
  nothing). Reads only what is on disk (sha256 from the stored raw PDF, text_chars from the
  sidecar) — never fabricates a label for an unfetched row.

## How an LLM/agent should use this
1. Find the meeting by `date` (+ `body`, + `meeting_type` for same-day Council work vs
   formal). For a Council item's "why", fetch the `full_packet` `source_url`.
2. Check `size_mb` first when present — Council packets can exceed 100 MB.
3. Council packets: extract with **vision/OCR**, not `pdftotext`. Stored PC `text` files:
   `pdftotext` is fine.
4. To bulk re-hydrate Council: feed the `source_url` column to `polite_fetch.py --batch`
   (budget ~15–30 GB for all 504). PC files are already on disk in `raw/pc/`.

## Regenerate / refresh
Re-pull `ListArchivedMeetings?year=YYYY` (2020–2026), keep `committeeId==5`, pick each
meeting's `Meeting Materials` (else `Agenda`) doc, re-probe a per-year sample of
`/Public/CompiledDocument?meetingTemplateId=<templateId>` for Content-Length. For PC,
re-harvest the slc.gov agendas-minutes page (current year), classify slcdocs PDFs by
filename, store ≤10 MB. `raw/api/*.json` + `raw/pc/agendas_minutes_page.html` are the
frozen source listings; `raw/_fetch_log.jsonl` is the probe/fetch provenance. See
`AVAILABILITY.md` for the method + gap log.
