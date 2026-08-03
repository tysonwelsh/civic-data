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

## The vision-itemized clerk-legacy rows (wave B2, 2026-08-02)

Unlike the EasyVote API rows, these are read off a page that **does** print a "Complete Mailing
Address" column. The rule applied at READ TIME, by every transcriber, was: **city and state only;
the street line and any PO box are discarded as they are read and are never written into a
record, a note, a cache or a CSV.** Three different blanks are distinguished in the row note,
because they are three different facts: the county **redacted** the block, the **filer left it
empty**, or the form has **no address column at all** (the clerk's system printouts and several
spreadsheet attachments).

**⚠ The county's own redaction is imperfect on some published legacy PDFs, and that is a finding
about `slco.org`, not about this dataset.** Wave B2 encountered, and deliberately did not
transcribe, at least these classes:
- a filing whose Schedule A address column is white-boxed, but whose **same scanned page carries
  an unredacted highlighted photocopy of the same table lower down**, with every street address
  legible (`08_joehatch_jan31.pdf`, June 2006 Hatch filing);
- files named `*_Redacted.pdf` that are **not redacted at all** — full street addresses in the
  clear (`SGill_11_YearEnd_DistAttny_Redacted.pdf`; the `_Redacted` suffix is a portal label, and
  GOTCHAS' "portal labels lie" applies to redaction status too);
- **white boxes that under-cover**, leaving a street address or a sliver of one visible
  (`Recanzone_P_12_…_Redacted.pdf` p5 row 1; `Petersen_S_…` p3 row 20).

In every case the structured layer carries city/state or an honest blank. **Nothing was
extracted from an imperfectly-redacted block.** The raw PDFs still ship verbatim — they are the
copies the County Clerk published, and re-redacting a public record is not this repo's call —
but a consumer republishing `raw/clerk_legacy/` should know the county's redaction is not
uniform.
