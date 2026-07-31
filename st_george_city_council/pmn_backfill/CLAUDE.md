# pmn_backfill — St. George PMN cross-check & gap recovery

**Source type 4** of the `expand-city-sources` skill. A **separate, additive** dataset that
cross-checks the audited minutes layer against Utah Public Notice (PMN) and recovers genuine
date-level minutes gaps. **As-of 2026-07-02.**

## Why this is a separate dataset (not merged into `meeting_minutes/`)
The `meeting_minutes/` and `planning_commission/` layers are audited and derived-from (votes,
`db/`, `weeks/`). This backfill is left as a reviewable sibling so a human can merge
deliberately; the audited layers are **never hand-edited** by this skill. If merged later,
map each row's `body`/`date` onto the corresponding minutes index — but note the recovered
docs still need the repo's markdown conversion + vote extraction before they'd participate in
`all_votes.csv` / `db/`.

## PMN body ids (verified, not guessed)
Discovered via the GET chain, since PMN ids are global not per-city:
`list/entities.html?id=3` (govType 3 = Municipality) → **St. George entity id 277** →
`list/publicBodies.html?id=277&limit=2000`.

- **City Council = body 241**
- **Planning Commission = body 242**
- (recon had assumed 241 & 242 were two *council* bodies — they are not; 242 is the PC.)

Full St. George body list (entity 277), for future sources: DTEC 2014, Airport Advisory 5003,
Ambulance Compliance 5283, Animal Shelter 4767, Art Museum 251, **Arts Commission 248**,
Board of Adjustments 243, Building Code Appeals 247, **City Council 241**, Community Education
Channel 3469, Dinosaur Discovery 250, Dog Hearing 6431, Economic Development Agency 1087,
Hillside Review 244, Historic Preservation 245, Land Use Authority 8305, Municipal Building
Authority 1088, **Planning Commission 242**, Police Unclaimed Property 8349, Procurement 7337,
Public Arts 249, Recycling Review 5761, Redevelopment Agency 1086, Shade Tree 252, Sign
Review 246, Snow Canyon Compact 254, St. George Housing Authority 2356, Water & Energy 253.

## Crawl mechanics (GET-only, polite)
- The notices *list* claims "past 6 months only," and historical *search* is POST/CSRF
  (can't do politely). Escape hatch: `list/notices.html?id=<body>&page=<high N>` is
  **cumulative** — one GET with `page=300` returned each body's full history.
- Parse attachment labels from the list HTML: `(Meeting Minutes)`, `(Public Information
  Handout)` (= agendas/packets), `(Audio Recording)`, `(Other)`. No literal `(Agenda)` label.
- Attachments are opaque `/pmn/files/<FILE_ID>.<ext>`; notice pages
  `/pmn/sitemap/notice/<NOTICE_ID>.html`. Both captured per row in `index.csv`.
- Parser: `scratchpad/pmn/parse.py` (regex over `<tr>` rows → notice_id, title, event date,
  attachment {file_id, label, name}). Index builder: `scratchpad/pmn/build_index.py`.

## Method
1. Set-difference by **meeting DATE** (±3 days), repo minutes dates vs PMN Meeting-Minutes
   dates, per body, 2020+.
2. Every candidate gap **content-verified** before inclusion (header body-name + date; MOTION/
   VOTE presence). This caught 3 non-gaps: an Arts-Commission mis-post, a false-positive whose
   file was a different (already-held) meeting, and a byte-dup. It also caught the 2023-05-23
   "minutes" that is really an agenda packet.
3. Fetch via `../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --now
   2026-07-02T00:00:00Z`; extract `pdftotext -layout` (docx → `textutil`); screen with
   `audit-city-data/scripts/screen_corpus.py` (clean).

## Files
- `raw/` — 20 originals verbatim + `_fetch_log.jsonl` (sha256 provenance).
- `text/` — extraction sidecars (for screening; not the canonical store).
- `index.csv` — schema `date,year,title,slug,body,path,source,source_url,notice_url,
  pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method,doc_type`. `source=pmn`,
  `format=text`. `body` ∈ council/planning_commission; `doc_type` ∈ minutes/agenda_packet.
- `coverage.md` — **primary deliverable**: per-year repo-vs-PMN-vs-recovered table.
- `AVAILABILITY.md` — what was checked, what's unavailable, what was excluded and why.

## Caveats
- Cross-check is PMN-directional (recovers PMN minutes absent from repo). Where the repo
  exceeds PMN (e.g. PC 2024), that's an expected superset, not a defect.
- 2023-05-23 PC minutes are genuinely unpublished on PMN (only an agenda packet) — retained as
  `doc_type=agenda_packet`, not counted as a minutes recovery.
- Recovered docs are raw+text only; they are **not** yet in `all_votes.csv`/`db/`/`weeks/`.

## 2026-07-17 — crosscheck flag verification (18 → 14)

Verified all 18 `crosscheck_flags.csv` flags (all agenda_only_gap — no minutes/count flags).
4 new exceptions appended; re-run: **14 flags** (all agenda_only_gap; 6 suppressed, 7
pending-adoption). St. George is a Thursday city; council meets 1st/3rd Thursday, PC Tuesday.

**Exceptions (4) — "Meeting Rescheduled" non-meeting notices:** the noticed date is a
schedule-change announcement, and the moved meeting is already in the repo:
- `2020-07-02 / 241` → moved to 2020-07-09 (held; July-4 holiday week).
- `2022-07-07 / 241` → moved to 2022-07-14 (held; holiday week).
- `2023-08-10 / 241` → surrounding Aug-2023 council meetings held (08-03/17/24/31).
- `2025-11-11 / 242` → PC moved to 2025-11-18 (held; Veterans Day).

**Recovery leads (14 agenda-grade — reported, NOT ingested; PMN has agenda only, matching
this dataset's "recovers work/joint meetings absent from the city site" pattern):**
- Council regular/special meetings the Revize archive missed: 2020-10-29 (5th Thu), 2021-01-07
  (1st-Thu regular — repo has 01-21 not 01-07), 2024-10-10, 2025-11-01 (a Saturday — verify),
  2025-11-27 (Thanksgiving — implausible as a meeting; flag for reviewer, likely a canvass or
  mis-dated notice).
- PC meetings the repo lacks: 2020-03-10, 2020-05-12, 2020-05-26 (sparse early-2020 PC),
  2022-09-27, 2022-11-15, 2022-11-22, 2023-09-12, 2026-03-10; plus 2023-05-04 "Joint Work
  Meeting of the Planning Commission and City Council" (a real distinct joint session).
Note: the known 2025-10-09 wrong-file work meeting did NOT flag (correctly).

**Hardening candidate:** "Meeting Rescheduled" / "Regular Meeting Rescheduled" is a recurring
non-meeting notice family (st_george ×4) not gated by `RE_NOT_MEETING`. These carry no minutes
attachment and the moved meeting is separately noticed. Consider adding "rescheduled" (when the
title has no minutes attachment) to `RE_NOT_MEETING` — but keep the draper-specials caution:
gate strictly on "rescheduled"/"cancelled" wording, never on the presence of "meeting".

## 2026-07-17 wave2 — the 14 agenda-grade leads worked to zero

All 14 remaining `agenda_only_gap` flags resolved. Every notice body was fetched and
verified in-body (PMN event-date fields lie); the city Revize archive (2022+) and PMN were
probed for real minutes. **crosscheck re-run: 0 flags** (5 suppressed by ledger, 7
pending-adoption). No minutes were recoverable, so **no votes/minutes were added** and the
db/weeks/referral layers are unchanged.

**2 IMPLAUSIBLE dates — both non-meetings (→ pmn_exceptions.csv):**
- `2025-11-01 / 241` (Saturday) → **wrong_date metadata error.** PMN event-date field =
  "November 1, 2025 04:00 PM" but the notice text reads "will hold a work meeting … on
  **Thursday, November 13, 2025**." The real event is the 2025-11-13 council work meeting;
  no meeting on 11-01.
- `2025-11-27 / 241` (Thanksgiving) → **cancellation.** Notice body: "the City Council
  meeting … scheduled for Thursday, November 27, 2025 **has been canceled**." No meeting held.

**1 already-recorded false gap (→ pmn_exceptions.csv):**
- `2023-05-04 / 242` "Joint Work Meeting of the PC and City Council" was filed by PMN under
  the PC body; the minutes are **already in the repo on the council side** (2023-05-04 City
  Council Work Meeting, Revize `2023.05.04 Minutes Work.pdf`). Not a PC-layer gap.

**11 genuine gaps, dead on every channel (→ each dataset's minutes_unrecovered.csv):**
each notice is a real "will hold a meeting" agenda whose in-body date matches the flag, but
no minutes exist on Revize or PMN. Council (3): 2020-10-29, 2021-01-07, 2024-10-10 (the last
has agenda + 2 audio recordings on Revize — ASR is a future option, minutes never posted).
PC (8): 2020-03-10, 2020-05-12, 2020-05-26, 2022-09-27, 2022-11-15, 2022-11-22, 2023-09-12,
2026-03-10 (agenda + packet on Revize, minutes never posted though the series is current
through 06-23-2026). Pre-2022 dates are simply not archived on Revize (born-digital 2024+);
their only PMN notice is agenda-only.

Adding these 11 to `minutes_unrecovered.csv` also removes them from future crosscheck flags
(the script drops any `agenda_only_gap` whose date is logged unrecovered) — they remain
documented, honest gaps, not live leads.
