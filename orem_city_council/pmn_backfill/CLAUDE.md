# orem pmn_backfill — Utah Public Notice minutes/agenda backfill

**Additive dataset.** Recovers Orem meeting minutes published on Utah's Public Notice
site (PMN, `utah.gov/pmn`) that are **absent from the audited minutes layer**
(`meeting_minutes/`, `planning_commission/`). It NEVER edits those layers — it sits
alongside them. Especially valuable pre-2021 (Orem's CivicClerk events start 2021-07)
and for bodies with no repo layer at all (RDA, MBA, Board of Adjustment).

Built 2026-07-05. Window 2020–2026.

## What's here

- `raw/` — every recovered PDF/DOCX exactly as PMN served it + `_fetch_log.jsonl`
  (polite_fetch provenance: url, status, bytes, sha256, retrieved_utc).
- `text/` — extracted plain text, one `.txt` per raw file (born-digital or OCR).
- `index.csv` — one row per unique (body, meeting-date) recovered. Draft/duplicate
  alternates for the same date are retained in `raw/` and listed in
  `duplicate_file_ids` / `notes`, not given their own row.
- `coverage.md` — per-year, per-body date comparison (repo vs PMN vs recovered).
- `AVAILABILITY.md` — Orem PMN entity id (**229**) + body ids, crawl chain, as-of date.

## index.csv columns

`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,
retrieved_date,format,extraction_method,text_path,notice_id,duplicate_file_ids,chars,orig_fname,notes`

Required-minimum cols present: `date,title,source_url,retrieved_date,format,
extraction_method`. `path`/`text_path` are dataset-relative (`raw/…`, `text/…`).
`format` ∈ {text, scanned} here (`scanned` = image PDF recovered via OCR). `body` ∈
{council, pc, rda, mba, boa, ssld}.

## Method — how the gap was found (date-diff logic)

1. **Crawl chain** (all GET; POST/CSRF search is unavailable to polite_fetch):
   entities (govType 3) → Orem entity `229` → `publicBodies` → per-body notice history
   via `notices.html?id=<bodyId>&page=300` (one GET returns the whole history; the
   default view is only 6 months). See AVAILABILITY.md for ids and URLs.
2. **Parse the notice-list HTML** into rows: notice id, title, meeting-datetime, and
   attachments with their `(…)` type labels. Keep attachments labeled
   **`(Meeting Minutes)`**. (PMN has no `(Agenda)` label; none were needed — every gap
   had minutes.)
3. **Resolve each minutes attachment's true meeting date**, in priority order:
   **filename date** (`MM.DD.YYYY`, `M.D.YYYY`, `MM-DD-YY`, `YYYY-MM-DD`) → notice
   **title** date → notice **datetime** column. Resolve its **body** from the filename
   (`ccmin`→council, `pcmin`→pc, `RDAmin`→rda, `MBA`→mba, `boa`→boa, `SSLD`→ssld) —
   a single Council notice sometimes bundles RDA/SSLD minutes, which are re-filed to the
   right body. Exclude items whose filename is plainly not minutes (e.g. a "Primary Legal
   Notice" mislabeled `(Meeting Minutes)`).
4. **Set-difference by DATE, not by count.** For Council & PC (which have a repo layer),
   a PMN minutes date is "missing" only if **no** repo `minutes_index.csv` date falls
   within **±4 days** (absorbs the routine 1–2 day offset between Orem's meeting date and
   how each system records it). RDA/MBA/BoA/SSLD have no repo layer → every minutes date
   is additive. The repo is a near-superset for Council/PC; do not compare per-year totals.
5. **Recover**: fetch the PDF/DOCX (retain raw), extract text (`pdftotext -layout`;
   python-docx-equivalent XML strip for `.docx`; **tesseract OCR at 200 DPI** for scanned
   image PDFs, `format=scanned`). Where a filename year was a typo, the **document's own
   header** (post-extraction) is authoritative — corrected `976307`→2022-06-14 MBA and
   `1097627`→2023-06-13 RDA.

## Cardinal rules honored

- **Additive only.** Nothing in `meeting_minutes/` or `planning_commission/` is touched.
- **Never fabricate.** A date the city never posted is data, not a gap to fill. Only the
  `(Meeting Minutes)` attachments that actually exist were recovered.
- **Raw retained.** Every original PDF/DOCX kept byte-for-byte with fetch provenance.

## Regenerate / extend

Re-crawl `notices.html?id=<bodyId>&page=300` for bodies 734/642/643/893/894, re-diff
against the current `minutes_index.csv` files, fetch new `(Meeting Minutes)` file ids.
Validate: `python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py
orem_city_council/pmn_backfill` (PASS). Screen text:
`python3 .claude/skills/audit-city-data/scripts/screen_corpus.py orem_city_council/pmn_backfill/text`.

## Caveats

- `format=scanned` rows are OCR (tesseract) — good for search/context, spot-check before
  quoting exact figures. Born-digital rows (`format=text`) are clean.
- Council 2026-05-12/-05-26 are recent (minutes not yet in CivicClerk as of build date);
  they are full packet-style PDFs incl. work session.
- Two byte-identical RDA 2022-05-10 files (`860073`,`860081`) — same document posted twice.
- SSLD (Special Service Lighting District) minutes appear only bundled under a Council
  notice; one date (2021-06-15) recovered, tagged `body=ssld`.

## 2026-07-19 — OCR pass over the image-only RDA/MBA (+ council) scans

The 12 `chars=0` image-only scans were OCR'd (tesseract, 300 DPI grayscale) and their
`index.csv` rows updated (`extraction_method=ocr-tesseract`, real `chars`). Every doc was
**in-body verified** for body + meeting date (PMN filenames lie):

- **RDA (5):** 2020-05-12, 2023-05-09, 2023-06-13 OCR'd + **promoted** to
  `meeting_minutes/all_votes.csv` (provenance=`pmn_minutes`); 2024-03-12 OCR'd and
  2024-05-14 (text taken from the **born-digital docx twin 1133405**, cleaner than OCR) are
  **already audited council-embedded** (`provenance=minutes`) so they auto-dedupe — text
  retained for search only.
- **MBA (5):** 2022-06-14, 2023-05-09, 2023-06-13, 2024-06-18 OCR'd + **promoted**.
  **`2026-06-10` was a PMN mislabel** — file `1454771` is the *approved scan of the
  2025-06-10 MBA meeting* (header/footer "June 10, 2025"; "PASSED and APPROVED … 26th day
  of June 2026"; same notice `1003075` as the draft docx `1311973`). Its index row was
  **removed and folded as a `duplicate_file_ids` of the 2025-06-10 row** (`pmn_exceptions.csv`
  wrong_date); MBA now has **5 unique recovered dates**, not 6. The raw + text files keep
  their id-based names.
- **Council (2):** 2026-05-12 (40pp), 2026-05-26 (24pp) — full work-session + meeting
  packet scans, header dates confirmed. **Text-retained only, NOT promoted** (council
  audited-layer backfill is out of the RDA/MBA scope).

Net promotion: **7 net-new RDA/MBA meetings / 17 motions** (all unanimous); pmn_minutes
RDA/MBA total 11 mtgs / 29 motions. Recovering 4 of those motions needed a **scoped
OCR/phrasing tolerance** in the parser (`ev.extract_file(..., lenient=True)`, used ONLY by
`extract_backfill_votes.py`): bare `<Body> Minutes-<date>` footers injected mid name-list
(2020-05-12 RDA budget), "The vote was unanimous, motion passed" (2022-06-14 MBA), and
"The motion <OCR-noise> passed" (2023-05-09 MBA). The **default audited council pipeline is
byte-identical** (diff-proven, 4037 rows unchanged). Validator 25 PASS / 1 WARN / 0 FAIL.
Backups `_backups/2026-07-19-pv-tierb-low/orem-ocr/`. **BoA (3 docs) remains OWNER-GATED**
(born-digital text already present; not ingested — no body plumbing).

## 2026-07-17 — final PMN-crosscheck flag verification (4 flags -> 1)

Verified all 4; appended 3 exceptions; re-run (--cached) 4 -> **1**. None related to the
RDA/MBA/BoA promotion candidates noted in config.
- **Recovery lead (1, agenda-grade):** council 2022-09-21 Public Hearing (body 734).
- **Exceptions:** wrong_date x2 (2024-05-08 '05.01.2024 Planning Commission Minutes.pdf' = held
  2024-05-01 PC min; 2024-06-04 '06.18.2024 approved cc minutes.pdf' = held 2024-06-18 council min
  — filename-date rescue, mirrors the existing 2023-09-20 duplicate); not_minutes x1 (2025-11-04
  '2025 Primary Legal Notice.docx' under 'Election Notices' — not meeting minutes).
