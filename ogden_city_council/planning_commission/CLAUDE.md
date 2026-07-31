# planning_commission/ — Ogden City Planning Commission vote extraction

Pipeline that turns **140 Planning Commission minutes** markdown files (2020–2026) into
structured roll-call vote data. Entry point: **`extract_votes.py`** (PURE PYTHON/REGEX —
no LLM, no network); QA via **`validate_votes.py`**. The old "2020–2023 PC coverage is
sparse" gap was **CLOSED 2026-07-19** — see "The 2026-07-19 gap recovery" below.

The Planning Commission (PC) is a separate body from the City Council. It **recommends**
land-use legislation to the Council (rezones, zoning/general-plan amendments, subdivisions,
annexations, street vacations) and takes **final action** on its own delegated approvals
(conditional use permits, design review, site plans).

## What's here

| Path | Role |
|------|------|
| `minutes/<year>/<week-monday>/<date>_planning-commission-meeting.md` | Source minutes. Immutable input. |
| `minutes_index.csv` | Index of the 140 files (`date,year,title,slug,path,source,source_url,format`). `format ∈ {text, ocr}`. Two dates (2021-08-18, 2021-12-15) carry BOTH a `planning-commission-meeting` (special/business) row and a sibling `planning-commission-work-session` row — distinct slugs, no path/JSON collision. |
| `minutes_unrecovered.csv` | Honest-gap ledger (now just the not-yet-posted 2026-07-01). |
| `vote_corrections.csv` | **Documented vote corrections** applied by `extract_votes.py` post-parse (see below). Never silent: every row cites its city source. |
| `raw/` | Retained source documents for the 2026-07-19 recoveries (born-digital PDFs, one .docx, two packet carves). |
| `extract_votes.py` | Parser. Reconstructs the roster, emits one JSON per meeting, rebuilds `all_votes.csv` + `roster.csv`. |
| `validate_votes.py` | QA: off-roster check, JSON↔CSV reconcile, tally mismatches, per-year voters, appointment cross-check. Writes `votes/_validation_report.txt`. |
| `votes/<year>/<week>/<date>_planning-commission-meeting.json` | Structured intermediate, one per meeting. |
| `votes/_validation_report.txt` | Validation output. |
| `all_votes.csv` | Long format, one row per member-vote. `body="PlanningCommission"`, `title="Planning Commission"` on every row. Authoritative analysis table. |
| `roster.csv` | Reconstructed commissioner roster (`commissioner,first_seen,last_seen,n_meetings`). |

## Run

```bash
python3 planning_commission/extract_votes.py            # full re-parse, rebuilds all_votes.csv + roster.csv
python3 planning_commission/extract_votes.py --rebuild  # rebuild CSV from existing JSONs only
python3 planning_commission/validate_votes.py           # writes votes/_validation_report.txt
```

## Schema

`all_votes.csv`: `date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source,provenance`
— identical 14-column schema to `meeting_minutes/all_votes.csv` (the trailing `provenance`
column was added 2026-07-19 — see "Recovery-channel provenance" below). One row per (motion × member).
`vote ∈ {Aye, Nay, Abstain, Absent, Recuse}`. A tally-only motion (`names_recorded:false`)
emits **one** row with empty `member`/`vote` so the motion is still represented.
`body` is **always** `PlanningCommission` (the PC does not sit as RDA/MBA).

## TWO source formats (the central design constraint)

| Years | Format | Motion / vote phrasing |
|-------|--------|------------------------|
| 2020–2023 (+4 files in 2024) | **born-digital, mixed case** | `MOTION: A motion was made by Commissioner Garner to recommend approval … Motion was seconded by Commissioner Graf and passed unanimously, with Commissioners Blaisdell, Boykin, … and Southwick voting aye.` / `… passed 7-1 with Commissioners … voting aye and Commissioner Graf voting no.` |
| 2024–2026 | **OCR'd, UPPERCASE roll-call** | `COMMISSIONER X MOVED TO … MOTION WAS SECONDED BY COMMISSIONER Y AND PASSED UPON BY THE FOLLOWING ROLL CALL VOTE: VOTING AYE — COMMISSIONERS AABERG, ROSS, … AND CHAIR SHINODA. VOTING NO — NONE.` / `COMMISSIONER X MADE A MOTION TO … COMMISSIONER Y SECONDED THE MOTION, ALL VOTING AYE.` |

The parser detects motions by anchoring on `motion was [then/again] made by` (born),
`MADE A MOTION`, and `MOVED` (OCR), windows each motion to the next anchor, and tries both
the OCR named-roll-call parser and the born-digital `with Commissioners … voting aye [and …
voting no]` parser.

## CARDINAL RULE — never fabricate

Tally-only forms — OCR `ALL VOTING AYE` / born `passed unanimously` with **no enumerated
member list** — record the tally with `names_recorded:false` and **empty** member lists.
Members are never guessed (e.g. we do NOT infer "absent" from the attendance header minus the
roll-call; people present can step out for a single vote). 341 of 988 motions are tally-only.

## Roster reconstruction (`build_roster`)

The roster is built **at runtime** from the `Members Present` / `Members Excused` headers of
all 138 meetings — no hard-coded names. Surnames are folded to a canonical display name; OCR
variants are merged by an **OCR-tolerant similarity** (`_sim`): ordered-overlap ratio, with a
near-identical letter-multiset (≥0.92, length within 1) rescue for transpositions
(`AHKMEDOV`↔`AKHMEDOV`). The multiset rescue is tightly guarded — without the 0.92+length
gate it over-matches prose anagrams (`FOREST`/`stores`/`Others` all share `STOKER`'s letters,
which earlier produced a phantom "Stoker" vote). **19 distinct commissioners 2020–2026**:
Sandau, Shale, Shinoda, Southwick, Safsten, Aaberg, Blaisdell, Akhmedov, Williams, Ross,
Graf, Schade, Humphreys, Garner, Stoker, Boykin, plus the **early-2020 cohort recovered
2026-07-19**: Janith Wright, Robert Herman, Angel Castillo (all present Jan–Mar 2020, gone
by the 2020-04-15 meeting when Boykin/Garner/Safsten/Stoker first appear — real turnover,
appointed before the 2020 data floor so no council appointment vote exists in-repo).
The capture stops at a "City Council" sub-heading so the 2020-10-22 East Central Town
Meeting's council attendees don't leak into the PC roster.

### Name matching in vote blocks — connector-aware (`names_from_segment`)

A surname is accepted from an AYE/NO segment **only when it directly follows a connector**
(`COMMISSIONER(S)`/`CHAIR`/`VICE`/`AND` or a comma/colon/period/dash). This captures clean
comma lists *and* multi-dissenter NO lists interleaved with explanation prose
(`VOTING NO — COMMISSIONER AABERG, STATING … AND COMMISSIONER ROSS, WHO FELT … .`) while
never picking up a surname that merely appears inside narrative text. Period is treated as a
separator because OCR writes `GARNER. SANDAU` for `GARNER, SANDAU`.

### Roll-call wrap handling (the known Ogden line-wrap pitfall)

AYE and NO segments are captured **independently**, each spanning line breaks (`[\s\S]`).
- **AYE** runs to the next `VOTING NO` or the sentence period. It does **not** stop on a blank
  line: OCR routinely injects a blank line right after `COMMISSIONERS` and before the names,
  which would otherwise truncate the entire list.
- **NO** runs to the first sentence period (cap 500 chars) so a multi-dissenter list with prose
  reaches its terminating period; `VOTING NO — NONE` = no nays.

## `result` — recommendation vs final action (machine-detectable)

`result` encodes both the disposition and the body's role:

| `classification` | `result` form | When |
|------------------|---------------|------|
| `recommendation` | `Positive recommendation N:N` / `Negative recommendation N:N` | Rezone, Zoning Text/General Plan Amendment, Subdivision/Plat, Annexation, Street/Alley Vacation — **OR** any motion with an explicit "recommend approval/denial … to Council" verb. These go to the City Council, which finalizes the ordinance. |
| `final` | `N:N Approved (Final Action)` / `N:N Denied (Final Action)` | Conditional Use Permit, Design Review, Site Plan, and other PC-delegated approvals. |
| `procedural` | `N:N Pass` / `N:N Fail` | Agenda, minutes, public-hearing open/close, officer elections, table/continue/postpone/recess/withdraw, adjourn. |

`N:N` is `aye:nay` from counted names; when names are not recorded it is the clerk's explicit
tally (`passed/failed 7-1`), or `unanimous`, or `recorded`.

**Disposition logic.** `effective_positive = (motion_is_approval == motion_passed)`, so a
motion *to deny* that **fails** is a Positive recommendation/Approval (the request was not
denied), and a motion *to approve* that **fails** (incl. a tie) is a Denial. Classification by
subject matter (`motion_type`) is required because the OCR-era clerk often writes "MOVED TO
APPROVE THE ZONING CHANGE" with **no** "recommend" keyword even though the PC can only
recommend rezones to Council; and the recommend keyword alone is unreliable ("subject to staff
*recommended* conditions" is not a recommendation-to-Council). `motion_type` checks the
specific petition type **before** generic plan/ordinance language, because boilerplate findings
("consistent with the General Plan", "comply with land use ordinances") appear in nearly every
motion and would otherwise mis-type a CUP as a zoning amendment.

## Coverage + validation (last run, 2026-07-19)

- **140 meetings · 988 motions · 4,764 member-vote rows (5,104 CSV rows) · 2020–2026.**
  (140 = 138 + the 2 sibling work-session docs ingested 2026-07-19 — both discussion-only,
  0 motions, so all_votes is byte-unchanged.)
- Classification: **310 recommendations · 298 final actions · 380 procedural.**
- Vote distribution: **Aye 4,491 · Nay 264 · Recuse 5 · Abstain 4.** **150 contested
  motions** (any named Nay/Recuse/Abstain). The 2026-07-19 "wit"→"with" parser fix
  (2020-05-06 m9) recovered 9 attributions (8 aye + Safsten nay); m9 was already
  tally-contested (printed 8-1) so cities.db `v_contested_all` membership is unchanged —
  only its `named_*` columns now populate.
- **340 tally-only** motions (`names_recorded:false`) — record notes, no enumerated members.
- **0 off-roster members.** JSON↔CSV motions and rows reconcile exactly.
- 31 meetings yield zero vote rows — work sessions / the 2020-10-22 town meeting, which
  record discussion but no motions (a meeting with no motions emits no all_votes rows). The
  2026-07-19 count is 31 = 29 + the 2 sibling work-session docs (2021-08-18, 2021-12-15).

### Tally mismatches (8, honest — all flagged by the validator)
All are **source defects preserved verbatim** (never papered over):
- **Member-in-both-lists (unrecoverable):** `2020-07-01 m9` (Stoker in aye AND nay, stated
  5-3 — aye kept, duplicate nay dropped, third dissenter unrecoverable) and `2020-03-04 m11`
  (Graf printed in BOTH lists of a "passed 5-3"; 8 members present, so the third No is
  probably the unlisted Wright — but that would be a guess, so it is not made).
- **Clerk omitted a name from the printed list** (stated tally counts one more voter than the
  list names): `2020-09-02 m11`, `2020-12-02 m8`, `2021-01-20 m7`, `2021-08-04 m8`,
  `2023-09-06 m6` — the extra voter is unattributable, honest gap.
- **Stated tally contradicts a fully-printed list:** `2023-05-17 m1` (8 named ayes + 1 named
  no vs stated "passed 7-2") — both kept verbatim, flagged.

### `vote_corrections.csv` — the documented-corrections hook (2026-07-19)
The born-digital drafts contain a recurring clerk-typo class where a FAILED motion prints
**both** name lists as "voting aye" (the second list should read "voting no"). Left as
parsed this reverses outcomes (the parser sees only the first list → `3:0 Pass`). Corrections
are applied **only** from `vote_corrections.csv`, each row citing its city source; the
minutes markdown stays verbatim; a snippet matching ≠1 motion is refused (warns). Classes:
- **Official approved correction** — `2021-11-03` honorary-street-name denial (the audited
  2021-12-01 minutes approve the Nov 3 minutes *with the correction* "three aye and five no").
- **Arithmetic-forced both-aye typo** — `2022-03-02` ("failed 2-4", both lists "aye";
  ratified as-prepared 2022-04-06), `2023-12-06` ("failed 3-6", both lists "aye").
- **Punctuation dropout / misspelling** (the name IS verbatim in the printed list but a
  missing comma or a misspelling hid it from the connector-aware parser): `2020-03-04 m7`
  ("Castillo Sandau"), `2022-03-02 m11` ("Safsten Southwick"), `2023-08-02 m8` ("Grad"=Graf).

## The 2026-07-19 gap recovery (the 2020–2023 "sparse coverage" era)

**63 net-new meetings ingested** (+543 motions / +2,955 named member-vote rows / 95 newly
visible contested motions): all 62 dates of the old `minutes_unrecovered.csv` 2020–2023
ledger except 2020-08-26 (see below), plus the newly discovered **2020-10-22 East Central
Town Meeting** (PC quorum, approved by the PC 2020-11-04, no motions). Channels:
- **Standalone born-digital draft minutes on DocumentCenter** (60 of 63): the clerk posted
  each meeting's "Unofficial draft ..." as its own small PDF (40–220 KB) ~3–4 weeks after
  the meeting, alongside the next meeting's packet materials. Found via the CivicPlus site
  search (`/Search/Results?searchPhrase=<Month D>` — full-text-indexes DocumentCenter) plus
  View-ID neighborhood probes (the 301 redirect leaks each doc's title slug).
  2022-09-07 is served as a **.docx** (extracted with textutil; raw retained).
- **Embedded in the following meeting's full agenda packet** (2 of 63): 2020-04-15 (carved
  from the May 6 packet, View/12522 pp.2–21) and 2021-11-03 (carved from the Dec 1 packet,
  View/18220 pp.2–13). Carved page ranges are in each file's provenance header.
- **Approval verification (the alta precedent), 100% closed:** every recovered meeting's
  minutes are approved by a later meeting's minutes (audited or recovered), evidence quoted
  in each markdown's provenance comment. All "as prepared" except: 2020-03-04 (approved as
  corrected — a Boykin attendance-list spelling only), 2021-05-05/-19 (the posted copy IS
  the revised version approved 2021-06-02), 2021-11-03 (approved with the vote correction
  above).
- **In-body year/date typos** (all documented in provenance headers, dated from approval
  chains + posting batches): 2020-01-08 prints "2019", 2020-01-15 prints "February 15",
  2020-10-22 prints "2022", 2021-11-03 prints "November 4", 2022-01-05 prints "2021",
  2023-04-19 prints "2021".
- **2020-08-26 is NOT a PC meeting** — removed from the gap ledger: the AgendaCenter item
  labeled "Ogden City Planning Commission Meeting Agenda 2020-08-26" (packets dataset,
  `raw/PlanningCommission/2020-08-26_1013.pdf`) is in-body a **Board of Zoning Adjustment**
  agenda (portal label lies). No PC approval chain ever references an Aug 26 meeting
  (2020-09-02 approves Aug 5 + Aug 19; 2020-10-07 approves Sep 2 + Sep 16).

### Recovery-channel provenance (`provenance` column, 2026-07-19)
The 63 recovered meetings came from a NEW channel — unofficial DRAFT minutes — so their
rows are tagged distinctly from audited portal minutes and are filterable apart (audit
F3). The trailing `all_votes.csv` `provenance` column (threaded into db `motion.provenance`
and `cities.db`) takes three values here:
- **`doccenter_draft`** — standalone CivicPlus DocumentCenter "Unofficial draft" minutes
  (incl. the 2022-09-07 .docx and the 2020-10-07 draft-in-packet). **525 motions / 3,008
  member-vote rows** (64 files, 40 with motions).
- **`packet_carve`** — carved from a following-meeting agenda packet: **2020-04-15** (May 6
  packet) and **2021-11-03** (Dec 1 packet). **34 motions / 206 rows** (2 files).
- **`minutes`** — audited portal minutes (everything else, incl. the OCR 2024–2026 era):
  429 motions / 1,890 rows.

Ledger source of truth: each recovered markdown carries a `<!-- provenance: … Recovered
2026-07-19 … -->` header (the 2 packet files say "agenda-packet carve"); audited files have
NO such comment. `extract_votes.py` reads that header (`classify_provenance`) — channel-keyed,
so a future same-channel recovery tags itself; no hand-maintained date list. Approval is
verified downstream (so trust is high) but a `provenance='minutes'` filter now honestly
excludes these draft-sourced recoveries.

### Appointment cross-check
Cross-referenced against `meeting_minutes/all_votes.csv`: **15 of the 19** roster commissioners
appear by name in a Council appointment/reappointment motion that mentions "Planning
Commission". The **4 not matched (Castillo, Wright, Herman, Shale)** are expected honest
non-matches, not extraction defects: Castillo, Wright, and Herman are the early-2020 cohort
appointed *before* the 2020 data floor (no in-repo Council appointment vote exists), and Shale
appears in Council motions only in multi-board text that doesn't co-locate the literal phrase
"Planning Commission". All four are genuine commissioners (confirmed by attendance across many
meetings). Shinoda — flagged as unmatched in an earlier build — is now among the 15 confirmed.

## Defaults chosen (documented, not asked)
- `body` is fixed to `PlanningCommission` (PC never convenes as RDA/MBA).
- Absent/Abstain are **not** inferred from the attendance header (cardinal rule).
- A name appearing in both aye and nay (source error) is kept in aye, dropped from nay.
- Motion text is trimmed to the substantive action (preamble + seconder clause removed), capped
  at 600 chars.
