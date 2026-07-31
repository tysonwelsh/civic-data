# ordinances/ — availability & gaps (as-of 2026-07-02)

What was checked for Lehi adopted-ordinance texts / lists, what exists, and what does not.

## Code host (current codified text)
- **American Legal Publishing** — `https://codelibrary.amlegal.com/codes/lehiut/latest/overview`
  (linked from `https://www.lehi-ut.gov/government/codes-ordinances/` as "Municipal Codes").
  Titles include **Land Use Development Code** and **Subdivision Regulations**.
  - **Not retrievable by the polite fetcher:** returns **HTTP 403** to both `polite_fetch.py` and
    WebFetch (bot-protected JS SPA). Provides only current consolidated text, not a
    number→date→subject ordinance history, so it is not the join backbone. Read it in a browser for
    current zoning text; disclaimer notes it "may not reflect the most current legislation."
- The city also posts the **Development Code chapter-by-chapter** as individual PDFs under
  `lehi-ut.gov/media/...` (e.g. `ch12-development-standards-51424.pdf`) — current land-use text,
  not per-adoption documents. Not mirrored here (out of scope for the adopted-ordinance index; belongs
  with the General Plan / land-use context in `housing_plans/`).

## Adopted-ordinance list (number → date → subject)
- **City ordinances page** — `https://www.lehi-ut.gov/government/meetings-and-agendas/ordinances/`
  posts **"Notice of Ordinance Adoption and Summary"** PDFs (Recorder-certified class-A notices with
  number + subject + summary + adoption date). **Only the current year (2026) is present** on
  2026-07-02; two PDFs were downloaded (Jan-28 and Feb-10 notices → ordinances #01–#04-2026). The page
  is a CMS accordion with no prior-year tab exposed; media URLs are hashed
  (`/media/<hash>/MMDDYY-ordinance-notice.pdf`) so prior-year notices cannot be URL-templated.
- **Recorder's Office** — every notice and the codes-ordinances page state a **complete copy of all
  ordinances is on file at the Lehi City Recorder's Office (153 N 100 E)**, i.e. **full texts are not
  published online**. Contact: Teisha Wilson, City Recorder — 385-201-2269 / twilson@lehi-ut.gov.
- **Utah Public Notice (`utah.gov/pmn`, body 2512)** — the notices are also posted here (each notice
  certifies posting "on the Utah Public Notice Website"). PMN retains prior years, but file ids are
  opaque and must be crawled per notice page (not attempted in this pass — see "Deferred").

## What this dataset therefore contains
Because no online full-text archive exists, the index is **reconstructed from the council minutes**:
334 motions (2020–2026) in `meeting_minutes/all_votes.csv` cite an ordinance number in their text,
yielding **313 unique adopted ordinances** with number, adoption date, subject, and the adopting
motion. The two available 2026 notice PDFs are retained in `raw/` and cross-validate the 2026 rows.

## Deferred / not obtained (and how to get it later)
- **Prior-year (2020–2025) official Notice-of-Adoption PDFs** — crawl **Utah Public Notice body 2512**
  notice pages for `*-ordinance-notice.pdf` attachments (overlaps Source 4 / PMN backfill). Would add
  official summaries + an independent cross-check for the ~331 minutes-derived rows.
- **Full ordinance texts** — Recorder's Office copies, or the draft-ordinance attachments bundled in
  **Granicus agenda packets** (Source 1, `packets/`) — each land-use item's packet typically contains
  the full ordinance and exhibits. Retrieving 300+ is a distinct, heavier scrape; logged, not done.
- **American Legal current code text** — blocked to the fetcher (403); readable in-browser only.

## Honest gaps
- **#2026-04 (Noise Control)** is indexed from the Feb-10 notice but has **no motion match**
  (`all_votes.csv` has no 2026-02-10 rows yet) → `match_confidence=none`, match fields empty.
- The index is a **floor**: ordinances adopted via a motion that did not restate the `#YYYY-NN` number
  (e.g. #2026-03, recovered only via the notice) may be under-counted for years without a notice PDF.
