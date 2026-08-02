# PRIVACY — washington_county/campaign_finance

Policy for this dataset, consistent with the repo's `PRIVACY.md` (2026-07-31) and
`GOTCHAS.md`: **verbatim primary sources are never redacted; constructed layers are.**

## What this dataset holds

| Layer | Treatment |
|---|---|
| `raw/` | **VERBATIM.** The county's published PDFs / `.xls` workbooks, byte-for-byte. Never redacted, never edited — they are the primary source and the only thing a disputed figure can be checked against. |
| `text/` | **VERBATIM.** Machine transcription (OCR / `pdftotext` / cell dump) of `raw/`. Not redacted — a redacted transcript could not be reconciled against the file it transcribes. |
| `portal_stated_totals.csv` | **VERBATIM** transcription of dollar totals the county printed on its own public web page. Contains candidate names and amounts only — no donor identities. |
| `index.csv` | Constructed catalogue: **candidates and offices only.** Carries no donor name, no address, no amount. |
| `excluded_school_board.csv` | Constructed ledger of out-of-scope files: candidate/office/URL/hash only. |

## Donor personal data — where it is, and the rule for any layer built on top

Utah's county campaign-finance form requires a donor's **name and street address** for
contributions over the reporting threshold, and the county publishes them. They are
therefore present, in the clear, in `raw/` and `text/` — most explicitly in the
**2014–2015 `.xls` generation**, whose contribution sheets carry a full mailing address on
the line beneath each donor (e.g. `145 N Mall Dr Unit 1, St George, UT 84790`).

**This is public record as published by the county, and this dataset does not alter it.**

**The binding rule for any DERIVED structured layer** (a future
`contributions.csv` / `expenditures.csv` built to `scripts/campaign_finance/SCHEMA.md`):

> **Structured donor rows carry `donor_city` and `donor_state` ONLY.**
> No street address, no unit number, no ZIP, no phone. The SCHEMA.md donor row already
> models exactly these fields (`donor_city`, `donor_state`, `donor_district`) — populate
> them from the printed address and **discard the street line**; never promote a street
> address into `donor_raw`.

The same rule applies to the candidate's own contact block (home address and home/business
telephone are printed on the cover of the 2006–2025 county form): it stays in `raw`/`text`
as published and is **never** lifted into a constructed CSV.

## Not collected
No attempt is made to link donors to voter registration, to resolve donor identity across
entities, or to geocode a donor address. There is no cross-entity donor identity layer in
this repo (`SCHEMA.md` §5: "no cross-city donor identity resolution in v1").
