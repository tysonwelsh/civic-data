# PRIVACY — this dataset

Module-level supplement to the repository policy in `/PRIVACY.md` (2026-07-31). Nothing
here overrides it; this records what the Weber County campaign-finance documents actually
contain and what was done about it.

## Everything here is a Utah public record

Weber County candidates for county office file campaign contribution & expenditure reports
with the **County Clerk/Auditor** under **Utah Code 17-16-6.5** and the county's own
campaign-finance ordinance, and the county **publishes them itself** on
`weberelections.gov`. Every byte in `raw/` was downloaded from a government channel with
no authentication, no request, and no scraping around an access control. Provenance for
every file — URL, HTTP status, byte count, sha256, fetch timestamp — is in the per-channel
`raw/<channel>/_fetch_log.jsonl`.

## `raw/` and `text/` are verbatim — including donor and candidate addresses

Per repository policy, the **verbatim layers are faithful reproductions and are not
edited**. On these forms that means:

- **Candidate home addresses and phone numbers** appear on the face of most filings (the
  form has `Address (Street) (City) (Zip Code)` and two phone lines).
- **Donor names, and on the Form A schedules donor addresses**, appear as the filer wrote
  them.
- The **2026 born-digital e-filings** (Polimorphic "Submit Campaign Financial Disclosure")
  additionally carry the submitter's **email address** in machine-readable text.

These are reproduced as published. Redacting them would break the verbatim-text guarantee
and would also misrepresent the source, which is the point of retaining it.

**The county itself redacts some of this, and that redaction is preserved.** In the 2024
archive PDF the county blacked out candidate street addresses before publishing (visible
as black bars on the rendered pages). We do not attempt to recover anything behind a
redaction the government applied, and the OCR sidecar simply contains nothing there.

## No structured layer, so no structured-layer exposure

The repository's deliberate asymmetry — *structured campaign-finance tables store donor
**city/state only**, never street addresses* — does not bite here because **no structured
layer was built** (see `AVAILABILITY.md` §7: the amounts and donor names are handwritten
and no shared parser family reads them without fabricating values). If a structured layer
is added later — the obvious candidate is a `weber_polimorphic` family for the five 2026
born-digital e-filings — it **must** follow that rule: `donor_city` / `donor_state` only,
never `donor_street`, and never the submitter's email.

## What this dataset does NOT contain

No school-board dataset (see `AVAILABILITY.md` §2 — school-board filings appear only as
inventory of the county's own compilation documents). No conflict-of-interest statements.
No municipal (city) filings — those belong to each city's own layer. No records obtained
by request rather than from a public channel. Nothing behind a login.

## Corrections and takedown

Same as the repository policy: **tysonwelsh@gmail.com** with the file path and the issue.
A correction that contradicts the source document goes through a documented override with
the evidence cited; the underlying filing itself can only be corrected by the Weber County
Clerk/Auditor, who holds it.
