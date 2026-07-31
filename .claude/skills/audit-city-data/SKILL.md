---
name: audit-city-data
description: Audit extraction quality and internal consistency of the civic-data city repositories — anomaly-screen text corpora against their own statistical baseline, ground-truth random samples against source documents, reconcile every doubly-stored fact, verify vote extraction and derived layers (db/, weeks/), and write a graded report with a ranked fix list. Use after building or refreshing a city, when adding a NEW city, or for periodic repo-wide QC.
---

# Audit city-data extraction quality

Audits one or more `<city>_city_council/` repos under `/Users/tysonwelsh/civic-data`.
Default scope: all cities. The user may name specific cities or datasets. The repo also
federates 8 counties, 2 MPOs, and `ut_state` — auditing those is a distinct section near the
end (their ceilings and invariants differ); the four pillars below still apply.

**Entity list = `registry/entities.csv`** (loaded by `scripts/entities.py`);
`scripts/cities.py` is a back-compat `level=='city'` SHIM (never hand-edit it) and does NOT
enumerate the non-city entities. The generated tier tree is `registry/HIERARCHY.md`. The
repo-root federated database is **gov.db (formerly cities.db)** — the Phase-6 rename is in
progress; both names refer to the same file, so this doc writes "gov.db (formerly cities.db)"
to stay correct across the cutover.

## Design principle: audit for unknown unknowns

This skill must catch failure modes nobody has seen yet — new cities bring new portals,
new PDF generators, new clerk conventions, and new ways to break. So the audit rests on
four failure-mode-agnostic pillars; a catalog of previously-found defects (appendix) is
checked *in addition*, never *instead*:

1. **Baseline anomaly detection** — judge each file/year/dataset against the corpus's own
   statistics (dictionary-word ratio, split-word rate, unusual-character ratio, size and
   count distributions), not against a fixed list of bad patterns. Corruption you can't
   name still shows up as an outlier.
2. **Random ground-truthing** — compare samples against the source document *regardless of
   whether anything was flagged*. The diff against reality is the only test that needs no
   hypothesis about what went wrong.
3. **Reconciliation of redundant representations** — any fact stored twice must agree:
   docs vs disk, index vs files, filename vs body dates, flat CSV vs db vs weeks/, tally
   strings vs counted member rows, roster vs names in votes. Disagreement anywhere is a
   finding, whatever its cause.
4. **Completeness against external reality** — compare what the repo has to what the world
   says should exist: meetings per year vs the body's cadence and the portal's own listing,
   date-gap scans, per-year record counts. Absence is the failure mode no content check sees.

Screening flags are SIGNALS, not verdicts (proven in the 2026-07-02 audit: most flags were
benign; every real defect was confirmed against a source). Never report a defect without
looking at the file — and, where possible, its source.

## Procedure

### 1. Scope and fan out

Split the cities among parallel `general-purpose` agents, 2–4 cities each (give large
corpora smaller groups). Launch all agents in one message. Each agent gets the full
checklist below and must return a structured report (grades + evidence + file paths), not
prose. For a **newly added city**, assign it its own agent and use larger samples (§2c):
assume nothing carried over from the template cities — verify its provenance claims from
scratch, and check that the city's own quirks (multi-body sessions, cadence, ward
structure, how its clerk records votes) are represented rather than forced into template
assumptions.

### 2. Per-city checklist (each agent)

**a. Provenance first.** Read the city's `README.md`, `CLAUDE.md`, and every subfolder
`CLAUDE.md`. Build a provenance table: per dataset, claimed source portal, extraction
method (born-digital pdftotext / OCR / vision / LLM / HTML scrape / structured API), and
claimed counts. Every claim gets verified against disk — doc drift is itself a finding.

**b. Statistical screen.** Run the bundled screener on each text corpus
(`meeting_minutes/minutes/`, `planning_commission/minutes/`, comment text):

```
python3 .claude/skills/audit-city-data/scripts/screen_corpus.py <dir> [--json]
```

Its general detectors: **dict_ratio** (fraction of real words), **split_word_rate**
(adjacent tokens that join into a dictionary word — catches any split-word corruption),
**weird_char_ratio** (chars outside normal typography — catches any encoding/font
corruption), stubs, duplicate bodies, truncation signals, plus the known-artifact checks —
all with corpus-relative outlier flags and a **per-year breakdown** (a single bad year
hiding inside clean corpus-wide medians was the Ogden failure). Investigate every outlier
and every year whose medians break from its neighbors. Report **rates** (`12/250 flagged`),
not just examples. If a corpus "passes," say which detectors it passed — and remember the
screener only sees text files; CSVs/JSON need the checks in §2d–e.

Then look for anomalies the script doesn't measure: sort files by size within meeting type
and eyeball both tails; grep for whatever repeated junk you notice in one file across the
whole corpus; if something looks odd, quantify it corpus-wide before judging it.

**c. Ground truth (the decisive step).** Per dataset, sample files in three strata:
(1) every screener outlier, (2) **4–6 uniformly random UNFLAGGED files** spread across
years (10+ for a new city), (3) any year with anomalous stats. For each:
- Get the source: prefer retained `raw/`; else re-fetch via `source_url` in
  `minutes_index.csv` (log dead links — that's a provenance emergency, not a skip).
- Born-digital PDFs: `pdftotext -layout`, token-level diff vs the repo markdown (strip the
  injected provenance header). Report word similarity; investigate any missing block
  > ~12 words.
- Image-only/scanned PDFs: Read the pages visually and compare. **Preserved source typos
  are positive evidence of faithful transcription**; implausibly clean text from a bad
  scan is a hallucination signal.
- Vision/LLM-extracted datasets: verify whole pages — every record on a sampled page must
  appear in the output, verbatim, in order; check apparent duplicates against the source
  (form-letter campaigns and twice-printed letters are real).

**d. Structured-data invariants.** These need no knowledge of how the data was made:
- Tally in `result` must equal the counted member rows; votes per motion ≤ roster size;
  no member voting twice on one motion (Aye+Nay pairs = clerk error or extractor bug —
  either way it must be documented); every voter name resolvable to the roster; dates
  parse, fall in range, match their filenames; no future dates.
- **Capture-rate stratification**: for named roll calls, captured-voter count vs roster
  size, by year. A year where >20% capture ≤5 of 7 voters means systematic name loss.
- Spot-check ~5 contested motions (non-unanimous) against the minutes text: names,
  Aye/Nay/Absent assignment, tally, result.
- Duplicate detection across the dataset: same body hash under two dates, same comment
  text under near-identical rows, records ending on function words ("…the") = truncation.

**d2. Motion-classification ground truth (outcome / disposition / recommendation)** —
the T1.3 method (2026-07-12; full worked example:
`_audits/2026-07-12-motion-classification/report.md`). The classification layer separates
`disposition` (what the motion PROPOSES) from `outcome` (did it CARRY) — audit both, per
city, against source minutes:

- **Learn the city's result-string CONVENTION before judging a single row.** Cities print
  tallies majority-first ("The motion was denied 7:0" = 7 opposed — provo), winner-first,
  or nays-first on failures ("failed 3-to-2" = 2A/3N — cottonwood_heights, bluffdale,
  herriman); an item-fate label ("Denied") can mean the DENY MOTION CARRIED; prose tallies
  ("Passed 4-to-1") may be deliberately unparsed. Judge rows against the city's own
  grammar, not the collection default.
- **Exhaustively sweep the SMALL outcome classes** — every Fail/Died/Continued row, never
  a sample (they are few and error-dense: in 2026-07-12 half of several cities' Fail
  classes were wrong). Random-sample the Pass majority.
- **Stratify disposition samples** by confidence: every `mixed`/`override`, a slice of
  non-high, and the NULL bucket (NULLs must be *honestly* unclassifiable — a NULL whose
  motion text was truncated mid-phrase is an extraction artifact, not honesty).
- **Dissent-coverage check**: every motion whose result carries a split tally (3-2, 4-1…)
  but has 0 named vote rows — read the source; most narrative-tally cities DO name
  dissenters ("with Council Members X and Y voting in opposition") and a systematic miss
  falsifies v_contested (magna had 33/41 such motions uncaptured).
- **Plausibility invariants** (need no source): a CARRIED motion with zero ayes is
  impossible (scrivener double-nay roll); an absent-majority roll is impossible (no
  quorum — page-break indent shift); tally aye+nay > that motion's own vote rows =
  double-counted roll lines (the db build's LINT prints these); sub-quorum "1-0/2-0"
  unanimity on a 5–7-member body = a truncated vote block.
- **Verify the build's own cross-checks are clean**: the tally↔outcome hard guard must
  show 0 unexplained contradictions and the word-over-tally review lines must equal the
  documented audited population; the disposition∘outcome-vs-legacy-`recommendation`
  cross-check mismatches are review items, not auto-errors.
- **Disposition recall probes**: "continue <File|application|Ordinance> [#X] [to <date>]"
  frames must classify `continue` (recall was ~0 in 14 cities pre-v3); "Table of Uses" /
  "defer to the Table of Commercial Uses" are NOT table motions; a bare PROC token
  ("minutes") colliding with a bled running header misfiles substantive motions.
- Report each city's conventions found (they belong in its CLAUDE.md quirk line) and each
  wrong row with the true value + the source line.

**e. Derived-layer reconciliation.** Count everything twice:
- `db/*.db` vs flat CSVs: rows per table; orphan FKs; **rows that failed to import**
  (UNIQUE-constraint drops silently deleted Park City's tie-breaks — count CSV−db, never
  assume clean).
- `weeks/` vs canonical CSVs: summed weekly rows vs flat totals; mtime of weeks/ vs the
  CSVs (stale derived layer). (Since 2026-07-07 weeks bundles LINK minutes rather than
  copying them — a weeks/<date>/minutes/ dir is now itself a staleness signal.)
- **cities.db search layer vs sources** (2026-07-07): `comment`/`cf_*`/`ordinance`/
  `document` row counts vs the per-city CSVs they load from; `fts_minutes` file count
  vs minutes on disk. `build_info` `search:*` keys hold the build's own reconciliation.
- Doc-vs-disk: every count claimed anywhere (README/CLAUDE/VERIFICATION) vs `wc -l` and
  file counts — including ENTITY-COUNT claims in repo-root docs vs the registry
  (`registry/entities.csv` via `scripts/entities.py`; `scripts/cities.py` is the
  `level=='city'` shim) and the generated `registry/HIERARCHY.md` totals (the docs said
  "13 cities" for a day while 16 existed). List every mismatch.
- Crosswalk coverage: `scripts/validate_city.py` check l.crosswalks (every observed
  body code / vote value / motion_type has a city or '*' crosswalk row).

**e2. Expansion datasets + the CF structured layer are IN SCOPE** (2026-07-07 —
previously unaudited): §9 contract headers (validate_dataset.py), ground-truth samples
from `packets/text/` + `ordinances/text/` sidecars vs their raw PDFs, per-city
`campaign_finance/` reconciliation (`validate_finance.py` PASS; spot-check
`cycle_totals.csv` review_flags; NEVER sum filing_totals), and `pmn_backfill`
recovered files vs their PMN source pages.

**f. Completeness vs external reality.**
- Meetings per year from `minutes_index.csv`: dips vs neighboring years, gaps > the body's
  normal cadence without a documented cancellation.
- Where compilation/packet sources are retained, scan them for meeting dates absent from
  the index (that's how Ogden's 8 uncarved meetings were found).
- If the portal is reachable, compare its listing count for one sample year to the index.

**g. Grade each dataset**:
- **A** — verified faithful; defects nonexistent or cosmetic (page headers/footers).
- **B** — usable with caveats; known noise or bounded, documented losses.
- **C** — significant problems: garbled years, missing meetings, systematic record loss.
- **F** — unusable or unfaithful (hallucinated, wrong-city, or majority-garbled data).

### 3. Synthesize (coordinator)

Merge agent reports into `_audits/<YYYY-MM-DD>/report.md`: provenance-method table, grade
table (city × dataset), every confirmed defect with path + evidence, and a **ranked fix
list** (data loss > garbling > duplicates > stale derived layers > doc drift).

Then run a **completeness critic** over the audit itself before reporting: which datasets
got no ground-truth sample? Which years were never sampled? Which extraction method has no
verified example? Which claims were reconciled from only one side? List the audit's own
blind spots in the report — an audit that can't name what it didn't check will be read as
"everything was checked."

Present the user a concise summary; the report file holds the detail. If new defect
classes were found, add them to the appendix below and, if they're screenable, teach
`screen_corpus.py` to detect them.

## Non-city entities (counties · MPOs · state)

The four pillars and §2 checklist still apply — but the CEILING (what "faithful" can even
mean) and which invariants are meaningful differ by tier. Each entity's own `CLAUDE.md` +
per-module `CLAUDE.md`/`SOURCES.md`/`recon.md` is authoritative on its conventions; read it
before grading. Audit against the on-disk files, then reconcile the federated db to them.

**FILES-WIN reconciliation discipline.** When the federated **gov.db (formerly cities.db)**
disagrees with an entity's on-disk per-module CSVs / minutes markdown, the **FILES are
canonical** — the db is a derived, regenerated layer (SCHEMA cardinal rule 3). A mismatch is a
build/federation DEFECT: report it, fix at the source layer, and re-federate — never patch the
db to match. This is the same doc-vs-disk / derived-layer reconciliation as §2e, extended to
`gov_level IN ('county','regional','state')`.

**Counties.** Ground-truth minutes samples per §2c exactly as for cities. The decisive
difference is the **named-roll vs tally ceiling, which varies by county AND era**: weber
(99.6% named 2015+) and cache (named 2021+, scanned tally-only 2015–20) print FULL roll calls;
utah is INVERTED (named 2015–16, tally-only OCR 2017+); SLCo and summit are tally-only. Apply
the §2d capture-rate / tally↔member-row invariants ONLY where named rolls exist — a tally-only
stretch is an honest ceiling, not systematic name loss. **County motions carry NULL
disposition by design** (classifier not yet extended); a NULL there is correct, not an
omission. Module-specific checks: the ordinance register's vote-linkage (weber's reconstructed
807-instrument register — spot-check the ~73% that claim a `motion_id` link; never quote an
ambiguous link); `development_application` pipeline rows vs their source minutes/packets; and
confirm quarantined artifacts stay OUT of parsed data (utah's posted "2023 SOVC" is the 2022
SOVC UNSUPPRESSED — a county publication error, must never reach the audited races file).

**MPOs (wfrc_mpo, mag_mpo).** These are tally-only adoption records: mover/seconder named,
dissent count-only, the **vote table EMPTY by source**. **Per-member analytics are INVALID
here** — do NOT audit for roll-call faithfulness or member vote records; instead verify the
adoption record itself (mover/seconder, date, item, outcome) and that the **caveat rows are
present and federated** (they are the mechanism that stops mis-comparison). The distinctive
failure mode to hunt is **regional_project vintage BLENDING**: each TIP/RTP vintage MUST stay
separate (vintage column populated; no cross-vintage dedup collapsing two vintages into one).
Geometry-variant dedup WITHIN a single vintage is legitimate; blending ACROSS vintages is a
defect. **Projections vintage separation**: the MPO forecasts are the RTP-2023 vintage, annual
2019–2050, control-totaled to Gardner V2022 — verify the control total holds and vintages
aren't co-mingled. RTP2027 drafts must be catalogued-only, never blended into adopted numbers.

**ut_state.** The legislation layer is the one place with FULL NAMED legislator votes, so
**roll-call vs printed-tally reconciliation applies** — but the build gate already enforces
**0 mismatches**, so the audit's job is to VERIFY that gate is clean (no unexplained
tally↔roll contradiction) rather than re-derive it. Two entity-specific traps: (1) confirm the
**HTML-comment shell trap** left no fabricated placeholder votes in the data (it would have
injected ~2,200 fake votes); (2) legislators are a **DISJOINT person population** — verify no
surname auto-merge folded a legislator into a municipal person (or vice-versa). Statute FTS
text must carry the CURRENT LUDMA numbering (2025 recodification: 10-9a→10-20, 17-27a→17-79) —
flag any repo doc still citing the repealed chapters as a doc-drift finding.

**Elections suppression preservation (all tiers).** Suppressed precinct rows must be
PRESERVED (kept, marked) and still reconcile to the certified canvass total — never dropped
and never back-filled with estimates. A cycle that is honestly dead on all official channels
(juab 2019/2021 municipal) must remain an honest gap, not an inferred row. Auditing an
elections module = verify the reconciliation-to-certified-total AND that no suppression was
"repaired."

## Appendix: known failure library (2026-07-02 + the 2026-07-12 T1.3/T3.1 additions — check first, but this is not the test plan)

| Pathology | Signature | Where found | Fix |
|---|---|---|---|
| Broken font cmap (PUA) | body majority U+F0xx; extractor yields 0 votes | Sandy 2021–23 (63/274) | subtract 0xF000; re-extract (raw PDFs retained) |
| Bad embedded OCR layer used as-is | split_word_rate ~25/1k vs 0 baseline; `HY ER` | Ogden 2022 | re-OCR from retained compilation PDF |
| Uncarved meetings in compilation PDFs | per-year meeting-count dip; PDF footer dates absent from index | Ogden 2022 (≥8 dates) | re-carve |
| Roll-call undercapture from OCR name splits | year with >20% roll calls ≤5/7 voters | Ogden 2022 (47%) | re-extract after re-OCR |
| Header-only stub as minutes | body <200B after header | Vineyard ×2 | re-acquire or list in minutes_unrecovered.csv |
| Wrong/duplicate doc under a date | identical body hashes, different dates | Vineyard (3 cases) | drop dupe, fetch real doc, rebuild votes |
| Mid-letter comment truncation | rows ending on function words | Provo (~10–15% of 81) | smarter page-continuation join |
| Ligature loss via defective font | U+FFFD where "ti" should be (`mee�ng`) | Nephi PC 2024-01-10 | vision re-extract |
| Split-boundary line loss | multi-body minutes split mid-sentence | Logan RDA 2026-05-12 | fix splitter |
| Silent UNIQUE-drop in db build | CSV rows − db rows > 0 | Park City (11 rows, both tie-breaks) | fail loudly; encode dual-vote policy |
| Stale `weeks/` | weeks mtime < canonical CSV mtime | Park City (0 vs 459 comments) | rerun build_weeks.py |
| Result-window bleed into the NEXT agenda item | tally/outcome word from the next item's title or recap ("Phase **1-3** Ordinances" read as a 1-3 tally; "the motion on the item failed" recap flipping a 4:0 pass) | kearns m596/598, orem m1057/60, magna m632 | bound the scan at the next heading / section divider |
| Misattribution CASCADE (unresolved motion binds the next result) | paired wrong rows — motion k wears motion k+1's result/roll; restated or called-question sequences merged into one row | magna (11 rows), sandy 2020-06, st_george truth-in-taxation | anchor sub-motions; park+reclaim main motions at "vote on the main motion"; emit honest no-result rows (NULL outcome) |
| Mid-roll page-break truncation | sub-quorum tallies (1-0/2-0 on a 7-member body); every grid X shifted into Absent; roll rows lost at a running header | SSL PC (~19), riverton ×2, draper grids, wj m412 (2500-char cap), midvale "Gouncil" roles | strip/tolerate footers + OCR role garble; never hard-cap mid-roll |
| Died/withdrawn motions skipped or condensed to bare "Fail" | Fail rows with 0 votes whose source says "lack of a second"; motions missing entirely; "no second" matching unrelated prose | white_city (13), st_george (13), taylorsville, magna | first-class `Died (no second)`/`Withdrawn` rows; full-phrase death regex; NULL outcome for genuine no-votes |
| Duplicate document pairs (draft embeds, portal/PMN, wrong-date PMN slots) | same motions twice on one date; DRAFT watermark letters; PMN label ≠ posting date ("May minutes.pdf" under July) | copperton, cottonwood_heights, holladay 2024-04-02, SSL 2026-05-07 embed | drop the dup from the index + unrecovered log; **delete its stale votes/ JSON** (glob-built CSVs resurrect it) |
| Same-surname DIFFERENT-PERSON collision | one person absorbing another's votes across eras/bodies; "duplicate" rows that are two real people | alta Bourke (Margaret 2020-21 vs Roger 2022+), holladay Chris+Howard Layton | per-file (PRESENT-block) name resolution; disambiguate, NEVER dedup |
| Zero-member motions dropped from the flat CSV | per-meeting JSON motions > CSV motions; no placeholder rows → the db never sees them | st_george ("tally-only -> none") | standard single placeholder row (blank member) |
| No-vote rows defaulting to Pass | deferred/restated/withdrawn motions with outcome Pass | alta RECORDED, magna "No result recorded", st_george, taylorsville | exact-string NULL set in `db_build_lib.outcome_of` (+ forks) |
| **Text-empty markdown counted as a built document** | front-matter-only `.md` (<500 B) or a `[SCANNED — … DEFERRED]` placeholder body, while `document.has_text=1` and the file sits in `fts_minutes` | cache (160/307), weber (21/533) — 2026-07-25 | OCR the retained raw; derive `has_text` from body length; exclude empty docs from FTS **and** from the searchable-coverage headline |
| **Recoverable data documented as an honest source ceiling** ⚠ the worst class | the docs assert tally-only/no-names, but the RETAINED SOURCE prints a roll — grep the raw (`AYES:`, `VOTE: n-n`, "voting in opposition") and compare to `names_recorded` | summit PC (127/130 HTMLs w/ roll blocks → 0/393 md), utah_county 2019–24, cache 2015–20 — 2026-07-25 | never take a ceiling claim on trust: verify it against the raw before grading. A stated ceiling stops anyone from looking again |
| **Era ceiling documented backwards** | doc says "scanned OCR tally-only from YYYY"; disk shows that year is born-digital with full name blocks, and the db itself holds named motions for it | utah_county 2017 (50/50 born-digital, 499 `AYE:` blocks, 174 named motions in db) — 2026-07-25 | derive the era table FROM the corpus (per-year extraction method + named rate), never hand-write it |
| **Extractor anchor broken by extractor-introduced whitespace** | per-year motion counts collapse; `pdftotext -layout` on the SAME retained raw yields more anchors than the repo md | utah_county 2015–18 (≥940 motions; pypdf `"f ollowing"`, `"mot ion"`) — 2026-07-25 | switch the born-digital path to poppler AND make result/motion regexes whitespace-tolerant |
| **Name capture running past the sentence boundary → fabricated persons** | `person` rows like `Mark Shepherd No`, `Carmen Freeman Amendment`, or a jurisdiction (`Clinton City`); each carries a role row | wfrc_mpo (12 invented people) — 2026-07-25 | sentence-boundary + jurisdiction stop-list in `clean_name()`; scan `person` for multi-token names ending in a stopword |
| **Harvester filename-pattern blind spot** | the portal's own listing API returns more dates than the index; missing files have words after the date (`11.19.2025 Approved … .pdf`) | utah_county (20 meetings; 44 API rows vs 32 indexed for 2025) — 2026-07-25 | always enumerate the portal listing per year and diff against the index — §2f is the only pillar that catches this |
| **Caveat rows absent for a whole tier** | `select city,count(*) from caveat` — an entity with a real ceiling has 0 rows; `v_member_record_all.record_caveats` empty on rows that need it | 7 of 9 non-city entities (all counties + ut_state) — 2026-07-25 | seed caveats at federation; the views already join them |
| Benign — do NOT report as defects | exhibit/plat pages garbled in the source; signature-block OCR junk; per-page headers; legal line-numbered layouts; "was led" ligature FP; real form-letter repeats; clerk tally-arithmetic misprints and prevailing-side-first conventions where roll+outcome agree | everywhere | note as cosmetic / source-faithful |

## Notes

- Screener is stdlib-only (uses `/usr/share/dict/words` if present). Ground-truthing wants
  poppler (`pdftotext`) or pypdf; fall back to visual Read of PDF pages.
- Re-fetching from `source_url` is expected (read-only GETs of public records).
- Never modify data during an audit — report only. Fixes are a separate, user-approved pass.
