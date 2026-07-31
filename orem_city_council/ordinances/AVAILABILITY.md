# ordinances/ — coverage & availability (as-of 2026-07-05)

Additive dataset (`expand-city-sources`, Source 3): an index of **adopted Orem City
ordinances**, each tied to the council motion that adopted it in
`meeting_minutes/all_votes.csv`. Read-only on every existing dataset. Emphasis on
**zoning / land-use** ordinances (Orem City Code **Title 22 = the Development / Land-Use
code**: rezones, zoning-map changes, Standard-Land-Use text amendments, general-plan
edits, moratoria).

## Headline counts (re-derived 2026-07-19 over the Q3-refresh minutes)
- **100 adopted ordinances total**, 2020-01-14 → 2026-07-14.
- **51 land-use (51%)**.
- Confidence tiers:
  | tier | n | meaning |
  |------|---|---------|
  | `within_source` | 92 | reconstructed FROM the adopting motion's own text (number-less backbone) |
  | `medium` | 4 | CROSS-SOURCE: numbered orem.gov ordinance post uniquely matched to a 2026-06-23 council adoption motion (`O-2026-0014`…`0017`) |
  | `none` | 4 | independently published (orem.gov posts) but no linkable vote row — `O-2026-0012`/`0013` (2026-06-23 consent agenda) + `O-2026-0018`/`0019` (2026-07-14, beyond vote coverage) |
  | high / low | 0 | see "Why the backbone is minutes-derived" below (no signed independent PDF archive → `medium` is the ceiling) |
- Excluded (caught by the "ordinance" keyword but **not** an adoption): 3 motions — 2
  motions to **deny** (2024-12-10 #3 passed = ordinance denied; #4 failed) and 1
  **continue/refer-back** (2024-08-27 #3). Listed by `build_index.py` on every run.

**2026-07-19 delta (+5 rows, 95 → 100):** the Q3 refresh added 5 OCR'd council minutes
(2026-05-12 … 2026-06-23), so the backbone gained **3** within_source rows (2026-05-12 m5
92 S 800 E rezone, 2026-05-12 m6 CARE tax, 2026-05-26 m3 PC-powers text amendment); a
re-crawl of orem.gov added the **2026-07-14** ordinance post (`O-2026-0018`/`0019`); and
the independent posts now overlap the vote layer, producing the dataset's first **4
`medium`** cross-source rows (previously all 6 June-2026 posts were `none`). `O-2026-0014`
(FY2025-2026 budget amendment) is a notable capture — its adopting motion omits the word
"ordinance", so only the independent post reveals it is an ordinance.

## Is there an independent online ordinance archive?
**Almost none — this index is minutes-derived by necessity.** Verified 2026-07-05:
- **Codified code host = EnCodePlus / GovOS** —
  `https://online.encodeplus.com/regs/orem-ut/` (linked from the City Recorder page,
  `https://orem.gov/recorders/`). This is the **current consolidated code** (Title 22
  Development Code, land-use lookup, etc.), a JS app — it gives *current* text, **not** a
  number→date→subject adoption history. No per-ordinance document archive.
- **Municode** (`library.municode.com/ut/orem`) resolves to a generic JS shell — Orem's
  code is **not** hosted there; EnCodePlus is the real host.
- **orem.gov WordPress "City Council Ordinance" posts** — the ONLY independent, dated,
  numbered publication of adopted ordinance text found. This is a **brand-new practice
  that began mid-2026**: **3** ordinance posts now exist — the **2026-06-23** meeting
  (2 posts, `O-2026-0012`…`0017`) and the **2026-07-14** meeting (1 post,
  `O-2026-0018`/`0019`, printed OCR-style `0-2026-00NN`), format `O-YYYY-NNNN`. Retained
  verbatim in `raw/` (+ `_fetch_log.jsonl`), text in `text/`. Re-crawled 2026-07-19 (the
  two 06-23 posts re-fetched: ordinance content byte-identical, only the WordPress page
  wrapper churned, so the original 2026-07-05 raw captures are preserved). Nothing
  comparable exists for 2020–early-2026.
- Full ordinance texts for earlier years are **"on file at the Recorder's Office"** /
  Utah Public Notice (PMN) — not templated online. See TODO / Source-4 (PMN) agent.

## Why the backbone is minutes-derived — and why `medium` (not `high`) is the ceiling
Orem's council minutes **never print an ordinance number**. Every ordinance ADOPTION is,
however, a roll-call motion in the already-audited `meeting_minutes/all_votes.csv`
(e.g. *"approve, by ordinance, to amend Article 22-5-3(A) and the zoning map …"*), which
carries the **adoption date + full subject + the vote**. So the index backbone is
**reconstructed from those motions** — 92 rows, labelled `within_source` (number-less, a
strong but not independent join). Since 2026-07-19 the orem.gov ordinance posts finally
overlap the vote layer, so 4 ordinances (`O-2026-0014`…`0017`) are now **cross-matched**:
the number+caption from the independent post + the roll-call from the minutes = `medium`.
There is **no `high` tier** because Orem has no *signed* independent PDF archive (contrast
Park City's Municode S3 bucket) — the WP post is a born-digital HTML caption, so `medium`
is the ceiling.

## Gaps / audit signals
- **4 independently-adopted ordinances have NO linkable vote row (AUDIT SIGNAL), all
  `match_confidence=none`, match fields empty, not forced, vote layer not edited:**
  - `O-2026-0012` (Flood Damage, Chapter 10) and `O-2026-0013` (355 W University Parkway
    rezone R8→C2) were adopted on the **2026-06-23 consent agenda** (blanket motion m2
    "approve the consent items", 7-0) — not individually rolled, so no distinct vote row.
    (A consent-agenda audit signal, mirroring Park City's `none` handling.)
  - `O-2026-0018`/`0019` were adopted **2026-07-14**, beyond current vote coverage
    (`all_votes.csv` ends 2026-06-23) — they will link on the next minutes refresh.
- **No full ordinance texts for 2020–early-2026** — only the adopting-motion subject
  (verbatim). Full texts would need Recorder-office copies, PMN "Notice of Ordinance"
  docs, or Granicus/CivicClerk agenda-packet attachments.
- **Number-less for 2020–2026 minutes rows** — Orem assigns `O-YYYY-NNNN` numbers but
  does not restate them in minutes, so `ordinance_no` is empty for all 92 `within_source`
  rows. Only the 8 independent-post rows (4 `medium` + 4 `none`) carry a number.
- Documented minutes gap **Apr–Jun 2021** (see repo CLAUDE.md) applies here too — any
  ordinance adopted then is absent from the vote layer and thus from this backbone.
- **68 of the source minutes files (2022–2026) are OCR** — those rows carry
  `format=scanned`; motion subjects may have minor OCR noise (e.g. "UT AH", "a mend").

Rebuild: `python3 ordinances/build_index.py` (idempotent).
