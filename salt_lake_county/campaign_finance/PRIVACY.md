# PRIVACY — Salt Lake County campaign_finance/

Policy for this dataset, consistent with the repo PRIVACY contract (2026-07-31): **verbatim
source documents ship as-is; constructed/structured layers carry geography only, never street
addresses.**

## What ships verbatim
- **`raw/`** — the acquired PDFs exactly as published. Both channels already serve **redacted
  public copies**: the EasyVote `viewfinalredactedpdf` endpoint returns the address-redacted
  public PDF, and the legacy clerk PDFs are the copies the County Clerk published. No further
  redaction is applied (and none is needed — these are the public record).
- **`text/`** — text sidecars of those same public PDFs (born-digital `pdftotext`; scans via the
  planned vision follow-up). Verbatim, not redacted (the source is already the public copy).

## What the structured layer carries
- **`contributions.csv` / `expenditures.csv`** are built from the EasyVote **itemized advanced-
  search JSON**, which itself exposes **no street addresses** — only contributor/payee name (or
  organization), date, and amount. Accordingly these CSVs carry `donor_city` / `donor_state` /
  `donor_district` **blank** (the API provides none) and **never** a street address. This is
  stricter than the SCHEMA floor (city/state allowed) purely because the source omits them.
- No donor identity is fabricated: a filing that named no donor yields a **blank `donor_raw`** row
  flagged `needs_review=1` (donor_type `unknown`) — never a promoted geography or guessed name.
