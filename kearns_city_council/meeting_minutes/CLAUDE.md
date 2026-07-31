# meeting_minutes/ — Kearns City Council (+ CRA)

City Council minutes (markdown) + extracted votes, **plus the standalone CRA
(Community Reinvestment Agency) minutes** (`body=CRA`, PMN body 9273, promoted from
`../pmn_backfill/` 2026-07-16). Source: **Utah PMN body 5823** (council; the city site
is Cloudflare-blocked). See the root `CLAUDE.md` for the full governing-regime and
voting model; the essentials for this dataset:

## Files
- `minutes/<year>/<date>/<date>_<slug>.md` — one markdown doc per meeting, with a
  provenance header (source URL, `Format: ocr|text`, in-body date match).
- `all_votes.csv` — the standard 13 columns
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`)
  **+ a documented trailing 14th `provenance` column since 2026-07-16**
  (`minutes` = audited primary; `pmn_minutes` = doc recovered via `../pmn_backfill/`
  and promoted — currently the 2 CRA docs; read from each md's `**Provenance:**`
  front-matter line by `extract_votes.py`).
  `result`/`motion_type` are **city-verbatim**; normalized fields are in
  `motions_std.csv` (join on `source,motion_no`).
- `minutes_index.csv` — one row per doc on disk (`…,source,source_url,format`).
- `minutes_unrecovered.csv` — meetings with no minutes doc on disk. **⚠ see Coverage.**
- `raw/` — retained source files (never deleted). 120 files = 119 minutes (118 PDF +
  1 `.docx`; incl. the 2 CRA raws `minutes_2025-07-14-cra.pdf` / `minutes_2025-09-08-cra.pdf`)
  + 1 `supdocs_2026-07-13.pdf` supporting-docs packet (not minutes, correctly
  not indexed). Same-date township meetings use a type-suffixed stem
  (`minutes_2019-11-19-special.pdf`, `-boc.pdf`); `manifest.csv` carries a `raw_stem`
  column driving `convert.py` (+ a `provenance` column marking promoted docs).
- `votes/<year>/<date>/*.json` — per-meeting extractor output; `convert.py`,
  `extract_votes.py`, `validate_votes.py`, `screen_corpus.py` are the tooling.

## Counts (2026-07-16, after the CRA promotion)
119 minutes docs (117 Council-family + **2 CRA**) · **501 motions** (492 Council +
**9 CRA**) · 2018-07-09 → 2026-05-29 · format: 23 OCR + 96 born-digital text (incl.
1 `.docx`). 36 named vote rows (32 council + 4 PC); provenance: 536 rows `minutes` +
9 rows `pmn_minutes` (the CRA docs).

## Vote style — narrative tally (READ THIS)
Motions record **mover + seconder + a numeric tally** ("Vote was 5-0, unanimous in
favor"), NOT a per-member roll call. Only **dissenters/abstainers are named**;
the majority is honestly **unnamed**. `COUNCIL MEMBERS PRESENT:` gives attendance.
→ a blank `member`/`vote` on a unanimous motion is a source limit, not missing
extraction. **Exception:** some 2018-2023 township minutes print a *full named roll
call* ("Roll was called…Council Member Schaeffer 'Nay,' …Mayor Bush 'Aye'") — those
per-member Ayes/Nays are captured verbatim (`extract_votes.py` `parse_rollcall`, scoped
strictly to an explicit "Roll…called" block so it never touches the 2024+ narrative
tallies). So there are **32 named council vote rows** (22 Aye / 8 Nay / 2 Abstain) and
**5 contested council motions** (the 2019-09-09 3-2 pass, 2019-10-14 2-3 fail, the
2023-08-14 + 2026-05-11 abstains). This is why `scripts/validate_city.py`'s `f.tally`
reports partial matches — expected, benign.

## The governing-regime seam
- **Township era (files 2018-07 → 2025):** 5-member council; the Chair is styled
  "**Mayor**" ("Mayor Kelly Bush, Chair, presided") but is one of the five members —
  NOT a separate executive. Max roll = 5.
- **City era (2026 →):** an elected **Mayor who VOTES** + 4 councilmembers. Full rolls
  tally 5-0 with only 4 members → the mayor casts the 5th (Mayor Valdez). Max roll =
  5 including the mayor.

## OCR seam
22 docs are `format=ocr` (2024-era + scattered township/2025 scans). OCR is faithful;
only the source's decorative `♦♦♦`/`−−−` separators garble (cosmetic — do not treat as
corruption). Born-digital text (incl. 1 `.docx`) preserves source typos verbatim = faithful.

## Coverage — the township back-catalog was harvested (2026-07-12)
Council minutes on disk now run **2018-07-09 → 2026-05**. The original build wrongly
logged the 2017-2023 township era as "only agendas + MP3 audio (minutes genuinely
absent)"; the 2026-07-12 audit disproved that and the back-catalog was harvested from
PMN body 5823 — all 255 notices enumerated, 111 township meetings carry a
"Meeting Minutes" attachment, **85 pulled** (2018-07 → 2023; 84 `.pdf` + 1 `.docx`).
`minutes_unrecovered.csv` now holds **41 genuine gaps** with accurate reasons:
- **25 township meetings 2017-01 → 2018-06** — minutes WERE published but the PMN file
  blob is **purged** from PMN's pre-~July-2018 store (`file_id` < ~450000 → 404;
  notice link stale; not on the Internet Archive) — a file-rot gap, recoverable only if
  PMN restores those blobs.
- **7 township meetings** — only agenda + MP3 audio posted, no minutes ever published.
- **9 recent meetings** — minutes not yet approved/posted at retrieval.

## CRA — `body=CRA` (lit up 2026-07-16)
The council sits as the **Kearns Community Reinvestment Agency** board (Utah 17C;
"Board Member" roles, **Chair Kelly Bush votes** — same 5-member composition as the
council; established by Ordinance 2025-O-06, 2025-03-10). Its standalone minutes live
on **PMN body 9273**: 2 real meetings — **2025-07-14** (5 motions, all 5-0; officers,
bylaws, legal counsel, 2025 calendar, adjourn) and **2025-09-08** (4 motions, all 4-0
with Board Member Peterson excused; bylaws + code of conduct adopted, July minutes,
adjourn) — recovered via `../pmn_backfill/` and promoted into this dataset 2026-07-16
as `minutes/2025/<date>/<date>_cra-meeting.md` (`**Body:** CRA`,
`**Provenance:** pmn_minutes`). The CRA's other 5 noticed 2025 meetings were
cancellations (see `../pmn_backfill/coverage.md`). Same narrative-tally grammar as the
council ("Board Member Snow moved… vote was 5-0, unanimous in favor") → all 9 motions
are tally-only placeholders (majority honestly unnamed). ⚠ The 2025-09-08 file is
PMN-labeled "DRAFT" but its certification block states the minutes were approved
2026-05-11 — treated as the approved record. The 2025-09-08 minutes print
"with Board Member Peterson absent from the vote" — like the audited council layer's
identical grammar, the absence is not emitted as a named `Absent` row (extractor
convention; the source PDF retains it).
