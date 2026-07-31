# ordinances/ — availability & gaps (as-of 2026-07-05)

What was checked for Vineyard adopted-ordinance texts / lists, what exists, and what does not.

## Do Vineyard minutes cite ordinance numbers? YES.
Empirically verified: Vineyard's CivicClerk minutes cite `Ordinance YYYY-NN` richly in both prose
and motion text (e.g. `APPROVE ORDINANCE 2021-07`, `ADOPT ORDINANCE 2023-04, GENERAL PLAN
AMENDMENTS`). This is the **Lehi/Logan branch** (numbers present), not the Orem branch (no numbers).
So the number→date→subject→motion index is reconstructable straight from the vote layers.

## Code host (current codified text)
- **`https://vineyard.municipalcodeonline.com/`** — the city's online municipal code (linked as
  "Municipal Code" from the agenda/minutes page). Fetcher-reachable (HTTP 200, not bot-blocked).
  It carries an **"Ordinances — an index of Ordinances adopted by the Municipality"** book, so an
  independent adopted-ordinance archive **does exist in principle**. **But** it is a JS single-page
  app: the ordinance tree loads via `/book/expand?type=ordinances`, which returns **HTTP 500** to a
  plain GET (needs a client-set `data-databookid`). So the number→date→subject list is **not politely
  GET-retrievable**, and the code gives current consolidated text, not per-ordinance documents.
- **American Legal** `codelibrary.amlegal.com/codes/vineyardut/` → **HTTP 403** to `polite_fetch.py`
  (bot-protected, as elsewhere in this repo).
- **Municode** has a vendor client record for Vineyard (`api.municode.com` `ClientID 17397`), but the
  public code host is municipalcodeonline; Municode is current-text-only regardless.

## Adopted-ordinance documents (independent)
- **Utah Public Notice — PMN body 530** (`utah.gov/pmn/sitemap/publicbody/530.html`; cumulative list
  via `/pmn/list/notices.html?id=530&page=200`). The Recorder posted **"Ordinance Passage" notices
  with the signed ordinance PDF attached** for a short 2021 window. **5 signed ordinance PDFs were
  retrieved** and retained in `raw/`:
  - `2021-07` ZC Amend Accessory Buildings/Swimming Pools (zoning) · `2021-09` City Manager Duties ·
    `2021-10` Election Code · `2021-11` Subdivision Code 14.06/14.08 (land use) · `2021-12` Committees
    & Commissions (Ch. 2.30).
  These are the only independently-published full ordinance texts a polite GET could recover. PMN also
  holds 2016/2019 zoning **public-hearing** notices (not adopted-ordinance documents).
- **City site** — `vineyardutah.gov` Recorder page + Document Center: no browsable signed-ordinance
  archive surfaced (ordinance texts route to the municipalcodeonline code host above).

## What this dataset therefore contains
Because no online full-text archive is politely retrievable, the index is **reconstructed from the
minutes**: 84 unique adopted ordinance numbers (2020-02 → 2025-16) cited in council/PC motion text in
`meeting_minutes/all_votes.csv` + `planning_commission/all_votes.csv`, with number, adoption date,
subject, and the adopting motion. The 5 PMN signed PDFs cross-validate their rows.

## Coverage & counts
- **Total ordinances indexed: 84** (years: 2020=16, 2021=12, 2022=15, 2023=25, 2024=9, 2025=7).
- **Land-use: 18** — zoning_text_amendment 8, zone_change 4, subdivision 3, general_plan_amendment 2,
  development_agreement 1.
- **Confidence tiers:**
  - `high` **5** — 2021-07, 2021-09, 2021-10, 2021-11, 2021-12 (independent PMN signed PDF + passing motion).
  - `within_source` **79** — number cited in motion text only; no independent archive retrieved
    (strong by construction, NOT independently corroborated).
  - `none` **0** — the former `2021-12` audit signal is RESOLVED (2026-07-19; see below).
- **Independent archive exists?** In principle yes (municipalcodeonline "Ordinances" book) but it is
  JS-gated / not GET-retrievable; the only independently-retrieved documents are the 5 PMN PDFs. The
  index is therefore **minutes-derived** with a 5-ordinance independent cross-check.

## Honest gaps / audit signals
- **RESOLVED (2026-07-19) — former `2021-12` audit signal.** The 2021-09-08 council meeting DOES
  record the adopting motion (business item 9.3, "Carried unanimously"); the clerk simply **mistyped
  the ordinance number** in the motion sentence as "APPROVE ORDINANCE 2021-02" (the agenda header
  reads "(Ordinance 2021-12)", and the signed PDF is adopted 2021-09-08 for Chapter 2.30). The vote
  was never absent from `all_votes.csv` — it is 2021-09-08 #4, mis-numbered at source. A documented
  `MOTION_ORD_OVERRIDE` in `build_index.py` re-keys that motion event to `2021-12` for linkage only
  (verbatim motion text unchanged); `2021-12` is now `high` and `2021-02` keeps only its genuine
  2021-02-10 adoption. See `CLAUDE.md` → "2021-12 source-typo resolution".
- **Floor, not census — 33 prose-only numbers.** These `YYYY-NN` numbers appear in the minutes prose
  but are cited by no passing motion, so they are not indexed: `2021-01, 2021-04, 2021-15, 2021-16,
  2021-17, 2022-01, 2022-02, 2022-03, 2022-10, 2022-15, 2023-18, 2023-20, 2023-23, 2023-25, 2023-28,
  2023-32, 2024-06, 2024-12, 2024-13, 2024-14, 2024-15, 2024-16, 2025-02, 2025-05, 2025-06, 2025-07,
  2025-10, 2025-11, 2025-13, 2025-16, 2026-01, 2026-02` (plus one OCR artifact `2024-253`). To capture
  these, obtain the municipalcodeonline "Ordinances" book (needs a JS-capable fetch) or the Recorder's
  office copies.
- **Pre-2020 (2014–2019)** — Vineyard's town-to-city years — not covered: no minutes floor and no
  politely-retrievable independent list.
- **Not-confirmed-adopted rows** — a few within-source numbers are cited only in a non-adopting motion
  (e.g. `2022-16`, a PC negative recommendation); flagged in `linkage_note`.

## Deferred / how to extend
- **municipalcodeonline "Ordinances" book** — the independent number→date→subject archive; needs a
  headless/JS fetch (its `/book/expand` endpoint 500s on plain GET). Would upgrade many within_source
  rows toward `high` and recover the 33 prose-only numbers + pre-2020 ordinances.
- **Full texts** — the municipalcodeonline documents, or the ordinance PDFs bundled in CivicClerk
  agenda packets (Source 1), or Recorder's office copies.
