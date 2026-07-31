# Draper City — independent verification

Independent QA of the Draper City Council + Planning Commission datasets, run **2026-07-11**
against the on-disk canonical files (not the build logs). Method: reconcile every doubly-stored
fact (flat `all_votes.csv` ↔ `minutes_index.csv` ↔ per-meeting vote JSON ↔ `db/civic.db`),
ground-truth a random sample of meetings against their source minutes markdown, confirm the
Granicus **Recap-vs-Minutes** resolution held, confirm the single mayoral tie-break, and
cross-check the 2021 / 2023 / 2025 election winners against outside sources. `scripts/validate_city.py
draper_city_council` = **24 PASS / 0 FAIL** (1 WARN = the docs written in this pass).

**Verdict: PASS on every built dataset, 0 FAIL.** One minor extraction miss logged (§7) — a single
ceremonial canvass motion — queued to `TODO.md`, not a data-integrity failure.

---

## 1. Council votes — PASS

| Check | Result |
|---|---|
| `minutes_index.csv` rows (docs on disk) | **151** (all `format=text`, born-digital) |
| Markdown files on disk | **151** (== index; 0 orphans, 0 missing) |
| Dates with ≥1 extracted motion | **147** |
| Distinct motions (`date`+`motion_no`) | **871** |
| Vote rows | **3,805** |
| Named vote rows (member ≠ blank) | **3,679** |
| Vote dates ⊄ index | **0** (every vote date has an indexed doc) |
| Index dates with **no** motion | **4** — all legitimately vote-less (§7) |
| Contested motions (any Nay/Abstain/Recuse) | **15** |
| `validate_votes.py` | **PASS** |

The 3,805 total / 3,679 named / 871 motion counts match the build facts exactly.

## 2. Planning Commission votes — PASS

| Check | Result |
|---|---|
| `minutes_index.csv` rows | **141** (all `format=text`) |
| Markdown files on disk | **141** (== index) |
| Dates with ≥1 extracted motion | **141** (every indexed PC meeting has a motion) |
| Distinct motions | **898** |
| Vote rows | **4,191** |
| Named vote rows | **3,969** |
| Vote dates ⊄ index | **0** |
| Contested motions | **201** (PC is far more contested than Council — a real land-use signal) |
| Vote values | Aye 3,120 · Absent 542 · Recuse 167 · Abstain 76 · Nay 64 · (blank tally-only) 222 |
| `validate_votes.py` | **PASS** |

Counts match the build facts (4,191 / 3,969 named / 898 motions / 201 contested). PC land-use motions
cite case numbers `YYYY-NNNN-TYPE` (**184 distinct** in the motion text; types `USE`/`SUB`/`MA`/`VAR`/`SP`).

## 3. db/civic.db reconciliation — EXACT

| db table | rows | reconciles to |
|---|---|---|
| `body` | 2 | Council, PlanningCommission |
| `meeting` | **288** | 147 Council + 141 PC vote-bearing meetings ✅ |
| `motion` | **1,769** | 871 Council + 898 PC ✅ |
| `vote` | **7,648** | 3,679 + 3,969 **named** CSV rows ✅ (0 dropped) |
| `person` | 28 | councilmembers + commissioners + movers/seconders + Mayor Walker (tie-break) |
| `referral` | 5 | all `medium` (PC→Council reconstructed links) |
| `v_contested` | **216** | 15 Council + 201 PC ✅ |

Every named member-vote row lands in `vote`; the db is an exact function of the two flat CSVs.

## 4. Recap-vs-Minutes trap — RESOLUTION HELD ✅

Draper's Granicus MinutesViewer publishes, for recent meetings, **both** a tally-only 1-page
**Recap** and the full **Minutes** behind a JS document selector. The build kept the full Minutes
and dropped every Recap. Verified by inspecting the most recent regular meetings — a Recap would be
~1 page / a few hundred words with **no** named roll-call grid; the full Minutes carry named
`Yes / No / Absent` grids:

| Meeting | Words | Named `Yes/No/Absent` grids | Named vote rows | Verdict |
|---|---|---|---|---|
| 2026-06-09 | 2,899 | 12 | 60 | full Minutes ✅ |
| 2026-05-19 | 3,584 | 6 | 29 | full Minutes ✅ |
| 2026-04-28 | 1,407 | 4 | 20 | full Minutes ✅ |
| 2025-12-02 | 2,293 | 6 | 30 | full Minutes ✅ |

**Zero tally-only Recaps slipped into the indexed minutes.** A sweep for any indexed council doc
under 450 words returned **5** files — none is a Recap: three are genuine special/electronic/retreat
meetings, one is the Board of Canvassers (§7), and one is 2024-04-29, a genuine single-item special
meeting (Resolution #24-20, Alpine School District interlocal) that carries a proper named roll-call
grid and IS extracted. The pending 2026-07-07 meeting, for which only a Recap exists so far, is
**correctly withheld** and logged `recap_only_pending` in `minutes_unrecovered.csv` — the build did
not stub it with the Recap.

## 5. Mayoral tie-break — CONFIRMED ✅

Draper's Mayor is **non-voting**. The data contains **exactly one** vote row for `Mayor Troy K.
Walker` in the entire corpus (Council + PC): **2024-10-15, motion 3**, "Councilmember Roberts moved
to approve Ordinance #1625", `result = 3-2 Pass`. The five-member roll was **Green Aye, Roberts Aye,
Johnson Nay, T. Lowery Nay, F. Lowry Recuse** — a 2-2 tie among voting members; **Mayor Walker cast
the deciding Aye** (recorded as a plain `Aye`, not a special note field). This is faithful to the
minutes and is the Mayor's sole appearance in any vote row. Confirmed against the source markdown
(`meeting_minutes/minutes/2024/2024-10-14/2024-10-15_city-council.md`).

## 6. Ground-truth spot-checks (markdown ↔ extracted rows)

- **Council 2022-05-03** — 7 motions in markdown, 7 extracted. Verified the roll-call grids
  line-by-line: Councilmember **Green is `Absent` on motions 1–4** (agenda items 5.1/6.5/7.2/8.4)
  and **`Aye` on motions 5–6** (9.3 Resolution #22-20, 10.1 CRA recess); motion 7 (adjourn) is
  tally-only (blank member/vote). Extraction matches the source exactly, including the mid-meeting
  arrival.
- **Council 2024-04-29** (§4) — single motion (Resolution #24-20), 5 named Ayes → extracted.
- **PC 2023-06-08** — 4 motions: two `5-0 Approved (Final Action)`, one `5-0 Positive
  Recommendation` (named grids: Squire/Tonks/Nixon/Ogden/Hawker all Aye), one adjourn tally-only.
  Matches markdown; the PC's Final-Action vs Positive-Recommendation distinction is preserved in
  `result`.
- **Council 2024-10-15** — the tie-break meeting (§5), verified.

No fabricated names or invented tallies found in the sample; blank member/vote cells correspond to
genuinely tally-only ("voice/tally-only") motions in the source, per the cardinal rule.

## 7. Meetings with no extracted votes — all legitimate

Four indexed council docs carry no motion. Three are genuinely vote-less; one is a real (minor) miss:

| Date | Title | Finding |
|---|---|---|
| 2023-03-04 | City Council Retreat | vote-less (0 "moved" in source) ✅ |
| 2023-03-10 | Special Electronic Meeting | vote-less ✅ |
| 2025-03-22 | City Council Retreat | vote-less ✅ |
| **2025-08-26** | **Board of Canvassers** | ⚠ **1-motion extraction MISS** — see below |

**⚠ 2025-08-26 Board of Canvassers.** The source markdown contains a named roll-call grid for
**Resolution #25-42** (canvassing the Aug-12 primary): Green **Yes**, Johnson **Yes**, T. Lowery
**Yes**, F. Lowry **Absent**, Vawdrey **Yes** ("passed unanimously"). The extractor did not capture
it (the canvassers-format header differs from a standard meeting), so this ceremonial certification
motion is absent from `all_votes.csv`. Impact is **1 motion / 5 vote rows** on a non-legislative
canvass — no effect on any legislative tally — but it is a genuine miss (not an honest source gap).
**Logged to `TODO.md`** for a targeted extractor patch. All other short (<450-word) meetings were
confirmed to be genuine special/retreat/electronic meetings, not missed extractions.

## 8. Date coverage vs the 2020 floor — PASS

- **Council:** 2020-01-14 → 2026-06-09.
- **Planning Commission:** 2020-01-09 → 2026-05-28.

Both start at the collection's standard **2020** floor (Draper is a long-established city — 2020 is a
normal floor, not an incorporation edge). No interior year is empty.

## 9. Known gaps — all honest, all logged

*[State as of the 2026-07-11 verification; superseded 2026-07-16 by the PMN minutes promotion —
see the addendum. The 3 broken-stub gaps are HEALED (promoted, `source=pmn`), the 2023-10-15 and
2024-03-14 rows were found to be record errors and removed.]*

Recorded in `meeting_minutes/minutes_unrecovered.csv` / `planning_commission/minutes_unrecovered.csv`,
never stubbed:

- **3 broken Granicus docs** (host serves a ~299-byte non-PDF stub for a listed document):
  Council **2021-07-20**, PC **2020-12-10**, PC **2024-10-10**. *(Healed 2026-07-16.)*
- **2 no-minutes-posted** meetings: Council **2023-10-15**, PC **2024-03-14**. *(Both removed
  2026-07-16 — the first was a phantom date, the second a stale row; see addendum.)*
- **Pending adoption** (too recent): Council **2026-07-07** (`recap_only_pending` — only the tally
  Recap posted), PC **2026-06-11 / 2026-06-25 / 2026-07-09**.
- **Faithful source limits (not gaps):** some 2020–2021 narrative motions name only the in-favor
  side, leaving a tally with unnamed members — retained verbatim, never Present-filled.

## 10. Election cross-check vs outside sources — PASS (one method caveat)

Outside sources: KSL.com municipal-results roundups, the *Draper Journal*, and the certified
Salt Lake County / Utah state results portal.

| Year | Race | Repo (`draper_races.csv`) | Outside source | Verdict |
|---|---|---|---|---|
| 2013 | Mayor | **Troy K. Walker** 2,127 / 51.8% over P. Shell | Walker first elected mayor 2013 (record) | ✅ match |
| 2017 | Mayor | **Troy K. Walker** 5,843 / 54.7% over M. Weeks | Walker re-elected 2017 | ✅ match |
| 2021 | Mayor | **Troy K. Walker** 5,360 / 100% (uncontested) | *Draper Journal*: "incumbents emerge victorious" | ✅ match |
| 2021 | Council (Vote-for-1) | **Tasha Lowery** 3,105 / 36.95% over H. Huh | *Draper Journal*: incumbent Lowery won | ✅ winner match — **RCV caveat** ↓ |
| 2023 | Council At-Large (3 seats) | winner **Fred Lowry**; first-loser Jordan Davis | KSL: **Lowry** top (Roberts, Johnson also seated); **Davis** 4th/first-loser | ✅ winner + order match ↓ |
| 2025 | Mayor | **Troy K. Walker** 5,910 / 72.35% over B. Rutherford 2,259 | KSL/*Draper Journal*: Walker 72.35%, Rutherford 27.65% | ✅ **exact** |
| 2025 | Council (2-yr, Vote-for-1) | **Kathryn Dahlin** 4,518 / 55.61% over B. Byington 3,606 | Dahlin ~55.6% over Byington | ✅ winner + margin match |

**All four Walker mayoral wins (2013 / 2017 / 2021 / 2025) confirmed.** The 2025 mayor row is an
**exact** match to the external totals — validating the **2025 raw-SOVC re-parse** the build did to
work around the upstream Salt Lake County long-file bug (dropped `25DR0N` Utah-vintage precinct
labels; see `SOURCES.md` / `TODO.md`). The 2025 council row differs from an election-night unofficial
count by ~19 votes (certified SOVC vs unofficial) — direction and winner identical.

**Caveats surfaced (both benign, both worth a reader flag):**
1. **2021 was Ranked-Choice Voting**, not plurality — Draper ran the RCV pilot that year. The repo
   row labels `voting_method=plurality` and stores **first-choice** tallies. The first-choice leader
   (Tasha Lowery) also won the RCV final, so the **winner is correct**, but the recorded `winner_pct`
   (36.95%) is a first-choice share, **not** the RCV-final share. Treat like Millcreek RCV: take the
   winner from the row, do not quote the pct as a final margin. *(Consider annotating the 2021 rows'
   `note` / `voting_method` in a future pass.)*
2. **2023 absolute totals** in the repo are the **certified SOVC** finals (Lowry 4,443); the KSL
   figure (3,914) was election-night unofficial. Winner and candidate ordering match; the totals
   difference is unofficial-vs-certified, expected.

## 11. Derived layers — consistent

- **`weeks/`** — 149 weekly bundles on the Monday grid (`MEETING_WEEKDAY=1`, council Tuesday)
  *(151 bundles / 3,848 rows after the 2026-07-16 promotion — see addendum)*. The
  weekly `votes.csv` sum is **3,805 == the flat Council total** *(now 3,848 == 3,848)*. `weeks/` buckets only the
  `meeting_minutes/` (Council) dataset — **this is the collection-wide convention** (Taylorsville and
  South Jordan `weeks/` likewise contain only Council/RDA/MBA, never PlanningCommission). PC votes are
  analyzed via `planning_commission/all_votes.csv` and `db/civic.db`, not the weekly bundles. Not a gap.

---

### Addendum log
- *2026-07-11* — Initial verification (this document). PASS / 0 FAIL; one logged extraction miss
  (2025-08-26 canvass, §7) and the 2021-RCV method caveat (§10) queued for follow-up.
- *2026-07-16* — **PMN minutes promotion** (`pmn_backfill/` → audited layers; backups in
  `_backups/2026-07-16-minutes-promotion/draper/`). **6 meetings promoted** with
  `minutes_index.csv` `source=pmn` and a new trailing **`provenance`** column in both
  `all_votes.csv` files (`minutes` = audited Granicus, `pmn_minutes` = PMN recovery):
  - **Council 2021-07-20** (heals the broken-stub gap; 7 motions / 35 named rows — narrative
    roll-calls, all 5-0) and the **3 August Truth-in-Taxation specials Granicus never listed**:
    **2022-08-24** (TRSSD Res #22-46, 5-0 grid roll call), **2024-08-14**, **2025-08-13**
    (hearing-only meetings; 1 tally-only adjournment motion each). Council: 151→155 docs,
    871→882 motions, 3,805→3,848 rows; contested unchanged (15).
  - **PC 2020-12-10** (COVID-era electronic; 4 motions / 24 named rows via the one-off
    "Vote: AYE: <names>" block form — parser extended additively, **zero-diff proven on all 141
    audited PC docs**; source names SIX ayes incl. the seated alternate while printing "5 to 0"
    — both kept verbatim) and **PC 2024-10-10** (9 motions / 65 rows, standard grids; Shah
    Not-Participating on 8 motions → PC contested 206→214). PC: 141→143 docs, 898→911 motions,
    4,212→4,301 rows.
  - **Row-level diff:** strictly additive — 0 rows removed in either dataset.
  - **Ordinance linkage resolved:** #1494 / #1496 / #1497 now match their enacting motions
    (2021-07-20 m3/m4/m5, each `5-0 Pass`) at **high** confidence; ordinances linkage
    179→182 high, 8→5 none.
  - **Referral layer:** the promotion generated 1 new medium candidate (Council 2021-06-01 ←
    PC 2020-12-10) — hand-verified a **generic-token false positive** (Ord #1492 temporary
    signage vs Chandler Pointe site plan) and suppressed via `db/referral_overrides.csv`;
    net referral count unchanged (5 medium).
  - **Record hygiene:** removed the stale PC `minutes_unrecovered.csv` row for **2024-03-14**
    (that doc has been in the PC index all along — `minutes/2024/2024-03-11/`); removed the
    phantom Council row for **2023-10-15** — 2023-10-15 was a **Sunday**, no such meeting or
    document exists on Granicus or PMN, and both sources hold the real **2023-10-17** minutes
    (already indexed). PMN's complete October-2023 notice history (bodies 5555) confirms
    meetings on 10-03, 10-05, 10-17 only.
  - `validate_city.py`: **24 PASS / 2 WARN / 0 FAIL** (both WARNs = the documented
    `provenance` column extension). weeks/ vote sum 3,848 == flat total.
- *2026-07-19* — **Two §7/§10 follow-ups closed** (backups
  `_backups/2026-07-19-pv-tierb-low/draper/`; scope: `draper_city_council/` only).
  - **§7 — 2025-08-26 Board of Canvassers extraction MISS → RESOLVED.** Root cause: the
    canvassers minutes use the title **"Board Member"** in the mover/seconder lines
    (`Board Member Green moved to approve Resolution #25-42…`), which `MOVE_RE`/`SECOND_RE`
    did not recognize; the roll-call **grid** rows themselves print the standard
    "Councilmember", so the grid parsed cleanly once the motion was detected. Fix:
    `meeting_minutes/extract_votes.py` — added `Board\s*Member` to `NAME_PREFIX` and a guard
    that skips a "Board Member"-moved motion carrying **no** grid (the pro-forma tally-only
    adjournment) so no blank placeholder row is emitted. Re-extracted (deterministic baseline
    re-run first confirmed byte-identical reproduction): **diff exactly +1 motion / +5 vote
    rows on 2025-08-26, 0 rows removed, all 150 other council meetings byte-stable.** The
    captured motion (motion_no 1, `motion_type=Appointment` from the classifier, `4-0 Pass`):
    Green `Aye`, Johnson `Aye`, T. Lowery `Aye`, Vawdrey `Aye`, F. Lowry `Absent` — verified
    verbatim against `minutes/2025/2025-08-25/2025-08-26_city-council-canvassers.md`. The
    seconder (T. Lowery) is left **blank** — it wraps across a pdftotext line break; an honest
    under-capture, never fabricated. Council: 882→**883** motions, 3,848→**3,853** rows;
    contested unchanged (15); `mayor_votes` unchanged (1 — Walker not in the canvass grid).
    Rebuilt normalize_motions/db/build_referrals/build_weeks: db reconciles (7,838 CSV named ==
    7,838 db votes, 1,794 motions), **referrals 5 medium** (the 2021-06-01←2020-12-10
    suppression override still binds — its app_keys are unaffected by a 2025 motion), weeks sum
    **3,853 == flat total**.
  - **§10 caveat 1 — 2021 RCV rows labelled plurality → ANNOTATED.** `draper_races.csv` is
    **script-generated** (`clean_elections.py`), so fixed at the script layer (an `RCV` set +
    `NOTE` entry) per the documented change path, mirroring the **Millcreek convention**
    (`voting_method='ranked choice (RCV)'` carries the caveat; first-choice tallies retained
    verbatim). Regenerated: **diff touches only the 2021 council-general row** — `voting_method`
    `plurality`→`ranked choice (RCV)` and a new `note` ("RCV pilot (2021) — winner_pct is a
    first-choice share, not the RCV-final margin; winner led first choice and won the final
    round"); winner (Tasha Lowery 3,105 / 36.95%), tallies, runner-up and margins **unchanged**;
    `draper_results_by_candidate.csv`/`by_precinct.csv` **byte-stable**. The 2021 **mayor** row
    (single candidate, uncontested, 100% — no ranking occurred) intentionally stays `plurality`.
    Docs updated: `election_results/CLAUDE.md` (new "Ranked-choice voting — the 2021 pilot"
    section; corrected the stale "Draper is not RCV" line) + main `CLAUDE.md`.
  - `validate_city.py`: **24 PASS / 2 WARN / 0 FAIL** (both WARNs = the documented `provenance`
    column extension — unchanged; no new warnings). weeks/ vote sum **3,853 == flat total**.
