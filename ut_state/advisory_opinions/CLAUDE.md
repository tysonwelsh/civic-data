# ut_state / advisory_opinions — Utah Property Rights Ombudsman advisory opinions

The full numbered set of **Advisory Opinions of the Office of the Property Rights
Ombudsman (OPRO)**, 2006 → present. Each opinion is a written legal analysis (under Utah
Code **§ 13-43-205**) predicting how a court would decide a specific Utah land-use dispute
between a property owner/developer and a city or county. **These interpret LUDMA — the
Municipal/County Land Use, Development, and Management Act that every city and county in
this repo administers** — so they are the highest cross-link value layer to the local vote
record: an opinion naming a repo entity is the state's read on a dispute that same council
or PC handled.

## Files

- `raw/AO-<NNN>.pdf` — the opinion PDF (zero-padded to 3 digits by opinion number).
- `text/AO-<NNN>.txt` — `pdftotext -layout` sidecar (the searchable text).
- `index.csv` — one row per opinion (schema below).
- `SOURCES.md` — provenance, retrieval method, the byte-verified source ledger, and the
  honest gap record.

## index.csv schema

`opinion_no, date, issued_verbatim, title, jurisdiction, topics, repo_entities_matched,
path, text_path, source_host, source_url, doc_class`

- `opinion_no` — the OPRO global number (verified from the PDF body's "Advisory Opinion
  #NNN" line, not just the filename).
- `date` / `issued_verbatim` — ISO date + the verbatim "Issued:" string from the PDF.
- `title` — the opinion's **Parties** line (e.g. "Ivory Development and Taylorsville City").
- `jurisdiction` — city/county/town named as the government party, parsed from the Parties
  line (blank = not cleanly parsed, never invented).
- `topics` — the opinion's own "TOPIC CATEGORIES" (verbatim OPRO topic codes).
- `repo_entities_matched` — `;`-joined repo entity slugs whose name appears in the opinion
  text (word-boundary, case-insensitive). **A simple name match** — a convenience index,
  not a verified holding. Short single-word city names (Alta, Sandy, Draper, Murray,
  Holladay…) can collide with surnames/common words; confirm against the text before
  quoting. Entities appearing in the Parties line are sorted first.
- `source_host` — `propertyrights.utah.gov` or `commerce.utah.gov` (the two hosts OPRO
  publishes on).
- `source_url` — the exact original PDF URL (fetched via the Wayback Machine — see below).
- `doc_class` = `advisory_opinion` (per SCHEMA_SPEC §9 doc-class convention).

## Retrieval (IMPORTANT — Cloudflare)

Both `propertyrights.utah.gov` and `commerce.utah.gov` sit behind **Cloudflare**; the
index pages AND the wp-content PDFs return **403 to every non-browser fetch** (curl,
WebFetch, the WordPress REST API, the origin IP). The opinion set was therefore
**enumerated and retrieved through the Internet Archive Wayback Machine**: the CDX API
listed every archived opinion PDF (both hosts), and each PDF was pulled from its
`web.archive.org/web/<ts>id_/<original-url>` capture. The `source_url` in `index.csv` is
the **original** OPRO URL (the durable citation); the Wayback capture is the fetch channel,
documented in `SOURCES.md`. To refresh, re-run the CDX enumeration; a live pull needs a
real browser (Cloudflare).

## Honest gaps

See `SOURCES.md` for the exact ledger of numbered opinions that could not be recovered
(no Wayback capture on either host) and the note on OPRO's newer `Advisory-Opinion-2025-NN`
year-sequential naming. Gaps in the numbering are findings, not errors — some opinion
numbers may never have been issued/published. Nothing was fabricated to fill them.
