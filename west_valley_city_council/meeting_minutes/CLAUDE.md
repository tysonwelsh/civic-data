# meeting_minutes/ — pipeline & vote-extraction notes

West Valley City council minutes (Hyland OnBase, `doctype=2`) converted to markdown,
plus the roll-call vote table extracted from them.

## Layout

```
meeting_minutes/
  minutes_index.csv            # 550 meetings (465 Council + 85 RDA/MBA): date,year,title,slug,path,source,source_url,format
  minutes/<year>/<week>/<date>_<slug>.md   # the markdown minutes (source of truth for votes)
  raw/                         # EMPTY — original PDFs were NOT retained (known gap, see below)
  extract_votes.py             # the parser (this pipeline)
  votes/<year>/<week>/<date>_<slug>.json   # one JSON per meeting (structured intermediate)
  votes/_validation_report.txt # tally-vs-result consistency log
  votes/_roster_by_year.json   # councilmembers seen in named roll calls, per year
  all_votes.csv                # long format, one row per member-vote (rebuilt from the JSONs)
  CLAUDE.md                    # this file
```

`all_votes.csv` columns: `date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`
(the `body` column sits right after `title`). Each per-meeting JSON also carries a
meeting-level `body` and a per-motion `body`.

`<week>` = the Monday of the meeting's week (WVC meets Tuesdays, 2nd & 4th of the month).

### Known gap — raw/ is empty (original PDFs not retained)

`raw/` was intended to hold the immutable original PDFs but is **empty** — the downloads
were not retained (most plausibly lost in the iCloud dataless-stub incident noted under
"RESOLVED" below, which also evicted 31 `.md` files). The markdown minutes on disk are
the extraction source of truth. Every original PDF remains **re-fetchable** from the
`source_url` in `minutes_index.csv`: replace `DownloadFile` with `DownloadFileBytes` in
the URL (the `DownloadFile` route returns a JS interstitial that does the same rewrite).
Spot-verified live 2026-07-02 (3/3 sampled URLs, council + RDA, 2020 and 2026, all
returned valid PDFs).

## Running

```
python3 meeting_minutes/extract_votes.py            # resumable: skips meetings whose JSON exists
python3 meeting_minutes/extract_votes.py --force    # re-parse everything
```

The script reads `minutes_index.csv`, parses each `.md`, writes one JSON per meeting,
then rebuilds `all_votes.csv`, `votes/_validation_report.txt`, and `votes/_roster_by_year.json`.
Everything is regenerable from `minutes/` + this script.

## Source format (what the minutes look like)

A recorded motion in a Regular meeting reads:

```
Councilmember Whetstone moved to approve Ordinance 26-03.
Councilmember Huynh seconded the motion.
A roll call vote was taken:
    Councilmember Wood          Yes
    Councilmember Whetstone     Yes
    ...
    Mayor Lang                  Yes
Unanimous.
```

Routine items (minutes approval, adjournment) instead say:
`A voice vote was taken and all members voted in favor of the motion.`  — a **tally-only**
vote with no per-member names.

### Format variation across years (the parser must absorb all of these)
- **Roll-call name prefix** varies: `Mr.` / `Ms.` / `Mrs.` (≈2020–21), **`Councilman`** /
  `Councilwoman` (the dominant 2022–2025 form, ~3,500 lines), `Councilmember` (2026),
  plus `Mayor`, `Mayor Pro Tem` / `Pro-Tem` / `Pro- Tem`, `Acting Mayor`.
- **Vote token**: `Yes`/`No` (and occasionally `Absent`). A member with a declared
  conflict of interest is marked **`N/A`** (sometimes `Conflict`) — recorded as **Recuse**.
- **Result word** after the block: `Unanimous.`, `Majority.`, or (rare) `The motion failed`.
  Sometimes followed by `Continued.`
- **Page breaks split roll-call lists.** A `pdftotext` page footer
  (`MINUTES OF COUNCIL REGULAR MEETING – <date>` + a page number like `-10-` + blanks)
  is injected mid-list. The parser skips this noise and keeps collecting the block.
- OCR typos in names: `Scot Harmon` → Scott Harmon, `Will Whetstone` → William Whetstone,
  truncations like `Christense` → Christensen (resolved by unique-prefix match to roster).

## Parser heuristics (`extract_votes.py`)

1. **Find motions** by the regex `<prefix> <Name> moved to <verb> …` (`RE_MOVED`). Each
   match is a candidate motion; `motion_no` is assigned in document order.
2. For each motion, look in a ~3,000-char forward window (bounded by the next motion so a
   vote is never stolen from the following item):
   - **Seconder**: `<prefix> <Name> seconded the motion`.
   - **Vote**: if `A roll call vote was taken` appears first → parse the per-member block
     (`parse_rollcall_block`), tolerating page-break noise and `N/A`/`Conflict` tokens,
     until the result word (`Unanimous`/`Majority`/`failed`) or the list ends.
     Otherwise if `voice vote was taken … in favor` → tally-only.
     Otherwise look for a nearby `Unanimous`/`Majority`/`all voted in favor` word.
   - If **no** vote outcome is found near the motion, the candidate is **skipped** (e.g. a
     motion superseded by a substitute motion that was never voted, or a "motion failed for
     lack of a second").
3. **Names**: roll-call lines give last names only; `LASTNAME_TO_FULL` maps each unique last
   name to a canonical full name (last names are unique across the 2020–2026 council).
   Mover/seconder names are normalized through the same table.
4. **Result string**: for named roll calls the parser builds `"<aye>-<nay>[-<n>A] <word> <Pass|Fail>"`,
   e.g. `7-0 Unanimous Pass`, `6-1 Majority Pass`, `2-5 Fail`. Pass/Fail is derived from the
   ayes-vs-nays count (a roll call with more Nay than Aye is `Fail`). For tally-only votes the
   `result` is the verbatim phrase (`Voice vote - all in favor`, `Unanimous`, etc.).

### `names_recorded` convention
- `names_recorded: true`  → a per-member roll call was found; member lists are filled and the
  motion emits one `all_votes.csv` row per member.
- `names_recorded: false` → only a tally/voice vote was recorded. **Member lists stay empty —
  we never guess who voted which way.** It emits a **single summary row** in `all_votes.csv`
  with `member` and `vote` blank (the motion + `result` are still captured).

## motion_type taxonomy (fixed 12 categories)

Classified by keyword over the motion text + the agenda heading immediately above it
(`classify()`), in priority order:

| Category | Trigger (first match wins) |
|---|---|
| Procedural/Administrative | adjourn/recess/reconvene; "approve the Minutes of …" |
| Public Hearing Action | open/close a public hearing |
| Appointment | appoint / elect / nominate / reappoint / Mayor Pro Tem |
| Land-Use/Zoning | zone change, rezone, subdivision, plat, conditional use, general plan, annex, vacate, right-of-way, development agreement |
| Budget Amendment | "amend … budget", budget amendment, appropriation |
| Grant-Funding | grant |
| Interlocal | interlocal / cooperation agreement |
| Contract/Purchase | contract, purchase, procure, bid, award, lease, warranty/quit-claim deed, professional services |
| Ordinance | mentions "ordinance" (and none of the above) |
| Resolution | mentions "resolution" (and none of the above) |
| Ceremonial | proclaim / recognition / honor / commend |
| Other | nothing matched |

Note: because land-use, budget, grant, interlocal and contract checks run **before** the
generic Ordinance/Resolution check, a budget-amending *ordinance* (e.g. Ord 19-49 "AMEND THE
BUDGET") is filed under **Budget Amendment**, and a zoning *ordinance* under **Land-Use/Zoning** —
this is intentional (the substantive subject, not the instrument, is the signal).

## Validation

`votes/_validation_report.txt` checks every named roll call for internal consistency:
- result says **Unanimous** but a **Nay** exists,
- result says **Majority** but **no Nay** recorded,
- result says **Fail** but ayes > nays,
- any roll-call name that couldn't be mapped to the roster.

### Known source discrepancies (NOT parser bugs)
Three meetings printed `Unanimous.` in the minutes while the per-member roll call directly
above it shows dissent — clerical errors in the official minutes:
- **2020-08-18** Regular, motion 5 — printed Unanimous, roll call is **5-1** (Mayor Bigelow No).
- **2021-07-06** Regular, motion 3 (Ord 21-40) — printed Unanimous, roll call is **4-2** (Fitisemanu, Lang No).
- **2023-01-24** Regular, motion 5 — printed Unanimous, roll call is **6-1**.

In every case the **per-member roll call is retained as the truth** and the `result` string
reflects the real tally; the verbatim "Unanimous" word is preserved in the string for audit.

## `body` column — governing body (Council vs RDA / CRA / CDRA / MBA)

In Utah the city council usually also sits **as the board** of the Redevelopment Agency
(RDA), Community Reinvestment / Community Development & Renewal Agency (CRA / CDRA), and
Municipal Building Authority (MBA) — same people, different legal capacity. The `body`
column (after `title`) tags which body took each vote so council-only analysis can
`filter body == "Council"`. The parser tags a motion non-Council two ways:
1. **Separate agency meeting** — the meeting `title` itself is "Redevelopment Agency" /
   "Municipal Building Authority" / "Community Reinvestment Agency" → every motion in it
   gets that body (`body_for_title`).
2. **In-council convene block** — text like "the Council **convened as the … Board of the
   Redevelopment Agency**" … "**reconvened as the City Council**" brackets a span; motions
   inside it are tagged accordingly (`build_body_spans` / `body_at`).
Board-capacity role synonyms (`Board Member` / `Agency Member` / `Authority Member` /
`Trustee` / `Chair` / `Director`) are recognized in the mover/seconder and roll-call
regexes and map to the **same** council member names — no new members are ever created.

### Body breakdown — Council + separately-acquired RDA & MBA
- **1,942 motions: Council 1,747 · RDA 132 · MBA 63** (rows: Council 8,908 · RDA 534 · MBA 213).
  Inside council meetings the agency *subjects* are voted by the **City Council** (every
  mover/seconder there is a "Councilmember"/"Mayor"), correctly tagged `Council`. The RDA and
  MBA **board's own** roll-call votes come from their **separate meetings** (below).

### RESOLVED — separate RDA / MBA meetings acquired (2026-06-25)
WVC holds standalone **Redevelopment Agency** and **Municipal Building Authority** meetings as
distinct OnBase meeting types. These were re-acquired this round:
- **Meeting-type IDs discovered:** RDA = **mtids 114 (Regular) + 115 (Special)**;
  MBA ("Building Authority") = **mtids 106 (Regular) + 107 (Special)** — found by probing the
  Search endpoint per-mtid (the `/Meetings` dropdown only lists current types 101–103).
- **Acquired: 85 minutes (56 RDA + 29 MBA), 2020–2026**, via the same OnBase
  `DownloadFileBytes` flow as the council types (born-digital text PDFs, no OCR). 17 RDA/MBA
  meetings exist with **no minutes PDF attached** (agenda-only) and are honestly skipped.
- Slugs `redevelopment-agency-meeting` / `municipal-building-authority-meeting` auto-tag
  `body=RDA` / `body=MBA` (title-keyed). The agency board's TIF / developer-subsidy / bond /
  project-area votes — the "follow the money" data — are now on disk.
- **Note (iCloud incident):** 31 council `.md` files had become unreadable iCloud "dataless"
  stubs (data evicted, path orphaned outside CloudDocs). Their votes survived in the per-meeting
  JSONs; the `.md` files were re-downloaded from OnBase to restore the canonical minutes.

## Coverage / honesty

- **550 meetings processed, 0 unparsed.** (Council 465: 221 Regular + 234 Study +
  10 special/strategic; plus 56 RDA + 29 MBA.)
- Council: **1,747 motions** extracted — **1,223 named roll-calls** (8,384 member-vote rows) +
  **524 tally-only** (voice votes — minutes approvals, adjournments, routine consent items).
- **Body breakdown: Council 1,747 (208 contested) · RDA 132 · MBA 63** — the separate
  agency meetings were acquired 2026-06-25 (see the RESOLVED section above); 220 contested
  motions across all bodies.
- **208 contested council motions** (≥1 Nay/Recuse) — the analytical signal.
- Study meetings usually carry only 1–2 procedural motions (minutes approval); Regular
  meetings hold the substantive votes. Both are parsed.
- The roster appears at 7 members every year 2020–2026 in named roll calls (the full council
  votes, Mayor included). One genuinely low-attendance meeting (**2025-01-14**, 4 members
  present) yields legitimate 4-0 votes — not a parse failure.

### Roster (canonical names; last name is the roll-call key)
| Last name | Full name | Seat / years |
|---|---|---|
| Bigelow | Ron Bigelow | Mayor (2020–2021) |
| Lang | Karen Lang | District 3 (2020–21) → **Mayor (2022+)** |
| Nordfelt | Lars Nordfelt | At-Large |
| Christensen | Don Christensen | At-Large |
| Huynh | Tom Huynh | District 1 |
| Buhler | Steve Buhler | District 2 (2020–2021) |
| Harmon | Scott Harmon | District 2 (2022+) |
| Whetstone | William Whetstone | District 3 (2022+) |
| Fitisemanu | Jake Fitisemanu | District 4 (2020–2023) |
| Wood | Cindy Wood | District 4 (2024+) |

Cross-referenced against the recon roster and `election_results/west_valley_races.csv` winners
(Christensen, Huynh, Harmon, Whetstone, Wood, Lang, Nordfelt all appear as elected winners).

### Known limitations
- A motion with **no recorded vote outcome** near it (superseded substitute motions, motions
  that died for lack of a second) is intentionally **skipped** — it is not counted as a vote.
- Consent-agenda bundles are recorded as one motion ("approve all items on the consent
  agenda") with one roll call; the individual ordinances/resolutions inside the bundle are not
  split out (they were not separately voted).
- `motion` text is the moved clause truncated at the first sentence boundary (≤400 chars);
  the full item description lives in the source `.md`.

---
*Doc corrections 2026-07-02 (audit `_audits/2026-07-02/report.md`, Phase 1.8): the
"raw/ — immutable original PDFs" claim was false — raw/ is empty (PDFs not retained);
replaced with an honest known-gap note incl. the verified re-fetch path
(`source_url` + DownloadFile→DownloadFileBytes, spot-checked live 2026-07-02).
minutes_index count 465 → 550 (RDA/MBA acquisition); the stale "RDA/CRA/CDRA/MBA 0 /
acquisition gap" coverage bullet updated to the measured Council 1,747 · RDA 132 ·
MBA 63 (220 contested total). All figures re-measured from `all_votes.csv` /
`minutes_index.csv`.*


## 2026-07-17 — PMN crosscheck: 2021-09-28 study meeting promoted
Promoted the 2021-09-28 Council Study Meeting (PMN file 767025) — repo previously had only the
Regular Meeting that date. +2 tally-only voice-vote motions. First pmn-sourced audited minutes
for WVC (source=pmn/format=text). The 2022 'Strategic Plan Minutes' lead was actually a verbatim
transcript (true date 2022-01-28) — NOT promoted; see pmn_backfill/CLAUDE.md.
