# Ordinances — availability & gaps (as of 2026-07-02)

Scope: adopted ordinance texts and adoption records for the **St. George, Utah** City
Council (Washington County), emphasizing zoning / land-use / general-plan-amendment
ordinances. Coverage window: 2020–2026 (votes floor 2020).

## What EXISTS and was captured

- **34 Recorder-certified "Ordinances Approved and Adopted by the City Council" notice
  PDFs**, per council meeting, **2024-10-03 → 2026-06-18**, retrieved from the city site
  (Revize/cms3 host, reached via `sgcityutah.gov` council Agendas-and-Minutes "Notices"
  subfolders). Each lists every ordinance adopted at that meeting + number + one-line
  subject. Born-digital, `pdftotext -layout`, text sidecars in `text/`.
- **Full codified Title 10 Zoning Regulations** (consolidated current text), retrieved from
  PMN `https://www.utah.gov/pmn/files/532983.pdf` (2.5 MB) — this is the zoning code the
  blocked Sterling host would otherwise hold. Indexed as a reference row (`doc_type=code`,
  no single adoption date).
- **Number → adoption-date → subject → motion index for 251 ordinances (2023–2026)** in
  `index.csv`, combining the Recorder notices (independent) with the council motions in
  `meeting_minutes/all_votes.csv` (which cite `Ordinance No. YYYY-NNN` verbatim):
  **118 `high`** (number confirmed by BOTH an independent Recorder notice AND a council
  motion), **91 `within_source`** (motion cites the number but no Recorder notice was
  posted — mostly 2023 / pre-Oct-2024), **39 `medium`** (Recorder notice lists it, matched
  by adoption date to a meeting, no motion named the number — consent-calendar adoptions),
  **3 `none`** (notice-only, no matching meeting in the vote layer yet). See `CLAUDE.md`.

## What does NOT exist online / could not be retrieved (verified)

- **The codified code (Title 10 Zoning) full text — NOT retrievable via polite GET.**
  Host `https://stgeorge.municipal.codes/` (Sterling Codifiers) sits behind **Cloudflare
  bot protection**: `robots.txt` serves 200, but every actual code page
  (`/Code/10`, `/Code/1-6-2`, …) returns **HTTP 403**. `robots.txt` additionally
  `Disallow`s `ClaudeBot` and sets `Content-Signal: ai-train=no, use=reference`. Per the
  polite-scraper rule we did **not** attempt to bypass the challenge. Consequence: the
  current consolidated zoning text is not mirrored here. (This contradicts the SKILL's
  prior assumption that Sterling is "usually more open than American Legal" — this
  particular instance is as locked as American Legal. See SKILL suggestions.)
  Verified 2026-07-02 via `polite_fetch.py --probe`.

- **Ordinance numbers before 2023 are not cited in the minutes.** The `YYYY-NNN`
  numbering scheme first appears in 2023 motions. 2020–2022 motions describe ordinances
  richly by subject (e.g. "an ordinance amending §10-8B-1 …") but carry **no ordinance
  number**, so those years have no number→date row here. The 2020–2022 ordinance *actions*
  are still fully present in `meeting_minutes/all_votes.csv` as land-use motions — they
  simply lack a citable number to key on. This is a publishing convention, not a scraper
  gap.

- **No adopted-ordinance PDFs before 2024-10-03.** The city posts the per-meeting
  "Ordinances Approved and Adopted" notice PDFs only back to Oct 2024 (verified by grepping
  the full agendas-and-minutes page HTML — earliest such PDF is 2024.10.03). Ordinance
  adoptions from 2020 → mid-2024 exist only as PMN HTML notice bodies (no attachment) or in
  the codified code. For 2023–mid-2024 the number→date→subject linkage is still captured via
  the motions (`within_source`); 2020–2022 have no numbers at all (below).

- **PMN "Ordinances Approved and Adopted" notices carry NO file attachment** — the list is
  in the notice's HTML body, duplicating (in text) the same summaries retrieved as PDFs from
  the city. Verified via the cumulative list `…/pmn/list/notices.html?id=241&page=200`.
  PMN planning-hearing notices (body 242) carry only "Public Information Handout" hearing
  notices, not adopted ordinance texts.

- **No standalone adopted-ordinance index / recorder archive page.** The City Recorder's
  Office page (recorder Christina Fernandez) only links out to the codified code and to PMN.

## How the "gaps" were verified
- Sterling/Cloudflare 403: three `polite_fetch.py --probe` calls (robots 200; `/Code/10`
  and `/Code/1-6-2` both 403), 2026-07-02.
- Pre-2023 numbering: `grep -icE "Ordinance No\.? ?[0-9]{4}-[0-9]+"` over 2020–2022 rows of
  `all_votes.csv` returns 0; the same grep returns 209 distinct numbers for 2023–2026.
