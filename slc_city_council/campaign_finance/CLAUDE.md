# slc_city_council/campaign_finance — how to use this dataset

Municipal **campaign-finance disclosures** for Salt Lake City Council (7 districts) + Mayor
candidates. Additive layer completing the **elections → members → votes** chain (who funded
the people casting the votes). Built by the `expand-city-sources` skill (Source 6).
As-of 2026-07-05.

> **2026-08-02 — read `RECON_2026-08-02.md` first.** An adversarial channel re-hunt
> **falsified** the "no PDFs exist anywhere / no pre-portal filings online" determination.
> A **2003 PDF tranche is now in `raw/recorder_2003/`** (8 filings, itemized donors +
> expenditures, Mayor + Council D1/D2/D4/D5/D6), plus a captured live **portal 503 page that
> embeds a 38-row candidate/balance table**. the STRUCTURED LAYER IS NOW BUILT
> (2026-08-02): `build_finance.py` parses the 8 filings into filing_totals (8) /
> contributions (222) / expenditures (162), every side reconciled to a filer-stated
> total or honestly unknown, every row geometry-anchored (`p:l:c` spans;
> make_snippet.py works — sidecars in text/recorder_2003/); index.csv carries the 8
> filings; validate_finance PASS 0/0.

## What this is (and is NOT)

- **IS:** a filing-level index + retained source documents. For **2019+** SLC self-hosts in a
  **JSON WebAPI** (no PDFs at that grain — see AVAILABILITY.md); for **2003** the Recorder
  published per-candidate PDFs, now recovered. `text/…` holds a human-readable sidecar per
  document; `index.csv` has one row per **(election, candidate)** filing.
- **IS NOT (for the 2019+ API era):** structured contribution/expenditure tables — the 2003
  tranche IS structured (see the banner above); this paragraph governs the future API
  harvest, whose itemized donor/vendor arrays
  live *inside* the retained `raw/contributions_*.json` / `raw/expenditures_*.json` documents
  but are deliberately **not** parsed into row-level CSVs here — that is a separate planned
  layer (`scripts/campaign_finance/` toolkit). `index.csv` summarizes them only as counts +
  stated totals.

## Source

SLC Campaign Finance Reporting System (City Recorder's Office), an Angular SPA over a .NET
WebAPI. Base: `https://dotnet.slcgov.com/Attorneys/CampaignFinance_Public/api/CampaignFinanceAPI/`.
Full endpoint map and the reverse-engineering path are in **AVAILABILITY.md** — read it first.

## Files

- `raw/` — retained source documents. `_fetch_log.jsonl` = provenance for **every** file
  (url, original_url, wayback_timestamp, status, bytes, sha256, retrieved_utc, channel).
  - `raw/recorder_2003/` — **8 recovered 2003 filings** (PDF) + `_index_feb_fin_disc.htm`,
    the Recorder's index page. **Real filings** with itemized contributions/expenditures.
  - `raw/portal_snapshot/` — the live **503** page (2026-08-02), which embeds the
    38-row candidate/office/**balance** table. A point-in-time snapshot, **not a filing**.
  - `raw/recorder_limitations/` — 12 scanned "Public Notice" declarations to voluntarily
    limit contributions/expenditures (2003/2005/2007). **Not filings**; no text layer
    (vision/OCR needed).
  - `raw/recorder_open_committees/` — live roster of 22 open Personal Campaign Committees
    as of 2019-05-03. **Not a filing.**
  - *(planned, when the API returns)* verbatim JSON payloads per candidate:
    `elections.json`, `candidates_e<EID>.json`, `periods_e<EID>.json`,
    `summary_/financial_/contributions_/expenditures_e<EID>_c<CID>.json`.
- `text/` — human-readable sidecar per document (`recorder_2003/`,
  `recorder_open_committees/`; the API era will use `e<EID>_c<CID>.txt`).
- `index.csv` — filing index. §9 contract cols (`date, candidate, office, election_year,
  filing_type, reporting_period, title, source_url, retrieved_date, format, extraction_method,
  path`) PLUS `district, candidate_id, election_id, status, stated_total_*`, itemized counts,
  and the join columns `matched_election_candidate, join_confidence`.
- `harvest.py` — pulls filings from the WebAPI (GET-only, ≥3s, browser UA, logged). Idempotent.
- `build_index.py` — regenerates `text/` + `index.csv` from `raw/`. Idempotent.
- `AVAILABILITY.md` — every host tried, portal structure, honest gaps, outage record.

## Rebuild

```
python3 harvest.py        # → raw/*.json  (needs the .NET backend up; 503 during maintenance)
python3 build_index.py    # → text/*.txt + index.csv
```

## Linkage to the rest of the repo

`index.csv` joins each filing candidate to `election_results/slc_results_by_candidate.csv`
by **candidate name + election_year + district** (names normalized: election names are
UPPER-CASE with `(NP)` suffixes; portal names are mixed-case). `join_confidence` ∈
`exact` / `high` / `medium` / `none`. To connect a donor profile to a member's *votes*,
go candidate → `election_results` winner → `db/` `v_member_record` / `all_votes.csv`.

## Cardinal rules honored

- **Additive only.** Nothing in `election_results/` or any parent doc was edited. If a
  filing surfaces a candidate/primary the election records don't list, that is FLAGGED
  (join_confidence=none in index.csv + a note here), never patched into the election data.
- **Never fabricate.** Values are verbatim from the API. Blank = the API returned none.
- **Retain raw.** Every JSON payload is kept byte-for-byte with a provenance log line.

## Known limitations

- **2019+ portal is data-only** (no PDF/scan of a signed form exists at that grain — the
  JSON *is* the record), and its public API has returned **503** since ≥2026-07-05.
- **2003:** 8 filings recovered; 2 more (`David_Spatafore`, `J_Michael_Clara`) are archived
  but currently blocked by an Internet-Archive donation interstitial — **retry**;
  `Dale_Lambert` was never captured (permanent gap).
- **2005–2017: honest gap.** These cycles *were* published (in the `CandidateReporting`
  app), but its result pages were POST-only and never archived, and the app now 500s.
  Recoverable only from the city.
- The recovered 2003 documents are **not yet parsed** into structured tables and are **not
  in `index.csv`** — that is the coordinator's structured-layer build.
- See the HARVEST STATUS block in AVAILABILITY.md for any acquisition-time outage and the
  actual per-year/candidate counts once harvested.
