# pmn_backfill — Taylorsville PMN cross-check & recovered minutes

Additive dataset from the `expand-city-sources` skill (source #4). Cross-checks Utah Public
Notice (`utah.gov/pmn`) against the built minutes layers and recovers only meetings the repo
is genuinely missing. **The `meeting_minutes/` and `planning_commission/` layers were not
touched.**

## Layout
```
raw/                 recovered minutes PDFs verbatim (+ _fetch_log.jsonl provenance)
text/                extracted markdown sidecars (labeled with extraction_method)
index.csv            recovered meetings — 8-col minutes schema + extraction_method + PMN cols
coverage.md          per-year repo-vs-PMN table + every flagged candidate's resolution
ocr_upgrade_candidates.csv   15 born-digital PMN copies of repo RICOH-scan meetings
AVAILABILITY.md      what was checked, what exists, what doesn't
```

## PMN body ids (discovered, not guessed)
Entity chain: `entities.html?id=3` → Taylorsville **entity 284** →
`publicBodies.html?id=284`. Council **720**, Planning Commission **722**, RDA **721**,
CDRA **2770** (empty), + inactive/non-repo bodies (Board of Adjustment 2523, Canvassers
3379, Taxing Entity 2871, Recorder 6931).

## Method (reproduce)
1. Cumulative crawl per body: `polite_fetch.py --out notices --name notices_<b>.html
   "https://www.utah.gov/pmn/list/notices.html?id=<b>&page=300"` — one GET returns the body's
   entire notice history (list view otherwise shows only 6 months; historical search is
   POST/CSRF and off-limits).
2. Parse each `<tr>` → notice title, posting date, and `(Meeting Minutes)` attachment file
   ids/filenames.
3. **Key on the internal/filename MEETING date, not the PMN posting date.** PMN routinely
   attaches the *previous* meeting's approved minutes to a notice, and filenames are often
   mis-dated (year typos, wrong month). Every set-difference hit was opened and its PDF header
   date read before a verdict (see `coverage.md` resolution table).
4. Set-difference vs repo `minutes_index.csv` dates (±1 day). Fetch only genuine gaps.

## What's here
- **2 recovered council meetings** (`index.csv`): the 2020-01-29 and 2024-01-31
  *Let's Talk Taylorsville* 5th-Wednesday town halls. NON-STANDARD informal constituent
  sessions — no formal roll-call votes; do not feed to the vote extractor as normal meetings.
  - `format` uses the validator vocab: `text` ≈ the minutes layer's `pdf-text`
    (born-digital, `pdftotext -layout`); `scanned` ≈ `ocr` (image PDF, `tesseract`).
- **15 OCR-upgrade candidates — RESOLVED 2026-07-12** (`ocr_upgrade_candidates.csv` carries the
  per-row outcome; all 15 PDFs fetched into `raw/` + indexed):
  - **6 PROMOTED** into the audited layer (council 2024-12-04, 2025-01-22, 2025-05-07; PC
    2021-08-24, 2021-09-14, 2022-04-26): the born-digital `pdftotext -layout` conversion
    replaced the OCR markdown (index rows now `source=pmn`, `format=pdf-text`; promotion
    provenance in each md header; the city scans stay in each dataset's `raw/`, PMN copies
    added alongside as `*_pmn<fileid>*`). Vote re-extraction diffed clean at the
    (date, body, motion_no, member, vote) level — the ONE change is a genuine recovery:
    **2025-01-22 council m5 regained Curt Cochran's Aye** that the RICOH OCR dropped
    (roll now the full 5). Backups: `_backups/2026-07-12-t3.3/taylorsville/`.
  - **2 NO-OPs** (council 2021-06-02, 2022-01-05): the PMN file is the COUNCIL minutes —
    already born-digital in the repo; the repo's OCR doc on those dates is the *separate RDA
    Board minutes*, which PMN does not carry (the PMN text only references the RDA recess).
  - **7 PC DRAFT sidecars** (2024-03-12, 2024-03-26, 2025-01-28, 2025-07-22, 2026-02-24,
    2026-03-10, 2026-03-24): PMN posts only DRAFT minutes; the repo's APPROVED RICOH scans
    stay canonical. The drafts live here as searchable raw sidecars — **do NOT swap.**

## If merging into the minutes layer later (deliberate, human-reviewed)
The two town halls are real council-body meetings but non-standard. If merged, add them to
`meeting_minutes/minutes_index.csv` with the same `slug`/path conventions, mark them as
town-hall/no-vote, and rebuild `db/` + `weeks/`. Until then they live here for review.

## 2026-07-17 — crosscheck flag verification (22 → 16)

Verified all 22 `crosscheck_flags.csv` flags. 6 exceptions appended; re-run: **16 flags**
(all agenda_only_gap; 6 suppressed, 6 pending-adoption). Consistent with this dataset's
"repo is a PMN superset / 0 genuine minutes gaps" finding — all 3 missing_minutes flags are
false positives.

**missing_minutes exceptions (3 — none net-new):**
- `2023-04-25 / 722` **not_minutes** — the only 04-25 attachment is an MP3 AUDIO recording;
  the paired PDF is the already-held 2023-02-28 PC minutes.
- `2023-09-29 / 720` **wrong_date** — attached `Minutes - 9-20-23.pdf` is the already-held
  2023-09-20 council minutes (notice date ≠ meeting date).
- `2026-05-12 / 722` **draft** — `Draft Minutes - April 28, 2026.pdf`; 2026-04-28 already
  held as an approved RICOH scan. Born-digital DRAFT = a text quality-upgrade candidate for
  2026-04-28 (the TODO-queued born-digital upgrade), but do NOT promote a draft over approved.

**agenda_only_gap non-meeting exceptions (3):** `2023-10-03/722` "Amended Annual Meeting
Notice"; `2024-12-16/722` "2025 Schedule of Planning Commission Meetings"; `2023-06-12/720`
"Candidate Orientation Meeting" (election-admin, out of scope). All kind=other.

**Recovery leads (16 agenda-grade — reported, NOT ingested; PMN has agenda only):**
PC meeting agendas the repo lacks (2020-02-11, 2020-07-28, 2020-09-22, 2021-02-23 WS,
2021-11-23 WS, 2022-10-25, 2022-11-08, 2022-11-22 WS, 2023-05-01 hearings, 2023-05-23,
2023-11-28, 2024-09-24, 2025-09-23); council 2022-03-25 "Public Meeting" + 2023-04-13 "City
Priorities Meeting"; RDA 2026-05-11 "Public Hearing". Reviewer checks CivicEngage for minutes.

**Hardening candidates:**
- "2025 Schedule of Planning Commission Meetings" slipped past `RE_NOT_MEETING` (H-3 added the
  exact phrase "meeting schedule"; this variant is "Schedule of … Meetings"). Broaden the
  schedule-notice regex to catch "schedule of … meetings" / "annual meeting notice".
- MP3 / audio-only attachments arriving under a `(Meeting Minutes)` label (2023-04-25) trigger
  missing_minutes though they carry no text minutes. Consider gating minutes attachments on a
  document extension (pdf/doc/docx) so audio files don't read as recoverable minutes.

## 2026-07-17 (wave 2) — 12 agenda_only_gap flags fully probed & resolved

Probed CivicEngage Central (Minutes year folders, verified live with the browser UA) AND
each PMN notice body for the 12 `agenda_only_gap` flags. **Every flagged date is confirmed
absent from the primary source (CivicEngage) too** — the repo really is a PMN superset; none
had a recoverable APPROVED minutes document. **Vote layer unchanged (0 promotions).** After
filing, `pmn_crosscheck.py taylorsville --cached` → **0 flags** (7 exception-suppressed, the
9 unrecovered dates filtered by the `near(unrec)` check). `validate_city.py` 26 PASS / 0 FAIL.

**3 → `pmn_exceptions.csv` (not genuine minutes gaps):**
- `2020-02-11 / 722` **other (cancelled)** — notice 585887 BODY text: the Feb 11 PC meeting
  "has been cancelled" (next = Feb 25). Cancellation is in body prose, not title/filename, so
  `RE_CANCEL` missed it → hardening candidate (scan notice body for cancellation).
- `2023-05-01 / 722` **wrong_date** — notice 829395 is the public-hearing notice for the
  already-held **2023-05-09** PC meeting ('3 Public Hearings - May 9, 2023.pdf').
- `2026-05-11 / 721` **wrong_date** — notice 1079547 is the RDA FY26-27 budget public-hearing
  notice for the already-held **2026-05-20** Council/RDA meeting ('...5.20.2026.pdf').

**9 → `minutes_unrecovered.csv` (real meetings, minutes never published anywhere; GRAMA-eligible):**
- Council (`meeting_minutes/`): **2022-03-25** & **2023-04-13** — informal "City Priorities"/
  "Public Meeting" sessions, "no formal action will be taken" (no roll-call votes).
- PC (`planning_commission/`): **2020-07-28, 2020-09-22, 2021-02-23, 2021-11-23** (four Work
  Sessions, agenda-only) + **2022-10-25, 2022-11-22, 2023-05-23** (meetings PMN carries only as
  an `.mp3` AUDIO recording + agenda — demonstrably held, no text minutes). These are honest
  publishing gaps: no born-digital or scanned minutes doc exists on CivicEngage or PMN. ASR of
  the audio is never authoritative (transcripts/ policy) and Whisper is out of scope — a GRAMA
  request to the City Recorder is the only recovery route.

Backups: `_backups/2026-07-17-wave2/taylorsville/`.
