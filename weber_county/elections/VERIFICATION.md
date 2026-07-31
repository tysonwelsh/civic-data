# weber_county/elections — VERIFICATION

Built 2026-07-20. Canonical county-canvass module per the salt_lake_county model.
Regenerate + re-check with:

```
python3 normalize_weber.py      # raw/ + ev_api/ -> weber_results_long.csv + reconciliation.csv
python3 build_elections.py      # long -> election_results_by_contest.csv
python3 verify_elections.py     # full reconciliation ledger (exits nonzero on any unexplained mismatch)
```

Latest run: **0 unexplained mismatches**; 106 expected-suppressed shortfalls
(see "Suppression", below); the 2018 CSV-vintage delta is DOCUMENTED (below).

## Sources and containment

- `sources.csv` — **every result file discovered on the county's sites, 87 rows,
  zero unrecorded**: 81 Wix files (hash-named; labels captured from both the
  `electionsresults` and `copy-of-historical-election-results` pages, byte
  sizes + sha256, body-verified identity) + 6 Enhanced Voting portal elections.
  Roles: 47 normalized, 3 verification-crosscheck, 36 catalogued-only, 1 dead
  link. Raw files are RETAINED in `raw/` (the Wix hash URLs are fragile and no
  external mirror exists); EV JSON harvest retained in `ev_api/`.
- Label vs body mismatches found by reading bodies (all recorded in
  `sources.csv` notes): the "2019 Primary" and "2017 Countywide Precinct
  Report" labels mislink to other files; the "2021 Primary" label says
  "Aug. 20, 2020" over a 2021 body; the 2018 precinct CSV is labeled ".pdf";
  the historical page labels the 2010 primary "2016 Primary"; one historical
  2014-SOVC link is an empty document stream (dead).

## Era / format ledger

| Era | Files | Grain | Parser |
|---|---|---|---|
| GEMS "Election Summary Report" native print (Diebold/Premier), 2007–2017 | odd-year municipal g+p 2007/11/13/15/17; 2008/2012/2014 generals; 2013+2017 specials; 2015p/16p | contest | `parse_p3` (pdfplumber baseline-clustered, label-anchored column split) |
| GEMS web re-print ("GEMS ELECTION RESULTS", printed 4/14/2016) | 2006, 2010 generals; 2008 primary/WSP; 2010 primary | contest | `parse_p3` + `clean_p3_line` (URL/banner strip) |
| GEMS "Statement of Votes Cast" precinct grids | 2008g 931pp, 2010g 1092pp, 2012g 810pp + 2012p 264pp, 2014g 756pp + 2014p 51pp, 2016g 833pp + 2016p 102pp, 2013 special 28pp, 2007 primary pp2–11, 2015 Prop-1 4pp | precinct×method | **retained + catalogued, NOT normalized** (deferred) |
| Image-only scans | 1994/1996/1998/2002/2004 files, 2004 precinct report, 2017 Pleasant View recount | — | catalogued only |
| Electionware "Summary Results Report", 2018–2023 | 2018 g+p, 2019 (per-jurisdiction sections), 2020 g+p, 2021 g+p, 2022p, 2023 per-city primaries | contest | `parse_p2` (2018 By-Mail/In-Person columns present, Total column parsed) |
| Electionware precinct-page canvasses, 2020–2025 | 2020g 2277pp, 2022p 428pp, 2022g 865pp, 2023 bond 194pp, 2023 per-city primary precinct files, 2025g 175pp (+OVC files) | precinct | `parse_p1` (handles `Suppressed` pages and `29OV03:X`-style split precincts) |
| 2018 "Full Precinct Report" CSV | 2018 general | precinct | `parse_p4` (band layout) |
| Enhanced Voting portal JSON, 2024–2026 | 2024 general (+2 primaries catalogued), 2025 municipal primary + general, 2026 primary | precinct + electionwide summary | `parse_p5` (`ev_api/` harvest) |
| Image-only signed Board-of-Canvassers certifications | 2022 general summary, 2023 bond summary | contest (certified) | `certified_totals_transcribed.csv` — tesseract OCR, **every digit re-read visually from the 300-dpi page renders** (`ocr/*.txt` retained; renders regenerable via pymupdf) |

## Suppression (cardinal: suppressed cells stay suppressed)

Weber suppresses precincts with <15 voters ("*Precincts with less than 15
voters will be suppressed to maintain their right to a secret ballot" — site
text). Suppressed pages print candidate names with EMPTY vote cells; the long
file carries them as `suppressed=True, votes=''` (451 cells; EV null
breakdowns likewise). **Certified election-wide totals INCLUDE the suppressed
precincts' votes**, so precinct-grain sums systematically undercount. The
derived `election_results_by_contest.csv` therefore takes candidate votes from
the official contest-grain summary rows wherever the county published one
(official-summary primacy), with `n_precincts` from the precinct grain. No
per-precinct value is ever imputed.

## Reconciliation results (verify_elections.py)

- **A. Internal** — 1,274 checks of parsed candidate sums vs each precinct
  report's own printed "Total Votes Cast" and each EV item's electionwide
  summary: **0 unexplained** (17 expected-suppressed shortfalls).
- **B. Contest-grain** — 290 printed "Total Votes" cells vs parsed sums across
  every GEMS/Electionware summary in the manifest: **0 mismatches**.
- **C. Cross-source** (independent documents):
  - 2023 municipal primary: 4 cities' precinct files vs their official
    summary PDFs — 40 cells, all exact.
  - 2025 municipal general: precinct canvass vs certified summary PDF (100
    cells) and vs EV portal (99 cells) — exact up to expected suppression;
    the separate OVC precinct PDF matches the county file exactly (13 cells).
  - 2025 OVC primary: official OVC PDF vs EV portal — exact up to expected
    suppression; the PDF truncates one name ("CHRISTOPHER CHARLES" for
    CHRISTOPHER CHARLES CALDWELL — EV, canonical here, carries the full name).
  - County contests: 2020 general and 2022 primary precinct grain vs their
    certified summaries; 2022 general + 2023 bond precinct grain vs the
    vision-verified transcriptions; 2024 general + 2026 primary EV grain vs
    the official canvass summary PDFs — all exact up to expected suppression.
  - **2018 general (DOCUMENTED vintage delta)**: the precinct CSV is
    internally consistent (its own "Totals" rows equal our sums exactly) but
    is an earlier official cut than the "Tuesday November 20th Final" summary
    — uniformly +13..+31 per contest there. The derived layer uses the Final
    summary; the CSV remains the only precinct grain.
- **External**: Ogden's audited `election_results/ogden_races.csv` winners
  (read-only) — **12 of 12 matchable winners agree with identical vote
  counts** (2019 g, 2021 g, 2023 primary, 2025 g). The 4 non-matchable races
  are all 2023 municipal GENERAL — exactly the county-publication gap below.

## Honest gaps (county-publication level — verified, not parse failures)

1. **2009 municipal cycle: absent from the county site entirely** (no general,
   no primary) — the only missing odd year between 2007 and 2025.
2. **2013 municipal primary (Aug 2013): not published** (site has only the
   2013 general + the June special).
3. **2019 municipal primary: not published** — the site's link is a mislink to
   the 2019 general report (the Ogden 2019 mayoral primary has no county
   report on the site).
4. **2023 municipal general: the county published a bond-only canvass** and
   printed "For municipal results visit the municipality's website". Not on
   the EV portal either (probed exhaustively). Ogden's audited city-published
   races cover Ogden; other cities' 2023 generals are outside this module's
   sources.
5. **No precinct grain before 2018** for municipal cycles (2017 "precinct"
   label mislinks to the summary), and none for 2019 g / 2021 g+p (summary
   reports only).
6. 2007 municipal primary is Ogden-only (body-verified); its SOVC pages and
   all GEMS SOVC precinct grids are retained but unparsed (deferred — see
   sources.csv `catalogued` rows).
7. 2008/2010/2012/2014 primaries + 2008 Western States Primary + 2020/2024
   presidential + 2024 REP primaries: no county-office contests — catalogued
   only. 2017 special (a Prop 1 for an unidentified 8-precinct district) and
   the image-only 2017 Pleasant View recount: catalogued only.
8. EV portal marks 2025/2026 elections `isOfficialResults:false` even after
   canvass; every EV number used is cross-checked against an official county
   PDF (2024, 2026, 2025 general, 2025 OVC primary). For the 2025 municipal
   primary EV is the ONLY published channel for 11 of 12 cities (the county
   site carries only the OVC files) — flagged, cross-checked where possible.

## Coverage (long file: 11,416 rows, 451 suppressed cells, 2006–2026)

| Election | rows | precincts | suppressed |
|---|---|---|---|
| 2006 general (county offices) | 21 | contest-grain | 0 |
| 2007 municipal g/p | 124 / 14 | contest-grain | 0 |
| 2008–2016 even generals (county offices) | 3–22 each | contest-grain | 0 |
| 2011–2017 municipal g/p | 25–111 each | contest-grain | 0 |
| 2013 special (library bond) | 2 | contest-grain | 0 |
| 2018 general (county) / primary | 1,078 / 6 | 153 | 0 |
| 2019 municipal general | 104 | contest-grain | 0 |
| 2020 general (county) / primary | 954 / 2 | 158 | 30 |
| 2021 municipal g/p | 86 / 27 | contest-grain | 0 |
| 2022 general / primary (county) | 1,218 / 1,044 | 173 | 56 / 48 |
| 2023 general (bond) | 382 | 190 | 38 |
| 2023 municipal primary (4 cities) | 915 | 86 | 0 |
| 2024 general (county + OVC questions) | 1,494 | 179 | 64 |
| 2025 municipal general / primary | 1,199 / 1,044 | 175 / 122 | 39 / 68 |
| 2026 primary (county commission) | 1,182 | 196 | 108 |

Derived `election_results_by_contest.csv`: **1,080 contest×candidate rows, 327
contests** (municipal council/mayor for every Weber municipality, county
offices, countywide measures; `jurisdiction_slug='ogden'` on the 154 Ogden
rows — the only repo-held Weber city; conforms to
`scripts/build_cities_db.py::load_election_result`).
