# meeting_minutes/ — minutes + vote extraction (West Jordan, UT)

## What's here
- `minutes/<year>/<week-monday>/<date>_<slug>.md` — 321 minutes (2020–2026): 250 council
  (City Council / Committee of the Whole) **+ 71 separate agency minutes** (48
  Redevelopment Agency, 23 Municipal Building Authority). All from PrimeGov
  (`westjordan.primegov.com`), mostly born-digital text-layer PDFs (one 2023-12-06 is
  `docx-text`). **Not entirely OCR-free:** early (≈2020–mid-2021) files end in *scanned*
  signature pages whose OCR leaves cosmetic junk in the signature block (e.g. 2020-01-08,
  2020-02-26, 2020-03-05, 2020-03-11), and the 2020-02-12 regular-meeting minutes are an
  OCR'd scan throughout (artifacts like "occmTed", "11 :07"). Motion/roll-call text in these
  files is clean (spot-verified); the junk is confined to signature/attest blocks.
  Raw PDFs are not retained (regenerable via `minutes_index.csv` source URLs); markdown is
  the working copy.
- `minutes_index.csv` — every minutes file + `source_url` + `packet_url` (Complete-Packet
  agenda URL, used by the public-comments harvest).
- `extract_votes.py` — the roll-call extractor (below).
- `votes/<year>/<week>/<date>_<slug>.json` — 321 per-meeting structured votes (each carries
  a `body` field).
- `all_votes.csv` — long format, one row per member-vote (6,705 rows). THE analysis file.
  Has a **`body`** column (after `title`); see below.

## `body` column — Council vs RDA/MBA
In Utah the council **sits as the board** of the Redevelopment Agency (RDA) and Municipal
Building Authority (MBA) — **same 7 people, no Mayor** — to vote tax-increment financing,
project-area budgets, and developer/bond matters. West Jordan holds these as **SEPARATE
meetings** the same night (the council minutes only record a recess motion like "moved to
recess … to convene in agency board meetings"; the actual agency roll-calls live in the
separate RDA/MBA minutes). The original scrape filtered those meeting types out — they were
**re-acquired** here (PrimeGov `ListArchivedMeetings` → `CompiledDocument?meetingTemplateId=`
→ Azure blob, browser UA; download→`pdftotext`→delete, disk-safe).
- `body` ∈ `Council` (default) / `RDA` / `MBA`. (No CRA/CDRA/LBA: West Jordan uses
  "Redevelopment Agency", never the Community-Reinvestment name; there is no Local Building
  Authority. Fairway Estates is a separate Special Service Recreation District, **not**
  tagged — out of the RDA/CRA/MBA scope.)
- Tagged from the meeting slug/title (`redevelopment-agency`→RDA,
  `municipal-building-authority`→MBA). No in-council "convened as the RDA" vote blocks exist
  to re-tag — every council/COTW vote is `body=Council`.
- **Agency role synonyms map to the SAME members** (no new members): in board capacity the
  minutes say "Board Member" / "Chairperson" / "Vice Chairperson" / "Board Chair" instead of
  "Councilmember" / "Chair" — the parser's title list + surname normalization collapse these
  to the identical 7 people. Verified: every RDA/MBA voter is a subset of the council roster.
- **Counts** (motions): Council 1158, RDA 126, MBA 51 (1335 total; the 2023-12-20 second
  adjourn motion — recovered by the 3.5 double-adjourn fix — is tally-only, so member-vote
  row counts are unchanged). **Contested**: Council
  150, RDA 13, MBA 1. Filter `body=Council` for council-only analysis.
- **Re-acquired:** 71 separate agency meetings (48 RDA + 23 MBA, 2020–2026).
  **Still missing:** ~7 agency meetings whose Minutes doc wasn't published in PrimeGov
  (cancelled or recent/future: e.g. 2024-05-08 RDA & MBA, 2026-03-24/06-09/06-23 RDA,
  2026-06-09 MBA) — documented gaps, not fabricated. One 2022-10-12 RDA meeting was acquired
  but recorded no votes (the meeting was not held, postponed to 10-26).

## Run
`python3 meeting_minutes/extract_votes.py` (rebuilds the JSONs + `all_votes.csv`).

## Vote formats handled (West Jordan minutes use four)
1. Named `YES:` / `NO:` / `ABSENT:` (+ `ABSTAIN:`/`RECUSED:`) comma lists after "The vote
   was recorded as follows" — the dominant 2022–2026 form. (Lists can wrap across a
   page-break — the running header/footer is stripped and a dangling first-name/comma pulls
   in the continuation, incl. the RDA/MBA "Redevelopment Agency Minutes … Page N" headers.)
2. Tabular roll-call rows `<Member>  Yes|No|absent|Abstain` after "A roll call vote was
   taken" — the 2020–2021 form. Title prefixes recognized include the agency forms
   **Board Member / Board Chair / Chairperson / Vice Chairperson** (mapped to the same names).
3. Narrative "All voted in favor … unanimously" / "passed by unanimous vote" → recorded
   with `names_recorded:false` and empty member lists (no per-member names to assign).
4. "failed for lack of (a) second" → recorded motion, no vote, `names_recorded:false`.

## Conventions
- Council = **4 district + 3 at-large = 7 voting members**. **Mayor (Dirk Burton) does NOT
  vote** (listed under STAFF) — excluded from rosters and all vote lists.
- `motion_type` uses the fixed 12-category taxonomy (Ordinance, Resolution, Budget
  Amendment, Grant-Funding, Interlocal, Appointment, Public Hearing Action,
  Procedural/Administrative, Ceremonial, Contract/Purchase, Land-Use/Zoning, Other).
- Tally-only motions never get guessed member names (`names_recorded:false`).
- Member names normalized across the dataset; per-year roster cross-checked against the
  election winners in `../election_results/west_jordan_results_by_candidate.csv`.
- `result` holds the verbatim tally/outcome (e.g. `7-0`, `3-4`, `unanimous`); contested =
  any Nay/Abstain. See `votes/_validation_report.txt` for tally-vs-result consistency.

---
*Doc correction 2026-07-02 (audit `_audits/2026-07-02/report.md`, Phase 1.8): the
"born-digital text-layer PDFs" provenance was overstated — see the OCR note added above
(scanned signature pages ≈2020–mid-2021; 2020-02-12 OCR throughout; motion/vote text
verified clean).*

*Repair 2026-07-02 (Phase 1.9, duplicate meeting): the 2022-06-22 council meeting had been
parsed TWICE — PrimeGov published the same minutes PDF under two meeting templates
(`meetingTemplateId=268` and `737`; byte-identical downloads), yielding two markdown files
with identical bodies. Kept `2022-06-22_city-council-meeting.md` (matches the document's
self-title "CITY COUNCIL MEETING"); removed `2022-06-22_city-council-regular-meeting.md`
+ its index row + vote JSON (originals in `_backups/2026-07-02/west_jordan_city_council/`).
`all_votes.csv` 6,783 → 6,705 rows (−78 duplicated member-votes; all other rows verified
identical). The separate 2022-06-22 work-session/RDA/MBA files are distinct meetings and
untouched. Counts above reflect the repair.*
