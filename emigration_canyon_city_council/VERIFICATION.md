# Emigration Canyon — Independent Verification

**Originally verified:** 2026-07-12 · **Re-verified and rewritten:** 2026-08-01
**Scope:** the built core (council + PC minutes/votes, elections, geo, comments, db, weeks).
**Method:** conformance validator, doc-vs-disk reconciliation, source ground-truth (quoting
the minutes), and — in the 2026-07-12 pass only — a live PMN gap probe and an outside
election cross-check.
**Result:** every built dataset **PASS** — `scripts/validate_entity.py emigration_canyon` =
**21 PASS / 5 WARN / 0 FAIL** (+ federation 1 PASS). The 5 WARN are all documented
extensions/advisories, none are defects. No fabrication found. **Verdict: SHIP.**

> **Why this file was rewritten (2026-08-01).** The 2026-07-12 edition asserted "429 motions
> (Council 288 + PC 141) reconciles exactly." That was true when written and is **stale now**:
> three township-era council minutes were recovered from PMN and promoted on 2026-07-17
> (+8 vote rows, +9 motions), so the entity carries **438 motions (Council 297 + PC 141)**.
> Every checkable number in this document has been re-measured against the live entity;
> §9 is the change log of what moved. The 2026-07-12 verification *narrative* (source
> ground-truth quotes, the PMN-purge probe, the election cross-check) is retained where it
> is still true, with its measurement date attached.

Emigration Canyon is a **~1,600-person canyon community** that incorporated as an
**Emigration Canyon Metro Township (2017-01-01)** and converted to a **CITY (2024-05-01, H.B.
35)** — one 5-member, all-at-large body throughout, whose **peer-selected Mayor PRESIDES AND
VOTES** (the Millcreek pattern; max tally = 5). Both facts were re-verified against source
below (§3) and still hold.

---

## 1. PASS/FAIL by dataset (measured 2026-08-01)

| Dataset | Verdict | Basis |
|---|---|---|
| `meeting_minutes/` (Council) minutes | **PASS** | **89** docs indexed, all paths exist, all dates parse; **81 `pdf-text` + 7 `ocr` + 1 `docx-text`**; 2018-10-25 → 2026-05-19 |
| `meeting_minutes/` votes | **PASS** | **297** motions / **301** CSV rows; `validate_votes.py` PASS; contested rows exact-match source (§3); JSON→CSV→db all reconcile (§2) |
| `planning_commission/` minutes | **PASS** | **60** docs indexed (59 `pdf-text` + 1 `ocr` — the 2025-11-13 doc promoted from `pmn_backfill/` 2026-07-16), all paths exist, all dates parse; 2018-11-15 → 2026-06-11 |
| `planning_commission/` votes | **PASS** | **141** motions (139 `provenance=minutes` + 2 `pmn_minutes`); structured `Motion/Motion by/Vote` grammar; recommendations verified (§3d) |
| `election_results/` | **PASS** | **5** race rows (2017, 2019, 2023, 2025 general, 2025 primary) + candidate/precinct tables; the 2023 + 2025 winners and margins were cross-checked against outside sources 2026-07-12 (§5) |
| `geo/` | **PASS (scope-limited)** | single-polygon boundary (all-at-large — no districts); precinct layer + `address_to_district.py` present |
| `public_comments/` | **PASS (honest-empty)** | header-only `all_comments_clean.csv` + `AVAILABILITY.md`; city publishes no written-comment archive (in-person only) — a legitimate honest zero |
| `db/civic.db` | **PASS** | **438 motions (Council 297 + PC 141)**, **13 votes**, 132 meetings, 16 persons, 16 applications — reconciles exactly to the flat CSVs (validator h.db, delta +0); build prints `INTEGRITY: OK` |
| `weeks/` | **PASS** | **82** weekly bundles; weekly vote sum **301 == flat total**; not stale |

**The 5 WARN, itemised** (none is a defect): `b.header` ×2 — the documented trailing
`provenance` 14th column on both `all_votes.csv` files; `d.index` ×2 — the documented
`meeting_type,pmn_notice_id,pmn_file_id` index extensions; `f.tally` — the narrative-tally
advisory (1/6 named-roll tallies match the printed result string, because EC names only the
dissenter and leaves the majority unnamed; see §3). *The 2026-07-12 edition also counted the
optional README/VERIFICATION files as WARNs; the validator now scores those PASS.*

---

## 2. Doubly-stored facts reconcile (index ↔ CSV ↔ JSON ↔ db ↔ weeks)

| Fact | Council | PC | Cross-check |
|---|---|---|---|
| Minutes docs on disk == index rows | 89 == 89 | 60 == 60 | every indexed `path` exists (validator d.index) |
| Motions in `all_votes.csv` | 297 | 141 | == per-`votes/…json` extraction (`validate_votes.py` PASS, CSV 301 == expected 301) |
| Motions in `db` | 297 | 141 | `motion` = **438** total; `body` split Council 297 / PlanningCommission 141 |
| Named member-vote rows == db `vote` | 10 | 3 | **13 CSV named rows == 13 db votes, 0 dropped** (validator h.db, delta +0) |
| Weekly vote rows == flat total | — | — | **301 == 301** (validator i.weeks) |
| `db` meeting rows | 76 (council w/ ≥1 motion) | 56 (PC w/ ≥1 motion) | **132 total** — see note |
| `provenance` split | 293 `minutes` / 8 `pmn_minutes` | 139 `minutes` / 2 `pmn_minutes` | audited-primary is filterable from recovered |

**The 13 named member-vote rows** are the entire attributed record (this is a narrative-tally
council; unanimous majorities are honestly unnamed). They reconcile exactly:

| # | Body | Date | Member | Vote | Result |
|---|---|---|---|---|---|
| 1 | PC | 2019-11-14 | Tim Harpst | Abstain | Pass (1 abstain) |
| 2 | Council | **2021-02-25** | **Gary Bowen** | **Nay** | 4-1 Pass |
| 3 | Council | 2021-04-27 | David Brems | Recuse | 4-1 Pass |
| 4 | Council | 2021-08-24 | Joe Smolka | Abstain | 4-1 Pass |
| 5 | Council | 2021-12-14 | Catherine Harris | Abstain | 4-1 Pass |
| 6 | PC | 2022-11-17 | Tim Harpst | Abstain | Pass (1 abstain) |
| 7–11 | Council | 2023-08-22 | Pinon / Brems / Hawkes / Smolka **Aye**, Harris **Nay** | full inline roll call | 4-1 Pass |
| 12 | Council | 2023-10-24 | Joe Smolka | Nay | 4-1 Pass |
| 13 | PC | 2026-06-11 | Andrew Wallace | Nay | Pass (1 nay) |

Row 2 is new since 2026-07-12 (recovered 2026-07-17 with the 2021-02-25 minutes); rows 3 and
7–11 were present but were summarised, not enumerated, in the prior edition — its "6 named
member-vote rows" line under-counted the 2021-04-27 recusal and the 2023-08-22 five-name roll.
**Contested council motions: 6** (2021-02-25, 2021-04-27, 2021-08-24, 2021-12-14, 2023-08-22,
2023-10-24). **Contested PC motions: 3.**

**Note on db meeting count (132 vs 149 docs).** The `meeting` table is motion-driven: **17**
indexed docs recorded **no formal motion** — 13 council (2019-01-31, 2019-04-08, 2019-04-25,
2019-11-19, 2021-03-04, 2021-03-16, 2021-05-18, 2021-05-24, 2022-04-28, 2023-03-28,
2024-02-22 ×2, 2025-01-28) and 4 PC (2019-06-13, 2021-01-06, 2023-01-26, 2026-03-12) — and
therefore create no `meeting` row. The canonical `minutes_index.csv` files still hold all
**149** docs; this is a derived-layer characteristic, not data loss.

---

## 3. Source ground-truth (quoting the minutes)

The six 2026-07-12 spot-checks were **re-run against the current files on 2026-08-01** — every
quoted string is still present in the named document, so (a)–(f) below stand unmodified.

**(a) Township-era mayor VOTES — 2023-10-24 (contested, Metro Township era).**
Minutes verbatim:
> *"Council Member Harris, seconded by Council Member Brems, moved to approve Resolution
> 2023-10-02. **The motion passed 4 to 1, showing Mayor Smolka voted in opposition.**"*

CSV row: `member=Joe Smolka, vote=Nay, result=4-1 Pass`. **Exact match.** This proves the
peer-selected Mayor is a **full voting member** counted in the 5 (a 4-1 on a 5-member body)
and dissents on the record — the township side of the seam.

**(b) City-era mayor VOTES — 2025-08-26 (City era).** Minutes verbatim (multiple motions):
> *"Council Member Brems moved to approve Ordinance 2025-O-09, rezoning the above parcel from
> RM to FR-20. Council Member Hawkes seconded the motion; **vote was 5-0, unanimous in favor.**"*

Mayor Brems both moves motions and is counted in the 5-0 tally — the **city side of the seam**.
Together (a)+(b) prove the **Smolka → Brems** presiding-mayor change is detected and modeled
correctly (Millcreek pattern, max tally 5), not an executive non-voting mayor.

**(c) Contested — 2021-12-14.** Minutes: *"passed 4 to 1, showing Council Member Harris
abstained from the vote."* → CSV `member=Catherine Harris, vote=Abstain, result=4-1 Pass`.
**Exact match.**

**(d) PC land-use recommendation — 2025-07-10.** Minutes verbatim:
> *"**Motion:** To recommend application #OAM2025-001433 Consideration of an ordinance
> repealing Chapters… **Motion by:** Commissioner Geroux · **Vote:** Commissioners voted
> unanimously in favor (of commissioners present)."*

Extracted as a `Land-Use/Recommendation` (the PC is a recommending body). Structured PC grammar
verified; the recommendation and its OAM case number are captured. **Faithful.**

**(e) OCR council doc that yielded motions — 2024-07-30** (`format=ocr`, 5 motions).
Minutes verbatim: *"Council Member Brems moved to approve Resolution 2024-07-01… Council
Member Hawkes seconded the motion; **vote was 4-0, unanimous in favor. Council Member Harris
was absent from the vote.**"* Extracted as a 4-0 (5-member body, 1 absent). Footer OCR noise
(`¢`, `e`) is present but **cosmetic**; the motion grammar is intact and correctly parsed.
Preserved OCR artifacts are positive evidence of faithful transcription, not fabrication.

**(f) OCR council docs that yielded ZERO motions — 2024-02-22 (`ocr`) & 2025-01-28 (`ocr`).**
Both are readable OCR of **discussion-only meetings** — 2024-02-22 is a *Community Council
reorganization* work session, 2025-01-28 an animal-services / fire / presentation agenda —
that recorded **no formal motion**. A grep for `motion|moved|second|vote|unanimous|N-M` finds
nothing in either body. (The companion 2024-02-22 *Special* meeting, a born-digital
`pdf-text` doc, likewise recorded 0 motions — so that date's zero is not even OCR-caused.)
**These are genuine no-motion meetings**, correctly yielding no fabricated votes. Both remain
zero-motion as of 2026-08-01. (Minor doc nuance: the top-level `CLAUDE.md` frames the two
`ocr` zeros as an "OCR-quality limit"; the more precise cause is "discussion-only, no formal
motions," compounded by imperfect OCR — the born-digital re-fetch TODO is still open.)

**(g) NEW 2026-08-01 — the ABSENT/EXCUSED roll is now read, and it cross-checks the tallies.**
`meeting_minutes/extract_votes.py` credited every roster surname in the attendance header as
PRESENT, including the members printed under `COUNCIL MEMBERS EXCUSED:` / `Council Members
Absent:` (§9). With the absent roll parsed, **23 of 89 council meetings** now record 1–2
absentees, and an independent check holds across the whole corpus: **no printed tally exceeds
the number of members recorded present — 0 violations in 297 motions** (before the fix this
check was vacuous, every meeting reading 5-present). Worked example, 2026-02-17:
> header *"Council Members Present: … Council Members Absent: …"* → Brems / Harris / Griffith
> present, Hawkes + Pinon absent; narrative *"quorum was present, noting Council Members
> Hawkes and Pinon were excused"*; motions print *"**3-0**, unanimous in favor with Council
> Members Hawkes and Pinon absent from the vote."*

**One source contradiction found and left city-faithful — 2023-06-27.** The header prints
`COUNCIL MEMBERS EXCUSED: DAVID BREMS`, but the body has Brems speaking 12 times and **moving
Ordinance No. 2023-06-01**. The header is the clerk's error (its present/excused block is
identical to the prior 2023-05-23 meeting's). Nothing was overwritten: `roster.csv` counts
attendance as *present-block ∪ that meeting's movers/seconders/named voters*, so Brems is
correctly retained for 2023-06-27 while the header is left exactly as printed. The other 22
changed meetings have **zero** narrative participation by the absent member.

---

## 4. KEY CHECK — the pre-2018-10 404 gap is GENUINE (not a missed harvest)

*(Live PMN probe run 2026-07-12; not re-run 2026-08-01 — network probes are not repeated on a
documentation pass. The on-disk conclusion is unchanged: council coverage still begins
2018-10-25, PC 2018-11-15.)*

Coverage begins **2018-10-25 (council)** / **2018-11-15 (PC)**; 2017 and scattered 2018–19
meetings sit in `minutes_unrecovered.csv` with reason *"PMN file store purged (attachments
404)."* A **sibling build (Kearns) had a FALSE gap** — its "audio-only" back-catalog was
actually harvestable on PMN — so this claim was independently re-tested live (browser UA)
against the PMN notice pages **and** the attachment file-store URLs.

| PMN notice (date, body) | Attachment link on the notice | `GET /pmn/files/<id>` result |
|---|---|---|
| 369113 · 2017-01-04 · Council | *(no attachment — agenda embedded as text)* | n/a — no minutes doc ever posted |
| 368993 · 2017-01-12 · PC | `269375.pdf` (a *Cancelled* notice) | **404**, 315-byte error page |
| 440741 · **2018-01-15 · Council** | **`406463.pdf` labelled "Meeting Minutes"** | **404**, 315-byte error page |
| 461135 · 2018-05-17 · PC | `391513.pdf` (a *Cancelled* notice) | **404**, 315-byte error page |
| (audio) 362997.mp3 · 2018-01-15 | — | **404**, 315-byte error page |
| **459655.pdf · 2018-10-25 · Council** (earliest recovered) | — | **200**, 68,960 bytes, `application/pdf` |
| **511437.pdf · 2018-11-15 · PC** (earliest recovered) | — | **200**, 289,998 bytes, `application/pdf` |
| 1456089.pdf · 2026-05-19 · Council (current) | — | **200**, 461,467 bytes |

**Conclusion — the gap is genuine.** The notice *metadata* survives (and for 2018-01-15 still
lists a "Meeting Minutes" attachment), but the underlying `/pmn/files/<id>` store returns a
315-byte 404 for **every** pre-2018-10 file tested, while files from 2018-10 onward download
normally. The surviving early files also carry **higher, later-issued file ids** (459655,
511437 > the purged 406463, 391513), consistent with an upstream purge/re-post of the store
around mid-2018. **This is the OPPOSITE of the Kearns false gap** — there the files actually
downloaded; here they are truly purged. The honest-gap logging is correct.

**Ledger as measured 2026-08-01:** `minutes_unrecovered.csv` holds **31 council** rows
(3 `PMN file store purged`; the other 28 are notice/agenda-posted-but-no-approved-minutes
dates, 12 of which have meeting audio on PMN) and **73 PC** rows (26 purged + 47
notice-only). *The 2026-07-12 edition cited "Council 14"; the council ledger has since been
expanded by the PMN crosscheck sweep to log the agenda-and-audio-only dates it surfaced —
more honest gaps recorded, not more data lost.* The documented backfill avenue named in the
recon ("MSD AgendaCenter secondary mirror") was later **disproved** — MSD's AgendaCenter hosts
the MSD Board of Trustees, not the townships' own bodies (all 189 meeting-ids enumerated,
0 EC minutes; see the top-level `CLAUDE.md`) — so the 2017 purge is a permanent gap on
present channels.

*Minor:* two of the "purged" PC rows (2017-01-12, 2018-05-17) were **cancelled meetings**
whose only attachment was a cancellation notice; the unrecovered `reason` string
("file store purged") is slightly imprecise for these — the meeting produced no minutes
because it did not convene. Cosmetic; the outcome (no minutes) is correct either way.
**Still open as of 2026-08-01** (both rows still read "PMN file store purged").

---

## 5. External election cross-check (browser UA)

*(Run 2026-07-12 against the Salt Lake County Clerk official results and `emigration.utah.gov`;
not re-run 2026-08-01. The rows quoted below were re-read from
`election_results/emigration_canyon_races.csv` on 2026-08-01 and are unchanged.)*

- **2023 Metro Township Council At-Large (3 seats):** CSV winners **Catherine M Harris (298),
  Jennifer Hawkes (277), David Paul Brems (277)**; runner-up **Tyler Tippetts (164)**,
  margin 113. Salt Lake County's official 2023 canvass confirms **Hawkes 277 / Brems 277
  (tie) / Tippetts 164** — exact. Harris was top vote-getter; Tippetts did not win. ✓
- **2025 City of Emigration Canyon Council At-Large (1 seat):** CSV winner **Roberto Pinon
  (324, 61.71%)** over Jacob Steed (201), margin 123; primary top-two (Pinon/Steed) also
  captured as a separate row (Pinon 197, 51.84%, margin 81). The city site confirms
  **Robert Pinon** on the current council. ✓
- **Mayor David Brems (city era):** confirmed by the city site and current PMN agendas. The
  **Smolka → Brems** transition is externally corroborated — a Sept 2024 minutes header still
  shows **Mayor Joe Smolka**; by Jan 2026 **Brems is Mayor** — matching the per-document mayor
  detection across the seam. ✓
- **Current 5-member roster** (Brems, Hawkes, Harris, Pinon, Griffith) matches the outside
  source exactly. ✓
- **Decoys correctly excluded:** the Emigration Canyon *Improvement District* (sewer/water,
  its own elected board) and the 2015 MSD ballot question are absent from the council races —
  as required.

**No election discrepancies.** **NOT yet externally cross-checked:** the **2017** (Joe Smolka,
338, 51.37%) and **2019** (Jennifer Hawkes, 300, 29.85%, margin 48) rows, which post-date the
2026-07-12 pass — the 2019 contest is the one the campaign-finance layer proved existed against
the recon's "no 2019 contest" assumption. They are internally well-formed (25-col superset,
validator m.elections PASS) but carry no outside confirmation yet; treat as a residual (§7).

---

## 6. Screener summary (both corpora clean — measured 2026-07-12)

*Scoped honestly: these numbers were measured on the **then-86-doc** council corpus and the
60-doc PC corpus. EC has no `screen_corpus.py` of its own, so the screen was not re-run on
2026-08-01; the **3 council docs promoted 2026-07-17** (2021-01-28, 2021-02-25, 2023-01-24)
have therefore not been statistically screened. Two are born-digital PDF text and one is a
`.docx` extraction, and all three parsed clean, but the screen is a residual (§7).*

- **Council** (86-doc corpus): dict_ratio median 0.777 (min 0.725), **0/86 dict outliers**,
  **0/86 weird-char outliers**, **1/86 split-word outlier** (2020-02-27, 3.11/1k — a mild OCR
  year, benign). `ends_mid`/`repeated_line` flags are advisory (per-page headers/footers).
- **PC**: dict_ratio median 0.751, **split-word 0.00 across every year**, weird-char ~0.0003 —
  essentially pristine born-digital text.

---

## 7. Residual items (all non-blocking — for the TODO queue, not ship-blockers)

1. **Born-digital re-fetch of the 2 zero-motion OCR council docs** (2024-02-22, 2025-01-28) to
   confirm no motion was lost to scan quality — textual + meeting-type evidence says these were
   genuinely motion-free discussion sessions (low priority). **Still open.**
2. **2017 / early-2018 backfill** — the PMN store is purged (§4) and the MSD AgendaCenter
   avenue has since been **disproved**. No known remaining channel; treat the pre-2018-10
   record as a permanent honest gap unless a new source appears. **Still open (reclassified).**
3. **Cosmetic:** tighten the `minutes_unrecovered.csv` `reason` for the two cancelled-meeting PC
   rows (2017-01-12, 2018-05-17) from "file store purged" to "meeting cancelled".
   **Still open** (verified unchanged 2026-08-01).
4. **NEW:** external cross-check of the **2017 and 2019** election rows (§5).
5. **NEW:** re-screen the council corpus at 89 docs (§6) — EC would need its own
   `screen_corpus.py`.
6. **NEW (upstream, not EC's to fix):** the **PC attendance table is not name-attributable.**
   PC minutes record attendance as a checkbox matrix (`Commissioners` / `Public Mtg` /
   `Business Mtg` / `Absent` columns with `x` marks) whose column-to-name mapping is destroyed
   by PDF text extraction — all 59 "Absent" occurrences across the PC corpus are the column
   *header*, never a named commissioner. `planning_commission/roster.csv` therefore lists every
   commissioner on the sheet for each meeting and **cannot** distinguish absentees without
   fabricating. Recorded here as an honest source ceiling; deliberately **not** "fixed".

None of these affect the integrity of what is on disk. **All built datasets verified faithful
— SHIP.**

---

## 8. Addendum — 2026-07-16 PC 2025-11-13 minutes promotion *(retained; one claim superseded)*

The 1 doc recovered by the `pmn_backfill/` sweep (PC **2025-11-13**, PMN file 1363983,
late-posted image-only scan → tesseract OCR) was promoted into `planning_commission/`:
index row added (`format=ocr`), the satisfied `minutes_unrecovered.csv` row (notice
1032655) dropped, raw PDF retained at `planning_commission/raw/2025/`. Re-extraction added
**2 motions** (both tally-only unanimous: approve the 2025-09-24 PC minutes, Wallace mover;
continue SUB2025-001345 Glassman 3-lot subdivision to 2025-12-11, Karkut mover), diffed
**additive-only** against the prior `all_votes.csv` (139 → 141 rows, 0 changed, 0 removed).
`all_votes.csv` gained the collection-standard trailing `provenance` column (139 `minutes`
+ 2 `pmn_minutes`). Both motions ground-truthed verbatim against the OCR text; the doc's
approval "with amendments" is recorded in the 2025-12-11 PC minutes.

Two claims from that addendum are **no longer current**:
- Its post-promotion counts (*"db 429 motions"*, *"motions_std 141"*, *"21 PASS / 4 WARN /
  1 FAIL"*) are superseded by §1–§2 above.
- Its `l.crosswalks` **FAIL** (missing `Recuse` vote_values row, from the 2026-07-12 T3.1(k)
  council recount) has since been repaired at the repo root: `l.crosswalks` now **PASSES**.
- Its closing "known source ceiling" — *"the extractor does not read the clerk's `2nd by:`
  seconder label … ~129 printed seconders unparsed across 51 docs"* — was **fixed 2026-07-17**.
  `planning_commission/extract_votes.py` now matches all three labels
  (`Second by:` / `Seconded by:` / `2nd by:`). Re-measured 2026-08-01: 52 PC docs carry 131
  `2nd by:` labels and only **17 of 141** PC motions still have a blank seconder (those are
  genuine — an inline procedural motion, or a label the OCR left with no readable surname).

---

## 9. Change log — what moved between the 2026-07-12 and 2026-08-01 editions

| Claim (2026-07-12 edition) | Now | Cause |
|---|---|---|
| Council minutes **86** docs | **89** | 3 township-era minutes recovered from PMN + promoted 2026-07-17 (2021-01-28, 2021-02-25, 2023-01-24) |
| Council motions **288** | **297** | +9 from the same promotion (+8 vote rows) |
| db motions **429** (288 + 141) | **438** (297 + 141) | same |
| db votes **12** / "6 named member-vote rows" | **13** / 13 | +1 real (2021-02-25 Bowen Nay); the "6" also under-counted the 2021-04-27 recusal and the 2023-08-22 five-name roll |
| Contested council motions **5** | **6** | 2021-02-25 recovered |
| db meetings **129** | **132** | 3 promoted docs carried motions |
| weeks **79** bundles / vote sum **288** | **82** / **301** | rebuilt over the larger corpus |
| Council format split **79 pdf-text + 7 ocr** | **81 pdf-text + 7 ocr + 1 docx-text** | the 2023-01-24 recovery is a `.docx` |
| `minutes_unrecovered` council **14** | **31** | PMN crosscheck sweep logged the agenda/audio-only dates (more honest gaps recorded) |
| election `races.csv` **4** rows | **5** | 2017 + 2019 rows added; a 2025 primary row split out |
| validator **21 PASS / 4 WARN / 0 FAIL** (+§8's 1 FAIL) | **21 PASS / 5 WARN / 0 FAIL** | README/VERIFICATION WARNs now score PASS; `f.tally` advisory + 4 documented-extension WARNs remain; the `l.crosswalks` FAIL is repaired |
| §8 "~129 seconders unparsed" | **17 blank of 141** | `2nd by:` label support added 2026-07-17 |
| *(not previously checked)* | **absent/excused roll now parsed** | `parse_present()` credited absent members as present — fixed 2026-08-01 (§3g); `all_votes.csv` **byte-identical** across the fix (the bug never touched votes), `roster.csv` attendance corrected on 23 meetings |
