# VERIFICATION — Herriman City civic-data repo

Independent QA of the Herriman City Council + Planning Commission datasets, run
**2026-07-11** (browser UA for all network checks). This is a second-pass audit by a
verification agent that did **not** build the data; it reconciles the doubly-stored facts,
ground-truths random meetings against source markdown, confirms the structural
**mayor-votes** finding at source, verifies the 2020 S3-recovered documents, and
cross-checks election winners/margins against outside sources.

**Verdict: PASS on every built dataset — 0 FAIL.** `scripts/validate_city.py .` reports
**25 PASS / 0 WARN / 0 FAIL** (re-validated after the 2026-07-11 post-audit PC remediation —
see the Addendum at the bottom of this file). One recon-stage assumption is **CORRECTED**
below (the Mayor was assumed non-voting; the source shows the Mayor votes as a full member).

---

## 1. Council votes — PASS

| Check | Result |
|---|---|
| Minutes docs: index rows == markdown files == per-meeting JSON | **182 == 182 == 182** ✅ |
| Date coverage | 2020-01-08 → 2026-05-27 (2020 floor honored) ✅ |
| Source split | 156 `primegov` + **26 `s3-legacy`** (2020 backfill) ✅ |
| Format | 180 `text` (born-digital) + 2 `ocr` ✅ |
| Distinct motions (`source`,`motion_no`) | **1,120** ✅ (== `motions_std.csv`, == db) |
| Vote rows in `all_votes.csv` | **3,691** (Council 3,614 · CDRA 32 · HCSEA 12 · HCFSA 33) ✅ |
| Named rows (member non-blank) | 3,216 · tally-only placeholders 475 ✅ |
| `validate_votes.py` | rows=3,691 motions=1,120 · schema-defects 0 · doubles 0 · HARD FAILURES 0 ✅ |

Per-year council rows: 2020 (420) · 2021 (590) · 2022 (528) · 2023 (472) · 2024 (672) ·
2025 (729) · 2026 (280) — a continuous, growing record with no interior year hole.

## 2. Planning Commission votes — PASS

| Check | Result |
|---|---|
| Minutes docs: index == markdown == JSON | **130 == 130 == 130** ✅ |
| Date coverage | 2020-01-02 → 2026-05-20 ✅ |
| Source split | 111 `primegov` + **19 `s3-legacy`** ✅ |
| Distinct motions | **850** (pc_final_action 529 · pc_recommendation 321 in db) ✅ |
| Vote rows | **3,369** (all `body=PlanningCommission`) · named 2,964 ✅ |
| `validate_votes.py` | clean; tally match 20/22 named rolls (2 known, documented) ✅ |

## 3. Relational db (`db/civic.db`) — PASS, reconciles exactly

```
body 5 · person 22 · meeting 288 · application 529 · motion 1,970 · vote 6,180
       · role 38 · referral 39
```
- **Motion reconciliation:** db 1,970 = council-file 1,120 (Council 1,091 + CDRA 16 +
  HCFSA 9 + HCSEA 4)  +  PC 850. Exact.
- **Vote reconciliation (fail-loud):** **CSV named rows 6,180 == db votes 6,180, delta +0.**
  Council-file 3,216 (Council 3,156 + CDRA 20 + HCFSA 30 + HCSEA 10) + PC 2,964. `validate_city.py`
  check `h.db` confirms.
- **Meeting count (288) < docs (312):** 24 minutes docs carry **no motion** (special/closed-
  session/adjournment-only meetings — e.g. 2021-03-05, verified below) and correctly produce
  no `meeting` row. Not a defect.
- Vote values: Aye 5,406 · Absent 627 · Nay 132 · Abstain 1 · Excused 14. Contested motions
  (`v_contested`): **88**. Referrals: 39 Council←PlanningCommission (**17 high / 18 medium /
  4 low** — respect the confidence column; do not quote `low`).
- Weekly bundles: `weeks/` sum **3,691 == flat council total** ✅.

## 4. ⚠ CORRECTION CONFIRMED AT SOURCE — the Herriman MAYOR VOTES

`recon.md` (§4) assumed **"max council tally = 4, Mayor non-voting on ordinary motions."**
**This is WRONG and is corrected here.** Herriman uses the Utah six-member form in which the
**Mayor is a full voting member** (the Millcreek model, not the Taylorsville/South Jordan
executive-mayor model). A full council roll call = **5** (4 districts D1–D4 + Mayor).
Confirmed by quoting real roll calls from the source markdown:

**Mayor David Watts (2020–2021) casts a decisive NAY — `2020-01-08` motion 5**
(`minutes/2020/2020-01-06/2020-01-08_city-council-meeting.md`, lines 434–441):
```
The vote was recorded as follows:
Councilmember Jared Henderson         Aye
Councilmember Sherrie Ohrn            Aye
Councilmember Steven Shields          Aye
Councilmember Clint Smith             Nay
Mayor David Watts                     Nay

The motion passed with a vote 3:2
```
The Mayor is inside the roll and his Nay is counted — a 5-member tally, not 4.

**Mayor Lorin Palmer (2022+) — `2023-01-11` motion 2**
(`minutes/2023/2023-01-09/2023-01-11_city-council-meeting.md`, lines 521–529):
```
The vote was recorded as follows:
Councilmember Jared Henderson        Yes
Councilmember Teddy Hodges           Yes
Councilmember Sherrie Ohrn           Yes
Councilmember Steven Shields         Yes
Mayor Lorin Palmer                   Yes
```
And a **contested** 2025 example — `2025-01-22` motion 6: Henderson/Hodges/Shields/**Palmer**
Aye, **Ohrn Nay** (a 4-1 with the Mayor in the majority). In the extracted data Mayor David
Watts carries **167** vote rows and Mayor Lorin Palmer **478** council vote rows — both are
first-class voters, exactly as the source prints them. The extractor's `Yes→Aye`
normalization is faithful.

## 5. 2020 S3-legacy recovery — PASS (real minutes with real votes)

PrimeGov only serves back to 2021-01; 2020 minutes were recovered from the city's legacy
AWS bucket (`s3-us-west-1.amazonaws.com/herriman-agendas/2020-agendas/…`).
- **Council:** all **26** s3-legacy docs carry vote rows (**420** rows total; 15 with named
  rolls — the 2020 clerk printed the full Mayor+member roll, which is exactly where the
  mayor-votes finding first surfaces).
- **PC:** **19** s3-legacy docs, 18 with votes (**544** rows; the one vote-less doc is a
  meeting with no roll-call motion).
These are genuine minutes, not agendas — the roll-call prose parses identically to the
PrimeGov era. 2020 interior date gaps are **real COVID-era cancellations** (confirmed 403s
at the portal, per recon); there is **no `minutes_unrecovered.csv`** because no expected
meeting is missing beyond those cancellations.

## 6. Random-meeting ground-truth (7 meetings, markdown vs extracted rows) — PASS

| Meeting | Extracted | Source check |
|---|---|---|
| Council 2021-03-05 special | 0 motions | ✅ source is Closed Session + Adjournment only — **no roll call** (correct empty) |
| Council 2023-01-11 | 8 motions / 24 rows | ✅ named 5-member rolls incl. Mayor Palmer match markdown exactly |
| Council 2022-03-30 joint w/ PC | 2 motions | ✅ tally-only, matches |
| Council 2025-09-16 special | 3 motions / 11 rows (10 named) | ✅ |
| PC 2020-08-20 | 6 motions / 26 rows | ✅ incl. a 5-1 with Rypien Nay; surfaces the `Lorin Powell` source typo (below) |
| PC 2020-11-19 | 7 motions / 32 rows (30 named) | ✅ |
| PC 2021-03-04 | 4 motions / 14 rows (12 named) | ✅ named commissioner rolls (recovered in the 2026-07-11 PC remediation) |

**Documented source typo retained verbatim — "Commissioner Lorin Powell".** Exactly **4 PC
rows** in 2020 (2020-08-20 m2, 2020-09-17 m2, 2020-11-19 m1 & m2) print `Lorin Powell`, a
clerk conflation of two real people (Commissioner **Andy Powell** and Commissioner/soon-Mayor
**Lorin Palmer**, both seated in 2020). Kept as-is — never guess-merged. Flag on any
person-level 2020 PC join.

## 7. Election cross-check vs OUTSIDE sources — PASS (no material mismatch)

`election_results/herriman_races.csv` = **38 races, 2007–2025**. The repo's figures are the
**final Salt Lake County certified canvass**; outside election-night reports run slightly
lower (partial counts) — every winner, order, and margin agrees.

| Race | Repo | Outside source | Verdict |
|---|---|---|---|
| **2021 Mayor** | Palmer 4,291 (63.21%) def. Clint Smith 2,498; margin 1,793 | Deseret/KUTV election-night: Palmer 62.4% / Smith 37.6%, +1,547 (partial 3,853 for Palmer) | ✅ MATCH — repo = final canvass, higher than the election-night partial; pct within 0.8 pt |
| **2023 D1** | Henderson 837 (54.42%) def. Chris Roberts 701; margin 136 | Herriman Journal: Henderson 834 (54.44%) / Roberts 698 (45.56%) | ✅ MATCH — 3-vote canvass-vs-preliminary variance, same winner & pct |
| **2023 D4** | Steven L. Shields 908 (65.61%) def. Matt Bello 476 | (unopposed-adjacent; Journal confirms Shields reelected) | ✅ |
| **2025 Mayor** | Palmer 6,884 (75.23%) def. Ty R. Brady 2,267; margin 4,617 | SLCo/press: Palmer **6,884** def. Brady **2,267** | ✅ EXACT |
| **2025 D2** | Hodges 1,959, unopposed | Hodges 1,959 unopposed | ✅ EXACT |
| **2025 D3** | Basham 1,583 (56.94%) def. Heather Garcia 1,197 | Basham (elected) / Garcia **1,197** | ✅ MATCH (winner + Garcia exact; minor winner-vote variance vs preliminary) |
| **2025 D4 (2-yr short term)** | Terrah Anderson 1,431, unopposed off-cycle special | Anderson 1,431 unopposed | ✅ EXACT — correctly flagged as a special in `note` |

**Recovered election years (not gaps):** **2019** (mislabeled in the shared county file —
recovered from the raw SOVC), plus **2011** and **2021** generals recovered from raw SOVC.
All present in the 38-race file with continuous odd-year coverage 2007→2025.
Salt Lake County certified 2025 report available on Utah PMN (notice 1040025).

## 8. Public comments — HONEST-EMPTY (verified)

`all_comments_clean.csv` is header-only (14-col schema, 0 rows) by design.
`public_comments/AVAILABILITY.md` documents the completed 2026-07-11 audit: Herriman's only
public-comment channels are **submit-only** (PrimeGov eComment "Add a new comment" form +
"Request To Speak"), tied to a live/upcoming meeting — **no retrievable written-comment
archive**. This is a legitimate honest zero, not an acquisition gap. Do not fabricate rows.

## 9. Known gaps / caveats (all honest, all logged)

- **2020 COVID cancellations** — real (confirmed portal 403s); not stubbed.
- **24 zero-motion minutes docs** (special/closed-session/adjournment-only) — indexed, but
  correctly produce no vote rows and no db `meeting` row.
- **Geo is current/post-2020 vintage** — official 4-district FeatureServer polygons; an
  address near a moved boundary may mis-assign for pre-redistricting questions.
- **Cross-city:** `result`/`motion_type` are Herriman-native — aggregate only via
  `motions_std.csv` + repo-root `crosswalks/`, never the raw strings.

---
*Method: reconciliation via `csv`/`sqlite3`, source ground-truth by reading the canonical
markdown, election cross-check via WebSearch/WebFetch (browser UA). No canonical CSV or
minutes file was modified. Extend this file with dated addenda on any future repair/re-audit.*

---

## Addendum 2026-07-11 — post-audit PC remediation

A follow-up audit of the Planning Commission extractor (dated report:
`_audits/audit_2026-07-11.md`, retained AS-IS as the pre-fix record) found three real
defects; all three are now **fixed**, and the whole repo was re-validated and re-federated.
The body of this VERIFICATION file above has been refreshed to the post-fix ground truth.

**Findings → fixes:**
1. **~75 missing named PC roll-call motions (~17% of the PC record).** The PC extractor was
   dropping named commissioner rolls on a minutes-prose variant it didn't match. **Fixed:**
   PC grew **670 → 850 motions** (445 named / 405 tally-only) and **2,784 → 3,369 vote rows**
   (2,964 named); s3-legacy 2020 PC rows 471 → 544. The db PC stage split is now
   pc_recommendation 321 · pc_final_action 529 (was 264 · 406).
2. **Mover/seconder over-capture polluting the `person` table (~165 junk rows).** Names that
   appeared only as movers/seconders (and prose fragments) were being minted as `person`
   rows. **Fixed:** the `person` table is cleaned to **22** real officeholders (was ~195),
   including one legitimate source-typo merge **"Adam Jacbson" → "Adam Jacobson"**.
3. **4 CDRA named rolls dropped to tally-only.** Four Community Development & Renewal Agency
   motions that print a full named roll had been reduced to tally-only placeholders.
   **Fixed:** the 4 CDRA rolls are recovered — CDRA is now 16 motions (12 tally-only + 4
   named → **20** vote rows; CSV body total 16 → 32 rows). Council-file named vote rows
   3,191 → 3,216; db votes 5,670 → 6,180.

**False positive (confirmed, NOT changed):** the audit flagged a suspected "10-voter merge"
on **2025-04-02** (a PC roll with ten voters). Verified against the source markdown — this is
**faithful**: 7 seated commissioners **+ 3 alternates** all cast recorded votes that day. No
merge or edit was made; the 10-voter roll stands as printed.

**Re-validation & refederation.** `scripts/validate_city.py .` now reports **25 PASS / 0 WARN
/ 0 FAIL**. Derived layers were rebuilt from the corrected flat CSVs (`db/build_db.py` +
`db/build_referrals.py`, `build_weeks.py`, `motions_std.csv`) and the repo was re-federated
into the collection `cities.db`. Post-fix db: person 22 · meeting 288 · application 529 ·
motion 1,970 · vote 6,180 · role 38 · referral 39 (17 high / 18 medium / 4 low) · v_contested
88. The 2020 `Lorin Powell` source typo (4 PC rows) remains retained verbatim — it is a
distinct, deliberately-unmerged conflation, unaffected by the person-table cleanup.

## Addendum — 2026-07-16: PMN minutes promotion + wrong-doc repairs

**Task:** promote the `pmn_backfill/` recoveries into the audited vote layer (TODO
"Herriman expansion follow-ups (a)"), per the ogden/vineyard/orem/south_jordan
provenance-tagged merge pattern. Backups of every modified canonical file:
`../_backups/2026-07-16-minutes-promotion/herriman/`.

**Promoted (66 docs → `provenance=pmn_minutes`):**
- council-family (55 → `meeting_minutes/all_votes.csv` via new
  `meeting_minutes/extract_backfill_votes.py`): 21 Council (2020-03-25 … 2023-12-15,
  incl. the 2023-12-05 Special Board of Canvassers and the real 2021-01-13 RCCM minutes
  fetched from PMN file 690779 during this pass), 5 Joint CC/PC (merged as
  `body=Council`, matching the audited joint-doc convention), 13 CDRA, 10 HCSEA,
  6 HCFSA (2020-05-27 … 2026-03-25).
- PC (11 → `planning_commission/all_votes.csv` via new
  `planning_commission/extract_backfill_votes.py`): 2020-12-03 … 2025-05-21, incl. 3
  tesseract-OCR scans.

**Rejected (permanent `pmn_backfill/` sidecars, never merged):** 2021-01-13 CDRA
(duplicate — see repair 1), 2023-11-01 PC (stamped "Pending Formal Approval / Draft"),
2022-04-21 PC (the PMN file named "…PC_Minutes.pdf" is a mislabeled zoning use-table /
agenda attachment, PDF title "Planning Commission Agenda" — not minutes), and both
AppealAuthority hearings (2025-02-20, 2026-06-09 — no appeals body exists in the city
model; catalogued only, modeling deferred).

**Wrong-doc repairs in the audited layer (verified at source, raw PDFs retained):**
1. **2021-01-13 "City Council Meeting" is the CDRA minutes** (in-body header: "SPECIAL
   COMMUNITY DEVELOPMENT AND RENEWAL AGENCY … MINUTES"; PrimeGov mistitles the slot).
   Front-matter `Body:` corrected Council→CDRA (+ index title updated); its 2 motions
   re-extracted as CDRA. The real RCCM minutes for the date exist on PMN (notice 649887)
   and were fetched + promoted.
2. **Both 2021-10-13 PrimeGov compiled docs (templateIds 547, 553) deindexed** — 547 is a
   bare agenda; 553 is agenda + attachments whose attachment is the FULL 2021-08-11
   minutes (item 8.1 approval), from which the extractor had produced **18 motions / 58
   vote rows mis-dated 2021-10-13**. The genuine 2021-10-13 minutes (templateId 563,
   `…work-meeting-2.md`, "Approved December 8, 2021") remain indexed with its 8 motions.
   The 18 removed motions all reappear correctly dated via the promoted 2021-08-11 doc
   (row-level diff verified exact). Corpus-wide scan for the embedded-foreign-minutes
   class found only this doc (the 2023-06-14 doc's "April 26, 2023" page footers are a
   clerk template error in genuinely-June minutes — retained verbatim).
3. **Dropped-verb motion lead-ins healed** (`DROPPED_VERB_RE`, both extractor copies):
   exactly 3 corpus lines print "<Role> <Name> to approve …" with "moved" omitted —
   2021-08-11 Ordinances 2021-19 + 2021-21 and the audited 2023-08-02 PC item 4.1. All 3
   motions (full named rolls) are now captured; the 2023-08-02 4.1 roll had additionally
   been mis-attributed to the preceding close-hearing motion (now tally-only per source,
   "all voted aye").
4. **`Darryl Finn` → Darryl Fenn** added to `CANON_FULL` (one 2021-06-17 PC roll row;
   the same doc prints Fenn in 9 other rolls — unambiguous same-person typo).

**Ordinance 2021-17/18/20 ambiguity RESOLVED:** the promoted 2021-08-11 minutes show all
five ordinances 2021-17…2021-21 adopted that day with named rolls (17/18: 3-0 with Ohrn +
Watts absent; 19: 3-0 same absences; 20: 4-0 with Watts absent; 21: 4-0 with Watts
absent). The "identical-subject 2021-10-13 motions" were the embedded copy (repair 2).
`ordinances/build_index.py` rebuilt: all five link **high** to 2021-08-11 motions; 15 rows
changed overall (several 2020 `none`→`high` against the recovered 2020 meetings), 4
ordinances newly indexed from recovered citations (2020-30, 2021-02, 2022-12, 2023-22);
index 274 → 278 rows.

**Retained source anomalies (verbatim, never corrected):** 2020-05-27 HCSEA roll prints
"Trustee Nicole Martin" (a 2019-era trustee; attendance lists Shields) — the meeting was
approving 2019 HCSEA minutes and the roll appears to be a stale template; 2023-01-04 PC
OCR header-year misprint; the `Lorin Powell` conflation now counts 5 PC rows (the
promoted 2020-12-03 m4 adds one). New KNOWN tally quirk documented in
`meeting_minutes/validate_votes.py`: 2020-09-30 m1's result cites "Utah Code Annotated
52-4-204" (2/3 closed-session supermajority), which motions_std's tally regex reads as
52:4 — the extracted 3 Aye / 2 Nay FAILED roll is verified correct (a genuine
supermajority failure, Smith + Mayor Watts dissenting).

**Ground-truth spot-checks (all exact vs source):** 2020-09-30 m1 (Council supermajority
failure), 2020-03-25 m3 (Ord 2020-09, Henderson absent), 2021-01-13 m4 (new fetch),
2021-08-11 m9/m10/m11 (Ordinances 2021-17/18/20), 2023-12-05 m1 (canvass, Yes-form roll),
CDRA 2024-05-08 m2 (present-tense "vote is recorded", Director roles), HCSEA 2022-05-11
m1 (Ohrn absent), PC 2020-12-03 m2 (5 ayes / 1 abstain, Ferguson), PC 2023-01-04 m4
(Fenn Recuse — Herriman's first Recuse row, crosswalk row added).

**Result:** council-family 1,120 → **1,343 motions** / 3,703 → **4,322 rows** (named
3,231 → 3,726; provenance `minutes` 3,645 / `pmn_minutes` 677; bodies: Council 1,209 ·
CDRA 64 · HCSEA 39 · HCFSA 31 motions); PC 850 → **921 motions** / 3,369 → **3,642 rows**
(named 2,964 → 3,206; 272 `pmn_minutes`). Named-dissent contested motions: council 48 →
54, PC 43 → 51. Row-level diff (source, date, body, motion_no, member, vote): the ONLY
removals are the two repaired docs (60 + 14 rows), all accounted for above. db rebuilt:
2,264 motions / 6,932 votes, reconciles exactly; referrals 39 → 51 (23 high / 22 medium /
6 low). `minutes_unrecovered.csv` created in both datasets (2020-07-29 joint; PC
2022-04-21 + 2023-11-01). `scripts/validate_city.py` → **24 PASS / 2 WARN / 0 FAIL** (the
2 WARNs are the documented `provenance` extra column). Federation into `cities.db` is
deliberately left to the orchestrator.
