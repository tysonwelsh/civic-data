# meeting_minutes/ — Emigration Canyon City Council + Metro Township Council votes

Council minutes and extracted narrative-tally votes for the one 5-member at-large body that
governed as a **Metro Township (2017–2024)** then a **City (2024-05-01+)**. Source: **Utah
PMN body 5809**. See the repo-root `CLAUDE.md` for the form-change and PMN-purge context.

## Files
- `minutes/<year>/<date>/<date>_<slug>.md` — **89** docs (2018-10 → 2026-05), born-digital
  text or OCR, with provenance front matter (`**Era:**`, `**Meeting type:**`,
  `**In-body date match:**`). Meeting types: Regular 82 · Workshop 3 · Canvass 2 · Special 1 ·
  Emergency 1.
- `raw/<year>/…pdf|docx` — retained PMN originals (89).
- `minutes_index.csv` — 8-col standard + `meeting_type,pmn_notice_id,pmn_file_id`; `source=pmn`.
- `minutes_unrecovered.csv` — **14** meetings with a PMN notice but no recovered minutes
  (2017 purge + gaps). *(The 3 dates recovered 2026-07-17 were NOT previously listed here —
  the crosscheck engine surfaced them as genuinely-missing, not logged gaps.)*
- `extract_votes.py` (PURE) → `votes/*.json` → `all_votes.csv` + `roster.csv`. `all_votes.csv`
  carries the collection-standard trailing **`provenance`** 14th column since 2026-07-17
  (`minutes` = audited primary harvest | `pmn_minutes` = the 3 PMN-recovered township docs).
- `validate_votes.py` → `votes/_validation_report.txt`.

## PMN-recovered council docs — PROMOTED 2026-07-17 (3 township-era minutes)
The crosscheck engine flagged 3 township-era **[Meeting Minutes]** docs the original PMN pull
missed (leads in `../pmn_backfill/crosscheck_flags.csv`); content-verified as real minutes and
promoted directly into this audited layer (`provenance=pmn_minutes`; the EC-PC precedent —
EC has no CMS, PMN is the only source):
- **2021-01-28** (file 692675, notice 654183) — 1 motion. Header prints "January 28, **2020**"
  (clerk year-typo); the motion approving the Dec 17 2020 minutes + notice date + Thursday
  weekday confirm **2021-01-28**.
- **2021-02-25** (file 717575, notice 660423) — 6 motions incl. a **new contested 4-1** (Bowen
  Nay on the Resolution). *(Its GP-adoption motion "failed **due to** a lack of a second" is
  SKIPPED, not recorded as a Fail — see below.)*
- **2023-01-24** (docx file 950381, notice 808281; `format=docx-text`) — 1 motion (ARPA funds).
  The notice's PDF twin (935045) is the AGENDA — rejected; the minutes are the .docx.
Net: **+8 vote rows, motions 288→296, contested 5→6.** The `LACK_SECOND` guard (which SKIPS
lack-of-second motions, EC's convention) was extended to also match "failed **due to** a lack
of…" (was only "failed **for** lack of…"); zero blast radius — the phrase occurs only in the
2021-02-25 doc corpus-wide.

## `roster.csv` counts ATTENDANCE — the "Others Present" fix (2026-07-29)
`roster.csv` is the **observed per-meeting attendance** aggregate (`first_seen`/`last_seen`/
`n_meetings`), distinct from the seat-tenure intervals in `../roster/council_terms.csv`.
It is built from each meeting's PRESENT block plus that meeting's mover/seconder/named-voter
names. **`parse_present()` used to scan a fixed 500-char window after the `MEMBERS PRESENT`
anchor and credit any roster surname found anywhere in it** — and that window runs straight
through the `Staff Present:` / `Others Present:` sub-blocks. **Gary Bowen left the council
after 2021-12-14** (Pinon appointed to AL-5 2022-01-25) but **attends every city-era meeting
as the Salt Lake County Animal Services Representative/Liaison**, printed under
`Others Present:`. He was therefore credited with **9 phantom meetings** (2024-06-25,
2024-07-30, 2024-09-24, 2024-11-19, 2025-01-28, 2025-05-27, 2025-12-15, 2026-02-17,
2026-04-21), stretching his `last_seen` to **2026-04-21** and `n_meetings` to **46**.
**Fix:** `trim_to_council_block()` cuts the PRESENT region at the first
staff/others/guests/public attendance label — but **only at a label that already has a
roster surname before it**. That guard is load-bearing: the **township-era minutes are
TWO-COLUMN** (`COUNCIL MEMBERS ELECRONICALLY PRESENT:` | `OTHERS IN ATTENDANCE:`), so
flattening puts the *label* ahead of every name and a blind cut would drop the whole
council. Result: **9 of 89 meetings changed, all 9 removing only Gary Bowen, each still
yielding the full 5-member roll**; no other member gained or lost a meeting. Bowen →
`2018-10-25..2021-12-14, 37 meetings`, matching `../roster/` AL-5 and the primary present
blocks (2021-12-14 lists `GARY BOWEN`; 2022-01-25 lists `ROBERT PINON` in his place).
*(Further corrected 2026-08-01 to `2018-11-29..2021-12-14, 36 meetings` — Bowen is printed
under `COUNCIL MEMBERS EXCUSED:` on 2018-10-25; see the next section.)*
**The VOTE layer was never affected** — `all_votes.csv` is byte-identical across the fix
(Bowen's last mover/seconder/vote row is 2021-12-14; his one named vote is the 2021-02-25
Nay), as are `motions_std.csv`, `db/civic.db` and `weeks/`.

## …and the ABSENT/EXCUSED half of the same bug (fixed 2026-08-01)
The "Others Present" fix cut the *non-council* attendees out of the PRESENT window. It did
**not** cut the second COUNCIL roll: every EC attendance header prints the seated members
**and** the ones who did not attend — `COUNCIL MEMBERS EXCUSED:` / `COUNCIL MEMBER EXCUSED:`
(township), `Council Members Absent:` / `Council Member(s) Absent:` (city), `CANVASSERS
EXCUSED:` (canvass nights). Those labels are not in `NONCOUNCIL_BLOCK_RE`, so **every absent
member was credited as PRESENT** — all 89 meetings read as a full 5-member roll, including
2026-02-17, whose motions print *"3-0 … with Council Members Hawkes and Pinon absent from the
vote."*

**Fix:** `parse_absent(body)` reads the absent roll from the **line-structured** body (not the
flattened text) and `parse_present()` subtracts it. The line structure is load-bearing because
the two layouts are only told apart by their blank lines:
- **STACKED** — `PRESENT:` ‹names› `EXCUSED:` ‹names› (`OTHERS IN ATTENDANCE:`). The absent
  names follow their own label, so they are the run of roster-name lines after it.
- **TWO-COLUMN** — `Council Members Present:` and `Council Members Absent:` are side-by-side
  column HEADS; flattening puts both labels ahead of every name and the two columns arrive as
  blank-line-separated groups (present first, absent second). An empty Absent column simply
  yields one group.

The layouts are distinguished exactly the way `trim_to_council_block()` does it — **a roster
surname printed BETWEEN the two labels means the block is stacked**. The step is strictly
restrictive (it can only REMOVE names) and is guarded: if the removal would empty the roll it
is discarded as a misparse.

**Result: 23 of 89 meetings changed** (2018-10-25, 2019-11-19, 2020-02-27, 2021-09-28,
2022-03-22, 2022-04-28, 2022-10-25, 2022-11-15, 2023-03-28, 2023-04-12, 2023-05-23,
2023-06-27, 2023-07-25, 2024-02-22 ×2, 2024-04-23, 2024-07-30, 2025-05-27 ×2, 2025-11-17,
2025-11-18, 2025-12-15, 2026-02-17), each dropping the 1–2 members the clerk printed as
absent. `roster.csv` attendance: Hawkes 89→82, Harris 72→61, Brems 89→84, Smolka 83→82,
Pinon 52→51, Bowen 37→36 (Brems and Bowen also lose 2018-10-25 as `first_seen` → 2018-11-29).
**The VOTE layer is again untouched** — `all_votes.csv` byte-identical, `motions_std.csv`,
`db/civic.db` (438 motions / 13 votes) and the weekly vote sums all unchanged. The bug
over-credited attendance; it never fabricated a vote.

**Independent cross-check:** with absentees removed, **no printed tally exceeds the number of
members recorded present — 0 violations across 297 motions** (before the fix every meeting
read 5-present, so the check was vacuous). And in 22 of the 23 changed meetings the absent
member never speaks in the narrative.

**The one exception is a SOURCE contradiction, left city-faithful — 2023-06-27:** the header
prints `COUNCIL MEMBERS EXCUSED: DAVID BREMS` but the body has Brems speaking 12 times and
**moving Ordinance No. 2023-06-01** (its present/excused block is a copy of the prior
2023-05-23 meeting's — a clerk error). Nothing is overwritten: `build_roster()` unions the
present block with that meeting's movers/seconders/named voters, so Brems is correctly
retained for 2023-06-27 while the printed header stands as-is.

`mayor_voted` in the JSON is now also absent-aware (`mayor is not None and mayor not in
absent`). Zero blast radius today — no meeting both detects a mayor and lists him absent —
but it keeps the flag honest.

**The PC has no equivalent fix and must not get one.** `planning_commission/` minutes record
attendance as a checkbox MATRIX (`Commissioners` / `Public Mtg` / `Business Mtg` / `Absent`
columns with `x` marks) whose column-to-name mapping is destroyed by PDF text extraction: all
59 "Absent" occurrences in the PC corpus are the column *header*, never a named commissioner.
Attributing an `x` to a name would be fabrication, so PC `roster.csv` honestly lists every
commissioner on the sheet. Recorded as a source ceiling in `../VERIFICATION.md` §7.

## THE MAYOR VOTES — max tally 5 (the key structural fact)
Peer-selected mayor is one of the five and **votes** (Millcreek pattern). A complete tally
tops out at **5**. `validate_votes.py` confirms no printed tally exceeds 5. The presiding
mayor is **detected per-document** from the PRESENT block (**Joe Smolka** township era →
**David Brems** city era), never hard-coded to a date.

## Vote extraction (`votes/_validation_report.txt`)
89 meetings · **297 motions** (291 tally-only · 6 named-dissent/roll) · **6 contested**
(the 5 below + 2021-02-25 Bowen Nay 4-1, recovered 2026-07-17) — historical note, the
pre-2026-07-17 record was: 86 meetings · 288 motions · 5 contested
(2021-04-27 Brems RECUSE; 2021-08-24, 2021-12-14 Smolka/Harris abstain 4-1; 2023-08-22
full 5-name roll, Harris nay; 2023-10-24 Smolka nay 4-1 — recount 2026-07-12 T3.1(k)) ·
off-roster names **0** · CSV==JSON **OK**. `result`/`motion_type` are verbatim/native. **13
meetings have 0 extracted motions** — mostly genuinely light meetings (emergency mudslide
discussion, brief specials) plus **2 OCR-quality gaps** (2024-02-22, 2025-01-28 scanned
approved minutes whose motion sentences didn't survive OCR — the raw PDF is retained;
born-digital re-fetch is a TODO). These are honest, never fabricated.

## Grammar handled (see extract_votes.py docstring)
City form `"<Name> moved to … <Name> seconded the motion; vote was N-M[, unanimous | ,
<Name> opposed]"`; township form `"<Name>, seconded by <Name>, moved to … The motion passed
[unanimously | N to M, showing <Name> voted in opposition/abstained]"`. Unanimous → one
tally-only row (blank member). Named dissent → the named Nay/Abstain row only.

**Seconder-label variant `second by` (fixed 2026-07-19):** one township doc (2019-06-19) writes
the label `second by` (no `-ed`) instead of `seconded by`, which is part of the township
mover-ANCHOR — so the whole motion (`approve the use of the Stormwater Maintenance Agreement
form…`, Brems moved / Paine seconded, passed unanimously) was silently DROPPED, not just its
seconder. `TWP_RE` now accepts `second(?:ed)?\s+by`; this recovered exactly **1 motion**
(counts 296→297; `second by` occurs once corpus-wide, so the change is strictly additive — the
recovered motion sorts first in the 2019-06-19 meeting, renumbering that meeting's other three
motions, with no other row altered). Analog of the PC `2nd by:` seconder fix done the same wave.

## Run
`python3 extract_votes.py [--force]` then `python3 validate_votes.py`. `all_votes.csv` is
RFC-4180 (motion text has commas) — read with a real CSV parser.
