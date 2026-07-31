# Lehi Planning Commission — vote-extraction pipeline

Turns the 160 Lehi **Planning Commission** minutes markdown files (Granicus text layer,
2020–2026) into structured roll-call vote data: one JSON per meeting, a flat
`all_votes.csv`, and a reconstructed commissioner `roster.csv`. Adapted from the council
extractor (`../meeting_minutes/extract_votes.py`), reusing its line-wrap flattening,
footer/watermark filtering, block pairing, tally orientation, and the cardinal
"never guess unanimous/named members" rule.

## Files
- `minutes_index.csv` — 160 meetings (`date,year,title,slug,path,source,source_url,format`).
  (2026-07-02: 2 duplicate same-date Granicus events removed — 2020-02-06 clip279 and 2024-04-25
  clip654 were md5-identical re-publications of clip278/clip653. See ../VERIFICATION.md addendum.)
- `minutes/<year>/<week>/<date>_planning-commission-meeting.md` — source minutes.
- `extract_votes.py` — parses each meeting → `votes/<year>/<week>/<date>_…json`, then
  rebuilds `all_votes.csv` **and** `roster.csv`. Resumable (skips existing JSON); `--force`
  re-extracts all.
- `validate_votes.py` — reads the JSONs → `votes/_validation_report.txt`.
- `all_votes.csv` — long format, **one row per member-vote**, council-identical schema:
  `date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`.
  `title`="Planning Commission" and `body`="PlanningCommission" (exact string the DB keys on)
  for **every** row. `source` = the markdown path.
- `roster.csv` — `commissioner,first_seen,last_seen,n_meetings`.

## Run
```bash
python3 planning_commission/extract_votes.py --force
python3 planning_commission/validate_votes.py
```

## Roster — reconstructed from the minutes (appointed body, no elections)
There is **no fixed elected roster** and **no mayor**; the Chair/Vice-Chair vote like any
member. The roster is rebuilt from the **"Members Present:" / "Members Absent:" headers** in
the minutes (`build_roster()`), folding OCR/short-form variants to one canonical person:
`Abe→Abram Nielsen`, `Greg→Gregory Jackson`, `Kenneth→Ken Roberts`, `Lindsay Gheman→Gehman`,
`Emily Briton→Britton`. Roll-call surname drift is normalized too (`Newell→Newall`,
`Briton→Britton`, `Carlsson→Carlson`, `Petersen→Peterson`, `Nielson→Nielsen`).

**19 commissioners, 2020–2026** (7 seats + 2 alternates; size is NOT fixed — alternates vote
when seated, so roll calls run 4–7 names). **Two distinct people share the surname
"Peterson"** — Jared (2020–2021) and Greg (2020, alternate). They overlap in time but **never
appear in a roll call**, so "Commissioner Peterson" is resolved per-meeting from that
meeting's present-set and **skipped if ambiguous** (never guessed).

Roll-call name matching anchors on the **global** roster surnames, not just that meeting's
present-set: Lehi headers sometimes omit a present member or contradictorily mark a voting
member "Excused", so global anchoring is what catches every real vote (per-meeting present is
used only to disambiguate Peterson).

### Appointment cross-check (informational)
PC appointments are **City Council** votes. `../meeting_minutes/all_votes.csv` has **11**
`motion_type="Appointment"` resolutions for the Planning Commission (2020-01-14 … 2025-12-16),
some naming the commissioner (e.g. **Emily Britton** appointed 2021-09-07; **Beau Jones**
2024-02-13) — the appointment dates corroborate the header-derived first-seen dates. The
roster itself is built from the PC attendee headers.

## Recommendation vs Final Action (the cross-body taxonomy)
The `stage` field + the `result` string distinguish the two, and the result string is
**machine-detectable** (verified: 0 stage/result disagreements):
- **`pc_recommendation`** — plats/subdivisions/rezones/annexations/GPAs forwarded to Council.
  `result` contains the substring **"recommend"** and the **direction**:
  `Positive recommendation 6:0` / `Negative recommendation 3:2`. A failed recommendation
  motion reads `Positive recommendation FAILED 1:4`.
- **`pc_final_action`** — CUPs, site plans, design review, consent, minutes, nominations.
  `result` has **no** "recommend": `5:0 Approved (Final Action)`, `0:5 Denied (Final Action)`,
  or plain `7:0 Pass` for procedural motions.

Direction keys on the **operative/earliest verb** in the flattened Motion line, so a
downstream "denial"/"Conditions of Approval" does not flip an approve motion. When the
**result sentence itself** states the effective disposition (e.g. a 3-3 split "forwarded with
a negative recommendation"), that explicit text is authoritative and overrides the
motion-verb direction (reading the source, not guessing).

Tally convention: `N:N` from the named roll call (or the minutes' printed tally for
tally-only motions), then the direction/disposition words.

## Roll-call format
Per-member inline only (no `YES:`/`NO:` label blocks exist in the PC corpus):
```
Vote: Commissioner Nielsen, yes; Commissioner Peterson; yes; Commissioner Ellis, yes;
… Commissioner Hereth, yes. The motion passed unanimously.
```
Separators drift and are all tolerated: comma, semicolon, the stray semicolon-between-name-
and-vote quirk ("Peterson; yes"), a bare space ("Everett no"), and the 2026 period style
("Gehman, yes."). The block is flattened before parsing; page-continuation headers
(`Lehi City … Planning Commission … <date>`), DRAFT watermarks, address/phone lines, and
standalone page numbers are dropped first. Vote tokens map yes→Aye, no→Nay, plus
Abstain/Recuse/Absent (Excused→Absent). **Tally-only** forms ("passed unanimously",
"four in favor, one against", "failed 2 to 4", "All in favor") set `names_recorded:false`
with an **empty** member list — never a guessed member.

A motion line prefixed by an agenda number (`3.4 Motion: …`) is recognized as a motion, not
an item header. A motion + roll-call that an attorney/recorder **re-reads "for the record"**
(a quoted *prior*-meeting action, not a vote taken now) is skipped — there is **1** such block
(2025-05-22, the Fort Street Partners original approval).

## Motion-type taxonomy
Same fixed 12 categories as council (Land-Use/Zoning checked first). Procedural sub-motions
(nominate/elect, table, continue, recess, minutes, bylaws) are typed from the motion text.

## Validation (`votes/_validation_report.txt`)
**OVERALL = PASS.** Hard invariants (all clean): every row `body="PlanningCommission"`;
**0 off-roster voters**; **JSON↔CSV reconciles** (6,219 member-votes both sides). The
remaining items are **reviewed source anomalies — flagged, never fabricated/auto-fixed**
(mirroring how council handled its 2 source-typo cases):

- **8 tally-vs-result mismatches** — all source omissions/typos where the minutes' own
  printed tally disagrees with its named roll call. The named roll call is authoritative:
  - `2021-07-08` (m2/m8/m9) — the source omits **Ellis's** vote word in *every* roll call
    ("Commissioner Ellis;"), so named is 1 short of the printed 6-1.
  - `2022-10-27 m4` — source omits **Carlson's** vote word ("Commissioner Carlson. The vote
    passed 6-1").
  - `2021-08-12 m10` — source omits **Eyre's** vote word and prints "4-2" against a named 5-1.
  - `2022-04-14 m4` — source prints an impossible "passed **5 – 7**" (typo for 5-2).
  - `2023-10-12 m6` — source lists 5 names but prints "5-1" (a 6th, unnamed yes).
  - `2020-11-12 m5` — roll call names a "Peterson" who is neither Present nor Excused that
    meeting → ambiguous, dropped (cardinal rule), so the lone nay is uncounted.
- **2 outcome-vs-count contradictions** — `2021-05-13 m1` is a legitimate **3-3 split** the
  source "forwarded with a negative recommendation" (captured as `Negative recommendation
  3:3`); `2023-03-09 m6` says "passed unanimously" while naming 3 nay votes (source typo).
- **1 out-of-window voter** — `2022-12-08 m7` names **Roger Ellis** in the roll call although
  that meeting's header lists him **Excused** (his prior meeting was his last as Present).
  He is on the roster; the date is 7 days past his present-window. Traced to source.

## Current corpus stats
160 meetings · 1,089 motions · 6,219 member-vote rows · body {PlanningCommission 1,089} ·
581 recommendations (536 positive / 45 negative) · 508 final actions ·
140 contested · 4 tally-only motions · 19 commissioners ·
8 (source) tally mismatches · 2 outcome contradictions · 1 out-of-window voter · 0 off-roster.

## Known gaps (honest)
- Bare inline procedural motions with **no roll-call label** and no inline outcome are not
  captured (the parser anchors on `Vote:` / inline "motion passed/failed"). Lowest-signal.
- A handful of roll calls **omit a member's vote word** in the source (the 2021-07-08 Ellis
  pattern, etc.); the missing vote is left uncounted rather than guessed — flagged above.
