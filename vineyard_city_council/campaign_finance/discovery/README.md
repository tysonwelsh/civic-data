# Discovery artifacts (reproducibility)

- `cdx_documentcenter_finance.json` — Wayback CDX enumeration of
  `vineyardutah.org/DocumentCenter/*` filtered to finance/disclosure/statement/report
  (original, timestamp, statuscode, mimetype, digest). The source of every archived filing.
- `fetch_plan.csv` — per-View-id fetch plan derived from the CDX (year, view, name, best
  timestamp, statuscode, mime, original url). Non-filing rows (audit/water/permit reports,
  pledge/COI forms, blank templates, info sheets) were excluded before fetching.

Hosts checked with no filings: easyvotecampaignfinance.com (no Vineyard tenant, DNS fail),
disclosures.utah.gov (Municipal path does not exist). See ../AVAILABILITY.md.
