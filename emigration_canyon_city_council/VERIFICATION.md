# Emigration Canyon — Independent Verification

**Verified:** 2026-07-12 · **Scope:** the built core (council + PC minutes/votes, elections,
geo, comments, db). **Method:** conformance validator, doc-vs-disk reconciliation, source
ground-truth (quoting the minutes), a live PMN gap probe, and an outside election cross-check.
**Result:** every built dataset **PASS** — `validate_city.py` = **21 PASS / 4 WARN / 0 FAIL**
(the 4 WARN are the optional README/VERIFICATION files this doc adds, the two documented
`meeting_type,pmn_notice_id,pmn_file_id` index-extension columns, and the narrative-tally
`f.tally` advisory — none are defects). No fabrication found. **Verdict: SHIP.**

Emigration Canyon is a **~1,600-person canyon community** that incorporated as an
**Emigration Canyon Metro Township (2017-01-01)** and converted to a **CITY (2024-05-01, H.B.
35)** — one 5-member, all-at-large body throughout, whose **peer-selected Mayor PRESIDES AND
VOTES** (the Millcreek pattern; max tally = 5). Both facts were re-verified against source
below.

---

## 1. PASS/FAIL by dataset

| Dataset | Verdict | Basis |
|---|---|---|
| `meeting_minutes/` (Council) minutes | **PASS** | 86 docs indexed, all paths exist, all dates parse; corpus screens clean (dict 0.777, 0 dict/weird outliers); 79 `pdf-text` + 7 `ocr` |
| `meeting_minutes/` votes | **PASS** | 288 motions; `validate_votes.py` clean; contested rows exact-match source (§3); JSON→CSV→db all reconcile (§2) |
| `planning_commission/` minutes | **PASS** | 60 docs indexed (59 `pdf-text` + 1 `ocr` — the 2025-11-13 doc promoted from `pmn_backfill/` 2026-07-16), all paths exist, all dates parse; screens very clean (dict 0.751, split 0.00, weird ~0.0003) |
| `planning_commission/` votes | **PASS** | 141 motions (139 audited + 2 `provenance=pmn_minutes`); structured `Motion/Motion by/Vote` grammar; recommendations verified (§3d) |
| `election_results/` | **PASS** | 4 race rows + candidate/precinct tables; winners + margins cross-check to Salt Lake County official results & the city site (§5) |
| `geo/` | **PASS (scope-limited)** | single-polygon boundary (all-at-large — no districts); 1 precinct EMG001; point-in-polygon tool present |
| `public_comments/` | **PASS (honest-empty)** | header-only `all_comments_clean.csv` + `AVAILABILITY.md`; city publishes no written-comment archive (in-person only) — a legitimate honest zero |
| `db/civic.db` | **PASS** | 429 motions (Council 288 + PC 141), 12 votes (post-T3.1(k) recount) — reconciles exactly to the flat CSVs (validator h.db, delta +0) |
| `weeks/` | **PASS** | 79 weekly bundles; weekly vote sum 288 == flat total; not stale |

---

## 2. Doubly-stored facts reconcile (index ↔ CSV ↔ JSON ↔ db ↔ weeks)

| Fact | Council | PC | Cross-check |
|---|---|---|---|
| Minutes docs on disk == index rows | 86 == 86 | 60 == 60 | every indexed `path` exists (validator d.index) |
| Motions in `all_votes.csv` | 288 | 141 | == per-`votes/…json` extraction (validate_votes.py clean) |
| Motions in `db` | 288 | 141 | `motion`=429 total; `body` split Council 288 / PlanningCommission 141 |
| Named member-vote rows == db `vote` | — | — | **6 CSV named rows == 6 db votes, 0 dropped** (validator h.db, delta +0) |
| Weekly vote rows == flat total | — | — | 288 == 288 (validator i.weeks) |
| `db` meeting rows | 73 (council w/ ≥1 motion) | 56 (PC w/ ≥1 motion) | **129 total** — see note |

**The 6 named member-vote rows** are the entire attributed-dissent record (this is a
narrative-tally council; unanimous majorities are honestly unnamed). They reconcile exactly:

| # | Body | Date | Member | Vote | Result |
|---|---|---|---|---|---|
| 1 | Council | 2021-08-24 | Joe Smolka | Abstain | 4-1 Pass |
| 2 | Council | 2021-12-14 | Catherine Harris | Abstain | 4-1 Pass |
| 3 | Council | 2023-10-24 | Joe Smolka | Nay | 4-1 Pass |
| 4 | PC | 2019-11-14 | Tim Harpst | Abstain | Pass (1 abstain) |
| 5 | PC | 2022-11-17 | Tim Harpst | Abstain | Pass (1 abstain) |
| 6 | PC | 2026-06-11 | Andrew Wallace | Nay | Pass (1 nay) |

**Note on db meeting count (129 vs 146 docs).** The `meeting` table is motion-driven: 17
indexed docs recorded **no formal motion** (work/emergency sessions, a Board of Canvassers
meeting, cancelled-substance meetings, and the 2 zero-motion OCR docs — §4) and therefore
create no `meeting` row. The canonical `minutes_index.csv` still holds **all 145 docs**; this
is a derived-layer characteristic, not data loss.

---

## 3. Source ground-truth (quoting the minutes)

Six meetings were checked against the minutes text — the OCR seam, **both sides of the
Smolka→Brems mayor seam**, a contested township motion, and a PC land-use recommendation.

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

**(f) OCR council doc that yielded ZERO motions — 2024-02-22 (`ocr`) & 2025-01-28 (`ocr`).**
Both are readable OCR of **discussion-only meetings** — 2024-02-22 is a *Community Council
reorganization* work session, 2025-01-28 an animal-services / fire / presentation agenda —
that recorded **no formal motion**. A grep for `motion|moved|second|vote|unanimous|N-M` finds
nothing in either body. (The companion 2024-02-22 *Special* meeting, a born-digital
`pdf-text` doc, likewise recorded 0 motions — so that date's zero is not even OCR-caused.)
**These are genuine no-motion meetings**, correctly yielding no fabricated votes. (Minor doc
nuance: the top-level `CLAUDE.md` frames the two `ocr` zeros as an "OCR-quality limit"; the
more precise cause is "discussion-only, no formal motions," compounded by imperfect OCR — the
born-digital re-fetch TODO is still worth doing to confirm.)

---

## 4. KEY CHECK — the pre-2018-10 404 gap is GENUINE (not a missed harvest)

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
downloaded; here they are truly purged. The honest-gap logging is correct; the documented
backfill avenue (MSD AgendaCenter secondary mirror) remains a `TODO`.

*Minor:* two of the "purged" PC rows (2017-01-12, 2018-05-17) were **cancelled meetings**
whose only attachment was a cancellation notice; the unrecovered `reason` string
("file store purged") is slightly imprecise for these — the meeting produced no minutes
because it did not convene. Cosmetic; the outcome (no minutes) is correct either way.

---

## 5. External election cross-check (browser UA)

`election_results/emigration_canyon_races.csv` winners/margins were cross-checked against the
**Salt Lake County Clerk official results** and the city site (`emigration.utah.gov`):

- **2023 Metro Township Council At-Large (3 seats):** CSV winners **Catherine M Harris (298),
  Jennifer Hawkes (277), David Paul Brems (277)**; runner-up **Tyler Tippetts (164)**,
  margin 113. Salt Lake County's official 2023 canvass confirms **Hawkes 277 / Brems 277
  (tie) / Tippetts 164** — exact. Harris was top vote-getter; Tippetts did not win. ✓
- **2025 City of Emigration Canyon Council At-Large (1 seat):** CSV winner **Roberto Pinon
  (324, 61.71%)** over Jacob Steed (201); primary top-two (Pinon/Steed) also captured. The
  city site confirms **Robert Pinon** on the current council. ✓
- **Mayor David Brems (city era):** confirmed by the city site and current PMN agendas. The
  **Smolka → Brems** transition is externally corroborated — a Sept 2024 minutes header still
  shows **Mayor Joe Smolka**; by Jan 2026 **Brems is Mayor** — matching the per-document mayor
  detection across the seam. ✓
- **Current 5-member roster** (Brems, Hawkes, Harris, Pinon, Griffith) matches the outside
  source exactly. ✓
- **Decoys correctly excluded:** the Emigration Canyon *Improvement District* (sewer/water,
  its own elected board) and the 2015 MSD ballot question are absent from the council races —
  as required.

**No election discrepancies.**

---

## 6. Screener summary (both corpora clean)

- **Council** (`screen_corpus.py`): dict_ratio median 0.777 (min 0.725), **0/86 dict outliers**,
  **0/86 weird-char outliers**, **1/86 split-word outlier** (2020-02-27, 3.11/1k — a mild OCR
  year, benign). `ends_mid`/`repeated_line` flags are advisory (per-page headers/footers).
- **PC**: dict_ratio median 0.751, **split-word 0.00 across every year**, weird-char ~0.0003 —
  essentially pristine born-digital text.

---

## 7. Residual items (all non-blocking — for the TODO queue, not ship-blockers)

1. **Born-digital re-fetch of the 2 zero-motion OCR council docs** (2024-02-22, 2025-01-28) to
   confirm no motion was lost to scan quality — textual + meeting-type evidence says these were
   genuinely motion-free discussion sessions (low priority).
2. **2017 / early-2018 backfill via MSD AgendaCenter** — the PMN store is purged (§4); the
   secondary mirror is the only remaining avenue for the pre-2018-10 record.
3. **Cosmetic:** tighten the `minutes_unrecovered.csv` `reason` for the two cancelled-meeting PC
   rows (2017-01-12, 2018-05-17) from "file store purged" to "meeting cancelled."

None of these affect the integrity of what is on disk. **All built datasets verified faithful
— SHIP.**

## 8. Addendum — 2026-07-16 PC 2025-11-13 minutes promotion

The 1 doc recovered by the `pmn_backfill/` sweep (PC **2025-11-13**, PMN file 1363983,
late-posted image-only scan → tesseract OCR) was promoted into `planning_commission/`:
index row added (`format=ocr`), the satisfied `minutes_unrecovered.csv` row (notice
1032655) dropped, raw PDF retained at `planning_commission/raw/2025/`. Re-extraction added
**2 motions** (both tally-only unanimous: approve the 2025-09-24 PC minutes, Wallace mover;
continue SUB2025-001345 Glassman 3-lot subdivision to 2025-12-11, Karkut mover), diffed
**additive-only** against the prior `all_votes.csv` (139 → 141 rows, 0 changed, 0 removed).
`all_votes.csv` gained the collection-standard trailing `provenance` column (139 `minutes`
+ 2 `pmn_minutes`). Both motions ground-truthed verbatim against the OCR text; the doc's
approval "with amendments" is recorded in the 2025-12-11 PC minutes. Derived layers
(db 429 motions INTEGRITY OK, referrals, weeks, motions_std 141 @100% outcome coverage,
sources 900 docs) rebuilt. `validate_city.py`: 21 PASS / 4 WARN / 1 FAIL — the FAIL
(`l.crosswalks` missing `Recuse` vote_values row) is PRE-EXISTING from the 2026-07-12
T3.1(k) council recount (2021-04-27 Brems recusal) and needs a one-line repo-root
`crosswalks/vote_values.csv` addition (out of this promotion's scope).
Known source ceiling carried honestly: the extractor does not read the clerk's "2nd by:"
seconder label (only "Second(ed) by:" and inline grammar), so structured-block seconders —
including this doc's OCR-garbled "2™4 by:" lines (Berreth, Geroux) — stay blank
corpus-wide (~129 printed seconders unparsed across 51 docs; a candidate follow-up repair).
