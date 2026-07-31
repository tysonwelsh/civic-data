# Ordinances — availability & gaps

As-of: **2026-07-03**. Scope target: **2020–2025** (2026 partial included as a bonus).

## What exists and was retrieved
- **Recorder-certified "Notice of Ordinances Approved" documents** for Provo, filed on the
  **Utah Public Notice Website (PMN)** under the *Provo Municipal Council* body (id **1600**).
  These are the authoritative adopted-ordinance summaries: each lists ordinance number(s),
  the council adoption date, and a full title/summary (with the land-use application code,
  e.g. `PLRZ…`/`PLOTA…`/`PLGPA…`).
  - **31 notice documents** (`.docx`) retrieved, covering **2024-05-14 → 2026-06-23**,
    = **87 distinct adopted ordinances**. Stored verbatim in `raw/`, text sidecars in `text/`.
- **Minutes-as-backbone** for the full 2020–2025 window: council motions in
  `../meeting_minutes/all_votes.csv` cite `Ordinance YYYY-NN` in their text for
  **2020, 2021, 2022, 2024, 2025, 2026**. These supply the number → date → subject mapping
  where no PMN notice exists.

## What does NOT exist / could not be retrieved (verified)
- **Full codified ordinance TEXT is not politely scrapable.** Both of Provo's code hosts are
  **HTTP 403 bot-protected** (verified 2026-07-03 via `polite_fetch.py --probe`):
  - `https://codelibrary.amlegal.com/codes/provo/...` (American Legal) → 403
  - `https://provo.municipal.codes/Code` (General Code / municipal.codes) → 403
  Both serve only the *current consolidated* code, not a chronological adopted-ordinance list.
  The PMN notices are summaries; each points to the full text at
  `https://documents.provo.org/onbaseagendaonline` (the OnBase packet portal — heavy PDFs,
  covered by the separate `packets/` source, not re-fetched here).
- **2023 adopted-ordinance NUMBERS are unavailable.** In 2023 the council minutes describe
  ordinances by *application code* and *agenda item id* (e.g. `PLGPA20210364`, `(23-023)`) but
  **stopped citing the adopted `Ordinance YYYY-NN` number in the motion text** (a minutes
  formatting change — 68 of 152 unique 2023 motions mention "ordinance", **0** carry a number).
  PMN has **no** Notice-of-Ordinance filings before 2024-05. So no scrapable source maps 2023
  Provo ordinance numbers to their subjects. **2023 = a genuine number-availability gap**
  (documented, not faked). The 2023 ordinance *actions* are still fully present in
  `all_votes.csv` by application code — they simply lack a resolvable ordinance number here.
- **PMN Notice-of-Ordinance filing began mid-2024.** The earliest is 2024-05-14; Jan–Apr 2024
  ordinances have no PMN notice and are represented only via minutes citations (`within_source`).
- **Pre-2024 independent adopted list:** none online. Utah State Archives holds the paper
  "Revised Ordinances" series (1877–2022, inventory 10088) but that is not a machine-readable
  online source.

## Adopted-but-not-in-votes (audit signal) — `adopted_not_in_votes.csv`
33 PMN-adopted ordinances have no matching motion (`match_confidence=none`). Split by reason:
- **30 = `meeting_not_in_vote_layer`** — the adoption date is **not in `all_votes.csv`** yet.
  `all_votes.csv` currently ends 2026-05-12 but is missing many 2H-2025 / 2026 council dates
  (OnBase publishes council minutes weeks late — see the city `CLAUDE.md` refresh note). These
  will resolve to high/medium matches once those minutes are ingested; they are a **coverage
  boundary, not a substantive discrepancy.**
- **3 = `adopted_meeting_extracted_but_no_matching_motion`** — the meeting IS in the vote layer
  but no clean number/app-code match exists (bundled or amended-in items):
  `2025-8` & `2025-10` (2025-01-28), `2026-6` (2026-02-10). These are the genuine audit flags.
