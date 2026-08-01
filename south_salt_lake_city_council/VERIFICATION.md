# South Salt Lake City Council — VERIFICATION

Independent QA of the built repo. Method: reconcile every doubly-stored fact (index ↔ disk ↔
JSON ↔ flat CSV ↔ db ↔ weeks), ground-truth motions against the source minutes, confirm the
structural invariants (mayor non-voting, max tally 7), verify the honest-gap record, and
cross-check election winners against outside sources. **No data was modified.**

**Verdict: PASS on every built dataset, 0 FAIL.** `scripts/validate_city.py
south_salt_lake_city_council` = **22 PASS / 3 WARN / 0 FAIL** (the 3 WARNs = the now-created
top-level docs + the two documented `minutes_index` extension columns).

Verified 2026-07-12.

---

## Dataset grades

| Dataset | Result | Basis |
|---|---|---|
| Council + RDA minutes | **PASS** | 34 md == 34 index rows; born-digital, corpus screener 0 outliers; coverage cliff logged (below) |
| PC minutes | **PASS** | 45 md == 45 index rows; corpus screener 0 outliers; 2020–2022 honest gap logged |
| Council + RDA votes | **PASS** | 142 motions / 985 named rows; ground-truthed; tally 142/142; mayor non-voting confirmed |
| PC votes | **PASS** | 238 motions / 1,291 rows (1,290 named + 1 tally-only); ground-truthed; tally 237/237 |
| Relational db | **PASS** | 2,275 named CSV rows == 2,275 db votes (delta 0); integrity OK; referral 0 (honest) |
| Public comments | **PASS (honest-empty)** | submit-only; `all_comments_clean.csv` header-only, verdict in AVAILABILITY.md |
| Election results | **PASS** | 52 races; winners cross-checked vs outside sources (below); 2011/2019/2021 recoveries verified |
| Geo | **PASS** | SSL's own 5 official district polygons; tool tested (City Hall → D1) |
| Weekly bundles | **PASS** | weekly council/RDA vote sum 985 == flat total; weeks/ newer than canonical CSVs |

---

## 1. ⚠ The coverage cliff — prominently documented as an HONEST GAP

**This is the single most important fact about this repo and is verified, not a scraper miss.**
South Salt Lake's recorded minutes live only on Utah Public Notice (PMN); the PMN "Meeting
Minutes" attachment slot **very often serves the AGENDA PACKET** (a multi-MB PDF headed
"REGULAR MEETING AGENDA", no roll call) **even when the file is labelled `… RC Minutes.pdf`.**
The harvester content-detects every candidate (roll-call grammar is the only reliable test)
and logs agenda-only dates as honest gaps.

**Result: recorded council minutes exist essentially only for 2020–early-2021 plus sporadic
recent meetings; 2021-mid → 2025 the slot served agenda packets only.**

- **253 council** agenda-only dates logged in `meeting_minutes/minutes_unrecovered.csv`
  (`reason=agenda-only/minutes-not-posted`). Plus **48 RDA** and **19 PC** gaps (301 total).
- **PC recorded minutes begin 2023-01-19** — 2020–2022 were never published (agendas only).

**Direct proof (re-fetched live 2026-07-12):** PMN file `963367`, labelled
**`2023.02.22RC Minutes.pdf`**, downloads as a 4.6 MB PDF whose text begins
`"South Salt Lake City Council / AMENDED REGULAR MEETING AGENDA … Wednesday, February 22,
2023"` and contains **0** occurrences of the roll-call grammar (`Roll Call Vote:` / `Voice
Vote:` / `Name: Yes`). The content-detector correctly rejected it and logged 2023-02-22 as an
agenda-only gap. A second-order consequence — the **db referral layer is empty (0 links)** —
follows honestly, because the Council side of most 2023–2025 PC recommendations is in this gap
(see `db/SCHEMA.md`). **The thin council record is data, not a defect.**

---

## 2. Reconciliation — index ↔ disk ↔ JSON ↔ CSV ↔ db ↔ weeks (all exact)

| Fact stored twice | Side A | Side B | Result |
|---|---|---|---|
| Council/RDA minutes files vs index | 34 md on disk | 34 `minutes_index.csv` rows | ✅ equal |
| PC minutes files vs index | 45 md on disk | 45 `minutes_index.csv` rows | ✅ equal |
| Motions: JSON vs CSV (Council/RDA) | 142 motions in `votes/*.json` | 142 in `all_votes.csv` | ✅ equal |
| Motions: JSON vs CSV (PC) | 238 | 238 | ✅ equal |
| Vote rows CSV total | 985 (MM) + 1,291 (PC) = 2,276 | — | 2,275 named + 1 tally-only blank |
| Named CSV rows vs db `vote` | 2,275 named | 2,275 db votes | ✅ delta 0 (validate_city `h.db`) |
| db motions by body | 109 Council / 33 RDA / 238 PC | 380 total | ✅ matches CSV |
| Weekly vote sum vs flat | 985 (weeks/*/votes.csv) | 985 (MM flat) | ✅ equal; weeks/ fresh |
| Synthesized tally vs counted rows | `f.tally` 142/142 + 237/237 | — | ✅ 100% match |

The single blank-member CSV row is the **PC 2023-01-19 "Motion to APPROVE the Agenda"**, a
tally-only procedural motion (`names_recorded:false`, one placeholder row, no members
fabricated) — correctly excluded from `vote` (2,276 − 1 = 2,275). This is honest source style,
per `planning_commission/CLAUDE.md`.

---

## 3. Structural invariant — strong-mayor, Mayor NON-voting, max tally 7

- **0** vote rows name the Mayor: no `member` value contains "Wood" across either dataset.
  Mayor **Cherie Wood** is absent from the db `person` table.
- **Max voters on any Council/RDA motion = 7** (e.g. RDA 2020-05-27 motion 1). **Max PC = 8.**
  `validate_votes.py` asserts 0 mayor-in-roll and 0 motions with >7 voters — both hold.
- The council **elects its own Chair** (Sharla Bynum, D3); a `Council Chair <Name>` roll entry
  maps to that councilmember. Confirmed strong-mayor form.

---

## 4. Ground-truth — motions vs the source minutes (quoted)

Six meetings sampled across bodies/years; every sampled motion's roll, dissent, and
**synthesized `<aye>-<nay>` result** matches the source PDF text exactly.

1. **RDA 2020-05-27** (body=RDA, PMN 629433) — motion 1 roll: `Bynum: Yes · deWolfe: Yes ·
   Huff: Yes · Mila: Yes · Pinkney: Yes · Siwik: Yes · Thomas: Yes` = **7-0**. Confirms the RDA
   board = the 7 councilmembers, 2020 roster; **Mayor Wood appears only as presenter**
   ("Mayor Wood advised that the RDA…"), never in the tally. ✅

2. **Council 2020-07-08** (body=Council, PMN 629441) — a 2020 council roll present and
   parsed; born-digital, line-numbered, names intact. ✅ (2020 is the well-covered floor year.)

3. **Council 2025-03-12** (PMN 1247409) — motion 2, "approve Tom Mills as a Civilian Review
   Board Alternate": `Bynum: Yes · Huff: Yes · Mitchell: Yes · deWolfe: Yes · Thomas: Yes ·
   Williams: Yes · Sanchez: No` = **6-1**, Sanchez the lone Nay. CSV `result` = `"6-1 Pass"`,
   dissent = Paul Sanchez. ✅ (synthesized tally matches the roll)

4. **Council 2026-06-17** (PMN 1454707) — motion 4, "approve the Ordinance (Public Safety
   Service Special Revenue Fund)": `Glad: Yes · Thomas: No · Bynum: Yes · Mitchell: No ·
   Jones: Yes · Williams: Yes · deWolfe: No` = **4-3**. CSV `result` = `"4-3 Pass"`, dissent =
   Thomas/Mitchell/deWolfe. ✅ A genuinely contested budget-ordinance split.

5. **PC 2024-01-18** (PMN 1086869) — motion 8, "forward a recommendation of APPROVAL to the
   City Council for the New Accessory Dwelling Unit Ordinance": `Bellina Yes · Ewell No ·
   Slifka No · Southey Yes · Spencer Yes · Pechmann Yes · Carter Yes` and the source itself
   prints **"The motion passed 5-to-2."** CSV `result` = `"5-2 Pass"`, dissent = Ewell/Slifka.
   ✅ Here the source printed a tally that matches the synthesized string exactly — strong
   evidence the synthesis logic is faithful.

6. **PC vote grammar** — the `Commissioner <Name> – Aye;` / `Vote:` format parses correctly;
   the retained faithful clerk typo `Oliva`/`Olivia Spencer` is present in the PC roster as a
   near-duplicate (not merged).

Corpus statistical screen (`screen_corpus.py`): **0/34 and 0/45** dict-ratio / split-word /
weird-char outliers; both corpora CLEAN (born-digital, no OCR).

---

## 5. Election winners — cross-checked against OUTSIDE sources (browser-UA web)

County SOVC winners in `election_results/south_salt_lake_races.csv` were confirmed against
independent reporting (Salt Lake Tribune, KSL, a public victory post):

| Year | Contest | CSV winner (votes) | Outside source | Match |
|---|---|---|---|---|
| 2025 | Mayor | **CHERIE WOOD** 2,203 vs Karzen 1,097 (66.8%) | SLTrib/KSL: Wood re-elected, 65.8% vs Brittany Karzen 34.2% | ✅ winner + challenger + margin direction |
| 2025 | At-Large (2-Yr special) | **G. RAY DEWOLFE** 2,183 vs Campos 959 | SLTrib results: deWolfe won the At-Large seat (~67%) | ✅ |
| 2025 | At-Large | **CLARISSA J. WILLIAMS** 2,660 (uncontested) | SLTrib: Williams 100% | ✅ |
| 2023 | District 4 | **NICK MITCHELL** 347 vs 314 | — (tight D4 race; internal-consistency + roster) | ✅ serving member |
| 2021 | Mayor | **CHERIE WOOD** 1,777 vs 678 | Public victory post "Congratulations Mayor Cherie Wood, Clarissa J. Williams…" | ✅ |
| 2021 | At-Large | **CLARISSA J. WILLIAMS** 1,490 vs 1,395 | same post confirms Williams won | ✅ |

**2026-07-31 — 2021 verified against the county's OFFICIAL RCV tabulation (new, strongest
check yet).** SSL was an RCV-pilot city; the Clerk's *Official Final Ranked Choice Results,
2021 General Election* (retained at `election_results/raw/2021-general-election-ranked-choice-
summary-report.pdf`, p.20 `CITY OF SOUTH SALT LAKE MAYOR`) publishes the round-1 table
independently of the SOVC spreadsheet this repo parses. **They agree exactly** — Wood
1,777/58.24%, Christensen 678/22.22%, Siwik 596/19.53%, continuing ballots 3,051 — matching
`south_salt_lake_results_by_candidate.csv` to the vote and to the hundredth of a percent. The
report also records *"Tabulation status: All Positions Filled"* with **only a Round 1 column**
(Wood cleared the 1,526 threshold), confirming the RCV final equals the stored first-choice
result. Consequence: the 4 rows were **relabelled `voting_method='RCV'`** (was `plurality`) —
label-only, no tally changed — and the long-suspected "missing 2021 primary" is **confirmed a
non-event**, since the pilot replaces the municipal primary. ✅

Notes: reported election-night percentages differ by ~1–2 pts from the certified SOVC totals in
the CSV (expected — unofficial vs canvassed), but every **winner** matches. One loose web
summary called the 2021 At-Large "unopposed"; the authoritative SOVC shows a real 1,490–1,395
margin — the CSV is correct. The **2025 At-Large (2-Year Term) special** (deWolfe) is verified
as an off-cycle unexpired-term seat (Pinkney → Salt Lake County Council; deWolfe appointed
Jan-2025), kept as its own contest.

---

## 6. Blind spots (an honest list of what this verification did NOT do)
- Ground-truthed 6 of 79 meetings; sampling favored contested motions and body/year spread. The
  corpus screener covered all 79 for statistical anomalies (clean).
- Election cross-check confirmed **winners**, not every vote total, against outside sources; the
  internal by-precinct sums were validated by the build (`clean_elections.py`, zero suppressed
  cells post-recovery) but not re-summed here.
- The 253 logged council gaps were spot-proven on **one** date (2023-02-22, both files
  re-fetched and confirmed agendas); the harvest log records the same reason for the rest.
- Geo tested at one address (City Hall → D1); polygon coverage not exhaustively swept.

---

## Addenda
_(Extend this file with a dated note whenever the data is repaired or re-audited.)_

- **2026-07-12** — initial verification (this document). See also `_audits/audit_2026-07-12.md`
  for the graded audit and SHIP verdict.
- **2026-07-16 — ArchivedMinutes promotion.** 119 of the 130 `pmn_backfill/` AgendaCenter
  recoveries were verified and promoted into the audited layer (Council 75 / RDA 29 / PC 15;
  2 rejected as agenda packets, 9 as content-duplicates of audited meetings — see
  `pmn_backfill/promote_to_audited.py` for the per-doc classification and reject reasons).
  Every promoted doc was re-classified from in-body content (date line, meeting banner,
  roll-call grammar): 41 council "WM"-labelled files are actually REGULAR-meeting minutes,
  the 2025-02-12 "RDA"-slot file is council minutes, 2024-08-07 is the Truth-in-Taxation
  hearing (kind TT), and 2024-09-25 / 2025-12-10 are regulars despite SM/BoC labels.
  Corpus now: Council/RDA 680 motions / 4,606 rows; PC 286 motions / 1,652 rows; db 966
  motions / 6,253 votes (reconciles delta 0); contested 68; referral layer 43 links.
  Extractor grammar was extended for the recovered clerks' forms (colon-less rolls,
  trailing commas, DRAFT-watermark fragments, "None"/typo values, "All present in favor"
  consent items) with **zero row regressions** on the pre-promotion corpus (the only
  pre-existing changes: +2 motions/+14 votes recovered in the 2020-09-17 SM whose
  colon-less roll had been silently missed, and 6 formerly description-less motions
  gaining their "moved to…" description). Ground-truth spot-checks: 8 motions across
  bodies/years/grammar-variants verified verbatim against source text (see
  `_backups/2026-07-16-minutes-promotion/` for pre-change canonical files).
  Statistics in sections above reflect the PRE-promotion corpus where they conflict;
  `COVERAGE.md` is the current authority.
