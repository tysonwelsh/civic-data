# planning_commission/ — West Valley City Planning Commission vote extraction

Roll-call votes extracted from the West Valley City **Planning Commission** minutes
(OnBase born-digital text PDFs → markdown). Covers BOTH meeting types the PC holds:
**"Planning Commission Regular Meeting"** (the action votes) and **"Planning
Commission Study Meeting"** (mostly discussion; occasional procedural votes). Data
floor **2020**. Modeled on `meeting_minutes/extract_votes.py` (the council pipeline).

## Layout

```
planning_commission/
  minutes_index.csv            # 264 meetings: date,year,title,slug,path,source,source_url,format
  minutes_unrecovered.csv      # meetings that HAPPENED but whose minutes we do not have
                               # (no document on OnBase, not yet posted, or the OnBase
                               #  document slot serves the WRONG meeting's PDF)
  minutes/<year>/<week>/<date>_<slug>.md   # markdown minutes (source of truth)
  raw/                         # EMPTY — original PDFs not retained; re-fetchable via minutes_index.csv source_url (DownloadFile→DownloadFileBytes; see meeting_minutes/CLAUDE.md)
  extract_votes.py             # the parser (this pipeline)
  validate_votes.py            # independent QA (JSON↔CSV reconcile, roster ranges)
  votes/<year>/<week>/<date>_<slug>.json   # one JSON per meeting
  votes/_validation_report.txt # built by extract_votes.py
  all_votes.csv                # long format, one row per member-vote
  roster.csv                   # commissioner, first_seen, last_seen, n_meetings
  CLAUDE.md                    # this file
```

`<week>` = the **Monday** of the meeting's week (PC meets ~2nd/4th of the month;
study sessions a couple of days before each regular meeting). `<slug>` is
`planning-commission-meeting` (regular) or `planning-commission-study-meeting`.

## Running

```
python3 planning_commission/extract_votes.py            # resumable: skips meetings whose JSON exists
python3 planning_commission/extract_votes.py --force    # re-parse everything
python3 planning_commission/validate_votes.py           # QA; exit 0 = PASS
```

## `all_votes.csv` schema (EXACT 13 columns, same as the council table)

`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`

- **`body` = `PlanningCommission` on EVERY row** — regular AND study meetings. The
  downstream DB keys on this value, so it is constant across both meeting types.
- **`title` = `Planning Commission`** on every row (the regular-vs-study distinction
  is carried by `source`, which is the markdown path with its slug).
- **`source`** = path under `planning_commission/` (e.g.
  `minutes/2024/2024-06-10/2024-06-12_planning-commission-meeting.md`).
- Named roll calls emit one row per member; **tally-only / voice votes emit a single
  summary row** with `member` and `vote` blank.

## Source format (what the minutes look like)

A recorded motion in a regular meeting reads:

```
Motion:  Commissioner Porter motioned to approve C-23-2022, subject to the seven
         staff alternatives.
         Commissioner Woodruff seconded the motion.
Vote: Commissioner Porter             Yes
      Commissioner Lovato             Yes
      ...
      Chair Fuller                    Yes
Unanimously – C-23-2022 – Approved
```

### Format variation absorbed by the parser
- **Motion verbs**: `motioned to …`, `moved to …`, `made a motion to …`,
  `moved for approval of …`, and the `that`-form `motioned that ZT-5-2024 be approved`.
- **Member naming**: motions and roll calls use **role + last name** (`Commissioner
  Porter`, `Chair Fuller`, `Vice Chairperson Lovato`). Attendance **headers** give
  full first+last names. Last names are unique across the 2020–2026 PC, so the parser
  maps last name → canonical full name (`LASTNAME_TO_FULL`). Typos folded:
  `Woodruf→Woodruff`, `Levato→Lovato`, `Martel→Martell Winters`.
- **Vote token**: `Yes`/`No` (mapped Aye/Nay), plus `Absent`, `Abstain`, `Recuse`,
  and `N/A`/`Conflict` (→ Recuse). The first voter often shares the line with the
  `Vote:`/`VOTE:`/`Roll Call Vote:` label (`VOTE:  Commissioner McEwen  Yes`) — the
  roll-call regex consumes that optional label.
- **Result line** forms (all handled): `Unanimously – C-23-2022 – Approved`,
  `Unanimous– ZT-3-2020– Approved`, `UNANIMOUS—Z-10-2025—APPROVED`,
  `Majority – GPZ-3-2020 – Continued`, `APPROVE GPZ-4-2024 – FAIL`,
  `CONTINUE GPZ-4-2024 to July 10, 2024 meeting – FAIL`.
- **Form-feed page breaks** (`\x0c`) are emitted by pdftotext and sometimes glue to
  the start of a real roll-call line (`\x0cCommissioner Woodruff No`). The parser
  strips `\f` at load time so those votes are not lost, and skips page-footer noise
  (`Planning Commission Public Hearing Minutes … Page 22 of 29`) **inside** a
  roll-call list that straddles a page boundary.

### Tally-only / voice votes (CARDINAL RULE — never fabricate)
Some items record no per-member roll call — only a narrative verdict:
`A voice vote was taken, and all five Commissioners were in favor`, `Motion passed
unanimously.`, `Unanimously – Z-9-2025 – Approved`, `MAJORITY—Z-9-2025—APPROVED`,
`all members voted in favor`. These are recorded with `names_recorded:false`,
**empty member lists** (we never attribute individual votes), and a single summary row
in `all_votes.csv`. The **count** in the `A:N` tally is filled, in priority order:
1. an explicit number in the wording (`all five Commissioners` → `5:0`);
2. otherwise, when the minutes **explicitly say the vote was unanimous / all in
   favor**, `A` = the number of commissioners present that meeting (a count
   inference — *not* a per-member guess — since "unanimous" means everyone present
   voted the same way); `N` = 0;
3. otherwise `0:0` (e.g. a bare `MAJORITY … APPROVED` where the split is genuinely
   unrecorded — 2 such rows in the corpus).

A motion that **failed for lack of a second** (`This motion failed due to a lack of a
second.`) never came to a vote and is **skipped**, not recorded as `0:0`.

## Parser heuristics (`extract_votes.py`)

1. Find each motion via `RE_MOVED` (`<role> <last> motioned/moved/made a motion
   to|for|that …`); `motion_no` assigned in document order.
2. For each motion, search a window bounded by the next motion (so a vote is never
   stolen from the following item):
   - **Seconder** via `RE_SECOND`.
   - **Roll call**: the first per-member `Yes/No` line begins the block, parsed by
     `parse_rollcall_block` (tolerates blanks, page-footer noise, `N/A`/`Conflict`),
     ending at the result line.
   - else **voice/tally** (`RE_VOICE`) or a nearby outcome word → tally-only.
   - else (no recorded outcome near the motion — e.g. a superseded substitute) the
     candidate is **skipped**, not counted.

## RECOMMENDATION vs FINAL ACTION (encoded in `result`)

WVC PC **forwards recommendations to the City Council** on legislative land-use items
and takes **final action** on quasi-judicial/administrative items. The split is
encoded in `result` exactly as required (the DB keys on the `recommend` substring and
on `positive`/`negative`):

| Item kind | `result` string |
|---|---|
| recommendation, approved | `Positive recommendation A:N` |
| recommendation, denied/failed | `Negative recommendation A:N` |
| final action, approved | `A:N Approved (Final Action)` |
| final action, denied/failed | `A:N Denied (Final Action)` |
| procedural / appointment | `A:N Pass` / `A:N Fail` |
| any item continued/tabled/withdrawn | `A:N Pass\|Fail (Continued\|Tabled\|Withdrawn)` |

`A:N` = ayes:nays from the per-member roll call (or the parsed voice-vote count).
**The per-member roll call governs pass/fail** even if the printed result word
disagrees (see source typos below).

### The recommendation-vs-final RULE (by case-number prefix)
The PC minutes almost never write "recommend to City Council" in the motion clause
(the motion just says "approve X-N-N"), so classification keys off the **case-number
prefix** (which always appears in the motion text, the result line, or the agenda
heading — the parser searches all three). Empirically only the legislative items
reference the City Council in the minutes ("…makes a recommendation to the City
Council"; street vacations confirmed to "go to City Council"); CUPs / site plans /
subdivision plats are PC final actions.

- **Recommendation** (legislative → Council): `Z` (rezone), `ZT` (zone-text/ordinance
  amendment), `GP` (general plan), `GPZ` (general plan + rezone), `S`/`SD`
  (subdivision), `SV` (street vacation), `SA` (subdivision/plat amendment), `PUD`
  (planned unit development).
- **Final action** (PC decides): `C`/`CA` (conditional use & amendments), `SMI` (site
  plan / preliminary site approval), `M` (code exception), `AD`/`PR`/`ZPR`/`ZSMI`/`B`
  (misc administrative).
- Items with **no case number** (rare) fall back to keywords: general-plan / rezone /
  zone-text / vacate / annex → recommendation; conditional-use / site-plan /
  subdivision / plat → final.

> Note on the spec's hint: the task brief listed "subdivisions → recommendation" and
> "SMI → final action". `SMI` in this corpus is itself a *subdivision/site* preliminary
> ("preliminary approval for …"), so the two hints overlap. We honor the explicit
> `SMI → final` and keep plain subdivisions (`S`/`SD`) and PUDs as recommendations,
> matching the legislative-vs-administrative reality of WVC PC authority. The
> `action_category` field in each JSON record makes the call auditable per motion.

`motion_type` (CSV column) is the descriptive land-use family — `Conditional Use`,
`Rezone`, `General Plan & Rezone`, `Zone Text Amendment`, `General Plan Amendment`,
`Subdivision`, `Subdivision Amendment`, `Street Vacation`, `Site Plan`, `Planned Unit
Development`, `Code Exception`, `Other Land-Use`, `Procedural/Administrative`,
`Appointment`, `Other`. Recommendation-vs-final lives in `result`, not `motion_type`.

## Roster (`roster.csv`)

Reconstructed from the attendance headers (`WEST VALLEY CITY PLANNING COMMISSION
MEMBERS` / `THE FOLLOWING MEMBERS WERE PRESENT:`) **unioned with anyone who cast a
recorded roll-call vote** (a vote is stronger evidence of presence than the header —
e.g. the 2024-07-03 study minutes omit Drozdek from the header but she voted, so her
range starts there). `n_meetings` = meetings where the commissioner was present.

| Last name | Full name | First seen → last seen |
|---|---|---|
| Fuller   | Brent Fuller    | 2020-01 → 2024-06 |
| Meaders  | Clover Meaders  | 2020-01 → 2022-05 |
| McEwen   | David McEwen    | 2020-01 → 2024-08 |
| Winters  | Martell Winters | 2020-01 → 2026-05 |
| Wood     | Cindy Wood      | 2020-01 → 2025-01 |
| Lovato   | Mathew Lovato   | 2020-01 → 2026-04 |
| Porter   | Darrick Porter  | 2020-01 → 2026-05 |
| Woodruff | Harold Woodruff | 2020-01 → 2026-05 |
| Layton   | Renee Layton    | 2024-01 → 2025-07 |
| Drozdek  | Nancy Drozdek   | 2024-07 → 2026-05 |
| Durfee   | Rob Durfee      | 2025-01 → 2026-04 |
| Matagi   | Pauline Matagi  | 2025-03 → 2026-05 |
| Ramirez  | Adrianne Ramirez| 2025-12 → 2026-05 |

13 distinct commissioners; the PC seats ~7 at a time. (Note: a "Cindy Wood" also sits
on the City Council District 4 from 2024 — plausibly the same person moving from PC to
Council; treat as a name to disambiguate by body when joining datasets.)

### Appointment cross-check (`meeting_minutes/all_votes.csv`)
The City Council appoints PC members, but the council `all_votes.csv` `Appointment`
rows (71) cover **Council seats, Mayor Pro Tem, and RDA/MBA chairs** — PC appointments
are handled on consent agendas and are not isolated as separate roll-call motions
there, so they do not surface as `Planning Commission` Appointment rows. They are
confirmed instead in the **council minutes text** ("…recommended for appointment as a
member of the Planning Commission"): every PC surname above (Drozdek, Durfee, Matagi,
Ramirez, Layton, Fuller, …) appears in those council minute files, cross-validating
the roster.

## Validation (`validate_votes.py` — independent re-read, exit 0 = PASS)

- 0 off-roster names, 0 out-of-range votes (every roll-call name is on the roster and
  within its attendance range).
- JSON member-vote rows reconcile **1:1** with `all_votes.csv` (2,991 = 2,991).
- result strings well-formed; recommendation strings carry `recommendation` +
  positive/negative, final-action strings never do.
- **Tally-vs-source mismatches (source typos, NOT parser bugs, NOT fabricated)** — the
  printed result word disagrees with the per-member roll call; the roll call is kept:
  - **2023-09-13** m5 (C-21-2023): printed `Unanimously – Approved`, roll call **4:1**
    (McEwen No).
  - **2023-09-13** m7 (Meeting Minutes): printed `Unanimously – Approved`, roll call
    **4:1** (McEwen No).
  - **2024-09-11** m4 (C-15-2024): printed `UNANIMOUS … CONTINUED`, roll call **6:1**.

## Coverage / honesty

- **264 meetings parsed, 0 unparsed** (134 regular + 130 study) — measured 2026-07-31.
- **604 motions**: **483 named roll-calls** (2,991 member-vote rows) + **121 tally-only
  voice votes** (recorded with `names_recorded:false`, no guessed members).
- **282 recommendations · 247 final actions · 75 procedural/appointment.**
- **57 contested motions** (≥1 Nay/Abstain/Recuse) — the analytical signal.
- An audit of all 658 "X motioned/moved" statements in the source confirms the 52
  not turned into vote rows are all legitimate skips (4 failed-for-lack-of-a-second +
  ~47 superseded substitute motions / statements embedded in discussion); **0**
  skipped statements have an unrecorded nearby vote.
- **129 study meetings carry no recorded votes** — expected (study sessions are
  discussion; the action votes happen at the regular meeting two days later). The few
  study-meeting votes that exist are chair elections / minutes approvals.
- A motion with **no recorded outcome** near it (superseded substitute motions) is
  intentionally skipped. Consent-style multi-item motions are one row.

## OnBase WRONG-DOCUMENT slots (duplicate-ingest defect, fixed 2026-07-31)

OnBase publishes a minutes anchor for two PC meetings but serves **a different
meeting's PDF** under the slot (a city mis-upload, re-verified live 2026-07-31).
Ingesting them had created **phantom meetings that double-counted another
meeting's motions**:

| Phantom date (removed) | OnBase meetingId | PDF actually served | Evidence the meeting itself was REAL |
|---|---|---|---|
| 2024-07-10 (Regular)      | 7889 | the **2024-04-10** PC minutes (in-body header "April 10, 2024"; approves the March 6/13 minutes) | its minutes were approved at the 2024-08-28 meeting ("Minutes from July 10, 2024, August 7, 2024…"); the 2024-08-14 agenda item reads "continued from July 10, 2024" |
| 2025-04-16 (Study)        | 8228 | the **2025-04-23** PC public-hearing minutes (in-body "MET IN REGULAR SESSION ON WEDNESDAY, APRIL 23, 2025"; every page footer says April 23) | its minutes were approved at the 2025-05-14 meeting ("the Minutes of the Study Meeting held April 16, 2025, and the Public Hearing held April 23, 2025") |

Both meetings HAPPENED — only their minutes are missing — so each is ledgered in
`minutes_unrecovered.csv` rather than silently dropped, and `fetch_new.py`'s
`WRONG_DOC_SLOTS` quarantine keeps a refresh from re-creating the phantoms.
Removed with the phantoms: 10 motions / 37 `all_votes.csv` rows (26 + 11);
the surviving 2024-04-10 and 2025-04-23 records are untouched.

---
*Doc correction 2026-07-31: counts above re-measured after the duplicate-ingest
removal (the 2026-07-02 audit paragraph about 658 "motioned/moved" statements
describes the corpus as of that audit and is left as written).*

*Doc correction 2026-07-02 (audit `_audits/2026-07-02/report.md`, Phase 1.8): the layout
line claiming `raw/` holds the original PDFs was false — raw/ is empty (PDFs not
retained); sources remain re-fetchable via `minutes_index.csv` `source_url`
(spot-verified live 2026-07-02).*
