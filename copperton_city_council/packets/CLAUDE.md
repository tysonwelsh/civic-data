# packets/ — Town of Copperton agenda packets & supporting documents

Additive `expand-city-sources` dataset (source type 1). The **Supporting Documents / packet behind
each Council and Planning Commission meeting** — agendas, staff reports, ordinance/resolution
drafts, budgets, studies, contracts, hearing notices — keyed by `date` + `body` so it joins the
minutes/votes layers. **Read `AVAILABILITY.md` first** for coverage, the two-portal split, and the
honest gaps. Canonical schema: `SCHEMA_SPEC.md` §9.

## What's here

```
raw/<date>/…            originals verbatim, one folder per meeting date
  _fetch_log.jsonl      per-date polite_fetch provenance (url, status, bytes, sha256, retrieved_utc)
raw/_fetch_log.jsonl    consolidated log (all dates, incl. the 18 purged 404s)
raw/_pages/             cached listing HTML the harvest parsed (GoDaddy year pages + PMN notice lists)
text/<stem>.txt         pdftotext -layout sidecars for born-digital PDFs (feeds cities.db fts_packet)
text/_extraction_log.csv  per-file extraction outcome (extracted / image_only / skipped)
index.csv               the dataset index — §9 packets contract + city-extra + doc_class columns
classify_attachments.py doc_class classifier (deterministic, rerunnable — see below)
AVAILABILITY.md         coverage, source split, gaps, as-of date
build_packets_index_copperton.py   the (idempotent) harvest→fetch→index builder
```

## index.csv columns

`date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,extraction_method,path`
(the exact §9 packets contract, in order) **+ city extras** `source,pmn_body,notice_url,bytes,sha256`
**+ the 2026-07-16 primary-docs extension columns** `doc_class,fetch_status,text_path,text_chars`
(`sha256` — one of the pilot's standard extension columns — already existed as a city extra and is reused).

- **`doc_class`** (in-scope rows only): `staff_report` | `member_memo` | `plan_amendment` |
  `development_agreement` | blank = **honestly unclassified** (out of scope / corpus bulk — never
  force-bucketed). Assigned by `classify_attachments.py`. See the layer section below.
- **`fetch_status`** (classified rows only): `ok` (usable text) | `needs_ocr` (scanned, no text) |
  blank (not classified). Copperton: all 6 classified rows are `ok` (no scanned classified rows).
- **`text_path`** / **`text_chars`**: the extracted-text sidecar (dataset-relative) + its char count,
  for classified rows. The binaries are already STORED under `raw/` (this is a stored dataset, so
  there is no fetch→discard step — `sha256`/`bytes` describe the on-disk raw).

- **`path`** is dataset-relative including `raw/` (e.g. `raw/2025-07-16/…pdf`) — the convention the
  validator + sources index expect.
- **`body`** ∈ `Council` | `PlanningCommission` (matches the vote/minutes layers).
- **`packet_kind`** ∈ `full_packet` (a combined agenda-with-supporting / Meeting Packet / Agenda
  Packet bundle) · `agenda_packet` (a bare agenda, kept only when no same-day packet supersedes it) ·
  `supporting_docs` (a standalone supporting-document set, item handout, ordinance/resolution draft,
  budget, study, hearing notice) · `staff_report` (an individual staff report / item analysis).
- **`meeting_type`** — `Special` / `Work` / `PublicHearing` when the source title says so, else blank.
- **`format`** — `text` (born-digital; `.pdf` sidecar in `text/`, or a `.docx`/`.doc` retained raw)
  or `scanned` (7 image-only PDFs — `extraction_method` says vision/OCR is needed to read them).
- **`source`** ∈ `pmn` | `godaddy`; **`pmn_body`** = `5831` (Council) / `1560` (PC) / blank (GoDaddy);
  **`notice_url`** = the PMN notice page (blank for GoDaddy).

## The two-portal split (why + how) — this is the load-bearing design decision

Copperton publishes packets on two portals with overlapping years; to avoid double-counting the same
meeting, each meeting is drawn from exactly one:

- **Council ≤ 2023-12-31 → PMN body 5831** (metro-township era). PMN posted per-meeting
  `[Public Information Handout]`/`[Other]` attachments with clean per-meeting date labels, and its
  2023 coverage is a superset of the GoDaddy 2023 page.
- **Council ≥ 2024-01-01 → GoDaddy** (`copperton.utah.gov/<YEAR>-agendas...`, docs on
  `img1.wsimg.com`). The town era packages a meeting's whole packet as one combined
  "Agenda with Supporting Documents" / "Meeting Packet" PDF — the truest "packet" artifact.
- **PC (all dates) → PMN body 1560.** The PC has no packets on the GoDaddy site.

**Fetch mechanics.** The GoDaddy *listing* pages fail plain `requests`/WebFetch (the
`copperton.utah.gov` GoDaddy site serves a `secureserversites.net` cert — TLS hostname mismatch), so
listings are fetched with **`curl -k` + a browser UA** and the doc anchors read from the rendered DOM
(opaque `img1.wsimg.com/.../downloads/<guid>/<file>.pdf?ver=<n>` GUIDs — **harvested, never
guessed**). The *documents* on `img1.wsimg.com` and `www.utah.gov/pmn` have valid certs and download
through `scripts/polite_fetch.py` (GET-only, ≥1s/host, logged). PMN notice lists are the cumulative
`.../list/notices.html?id=<body>&page=N` GET (pages 1/20/48 unioned to reach the oldest rows).

## Primary-document text layer (doc_class, PRIMARY_DOCS_ROLLOUT 2026-07-16)

Classify-in-place (Bucket A-lite): the packets are already STORED with `text/` sidecars, so this
step only added a `doc_class` label + linked the existing text — **no fetching**. Only the
`supporting_docs` + `staff_report` packet_kind rows (210 of 305) are scanned; the
`full_packet`/`agenda_packet` containers (95) are skipped (their whole-meeting text already feeds
`fts_packet`; none names a specific in-scope primary doc). ~800-pop town — **small honest counts are
CORRECT.**

| doc_class | rows | ok | needs_ocr | what it is |
|---|---|---|---|---|
| staff_report | 6 | 6 | 0 | MSD land-use staff reports (rezone / Title 18-19 code-compliance / parking / landscaping ordinance amendments) — the "…Staff Report" / "REZONE SUMMARY AND RECOMMENDATION" / "Ordinance Summary and Recommendation" MSD template (Meeting/Public Body + File #/OAM|REZ case key + Planner/Recommendation) |
| member_memo | 0 | — | — | **empty** — the ~4 councilmember/memo title hits are all administrative (board-appointment resolutions, an interlocal redline, a park proposal, a subdivision redline), none a member-authored proposal memo |
| plan_amendment | 0 | — | — | **empty** — see the Annexation Policy Plan boundary note |
| development_agreement | 0 | — | — | **empty** — the ~15 "agreement"/annex title hits are all interlocal / franchise / annexation instruments; no private land-development agreement exists (correct for an ~800-pop town) |

The six `staff_report` docs (all born-digital `ok`): 2023-04-19 (Title 18/19 repeal-replace, docx →
textutil sidecar), 2023-07-19 (REZ2023-000840 rezone C-2→NMU), 2024-09-10 (OAM2024-001253 SB174/HB476
subdivision compliance), 2025-07-02 (OAM2025-001422 parking revisions), 2025-12-03 (OAM2025-001540
HB368 bonding), 2026-06-03 (OAM2026-001628 landscaping). Three join a recorded vote (2023-07-19
rezone ordinance; **2024-09-10 PC "To recommend file #OAM2024-0001253…"** — exact case-key join;
2023-04-19 land-use steering-committee actions); the 2025-26 PC reports have no extracted vote (the PC
is tally-only / cancels most meetings — an honest gap, not a miss).

- **Classifier**: `classify_attachments.py` — deterministic title-token + sidecar-head rules
  (`python3 classify_attachments.py`; `--dry-run` reports counts, writes nothing). staff_report =
  a "staff report / summary and recommendation" title candidate **confirmed** by the MSD template +
  a land-use case key/term in the document text. The one classified `.docx` (no pdftotext sidecar)
  gets a `textutil`-converted sidecar on first run (`extraction_method="textutil (docx->txt)"`);
  unclassified office-docs are **never** bulk-converted. Rerunnable + idempotent.
- **Quality gates (met)**: precision — `staff_report` whole-class verified (n=6, MSD template +
  land-use case key in every text) = 100%; the three empty classes have no false positives. Recall —
  exhaustive sweep of all 210 in-scope sidecar heads + office-doc titles + OAM/REZ/CUP/VAR/RWD case
  keys found **0** additional land-use staff reports (0 est. miss).
- **Boundary decisions (documented, not bugs)**:
  - The 2025-08-20 `packet_kind=staff_report` rows (UFA Q2 report, EOC training, Hazard Mitigation
    Plan annex) are OPERATIONAL reports, not land-use staff reports → blank. `packet_kind` ≠ `doc_class`.
  - Draft Title 18/19 subdivision/zoning CODE-text amendment drafts and the 2022 "Phase 1 Package"
    staff cover MEMO are land-use-adjacent but are code drafts / a non-"staff report" staff memo →
    blank (Sandy precedent; enacted ordinances live in `ordinances/`). Their text still feeds `fts_packet`.
  - The DRAFT **Copperton Annexation Policy Plan** (2022) is a distinct STATUTORY land-use policy
    plan (Utah Code 10-2-401.5), NOT a general-plan amendment and NOT a land-use-map amendment exhibit,
    so `plan_amendment` is left **empty** to keep the class precise. The plan text remains
    FTS-searchable via the full pdftotext sidecar layer (it is not lost, just not class-tagged).

## Rebuild (idempotent)

```
python3 build_packets_index_copperton.py --harvest   # parse cached raw/_pages/ -> _candidates.csv
python3 build_packets_index_copperton.py --fetch      # download survivors -> raw/<date>/ (skips existing)
python3 build_packets_index_copperton.py --index      # -> index.csv (reads text/_extraction_log.csv)
python3 /Users/tysonwelsh/civic-data/scripts/extract_packet_text.py copperton   # text/ sidecars
python3 build_packets_index_copperton.py --index      # re-run to finalize format/extraction_method
python3 classify_attachments.py                       # doc_class + text_path/text_chars/fetch_status
```

⚠ Run `classify_attachments.py` **last** — it appends the `doc_class`/`fetch_status`/`text_path`/
`text_chars` columns and (re)writes them; re-running `--index` would drop them, so re-classify after
any index rebuild.

`--harvest` re-fetches the listing pages only if `raw/_pages/` is empty (delete it to force a fresh
pull on a refresh). Classification/exclusion rules live at the top of the script. Do NOT hand-edit
`index.csv` or files under `raw/`/`text/` — regenerate.

## Exclusions (recorded so they're not mistaken for scraper misses)

minutes & minute-attachments (they're the minutes datasets) · audio · PC cancellation/no-meeting/
annual-schedule notices (PC cancels most meetings — quantified in `AVAILABILITY.md`) · re-posted
prior-meeting minutes attached to a later notice for approval · branding/images · undated GoDaddy
loose docs (adopted ordinance/resolution/budget texts with no meeting date — future `ordinances/` /
`housing_plans/` datasets).

## Known limits

- **Packet floor is effectively 2019.** 2017–2018 packet/handout attachments are **404-purged** on
  PMN (18 logged failed fetches) even though the town data floor is 2017 and 2018-07+ *minutes*
  survived — PMN retains minutes longer than handouts. Not a harvest miss; the notices exist, the
  packet PDFs are gone.
- **7 scanned PDFs** need vision/OCR (no text sidecar); `.docx`/`.doc` packets are retained raw with
  no PDF sidecar (`format=text`, `extraction_method="none (docx raw retained)"`).
- **Duplicate source docs are honest.** The same budget/fee-schedule is re-attached across several
  council notices (the screener's `duplicate_bodies` flag) — that reflects the town's own postings,
  not an extraction bug.
