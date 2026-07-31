# ordinances/ — availability & gaps (as-of 2026-07-05)

What was checked for Ogden City adopted-ordinance texts / lists, what exists online, and what
does not. Additive dataset built by the `expand-city-sources` skill (Source 3). **Read-only** on
every existing dataset — nothing here modifies `meeting_minutes/`, `planning_commission/`, `db/`.

## Coverage summary
- **308 adopted Ogden City ordinances indexed**, 2020-01-07 → 2026-06-16 (numbers 2019-54 → 2026-14;
  the two 2019 numbers were adopted at the first Jan-2020 meetings, in-window).
- **107 of 308 (35%) are land-use / zoning** (`land_use=yes`): zoning-map reclassifications, General
  Plan / community-plan amendments, Title 15 (Land Use Code) text amendments, street/alley vacations,
  subdivision/overlay changes. The rest are budget, fee, personnel, and general municipal-code ordinances.
- Per year: 2019 (2), 2020 (52), 2021 (54), 2022 (56), 2023 (60), 2024 (34), 2025 (39), 2026 (11).

## Confidence tiers (see CLAUDE.md for method)
- **high — 27** — ordinance number appears in BOTH a council adoption motion (`meeting_minutes/all_votes.csv`)
  AND an independent Recorder-certified Synopsis-of-Ordinance PDF retained in `raw/`. (2022: 1; 2023: 3;
  2024: 13; 2025: 8; 2026: 2.)
- **within_source — 276** — derived from the council adoption motion text only; the number/date/subject
  are present *by construction* from the motion, NOT independently corroborated (no synopsis PDF was
  located for these). This is a within-source linkage, honestly labeled — do **not** read it as a
  cross-checked match.
- **none — 5** — a genuinely adopted ordinance (per an independent Recorder Synopsis PDF) with **no
  matching adoption motion in `all_votes.csv`**. Match fields left empty — no match was forced. These
  are audit signals (see "Adopted ordinances missing from the vote layer").

## Code host (current codified text)
- **American Legal Publishing** — `https://codelibrary.amlegal.com/codes/ogdencityut/latest/`
  ("CITY CODE of OGDEN CITY, UTAH"; includes the Land Use Code). Linked from the city Codes page.
  - **Not retrievable by the polite fetcher:** returns **HTTP 403** to `polite_fetch.py` (bot-protected
    JS SPA). Provides only the *current consolidated* code text, not a number→date→subject ordinance
    history, so it is not the join backbone. Read it in a browser for current zoning text.

## Adopted-ordinance list — an independent archive DOES exist (partial)
Unlike some cities, Ogden's City Recorder publishes **"AFFIDAVIT OF POSTING — SYNOPSIS OF OGDEN CITY
ORDINANCE"** certificates — each names the council meeting date, every ordinance number adopted that
night, and the full ordinance title. Two independent hosts:
- **City DocumentCenter** (`https://www.ogdencity.gov/DocumentCenter/View/<id>`) — discrete synopsis
  PDFs, reliably posted **late-2023 onward** (earliest discrete file found: 2023-58/59, Nov 2023).
- **Utah Public Notice** (`https://www.utah.gov/pmn/files/<id>.pdf`) — the same certificates, reaching
  **back to 2022** (e.g. 2022-39, Oct 2022; 2024-3/4, Feb 2024).

**20 signed PDFs were retrieved** into `raw/` (17 DocumentCenter + 3 PMN; the PMN "Ordinance 24-11" hit
was **South Ogden**, a different city, and was **excluded** from the index). Together they independently
corroborate **32 ordinance numbers** (2022, 2023, 2024, 2025, 2026), of which 27 matched a council
motion (→ high) and 5 did not (→ none). Extracted text is in `text/` (labeled); `screen_corpus.py` =
clean (0 PUA/mojibake/replacement-char anomalies; the 4 advisory flags are the long full-text 2026
budget/salary PDFs, expected for those documents).

### Why the independent set is not exhaustive
The CivicEngage site search (`/Search/Results?searchPhrase=Synopsis of Ordinance`) **returns a fixed
top-10 regardless of the `pagenum` parameter** — it cannot be paged to enumerate the full synopsis
back-catalog, and the DocumentCenter exposes no browsable "ordinance synopsis" folder. The 20 PDFs
here were assembled from that top-10 plus targeted web-search discovery. A complete synopsis harvest
would require the Recorder's Office or a full PMN body crawl (see Deferred). **Pre-2022 synopses were
not located online at all.** The index backbone therefore remains the council minutes.

## The backbone: minutes-derived
Ogden's council **minutes richly cite ordinance numbers** — 319 distinct `Ordinance YYYY-NN` numbers
are referenced across `all_votes.csv`, and 300+ carry an explicit adoption motion (the clerk's "…WAS
ADOPTED AS OGDEN CITY ORDINANCE N" (2020-23) or "ORDINANCE N WAS ADOPTED [ENTITLED: …]" (2024+) forms,
plus "ORDINANCE N BE ADOPTED" / amend-and-adopt variants). The 2026-07-02 subject-enrichment
(`[ENTITLED:"…"]` / `[AGENDA ITEM:"…"]` brackets appended to Council adoption motions by instrument
number) is what supplies each ordinance's verbatim title. This is the source for all 276 within_source
rows and the title/vote for the 27 high rows.

## Adopted ordinances missing from the vote layer (audit signals — 5)
Every "none"-confidence row is a real adopted ordinance with no vote row:
- **2025-01** (adopted **2025-01-07** per the 2025-1 synopsis PDF) — `all_votes.csv` has no 2025-01-07
  meeting at all (first 2025 vote date is 2025-01-14). The first council meeting of 2025 appears to be
  **missing from `meeting_minutes/`** → worth a minutes-acquisition check.
- **2026-09, 2026-10, 2026-13, 2026-14** (all adopted **2026-06-16**, the FY27 budget/CIP/salary
  package) — council minutes coverage currently ends **2026-05-19**, so the June 16 2026 meeting is
  simply not yet ingested. These will link automatically once that meeting's minutes are added.

## Known limitations / how to extend
- **No full ordinance texts for most rows** — only the Recorder synopses (titles + adoption date) are
  online for a subset; full signed texts are "available for review in the Ogden City Recorder's Office,
  2549 Washington Blvd #210." The four 2026 budget/CIP/salary items are the exception (full-text PDFs).
- **within_source rows are a floor**, not a corroborated list — an independent synopsis was not found
  for them. To upgrade: crawl the Utah PMN Ogden-City body for the synopsis back-catalog (overlaps
  Source 4 / PMN backfill), or pull Recorder's Office copies.
- **4 multi-date rows** (2019-54, 2020-26, 2025-07, 2025-23) cite the same number in passing motions on
  more than one date (item continued / re-read / re-numbered); the chosen adoption is noted in
  `linkage_note` — spot-check before quoting a single date.
- **2022-39 date conflict** (flagged, high): the OCR'd minutes record the adopting roll-call on
  2022-08-09 (5-1 Pass), but the Recorder's PMN synopsis certifies adoption at the **Oct 4 2022**
  meeting. `matched_motion_date` points to the real Aug-9 vote row; `linkage_note` records the conflict.

Rebuild: re-run the Source-3 builder against `meeting_minutes/all_votes.csv` plus any newly downloaded
synopsis PDFs (`raw/`), then `python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py
ogden_city_council/ordinances`.
