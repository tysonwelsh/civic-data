# slc_city_council/campaign_finance — how to use this dataset

Municipal **campaign-finance disclosures** for Salt Lake City Council (7 districts) + Mayor
candidates. Additive layer completing the **elections → members → votes** chain (who funded
the people casting the votes). Built by the `expand-city-sources` skill (Source 6).
As-of 2026-07-05.

## What this is (and is NOT)

- **IS:** a filing-level index + retained source documents. SLC self-hosts its filings in a
  **JSON WebAPI** (there are no PDFs — see AVAILABILITY.md). Each `raw/*.json` payload is the
  retained source document; `text/<id>.txt` is its human-readable sidecar; `index.csv` has
  one row per **(election, candidate)** filing.
- **IS NOT:** structured contribution/expenditure tables. The itemized donor/vendor arrays
  live *inside* the retained `raw/contributions_*.json` / `raw/expenditures_*.json` documents
  but are deliberately **not** parsed into row-level CSVs here — that is a separate planned
  layer (`scripts/campaign_finance/` toolkit). `index.csv` summarizes them only as counts +
  stated totals.

## Source

SLC Campaign Finance Reporting System (City Recorder's Office), an Angular SPA over a .NET
WebAPI. Base: `https://dotnet.slcgov.com/Attorneys/CampaignFinance_Public/api/CampaignFinanceAPI/`.
Full endpoint map and the reverse-engineering path are in **AVAILABILITY.md** — read it first.

## Files

- `raw/` — verbatim JSON payloads, one set per candidate:
  `elections.json`, `candidates_e<EID>.json`, `periods_e<EID>.json`, and per candidate
  `summary_e<EID>_c<CID>.json`, `financial_…`, `contributions_…`, `expenditures_…`.
  `_fetch_log.jsonl` = provenance (url, status, sha256, bytes, retrieved_utc).
- `text/e<EID>_c<CID>.txt` — sidecar per filing (candidate, office, district, stated totals,
  itemized counts, source URL). Source-6 requires a text sidecar for every filing.
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

- Portal is **data-only** (no PDF/scan of a signed form exists to retain — the JSON *is* the
  record). `format=json` for every row; `extraction_method` notes the API + sidecar render.
- Pre-2019 cycles: filings not published online (results exist back to 2007). Honest gap.
- See the HARVEST STATUS block in AVAILABILITY.md for any acquisition-time outage and the
  actual per-year/candidate counts once harvested.
