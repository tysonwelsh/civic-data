# Roster layer — hardening log

Running record of defects found by the per-city roster audits (task #14) and how the
shared `scripts/roster_lib.py` + the maintenance skill were hardened in response. Each
city is built, then independently audited (a fresh adversarial agent); systemic findings
harden the shared library so the whole fleet benefits. Per-city audit records live in
`<city>/roster/AUDIT.md`.

## 2026-07-11 — Vineyard (first real-reuse audit)

**Defect found (F1/F2): gap-bounded dates marked `high`.** The AL-A2 `VACANT` interval and
the departing Sara Cameron tenure were `confidence=high`, but the resignation/appointment
dates fall in an un-recovered Nov/Dec-2025 minutes gap (`2025-12-10` is in
`minutes_unrecovered.csv`) — inference, not documented. Audit-confirmed against the sources.

**Hardening applied to `roster_lib.py` (protects all future cities):**
1. **`vacate_confidence` field** on a tenure — the inserted VACANT row now inherits it
   (was hard-coded `high`). Carried through `build()` (was being dropped — a latent bug).
2. **Consistency invariant** in `validate()` — a tenure that vacates cannot be *more*
   confident than its own `vacate_confidence`.
3. **Gap detector** in `validate()` — reads the city's `minutes_unrecovered.csv`; a `high`
   VACANT interval whose window contains an un-recovered minutes date FAILS the build,
   forcing `vacate_confidence<=medium`. Verified: fires on Vineyard, spares Nephi/Provo.

**Fix:** Vineyard driver set Cameron `confidence=medium` + `vacate_confidence=medium`; the
VACANT row inherits `medium`. Nair's `appointed` row correctly stays `high` (its start_date
anchors to a real 2026-01-14 present-list). Distribution 15h/3m → 13h/5m. Re-federated, ok.

**Cleared by the audit (no change):** Clawson 3-2 appointment + swearing-in, Clawson
ran-2025-and-lost, Stratton=Mayor (2 db votes explained), Fullmer=Mayor (not double-counted),
Jan-2026 4→5 expansion + McCumber 2-yr-by-lot, two-Jacobs disambiguation, all structural
invariants.

**Hardening backlog (audit recs not yet implemented — do as they recur or in a batch):**
- **Bidirectional election crosscheck** — every `elected`/`reelected` tenure with an
  `election_year` must map to an `is_winner` general row (reverse of the existing forward
  check); pre-floor `medium` rows the only exception.
- **Appointee/vote-window consistency** — an `appointed` person's db `first_vote` must land
  within the predecessor's vacancy window; an appointee who also lost the same cycle is
  consistent.
- **Derive `vacate_date` from vote-lists, not present-list headers** — Vineyard leaves stale
  headers (the 2024-11-20 Rasmussen case); prefer the last actual recorded vote.
- **Person- vs tenure-level vote-bound disclosure** for multi-tenure holders (Fullmer's two
  MAYOR rows share person-level first/last_vote).
- Nits: stale-present-list-header tolerance (handled), roster CLAUDE prose vs CSV last_vote.

## 2026-07-11 — Salt Lake City (Opus audit)

Largest/hardest city (52 tenures, 7 districts + Mayor, votes 2021+, elections 2007+,
resolution-based redistricting, 6 VACANT chains). Audit: **remarkably clean** — 1 defect.

**Defect (A1): renamed member's vote span truncated.** Victoria Petro (formerly
Petro-Eschler) has two `cities.db` name_keys; `load_vote_bounds` OVERWROTE per person_key
instead of unioning, so her `last_vote` read 2022-11-10 instead of 2026-06-09. Informational
field only — did not touch tenure/confidence.

**Hardening applied (C1 — systemic, protects every city):** `load_vote_bounds` now UNIONS
across all name_keys mapping to one person_key (earliest first_seen, latest last_seen). Fix
verified: SLC Petro → 2026-06-09; Nephi/Provo/Vineyard byte-identical (no renamed members →
clean no-op); only the `last_vote` column changed anywhere. Re-federated, integrity ok.

**Cleared by the audit:** all 6 vacancy chains source-quoted (Mano Res.1-2020 all-aye;
Faris appointed-then-lost-his-own-special; Young/Petro/Napier-Pearce/Valdemoros); the
vacate-confidence invariant + gap-detector caught every gap-bounded departure; SLC's known
source defects handled honestly (broken 2019 SOVC, 2021 D2 Puy-not-Palmer, Mano stray
8th-voter artifact, Petro name-change); Res.9-of-2022 redistricting verbatim; all 6
plan_2022 precinct checks reconcile; Mayor not a council voter; 0 overlaps; no pre-2020 high.

**Backlog (logged, not yet done):**
- **C2 (cosmetic):** `precinct_hi_source` accepts only ONE high source-year, so SLC's
  2023-sourced precinct rows read `medium` despite equal authority with 2025 (62 high / 82
  medium; ~57% cosmetically downgraded). Fix: accept a SET of high source-years.
- **Skill checks** (for the maintenance skill): a name-change/union assertion (first_vote ≤
  every tenure start; last_vote from the union), and an "8th-voter" roll-size sentinel
  (a vote count exceeding the seat count on a date flags an extraction artifact like Mano's
  stray 2026-03-24 vote — which must not extend a tenure).

## 2026-07-11 — Lehi (backlog #1, Opus audit)

Essentially clean (17 tenures; Albrecht→Lockhart appointment chain verbatim-verified via
Resolution #2025-103; non-voting/tie-break-only mayor). One minor defect + two hardening wins.

**Defect (off-by-one):** the VACANT interval started on Albrecht's last VOTING day (2025-12-02),
so `roster_as_of('2025-12-02')` returned VACANT though she was present + voting. Fixed: Lehi
vacate_date → 2025-12-03 (VACANT begins the day AFTER last service; that day belongs to the member).

**Hardening applied — `non_voting_mayor` config flag (systemic, corroborated by the audit):**
Replaces the old implicit "omit the mayor from `db_key`" convention. When set, MAYOR-body rows get
EMPTY vote bounds and `validate()` enforces it, so a stray tie-break vote can't smear a person-level
span across a mayor's tenures. Set True on nephi/provo/slc/lehi; Vineyard stays False (its mayor
genuinely votes). **Caught a latent bug:** Nephi had its tie-break-only mayor (Nielson, 2 tie-breaks)
in `db_key`, so his span was smeared — the flag stripped it (6 lines, Mayor rows only, no tenure drift).
Provo/SLC already excluded the mayor (0 change); Vineyard 0 change.

**Backlog (batch when convenient):**
- **Fleet-wide vacate-date convention** — adopt "vacate_date = last day served; VACANT begins the next
  day" in `roster_lib.chain_end_dates` (+1 day) + a validator that no VACANT starts on a predecessor
  voting day. Vineyard/SLC VACANT rows may carry the same one-day edge; batch-fix them together rather
  than per-driver. (Lehi fixed at the driver for now.)
- Nit (out of roster scope): add `Alrecht→Albrecht` to Lehi's minutes-extractor variant list.

## 2026-07-11 — Orem (backlog #2, Opus audit)

**CLEAN — 0 defects.** At-large + VOTING mayor. 0-VACANT claim held (all 14 Council voters land on
clean January boundaries; no off-cycle appointee); voting mayor verified (Brunst/Young/McCandless in
the aye lists; 2026 mayor is **Karen** McCandless, not David — brief error the builder corrected);
pre-floor mediums honest (no fabricated `election:2017`); two Davids (Young/Spencer) distinct.
No `roster_lib` changes needed.

**Backlog (nice-to-have, not defects):**
- Preventive validator: assert every `elected`/`reelected` `start_date` equals a real Council meeting
  date and no person's vote bounds fall strictly between term-boundary dates — so a future off-cycle
  appointee trips `--check` instead of producing a clean-looking chain. (Partly covered already by the
  `update-council-roster` skill's unrostered-voter detection query.)
- Prose nit: "distinct surnames" safety wording in per-city roster CLAUDE.md is imprecise — safety comes
  from the `first_last` person_key, not global surname uniqueness (Orem has a 3rd Spencer on the PC).

## 2026-07-11 — Logan (backlog #3, Opus audit pending)

Built clean (19 tenures; TWO VACANT/appointment chains — Bradfield→López 2020, Mark Anderson→Dahle
2025-26; two-Andersons disambiguated; non-voting mayor; the Anderson council→mayor case with the
flag emptying his mayor row so his council span doesn't smear).

**Hardening applied — `load_election_winners` accepts `is_winner` = `Y`.** Logan's CANONICAL election
CSV encodes winners as `Y`/`N`; the lib only accepted `true/1/yes`, so the build agent had shimmed a
normalized temp copy at runtime. Broadened the truthy set to `{true,1,yes,y,t}` and DELETED the
Logan shim (now reads the canonical file directly). Verified byte-identical output; nephi/provo/
vineyard/slc/lehi/orem unaffected. Removes a hack and pre-empts the same shim for other Y/N cities.

**Audit verdict: CLEAN — 0 defects.** Both chains fully on-disk; council→mayor crossover correct; two Andersons distinct; Dahle twist verified. Nits only: two citation date-LABELS use the folder date not the meeting date (no `council_terms.csv` column affected). Rec to make "no MAYOR row carries vote bounds" a validator is N/A — voting-mayor cities (Vineyard/Orem) legitimately carry mayor bounds; the flag-conditional check already covers non-voting cities.

## 2026-07-11 — Millcreek (backlog #4, Opus audit)

**CLEAN — 0 defects.** First fleet city with a district councilmember becoming mayor mid-term
(Silvestrini resigned → Jackson (D3) sworn Mayor 2025-11-10 → D3 VACANT → Handy appointed 2025-11-24;
the 2025-11-18 meeting inside the window independently shows D3 empty). Founding 2016 council `high`
(young city, full history in-window — not pre-floor). Voting mayor confirmed; redistricting Ord 22-23
versioned (plan_2022 real + plan_2016 gap); precinct cross-check reconciles (2021 D2 RCV divergence
correctly hidden under the gap). No `roster_lib` edits needed.

**Backlog (low priority, no data impact — batch with SLC's C2 as a precinct-confidence pass):**
- `write_precincts` uses `r["source_year"]` — make it `.get()` with an explicit fallback so a future
  city missing the column fails safe. (Deliberately NOT a silent default — a missing source_year should
  still be visible, per the audit's own warning about eroding the high/medium provenance.)
- `precinct_crosscheck` gates the per-precinct mismatch detector on `year == precinct_hi_source`, but a
  TOKEN hi_source (Millcreek's "election-xcheck") never equals a year → that branch is dead; only the
  aggregate district-winner is validated. Split `precinct_hi_source` into a source-token field + a
  separate crosscheck key so per-precinct validation actually runs (the "cross-validated→high" label).

## 2026-07-11 — Ogden (backlog #5, Opus audit pending)

Built clean (20 tenures; mixed 4-district + 3-at-large; non-voting strong-mayor). Caldwell→Nadolski
mayoral chain + Nadolski's D4-council-chair→mayor CROSSOVER handled (D4 bounds on his council rows,
MAYOR row emptied by the flag, clean 2024 cycle handoff — 2023 election filled D4 with Graf, so NO
VACANT). Redistricting Ord 2022-9 (2022-03-15, contested 6:1) versioned: plan_2022 real + plan_2012 GAP.

**Precinct-crosscheck robustness CLUSTER (now flagged by SLC + Millcreek + Ogden) — schedule ONE
dedicated `precinct_crosscheck` hardening pass (no roster-DATA impact; district_precincts confidence
labels only):**
- Compare winners via `canon_key`/surname, not exact string — Ogden's "RICHARD HYER" vs "Richard A.
  Hyer" prints a FALSE discrepancy (same person).
- Guard `int(float(votes))` against blank/voter-privacy-suppressed rows (Ogden crashed → per-city
  sidecar workaround; a guard removes the need).
- Tolerate county-vs-city precinct code prefixes (Ogden `29OG##` vs `OGD##`) so the per-precinct
  GIS↔ballot mismatch detector actually runs (else only the aggregate winner check does).
- Split `precinct_hi_source` into a source-token field + a crosscheck key (SLC/Millcreek), and the
  `source_year` `.get()` fail-safe (Millcreek). Batch all of these together.

**Audit verdict: CLEAN — 0 defects.** Nadolski D4→mayor crossover exact (bounds 2020-2023 on council rows, empty mayor row, no overlap, clean cycle handoff to Graf); the Blair/Choberka/Stephens vote-bound smears are preserved source typos that do NOT corrupt tenure end-dates; Ord 2022-9 redistricting verbatim; 4 pre-floor mediums honest. NEW low-pri rec: an optional `vote_bound_artifact` boolean so a consumer cannot seat a smeared name by querying vote bounds instead of the authoritative start/end interval.

**Audit verdict: CLEAN — 0 defects.** The AL-A1 double council→mayor crossover chains without overlap; both VACANT windows legitimately high; the **override layer proven** (first data-row use — Worel `last_vote` correction verified legitimate, removes a tie-break smear, hides no service); non-voting mayor = exactly 2 documented tie-breaks; Miller appointed-after-losing twist confirmed. One cosmetic rec (vacate_source prose). Ship as-is.

## 2026-07-11 — Sandy (backlog #7, Opus audit pending)

Built clean (22 tenures; 4-district + 3-at-large; non-voting strong-mayor). Zoltanski D4→mayor
CROSSOVER as a MID-TERM VACANCY (D4 off-cycle in 2021 → VACANT 2022-01-03→18 → Earl appointed 5-1);
two members ran-for-mayor-lost-then-won-old-seat-back (Christensen D1, Coleman-Nicholl D3, 2025);
redistricting Res 22-24C versioned (plan_2022 real + plan_pre2022 GAP); at-large↔district within-council
moves (Robinson, Houseman). Precinct map derived via point-in-polygon sidecar (no geo file); all 4 plan_2022
contests reconcile (SAN codes match, no false discrepancy).

**Backlog additions (systemic, informational-only — batch with the post-backlog hardening pass):**
- **At-large candidate→seat crosscheck.** The lib's forward election crosscheck maps CONTEST→seat, but
  at-large multi-winner ("Vote-for-N") contests have no per-seat label → 6 "unmapped At-Large" info lines.
  Sandy worked around with a driver-level `_atlarge_crosscheck` (cohort). Add a candidate→seat hook to the lib.
  (Will recur for West Jordan / West Valley at-large seats.)
- **Vote-bound tenure smear (recurring: Ogden, Park City, Sandy).** A councilmember→mayor person's COUNCIL
  row shows mayor-era `last_vote` (Zoltanski D4 last_vote=2025-11-18 is a Mayor-era canvass under body=Council;
  true D4 end 2021-12-14). Park City OVERRODE it (Worel), Ogden/Sandy DOCUMENTED it — inconsistent. Systemic
  fix: clamp `first_vote`/`last_vote` to the tenure's [start,end) window (tenure-level bounds) instead of
  person-level max, which fixes the whole class and obviates the per-city overrides. Tenure DATES are correct
  everywhere; this is the informational bound only. Do in the batch pass + then remove the Park City override.

**Audit verdict: structurally SOUND — 2 documentation-only fixes applied.** All chains/vacancy/redistricting/winner-mapping verified (Earl appointed 5-1, "Seat Vacant, District 4" masthead, Res 22-24C 7-0). FIXED: (A1) the D4 appointment resolution mis-cited "21-03" → the signed doc is **22-03** (driver notes + CLAUDE); (A2) "last recorded D4 vote 2021-12-14" → her last NAMED vote is **2021-12-07** (2021-12-14 was her last meeting served — a unanimous voice vote with no named members). Only note/sources columns changed; tenure dates unaffected. (C) note prose isn't reachable by roster_overrides — corrected in the driver, the curated source.

**Audit verdict: CLEAN — 0 defects.** All 18 pre-floor `medium` terms verified vs the SOVC (none overstated to high; Money→Osborne succession flagged not fabricated); Ramsey's single 2025-06-17 tie-break is her only council vote (all 5 MAYOR rows empty); D2 Marlor→Johnson clean handoff + Johnson's 2008-2011 prior stint distinct; 0 VACANT verified by full minutes sweep; Ord 2022-13 redistricting 5-0 verified. Optional cosmetic notes only (mayor district_versions source_url; a Monday-folder vs Tuesday-meeting-date doc seam). Ship as-is.

## 2026-07-11 — St. George (backlog #9, Opus audit)

Structurally sound (21 tenures; 3 VACANT + 2 crossovers + a mayoral resignation-succession, all in
2021/2026). Non-voting (tie-break-only) mayor; Randall override (de-smear) verified legitimate.

**Defect fixed (DEFECT-1, medium): stale-PMN-template mis-dating.** The Pike→VACANT mayoral bracket
cited "2021-01-14 Pike last presided," but that meeting's PRESENT list shows Mayor Pro Tem Hughes
presiding (Pike ABSENT) — the build trusted a stale PMN "Mayor Pike called the meeting to order" header
line contradicted by the roll calls. Pike's real last presiding = 2020-12-17. FIXED in the driver:
`vacate_date` 2021-01-15→**2021-01-14** (the documented-vacant meeting), sources/vacate_source corrected
to the honest bracket [2020-12-17 last-presiding … 2021-01-14 documented-vacant]. Only 2 rows changed
(Pike MAYOR + its VACANT); no overlap; re-federated ok.

**Backlog / out-of-scope:**
- **Skill check (add to `update-council-roster`):** a departing officer's `end_date`/`vacate_date` must be
  ≤ the first meeting where a Mayor Pro Tem / successor presides per the PRESENT LIST (presiding officer),
  NOT a "called to order" template line — exactly the DEFECT-1 slip.
- **st_george vote-extraction cleanup (out of roster scope):** `cities.db` carries a SPURIOUS Randall
  council vote at 2021-02-25 (mis-parse of "Mayor Randall called for a vote / suggested appointing…" while
  she presided as Mayor). No roster impact (MAYOR rows empty; override caps below it). Flag for extraction.

## 2026-07-11 — Taylorsville (backlog #10, Opus audit)

Structurally SOUND (35 tenures — 15 high / 19 medium / 1 low; 2 VACANT; 0 overlaps/gaps). Pure-district
executive (non-voting) mayor confirmed (Overson + L. Johnson absent from cities.db `person`; 4-1 / 4-0
rolls poll exactly the 5/4 councilmembers). D3 Christopherson→VACANT→Barbieri chain exact ("immediately
upon approval of Ordinance 20-17"); both councilmember→mayor crossovers single-key, no overlap; Res 22-11
redistricting exact (Harker moved / Burgess 2nd / Cochran No / 4-1 / 60,448 residents). OCR-era oath
names (2026-01-07, 2024-01-03) clean.

**Audit verdict: CLEAN — 0 defects.** No fabricated names, no overstated confidence, no OCR-corrupted
names. Notably validates the FIRST `low` row in the fleet: the D2 2018-2020 interim VACANT is the CORRECT
honest move — Overson genuinely vacated D2 to become Mayor (~2 yrs early), the interim holder is genuinely
below the 2020 floor + unnamed in any loaded source, no name invented, the override note removes the
"literally empty" ambiguity. `low`+VACANT is the right representation (no `UNKNOWN` sentinel exists in the
schema; a new one for a single below-floor row = divergence with no analytic payoff). All 5 spot-checked
pre-floor `medium` terms (Catlin/Pratt/Rechtenbach/Barbour/L.Johnson) honestly win=fact/service=inferred.

**Backlog additions (FLEET-SCHEMA, informational — decide uniformly in the post-backlog pass; NOT
inline-fixed to avoid one-city divergence):**
- **`end_event` vocabulary — residency-loss vs true resignation.** Christopherson's D3 departure is
  labelled `end_event='resigned'`, but the 2020-08-19 minutes say he "began their new adventure OUTSIDE
  Taylorsville" (a **move-out / residency-loss** vacancy — the word "resign" never appears for him; all
  downstream dates are airtight). A distinct value (`moved-out` / `vacated`) would be marginally more
  faithful than `resigned`. Systemic: audit every city's `resigned` end_event for residency-loss vs
  filed-resignation and split the vocabulary fleet-wide in one pass (St. George's Pike IS a true
  resignation — keep). Do NOT change one city's label in isolation.
- **`UNKNOWN-HOLDER` sentinel vs `VACANT`.** With the first `low` holder-unknown row now on disk (Taylorsville
  D2), the "seat empty" (VACANT) vs "holder exists but unknown here" distinction rests solely on the note
  string. If more holder-unknown rows accrue fleet-wide, add a machine-legible sentinel (e.g. person_name
  `UNKNOWN` at `low`) distinct from `VACANT` so the distinction is queryable. One row today = defer.

## 2026-07-11 — West Jordan (backlog #11, Opus audit)

Structurally SOUND — the fleet's FIRST MIXED-STRUCTURE city (4 districts D1–D4 + 3 city-wide at-large
AL1–AL3 + a separately-elected NON-VOTING strong Mayor). 21 tenures (19 high / 2 medium / 0 low; 1 VACANT).
Audit PASS: the district↔at-large split is faithful (4 real district contests + one grouped "Vote-for-3"
at-large field), every at-large Vote-for-3 winner maps via the driver's `crosscheck_field="district"`
workaround (0 unmapped / 0 reverse drift), the D2 Worthen→VACANT→Bennett coin-toss appointment (Res 23-070)
chain is exact, Chad Lamb's single-key two-non-contiguous-seat span (AL3 holdover → lost 2021 → won D1 2023)
is clean/no-overlap, non-voting Mayor Burton absent from cities.db (rolls top at 7), Res 22-011 redistricting
5-0, precinct cross-check reconciles all four 2023 district winners.

**Defects fixed (all LOW — free-text note/doc only, no schema/tenure-date impact):**
- (A1) D1/Lamb note said "Council Chair 2024/2025" — the 2024 Chair was **Jacob** ("Chair Jacob called the
  meeting to order" 34× vs "Chair Lamb" 4×; Lamb chaired 2025). → "Council Chair 2025; Jacob chaired 2024."
- (A2) AL1/Whitelock note + sources said "Vice Chair 2026" — the 2026-01-13 roll reads "Chair Bob Bedore,
  **Vice Chair Jessica Wignall**"; Whitelock was Vice Chair in **2025**, a plain member in 2026. → note
  "Vice Chair 2025; a plain member in 2026", sources de-tagged, and the "(Vice Chair)" tag dropped from the
  AL1 line in `roster/CLAUDE.md`'s current-roster table (AL3/Wignall keeps it — she IS the 2026 Vice Chair).
- (doc) `roster/CLAUDE.md` said "all 25 winner rows map" — empirically **17** (6+3+5+3 across 2019/21/23/25),
  all map. → corrected to 17.
Re-federated clean (idempotent; integrity ok; the one residual "Vice Chair 2026" in the CSV is Wignall's
correct AL3 line).

**Audit verdict: PASS — 0 structural defects, 0 library changes.** Confirms the mixed district+at-large
model + the at-large candidate→seat crosscheck workaround (already a logged batch item — West Jordan is the
concrete case for promoting it into the lib in the post-backlog pass). No new hardening items.

## 2026-07-11 — West Valley (backlog #12 — FINAL, Opus audit)

Structurally CLEAN — MIXED 4-district + 2 single-winner at-large + a **VOTING Mayor** (inverse of West
Jordan). 22 tenures (18 high / 4 medium / 0 low; 2 VACANT). Audit CLEAN, 0 data defects. Verified: both
mayors (Bigelow, Lang) polled on routine legislation (Ord 22-10 7-0 "Mayor Lang Yes"; 2020 roll "Mayor
Bigelow Yes"), Council rolls top at 7; Lang single person_id, D3 [2020-01-07,2022-01-04) vs MAYOR
[2022-01-04,…) no overlap (no cross-tenure smear); AL1=2019/2023 Christensen, AL2=2021/2025 Nordfelt
(single-winner per cycle, correct); RDA/MBA kept OUT of roster (19 Council + 3 Mayor rows only, despite
same people holding those board roles); both appointments quoted (Res 22-11 Whetstone 6-0; Res 25-11 Wood
6-0); both VACANTs day-after-last-service, close at successor seating, 0 gaps/overlaps; all 14 general
winners map; Ord 22-10 redistricting 7-0 (plan_2022 real + plan_pre2022 GAP).

**Defect fixed (LOW — prose only):** 9 note strings + roster CLAUDE.md cited person-level vote bound
"2026-06-09" — that is the **RDA**-body `last_seen`; the Council-body last vote is **2026-05-26**. The
`last_vote` COLUMN was correct everywhere (only 2021-12-14 / 2024-12-10 / 2026-05-26 ever appear), so no
query was affected — pure prose over-reach on a Council-scoped layer. FIXED: prose 2026-06-09→2026-05-26 in
driver + CLAUDE.md; column values unchanged; idempotent; re-federated ok. (Reinforces the vote-bound-clamp
batch item — an across-body max leaking into a Council-scoped prose bound is the same class as the
councilmember→mayor smear; the tenure-window clamp resolves both.)

---

# BACKLOG COMPLETE — all 16 cities built, federated, and independently audited (2026-07-11)

370 term rows across 16 cities in cities.db (`term` + `district_version` + `district_precinct` +
`v_council_current`/`v_term_provenance`). Every city passed an independent adversarial Opus audit; all
defects found were LOW/documentation-grade (note/citation prose) except a handful of real date/label
corrections (SLC Petro, Vineyard gap-confidence, Lehi off-by-one, Sandy citations, St. George Pike
mis-dating) — all fixed in-driver and re-federated. NO fabricated names anywhere; the one below-floor
holder-unknown case (Taylorsville D2) is an honest `low` VACANT. Remaining work is the consolidated
post-backlog hardening pass (promote the batched lib items below) + boundary-gap housekeeping.

---

# HARDENING PASS (post-backlog) — item #2 LANDED: vote-bound tenure clamp (2026-07-11)

**The batched "vote-bound tenure clamp" item is DONE.** `roster_lib` gained `load_vote_dates()`
(per-person distinct Council-body vote dates via `vote→motion→meeting`, db_key-mapped, name_key-UNIONed)
and `clamp_vote_bounds()`; `build()` now assigns `first_vote`/`last_vote` as the earliest/latest observed
Council vote WITHIN each tenure's own `[start_date, end_date)` window (blank if none), run AFTER
`chain_end_dates()`. Replaces the old person-level `role` min/max.

**Effect (verified):** 209 bound-cells changed across all 16 cities, 28 blanked, **0 suspect**
(every change is a valid in-window narrowing; classifier confirms new value ∈ `[start,end)`). Fingerprint
stable at 370 rows / 255h·114m·1l (prose edits changed no counts). All 16 build+validate+idempotent;
re-federated (integrity ok).

**Kills the whole councilmember→mayor smear class structurally:** Worel AL-A1 last_vote 2021-12-16 (excl.
2024-08-22 mayoral tie-break); Randall AL-B1 2021-01-19 (excl. 2025-02-20); Lang D3 2021-12-14 (excl.
mayor-era, D3 vs MAYOR rows now differ); Sandy Zoltanski D4 2021-12-07 (excl. 2025 canvass). **Both
per-city de-smear OVERRIDES RETIRED** (Park City Worel, St George Randall → header-only files) — the clamp
reproduces their corrected values with no override. Also splits consecutive re-elected terms into per-term
bounds and blanks pre-floor tenures whose holder's only votes fall in a later term (truthful).

**Prose reconciled fleet-wide** (4 parallel Opus agents, disjoint city sets): driver `note`/`sources`,
`roster/CLAUDE.md` schema + override sections, and a dated RESOLUTION ADDENDUM appended to all 14
`roster/AUDIT.md` files that had flagged the smear. All value columns verified unchanged by the prose pass
(agents + independent 0-suspect re-check). Independent adversarial audit of the whole change in progress
(`scripts/roster_clamp_AUDIT.md`).

**Remaining hardening items:** #1 at-large candidate→seat crosscheck hook (unify the WJ/WV `crosscheck_field`
+ Sandy `_atlarge_crosscheck` workarounds); #3 precinct-crosscheck robustness cluster (retire the per-city
`_precinct_*.csv` sidecars); #4a end_event vocab split (residency-loss `moved-out` vs true `resigned`);
#4b UNKNOWN-holder sentinel — DEFERRED (auditor: one below-floor row, no analytic payoff).

**Item #2 independent audit: CLEAN.** From-scratch recompute of all 370 rows straight from cities.db
matched the CSVs exactly (0 data defects); 47 blanks proven truthful; all 12 crossover people de-smeared;
both retired overrides reproduced by the clamp alone; no query regressed. Lone finding = 1 doc-only miss:
**provo/roster/CLAUDE.md** still called the field "person-level" (my earlier cleanup grep was case-sensitive;
provo used a capital "P"). FIXED — reworded to the clamp description + corrected source ref
(`vote→motion→meeting`, not `role`); provo data was already correctly clamped. Full report:
`scripts/roster_clamp_AUDIT.md`.

## Hardening item #4a — end_event vocab: DECIDED (no vocabulary expansion) + 1 honesty fix (2026-07-11)
Surveyed all 15 `end_event='resigned'` rows fleet-wide: they span genuinely varied departures — elected
elsewhere (SLC Kitchen→Senate, WV Fitisemanu→House), health (Millcreek Silvestrini), won-the-mayoralty
(Logan Anderson), ran-for-mayor-and-lost-then-resigned (Lehi Albrecht), moved-out (Taylorsville
Christopherson), and plain mid-term resignations (SLC Fowler/Lopez Chavez, WJ Worthen, Vineyard
Cameron/Rasmussen). **DECISION: do NOT expand the end_event vocabulary.** A binary `moved-out` vs
`resigned` split is arbitrary given that variety, and `end_event` is a NORMALIZED field — under the repo's
cardinal rule #2, the coarse "left the seat mid-term" bucket (`resigned`) is correct and the faithful
specific reason belongs in the row `note`. **Fixed the one honesty issue** the Taylorsville audit raised:
Christopherson's note/CLAUDE.md/demo asserted "RESIGNED" though the minutes describe a move OUTSIDE
Taylorsville ("resign" never appears) — reworded to "DEPARTED (residency-loss)" with the normalized-bucket
note. Verified only the `note` column changed; re-federated.
- **New minor batch item (NOT fixed — out of #4a scope, Logan audited clean earlier):** Logan Anderson's
  end_event is `resigned` but he WON the 2025 mayoralty and vacated council — the fleet crossover
  convention is `became-mayor` (cf. St George Randall/Hughes, Taylorsville). A one-row normalization-
  consistency nit to consider in a future end_event consistency sweep.

## Hardening item #4b — UNKNOWN-holder sentinel: DEFERRED (auditor's call; 1 below-floor row, no payoff).

## Hardening item #1 — at-large candidate→seat hook: SKIPPED (owner decision 2026-07-11).
Diagnostic-only, no functional gain — pure at-large cities key cleanly on `body`, WJ/WV on `district`,
Sandy has a working `_atlarge_crosscheck` helper; all report 0 drift today. Not worth the churn. Left as
a logged batch item (unify into the lib only if a future city needs it).

## Hardening item #3 — precinct-crosscheck robustness cluster + retire per-city sidecars: IN PROGRESS.

**Item #3 LANDED (2026-07-11): precinct-crosscheck robustness + sidecar retirement.**
roster_lib gained 3 robustness features: (a) multi-year `precinct_hi_source` (`_hi_srcs()` accepts a
tuple → a geo map with per-row source_years for ONE current plan marks them all `high`, no collapse
token); (b) an in-library blank/**suppressed** vote guard in `precinct_crosscheck` (skips empty/
non-numeric cells AND voter-privacy `suppressed=true` rows at read time); (c) `_winner_matches()` —
precinct-sum-winner vs roster-winner compared via `canon_key` (surname fallback), not exact string.
All backward-compatible (verified byte-identical no-op with the old sidecar drivers first).

**Result:** retired **9 of 11** per-city precinct sidecars — the byprecinct `_precinct_votes.csv` for all
6 district cities (ogden/sandy/south_jordan/taylorsville/west_jordan/west_valley) + the
`_precinct_to_district.csv` for the 3 clean source-year wrappers (taylorsville/west_jordan/west_valley).
**2 kept** (documented as genuine per-city geo derivations, NOT lib-rigidity workarounds): sandy
`_precinct_to_district.csv` (point-in-polygon of precincts.geojson × council_districts.geojson — no
canonical county precinct map) and south_jordan `_precinct_to_district.csv` (geo file has no source_year
column). Drivers repointed to the canonical `geo/precinct_to_district.csv` + `election_results/*_by_precinct.csv`.

**Wins:** the canon_key compare turned former FALSE discrepancies into clean RECONCILES with no per-city
exclusion — Ogden D2/D3 ("RICHARD HYER"/"KEN R. RICHEY"), West Valley D2/D3 ("SCOTT L. HARMON"/"WILL
WHETSTONE"), Taylorsville D1 ("ERNEST GLEN BURGESS"); all previously-excluded districts are now in the
automated check. Ogden's guard correctly skips 2 voter-privacy-suppressed rows.

**Verified (4 gates, 3 parallel Opus agents + my re-check):** all 16 build+validate clean; council_terms
BYTE-IDENTICAL for all 6 cities; fleet fingerprint stable 370 / 255h·114m·1l; district_precincts
confidence distributions preserved; **0 DISCREPANCY** fleet-wide; re-federated (integrity ok).

---
# HARDENING PASS COMPLETE (2026-07-11). #2 clamp (audited clean) + #3 precinct robustness/sidecars LANDED;
#4a end_event DECIDED (no vocab expansion) + honesty fix; #1 at-large hook + #4b UNKNOWN-sentinel SKIPPED/
DEFERRED (owner call / auditor call). Fleet: 16 cities, 370 term rows, all federated + validated.

## 2026-07-12 — Bluffdale (first new-city-wave roster; audit `bluffdale_city_council/roster/AUDIT.md`)

Three systemic items surfaced by the independent audit (roster itself PASSED all checks):

- **E1 — ballots-cast ceiling validator for the ELECTIONS layer.** The 2019 Bluffdale
  vote-for-3 contest ran for years with `N_SEATS=2` (mis-flagging a real winner
  `is_winner=False`, poisoning runner_up/margin/notes and the federated `election_race`
  row). A per-contest invariant — Σ(candidate votes) ≤ n_seats × ballots_cast — would have
  auto-caught it (the raw SOVC showed 4,977 votes vs 2,154 ballots, impossible under
  vote-for-2 in EVERY precinct). Belongs in the elections normalizer/validator, fleet-wide.
- **C3 — documented-exceptions mechanism for the future in-lib reverse crosscheck.** When
  the bidirectional election crosscheck moves into `roster_lib.validate()` (existing
  backlog item), it needs a per-city allowlist for legitimate tenure→no-winner-row cases
  (pre-floor election-anchored terms; source-data winner-flag defects while unfixed).
- **S2 — "recorded mayoral participation" allowlist for the roll-size sentinel.** Bluffdale
  2025-05-14 prints a verbatim "Mayor Hall-Yes" on a motion already passing 3-2 — a
  faithful over-size roll (6 recorded on a 5-seat council), unlike SLC's Mano extraction
  artifact. The sentinel needs to distinguish faithful mayoral participation (minutes print
  it) from pipeline strays before it can fail-loud in-lib.

## 2026-07-13 — new-city-wave rosters (9 built: murray/herriman/draper/riverton/alta/midvale/cottonwood_heights/holladay/south_salt_lake)

Nine wave-city rosters built + federated (roster layer 17→26 cities, term 385→542). The
fleet's FIRST district cities with a **VOTING mayor** (herriman/cottonwood_heights/holladay)
and first **councilmember→mayor** seams in district form (Holladay Fotheringham D3→Mayor) fit
`roster_lib` with NO library change — `non_voting_mayor=False` + the existing vote-bound clamp
handled both. Systemic findings (converged across the three parallel forks):

- **H-A (precinct-file `source_year` mismatch — RECURRING, fleet-wide).** `write_precincts()`
  / `precinct_crosscheck()` hard-require a `source_year` column in `geo/precinct_to_district.csv`
  that the SLCo district cities' geo files DO NOT carry (schemas vary: `…district_area_frac,
  method,split` / `…election_district,method,agrees_with_current_election`). Worked around
  WITHOUT touching `geo/` or `roster_lib` by a **roster-local `_precinct_to_district.csv`
  sidecar** (adds `source_year=current`) passed as `precinct_map_path` — now the established
  pattern for herriman/cottonwood_heights/holladay. murray/riverton/midvale instead SKIPPED
  the precinct layer (rosters still valid). **Fix:** let `write_precincts` default a missing
  `source_year` to a config token (or accept a plain `precinct,district` map). Because the
  token isn't a year, per-precinct MISMATCH detection stays dormant (the aggregate winner
  cross-check still runs) — the documented "token-not-a-year" limitation.
- **H-B (vote-outside-tenure-window sentinel — NEW, recommended).** Staff/treasurer-as-voter
  (Alta: `craigheimark` treasurer-era 2022-23 procedural mentions) and post-departure stray
  votes (Holladay: `gibbons` ×4 after 2024-01-04; Alta: Davis 2024-02-14) are SILENTLY absorbed
  by the tenure-window clamp — a good roster outcome, but the underlying votes-pipeline
  artifacts are invisible to `validate()`. Add a build-time flag: "a mapped person cast a
  Council vote outside every one of their tenure windows." Subsumes the roll-size/8th-voter
  sentinel (Holladay's is a 7th name over a roll-of-6).
- **H-C (reverse election-crosscheck exceptions — extend the bluffdale-audit list).** When the
  reverse crosscheck moves into `validate()`, its per-city documented-exceptions allowlist (the
  Hales winner-marking class) needs TWO new sub-classes surfaced this wave: **canceled-
  uncontested race** (Draper 2025 regular 2-seat B: Lowery+Green certified via Res #25-49,
  never on the SOVC) and **privacy-suppressed / not-yet-in-county-file winner** (Alta 2021
  suppressed tallies; Alta 2025 + Draper 2025 county-file gaps).
- **H-D (no estimated-switch-date confidence for a redistricting).** Cottonwood Heights' 2022
  redistricting is documented in effect but its ADOPTING ordinance isn't in the recovered
  minutes; `Redistrict.plan_switch` + `write_districts` hardcode the `plan_new` rows to
  `confidence=high`, with no way to mark the SWITCH DATE itself low-confidence (worked around
  via a note + an estimated 2022-06-01 switch). Fix: per-plan switch-date confidence.
- **H-E (within-data "canceled race" marker).** The clean long-term fix for H-C's canceled-
  uncontested class: let `election_results` carry canceled-uncontested certifications so those
  winners stop being invisible to both the forward and reverse crosschecks.

**Data defects FLAGGED (not fixed from the roster — queued in TODO.md):** Holladay 4 spurious
`gibbons` Council votes post-2024 (extraction artifact); Alta `craigheimark` treasurer-era +
Davis 2024-02-14 stray votes; Draper `election_results` 2025 canceled-uncontested B race
absent from the SOVC (acquisition gap).

**Still unbuilt (their forks all died on the 11:50pm session limit):** white_city, kearns,
magna, copperton, emigration_canyon — the 5 township→city HB35-seam cities (presiding-officer
vote FLIP at the 2024 seam for magna; floor 2017). Residual work.

## 2026-07-13 (cont.) — the 5 township→city HB35-seam rosters (white_city/copperton/kearns/magna/emigration_canyon)

Completes the wave: **roster layer now 31/31 city-town entities** (term 632). All 5 built +
validated + idempotent + federated. New systemic findings:

- **H-F (terminal ABOLISHED-seat end_date is clobbered — BUG, found+worked-around 2026-07-13).**
  `chain_end_dates()` unconditionally sets the LAST tenure on each seat to `end_date=""`
  (serving). For a seat that was **abolished** (Kearns D5 at the 5→4 HB35 restructure) there is
  no successor to chain from, so an explicit `end_date` in TENURES is silently blanked → the
  abolished seat wrongly appears in `v_council_current` (caught post-federation: kearns showed 6
  current seats, should be 5). **Per-city fix applied:** a `roster_overrides.csv` row (applied
  after chaining, wins) pins Kearns D5 Bush end_date=2026-01-12. **Fleet fix (do in the lib
  later, with full re-verification):** in the terminal-tenure branch, KEEP an explicit `end_date`
  when the tenure carries a terminating `end_event` (e.g. `seat-abolished`) instead of always
  blanking it. Pairs with H-? (Kearns `districts_old` for district-count-changing seams).
- **H-G (presiding-officer VOTE-FLIP across a seam — modeled without a lib change, Magna).** The
  township-era voting "Mayor" is a rotating ceremonial hat on a sitting DISTRICT member (Magna:
  Peay D3, Barney D2; Kearns: Bush D5) — so those stay on `body='Council'` DISTRICT seats with
  real vote bounds, and the `MAYOR`/`body='Mayor'` seat is reserved for the post-seam directly-
  elected executive (Magna: Sudbury 2026+, non-voting → `non_voting_mayor=True` and validate()
  ENFORCES empty mayor bounds; Kearns: Valdez 2026+, VOTING → `non_voting_mayor=False`). The
  single per-city `non_voting_mayor` flag can't carry a voting-chair era + a non-voting-exec era
  on ONE mayor chain, but the district-seat-split representation makes that unnecessary. A
  per-tenure voting flag would be the clean general fix (not implemented).
- **H-H (district-count-changing seam — Kearns 5→4).** `Redistrict` assumes the same district
  list across both plans, so an abolished district (Kearns D5) can't get a `plan_old` boundary
  row — folded into the general `plan_township` gap. Fleet fix: a distinct `districts_old` list.

**Data defect flagged (votes pipeline, queued in TODO):** Emigration Canyon
`meeting_minutes/roster.csv` over-attributes Gary Bowen to 2026-04-21 via agenda-text false
positives — his real council service ends 2021-12-14.

## 2026-07-19 — H-A…H-H hardening pass (shared-lib wave; backups `_backups/2026-07-19-lm-wave/shared-libs/`)

All eight items dispositioned. Every lib change is default-off / backward-compatible: an A/B rebuild
of all 30 rosters (fleet minus millcreek — another agent held its roster/geo; its regeneration +
re-federation are the ORCHESTRATOR's) with the old vs new lib produced **byte-identical outputs
everywhere**; the per-city diffs below are explicit driver opt-ins. NOTE: the pre-existing baseline
CSVs were stale vs the refreshed cities.db (2026-07-16/17 recovery waves) — regeneration refreshed
`first_vote`/`last_vote` in 7 cities (emigration_canyon, herriman, nephi, ogden, orem, park_city,
riverton); those diffs are vote-bound refreshes, not lib effects (verified by the A/B run).

| Item | Disposition | Change | Proof |
|---|---|---|---|
| **H-A** precinct `source_year` | **LANDED** | `Redistrict.precinct_source_default` — explicit fallback token when the precinct map has no `source_year` column; unset ⇒ fail-loud (never a silent default). | The 3 wrapper sidecars (herriman / cottonwood_heights / holladay `roster/_precinct_to_district.csv`) verified pair-identical to their `geo/precinct_to_district.csv` and **RETIRED**; drivers read the geo file directly. terms+versions byte-identical; district_precincts changed ONLY the `note` prose; crosschecks RECONCILE. kearns/magna/sandy/south_jordan sidecars KEPT (genuine derivations, not wrappers). **Follow-up:** riverton + midvale still SKIP the precinct layer — the lib now supports enabling it (needs per-city driver+CLAUDE work, queued). |
| **H-B** vote-outside-window sentinel | **LANDED** | `vote_window_sentinel()` — informational build-time stderr flag: a db-mapped person with Council votes outside EVERY tenure window. Windows include Mayor rows, so faithful mayoral tie-breaks (bluffdale S2 class) never false-flag. Never fails the build. | Fires on the pre-documented artifacts (holladay gibbons ×4, alta heimark/davis, slc mano 2026-03-24) AND surfaced two likely STALE-ROSTER chains needing minutes adjudication: **murray D1 2023** (markham ×11 + rodgers ×5 in-2023 votes vs a rostered Jan–Nov VACANT — roster predates the 2026-07-16 murray minutes recovery) and **south_salt_lake** (jones + glad ×6 votes 2026-03..05 BEFORE their rostered 2026-06-10 appointments — predates the SSL recovery). Also magna pierce 2019-10-22, ogden choberka/blair 2026-05-19 + stephens 2022-01 ×2, park_city gerber/rubell/doilney 2026-06-11, slc fowler/johnston/lopez_chavez/rogers ×1 each, vineyard cameron 2025-10-22. ALL queued for votes-layer / update-council-roster adjudication (TODO is orchestrator-owned this session). |
| **H-C** reverse election crosscheck | **LANDED** | `reverse_election_crosscheck()` (called from `build()`, informational, mirrors the forward check) + `RosterConfig.reverse_crosscheck_exceptions` {(year, key, person): cited reason} with stale-entry fail-loud, + AUTO-EXEMPT below the elections CSV's own coverage floor. | Curated exceptions where the class is already documented: **draper** 2025 lowery/green (canceled-uncontested Res #25-49, never on the SOVC) and **alta** 2025 heimark/anctil/bourke (2025 election CANCELLED, Res 2025-R-26 certification — `alta_races.csv` has the `cancelled_certification` rows but no by_candidate tally rows can exist). Both cities rebuild flag-free, terms byte-identical. **Remaining honest drift (exception-candidate queue, NOT curated blind):** copperton 2019×3/2025×3, holladay 2023 durham+gray, magna 2023×3, riverton 2017/2021 buroker+mccay (the D3↔D4 renumbering — same class as its pre-existing forward-check drift), sandy at-large ×6 (the known unmapped Vote-for-N class), white_city 2021 price+cardenaz. Each needs per-city verification before an exception entry is written. **slc RESOLVED AT THE DATA LAYER 2026-07-19:** the four slc exceptions curated earlier that day (johnston/dugan/mendenhall 2019 + puy 2021 D2) were removed after the election source itself was fixed (the garbled 2019 slice re-synced from the archive's family-B re-parse; the 2021 "Puy-not-Palmer swap" exposed as a suppressed-precinct partial-count artifact — certified first-choice totals Puy 1,084 / Palmer 751 — fixed by the normalizer's Total-recovery, `_backups/2026-07-19-slc-elections-fix/`); the stale-entry fail-loud fired exactly as designed on all four, slc rebuilds exception-free, terms byte-identical. |
| **H-D** switch-date confidence | **LANDED (latent)** | `Redistrict.current_confidence` (default "high") — the plan_new rows' confidence is configurable. | Fleet byte-identical (default). cottonwood_heights DELIBERATELY unchanged: its audited representation (geometry authoritative `high` + the estimated-switch-date caveat in the note) stands; the knob exists for a future city whose current-plan rows genuinely warrant `medium`. |
| **H-E** in-data canceled-race marker | **DEFERRED (elections layer, partially superseded)** | none in roster_lib | Alta already carries the canceled-2025 certification in `alta_races.csv` (`cancelled_certification`, recovered 2026-07-17) — the races-level pattern EXISTS. The remaining gap is (a) the by_candidate winner form the lib reads cannot represent a no-votes certification and (b) draper's Res #25-49 certification was never acquired into its election_results. An elections-normalizer schema decision + acquisition — out of roster_lib scope; the H-C exception mechanism covers the roster side meanwhile. |
| **H-F** terminal abolished-seat end_date | **LANDED** | `TERMINAL_END_EVENTS = ("seat-abolished",)`; `chain_end_dates()` keeps an explicit driver-supplied `end_date` on a terminal tenure with a terminating end_event instead of blanking to serving. | kearns driver now carries Bush D5 `end_date=2026-01-12` in TENURES; the `roster_overrides.csv` pin RETIRED (0 data rows again). Diff: exactly one cell — Bush's `sources` loses the `override:roster_overrides.csv` tag. Serving seats correct (D1–D4 + MAYOR, no D5). |
| **H-G** presiding-officer vote-flip | **NO LIB CHANGE (decision confirmed)** | none | The district-seat-split representation (township chair-'Mayor' stays on the DISTRICT seat with real bounds; the MAYOR seat is the post-seam elected office with its own `non_voting_mayor` posture) is validated: magna + kearns build/validate clean with opposite city-era mayor voting rules and no per-tenure flag. A per-tenure voting flag remains the clean general fix IF a city ever needs both eras on ONE mayor chain — none does. |
| **H-H** district-count-changing seam | **LANDED** | `Redistrict.districts_old` (default None = same list, byte-identical) — plan_old rows in `district_versions` AND the plan_old gap rows in `district_precincts` iterate the PRIOR plan's own list. | kearns sets it: the abolished township D5 now has its own honest `plan_township` gap row in both files (+1 row each; prior-note reworked via `prior_note_by_district`). CLAUDE.md + driver prose reconciled. |

**New mechanism (found mid-pass, not an H item): `vacate_unrecovered_ack`.** Logan's roster had become
UNBUILDABLE: `minutes_unrecovered.csv` gained the 2020-10-13 Interim-Appointment meeting (PMN
agenda-only) AFTER the roster was built, and the gap-detector capped the AL-B1 VACANT at medium —
but BOTH bracket dates of that vacancy are attested in RECOVERED minutes (resignation 2020-09-22
quoted verbatim in the 2020-10-20 oath minutes; the seating itself), so a medium downgrade would
misstate. New per-tenure field `vacate_unrecovered_ack` (comma-separated dates): the driver
explicitly acknowledges a mid-window un-recovered date as non-undermining, with the justification
required in `vacate_source`; a stale/mis-dated ack fails loudly. Logan carries the ack + the
justification clause (diff: that one VACANT row's `sources`). Confirmed failing identically under
the OLD lib — pre-existing breakage, not introduced by this pass.

**Gates:** all 30 rosters build + `--check` validate + idempotent (re-run byte-identical); 0
precinct DISCREPANCY; A/B old-lib/new-lib byte-identical at defaults. **Millcreek excluded per the
session constraint — orchestrator must regenerate it once (expect byte-identical at defaults) and
re-federate cities.db (term 632 + kearns district_versions/district_precincts +1 row each +
prose-changed rows).** Also queued for the orchestrator: the 7-city vote-bound refresh means
`cities.db.term` is stale until re-federation; and the ogden D2/D4 note prose ("first_vote ...
2024-02-06") now disagrees with the refreshed first_vote=2024-01-09 (recovered-votes effect) — a
prose nit for the next ogden roster touch.
