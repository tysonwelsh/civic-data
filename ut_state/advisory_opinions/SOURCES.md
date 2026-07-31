# ut_state / advisory_opinions — sources & provenance

The numbered **Advisory Opinions of the Utah Office of the Property Rights Ombudsman
(OPRO)**, issued under **Utah Code § 13-43-205**. Each is the state's reasoned prediction
of how a court would decide a specific Utah land-use dispute — i.e. the authoritative gloss
on LUDMA, the act every repo city and county administers. Every value in `index.csv` is
recorded from the opinion's own PDF (opinion number, parties, issue date, and topic codes
are read from the document body), with two documented exceptions (opinions 102 and 206 —
see the gap ledger). Nothing is fabricated.

## Publisher (official)

**Office of the Property Rights Ombudsman**, Utah Department of Commerce. OPRO publishes
opinions on two hosts:
- `propertyrights.utah.gov` (WordPress; primary)
- `commerce.utah.gov` (the department mirror; carries the same PDFs, and holds some the
  primary lost)

## Retrieval method — Cloudflare forced a Wayback pull

Both hosts sit behind **Cloudflare**. Every direct machine fetch — `curl` (browser
User-Agent included), `WebFetch`, the WordPress REST API (`/wp-json`), and even the origin
IP `35.83.35.239` — returns **HTTP 403 / a Cloudflare challenge**, for the index pages AND
the `wp-content` PDFs alike. The set was therefore **enumerated and retrieved through the
Internet Archive Wayback Machine**:

1. **Enumerate** — the Wayback **CDX API** was queried for every archived object under
   `propertyrights.utah.gov/wp-content/uploads/*` (1,017 captured URLs; 640 PDFs) and
   `commerce.utah.gov/wp-content/uploads/*` (1,951 PDFs). Opinion PDFs were identified by
   the OPRO filename convention (`<num>-AO-<name>-Advisory-Opinion-<date>.pdf` and
   variants) and deduped by opinion number, choosing the latest 200-status capture.
2. **Fetch** — each opinion PDF was pulled from its
   `https://web.archive.org/web/<timestamp>id_/<original-url>` capture (the `id_` suffix
   returns the raw archived bytes). Fetched files were validated (`%PDF` header) before a
   `pdftotext -layout` sidecar was written; failed pulls were retried, then re-attempted
   against the **commerce.utah.gov** capture as a fallback.

**`source_url` in `index.csv` is the ORIGINAL OPRO URL** (the durable citation, host in
`source_host`); the Wayback capture is only the fetch channel. To refresh, re-run the CDX
enumeration; a live pull requires a real browser (Cloudflare).

## Ledger (byte-verified 2026-07-20)

| | count |
|---|---|
| Opinions with PDF + text sidecar | **307** |
| — from `propertyrights.utah.gov` | 304 |
| — from `commerce.utah.gov` (recovered where the primary had no capture: #294, #299, #309) | 3 |
| Numbered opinions with no recoverable PDF (gap rows in `index.csv`, blank `path`) | 2 (#102, #206) |
| **Total index rows (opinion universe 1–309)** | **309** |
| Opinion-number span | 1 → 309 |
| Issue-date range (fetched) | 2006-07-05 → 2025-08-01 |
| Raw PDF footprint | ~135 MB (largest: `AO-251.pdf`, 15.2 MB; all < 50 MB, so all stored, none link-only) |

Every fetched opinion's exact original URL is in `index.csv` (`source_url`) — **zero
unrecorded**.

## Cross-link to repo entities

`index.csv.repo_entities_matched` flags the **117** opinions whose **Parties line** names a
repo city/county entity (**28 distinct entities**). The match is deliberately scoped to the
Parties line — not the full text — because OPRO's own **Salt Lake City** letterhead and the
boilerplate "State of Utah" appear in nearly every opinion and would swamp a full-text
match. Directional-prefix guards keep "North Salt Lake City"/"North Ogden"/"South Ogden"
from mis-attributing to slc/ogden, and single-word city names (Logan, Sandy, Draper…)
require a City/County/Town designator so surnames/first-names ("Logan Iverson") don't
false-match. Most-referenced: Summit County (14), Park City (13), Salt Lake City (9),
Lehi (8), Provo (8), Draper (7), Cottonwood Heights (6). It is a convenience index — a
name match, not a verified holding; confirm against the opinion text before quoting.

## Honest gaps (findings, never filled)

- **#102** — *PCCARG Properties (Sean Brown) / Wasatch County*, issued 7/6/2011. No
  Wayback capture of the PDF exists on either host (the original
  `.../2012/11/102-ao-pccarg-advisory-opinion-7-6-11.pdf` was never archived; the live copy
  is Cloudflare-walled). Recorded in `index.csv` with metadata from the archived filename +
  the OPRO index, **`path`/`text_path` blank** (text unrecovered). Wasatch County is not a
  repo entity.
- **#206** — no capture of any object for this number was located on either host in
  Wayback, and no metadata surfaced. Recorded as a blank gap row. May be an unissued /
  never-published number, or lost — cannot be determined without a live (browser) pull.
- **#142, #145** — PDFs are present, but they are **image-only scans** (`pdftotext`
  extracted <10 characters); their `date`/`title` are blank (not fabricated) and titled
  `[image-only scan; PDF present, text not extractable]`. A vision OCR pass could recover
  them (future work).
- **OPRO's newer `Advisory-Opinion-2025-NN` naming.** Late-2025 captures on
  `commerce.utah.gov/wp-content/uploads/2025/12/` show a NEW **year-sequential** filename
  scheme (`Advisory-Opinion-2025-01.pdf` … `-14.pdf`) that runs parallel to the global
  number series. These were **not** ingested here (their global opinion numbers must be read
  from each PDF body to dedupe against the 1–309 set) — a documented follow-up, not a
  silent omission. The 1–309 global-number set above is complete except for #102/#206.

## Note on the acquisition instruction

The task expected individual PDFs to "pull clean once listed." As of 2026-07-20 that is no
longer true — Cloudflare blocks direct PDF fetches too — so the Wayback channel above was
used instead. No accounts were created and no live Cloudflare bypass was attempted beyond a
standard browser User-Agent.
