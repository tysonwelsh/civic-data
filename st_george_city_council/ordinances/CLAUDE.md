# ordinances/ — build method, linkage logic, caveats

Adopted zoning/land-use ordinance records for the **St. George, Utah** City Council
(Washington County — NOT St. George, Louisiana). Additive dataset built by the
`expand-city-sources` skill, SOURCE 3. As-of 2026-07-02.

## What this dataset is (and is not)

The primary artifact is a **number → adoption-date → subject → motion index**
(`index.csv`) so that a council vote on "Ordinance No. 2023-007" links to what the
ordinance did and when it was adopted. It is **NOT** a live mirror of the codified zoning
code: the Sterling Codifiers host (`stgeorge.municipal.codes`) is Cloudflare-403 blocked
(see `AVAILABILITY.md`). The full **Title 10 Zoning Regulations** text was, however,
recovered from a PMN-hosted PDF and is stored as a single reference row
(`doc_type=code`) — a one-time snapshot of the zoning title, not the whole code.

## Sources tried

| Source | Result |
|---|---|
| `stgeorge.municipal.codes` (Sterling Codifiers — current consolidated code, incl. Title 10 Zoning) | **Blocked.** robots 200 but `/Code/*` pages = HTTP 403 (Cloudflare); robots disallows ClaudeBot + `ai-train=no`. Not scraped (polite rule). |
| City site `sgcityutah.gov` "Notices" subfolders (Revize/cms3 host) | **Primary independent source** — per-meeting "Ordinances Approved and Adopted by the City Council" Recorder notices. **34 PDFs, 2024-10-03 → 2026-06-18.** No standalone adopted-ordinance index page; the Recorder's Office page only links out to the codified code + PMN. No notice PDFs posted before 2024-10-03. |
| Utah Public Notice (PMN), St George council bodies 241/242 | PMN "Ordinances Approved and Adopted" notices carry the list **in the notice HTML body, no PDF attachment** — they duplicate the city PDFs in text, so nothing new fetched. PMN planning-hearing notices (body 242) carry only "Public Information Handout" hearing notices, not adopted ordinance texts. **One useful PMN file: the full codified Title 10 Zoning Regulations** (`/pmn/files/532983.pdf`). |
| `meeting_minutes/all_votes.csv` council motions | **Backbone** — 209 ordinance numbers cited in motions (2023–2026). |

## Linkage method & confidence

`index.csv` columns: `ordinance_no, adoption_date, date (=adoption_date alias),
title, source_url, retrieved_date, format, extraction_method, path, land_use, result,
matched_motion_date, matched_motion_no, match_confidence, motion_type, doc_type`.

**Within-source backbone (the 209 rows, `match_confidence=within_source`).**
St. George council minutes are richly structured (MOTION / SECOND / VOTE) and the motion
text cites the ordinance number verbatim (`Ordinance No. YYYY-NNN`). The index is derived
by regex over the motion text in `all_votes.csv`:

1. Find every motion whose text contains `Ordinance No. YYYY-NNN`.
2. Group by ordinance number. For each number, the **adoption motion** = the earliest
   *passing* motion whose text contains approve/adopt/enact (a small number of ordinances
   appear first as a "continue" and later as an "approve" — e.g. 2025-001 continued
   2025-02-06, approved 2025-03-06 — the approve date is taken as adoption).
3. `adoption_date = date = matched_motion_date` = that meeting date;
   `matched_motion_no` = the motion number within that meeting; `title` = the motion text
   (subject); `source_url` = the minutes markdown that contains the motion.

> **CAVEAT — read before quoting.** `within_source` is **HIGH by construction, NOT an
> independent cross-match.** The number, date, subject, and motion all come from the *same*
> record (the minutes), so they cannot corroborate each other. A distinct value
> `within_source` (not `high`) is used precisely so this is never read as an
> externally-verified linkage. To promote a row to a genuine `high`, you would cross-match
> it against an independent Recorder-certified adoption record (a "Notice of Ordinance
> Adoption and Summary" PDF) — see below.

**`format=na`** on the 209 within-source rows: no separate ordinance document was
downloaded for these; the row is a derived index entry, not a retrieved file, so `path`
is empty (this is valid — the validator only checks non-empty paths resolve).

Confidence vocab in use: `high` (date + number both independently confirmed), `medium`
(date + subject, number not independently confirmed), `low` (date-only/fuzzy),
`within_source` (derived from the motion itself — this run), `none` (unmatched). **Never
force a match.**

**Independent cross-match → `high` (the 118 rows).** The 34 Recorder "Ordinances
Approved and Adopted by the City Council" notice PDFs are an **independent** record
(certified by the City Recorder, published separately from the minutes). Each notice
lists, per meeting, every ordinance number adopted + the Recorder's one-line subject +
the adoption date. Extraction: `pdftotext -layout`, then regex `Ordinance No. YYYY-NNN` +
subject span (the born-digital PDFs embed zero-width/bidi marks and split some first
letters onto their own line — these are stripped/rejoined during parse; see
"Text quirks"). Where a notice ordinance number ALSO appears in a council motion, the
number is confirmed by two independent documents → `match_confidence=high`. For these
rows `adoption_date`, `title`, `source_url`, `path` come from the authoritative Recorder
notice; `matched_motion_date/no` point at the corroborating motion (the motion whose date
equals the notice date; e.g. 2026-011 appears on two dates in motions and the notice
resolves adoption to 2026-04-02).

**Notice-only → `medium` / `none` (42 rows).** 42 ordinances appear in a Recorder notice
but no motion cited their number (typically consent-calendar adoptions — the consent
motion doesn't name individual ordinances). 39 fall on a date with a council meeting in
`all_votes.csv` → `medium` (matched by adoption date + subject to that meeting;
`matched_motion_no` left blank because no single numbered motion names it). 3
(2026-048/049/050, adopted 2026-06-18) have no matching meeting in `all_votes.csv` yet →
`none`, but the ordinance is still recorded from the authoritative notice.

## Text quirks (screener note)

`screen_corpus.py` flags `weird_char_outlier` on 8/35 notice files: the born-digital
notice PDFs embed zero-width space / bidi control marks (`U+200B`, `U+200E/F`, …) and
split some words' first letter onto a separate line — an authoring/pdftotext artifact,
not OCR error (dict_ratio median 0.78, split_word_rate ≈ 0, no dict/split outliers). The
raw `text/` sidecars are preserved verbatim (marks included, per the "don't clean source"
rule); only the `index.csv` `title` field has these marks stripped and split letters
rejoined so the subjects are readable.

## Coverage & confidence distribution

- **258 rows** = 257 ordinances (2023–2026) + 1 codified Title 10 reference row.
- **Confidence: high = 124, within_source = 91, medium = 39, none = 4** (3 notice-only
  no-meeting + the Title 10 code row).
- **2026-07-19 backfill:** ordinances **2026-051 … 2026-056** (all adopted 2026-07-02,
  each 4-0; Mayor Hughes presiding, Councilmember Tanner absent) added as **`high`** rows —
  each number is confirmed by BOTH the fetched 2026-07-02 Recorder "Ordinances Approved and
  Adopted" notice (independent; `raw/`+`text/`, provenance in `raw/_fetch_log.jsonl`) AND
  the enacting council motion (motions 6–11 of the 2026-07-02 regular meeting). The
  **"Title 10 codification"** requested in the same pass is the **existing `doc_type=code`
  reference row** (full codified Title 10 Zoning Regulations, PMN snapshot) — there is **no
  separate Title 10 codification/recodification ordinance**: the 2026-07-02 Recorder notice
  (authoritative) lists only 051–056, no 2026 minutes adopt a Title 10 recodification, and
  `stgeorge.municipal.codes` remains Cloudflare-403. Not fabricated.
- The 118 `high` rows are genuinely cross-confirmed (minutes motion ⟷ independent Recorder
  notice). The 91 `within_source` rows are mostly 2023 (39) and pre-Oct-2024 2024 (44) —
  before Recorder notice PDFs were posted online — plus 8 in 2025 the notices didn't list.
- By motion type (ordinances that had a motion): Land-Use/Zoning ≈ 173, Ordinance
  (fee schedules / Title-10 code text amendments) ≈ 33, other 3 → ~99% land-use/zoning/code.
- Pre-2023: no numbered ordinances (numbering scheme started 2023); 2020–2022 ordinance
  actions live un-numbered in `all_votes.csv` (see `AVAILABILITY.md`).

## Rebuild

The index is regenerated from `meeting_minutes/all_votes.csv`; there is no separate raw
corpus to re-extract for the within-source rows. Re-run the extraction described above if
`all_votes.csv` is refreshed. Any retrieved PDFs live verbatim in `raw/` with
`_fetch_log.jsonl` provenance.
