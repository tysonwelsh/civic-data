# ordinances/ — Lehi adopted ordinances index + linkage (as-of 2026-07-02)

Additive dataset built by the `expand-city-sources` skill (Source 3). **Read-only** on every
existing dataset; nothing here modifies `meeting_minutes/`, `planning_commission/`, `db/`, etc.

## What this is
An index of **adopted Lehi City ordinances** (313 rows, 2020-01-14 → 2026-02-10), each mapped to
the council **motion** that adopted it in `meeting_minutes/all_votes.csv`, with a confidence score.
The emphasis is **zoning / land-use** ordinances (zone-map changes, general-plan/area-plan
amendments, Development Code text amendments): **284 of 313 (91%)** are land-use.

## Where the data comes from (and why it is shaped this way)
Lehi does **not** publish a browsable online archive of full adopted-ordinance texts. Verified
2026-07-02:
- **Codified code host = American Legal Publishing** — `https://codelibrary.amlegal.com/codes/lehiut/`
  (the "Code of Ordinances", incl. the Land Use Development Code + Subdivision Regulations titles).
  This is the *current consolidated* text, not per-ordinance documents, and it is bot-protected
  (HTTP 403 to both `polite_fetch.py` and WebFetch — a JS SPA). It gives current code, not the
  number→date→subject history.
- **City ordinances page** — `https://www.lehi-ut.gov/government/meetings-and-agendas/ordinances/`
  posts **"Notice of Ordinance Adoption and Summary"** PDFs, but **only for the current year**
  (only 2026 present on 2026-07-02). Each notice is a Recorder-certified class-A notice listing every
  ordinance adopted at a meeting: number + subject + a plain-language summary + adoption date.
- The city/notices state full ordinance texts are **"on file at the Lehi City Recorder's Office"**
  (153 N 100 E) — i.e. **not online**. Prior-year notices are posted to Utah Public Notice
  (`utah.gov/pmn`, body 2512) but are not templated by date (opaque file ids) — see AVAILABILITY.md.

Because the full-text archive is offline, the **backbone of this index is reconstructed from the
council minutes themselves**: 334 council motions across 2020–2026 cite a specific ordinance number
in their text (e.g. `Consideration of Ordinance #14-2020, a zone change …`). Those motions carry the
ordinance **number, adoption date, and full subject** — everything needed for the number→date→subject
map — and they live in the already-audited `meeting_minutes/all_votes.csv`. This dataset is therefore
primarily a **derived index**, not a cache of downloaded texts.

## raw/
Only the material Lehi actually publishes online was downloadable: the **two 2026 Notice of Ordinance
Adoption PDFs** (born-digital). Retained verbatim in `raw/` with `_fetch_log.jsonl` (url, status,
bytes, sha256, retrieved_utc) from `polite_fetch.py`. Extracted text (labeled) is in `text/`.
`screen_corpus.py` on `text/` = clean (0 anomalies, 2 files).

## index.csv columns
Minimum provenance cols (`date`,`title`,`source_url`,`retrieved_date`,`format`,`extraction_method`)
plus source-specific cols:
- `ordinance_no` — canonical `YYYY-NN` (zero-padded). Lehi's minutes use two raw spellings —
  `#NN-YYYY` (2020–2021) and `#YYYY-NN` (2022+) — both normalized here.
- `adoption_date` (= `date` alias) — the council meeting date the adopting motion passed.
- `title` — ordinance subject, taken verbatim from the motion (or the notice PDF for notice-only rows).
- `source_url` — for the 4 ordinances covered by a 2026 notice PDF, the notice URL; otherwise the
  **repo-relative minutes file** that recorded the adoption (Lehi publishes no per-ordinance URL).
- `format` — `text` for all (born-digital minutes / born-digital notice PDFs; nothing scanned).
- `extraction_method` — `pdftotext -layout (…Notice PDF)` for notice-backed rows;
  `reconstructed from meeting_minutes motion text (…Granicus minutes)` for the rest.
- `path` — set only for notice-backed rows (the `raw/` PDF); empty for minutes-derived rows.
- `land_use` — informational classification (regex on the subject).
- `result` — Pass/Fail of the chosen adopting motion (all 313 = Pass; every indexed number was
  ultimately adopted).
- `matched_motion_date`, `matched_motion_no`, `match_confidence` — the linkage (below).
- `land_use_category` — informational classification (regex on the subject).
- `n_motion_events` — how many distinct (date, motion_no) motions cite this number (0 = notice-only).
- `linkage_note` — free text: multi-date ambiguity, cross-validation, notice-only reasoning.
- `minutes_source` — the repo minutes markdown that recorded the adoption vote (the join target row).

## Linkage method + confidence
Each ordinance is joined to the council motion that adopted it, following the skill's rule
(join by adoption date + ordinance number cited in the motion text). Because the index backbone is
*derived from* the motions, the number and date are present by construction for minutes-derived rows —
so linkage is strong but this is a **within-source** join, documented honestly, not an independent
cross-match. Where an official notice PDF exists (2026), the join is genuinely **cross-source**.

- **high (295)** — the ordinance number *and* adoption date both appear in exactly one council-motion
  event; that motion is the adoption. (Includes #01-2026 / #02-2026, which are additionally
  cross-validated against the Jan-28 Recorder notice.)
- **medium (17)** — the same ordinance number is cited in motions on **more than one date**
  (item continued across meetings, an amendment-then-main-motion, or a probable minutes
  renumbering/typo where June vs July subjects diverge); the last passing motion is chosen as the
  adoption and the alternates are listed in `linkage_note`. Also #2026-03 (notice-only impact-fee
  ordinance whose motion — "Transportation Impact Fees", 2026-01-27 — matches by **subject + date**
  but does **not** cite the number).
- **none (1)** — #2026-04 (Noise Control, adopted 2026-02-10): known only from the Feb-10 Recorder
  notice; `all_votes.csv` has **no 2026-02-10 rows** (beyond current vote coverage), so no motion
  match. Match fields left empty. **No match was forced.**

To go from an ordinance to its full vote: read `minutes_source` (the exact minutes markdown), or filter
`meeting_minutes/all_votes.csv` on `matched_motion_date` + `matched_motion_no`.

## Known limitations / how to extend
- **No full ordinance texts** — only official summaries (2026 notices). To obtain full texts, pull the
  Recorder's office copies, or scrape the draft-ordinance attachments inside Granicus agenda packets
  (`packets/`, Source 1) / Utah Public Notice (body 2512).
- **Numbered-motion coverage only** — a handful of ordinances may have been adopted via a motion that
  did not restate the `#YYYY-NN` number (like #2026-03); those are only captured where a notice PDF or
  a clean subject+date match surfaced them. This is a floor, not a guaranteed-complete list.
- 17 medium rows with multi-date number citations warrant a spot-check before quoting a single
  adoption date (see `linkage_note`).

Rebuild: re-run the builder in the Source-3 step of the skill against `meeting_minutes/all_votes.csv`
plus any newly downloaded notice PDFs.
