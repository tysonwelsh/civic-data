# weber_county / ordinances — adopted-instruments register + code catalog

Two things live here: (1) the **adopted-instruments register** — the adopted-ordinance /
resolution table Weber County itself never published, derived from the Commission minutes'
named-roll motions; and (2) a catalog of the adopted-code sources plus a corpus-derived
land-use **case-key index**.

## `adopted_instruments.csv` + `index.csv` — the adopted-instruments register (NEW 2026-07-20)

Weber prints numbered instruments (`Resolution NN-YYYY`, `Ordinance YYYY-N`) inline with
the motion that acts on them, and the minutes name **every commissioner's roll-call vote**.
So each adopted instrument is tied to the EXACT enacting motion and its named roll call —
**every row cites its minutes** (`source_file` + `source_url`). Built by
`build_adopted_instruments.py` from `../db/staging/motion_refs.csv` (1,102 motion-anchored
instrument refs) joined to `../db/weber_county.db` motions. DERIVED + idempotent —
regenerate after `db/build_db.py`; never hand-edit.

- **`adopted_instruments.csv`** — the full working register, **807 rows** (269 ordinances +
  538 resolutions), one row per distinct instrument number. Columns: `instrument_type`,
  `instrument_number`, `adoption_date`, `adopting_motion_no`, `motion_id` (the
  `weber_county.db` motion_id of the adopting motion; blank when not unique), `outcome`
  (Pass/Fail of that motion), `names_recorded` (named-roll availability — **1 for all 269
  ordinances**), `reading_stage` (First/Second/Final Reading, where printed), `n_readings`,
  `prior_readings` (earlier readings as `date#motion_no(stage)`), `match_confidence`,
  `motion_resolution` (`unique`/`ambiguous`), `title` (adopting-motion verbatim), plus the
  two citations.
- **`index.csv`** — the **ordinance-class subset (269 rows)** in the schema the repo-root
  federation loader consumes (`scripts/build_search_layer.py::load_ordinances`, non-city
  path): a DIRECT county-db `motion_id` (the loader applies the fed_index offset) so Weber's
  ordinances federate into `cities.db` `ordinance` **with enacting-vote linkage**. Resolutions
  stay register-only. `path`/`text_path` are blank (no per-ordinance PDF — the **minutes are
  the source**, cited by `source_url`); `result='adopted'`.

**Selecting the adopting motion + honest ambiguity.** An instrument can appear across
several motions (readings). The adopting motion is the one maximizing (passed, reading-stage
rank, date, motion_no); earlier appearances go in `prior_readings`. The link is `unique`
only when that winner is not tied with another motion on the SAME date at the SAME
(pass, stage) — otherwise `ambiguous` and the federated `motion_id` is **left blank** (never
force an ambiguous join; the loader then stores it `unlinked`).

**PROCEDURAL motions are not candidates (2026-07-29).** Weber prints the number in its
ALL-CAPS section header ("7.H.4-… – ORDINANCE 2019-13"), so a header-anchored reference
lands on whichever motion follows the header — routinely "moved to adjourn the public
meeting and reconvene the public hearing". Left in the pool that procedural row either WON
the tie-break (highest motion_no on the day) or manufactured a spurious tie that blanked an
otherwise-unique link. `PROCEDURAL_RE` now excludes adjourn / recess / reconvene / convene
motions from candidacy. Effects: **50 ordinances recovered a unique link** to a motion that
cites their own number verbatim, and **2019-13 became honestly `unlinked`** — its real
adopting motion ("Commissioner Harvey moved to adopt Ordinance 2019-13 amending the Weber
County Zoning Map to overlay the Solar Overlay Zone…", 2019-07-30, aye/aye/aye) was IN the
minutes but had never been extracted into the vote layer, so there was no motion row to
point at. An instrument whose every reference is procedural keeps its row (date +
`source_url` + a blank `title`, `match_confidence=unlinked`) rather than being dropped or
mislinked.

**2019-13 RESOLVED (2026-07-31).** The missing motion was an `extract_votes.py` bug, not an
ordinance-layer gap: when the roll-call scan stopped at the NEXT motion it resumed at
`j + 1` and stepped over that motion, so any motion printed directly beneath a retracted /
unvoted motion was lost — here the retracted "moved to adjourn the public meeting and
reconvene the public hearing" that sits just above the Solar Overlay adoption. (The
previously-suspected cause — the mid-roll "Commissioner Harvey amended his motion to include
that" — was NOT the problem; the extractor scans past interleaved prose fine.) 2019-13 now
carries a `unique` / `high` link to its own adopting motion with the full aye/aye/aye roll.

**DIED-MOTION LINKS CORRECTED (2026-07-31, second pass).** Two ordinances were linked
`unique`/`high` to a motion that had **died for lack of a second** — the extractor had let
the died motion swallow the SUBSTITUTE motion's roll call (see `../CLAUDE.md`, the
died-for-lack-of-a-second repair). **2018-14** pointed at "Commissioner Ebert moved to adopt
Ordinance 2018-14 approving the C-2 zoning… Motion died for lack of a second" and now points
at the motion that actually adopted it (Chair Harvey, C-1 Zone, 2018-09-11 #9, 2-1);
**2018-23** pointed at Chair Harvey's died $1,250 trails-fee motion and now points at
Commissioner Jenkins's adopted $1,350 motion (2018-12-18 #15). **Resolution 29-2018**
entered the register for the first time (its adopting motion had never been extracted).
2018-15 stays honestly `ambiguous` — its real adopting motion (2018-09-11 #11) ties on the
same date with the Resolution 46-2018 motion that picks "2018-15" off the section header.

Link rates (2026-07-31, after the died-motion pass): **248 / 277 ordinances (89.5%)** carry a
unique enacting-motion link; **29** are honestly unlinked/ambiguous (two same-date/same-stage
motions, or a header-only reference — the register keeps the row and records
`prior_readings`, but withholds the link). **277 of 277** now have a named roll call
available on the adopting motion. Register-wide unique rate: 733 / 846 (86.6%). Ordinances
**2021-13 / 2021-14 / 2021-15** moved from adoption_date 2021-06-01 to **2021-05-11** in the
same pass — the 2021-06-01 meeting was a phantom created by a county mis-post (see
`../CLAUDE.md`), which had also given them a spurious extra "reading". (Superseded: 248/277
89.5% and 731/845 86.5% earlier on 2026-07-31; 247/277 89.2% and 729/844 86.4% on
2026-07-29; 193/269 71.7% and 589/807 73.0% before the 2026-07-26 OCR backfill.)

## `case_keys.csv` — land-use applications mined from the PC/BOA corpus

The Weber County **planning-commission** minutes reference land-use matters by **case file
number**, not by adopted-ordinance number. 169 distinct case keys mined from the 166-minute
land-use corpus (CUP 67 / ZMA 45 / ZTA 34 / DR 23) with first/last-seen dates, mention
counts, and hearing bodies. Its `enacting_ordinance` / `enacting_motion` / `vote_linkage`
columns stay **`deferred`**: adopted ordinance numbers are assigned by the **Commission**
(now catalogued above), not the planning commissions, and the PC case keys do not carry the
Commission ordinance number — joining the two is a future land-use-promotion task.

## `code_sources.csv` — the adopted code (dual codification)

Weber County adopts a **dual codification** — the same Code of Ordinances published on two
official hosts: **Municode Library**
(https://library.municode.com/ut/weber_county/codes/code_of_ordinances) and **Municipal Code
Online** (https://weber.municipalcodeonline.com/). Organized as **Part I** (general county
code, Titles 1–44) + **Part II — the "Uniform Land Use Code of Weber County, Utah" (LUC)**,
the growth-relevant zoning/land-use title the PC and BOA corpus applies. Both hosts are JS
single-page apps; the Municipal Code Online printable Land Use Code view is the best
candidate for a FUTURE full-text FTS ingestion of the code itself (not done in this pass).
(This file was `index.csv` before the 2026-07-20 register build repurposed `index.csv` as
the federation file.)

Verified live 2026-07-20.
