# meeting_minutes/ — Vineyard, UT council vote pipeline

## What's here
- `minutes/<year>/<week-monday>/<date>_<slug>.md` — **172 minutes** (163 council + 9 RDA
  board; born-digital text-layer PDFs → markdown via CivicClerk; 3 council files recovered
  via OCR; **26 files recovered locally from saved agenda packets**, see below; 2 files
  recovered from the Utah Public Notice Website where CivicClerk carries a mis-uploaded
  document, see "2026-07-02 repairs"). Index: `minutes_index.csv`. Meetings the
  source still has no recoverable minutes for: `minutes_unrecovered.csv` (**3 rows**).
- `extract_votes.py` — parses recorded roll-call motions → per-meeting JSON + rebuilds
  `all_votes.csv`. Idempotent: re-run any time; it overwrites votes/ and the CSV.
- `validate_votes.py` — checks per-member tallies vs the stated result →
  `votes/_validation_report.txt`.
- `votes/<year>/<week>/<date>_<slug>.json` — structured intermediate (one per meeting).
  `votes/_roster_by_year.json` — per-year council roster derived from attendance + votes.
- `all_votes.csv` — long format, one row per member-vote
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`).

Run order: `python3 extract_votes.py && python3 validate_votes.py`.

## `body` column — governing body that took the vote
`body` ∈ {`Council` (default), `RDA`, `CRA`, `MBA`}. In Vineyard the City Council mostly acts
as the Council; it also holds **separate Redevelopment Agency (RDA) board meetings** (same
members sitting as the RDA board) — slug `redevelopment-agency-board-meeting`. Those motions are
tagged `body=RDA` (**75 rows** across 9 RDA board meetings, 2024–2025). **8 of those 9 RDA minutes
were scanned image-only PDFs recovered via OCR** (pdftoppm 300dpi + tesseract — CivicClerk's
`plainText` returned empty); OCR fidelity is lower than the born-digital council minutes (the
Present/Absent columns can flatten to plain name lists), so per-member RDA roll-calls on those 8
are less precise than the tally/result. Filter `body=Council` for council-only analysis; `body=RDA`
is the TIF / project-area / developer-subsidy ("follow the money") subset.
**RDA now spans 67 dates / 218 motions / 1,058 member-vote rows** — the 15 council-embedded
motions above (`provenance='minutes'`, audited) PLUS **203 standalone RDA-board motions
recovered from Utah Public Notice** (`provenance='pmn_minutes'`, born-digital text — NOT the
OCR set), promoted via `extract_backfill_votes.py` (63 RDA-board meetings; 43 in 2026-07-10,
20 oversize-deferred docs added 2026-07-19). Filter `provenance='minutes'` for the audited-only
RDA slice; `pmn_minutes` is the recovered standalone-board record.

## Roll-call formats (two)
The corpus uses two phrasings; `extract_votes.py` handles both per motion block
(blocks are split on `^Motion:`, case-insensitively — some 2024 minutes write the
header as ALL-CAPS `MOTION:`).

**(A) ALL-CAPS INLINE** (dominant, ~2020–2025):
```
Motion: COUNCILMEMBER X MOVED TO ...  COUNCILMEMBER Y SECONDED THE MOTION.
[ROLL CALL WENT AS FOLLOWS:] MAYOR FULLMER, COUNCILMEMBERS A, B, AND C VOTED
AYE/YES (or VOTED IN FAVOR).  COUNCILMEMBER D VOTED NAY/NO.  COUNCILMEMBER E
ABSTAINED.  COUNCILMEMBER F WAS ABSENT/EXCUSED.  THE MOTION CARRIED UNANIMOUSLY /
CARRIED 3-2 / CARRIED FOUR (4) TO ONE (1) / CARRIED/PASSED WITH ONE ABSENT / FAILED.
```
Parsed **clause-by-clause**: each vote verb (`VOTED AYE/YES`, `VOTED IN FAVOR`/`IN
SUPPORT`/`IN THE AFFIRMATIVE`, `VOTED NAY/NO`, `VOTED IN OPPOSITION`/`AGAINST`/`IN THE
NEGATIVE`, `ABSTAINED`, `WAS/WERE ABSENT|EXCUSED`, `RECUSED`) consumes only the name run
since the previous clause boundary, so a "VOTED NO" clause can't reach back across a
period and swallow the preceding "VOTED YES" names. ("EXCUSED" is treated as Absent.)
The 2024+ "COUNCILMEMBERS A, B, AND C VOTED IN FAVOR" / "MAYOR X AND COUNCILMEMBERS …
VOTED IN FAVOR" form is parsed as an aye list (the mayor is captured when named).

**(B) STRUCTURED** (2026 onward, incl. the OCR files):
```
Motion: Council Member X motioned to ...
Second/Seconded: Council Member Y
Yes: Council Members A, B, and C.   No: None.   Absent: Council Member D.
Motion Passed 5-0.
```
Member lists are whitespace-flattened first (they wrap across lines), then split at the
next label or sentence end. `No: None.` etc. yield empty lists.

## Result / tally parsing
`find_result` recognizes: `Motion Passed/Failed N-N`, `THE MOTION CARRIED/PASSED/FAILED
N-N`, word-number tallies `CARRIED FOUR (4) TO ONE (1)` / `THREE TO TWO`,
`CARRIED/PASSED UNANIMOUSLY`, `CARRIED WITH <word> ABSENT`, and bare `CARRIED`/`FAILED`.
Stored verbatim-ish in `result`, e.g. `4-1 Pass`, `Carried unanimously`,
`Carried with one absent`.

## Does the mayor vote? YES.
Vineyard's mayor is a full voting member of the council, throughout the record. Mayor
Fullmer and Mayor Stratton both appear in roll-call vote lists and have cast dissenting
votes (e.g. **2022-07-13**: Mayor Fullmer VOTED NO on a 3-2 motion). Under the UCA
six-member-council form adopted via Prop 10 (effective Jan 2026), the mayor remains a
voting council member. So `aye`/`nay` lists routinely include the mayor's surname.

## Council size over time (matches election_results cross-check)
Mayor + 4 council (5 voters) 2020–2025; **Mayor + 5 (6 voters) from Jan 2026** (Prop 10).
`votes/_roster_by_year.json` (derived from attendance + vote lists) cross-checks cleanly
against `election_results/vineyard_results_by_candidate.csv`:
- 2020–21: Fullmer(M) · Earnest, Flake, Judd, Welsh.
  (2021 roster shows 7 because Sifuentes & Rasmussen, elected Nov 2021, attended the
  Dec 2021 meeting as councilmembers-elect — legitimate, not an error.)
- 2022–23: Fullmer(M) · Flake, Welsh, Sifuentes, Rasmussen.
- 2024: Fullmer(M) · Sifuentes, Rasmussen, Holdaway, Cameron (2023 winners).
- 2025: Fullmer(M) · Sifuentes, Cameron, Clawson, Holdaway.
- 2026: **Stratton(M)** · Holdaway, Lauret, Wood, McCumber, Nair (Mayor+5; 2025 winners).

## Name normalization
Surnames are canonicalized via `NAME_MAP` in `extract_votes.py`. Known OCR/spelling
variants folded in: `HOLDWAY`/`HOLAWAY`→Holdaway, `MCCUMMBER`→McCumber, `STATTON`→
Stratton, `ERNEST`→Earnest. Role prefixes (Mayor, Mayor Pro Tem(pore), Councilmember,
Council Member) are stripped; tokens that aren't council surnames (staff, residents,
attorneys named in a clause) are dropped, never invented.

## names_recorded convention
A motion gets `names_recorded:true` iff at least one member appears in `aye`/`nay`/
`abstain`. When the minutes give only a tally / "carried unanimously" with **no per-member
list**, lists stay empty and `names_recorded:false` (22 motions). We never back-fill an
"unanimous" vote from the attendance roster — no guessing who voted which way.
NB: in 2026 the clerk lists only the councilmembers by name in roll calls and does **not**
name Mayor Stratton in any vote run, even though the mayor is a voting member. We never
back-fill the mayor into an aye list — so Stratton legitimately has 0 vote rows despite
presiding (he appears in the 2026 roster via attendance). Prior mayor Fullmer **is** named
in roll calls (incl. "MAYOR FULLMER AND COUNCILMEMBERS … VOTED IN FAVOR") and does vote.

## motion_type mapping (12-cat taxonomy)
`classify()` keys on the motion text, checked in priority order:
- Public-hearing open/close → `Public Hearing Action`.
- adjourn / recess / closed session / continue / table / amend-agenda / mayor-pro-tem
  procedural / approve-minutes / consent → `Procedural/Administrative`.
- `ordinance` → `Ordinance`; budget/tax-rate → `Budget Amendment`; grant/CDBG →
  `Grant-Funding`; interlocal/cooperative → `Interlocal`; appoint/nominate/swear →
  `Appointment`; rezone/plat/general-plan/land-use/annex/development-agreement →
  `Land-Use/Zoning`; contract/agreement/purchase/bid/lease → `Contract/Purchase`;
  `resolution` → `Resolution`; proclaim/recognize/honor → `Ceremonial`; else `Other`.
Note: "go into a closed session" motions classify as Procedural/Administrative even though
they're roll-call votes (they are housekeeping, not policy).

## Recovered files & known quirks
- **26 packet-recovered files** (2023-10 .. 2026-05): the CivicClerk `plainText` endpoint
  returned empty at build time, so these were saved as oversized "packet" PDFs and logged in
  `minutes_unrecovered.csv`. They actually carried a **real text layer**, so a local
  `pdftotext -layout` of the saved packet recovered the full minutes — no OCR needed. Their
  `minutes_index.csv` `source_url` points at the CivicClerk `GetMeetingFileStream(fileId=…)`
  PDF; the `.md` header records the recovery method. Source typos seen in these (e.g.
  `CAMREON`→Cameron) are folded into `NAME_MAP`.
- **3 OCR files** (no text layer in source): `2020-09-23_city-council-meeting-regular`
  (scanned copier PDF, recovered in the 2026-07-02 repair), `2026-04-14_city-council-meeting`
  and `2026-04-21_city-council-work-session` (all flagged `format=ocr`). 2020-09-23 parsed
  cleanly (10 motions); 04-14 parsed cleanly (3 motions). 04-21 is a pure work/study session
  with **no recorded votes** (0 motions) — correct, not a parse failure.
- **2026-07-02 repairs** (details in `../VERIFICATION.md`): (a) the CivicClerk minutes
  attachment for event 533 (2020-06-24) is a mis-uploaded copy of the 2020-02-26 minutes —
  the real June 24 minutes were recovered from PMN (`source=pmn` in the index); (b) two
  header-only stub files (2020-09-23, 2023-08-30) were replaced with the real minutes
  (OCR / pdftotext of the source PDFs); (c) the city attached one combined minutes PDF to
  BOTH 2024-04-10 events (regular meeting + budget planning session) — kept once as
  `2024-04-10_city-council-meeting.md` (the document titles itself "MINUTES OF A REGULAR
  CITY COUNCIL MEETING"; its WORK SESSION section covers the budget-planning content).
- **3-meeting gap** (`minutes_unrecovered.csv`): 2025-12-10, 2026-03-10 (both City Council
  Meetings) and 2026-05-19 (Work Meeting). CivicClerk serves a **corrupt / 0-page PDF** for
  these (truncated server-side; unreadable by poppler/Ghostscript/PyMuPDF) and `plainText` is
  empty. PMN was checked as an alternate source. These produce no votes until re-acquired.
- **16 zero-vote meetings**: planning retreats, budget work sessions, town halls, open
  houses, joint study sessions — they legitimately take no formal action. Verified, not
  parse failures.

## Validation result
**1,076 motions across 172 meetings**; **0 motions with an unparsed result**; **2 remaining
tally mismatches**, BOTH SOURCE errors, not parser errors:
- **2024-05-08 m8** (budget adoption): only 4 members present (Rasmussen excused); the
  named roll call is 3 Yes + 1 No, but the clerk wrote "CARRIED FOUR TO ONE". Extraction
  reflects the actual named roll call (3-1); the document's stated tally is wrong.
- **2025-08-26 m3** (open public hearing): "MAYOR FULLMER, COUNCILMEMBERS CAMERON, CLAWSON,
  AND SIFUENTES VOTED YES … CARRIED FOUR (4) TO ONE (1), WITH ONE ABSENT" — actually 4 Yes,
  0 No, Holdaway absent. The clerk's "four to one" sloppily counted the absent member;
  extraction reflects the true 4-0-with-1-absent.
Mid-motion vote changes are handled: when a block contains "CHANGED HER/HIS/THEIR VOTE",
only the FINAL "ROLL CALL WENT AS FOLLOWS" segment is used (1 case: 2022-07-13 m6, a 3-2
where Sifuentes changed abstain→yes — resolves correctly).
