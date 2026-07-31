# meeting_minutes/ — Magna City Council + CRA

Council minutes (markdown) + extracted roll-call votes for the **Magna City Council** and its
in-recess **Community Reinvestment Agency (CRA)**. Conforms to `SCHEMA_SPEC.md`.

## Contents
```
minutes/<year>/<date>_<body>_<id>.md   173 files, 2018-07-17 → 2026-05-26
raw/                                   retained source PDFs/DOCX (never deleted)
votes/<year>/*.json                    per-meeting extracted-vote records (audited docs only)
all_votes.csv                          13-col standard flat table + documented trailing 14th
                                       `provenance` column (1,033 rows, 988 motions since the
                                       2026-07-17 wave-2 COVID-cluster promotion)
motions_std.csv                        normalized layer (988 rows) for cross-city work
minutes_index.csv                      one row per file on disk (173; the 16 PMN-promoted docs
                                       are NOT here — they live in ../pmn_backfill/)
minutes_unrecovered.csv                41 meetings that exist but whose minutes don't (36 x 2017-18
                                       404 + 5 x Aug-Dec 2020 COVID council dates never published)
roster.csv                             members with district + first/last seen + seam roles
                                       (hand-curated; not auto-refreshed by the backfill merge)
extract_votes.py / validate_votes.py   extraction + conformance (audited layer)
extract_backfill_votes.py              REQUIRED after any extract_votes.py re-run — merges the
                                       16 PMN-promoted docs (provenance=pmn_minutes) or their
                                       67 motions drop out of all_votes.csv
```

## Sources & format
- **Two portals:** **CivicPlus AgendaCenter** (`magna.utah.gov`, catID 3) for **2022+**, and
  **Utah PMN body 5803** (`www.utah.gov/pmn/files/<id>.pdf` — **use the `www.` host**) for the
  township years **2018–2021**.
- **Format:** 151 `pdf-text` (born-digital) + **21 `pdf-ocr`** (2024 Apr–Dec + early-2025 signed
  image scans) + 1 `docx-text`. PMN-era text carries mild character-substitution garble
  (`quonrm`→quorum, `Hoffrnan`→Hoffman) normalized during extraction. Corpus screen: **0 outliers**.
- **⚠ CivicPlus wrong-doc slot:** the AgendaCenter sometimes serves an agenda/spreadsheet/
  correspondence file under "Minutes". Real minutes were recovered from PMN where they existed;
  wrong-docs with no real minutes were **not** fabricated into stubs.

## The vote model — narrative tally + a seam
- **Narrative-tally.** Motions record **mover + seconder + a numeric tally** ("vote was 4-0,
  unanimous in favor with Council Member Pierce absent"). A real roll call is taken but the
  printed minutes usually give only the tally — so **only 175 of 1,033 rows are named** (the
  dissenters, abstainers, absentees; recount 2026-07-16 after the pmn_backfill promotion —
  the 2026-07-12 T3.1(e) repair captured the "votING in opposition" / "nay votes from X" /
  quoted-roll dissent grammars, and 41 of 42 split-tally motions carry their named dissenters;
  the one exception has the vote word physically missing in the source render). **A blank
  member list on a unanimous motion is source style, not an extraction miss.** 10 seconded
  motions whose minutes print NO result sentence carry `result="No result recorded"` with an
  honestly-NULL db outcome (incl. the 2023-11-14 fee-schedule hearing motion whose old
  'Died (no second)' was fabricated from scanned-forward prose; was 11 until 2026-07-16, when
  the "passed BY A unanimous vote" clerk phrasing was added to the grammar and repaired
  2022-12-13 m15 — that motion's source DOES print a result). Contested motions and some
  city-era rolls carry a full named `AYE: … EXCUSED: …` block.
- **The presiding-officer seam (keys off meeting date).** Through **2025** the council elected its
  own **Chair, titled "Mayor"** (Dan Peay ≤2023, Eric Barney 2024–25) who **is one of the five and
  VOTES** (2024-12-10: "AYE: … Mayor Barney … 4-0"). From **2026** the elected executive **Mayor
  Sudbury presides but does NOT vote** (2026-05-26: `4-0` excludes him). **Max roll = 5 both eras.**
  Members are **"Council Member" in all eras.**
- **CRA rows** (`body=CRA`, **32 motions since 2026-07-16**) are the council sitting as the
  Community Reinvestment Agency board; members appear as "Board Member <Name>". Two capture
  modes: the audited in-recess/one-off CRA docs (13 motions, `provenance=minutes`) PLUS the
  **standalone CRA meeting minutes recovered from PMN body 6925 and promoted 2026-07-16**
  (19 motions across 7 dates, `provenance=pmn_minutes` — the CRA regularly met at 5:30 PM
  before the 6:00 PM council meeting as its own filed meeting; those docs were never on
  CivicPlus). An 8th recovered CRA doc (2025-11-18) is stamped "DRAFT MINUTES – UNAPPROVED"
  and stays an unpromoted `pmn_backfill/` sidecar.
- **Provenance column (14th, since 2026-07-16):** `minutes` = audited doc in `minutes/`;
  `pmn_minutes` = PMN-promoted doc merged by `extract_backfill_votes.py`, whose `source`
  paths point into `../pmn_backfill/text/`. **Run order: `extract_votes.py` then
  `extract_backfill_votes.py`.**
- **Vote values:** `Aye/Nay/Abstain/Absent`; source **"EXCUSED" → `Absent`** (verbatim word kept
  in the markdown).

## Roster (with the seam)
Steve Prokopis (D1), Megan Olsen / Eric Barney / Brint Peel (D2 over time), Michael Jensen (D3,
from 2025-11), Terry George / Trish Hull (D4), Audrey Pierce (D5). **Dan Peay** and **Eric Barney**
each served as the **voting Chair titled "Mayor."** **Mick Sudbury** was a **D3 councilmember who
voted through 2025**, then Magna's first elected **Mayor (non-voting) from 2026** — a single person
spanning the seam. Eric Ferguson served early (through mid-2019).

## Honest gaps
- **2017 + Jan–Jun 2018 council minutes (36 meetings) are 404-unrecoverable** on PMN (attachment
  purged; no Wayback) → on-disk council record begins **2018-07-17**. All 36 logged verbatim in
  `minutes_unrecovered.csv`, **never stubbed**.
- **17 indexed files carry 0 motions** — genuinely vote-free meetings (work sessions,
  presentation-only regulars, Board-of-Canvassers certification dates, ceremonial CRA schedule
  votes). Not stubs (2–43 KB real text). **Board-of-Canvassers "moved to certify" motions are
  deliberately excluded** (a distinct statutory body, not a council legislative vote).
- **3 township SPECIAL WORKSHOP council minutes recovered 2026-07-17** into `../pmn_backfill/`
  (2022-11-29, 2023-02-23, 2023-03-23; PMN body 5803 — the crosscheck engine's 3 council
  `missing_minutes` leads). Title 18/19 code-review study sessions with **no formal action** →
  `extract_backfill_votes.py` reports them as zero-motion (0 rows; `all_votes.csv` unchanged).
  They fill the coverage record without fabricating votes. See `../pmn_backfill/CLAUDE.md`.
- **4 Aug–Dec 2020 COVID-era regular council minutes recovered + PROMOTED 2026-07-17 (wave-2)**
  (2020-08-11, 2020-08-25, 2020-09-08, 2020-10-27; PMN body 5803; **16 motions**, township-era
  voting Chair-"Mayor" Peay). The 09-08/10-27 minutes existed only *embedded in the next
  meeting's approval packet* (retained verbatim; sidecar is the minutes page-range). See
  `../pmn_backfill/CLAUDE.md`.
- **5 Aug–Dec 2020 COVID-era council dates are genuine publish gaps** (2020-09-22, 2020-10-13,
  2020-11-24, 2020-12-08, 2020-12-15) — PMN posted an agenda/audio but never a minutes document
  (approval-packet chain traced through 01-12-2021). Logged in `minutes_unrecovered.csv`, never
  stubbed.
