# Verification — Millcreek City council data repo

**Verification date:** 2026-07-06 · **Agent:** independent Phase-5 verification (did NOT build the data)
**Method:** adversarial re-check — reconciliation counts measured independently, ~8 motions
traced to source scans, all four election findings cross-checked against outside news sources,
corpus screener + `validate_votes.py` + `validate_city.py` re-run. READ-ONLY except this file.
**External sources cross-checked:** Deseret News, KSL, Salt Lake Tribune, Millcreek Journal,
Fox13, KUTV (URLs in the election section).

---

## Summary table

| Dataset | Status | Rows / files | Coverage | Notes |
|---|---|---|---|---|
| meeting_minutes (Council + CRA) | **PASS** | 372 md / 5580 vote rows (4245 named) | 2016-12 → 2026-06 | mayor votes (max tally 5) verified; named roll-calls 2022+; 2017-2021 genuinely tally-only |
| planning_commission | **PASS** | 149 md / 2840 vote rows (2476 named) | 2017-02 → 2026-05 | own PC; named commissioner rolls; referral language present; 13 unrecovered logged |
| election_results | **PASS** | 22 races | 2016 founding → 2025 | all 4 flagged findings (RCV / appointment / cancelled / founding) MATCH outside sources |
| public_comments | **PARTIAL** | AVAILABILITY.md only | — | verdict IN-PACKETS (real comments inside PC packet PDFs); Provo-style harvest not yet done (documented) |
| geo | **PASS** | 4 district polygons, 51 precincts | 2022-2032 vintage | address→district tool present |
| db (millcreek.db) | **PASS** | 6721 votes / 3016 motions | — | reconciles exactly to named CSV rows; 4 views present |
| weeks/ | **PASS** | 275 week dirs | — | regenerates fresh; weekly vote sum 5580 == flat total |

No FAILs. One PARTIAL (public_comments — a documented, deliberate pending-harvest state, not a defect).

---

## Reconciliation (independently measured)

- **Council minutes:** 372 md on disk == 372 `minutes_index.csv` rows == 372 indexed paths (all exist).
  Raw = 376 PDFs; **3 duplicate content-hashes** (md5-confirmed pairs) + **1 unrecovered**
  (2018-03-20 budget-only) → 376 − 3 − 1 = **372**. Reconciles exactly.
- **PC minutes:** 149 md == 149 index == 149 raw PDFs; 13 unrecovered logged separately in
  `minutes_unrecovered.csv` (not stubbed). Reconciles.
- **db vote rows = 6721** == council named (4245) + PC named (2476) = **6721**. Exact (validator
  reports delta +0). Tally-only (blank-member) rows — council 1335, PC 364 — correctly live only
  as motions, not as person-vote rows.
- **weeks/** = 275 week directories; `validate_city.py` confirms weekly votes sum to 5580 == flat total.
- **0 duplicate (date, meeting, motion_no, member) rows** in either body.

---

## No-fabrication findings (the core adversarial checks)

- **Distinct named voters = exactly the roster.** Council: 7 names, all real members
  (Uipi, C. Jackson, Marchant, Silvestrini, Handy, Catten, DeSirant) — **no OCR-invented or
  misspelled names** despite systematic scan garble. PC: 21 commissioners, all in `roster.csv`.
- **OCR fuzzy-match spot-checks (source scan → CSV):**
  - `2023-08-14` motion 2: source reads *"Council Member Catten voted no, … Uipi voted yes, and
    Mayor Silvestrini voted yes. The motion passed."* Even with garble (*"Councn Member Jackson"*
    elsewhere in the same file) the parser resolved every surname correctly → CSV = 4-1 Pass,
    Catten the lone Nay, mayor counted. **Match.**
  - `2019-05-13` (council): source *"…Catten, and Mayor Silvestrini voted yes. Council Member Uipi
    was absent."* → CSV = 4 named Ayes, Uipi correctly **not** fabricated. Match.
  - `2026-05-20` PC motion 1: source names 8 commissioners (LaMar, Anderson, Burgess, Larsen, Reid,
    Richardson, Soule, Wright) all yes → CSV = 8:0 Positive recommendation. Match. Referral
    linkage present: *"Council voted 5-0 on May 5 to recommend approval of the rezone request."*
  - CRA motions: *"Board Member … / Chair Silvestrini"* correctly map to the **same 7 people** as
    council; CRA rolls also cap at 5 (Chair = mayor counted). Verified.
- **Tally-only unanimous carry NO invented names.** The key finding: **2017-2021 council minutes
  use the collective phrasing *"All Council Members voted yes. The motion passed unanimously"***
  — the parser correctly recorded these as tally-only (blank member), NOT as five fabricated
  individual votes. Individual named roll-calls (*"Member X voted yes, Member Y voted yes …"*)
  begin ~2022. This is a **genuine source-format change, not a parser miss** — confirmed by reading
  2019/2020/2021 source text directly (grep for "voted yes" hits "All Council Members", not
  per-member lines). This also explains Marchant's low named-vote count (15): he served only in the
  tally-only era. Named-vs-tally-only motion counts by year: 2017 [0/174], 2018 [0/236], 2019 [4/208],
  2020 [5/225], 2021 [6/216], 2022 [70/135], 2023 [199/0], 2024 [207/1], 2025 [231/0], 2026 [112/0].
  The handful of pre-2022 named motions are legitimate individual rolls (e.g. 2019-05-13 with an
  absentee named).

## Mayor-votes correctness

- **Max roll-call size = 5** across all named council motions (distribution: size 3 ×24, size 4 ×272,
  size 5 ×538) — **no tally exceeds 5.** Mayor is included in the roll: Silvestrini casts 695 named
  votes, Jackson 897 (D3 council + Mayor). Both mayors (Silvestrini, then Jackson from Nov-2025)
  appear as voters. Verified in-source on a named roll (`…and Mayor Silvestrini voted yes`).
- CRA "Board Member / Chair" → same-people mapping confirmed on multiple CRA motions.

## Date coverage

- **Council starts 2016-12-05** (incorporation era) — the real founding start, **not a fabricated
  pre-2017 gap.** PC starts 2017-02-15 (matches the recon: PC stood up 2017). No 2020-floor hole.
- The **1 unrecovered** council meeting (2018-03-20 budget work meeting) is honestly logged with reason
  (published file is a budget spreadsheet, no narrative/votes) and its raw PDF retained.

---

## External election cross-check (race-by-race, outside sources)

All four flagged Millcreek findings **MATCH** independent reporting. No mismatches.

| Finding | File records | Outside source confirms | Result |
|---|---|---|---|
| **2021 D2 RCV** | THOM DESIRANT winner, `voting_method=ranked choice (RCV)`, margin_votes **−26** (first-choice deficit vs Clark 1014) | SL Trib / Millcreek Journal: Clark led first-choice; after eliminations transfers moved to DeSirant; final **DeSirant 51.7% vs Clark 48.3%** | **MATCH** — final-round winner recorded & RCV-flagged |
| **2025 mayor = appointment** | **No 2025 mayor race row** (2025 has D2 + D4 only) | Deseret/KSL/Fox13/KUTV: council **selected** Jackson to complete Silvestrini's term (retired for health); sworn in Nov 10 2025 — **not elected** | **MATCH** — no fabricated election |
| **2023 cancelled-uncontested** | D1 (Catten) & Mayor (Silvestrini) both `uncontested (election cancelled)`, **blank vote counts**, source `CANCELLED-UNCONTESTED` | Millcreek Journal: only Catten filed for D1, only Silvestrini for mayor; city **cancelled** both per state law, saved ~$85k | **MATCH** — no fabricated counts |
| **Founding 2016** | Silvestrini Mayor 100% (uncontested, opponent withdrew); Catten D1, Marchant D2, Jackson D3, Uipi D4 | KSL: Healey withdrew (cancer) → Silvestrini unopposed at 100%; council = Catten/Marchant/Jackson/Uipi | **MATCH** |
| (bonus) 2019 gap recovery | 2019 Mayor Silvestrini 74.97% def. Angel Vice; D1 Catten (unopp.); D3 Jackson def. Keller | SL Trib 2019: "Millcreek mayor holds big lead" (Silvestrini) | **MATCH** — recon-flagged 2019 absence was successfully re-parsed/backfilled |

- **Roster consistency:** every election winner (7 distinct names) appears casting votes in
  `all_votes.csv` after normalization; seat transitions (Marchant→DeSirant D2 2022; Jackson→Mayor
  + Handy→D3 Nov-2025 appointments) are reflected in both the roster and the vote record.

---

## Conformance & screeners

- **`validate_city.py millcreek_city_council`: 21 PASS / 1 WARN / 0 FAIL.**
  The single WARN = missing optional `public_comments/all_comments_clean.csv`, `README.md`,
  `VERIFICATION.md`. Each maps to a documented state: comments are **IN-PACKETS pending harvest**
  (AVAILABILITY.md), and README/root-CLAUDE are **known Phase-6 TODO placeholders** (root CLAUDE.md
  still shows `{{CITY}}` templating). VERIFICATION.md now exists (this file). No unexplained WARN.
  Key PASS lines: tally-vs-result 922/922 council & 375/375 PC (100%); db reconciles 6721==6721;
  weeks fresh; `validate_votes.py` clean for both bodies.
- **Corpus screener — both bodies clean / documented-benign.** Council (372): 0 stub, **0
  duplicate_bodies** (no source mis-upload), 0 read_errors, 0 dict_ratio/PUA/mojibake outliers;
  benign advisories only (89 `ends_mid` = minutes sit at the front of combined Agenda+Packet PDFs;
  2 replacement_chars, 8 repeated_line). PC (149): 0 stub, 0 duplicate_bodies, 0 read_errors, no
  outliers except 2 benign split-word. The OCR garble the recon warned about is present in the text
  but did **not** propagate into fabricated data (see no-fabrication section).

---

## Gaps & recommendations (all honest, none blocking)

1. **public_comments** — real verbatim comments exist inside PC packet PDFs (verdict IN-PACKETS);
   a Provo-style page-walk harvest is **not yet built**. Tracked in AVAILABILITY.md. → PARTIAL, by design.
2. **Root `README.md` + root `CLAUDE.md`** — placeholders (`{{CITY}}` templating); Phase-6 TODO.
3. **geo** — district layer is the **2022-2032** vintage; pre-2022 votes/elections used the original
   2016 lines. Fine for current use; source the earlier boundary if pre-2022 address→district accuracy
   is ever needed (already noted in geo/CLAUDE.md + recon).
4. **Named-vote era** — quantitative member-vote analysis is only meaningful **2022→present**;
   2016-2021 is tally-only by source. This is a source property, documented here — not a defect, but
   analysts must not read 2017-2021 blank-member motions as missing extraction.

**Overall: the Millcreek repo passes independent verification.** Every reconciliation ties out, no
fabrication was found (OCR garble contained, tally-only unanimous left unnamed, absentees not
invented), the mayor-as-voter structure is correct (max tally 5), and all four unusual election
findings are corroborated by outside sources.

---

## Addendum — 2026-07-06 (Phase-6.3 independent FINAL-GATE audit)

Full report: `_audits/2026-07-06/report.md`. The Phase-6.3 audit re-ran the screeners/validators
and went deeper (13 ground-truth motions, corpus-wide collision/undercapture screens, external
election re-confirmation). It confirms this verification and adds two corrections:

1. **Doc-drift correction (this file).** The *Conformance & screeners* section above (written
   before `README.md`/`CLAUDE.md` were filled) states README/root-CLAUDE are unfilled `{{CITY}}`
   placeholders and that the `validate_city.py` WARN covers README/VERIFICATION. **Both are now
   stale:** `README.md` and `CLAUDE.md` are fully filled (0 `{{...}}` remain), and the current
   single WARN is only the optional IN-PACKETS `public_comments/all_comments_clean.csv`. Conformance
   re-run 2026-07-06: **21 PASS / 1 WARN / 0 FAIL**.

2. **New data-level finding F-1 (documented, not fixed).** The "2017–2021 tally-only **by source**"
   claim (and the "2017 [0/174]" figure) is **inaccurate for 2017**: 70 unanimous 2017 council
   motions name individual voters in a tabular en-dash format (`Councilmember Uipi – Aye` … under
   "…passed unanimously by roll call vote with members voting as follows:"), but `extract_votes.py`
   only handles collective and prose formats, so all 70 (~380 all-Aye member lines) are extracted as
   tally-only → 2017 has 0 named rows. This is a **bounded, recoverable, safe-direction undercapture
   (no fabrication; motion outcomes/tallies correct)**, confined to 2017 (2018–2021 tally-only status
   is genuine). Remediation (extend the extractor, re-extract 2017, rebuild derived layers, correct
   the "by source"/[0/174] wording) is queued for a separate approved pass — see the audit report.

Everything else in this verification stands: all reconciliations tie out (db 6721/3016; weeks 5580;
motions_std outcome 100%; referrals 34 with the 3 `case_no` bridges traced to real PC↔Council pairs;
precinct sums 17/17), and no fabrication was found across the deeper ground-truth sample.
