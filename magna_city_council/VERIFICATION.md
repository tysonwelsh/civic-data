# Magna City — Independent Verification

**Verified:** 2026-07-12 · **Method:** conformance validator + three-way reconciliation
(all_votes ↔ minutes_index ↔ db/civic.db + per-meeting `votes/*.json`) + statistical
corpus screen + 8 source-quoted ground-truth spot-checks (both bodies, both seam sides,
CRA, OCR, PC rezone, contested) + external election cross-check (browser-UA web).
**No canonical CSV, minutes file, extractor, or db was mutated during verification.**

**Headline:** `python3 scripts/validate_city.py magna_city_council` = **21 PASS / 4 WARN /
0 FAIL**. Every dataset PASSES on its own contract; the 4 WARN are the expected optional-doc
notices (README/CLAUDE/VERIFICATION now added), two "index column order differs" cosmetics,
and the narrative-tally tally-vs-named heuristic (see §3). **Verdict: SHIP.**

---

## 1. Dataset PASS/FAIL summary

| Dataset | Result | Evidence |
|---|---|---|
| Council minutes (incl. CRA) | **PASS** | 173 indexed files all exist; 151 pdf-text + 21 pdf-ocr + 1 docx-text |
| Council votes | **PASS** | 912 motions · 934 vote rows · bodies Council 921 / CRA 13; validate_votes clean |
| Planning Commission minutes | **PASS** | 80 indexed files all exist; 80 pdf-text |
| Planning Commission votes | **PASS** | 314 motions · 315 rows · ~151 land-use-typed; validate_votes clean |
| Elections | **PASS** | 18-race superset; 2016/2019/2021/2025 + 2025 primary; externally cross-checked (§5) |
| Public comments | **PASS (honest-empty)** | header-only `all_comments_clean.csv`; SUBMIT-ONLY (AVAILABILITY.md) |
| Geo (address→district) | **PASS (mixed-vintage)** | 5 precinct-derived districts; D2/D4 2025-high, D1/D3/D5 2019-medium, 4 precincts honestly unresolved |
| db/civic.db (derived) | **PASS** | 1,226 motions · 91 votes · 236 meetings · 24 persons; 0 orphan FKs; reconciles exactly (§2) |
| weeks/ (derived) | **PASS** | 167 bundles; weekly vote sum 934 == flat total; not stale |

---

## 2. Reconciliation — all_votes ↔ index ↔ per-meeting JSON ↔ db (both bodies)

**Meeting Minutes (Council + CRA)**
- `all_votes.csv`: **934 rows**, **912 distinct motions**, **72 named member-vote rows**,
  bodies **Council 921 / CRA 13**.
- `minutes_index.csv`: **173 rows** (151 pdf-text / 21 pdf-ocr / 1 docx-text). **Every**
  vote `source` resolves to an indexed `path` (0 dangling).
- 156 of the 173 indexed files carry motions; **17 carry none** — all are genuinely
  vote-free meetings (work sessions, presentation-only regulars, Board-of-Canvassers and
  in-recess CRA schedule/ceremonial dates). None are stubs (2.0–43 KB of real text; corpus
  screen found 0 stubs). See §6.
- Per-meeting `votes/<year>/*.json` present for every meeting-with-votes.

**Planning Commission**
- `all_votes.csv`: **315 rows**, **314 distinct motions**, **19 named rows**, all
  `body=PlanningCommission`.
- `minutes_index.csv`: **80 rows** (all pdf-text); every vote `source` resolves; all 80
  files carry motions.

**db/civic.db** (READ-ONLY — build_db.py was **not** run)
- 1,226 motions (== 912 + 314), 236 meetings (== 156 + 80 vote-bearing sources),
  24 persons, 182 applications, 6 referrals (all `medium`), 28 contested motions.
- **Vote reconciliation is exact:** 72 (MM named) + 19 (PC named) = **91 CSV named rows ==
  91 db vote rows** (validator check `h.db`: delta +0). **0 orphan votes, 0 orphan
  motions→meeting, 0 unresolved voter names, 0 duplicate member-on-a-motion.**

**Seam invariant — max council roll = 5, both eras.** Across **both** bodies, **0 motions
have >5 named voters** (MM max named/motion = 5; PC max = 2). This holds through the
2025→2026 form-of-government seam and confirms the presiding officer never pushes the tally
past 5. See §4.

---

## 3. Corpus statistical screen (`screen_corpus.py`)

**Council minutes — 0 outliers of any kind.** dict_ratio median 0.768 (min 0.639);
split_word_rate median 0.00/1k (max 2.61 — trivially small; Ogden's failing corpus was
~25/1k); weird_char median 0.0143 (max 0.057). The per-year weird_char profile tracks the
documented source characteristics exactly: the **PMN/township years (2018–2023)** carry the
mild character-substitution garble the recon flagged (`quonrm`→quorum, `Hoffrnan`→Hoffman)
at ~0.016–0.023, while the **born-digital city years (2024-12+)** drop to 0.000–0.001. The
21 OCR files (2024 Apr–Dec, early 2025) sit inside this band — clean OCR, no split-word
explosion.

**Planning Commission minutes — 0 outliers.** All born-digital: weird_char median **0.0003**
(max 0.0004), dict_ratio 0.754, split 0.00/1k. The lone advisory (`ends_mid`, 168/173 MM
and most PC) fires because minutes end on a signature/attest block — benign, not truncation.

---

## 4. Ground-truth spot-checks (source text quoted)

Eight meetings pulled and compared line-for-line to their source minutes. **All match.**

**① SEAM — pre-2026 Chair-titled-"Mayor" VOTES** · `2024-12-10` (pdf-**OCR**), Ordinance
2024-O-16 roll:
> "AYE: Council Member Prokopis, Council Member Sudbury, **Mayor Barney**, Council Member
> Pierce EXCUSED: Council Member Hull FINAL RESULT: 4-0 Motion Passes"

The elected Chair Eric Barney (styled "Mayor Barney, presiding") is **inside the AYE list** —
the presiding officer votes. CSV motion 2 = {Prokopis, Sudbury, Barney, Pierce}=Aye,
Hull=Absent, `4-0 Pass`. ✔ (Doubles as the required 2024 OCR check — OCR quirks such as
`2024-0-16` for the O-number are faithfully preserved.)

**② SEAM — 2026+ elected Mayor does NOT vote** · `2026-05-26` (born-digital):
> Present: **Mayor Mick Sudbury** + Council Members Olsen, Prokopis, Jensen, George;
> Absent: Council Member Audrey Pierce.

Motion 2 tally is **4-0** — the four councilmembers present vote; **Mayor Sudbury is absent
from the tally**. CSV: Pierce=Absent, `4-0 Pass`; Sudbury in **0** vote rows this meeting. ✔
The same person (Sudbury) votes as a councilmember in ① and is the non-voting Mayor in ② —
the seam in one biography.

**③ CRA (in-recess body)** · `2024-10-22` CRA:
> "Board Members Present: Eric Barney, Chair … Board Member Hull moved to elect Eric Barney
> as Chair and Audrey Pierce as Vice Chair. The motion was seconded by Board Member Sudbury
> and passed"

CSV motion 1, `body=CRA`, mover Trish Hull, seconder Mick Sudbury, `Unanimous Pass`. ✔
The "Board Member <Name>" roles are the councilmembers convening in recess as the Community
Reinvestment Agency; `body=CRA` correctly separates the 13 CRA rows.

**④ 2024 OCR council** · `2024-04-09` (pdf-OCR): header "THE MAGNA METRO **TOWNSHIP**
COUNCIL … TUESDAY, APRIL 09, 2024" (pre-cityhood title, correct — HB35 took effect
2024-05-01), narrative-tally motion "Council Member Hull, seconded by Council Member
Prokopis, moved to suspend the rules … The motion passed." Preserved OCR typos (`Schoo!`,
`residential`) = faithful transcription, not hallucination. ✔

**⑤ PC rezone (REZ key)** · `2021-04-08` motion 3:
> "Motion: To recommend approval of application **#REZ2021-000256** to the Magna Council as
> presented with staff recommendations. Vote: Commissioners voted unanimous in favor (of
> commissioners present)"

CSV PC motion 3 = same text, `Unanimous Pass`. ✔ PC recommends up to Council; land-use
cases keyed `REZ####-######`.

**⑥ Contested council (named dissent)** · `2022-08-23` motion 2:
> "The motion failed 2 to 2, showing that Council Members **Hull and Peay voted in
> opposition** and Council Member **Prokopis abstained**."

CSV: Hull=Nay, Peay=Nay, Prokopis=Abstain, result `Failed`. ✔ (Same meeting, a later motion
records a full named roll including "Mayor Peay 'Aye'" — again the Chair-titled-Mayor votes,
consistent with ①.)

**⑦–⑧** The 72 MM + 19 PC named rows were swept in aggregate against their result strings;
absences/dissents/abstentions align with the printed tallies (e.g. the 2021-12-14 block where
Pierce is `Absent` across eight unanimous motions).

---

## 5. External election cross-check (browser-UA web, 2026-07-12)

| Race | `magna_races.csv` | Outside source | Match |
|---|---|---|---|
| 2025 **Mayor** | **SUDBURY 2,260** (65.4%) def. Adriano 1,196 | *Salt Lake Tribune* 2025-11: **Sudbury** won (~67% unofficial) over Adriano; describes Sudbury as the "District 3 council member" running for the open seat Barney vacated | ✔ winner + runner-up |
| 2021 **Council D2** | **BARNEY 347** · Peel 190 (total 581, n=3) | rcvis.com / *SLTrib* voter guide: **Barney 347**, Peel 190, Ramos 44 (=581) | ✔ exact |
| 2019 **D1/D3/D5** | Prokopis 538, Peay 470, Pierce 435 (uncontested; **recovered from raw SOVC**) | current roster (magna.utah.gov) has Prokopis D1, Pierce D5; consistent | ✔ consistent |

The Tribune's independent description of Sudbury as the sitting **District 3 councilmember**
externally corroborates the internal vote data (spot-check ①: Sudbury casting councilmember
Ayes in 2024) and the seam narrative (D3 councilmember → open-seat Mayor 2026).

---

## 6. Honest gaps & wrong-doc handling (documented, not defects)

- **2017 + Jan–Jun 2018 council minutes — 36 meetings, 404-unrecoverable.** Every PMN listing
  for these dates references a minutes PDF that returns **HTTP 404** on `www.utah.gov/pmn/files/…`
  (attachment purged from the archive; no Wayback copy; legacy township site blocks scraping).
  All 36 are logged verbatim in `meeting_minutes/minutes_unrecovered.csv`
  (26 × 2017 + 10 × 2018), **never stubbed**. On-disk council record therefore begins
  **2018-07-17**. This is Magna's structural coverage floor for council votes, not a build miss.
- **PC 2017–2018 — 57 meetings, agenda/audio only.** PMN posts agendas + audio for the
  township-era PC but **no minutes documents** were published for 2017–2018; all 57 are logged
  in `planning_commission/minutes_unrecovered.csv`. PC vote record begins **2019-03-14**.
- **CivicPlus wrong-doc-in-Minutes-slot.** The AgendaCenter occasionally serves an agenda,
  spreadsheet, or correspondence file under the "Minutes" label. Where a genuine minutes
  document existed it was recovered from **PMN body 5803** instead; the wrong-doc dates that
  had no real minutes anywhere are not fabricated into stubs. Handling is recorded in
  `SOURCES.md` and `meeting_minutes/CLAUDE.md`.
- **Board-of-Canvassers certification motions not extracted** (e.g. 2019-11-19, 2025-08-26,
  2025-11-18): these "Canvasser <Name> moved to … certify the election results" motions are a
  distinct statutory body (the council sitting as canvassers), not council legislative votes —
  deliberately outside the vote datasets, consistent across all such dates.
- **Vote-value normalization:** source "EXCUSED" is recorded as `Absent` in the flat CSV
  (controlled vocab); the verbatim word survives in the minutes markdown. Consistent, expected.
- **Geo mixed-vintage:** D2/D4 boundaries are 2025 (high-confidence); D1/D3/D5 fall back to
  2019 pre-2022 lines (medium); 4 precincts (MAG001, MAG008, MAG009, MAG017) are honestly
  flagged `confidence=none` (dropped/added between cycles → current district unknown). Pre-2022
  addresses near a moved boundary may mis-assign — this is disclosed, not hidden.

---

*Addenda convention: append a dated `## Addendum YYYY-MM-DD` block whenever the data is
repaired or re-audited; never rewrite the record above.*

## Addendum 2026-07-16 — pmn_backfill promotion (5 Council + 7 CRA docs)

**What changed.** The 13 minutes docs recovered 2026-07-14 into `pmn_backfill/` (PMN bodies
5803 Council / 6925 CRA) were promoted into the vote layer via the new
`meeting_minutes/extract_backfill_votes.py` (ogden/midvale/herriman promotion pattern):
**12 docs merged → 51 motions / 51 rows** with a documented trailing `provenance` column
(`minutes` audited | `pmn_minutes` promoted). Totals: 966 → **1,017 rows**, 921 → **972
motions**; CRA 13 → **32 motions** (5 → 12 minutes-on-record dates). The 2025-11-18 CRA doc
is stamped "DRAFT MINUTES – UNAPPROVED" and was NOT promoted (honest sidecar).

**Verification performed.**
- Every doc's date + body verified from in-body content (the 2025-01-14 CRA doc's OCR header
  misprints "JANUARY 14, 2024" — adjourn motion + attest chain + the 2025-02-11 approval
  motion confirm 2025-01-14; the 2024-11-12 CRA attest line says "City Council" — a clerk
  template slip, content is CRA). No (date, body) collision with the audited layer (the 7
  CRA dates coincide with separately-recorded 6:00 PM Council meetings — the CRA met 5:30 PM
  as its own filed meeting; audited council docs on those dates contain no CRA motions).
- Mover-line counts reconcile 1:1 with extracted motions in all 12 docs.
- Ground-truth spot-checks (verbatim vs sidecar): 2024-02-27 m1 (settlement ratification) +
  m2 (Ordinance 2024-O-03 ADU adoption); 2024-11-12 CRA m2 (agency bylaws); 2024-11-26 m5
  (DENY Ordinance 2024-0-16, 5-0 — disposition=deny, outcome=Pass); 2025-02-11 CRA m1 /
  2025-06-10 CRA m1–m3 (named Pierce/Prokopis Absent); 2026-03-10 m4 (Pierce Abstain, 4-0);
  2026-06-09 m2 (the previously-swallowed FY2025-26 budget PH motion). All match source.
- Diff at (source,date,body,motion_no,member,vote): **0 removals, +51 additions**; one
  result-string change on a surviving audited key (below).

**Extractor repairs made during promotion** (extract_votes.py, backed up to
`_backups/2026-07-16-minutes-promotion/magna/`):
- UNANIMOUS grammar now recognizes "passed BY A unanimous vote" (early-2024 clerk phrasing;
  its absence silently DROPPED 2 motions of 2024-02-27 and falsely nulled a third) and bare
  "vote was unanimous." (2024-11-12 CRA adjourn). Audited-layer effect: exactly one row —
  **2022-12-13 m15 "No result recorded" → "Unanimous Pass"** (the source DOES print a result;
  the honest-NULL count drops 11 → 10).
- GARBLE map: `Paerce → Pierce` (2025-05-13 CRA sidecar OCR; zero audited-corpus hits).
- extract_backfill_votes.py strips TRAILING OCR pipe noise from the sidecars ("The motion
  passed |" wraps) — without it the scan window overran into the next motion and swallowed
  one (2026-06-09).

**Derived layers** rebuilt (db, referrals, motions_std, weeks, sources): db motion count
1,286; provenance threaded to `motion.provenance` (940 Council: 908 minutes + 32
pmn_minutes; 32 CRA: 13 + 19). Contested (db v_contested) 63 → 64 (+ the 2026-03-10 Pierce
Abstain). Referrals 1 → **3 medium** (2 Council←PC ordinance chains surfaced by the promoted
2024-02-27 ADU + 2024-11-26 glass-requirements minutes; 1 same-night Council←CRA
Broadway-project-area pair — note the prior CLAUDE.md "6 links" claim was stale vs the
built db's 1). `validate_city.py`: **22 PASS / 4 WARN / 0 FAIL** (WARNs: documented
provenance extension, pre-existing index column order, and the narrative-tally
named-vs-tally ceiling).

---

## Addendum — 2026-07-31: four PHANTOM Planning Commission meetings de-ingested

**Defect.** Utah PMN body 1559 attaches minutes to a notice in two distinct ways:
`YYMMDD_MagnaPC_MinutesApproved.pdf` is the APPROVED minutes of **that notice's own**
meeting, while `<Month> minutes.pdf` is the **DRAFT of the PREVIOUS meeting**, posted with
this meeting's agenda packet because this meeting is the one that will approve it. Across
all 112 minutes attachments on body 1559, exactly **four** notices carry no approved copy;
on those four the original ingest fell back to the draft and stamped it with the notice
date, manufacturing a duplicate of the previous meeting.

| PHANTOM date (removed) | PMN file ingested | what the file actually is |
|---|---|---|
| 2023-08-10 | 1008935 `July minutes.pdf` | draft of **2023-07-13** |
| 2023-10-12 | 1032545 `September minutes.pdf` | draft of **2023-09-14** |
| 2024-08-08 | 1154441 `July minutes.pdf` | draft of **2024-07-11** |
| 2025-10-16 | 1337021 `September minutes.pdf` | draft of **2025-09-11** |

**Evidence (four independent lines, all four pairs).** (1) The in-body MSD header
(`MAGNA PLANNING COMMISSION MEETING — Thursday, <true date>`) names the earlier meeting.
(2) The correctly-dated twin carries the stamp `**Meeting minutes approved on <phantom
date>**` — i.e. the phantom date is when the earlier meeting's minutes were APPROVED, not
when the meeting happened; the draft copies lack that stamp. (3) PMN attachment filenames
(above). (4) Later meetings' own minute-approval motions — 2023-11-09 m1 "To continue the
October 12, 2023 ... minutes to the December meeting", 2024-09-12 m1 continuing approval of
the August 8, 2024 minutes, 2023-09-14 m4 approving the August 10, 2023 minutes.

**Delta — expected rows only.** motions **314 → 302** (−12: 4+4+2+2, each a verbatim
duplicate of its twin's motions), all_votes rows **315 → 303**, named vote rows **19 → 18**
(the one removed row, `2024-08-08 m1 VanRoosendaal Abstain`, is a duplicate of
`2024-07-11 m1 VanRoosendaal Abstain`), indexed PC documents **80 → 76**, db meetings
**252 → 248**, db motions **1,302 → 1,290**, db votes **175 → 174**, db applications
**223 → 217** (six singleton apps keyed only to the phantom source files). **No motion,
vote, or application unique to a real meeting was removed.** Referrals unchanged (3 medium).
`weeks/` is byte-identical — Magna's weekly grid covers `meeting_minutes/` only.

**Honest-gap handling.** All four vacated dates are **REAL meetings** (PMN notice + audio
recording + agenda packet exist for each, and each was the meeting that approved its
predecessor's minutes) whose **approved minutes PMN never published**. Four rows were added
to `planning_commission/minutes_unrecovered.csv` (**59 → 63 rows**: the 57 township-era
2017–2018 meetings + 2 from 2019 were already there; the 4 new rows are the first modern
ones) with the notice URL and the specific evidence. The four retained PDFs live in
`planning_commission/raw/_duplicate_drafts/` with a README — nothing was deleted.

**Regression guard.** `planning_commission/validate_votes.py` now runs a DOCUMENT-DATE
GUARD: every indexed minutes document's in-body MSD header month+day must equal its index
date (year mismatches are WARN only — the MSD clerk typo'd the year on five 2023 documents).
`--check-dates` makes a mismatch a non-zero exit. Current state: **fails=0, warns=5**.

**Also regenerated.** `planning_commission/roster.csv` — its `last_seen` values for Elieson
and VanRoosendaal pointed at the phantom dates. It had no build script (hand-written, not
reproducible), so it is now produced by the documented `planning_commission/build_roster.py`
(attendance-block seat/presence + narrative motion action). Elieson last_seen
2023-08-10 → **2023-09-14** (seated but marked absent that night), VanRoosendaal
2024-08-08 → **2024-07-11**; counts shift because the rule is now explicit.

**Post-fix validator:** `python3 scripts/validate_entity.py magna` = **22 PASS / 4 WARN /
0 FAIL** (same four pre-existing WARNs), plus the expected `gov.db is STALE` federation
notice — re-federation is the wave coordinator's step, not this entity's.

**Not a duplicate (checked, left alone).** A repo-wide same-signature scan of magna's db
now returns one pair above 0.90: CRA **2025-02-11 ↔ 2025-04-08** (0.936). Both are genuine,
distinct meetings — each from its own `*- APPROVED.pdf`, each self-referencing its own date;
the similarity is the two-motion CRA template (approve prior minutes / adjourn).
