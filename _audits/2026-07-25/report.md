# Post-build audit — the 9 non-city entities (2026-07-25)

**Scope.** The 6 counties + 2 MPOs + `ut_state` added in the 2026-07-20 Phase 4–6 wave, plus
wfrc's 2026-07-22 Phase-1 derived layer. First independent adversarial ground-truth pass on
any of them (TODO.md:864 residual 2; ranked in HANDOFF.md as the top non-owner-gated work).

**Method.** `.claude/skills/audit-city-data/SKILL.md` — four pillars + §2 checklist + the
non-city section's tier-specific ceilings. Four parallel agents grouped by ceiling type:
A weber+cache (named-roll), B utah_county (inverted ceiling), C summit+washington+juab
(tally-only + db-less), D wfrc+mag+ut_state (data-forward + state).

**Read-only.** No repo data file was created, modified, or deleted. Two stray 0-byte
`gov.db` files were created by agents running `sqlite3 gov.db` from inside an entity
directory (`summit_county/`, `juab_county/elections/`) and are listed for cleanup in §7.

**Verification convention.** ✅ = re-verified independently by the coordinator against files
and sources. ▫ = agent-reported with cited evidence, not independently re-run.

---

## 1. Headline

**The build gates were all clean and all nine entities pass `validate_entity.py` at
0 FAIL / 0 WARN — and that is exactly the problem the audit was for.** Structural
conformance validated; faithfulness to source did not. Four of the nine carry material,
provable extraction loss that no existing gate could see, and in three cases **recoverable
data is documented as an honest source ceiling** — the most damaging failure mode in this
repo, because a stated ceiling stops anyone from looking again.

Two findings were reached independently by different agents on different entities, which is
what raises them from local defects to systemic ones: the **missing `caveat` rows** and the
**`motion_std` / `v_coverage` gap** for the whole non-city tier.

Best-in-repo work also confirmed: `ut_state`'s vote gates are genuinely clean (shell trap
uncontaminated, person populations provably disjoint, LUDMA numbering current), wfrc's
Phase-1 derived layer **re-derived from source with 0 cell diffs across 22 columns**, and
juab + washington's honest gaps are exemplary — nothing inferred, no suppression "repaired."

---

## 2. Grade table

| Entity | Text fidelity | Coverage | Votes / motions | Elections | Derived / federation |
|---|---|---|---|---|---|
| **weber_county** | A | **C** — 21 image-only scans never OCR'd | A− | A | C |
| **cache_county** | A | **F** — 160/307 files text-empty | B | A | C |
| **utah_county** | B | **C** — 20 meetings absent | **C** | A (exemplary) | A / **C** analytic |
| **summit_county** | A | A | **C** — PC rolls dropped | A | C |
| **washington_county** | B+ | A | n/a (deferred, honest) | A | A docs / **F** caveat |
| **juab_county** | n/a | A | n/a (deferred, honest) | A | A / **F** caveat |
| **wfrc_mpo** | B | A | B (adoption record) | n/a | A derived / B |
| **mag_mpo** | A | A | B+ | n/a | A |
| **ut_state** | A | A | **A** (gates verified clean) | n/a | **C** — no caveat rows |

Per-dataset grades with justifications are in the agent reports; the table above is the
roll-up. For deliberately-absent layers (washington/juab vote layers, MPO vote tables) the
grade reflects **the honesty of the absence**, not the emptiness.

---

## 3. Systemic findings (all independently verified)

**S1 — 7 of the 9 entities have ZERO `caveat` rows.** ✅ Only the two MPOs carry any
(wfrc 5, mag 1). utah, weber, cache, summit, washington, juab and ut_state have none.
```
select city,count(*) from caveat group by 1;   -- 44 rows total, none for those 7
```
Root `CLAUDE.md` states the caveat table "carries the data-forward framing for the non-city
entities — an MPO's empty vote layer and a db-less county's deferred vote/pipeline layers are
honest properties." **That mechanism is not in place for any county or for the state.**
Verified consequence: `v_member_record_all` returns, for summit_county, a top row of
`Clyde | Eastern Summit County PC | 32 votes | 0 ayes | 28 nays | nay_pct 100.0` with
`record_caveats` **empty** — a cross-entity "who dissents most" query puts Summit PC
commissioners at the top of the repo with no warning. Severity: **honesty mechanism absent
exactly where the ceilings are most treacherous.**

**S2 — `motion_std` is empty for the entire non-city tier.** ✅
```
city 49,172/49,172 · county 0/24,346 · regional 0/958 · state 0/1,208
```
Root `CLAUDE.md` says `motion_std` is "joined to `motion` at 100%" — true only of cities.

**S3 — `v_coverage` returns zero rows for all 9 entities.** ✅ It depends on `motion_std`,
so the one view whose caveat branch would have surfaced the db-less entities' deferrals
returns nothing for them either.

**S4 — `coverage.json` covers only cities.** ✅ `as_of` 2026-07-22, top-level keys are
`description / as_of / generated_by / note / cities` (31 entries). No counties, no regional,
no state — although root `CLAUDE.md` presents it as the repo's "measured coverage."

**S5 — searchable-coverage figures overstate on two counts.** ✅ Docs claim `fts_minutes`
= 13,852 docs (README.md:53, CLAUDE.md:87); the db holds **13,896** (`build_info` agrees
with the db, not the docs). Separately, **195 of those rows carry no usable text** — 160
cache `[SCANNED …]` placeholders, 21 weber empty scans, 14 others — and `document.has_text`
is `1` for all of them (cache 307/307, weber 533/533).

**S6 — `validate_entity.py` has a vacuous check.** ✅ It validates `md_path`, but weber's
and mag's minutes indexes use the column `minutes_md`. Both report
`minutes_index: 0 md_paths, 0 unresolved` — 533 weber and 151 mag paths are never checked.
More broadly, the validator checks structure only: it caught **none** of the defects below,
while reporting 0 FAIL / 0 WARN for all nine entities.

---

## 4. Ranked fix list

### Tier 1 — data loss (recoverable data absent or mislabeled as a ceiling)

**F1. cache_county — 160 of 307 legislative minutes are text-empty placeholders.** ✅
145 are the entire 2015–2020 era; **15 sit inside the named-roll era** (2021×4, 2023×5,
2024×3, 2025×3) and are undocumented anywhere. Mechanism: `cache_county/legislative/
extract_votes.py:293` — `if fmt == "scanned": continue`, while the `extract_ocr()` tally
grammar at line 242 is implemented and never reached. ▫ Agent A re-fetched
`Cache County Minutes 05.13.2025 (Approved).pdf` (HTTP 200, born-digital print-to-PDF) and
read a **contested** named roll it contains: `Aye: 5 … Nay: 1 David Erickson`. Estimated
loss ≈1,400 tally motions (2015–20) + ≈200 motions / ≈1,300 named votes (2021–25), including
contested motions absent from `v_contested_all`. **CLAUDE.md's claim that these are "OCR
(tesseract)" is false — no OCR ran.**

**F2. summit_county — the Planning Commissions' named roll calls are dropped and the loss is
documented as an unliftable ceiling.** ✅ 127 of 130 retained Granicus PC HTMLs contain full
`AYES:/NOES:/ABSENTS:/ABSTAINS:/RECUSALS:` blocks; **0 of 393 repo minutes markdown files
contain them.** Verified source block (2025-05-13 Snyderville Basin):
`AYES: Makena Hawley, Matthew Nagie, Spencer Young, Tim Jeffrey, Heather Peteroy, Eric Sagerman`.
▫ ≈2,447 named vote positions / ≈408 motions. The ceiling is asserted in three places
(`summit_county/CLAUDE.md:43-46`, `land_use/CLAUDE.md:44-47`, `land_use/build_votes.py:3`).
The AgendaCenter era loses prose rolls too (`2023-01-05_eastern_summit_pc.md:180`:
"passed, 4-1 (Commissioners Benson, Clyde, Wheaton, and Peterson voted in favor; Sargent
opposed…)" → only `Sargent | Nay` captured).

**F3. utah_county — three compounding losses.** ✅ all three verified:
- **≥940 motions lost 2015–18**: pypdf inserts mid-word spaces that break the extractor's
  literal anchor. `2016-08-30` — `pdftotext -layout` on the retained raw yields **17**
  intact anchors and the markdown holds **26** `AYE:` blocks, but the repo markdown has
  **5** anchors and the db has **5 motions**. Corrupted text in the file: `"f ollowing"`,
  `"seconde d"`, `"mot ion"`. The exact-anchor count equals the db motion count in every
  year 2015–17 — the anchor is the bottleneck, and poppler extracts the same PDFs cleanly.
- **The entire 2019–2024 named era stored as tally-only**: `named` = 0 for every year
  2019–2024 in the db, while `2019-01-29_board_of_commissioners.md` reproduces
  `VOTE: 3-0 / AYE: COMMISSIONER LEE / COMMISSIONER AINGE / COMMISSIONER IVIE` correctly —
  and the db has **0 motions for that meeting**. Cause: `NAME_LINE_RE` matches Title-Case
  only; 2019+ prints ALL-CAPS. ▫ ≈521 named roll calls, ≈1,300 member-vote rows, and
  **contested detection is blind after 2018** (3 Fail motions in 10,089).
- **20 meetings absent that the county's own API lists**: ✅ the 2025 archive endpoint
  returns **44 rows** against **32** dates in the repo index. Missing filenames carry words
  after the date (`11.19.2025 Approved Commission Meeting Minutes.pdf`) — a fetcher
  filename-pattern blind spot; ▫ 4 spot-checked return HTTP 200 today.

**F4. weber_county — 21 minutes documents are front-matter only (~307 bytes).** ✅ Konica
copier scans with no text layer and no OCR fallback; 19 are 2021, 2 are 2023. ▫ Agent A read
`raw/min_09212021.pdf` visually: a complete document with 7 named roll calls, including
`APPROVE OF RESOLUTION 36-2021` — and `ordinances/adopted_instruments.csv` is missing 37 of
the 2021 resolution numbers, Resolution 36-2021 among them. 2021 motions/meeting collapses
to 5.4 against an 8.5 baseline. CLAUDE.md's "minutes_unrecovered.csv = none within floor"
is false for these.

### Tier 2 — fabrication and wrong derived facts

**F5. wfrc_mpo — 12 non-existent people in the federated `person` table.** ✅ `Clinton City`
(a jurisdiction), `Bob Stevenson No`, `Bob Stevenson This`, `Carmen Freeman Amendment`,
`Jeff Scott No`, `Jim Harvey This`, `Mark Shepherd No`, `Joy Petro With`, and 4 more — each
with a `role` row. Verified source: `2022-10-27_council.md:131` reads
*"seconded by Mayor Mark Shepherd. No discussion, approved unanimously."* Cause:
`extract_motions.py` `clean_name()` takes up to 3 capitalized tokens past the sentence
boundary. Also splits one person across `Bob Stevenson`/`Bob Stevension`,
`JoAnn`/`JoAnne Seghini`, `Tami`/`Tamara Tran`.

**F6. cache_county — 2 documents double-ingested: 24 motions / 168 votes / 4 contested
counted twice.** ✅ `2022-10-25_council.md` and `2022-10-25_council_3.md` are both 18,535
chars; `2024-11-26` has an amended + approved posting of the same meeting. Headline
"182 contested" is really 178 distinct. **Coordinator correction to the agent report:** of
the 7 duplicate meeting dates in the db, only these 2 are true duplicates. ✅ I checked the
other 5 — `2025-12-02`, `2026-05-26`, `2026-06-23` are `_council` + `_workshop` pairs with
distinct source PDFs and distinct content (verified by reading both headers), and
`2024-12-10` / `2025-11-18` are documented regular+special pairs. The agent's "legitimate"
list named two dates the query does not return; use this classification, not that one.

**F7. summit_county — 29 spurious motion rows and 31 duplicated ones.** ▫ 26 motions whose
text is the fragment `'which was'`, plus `'there in 2015'`, `'this area two years ago'` —
the last lifted from a *public commenter's* sentence ("The Payans **moved** there in 2015").
All carried into the db with `outcome='Pass'`. Separately 26 meetings carry repeated
`(motion, result, tally)` signatures from a PDF that embeds a second copy of its own body.

**F8. cache_county — an ordinance link marked `high` confidence points at the wrong
ordinance.** ▫ ORD 2021-22's link lands on a clerk typo (the source tables 2021-22 and
approves 2021-23 in the same session); the register's own `adoption_date` (2021-12-14)
contradicts the linked motion date (2021-10-12) and nothing flagged it.

**F9. summit_county — 2 of 4 linked ordinance adoption dates contradicted by the primary
document.** ▫ Ordinance 1003's index row says `2025-12-04`; the ordinance text itself says
*"Enacted this 17th day of December, 2025"*, matching its enacting motion.

### Tier 3 — garbling (bounded, source retained)

**F10.** ✅ wfrc — 13 of 53 minutes files carry unstripped U+202C/D at 14–19% of characters
with ~217 displaced first letters ("Thursday" → `hursday` + `T`); the extractor documents a
strip that does not happen. Content is complete; words are unsearchable.
**F11.** ✅ wfrc — 13 `result_raw` values truncated one character (all begin `"ith "`), from
an unanchored `it` alternative matching inside "W**it**h". Verbatim-fidelity (cardinal rule
2) violation; `outcome` unaffected.
**F12.** ▫ cache land_use — 7 motions on 2024-11-07 drop Chris Sands because a trailing
legal line-number token fuses onto the last name.
**F13.** ▫ weber — 9 vote rows silently dropped CSV→db by `UNIQUE(motion_id,person_id)`
(the Park City class); all 9 trace to source clerk typos naming one commissioner twice.
**F14.** ▫ washington — 1 file with shredded ALL-CAPS headings (2023-02-21, a resolution
number destroyed); ▫ 3 files with 76 chars of ligature loss; ▫ summit — 10 of 118 packet
sidecars with font-cmap-offset garbling.
**F15.** ▫ mag — printed divided tallies ("roll call vote of 4 Ayes and 11 Nay") dropped
from `result_raw`; and 2 motions **do** name a dissenter, which the absolute "no individual
vote attribution" ceiling wording doesn't allow for.

### Tier 4 — doc drift

✅ S4/S5 above; ✅ utah_county's era ceiling is wrong in three places — `utah_county/
CLAUDE.md:37`, `recon.md`, and root `CLAUDE.md:328` all say 2017+ is scanned-OCR tally-only,
but **2017 is 100% born-digital (50/50 files), 49 of 50 carry `AYE:` name blocks (499 total),
and the db itself records 174 named motions in 2017**. ▫ Root `CLAUDE.md` says the ut_state
advisory opinions and statutes are "not federated into gov.db's fts tables" — 525 rows are.
▫ Root says 42 registered entities; the registry has 44 rows. ▫ Plus: weber `recon.md`
motion_refs 1,679 vs 1,102 on disk; cache 312 vs 307 minutes + 1 unlogged URL; summit
recon 195 vs 198 and an elections doc still saying the entity isn't registered; wfrc
"all 53 docs" in FTS vs 81; ut_state "847 recorded roll calls" vs 759; `project_history.
exited_tip`'s schema comment disagrees with the builder for 24 non-contiguous pins.

### Tier 5 — provenance

**F16.** ▫ cache_county retains **no `raw/`** for its legislative corpus, and its 26
Wayback-recovered documents store the **dead live URL** with no snapshot URL recorded —
those documents currently have no reproducible provenance pointer. Every ground-truth check
requires a live re-fetch, and one sampled URL 404s today.

---

## 5. What passed, and deserves to be said plainly

- **ut_state gates verified clean, not merely re-asserted.** ▫ Shell trap uncontaminated
  (0 rollcall_ids shared across bills, 0 session/date-year mismatches); a re-fetch of
  `svotes.jsp?sessionid=2025GS&voteid=175&house=H` matched all 75 names exactly. Person
  populations **provably disjoint** in both directions (0 cross-level votes, 0 name_key
  collisions). LUDMA numbering current — 0 files cite the repealed 10-9a-/17-27a- chapters.
- **wfrc Phase-1 derived layer independently re-derived** from `raw/TIP*.json` without
  copying the builder: 3,453 + 1,884 rows, **0 cell diffs across 22 columns**; all 5 gate
  counts reproduce; both `vintage_overrides.csv` adjudications evidence-justified.
- **Vintage separation provably holds.** No blank `plan_vintage` anywhere; every duplicate
  `project_id` confined within a single vintage; RTP2027 catalogued-only (0 rows in
  projections/projects). MAG's Gardner V2022 control total reproduced to ±2 persons; WFRC's
  region row equals the exact sum of its 98 city-areas across all 96 metric-years.
- **Elections are the strongest layer in the tier.** utah_county's quarantine held — the
  mislabeled "2023 SOVC" (really the 2022 SOVC unsuppressed) is cited by **0 of 198,459**
  rows, and 29,084 suppressed rows sit preserved next to it. juab: 123/123 by-contest rows
  equal their certified total, 311 suppressed rows preserved, 2019/2021 remain an honest
  gap. washington: 95/95 candidate columns re-derived from the certified canvass export.
- **Honest gaps are honest.** summit's 460-row unrecovered ledger reproduces its recon
  per-year counts exactly with 0 overlap; washington's deferrals are stated identically in
  four places; juab's zero `fts_minutes` is consistent with building no minutes modules.

---

## 6. The audit's own blind spots

Per SKILL.md §3's completeness critic — what this pass did **not** establish:

- **Elections were largely reconciled from one side.** Only washington (1 of 15 election
  files) and juab had a total independently re-derived from a raw certified canvass.
  utah_county's 198,459 rows were reconciled against its own VERIFICATION.md; weber's and
  cache's cross-checks were read from their module reports, not re-run. The `pdf_ocr`,
  `pdf_ocr+visual` and vision-transcription extraction paths have **no independently
  verified example anywhere in this audit**.
- **Sampling was ~1–2% of the large corpora.** weber 11 of 533 legislative diffs; cache 4 of
  307; utah_county 12 random + 8 targeted of 495. A 1.0000 diff ratio proves the
  pdftotext→markdown step; it says nothing about documents the harvester never enqueued —
  and F3/F4 show that is where the losses live.
- **Years never sampled at source:** utah_county 2020–2023, 2025, 2026 (grep-level only);
  weber 2016, 2021 non-empty files; cache 2025 born-digital; summit land_use 2017, 2019,
  2022, 2024, 2026; wfrc 2017, 2020, 2021; mag 2018, 2020.
- **Whole modules unsampled:** every entity's `plans/text/` (44 MPO docs got the screen but
  one ground-truth open); weber `case_keys.csv`, `code_sources.csv`; cache's 169 ordinance
  texts (0 opened); wfrc `taz_county_rollup.csv`; all GIS catalogs checked for reachability
  or structure only, never attribute content.
- **ut_state: 3 of 830 roll calls externally re-fetched.** Sessions 2016, 2019–2023 and 2026
  have no externally verified vote. The bill classifier's **recall** was never tested — no
  sample of blank-`relevance` rows was checked for wrongly-excluded land-use bills.
  Statutes: only Title 10 Ch 20 compared against live XML; 17-79 and 13-43 verified by
  filename/index count only.
- **Completeness vs portal is one-sided for most entities.** Proven for weber (484 + 49 =
  533 exact) and utah_county (which is how F3's 20 missing meetings surfaced). Not
  enumerated for cache 2015–2023/2026, either MPO, or either summit PC portal — so
  "meetings the harvester never saw" is unbounded for those.
- **Loss magnitudes are estimates.** F1's ~1,400, F2's ~2,447, F3's ~940 and ~521, F4's
  ~198 are anchor-arithmetic and rate-extrapolation lower bounds calibrated on samples. The
  true recoverable counts require the re-extraction itself.
- **Same-surname collisions not ruled out.** wfrc's `Tami`/`Tamara Tran` split was judged by
  name shape, not by reading each occurrence's context — the alta Bourke pathology (two real
  people, one surname) cannot be excluded without that read.
- **No builder was re-run** (forbidden in an audit), so idempotency claims in the
  BUILD_REPORTs are verified by re-deriving outputs, not by observing a build.

---

## 7. Screener taught two new detectors

Per SKILL.md §3 ("if they're screenable, teach `screen_corpus.py` to detect them"), the
empty-body class from F1/F4 is now screenable:

- **`PLACEHOLDER`** — a body that only announces missing/deferred content
  (`[SCANNED — … OCR + vote extraction DEFERRED]`, "image-only PDF", "minutes not posted").
  This class was **invisible to every existing detector**: cache's 160 placeholder bodies
  scored `stub(<200B) 0/307` because the placeholder sentence exceeds the stub threshold.
- **`no_content`** — fewer than 40 real word tokens regardless of byte size. weber's 21
  empties *were* reachable via the existing `short(<500B)` flag, but nothing named them as
  a content failure, so they read as a size curiosity rather than 21 missing documents.

Validated on the defects and regression-tested for false positives:

| corpus | files | PLACEHOLDER | no_content |
|---|---|---|---|
| cache_county legislative | 307 | **160** | 0 |
| weber_county legislative | 533 | 0 | **21** |
| slc meeting_minutes | 477 | 0 | 0 |
| ogden meeting_minutes | 505 | 0 | 0 |
| park_city meeting_minutes | 242 | 0 | 0 |
| summit_county land_use | 393 | 0 | 0 |
| utah_county legislative | 495 | 0 | 0 |
| washington_county legislative | 230 | 0 | 0 |

**0 false positives across 2,342 healthy files**; the detectors fire only where the defect
is. Six new pathologies were also added to the skill's failure-library appendix, headed by
*"recoverable data documented as an honest source ceiling"* — the class that produced the
three largest findings here.

## 8. Remediation summary (appended 2026-07-25, same day)

Two fixes executed under `/remediate-city-data`; full record in
`_audits/2026-07-25/remediation.md` + `summit_county/land_use/VERIFICATION.md`.

**Tier-4 doc drift — utah_county era ceiling: FIXED.** All three locations corrected from a
per-year derivation of the actual corpus (extraction method × `AYE:` blocks × db named
motions). Root `CLAUDE.md` no longer tells every session that 2017+ is tally-only OCR.

**F2 summit_county PC votes: LARGELY FIXED, and this report's premise was wrong.** F2 said
127 of 130 retained HTMLs carry roll blocks that the repo failed to parse. **All 545 of
those blocks are inside HTML comments Granicus never renders** — the converter stripped them
correctly. This report should have said so; it did not, because the agent read the stripped
text without checking the markup context. Corrected findings:

- The hidden data is **real** — 520/520 blocks agree exactly with the published tally.
- But it adds **zero** dissent: all 25 divided motions already name their dissenter in the
  **rendered** text. The recoverable analytic value was much smaller than F2 implied.
- **Owner ruling: published prose only.** The 3,001 comment-hidden positions are not
  ingested.

What the published text did yield: 4 unparsed divided-vote grammars + en-dash tallies →
named rows **409 → 469**, named-roll motions **256 → 270**. Separately, a defect F2 never
identified turned out to matter more — v2 took each motion's result from the first `Pass`
keyword anywhere in a segment up to 40k chars long, so **15 motions were reporting a `Pass`
inherited from a different motion** (2020-06-23 m1 borrowed one from ~10k chars downstream
while its own item had FAILED). Those now carry an honest blank; 1 flipped to `Fail`; 2
impossible attributions (Nay rows against a `(7-0)` tally) were removed.

**Lesson for the failure library:** F2 is itself an instance of the pathology it reported —
a conclusion drawn from text without checking whether the source *published* it. Added to
the skill appendix as "recoverable data documented as an honest source ceiling," with the
inverse now also noted: verify that apparently-missing data was ever rendered.

Residual queued in TODO.md: ~16 divided motions remain un-named due to motion↔result-marker
misalignment (needs marker-anchored segmentation, which rewrites the motion spine).

## 9. Non-mutation record

- Baseline `validate_entity.py --all`: all 9 entities 0 FAIL / 0 WARN (saved pre-audit).
- 15,834 files across the 9 entity dirs at start.
- **No repo data file was created, modified, or deleted.**
- Three stray 0-byte `gov.db` files were created by agents running `sqlite3 gov.db` with a
  relative path from inside an entity dir (`utah_county/`, `summit_county/`,
  `juab_county/elections/`). All three were verified empty and removed — they were audit
  artifacts, not repo content.
- **Closing proof:** `validate_entity.py --all` after the audit is **byte-identical** to the
  pre-audit baseline, and the file count across the 9 entity dirs returned to **15,834 —
  exactly the starting count**. No repo data file was created, modified, or deleted.
- Files changed by the audit's *reporting* step, all outside the data layers: this report,
  `TODO.md` (residual 2 checked off + the ranked fix list added), the skill's failure-library
  appendix, and `screen_corpus.py`'s two new detectors.
