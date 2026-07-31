---
name: expand-city-sources
description: Expand a civic-data city repo with seven NEW source types — agenda packets/staff reports, moderate-income housing plans + general plan, zoning/land-use ordinances, Utah Public Notice (PMN) backfill, meeting-video transcripts, campaign-finance disclosures, and a primary-document TEXT layer (doc_class classifier over packet attachments + GP text) — each as an additive dataset with retained raw originals, machine-readable provenance, and honest gap records. Use when the user asks to expand/enrich a city's sources beyond the standard minutes/votes/comments/elections layer, one city at a time.
---

# Expand city sources

Adds seven new source types to an existing `<city>_city_council/` repo under
`/Users/tysonwelsh/civic-data`. **Purely additive** — this skill NEVER modifies an
existing dataset (`meeting_minutes/`, `planning_commission/`, `public_comments/`,
`election_results/`, `geo/`, `db/`, `weeks/`). It only creates new sibling datasets and
appends new sections to the city's `README.md` / `CLAUDE.md`.

> **⚠️ CONCURRENCY PRE-FLIGHT — do this FIRST, every run.** Another session (e.g. an audit
> or remediation run) may be writing the same city. If two sessions edit the shared
> `README.md`/`CLAUDE.md` or regenerate `all_votes.csv`/`db/` at once, one clobbers the
> other. Before starting, check the target city is quiet:
> ```
> find <city>_city_council -type f -mmin -5 ! -path '*/raw/*'      # recent writes?
> ls -dt _backups/$(date +%F 2>/dev/null || echo 2026-*)/ 2>/dev/null # backup being written now?
> ```
> If the city's `meeting_minutes/*.csv`, `db/`, `README.md`, or `CLAUDE.md` changed in the
> last few minutes, or a `_backups/<today>/` tree is actively growing, **abort and tell the
> user** — do not run alongside another writer. (Lehi pilot, 2026-07-02: a concurrent
> remediation session rewrote Lehi's vote layer mid-run; harmless only because it backed up
> first, but the doc edits collided.) To shrink the collision surface even in the solo case,
> defer parent `README.md`/`CLAUDE.md` edits to a single final step; the per-dataset
> `CLAUDE.md` files are the durable record.

## Inputs

- **city** (required) — e.g. `lehi`, `st_george`. Resolves to `<city>_city_council/`.
- **sources** (optional) — subset of the seven by number/name; default = all seven, in the
  priority order below. Do a source only if named (or if doing all).

Before touching anything, **read the city's `recon.md`** (portal vendor, URL patterns,
council structure, county, GIS ids, known blockers) and skim its `README.md` +
`meeting_minutes/CLAUDE.md`. The recon file is the retrieval map — most per-city specifics
(vendor, host, filename conventions, PMN body id, election county) are already in it.

## The seven source types (priority order)

Do them in this order; each is independent, so a blocked source never stalls the others.

### 1. Agenda packets / staff reports → `<city>_city_council/packets/`
The staff analysis behind each council and Planning Commission agenda item — fiscal notes,
zoning analysis, alternatives, staff recommendation. This is the single highest-value
addition: it join to existing minutes/votes by meeting date and explains *why* items passed.

- **Where:** the city's agenda portal (vendor in `recon.md`). Packets are usually a
  distinct document type alongside the agenda/minutes:
  - *PrimeGov* — `/api/…/meetings` JSON; each meeting has a packet/document URL.
  - *Granicus (ViewPublisher)* — the combined `ViewPublisher.php?view_id=<n>` table lists
    all bodies; scrape it and classify each row by body name. **There is often no single
    packet doc**: the agenda link (`AgendaViewer.php`/`GeneratedAgendaViewer.php`, follow the
    302 with browser UA + Referer — a 14-byte `Redirecting…` stub means you forgot to follow
    redirects) resolves to an **agenda-outline PDF that embeds `/URI` hyperlinks** to each
    item's Legistar staff report/exhibit. So the real packet = agenda PDF + its linked
    attachments: extract the embedded links (regex `/URI\s*\(([^)]+)\)` over the PDF bytes,
    or a PDF lib's annotation/link API) and fetch each. Attachment hosts are usually
    `<city>.granicus.com/services/legistar/download/…` and
    `legistarweb-production.s3.amazonaws.com/…`. (Some smaller Granicus sites do expose a
    single `DocumentViewer.php?file=<hash>.pdf` packet — check both.)
  - *CivicClerk / Legistar* — API or `AgendaViewer`/attachments per event.
  - *Revize / CivicPlus* — static file host; packets are an "Agenda Packets" folder
    parallel to "Minutes" (scrape the agendas-and-minutes page for links; don't guess URLs).
  - *CivicPlus **AgendaCenter*** (a.k.a. CivicEngage; sslc.gov, millcreek, bluffdale, nephi) —
    the per-category listing is an AJAX endpoint, **not** a static page: GET
    `<host>/AgendaCenter/UpdateCategoryList?catID=<n>&year=<YYYY>&term=&Keywords=` per body
    (catID) per year — it returns the HTML fragment of that year's meeting rows (each with an
    Agenda/Minutes/Packet link). Enumerate `catID` (Council/PC/RDA…) × the year range to build
    the date index; the document links resolve to
    `<host>/AgendaCenter/ViewFile/{Agenda,Minutes,AgendaPacket}/<opaque-id>` (opaque ids —
    crawl the listing, don't template). Packets ride under the `Agenda` doc-type flagged by a
    "PACKET" title-keyword on some sites (bluffdale); on others (SSL) the ArchivedMinutes slot
    (`ViewFile/ArchivedMinutes/<id>`) is a first-class minutes-recovery surface too. Verified in
    `south_salt_lake_city_council/{recon.md,packets/CLAUDE.md}` and its `sources.csv`
    (`.../AgendaCenter/ViewFile/ArchivedMinutes/...`).
  - **CivicEngage/CivicPlus current-cycle-only trap:** some AgendaCenter/CivicEngage packet
    pages expose **only the current cycle's** packets — no historical archive (Taylorsville:
    2020–2026 packets unrecoverable, an honest gap; Wayback captures of the packet pages are the
    only low-yield partial-recovery lead). When `UpdateCategoryList?year=<prior>` returns empty
    for every back-year, that's a portal limit, not a scraper miss — record the recoverable
    window in `AVAILABILITY.md` and note Wayback as the fallback, don't keep re-crawling.
- **Store — pick the mode by portal, and confirm the disk budget with the user:**
  - *Granicus / separable-attachment portals* — the narrative staff report is a small text
    PDF, separate from bulky exhibits. Download the small reports to `packets/raw/<date>/…`
    verbatim and cap the bulky exhibits with `polite_fetch.py --max-bytes 4000000` (skipped
    files auto-log to `_fetch_log.jsonl`; also list them in `dropped_oversize.csv`).
  - *Revize / CivicPlus / static-CMS portals* — the packet is usually **one bundled
    whole-meeting PDF** (agenda + all staff reports + all exhibits), 10–150 MB, heavy with
    maps/plats/site plans (**not text-convertible** — vision/OCR only). A blanket `--max-bytes`
    cap here drops *entire meetings*, including their staff analysis — do NOT use it. Instead
    HEAD-probe every packet's `Content-Length` (`polite_fetch.py --probe`) and estimate the
    full-set size; a year of these is multi-GB. If that exceeds the disk budget, build an
    **INDEX-ONLY dataset**: `packets/index.csv` catalogs every packet with a live `source_url`,
    `size_mb`, and `packet_kind` (`full_packet` vs thin `agenda_packet`), `format=na`,
    `stored_locally=no` — no PDFs on disk; an LLM fetches a specific one on demand. This is a
    **documented, allowed exception** to "retain every raw original" (the files are public +
    re-fetchable; keep `raw/_fetch_log.jsonl` for provenance) — state it explicitly in the
    dataset `CLAUDE.md`/`AVAILABILITY.md` and note vision/OCR is required to read one.
  - Either way: `index.csv` is keyed by `date` (+ `body`, `meeting_type` for same-day Work vs
    Regular) so items join to `all_votes.csv`/minutes. **Never silently cap or drop** — record
    the year window, the mode (stored vs index-only), and the size math in `AVAILABILITY.md`.
    Watch for a council-vs-PC asymmetry (a city may publish PC packets but not council ones,
    or hyperlink one body's and only *name* the other's — a publishing gap, not a scraper
    miss; log it).
- **Text sidecars are MANDATORY for stored born-digital packets** (policy change
  2026-07-07, REFACTOR_PLAN 5.6 — "extract lazily" produced zero sidecars in every
  city and left the staff analysis PDF-locked): after acquisition run
  `python3 scripts/extract_packet_text.py <slug>` (idempotent; writes
  `packets/text/<stem>.txt`, keeps only ≥200-char real text, logs image-only/oversize
  honestly to `packets/text/_extraction_log.csv`). The sidecars feed `cities.db`
  `fts_packet` on the next `build_cities_db.py` run. Record `extraction_method` per row.
- **`path` values are dataset-relative including `raw/`** (e.g. `raw/2024-04-23/x.pdf`)
  — never repo-relative with the city-dir prefix (that convention hid lehi/ogden
  packets from the sources index until 2026-07-07).

### 2. Moderate-income housing plans + annual reports → `<city>_city_council/housing_plans/`
Utah requires every municipality to adopt a **moderate income housing (MIH) element** in
its general plan (Utah Code **10-9a-403/408**, amended by **HB 462** 2022 and later) and
to file **annual implementation reports** with the state.

- **Where:**
  - City general-plan / community-development page → the adopted **General Plan** and its
    **MIH element/plan** (grab the current General Plan too — it's the land-use context).
  - **State repository** — Utah Dept. of Workforce Services, **Housing & Community
    Development (HCD)**. Stable, generic URLs (verified 2026-07): index
    `https://jobs.utah.gov/housing/affordable/moderate/reporting/`; the annual reports are
    published as **statewide compilation PDFs, not per-city files** —
    `.../reporting/documents/{23,24,25}reports.pdf` (pattern `NNreports.pdf`) — plus the SB 34
    progress summary `.../reporting/documents/sb34.pdf`. Correct pattern: download the
    compilation, find the city's alphabetical page range (bracket by the next city's header),
    extract a `text/<city>-<year>.txt` sidecar. Confirm the city is present; absence of a
    standalone per-city report is expected, not a gap.
  - **Discovery tip (generic):** city CMSs migrate and web-search-cached PDF URLs go stale
    (e.g. dead `/wp-content/uploads/…`; live docs at `/media/<hash>/<slug>.pdf`). **Crawl the
    city `sitemap.xml` first** and navigate to the planning/general-plan page, rather than
    trusting search-result URLs.
- **Store:** `housing_plans/raw/` (each PDF verbatim) + `housing_plans/index.csv`
  (`date` = adoption/filing/report year, `doc_type` ∈ general_plan / mih_element /
  mih_annual_report / compliance_letter). If the city hasn't filed something, that is a
  finding → `AVAILABILITY.md`.

### 3. Zoning / land-use ordinances → `<city>_city_council/ordinances/`
Adopted ordinance texts — especially **zoning map and text amendments** — so a council vote
on "Ordinance 2023-7" links to what the ordinance actually did.

- **Where:** the city's codified-code host (**Municode**, **Sterling Codifiers**,
  **American Legal**, **Code Publishing / Franklin Legal**, **municipalcodeonline.com**) —
  the recon or the city site says which — and the city's **adopted-ordinance list** (often a
  clerk/recorder page or a Laserfiche/portal search). The codified code gives current text;
  the adopted-ordinance list gives the number → date → subject mapping.
  - **municipalcodeonline.com — the full ordinance/resolution back-catalog on public S3.**
    Unlike the 403 hosts below, MCO exposes each entity's *individual adopted* ordinances and
    resolutions (not just consolidated code) as PDFs on a us-west-2 bucket. The pattern
    (verified, `white_city_city_council/sources.csv` — 136 ordinances/resolutions 2017+):
    `https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/<slug>/{ordinances,resolutions}/documents/<Name>.pdf`
    — already **path-style** (`s3-us-west-2.amazonaws.com/<bucket>/…`), which you must keep:
    the bucket name `municipalcodeonline.com-new` contains dots/dashes that break `requests`
    virtual-host TLS exactly like the underscore Granicus buckets, so never rewrite it to
    `<bucket>.s3.amazonaws.com`. Enumerate the `documents/` listing per doc-type folder. These
    scans are frequently image-only → `ocr_tesseract` (see §4 OCR discipline). MCO's codified
    *book* pages (`book/*`) are auth-gated — the loose ordinance PDFs are the accessible layer.
- **Store:** `ordinances/raw/` + `ordinances/index.csv` with the exact §9 contract
  header (SCHEMA_SPEC.md), whose linkage columns `matched_motion_date,
  matched_motion_no, match_confidence` map each ordinance to a row in
  `meeting_minutes/all_votes.csv`. **Ordinance BODY text gets a `text/<stem>.txt`
  sidecar wherever the raw is born-digital** (sandy shipped only Legistar JSON
  metadata and its ordinance text was unsearchable until flagged) — the sidecars
  feed `cities.db` `fts_ordinance`.
  - **Linkage rule:** join by adoption date + ordinance number cited in the motion text.
    Confidence: `high` = date and number both cited in the motion; `medium` = date match +
    subject agreement, number not in motion; `low` = date-only or fuzzy. **Never force a
    match** — an unmatched ordinance keeps empty match fields and `match_confidence=none`.
    Record the linkage method in `ordinances/CLAUDE.md`.
- **When there is no online ordinance archive** (common: American Legal
  `codelibrary.amlegal.com` and similar hosts are **403 bot-protected and
  current-consolidated-text only**; the city often posts only the *current* year's
  Recorder-certified "Notice of Ordinance Adoption and Summary" PDFs, back-catalog on PMN) —
  the **minutes themselves are the backbone.** If council motions cite `Ordinance #YYYY-NN`
  in their text (many do, richly), derive the number→date→subject→motion index straight from
  `all_votes.csv`. **State the honest caveat:** an index *derived from* the motions makes the
  linkage `high` *by construction* (within-source), NOT an independent cross-match — use a
  distinct value like `within_source` for those rows so it isn't read as corroborated. Grab
  any posted "Notice of Ordinance Adoption and Summary" PDFs, and run this source together
  with source 4 (PMN holds the notice back-catalog).
  - **PMN as the ordinance archive (when the code host is 403).** Every adopted ordinance is
    published as a Recorder-certified "Notice of Ordinance" attachment on Utah Public Notice,
    so the city's PMN body is an **independent** ordinance back-catalog the amlegal/codifier
    403 wall can't reach. Harvest it with the §4 GET-only cumulative crawl
    (`/pmn/list/notices.html?id=<body>&page=<big-N>`), filtering the attachment-type labels for
    "Notice of Ordinance" (evidence: TODO PMN body-1788 / body-720 harvests). This is worth two
    things: (a) fills the number→date→subject index the codifier withholds; (b) **upgrades
    `within_source` rows toward `medium`** — a PMN "Notice of Ordinance" that matches a
    minutes-derived row is a genuine independent corroborator, so the linkage is no longer
    single-source. Note PMN purges deep history (kearns/magna/copperton pre-2018), so PMN
    absence proves nothing.

### 4. Utah Public Notice (PMN) backfill → into the EXISTING dataset's gap-log, plus recovered files
`utah.gov/pmn` is the statewide public-notice repository; every public body posts
agendas/minutes there. It has already rescued gaps in this repo (St. George 2020–21).

- **Where / body-id discovery (generic, GET-only):** `https://www.utah.gov/pmn/`. Body ids
  are **assigned globally, not sequentially per city** — do not guess by proximity (Lehi
  council=2512 but PC=2651, RDA=3315). Find them via the chain
  `/pmn/list/entities.html?id=3&limit=2000` (govType 3 = Municipality) → the city's entity id
  → `/pmn/list/publicBodies.html?id=<entityId>&limit=2000` lists every body + id. Notice
  pages are `/pmn/sitemap/notice/<ID>.html`; attachments `/pmn/files/<FILE_ID>.pdf` (opaque
  ids — crawl notice pages, not date-templated).
- **Crawl gotcha (critical):** the notices *list* view shows "only past 6 months" and the
  historical *search* is POST/CSRF (violates polite-GET and `polite_fetch.py` can't POST).
  The escape hatch: `/pmn/list/notices.html?id=<body>&page=N` is **cumulative** — a single
  high page number (e.g. 200) returns the body's *entire* notice history via one GET. Parse
  attachment type labels from the list HTML (`(Meeting Minutes)`, `(Agenda)`, …) to filter to
  minutes without opening every notice page.
- **What to do:** cross-check by **meeting DATE, not per-year counts.** Bodies attach minutes
  to PMN sporadically, so the repo is usually a *superset* and per-year counts hide the real
  gaps. Do a per-date set-difference (repo `minutes_index.csv` dates vs PMN minutes dates,
  ±3–4 day tolerance for meeting-date vs posted-date offset). For each **missing** date, fetch
  the PMN minutes (or agenda if no minutes), extract, and add it. **Do not modify existing
  rows** — append recovered meetings and log every recovery.
- **Store:** recovered minutes go into a clearly-labeled backfill area
  `pmn_backfill/raw/` + `pmn_backfill/index.csv` (same 8-col schema as `minutes_index.csv`
  plus `extraction_method`), and a `pmn_backfill/coverage.md` table (per year: repo count,
  PMN count, recovered, still-missing). Keep it a *separate* dataset the user can review
  and merge deliberately — never hand-edit the audited `minutes/` layer in place.

### 5. Meeting video transcripts → `<city>_city_council/transcripts/`
Most cities post council/PC meetings on **YouTube** (some on Granicus/Vimeo). Caption
tracks capture the deliberation the clerk's minutes summarize away.

- **Where:** find the city's YouTube channel (recon or a search); map videos to meeting
  dates by title/date. Retrieve the **caption track where it exists** — these are
  **ASR (automatic speech recognition) quality**, verbatim-ish but error-prone.
- **Tools:** the clean path is `yt-dlp --write-auto-sub --write-sub --sub-format vtt
  --skip-download`. `yt-dlp` is **frequently NOT installed** — so **step 0: try to install
  it** (`python3 -m pip install yt-dlp`; Python is present). Only if install is blocked, fall
  back to recording the channel + video→date map and marking transcripts `unrecovered` with
  the reason (`format=na`, `caption_type` = the type that exists on the source). Channel
  discovery: WebSearch `"<City> City <State>" youtube public meetings`; note channel `/videos`
  pages are JS-rendered (plain WebFetch sees only the footer) — enumerate videos with
  `yt-dlp --flat-playlist` against the channel/playlist URL. Do NOT scrape YouTube in ways
  that violate ToS; captions via the official timedtext/yt-dlp path only. **OpenUtah /
  @UtahRecord mirror** (`<city>.openutah.org`; the `@UtahRecord` YouTube channel is the video
  side) is a recurring Utah meeting-video/transcript mirror that often **covers the exact gap a
  city's own YouTube leaves** — e.g. after a city moves meetings off YouTube to Swagit,
  OpenUtah keeps indexing them with AI transcripts (west_jordan: 196 indexed / 141 transcribed,
  current through the migration gap YouTube stops at 2025-02-04). **But** its verbatim
  transcript text is served client-side behind `robots.txt Disallow: /api/`, so treat it as a
  **summary/metadata source only** under the polite rule, not a bulk grab — record it as the
  recovery lead in `AVAILABILITY.md` and point the user at the underlying Swagit captions.
- **Audio-only-city branch (the §5 fallback when there is NO meeting video anywhere).** Some
  cities publish only an **audio** archive (Taylorsville "Audio Recordings"; PR-only YouTube
  with no gavel-to-gavel video) — no caption track exists to fetch. The branch, in order:
  (1) the OpenUtah/@UtahRecord mirror for whatever AI transcripts it indexes (robots-limited →
  metadata/manual reference only, per above); (2) **Whisper over the city/PMN/Streamline MP3s**
  — **owner-gated, do NOT run by default** (expensive; user decides), list the high-value audio
  meetings in `AVAILABILITY.md` with why they matter. Mark the meetings `unrecovered`
  (`format=na`, `caption_type` = what actually exists on the source, e.g. `audio`) — an
  audio-only city with no captions is an honest gap, not a scraper miss.
- **Store:** `transcripts/raw/<date>.<ext>` (the raw .vtt/.srt) + a cleaned
  `transcripts/text/<date>.md` **clearly headed** "AUTOMATIC TRANSCRIPTION — ASR, expect
  word errors; not an official record" + `transcripts/index.csv` (`date, video_url,
  video_id, caption_type` ∈ manual/asr, `format=caption`).
- **Whisper:** only *propose* Whisper transcription for high-value **untranscribed**
  meetings (list them in `AVAILABILITY.md` with why they matter); **do not run Whisper by
  default** — it is expensive and the user decides.

### 6. Campaign-finance disclosures → `<city>_city_council/campaign_finance/`
Filings for municipal candidates, completing the **elections → members → votes** chain
(who funded the people casting the votes).

- **Where (investigate per city, in this order):**
  - **City recorder / elections page FIRST** (`/elections/financial-disclosures/` and
    `/campaign-finance-disclosures/`). For mid-size Utah cities the filings live here, NOT on
    the state or county site. `disclosures.utah.gov` frequently just **redirects to the city
    page**; the county posts county/state filings, not municipal.
  - **Wayback Machine — a first-class tool here, not a last resort.** Cities migrate CMS and
    silently drop old `/wp-content/uploads/…` PDFs; the legacy disclosure page + its PDFs
    survive only in the Internet Archive. Recipe: query CDX
    `https://web.archive.org/cdx/search/cdx?url=<page>&output=json` → fetch archived HTML
    `https://web.archive.org/web/<ts>id_/<url>` → extract original PDF links → fetch each
    `…/web/<ts>id_/<pdf-url>`. **`WebFetch` cannot reach web.archive.org — use
    `polite_fetch.py`/urllib.** The `id_` form 404s if that exact timestamp lacks a capture
    (no auto-redirect to nearest) — verify with the availability/CDX API before declaring
    unrecoverable. **Prefix saved filenames with the upload `YYYYMM` (or media hash)** — bare
    basenames collide across filing periods and silently overwrite.
  - **County clerk** — occasionally posts municipal filings.
- **Store:** `campaign_finance/raw/` + `campaign_finance/index.csv` (`candidate, office,
  election_year, filing_type` ∈ interim/summary/contribution/expenditure, `source_url`,
  `retrieved_date`, `format`, `extraction_method`). Join candidates to
  `election_results/`. **Document honestly what isn't published** — Utah municipal filing
  is genuinely fragmented and an honest empty/partial result is valid. Note that finance data
  can **surface election-record gaps** (a filing set proving a primary the elections docs
  don't list) — flag such discrepancies, do NOT edit the existing election dataset.
- **CRITICAL — multiple filings per cycle / the double-count trap.** Candidates file **several
  reports per election cycle** (interim reports pre-primary/pre-general + a year-end summary/final),
  so there is **NOT one filing per candidate.** Set `filing_type` (interim/summary/final) per PDF,
  and record a per-filing `is_incremental` — but do NOT assume it's a per-city constant: **the
  filing style varies BY CANDIDATE within one city** (Logan: 7 incremental + 2 cumulative filers;
  Orem: some candidates' year-end *summary* is the true cumulative cycle total, others leave it
  near-empty and the money is in the interims; some file *cumulative interims* that each restate
  cycle-to-date and blow up 6× if summed). **Any per-candidate or per-race dollar total MUST be
  computed with the dedup in `scripts/campaign_finance/cycle_totals.py` (→ `cycle_totals.csv`),
  never by summing `filing_totals.csv`.** When structuring a new city's finance data: (a) classify
  filing_type + is_incremental per filing; (b) for a sanity check, compare each candidate's latest
  summary total vs their summed interims — if they diverge a lot, the filer is mixed/cumulative and
  needs the max-with-cumulative-guard rule, not a blind sum; (c) run `cycle_totals.py --all` and
  investigate every `review_flag` before quoting any cross-city "most expensive race" figure.
- **CRITICAL — the mandatory-annual regime / the `filing_regime` column.** Utah officeholders
  file a **mandatory annual** financial statement (the March-1 / year-end statement) *regardless
  of an election* — a DIFFERENT regime from the pre-primary/pre-general **election-cycle** C&E
  filings. These carry real money (Taylorsville: Overson 2025 annual $11,500) but they are NOT
  campaign spending for a race and would **inflate race totals if summed in.** So `filing_totals.csv`
  carries a trailing **`filing_regime`** column (∈ `election_cycle` | `mandatory_annual`; blank/
  `election_cycle` for cities that file only C&E, e.g. Magna — set it explicitly in `build_finance.py`),
  and **`cycle_totals.py` must filter to `filing_regime='election_cycle'`** so annual-regime rows
  (typically blank `election_year`) never enter a per-candidate or per-race cycle total. Verified
  across `*/campaign_finance/build_finance.py` + `filing_totals.csv` (the column is the header's
  last field). Keep the annual filings as an acquired, itemizable parallel stream — they surface
  officeholder finances — just regime-excluded from race math.

### 7. Primary-document TEXT layer (doc_class classifier over packets + GP text) — added 2026-07-16

**Normative design + reference implementation: repo-root `PRIMARY_DOCS_PILOT_SPEC.md` +
`sandy_city_council/packets/` (classifier, pipeline, gates, acceptance test — READ BOTH
FIRST).** Motivation: minutes *paraphrase* primary documents and can invert meaning (the
Sandy Sharkey-memo incident — a dropped "Eliminate" reversed a reading). This source makes
the PRIMARY text the default FTS hit, one `matter_id`/date join from the vote. Text is
~1–5% of PDF size, so fetch → extract text → **discard binary** (keep sha256 + source_url
as provenance) — rot-proof and disk-cheap (Sandy: 25.2 MB vs a 2.26 GB counterfactual;
26/889 URLs were ALREADY dead at first fetch).

- **The five classes** (`doc_class` values): `staff_report` (land-use staff reports),
  `member_memo` (council-member proposal memos/amendment text), `general_plan` (draft-era
  GP chapters + small/station-area plans — goes in `housing_plans/`, which RETAINS raws
  per its convention), `plan_amendment` (GP/LU-map amendment exhibits),
  `development_agreement` (DAs/MDAs). An empty class is a valid honest result (Sandy has
  zero DAs). `code_snapshot` (class 6) is NOT part of this source — codifier hosts are
  mostly auth-gated (MCO `book/*`); see the spec §7/§10 before attempting it anywhere.
- **Classifier before ANY bulk fetch** — a deterministic, rerunnable script in `packets/`
  emitting a `doc_class` column (blank = honestly unclassified, never force-bucketed).
  Inputs: attachment title/filename tokens + whatever matter/agenda metadata the portal
  gives (Legistar cities: the `legistar_matter` join; others: agenda-item context, case
  keys, packet section headings). **Gates: ≥95% sampled precision per class (n≥50 or the
  whole class) + a ~100-row unclassified recall sample iterated to <10% est. miss** —
  record the metrics in the dataset CLAUDE.md.
- **Portal reality check (confirmed by the 2026-07-16 30-city rollout):** Sandy's
  per-attachment Legistar index with a matter-metadata join is the EXCEPTION — no other
  city had one. The working classifier inputs everywhere else: title/filename tokens +
  `body`/`packet_kind` + in-title case/instrument numbers, plus the **sidecar-head**
  (first ~500 chars of the existing text sidecar) where titles are opaque — still
  deterministic. Recurring high-precision signals: the MSD staff-report template header
  (`Meeting Body:/Planner:/File Number & Project Type:/Staff Recommendation:` — kearns/
  copperton/emigration_canyon/magna) and `OAM/REZ/CUP/VAR/RWD/SUB####-######` case keys.
  Most cities are **classify-in-place** (sidecars already exist from the mandatory-sidecar
  policy — link `text_path`, no fetch). Cities whose `packets/` hold monolithic
  `full_packet` PDFs: classify at the packet-SECTION level ONLY if sections are separable
  at high confidence via an explicit anchor (a TOC manifest or rigid template) — the
  `packet_kind=packet_section` row scheme is standardized in SCHEMA_SPEC §9 (sha256 blank,
  `extraction_method=section_split`, parent_path/case_key extras; reference impls
  cottonwood_heights + magna, both boundary-verification-gated). Otherwise the existing
  full-packet text sidecar already serves FTS and the honest answer is "classes not
  separable for this portal" — document it in AVAILABILITY.md, don't force it. All 31
  cities carry a dated disposition record as of 2026-07-16; re-triage only if a portal
  changes shape.
- **Index columns** (additive, documented): `doc_class`, `fetch_status`, `sha256`,
  `text_path`, `text_chars` (`stored_locally` keeps describing the binary). Text sidecars
  under `packets/text/…`. Scans → `needs_ocr` flag (a later vision pass), 404s → dated
  honest gaps. Use `polite_fetch.py` (headerless batch files!).
- **Federation is already wired**: `scripts/build_search_layer.py` honors explicit
  `text_path` index columns and federates `doc_class` into `document` + `fts_packet` —
  no script change needed per city; just rebuild at the work-package boundary.
- **Acceptance per city** (the Sharkey pattern): pick one known consequential
  memo/staff-report; after federation its FTS snippet must return the document's OWN
  text and join to the acting motion. Plus: validate_dataset PASS, 10-doc spot-check
  (right document for the matter), disk ledger reported.

## NON-NEGOTIABLE RULES (encode these in every dataset)

These are lessons the repo learned the hard way — see `_audits/2026-07-02/report.md`
(§Methodology: raw PDFs discarded in 11/13 cities; provenance partial; doc drift). Every
new dataset must satisfy `scripts/validate_dataset.py`.

1. **RETAIN EVERY RAW ORIGINAL.** Each dataset has a `raw/` subdir holding the fetched
   PDFs/HTML/JSON *exactly as downloaded*. Never delete or normalize them. Fetch through
   `scripts/polite_fetch.py`, which also writes a `_fetch_log.jsonl` (url, http status,
   bytes, sha256, retrieved_utc) — that log is machine-readable provenance for the bytes.
2. **MACHINE-READABLE PROVENANCE — the §9 CONTRACT HEADERS.** Every dataset's
   `index.csv` MUST begin with its source type's EXACT contract header from
   **SCHEMA_SPEC.md §9** (adopted 2026-07-06 — all 16 cities migrated; enforced by
   `validate_dataset.py`). City-specific extra columns go ONLY AFTER the contract
   columns. Blank values are fine (= not recorded); never invent. `format` ∈
   `text` (born-digital) / `scanned` / `html` / `json` / `xml` / `video` / `caption` /
   `na`. NEVER reintroduce the retired synonyms (doc_type-for-packets,
   retained_raw_path, zoning, motion_result, file_id/fid, pmn_body, report_period,
   filing_period — see the §9 retirement list).
3. **NEVER FABRICATE; GAPS ARE DATA.** If a city doesn't publish something, record what you
   checked and when in `AVAILABILITY.md` (prose) or `unrecovered.csv` (rows). An honest
   empty dataset is a valid, complete result — six cities already have honestly-empty
   public_comments. Do not invent, infer, or "reconstruct" content that isn't in a source.
4. **EXTRACTION DISCIPLINE.**
   - Born-digital PDFs → `pdftotext -layout` (or pymupdf). Scanned/image PDFs → OCR
     (`tesseract`) or vision, **labeled as such per file** in `extraction_method`.
     - **tesseract gotchas (from the Orem OCR pass, 2026-07-19):** (a) **it can't read `/tmp`
       here** — render the page images and point tesseract's input/output at the session
       **scratchpad** dir (see the top-of-prompt scratchpad path), not `/tmp`, or the run fails
       to open the file; (b) **tesseract writes non-UTF-8 bytes to stderr** (progress/leptonica
       warnings), so a naive `subprocess` capture that decodes stdout/stderr as UTF-8 crashes —
       capture with `errors='replace'` (or `text=False` and decode yourself). Rasterize
       image-only scans at ~200–300 DPI before OCR. MCO (§3) and other scan-only ordinance/
       minutes sources land here (`ocr_tesseract`).
   - Preserve source typos — do NOT let an LLM "clean up" documents. Implausibly clean
     text from a bad scan is a hallucination signal.
   - After extracting **any text corpus**, run the shared screener and investigate every
     outlier before declaring the dataset done:
     ```
     python3 .claude/skills/audit-city-data/scripts/screen_corpus.py <dir>
     ```
5. **PRESERVE NUANCE.** Keep city-faithful raw values verbatim. If you add normalized
   fields (dates, canonical names), add them ALONGSIDE the raw value, never overwriting.
   **Do not modify any existing dataset** — additive only.
6. **DOCUMENT.** Update the city's `README.md` and `CLAUDE.md` with a section per new
   dataset: source, method, coverage window, record counts, known limitations, as-of date.
   Give each dataset its own `CLAUDE.md` for build/linkage detail. Keep counts truthful
   (doc drift — docs contradicting data — is itself an audit finding). *(When fanning out to
   parallel agents, the orchestrator does the parent `README.md`/`CLAUDE.md` edits once at
   the end; agents write only their own dataset docs — see Procedure §3.)*
7. **BE A POLITE SCRAPER.** Public-records GETs only, throttled (`polite_fetch.py`
   defaults to ≥1s/host with backoff). No auth, no bypassing, no POST. If a portal is a JS
   SPA, use its underlying JSON/export endpoint — don't hammer or headless-render abusively.

## Standard dataset layout

```
<city>_city_council/<dataset>/
  raw/                     originals verbatim (+ _fetch_log.jsonl from polite_fetch.py)
    <date>/ or flat        (subfolder-by-date for packets/transcripts; flat is fine otherwise)
  text/  (optional)        extracted text sidecars, labeled by extraction_method
  index.csv                REQUIRED — date,title,source_url,retrieved_date,format,extraction_method[,…]
  AVAILABILITY.md          what was checked, what exists, what doesn't, as-of date
  unrecovered.csv (opt.)   machine-readable list of known-missing items
  CLAUDE.md                build method, linkage logic, caveats
```

## Procedure

0. **Concurrency pre-flight** (see the callout at the top). Confirm no other session is
   writing the target city and no `_backups/<today>/` tree is actively growing. Abort if it is.
1. **Read recon.md + existing docs.** Confirm vendor, hosts, body ids, county, structure.
2. **Scope.** Decide the source subset and coverage window. State the plan briefly.
3. **Per source, fan out if useful.** For a full seven-source run you may dispatch
   `general-purpose` agents per source (they are independent), but each agent MUST follow
   the non-negotiable rules and return structured results (counts + paths + gaps), not
   prose. Retrieval is I/O-bound and portal-specific — one focused agent per source keeps
   context clean. **Doc ownership when fanning out:** each agent writes ONLY its own
   dataset's `CLAUDE.md`/`AVAILABILITY.md`/`index.csv`. The **orchestrator** writes the
   parent `README.md`/`CLAUDE.md` sections once, at the end (step 9) — parallel agents must
   NOT edit those shared files concurrently (lost-update risk). Say so in each agent's prompt.
4. **Fetch** through `scripts/polite_fetch.py` into the dataset's `raw/`.
5. **Extract** with the right method per file; label it. Run `screen_corpus.py` on any text
   corpus; investigate outliers.
6. **Build `index.csv`** with the required columns + source-specific columns. For
   ordinances, compute the motion linkage with confidence.
7. **Record gaps** in `AVAILABILITY.md` / `unrecovered.csv`. An empty dataset still gets
   these.
8. **Validate:** `python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py
   <dataset_dir>` — must PASS.
9. **Document:** add a section to the city `README.md` + `CLAUDE.md`; write the dataset
   `CLAUDE.md`. Keep counts exact.
10. **Load into the federated db:** `python3 scripts/build_cities_db.py` — the search
    layer (`scripts/build_search_layer.py`, run automatically) picks up the new
    dataset's index.csv into the `document` catalog (+ `ordinance`/`cf_*`/`comment`
    tables and the `fts_*` indexes where applicable). A dataset that isn't in
    cities.db after this step means its index deviates from the §9 contract — fix,
    don't skip.
11. **Report** (see below).

## Deliverable report (always end with this)

A short report covering, per source type:
- **Yielded** — what was retrieved (counts, coverage window, formats, raw bytes).
- **Unavailable** — what the city doesn't publish and how you verified it.
- **Time** — rough wall-clock per source.
- **Skill changes** — what you'd change in this SKILL before scaling to other cities
  (per-vendor quirks, missing tools like `yt-dlp`, portal specifics worth adding to recon).

## Bundled scripts

- `scripts/polite_fetch.py` — throttled, logged, retrying public-records fetcher. Use for
  ALL raw downloads. Flags: `--probe URL` (liveness/content-type), `--batch FILE` (a
  `url[,name]` list), `--referer URL`, `--now <ISO>` (freeze `retrieved_utc` under a frozen
  clock), `--size-only URL` (**HEAD Content-Length only, no body GET** — use this to size
  large bundled packets before deciding stored-vs-index-only; `--probe` downloads the full
  body and is abusive for GB-scale PDFs), and `--max-bytes N` (HEAD-probe Content-Length and
  **skip+log oversize files**). It **auto-rewrites virtual-host S3
  URLs to path-style** when the bucket name contains an underscore
  (`granicus_production_attachments.s3.amazonaws.com` → `s3.amazonaws.com/granicus_production_attachments/…`),
  which Python `requests` otherwise rejects on a TLS hostname mismatch — this bites Granicus
  attachment hosts.
- `scripts/validate_dataset.py` — lints a dataset dir against the non-negotiable rules
  (raw/ present, index.csv schema, format vocab, gap-log for empties, path existence).
  **Gotcha:** an index.csv `path` column must be dataset-relative *including* `raw/`
  (e.g. `raw/2024-04-23/foo.pdf`) for the linter to resolve it.

## Notes / gotchas learned so far

- **Granicus** minutes/packets: MinutesViewer/DocumentViewer 302-redirect; use browser UA
  + Referer and follow redirects, or you get a 14-byte stub. One combined ViewPublisher
  table holds all bodies — classify each row by meeting-name string.
- **Revize / static CMS** (e.g. St. George): no API; scrape the agendas-and-minutes page
  for links, filename spacing/suffix varies — don't guess URLs.
- **Enhanced Voting** election portals are JS SPAs — empty to plain fetch; use the export
  endpoint. (Relevant if campaign finance points back to election data.)
- **yt-dlp is frequently NOT installed** — `python3 -m pip install yt-dlp` first; only if
  that's blocked, log the video→date map and mark transcripts unrecovered.
- **PMN file ids are opaque** — crawl notice pages (GET-only cumulative
  `notices.html?id=<body>&page=N`); you cannot template URLs by date. Cross-check by date,
  not per-year counts.
- **Granicus S3 attachment buckets** have underscores that break `requests` TLS —
  `polite_fetch.py` auto-rewrites to path-style; if you fetch outside it, do the same.
- **municipalcodeonline.com** is a full loose-ordinance back-catalog on a **us-west-2 S3**
  bucket (`s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/<slug>/…`) — keep it
  **path-style** (the dotted bucket name breaks virtual-host TLS); scans are usually
  `ocr_tesseract`. Full recipe in §3.
- **tesseract here can't read `/tmp` and emits non-UTF-8 stderr** — OCR into the session
  scratchpad and capture subprocess output with `errors='replace'`. Full note in §4.
- **AgendaCenter (CivicPlus/CivicEngage)** listings are the AJAX
  `UpdateCategoryList?catID=<n>&year=<Y>` endpoint (per body × year); docs resolve to
  `ViewFile/{Agenda,Minutes,ArchivedMinutes,AgendaPacket}/<opaque-id>`. Some sites are
  **current-cycle-only** (no packet back-catalog → Wayback is the only lead). Recipe in §1.
- **Wayback is a first-class recovery tool** for any CMS-migrated city page (disclosures,
  general plans, old ordinance lists) — `WebFetch` can't reach it; use `polite_fetch.py`.
- **A concurrent audit/remediation session may be writing the same city** — run the
  concurrency pre-flight; a net *decrease* in an existing layer during your run is a red flag
  to investigate (it may be a legitimate dedup — verify against a backup before concluding).
- Mayor voting rules vary (6-member Utah cities: mayor votes only to break ties) — don't
  let a packet/ordinance linkage assume the mayor is a normal voter.
