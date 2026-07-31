# PRIVACY — what personal information this repository contains, and why

Everything here derives from **Utah public records** (Utah GRAMA, Utah Code 63G-2):
meeting minutes, public-comment records, election canvasses, and campaign-finance
disclosures that Utah governments published themselves. Names appear because civic
participation is public in Utah — who addressed a council, who donated to a candidate,
who voted on a motion.

Aggregating scattered public PDFs into one indexable repository does change
discoverability, and we treat that as a real design decision rather than a default. The
policy (decided 2026-07-31):

## Verbatim reproductions stay as published

Minutes markdown, ordinance text, and the `campaign_finance/text/` extraction layer are
**faithful reproductions of government-published documents** and are not edited — that
includes contact details a clerk printed in minutes and donor street addresses on the
face of campaign-finance filings. Editing them would break the repository's verbatim-text
guarantee (see METHODS.md, honesty rule 2). Note the deliberate asymmetry: the
*structured* campaign-finance tables store donor city/state only, never street addresses;
the verbatim text layer reproduces the filing as filed.

## Constructed aggregation layers are contact-redacted

The public-comment CSVs (`*/public_comments/all_comments_clean.csv` and derived copies)
are **this project's construction**, not a government document. In the published form,
**email addresses and phone numbers are redacted** (replaced with `[redacted-email]` /
`[redacted-phone]`; redaction implemented by `scripts/redact_comments.py`, which must be
re-run after any comment-layer rebuild). Commenter **names, and street addresses given to
establish residency, are retained** — they are the civically meaningful content of a
public comment. The unredacted source PDFs remain local-only (not in the published
repository) and re-fetchable from each government's own channel.

## Corrections and takedown

If you believe a record here misattributes something to you, reproduces sealed/withdrawn
material, or creates a concrete safety concern, contact **tysonwelsh@gmail.com** with the
file path and the issue. Corrections that contradict the source document go through the
repository's documented override mechanism (with the evidence cited); the underlying
government record itself can only be corrected by the government that holds it.

## What this repository does NOT contain

No non-public records, no GRAMA-restricted material, no sealed filings, no records
obtained by request rather than from public channels (the one channel class pending —
GRAMA requests for unpublished minutes — would enter through the same provenance
discipline if ever used). Election results suppressed by a county for privacy (e.g. small
towns) stay suppressed here.
