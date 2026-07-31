# Vineyard roster — independent adversarial audit

**Auditor:** independent QC pass (did NOT build the roster).
**Date:** 2026-07-11.
**Scope:** `roster/council_terms.csv`, `district_versions.csv`, `roster_overrides.csv`,
`build_roster.py`, `roster/CLAUDE.md`, ground-truthed against
`election_results/vineyard_results_by_candidate.csv`, `meeting_minutes/minutes/**`,
root `cities.db`, and `meeting_minutes/minutes_unrecovered.csv`.
**Method:** re-derived every tenure from source; quoted the minutes; re-ran vote-bounds
from `cities.db`; programmatic structural-invariant checks.

**Verdict: the roster is substantially CLEAN — no fabricated names, no phantom/dropped
tenures, no overlaps, correct seat count, correct person disambiguation.** The only
material issue is a **confidence mis-calibration on the AL-A2 (Cameron→VACANT→Nair)
chain**, where a `high` label contradicts the builder's OWN stated confidence model and
the row's own note. Details below.

---

## What ground-truthed CLEAN (verified against source)

- **Clawson (AL-B2) appointment — fully on-disk, exactly as claimed.**
  `minutes/2024/2024-11-11/2024-11-13_city-council-meeting.md` present-list = Fullmer,
  Cameron, Holdaway, Sifuentes — **Rasmussen ABSENT** — and resident *"Daria Evans …
  thanked councilmember Rasmussen for her service"* (line 54). The
  `2024-11-20_city-council-meeting-special-session.md` item 2.1 *"Vineyard City Council
  Vacancy"* interviewed 20 applicants (Clawson listed **#5**, Nair **#10** — the note's
  "applicant #10" claim is verbatim-correct) and *"voted by means of a secret ballot. The
  voting results were: three (3) votes for Brett Clawson (winner) and two (2) votes for
  Kimberly Olsen … Ms. Spencer swore in Brett Clawson as the new councilmember."* The
  `2024-12-11` present-list confirms the swap (Cameron/**Clawson**/Holdaway/Sifuentes).
  `cities.db`: Clawson first Council vote **2024-11-20**. Clawson then ran in the 2025
  general and LOST (rank5 of 6, **998 votes** — election CSV confirms). Every element of
  the AL-B2 chain is source-attested. **`high` fully justified.**
- **Nair seated / Cameron departed (the FACTS).** `2026-01-14` present-list = Mayor
  Stratton + McCumber, Wood, Holdaway, Lauret, **Nair**; **Sara Cameron and "Former
  councilmember Brett Clawson" appear only in "Others Speaking" as residents.** Nair lost
  the 2025 general (rank4, 1002 votes) yet sits as a councilmember ⇒ he MUST be an
  appointee. `cities.db` Nair first Council vote **2026-01-14**. The *fact* of
  Cameron-out / Nair-appointed is high-confidence and correct.
- **Stratton = MAYOR, no phantom council tenure.**
  `2026-02-03_city-council-meeting-special-session.md`: *"MAYOR STRATTON AND
  COUNCILMEMBERS NAIR, LAURET, WOOD, HOLDAWAY, AND MCCUMBER VOTED IN FAVOR"* — this is
  why `cities.db` shows Stratton with exactly **2 Council-body votes on 2026-02-03 only**.
  Roster attaches them to the `MAYOR` row; no council seat invented, none wrongly dropped.
  Election CSV: Stratton def. Sifuentes **1417–1173 (54.71%)**. Correct.
- **Fullmer = MAYOR, not double-counted.** `cities.db`: Fullmer = Council **973** + RDA
  **146** votes. Roster places her only in the `MAYOR` seat (two terms); no council
  tenure exists for her. Her 973 "Council-body" rows are legitimate voting-mayor roll-call
  participation. Correct.
- **Jan-2026 4→5 expansion + McCumber 2-yr-by-lot.** Election CSV: 2025 general was
  **Vote-for-3** — McCumber (1460, rank1), Wood (1389, rank2), Lauret (1348, rank3) won.
  `election_results/CLAUDE.md` (lines 75, 94, 168-169) + Daily Herald confirm McCumber
  **drew the 2-year term by lot** to stagger the new 5th seat. 2026-01-14 present-list = 5
  councilmembers + mayor. Seat count and McCumber's AL-C bound (Jan-2026→Jan-2028) correct.
- **Sifuentes ran for MAYOR (not council) in 2025 and lost.** Election CSV confirms
  (Mayor race, 1173). Council term correctly ended Jan-2026, end_event `did-not-run`.
- **Election reverse-crosscheck (I ran it by hand): every `is_winner=Y` GENERAL winner
  maps to a tenure** — 2019 Welsh/Flake, 2021 Fullmer/Sifuentes/Rasmussen, 2023
  Holdaway/Cameron, 2025 Stratton/McCumber/Wood/Lauret. Appointees (Clawson, Nair) and
  pre-floor holders (Earnest, Judd) correctly carry NO winner row. No fabricated winners.
- **Structural invariants — all PASS:** 18 rows (16 person-tenures + 2 VACANT);
  15 high / 3 medium / 0 low; **0 rows missing sources or confidence; 0 overlapping
  tenures per seat_id; 0 unfilled gaps** (VACANT rows fill both departures). person_keys
  distinct: two Jacobs kept apart (`jacob_holdaway` / `jacob_wood`); `cristy_welsh`
  distinct; Fullmer's two mayoral terms share one key (correct). The 3 `medium` rows are
  exactly the pre-floor 2017-cohort holders (Earnest AL-B1, Judd AL-B2, Fullmer Mayor-term1),
  honestly flagged.
- **`district_versions.csv`** — correctly degenerate (one At-Large row); annexation
  caveat honest; no fabricated ward boundaries.

---

## FINDINGS

### F1 — AL-A2 VACANT row is `high` but violates the builder's own confidence model — **DEFECT**

**Row:** `AL-A2, VACANT, 2025-10-22 → 2026-01-14, confidence=high`.

`build_roster.py` (lines 36-39) defines the model:
> `high` = anchored to an election result OR a **minutes-documented** appointment/oath/vacancy
> `medium` = inferred from a pre-floor staggered cycle, **or bounded by documented service
> across an un-recovered minutes gap**

The AL-A2 vacancy is the textbook `medium` case, and the row's **own note says so**:
> *"the VACANT window is documented-service-bounded, not exact (**medium on the dates**, high on the fact)."*

Evidence it is NOT minutes-documented:
- `minutes_index.csv` jumps straight from **2025-10-22** to **2026-01-14** — there are
  **no recovered Nov/Dec-2025 council minutes**, and **2025-12-10 is in
  `minutes_unrecovered.csv`**.
- `grep -riE 'cameron.*resign|resign.*cameron|cameron.*vacat'` over all minutes → **zero
  hits.** Cameron's resignation is documented nowhere on disk; the fact rests entirely on
  `election_results/CLAUDE.md` cross-check + the `vineyardutah.gov` council page +
  Ballotpedia (all off-disk web sources) plus the logical inference from Nair being a
  2025 loser.

Contrast **AL-B2 VACANT** (Rasmussen→Clawson), which is *correctly* `high`: a **recovered
minutes file inside the window (2024-11-20)** declares the vacancy and documents the
appointment + swearing-in. The two VACANT rows have **asymmetric evidence but identical
`high` labels** — that asymmetry is the calibration error.

**Recommended fix (via `roster_overrides.csv`, then regenerate — do NOT hand-edit the CSV):**
set the **AL-A2 VACANT row confidence = `medium`**. This aligns the label with (a) the
builder's stated model, (b) the row's own note, and (c) the treatment of every other
gap-inferred row in the table.

### F2 — Cameron `resigned` end-confidence overstated — **DEFECT (same family as F1)**

**Row:** `AL-A2, Sara Cameron, 2024-01-10 → 2025-10-22, end_event=resigned, confidence=high`.

Cameron's **elected start** (2023 RCV winner, 907 final-round) and **documented service
through 2025-10-22** (present + voting; `cities.db` last vote 2025-10-22) are high. But the
**`resigned` mechanism and the vacate_date are not minutes-documented** (no farewell, no
vacancy declaration on disk — unlike Rasmussen, who has an on-disk farewell). By
weakest-link, a row that bundles a high start with a gap-inferred end should read `medium`,
or the note must own the split. The note *does* say *"medium on the dates, high on the
fact,"* so this is milder than F1, but the `high` column still reads as fully-attested when
the departure is inference-only.

**Recommended fix:** downgrade to `medium` (preferred, consistent with F1), OR leave `high`
only if the note's "medium on the dates" caveat is considered sufficient disclosure. At
minimum F1 and F2 should be resolved together.

### F3 — 2024-11-20 present-list re-lists the already-departed Rasmussen — **NIT (source quirk; roster handles it correctly)**

The `2024-11-20` special-session present-list header still shows *"Councilmember Amber
Rasmussen"* — on the very day her successor is appointed. She is **absent from that
meeting's roll-call vote** (the Resolution 2024-34 roll names Cameron/Clawson/Sifuentes/
Holdaway + Mayor, not Rasmussen). So the header is a **stale agenda template**, and the
roster **correctly** treats Rasmussen as departed before 2024-11-20 (vacate_date 2024-11-13,
the first-absent + farewell meeting). No fix needed — but see hardening rec C5: a
vacate_date should be corroborated against the *vote* lists, not the present-list header,
which Vineyard sometimes leaves stale.

### F4 — roster/CLAUDE.md prose "present and voting through 2024-10-09" — **NIT**

The narrative says Rasmussen is *"present and voting through 2024-10-09."* She **was
present** 2024-10-09 (present-list confirms; "rasmussen" appears 19× in that file), but her
**last recorded Council vote in `cities.db` is 2024-09-25** (4 votes; none on 10-09). The
CSV is correct (`last_vote=2024-09-25`); only the prose over-reaches on "voting." Minor.
*(Aside for the votes pipeline, not the roster: 19 Rasmussen mentions on 2024-10-09 with 0
extracted votes may be an under-capture worth a spot-check — out of roster scope.)*

### F5 — Fullmer's two MAYOR rows carry identical person-level vote bounds — **NIT**

Both Fullmer rows show `first_vote=2020-01-08, last_vote=2025-10-22`, so **term-1's
`last_vote` (2025-10-22) falls inside term-2.** This is per-schema (first_vote/last_vote
are defined person-level) and disclosed in the note, but a consumer reading term-1 in
isolation would mis-attribute a 2025 vote to a term that ended Jan-2022. Consider
tenure-windowing the bounds or emitting a machine-readable "person-level bounds" flag
(hardening rec C6).

---

## Confidence-calibration summary

| Row | Current | Should be | Why |
|-----|---------|-----------|-----|
| AL-A2 VACANT (2025-10-22→2026-01-14) | high | **medium** | gap-bounded, no recovered minutes in window; violates builder's own model + own note (F1) |
| AL-A2 Sara Cameron (resigned) | high | **medium** | resignation/date inference-only, off-disk sources (F2) |
| AL-A2 Ezra Nair (appointed) | high | high (OK) | start anchors to a real 2026-01-14 present-list; appointee status a strong inference — defensible |
| AL-B2 VACANT (Rasmussen→Clawson) | high | high (OK) | vacancy + appointment minutes-documented 2024-11-20 |
| AL-B2 Brett Clawson (appointed) | high | high (OK) | secret-ballot 3-2 + swearing-in on disk |
| pre-floor Earnest/Judd/Fullmer-t1 | medium | medium (OK) | 2017 cycle predates data floor, honestly inferred |

No `medium` row was found that is actually solid enough to promote; no other `high` row is
inferential beyond the AL-A2 chain.

---

## Hardening recommendations for `scripts/roster_lib.py` + the maintenance skill

1. **Gap-provenance confidence guard (would have auto-caught F1/F2).** In validation, FAIL
   (or WARN) any row where `confidence=='high'` while its `sources`/`vacate_source`/`note`
   contains gap markers: `un-recovered`, `minutes GAP`, `not on disk`,
   `documented-service-bounded`, `~Nov`/`~Dec`, `medium on the dates`, or a date matching a
   row in `minutes_unrecovered.csv`. The rule "if the row's own prose admits inference,
   the confidence may not be high" is directly encodable.
2. **VACANT-window evidence check.** For each VACANT interval, require that a **recovered
   minutes file exists within `[start,end)`** (cross-check `minutes_index.csv`) that
   documents the vacancy/appointment; if none exists (or the only in-window meeting is in
   `minutes_unrecovered.csv`), **cap the VACANT row at `medium`.** AL-B2's window contains
   the recovered 2024-11-20 → high; AL-A2's window contains no recovered council minutes →
   medium. This is the principled distinction the current build misses.
3. **Bidirectional election crosscheck.** The builder already forward-checks "every general
   winner → a tenure." Add the **reverse**: every tenure with `start_event ∈
   {elected,reelected}` and non-blank `election_year` must map to an `is_winner=Y` general
   row — else FAIL. Sanctioned exception: pre-floor rows must be `confidence=medium` AND
   `election_year < first-election-in-data`, else FAIL. Formalizes today's by-hand check
   and catches a fabricated/mis-yeared elected tenure.
4. **Appointee/loser consistency + vote-window check.** For any `start_event=='appointed'`
   (blank `election_year`): (a) assert internal consistency if the person also appears as a
   same-cycle election loser (Nair/Clawson pattern); (b) assert the appointee's `cities.db`
   `first_vote` falls within `[predecessor.vacate_date, next_election]`. Flags an appointee
   dated outside the vacancy window.
5. **Vacate_date from vote-lists, not present-list headers.** When deriving a vacate_date
   from a "first-absent" meeting, confirm the person is absent from the **roll-call vote
   lists**, not just the present-list header — Vineyard leaves stale headers (the 2024-11-20
   header re-lists the departed Rasmussen, F3). Prefer "last date the person appears in an
   aye/nay list" as the documented-service bound.
6. **Person-level vs tenure-level vote-bound disclosure.** When one person holds multiple
   tenures on a seat (Fullmer ×2), either window `first_vote`/`last_vote` to each tenure's
   `[start,end)` or emit an explicit `vote_bounds_scope=person` flag so downstream
   consumers don't attribute a term-1 row a vote cast during term-2 (F5).

---

*END OF AUDIT — 2026-07-11. Read-only pass; no roster CSV, `roster_lib.py`, or build
artifact was modified. Recommended confidence changes (F1/F2) should be applied through
`roster_overrides.csv` and the CSVs regenerated, per cardinal rule 2.*

---
## RESOLUTION ADDENDUM — 2026-07-11 (post-audit): vote-bound smear FIXED fleet-wide
Any observation in this audit describing a `first_vote`/`last_vote` **person-level smear** (a
councilmember→mayor person's mayor-era vote appearing on a council tenure, or a re-elected
member's whole-career span repeated on each term row) is **RESOLVED**. `scripts/roster_lib.py`
now CLAMPS `first_vote`/`last_vote` to each tenure's own `[start_date, end_date)` window
(`load_vote_dates()` + `clamp_vote_bounds()`), so each tenure carries only its own window's votes
(blank if none). The per-city de-smear overrides (Park City Worel, St George Randall) are retired —
the clamp reproduces their corrected values structurally. See `scripts/roster_HARDENING.md`
(hardening item #2). This addendum records the resolution; the dated findings above are unchanged.
