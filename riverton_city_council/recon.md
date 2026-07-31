# Riverton City, Utah — Civic Data Recon

**City:** Riverton City, **Salt Lake County**, Utah (~45k pop., incorporated 1997).
**Recon date:** 2026-07-11
**Data floor:** **2020-01-01**.
**Form of government:** **six-member council form** — five district councilmembers (D1–D5)
+ a separately-elected **Mayor** who is chair of the council and chief executive. **The
Mayor does NOT vote on ordinary motions** — the Mayor "casts a vote as a member of the city
council [only] when necessary to break a tie vote among councilmembers; when voting on the
appointment or dismissal of a city manager; and when voting on whether to amend the powers
of the office of the mayor" (city's own language). → **Max ordinary council tally = 5;**
Mayor appears as presiding officer + tie-breaker only. **VERIFIED against two real roll
calls** (§1). This is the **Park City model** (mayoral tie-break stored as a vote note),
not Millcreek (mayor votes) and not Taylorsville (mayor never votes, no tie-break seen).
**Official city site:** `https://www.rivertonutah.gov/` — a **Revize** CMS (page chrome
carries `powered-by-revize`). The **meeting archive is a separate Granicus instance** (§1).

---

## 1. Council meeting minutes

### Portals — Granicus archive (primary) + Utah PMN (mirror/fallback)
The city CMS (Revize) hosts a **City Meetings** landing page that lists meetings by date, but
the actual agendas/minutes/video archive is a **Granicus** instance:

- **City Meetings landing (Revize):**
  `https://www.rivertonutah.gov/meetings/index.php`
  (schedule doc: `https://www.rivertonutah.gov/government/meetings/city-meeting-schedule-2026.pdf`;
  public-comment procedure: `https://www.rivertonutah.gov/meetings/public-comment.php`)
- **Granicus archive (all bodies, one publisher):**
  `https://rivertoncity.granicus.com/ViewPublisher.php?view_id=1`
  — archives span **December 2020 → present** (July 2026 upcoming at recon time).
  Bodies carried here: **City Council, Planning Commission, Redevelopment Agency,
  Riverton Law Enforcement Service Area Board, Riverton Fire Service Area Board, Historic
  Preservation Commission, Board of Adjustment, Board of Canvassers.**
- **Granicus doc URL patterns:**
  - Agenda: `https://rivertoncity.granicus.com/AgendaViewer.php?view_id=1&clip_id=<clip_id>`
  - Minutes: `https://rivertoncity.granicus.com/MinutesViewer.php?view_id=1&clip_id=<clip_id>&doc_id=<uuid>`
  - RSS harvest: `https://rivertoncity.granicus.com/ViewPublisherRSS.php?view_id=1&mode=minutes`
    (also `mode=agendas`, `mode=podcast`) — **preferred enumeration route** (returns clip_ids +
    dates without scraping the JS table).
- **Utah PMN mirror / fallback (born-digital PDFs, easiest to harvest):** every meeting is
  cross-posted to Utah Public Notice. Minutes/agenda PDFs live at
  `https://www.utah.gov/pmn/files/<fileId>.pdf`. Riverton **Planning Commission** body =
  **5473** (`https://www.utah.gov/pmn/sitemap/publicbody/5473.html`); the Council/RDA bodies
  have their own ids on the same entity (enumerate via the notice pages). **PMN is the
  recommended acquisition source** — the PDFs are clean born-digital text and don't require
  Granicus scraping.

### Format — CONFIRMED born-digital clean text (NO OCR)
`pdftotext -layout` on both verified samples yields clean, selectable, line-numbered text;
proper names intact. Not scanned. Two docs saved to `meeting_minutes/raw/`:
- `riverton_council_2024-04-02.pdf` (PMN `1111447.pdf`)
- `riverton_council_2025-12-16.pdf` (PMN `1380299.pdf`)

### Meeting cadence — **1st & 3rd Tuesday**
Each meeting-day is **one combined minutes doc**: a **Mayor & Council Informal Meeting
~5:15 PM → Work Session (6:00 PM; moving to 4:30 PM in 2026) → Regular City Council Meeting
7:00 PM**. Verified Tuesdays: 2024-04-02 (1st), 2025-04-15 (3rd), 2025-12-02 (1st),
2025-12-16 (3rd), 2026-01-06/-20, 2026-02-03/-17. Riverton City Hall, 12830 S 1700 W.

### Roll-call votes in minutes — CONFIRMED PRESENT, **named per-member** (Riverton/Millcreek-style)
Motions record **mover + seconder + a full named roll call** (every member's yes/no):

> *"Councilmember McDougal MOVED to approve … Councilmember Pierucci SECONDED the motion.
> Mayor Pro Tempore Buroker called for a roll-call vote. The vote was as follows: Buroker-yes,
> Haymond-yes, McCay-yes, McDougal-yes, and Pierucci-yes. The motion passed unanimously."*
> — 2024-04-02 minutes (Mayor Staggs **excused**; 5-member roll).

**MAYOR-VOTE — VERIFIED FROM A REAL TIE-BREAK** (2025-12-16 minutes, Mayor Staggs **present
and presiding**):

> *"Councilmember McDougal MOVED that the City Council approve Resolution No. 25-62 … Mayor
> Staggs called for a roll-call vote. The vote was as follows: Buroker-no, McCay-no,
> McDougal-yes, and Pierucci-yes. **The motion ended in a tie, 2 to 2. Mayor Staggs was
> called to vote to break the tie and voted yes. The motion passed.**"*

→ **Definitive:** even when the Mayor presides and conducts the roll call, the Mayor is **not
in the ordinary tally** (here 4 members present, Haymond excused) and votes **only to break a
tie** — exactly the six-member-council rule. **Build with max council tally = 5, Mayor
non-voting except tie-breaks** (store tie-break Mayor votes as a `vote.note`, Park City
pattern). Named dissent format is **confirmed** (`Buroker-no`), unlike Taylorsville.

---

## 2. Council structure — 5 districts + tie-breaking Mayor

- **5 council districts (D1–D5)**, one member each, elected by district voters; **Mayor
  elected citywide.** 4-year staggered non-partisan terms. **Districts have existed since
  ~2009** (elections labeled "DIST 3/DIST 4" from 2009 on); boundaries **redrawn by
  Ordinance No. 22-07 (2022)** into five equal-population districts (the current lines).
- **Current roster (terms seated January 2026):**

  | Seat | Member | Term |
  |---|---|---|
  | **Mayor** (citywide, tie-break only) | **Tish Buroker** | 2026–2030 (won Nov 2025; was Councilmember/Mayor Pro Tem before) |
  | District 1 | **Andy Pierucci** | 2024–2028 |
  | District 2 | **Troy McDougal** | 2024–2028 |
  | District 3 | **Alexander Johnson** | 2026–2030 (newcomer, Nov 2025) |
  | District 4 | **Shannon Smith** | 2026–2030 (newcomer, Nov 2025) |
  | District 5 | **Spencer Haymond** | 2024–2028 |

- **Roster drift across the 2020-floor record (important for vote attribution):**
  - **Mayor Trent Staggs** presided 2018–Dec 2025 (left after an unsuccessful U.S. Senate
    run); **Tish Buroker** was a **Councilmember (D3)** through 2025 and frequently served as
    **Mayor Pro Tempore**, then won the mayoralty in Nov 2025.
  - **Tawnee McCay** (D4) served through Dec 2025 (recognized for 8 years' service in the
    2025-12-16 minutes) → succeeded by **Shannon Smith (D4)**.
  - **Buroker (D3)** → succeeded by **Alexander Johnson (D3)**.
  - So the 2020–2025 voting bench = **Buroker, Haymond, McCay, McDougal, Pierucci** (+ earlier
    members before 2020 out of scope). Normalize person identity across the mayor/council move
    (Buroker appears as councilmember in votes, then as tie-break Mayor from 2026).
- **Term stagger:** **D3 / D4 / Mayor** on the **2013/2017/2021/2025** cycle; **D1 / D2 / D5**
  on the **2015/2019/2023** cycle.
- City Council page: `https://www.rivertonutah.gov/government/city-council/index.php`
  Mayor page: `https://www.rivertonutah.gov/government/mayor/index.php`
  Government/about: `https://www.rivertonutah.gov/government/about.php` (form-of-government text)

---

## 3. Planning Commission — Riverton has its OWN PC

- **Own Planning Commission**, minutes on the **same Granicus archive** + **PMN body 5473**
  (`https://www.utah.gov/pmn/sitemap/publicbody/5473.html`). Coverage reaches the Granicus
  floor (Dec 2020) and PMN carries current docs (e.g. 2026-06-11 minutes = `utah.gov/pmn/files/1455569.pdf`).
- **Cadence — 2nd & 4th Thursday** (verified: 2026-05-14/-28, 2026-06-11/-25, 2026-07-09).
- **Votes — CONFIRMED PRESENT** (text-verified on the 2026-06-11 doc, saved to
  `planning_commission/raw/riverton_pc_2026-06-11.pdf`). Format = **narrative named
  mover/seconder + outcome**:
  > *"Commissioner Cannon moved that the Planning Commission recommend APPROVAL … Commissioner
  > Keele seconded the motion. The motion passed with unanimous consent of the Commission."*
  PC makes **recommendations to Council** on rezones/land-use (rich referral material — e.g.
  the 2026-06-11 doc carries RM-6 rezone recommendations by application number). Commissioners
  seen: Cannon, Cluff, Marzo, Keele, Beck, Chair Park. **Note:** unanimous outcomes are
  "unanimous consent" (majority not individually named) — spot-check whether contested PC
  votes print a named roll call during acquisition.

---

## 4. Public comments — inline speaker notes + eComment submission; **no separate published archive**

- **In-meeting public comment** is taken and **paraphrased inline in the minutes** under a
  "Citizen Comment" section (verified in the 2025-12-16 doc: named speakers with paraphrased
  remarks). Council comment period = 15 min total, 3 min/speaker; PC comment restricted to
  public-hearing topics. → these are **meeting-record speaker notes, NOT genuine written
  comments** → a labeled `minutes_speaker_log.csv`, never `all_comments_clean.csv`.
- **Submission channels:** **eComment via the City Meetings page** and **email to
  `recorder@rivertonutah.gov`** (per the city's meetings guidance). No standalone
  published written-comment / correspondence archive surfaced.
- **Verdict:** treat as **SUBMIT-ONLY / honest-empty for `all_comments_clean.csv`**, with the
  inline speaker log captured separately. Phase-2 check: whether Granicus agenda packets or the
  eComment portal expose any archived written submissions before finalizing the honest-zero.

---

## 5. Elections — Salt Lake County; **already in the canonical CSV** (one 2019 gap)

- **Run by:** Salt Lake County Clerk; live results `https://electionresults.utah.gov/`.
  City page: `https://www.rivertonutah.gov/government/elections/index.php`.
- **The canonical `salt_lake_county/elections/slco_municipal_results_long.csv` ALREADY
  contains Riverton** — **3,495 rows**. Filter `contest LIKE '%RIVERTON%'` (labels vary:
  `RIVERTON CITY COUNCIL DIST 3`, `RIVERTON CITY COUNCIL DISTRICT 4`, `RIVERTON CITY MAYOR`,
  early `RIVERTON CITY COUNCIL #1`).
- **Seat structure = 5 districts + citywide Mayor** (non-partisan). Years present and cycle:

  | Year | Riverton contests present |
  |---|---|
  | 2007 | Council #1, #2, #5 (early **numbered** at-large labels, pre-district naming) |
  | 2009 | Council DIST 3, DIST 4, **Mayor** |
  | 2011 | Council 1, 2, 5 |
  | 2013 | Council DIST 3, DIST 4, **Mayor** |
  | 2015 | Council DIST 1, DIST 2, DIST 5 |
  | 2017 | Council DIST 3, DIST 4, **Mayor** |
  | **2019** | **NONE — 0 rows (GAP)** |
  | 2021 | Council DISTRICT 3, DISTRICT 4, **Mayor** |
  | 2023 | Council DISTRICT 1, DISTRICT 2, DISTRICT 5 |
  | 2025 | Council DISTRICT 3, DISTRICT 4, **Mayor** |

- **⚠ 2019 GAP:** the 2015/2019/2023 cycle (D1/D2/D5) is missing its **2019** general — same
  failure mode seen for Taylorsville/South Jordan/Millcreek (numbered-sheet layout dropped the
  city string). Those D1/D2/D5 winners govern **2020–2023 (in-scope)** → **re-parse the raw
  2019 SOVC** for Riverton D1/D2/D5. (2019 is below the repo's 2020 floor as an *event* but its
  winners are the 2020-2023 bench, so recover it.)
- **County = Salt Lake (UGRC CountyID 18).** Winners are UPPER-CASE — normalize before joining
  to the minutes roster (person + year + district).

---

## 6. GIS — **official council-district FeatureServer exists** (rare — no need to derive)

Riverton runs its own ArcGIS Server: **`https://gis.rivertoncity.com/arcgis/rest/services`**
(v10.9; folders Hosted/Streets/Utilities; 178 services). Council-district layers:

- **Combined (recommended):**
  `https://gis.rivertoncity.com/arcgis/rest/services/Council_Districts/FeatureServer/0`
  → layer `Riverton_City_Council_Districts_2022` (post-Ordinance 22-07 boundaries).
- **Per-district split:**
  `https://gis.rivertoncity.com/arcgis/rest/services/Hosted/Council_Districts_2022/FeatureServer`
  → layers 0–4 = **District 1 … District 5**, layer 5 = combined.
- **Pre-2022 vintage (for pre-redistricting address→district):**
  `https://gis.rivertoncity.com/arcgis/rest/services/Hosted/City_Council_Voting_District_20191231/FeatureServer`
  (the 2019 lines — use for questions before the 2022 redraw).
- Web map / portal: `https://gis.rivertoncity.com/portal/home/` ;
  district-map page `https://www.rivertonutah.gov/publicworks/gis/district-map.php` ;
  adoption blog "Riverton City Council Adopts New District Map"
  (`https://www.rivertonutah.gov/blog_detail_T55_R244.php`).
- **UGRC fallbacks:** precinct/VistaBallotAreas **CountyID = 18**; UGRC Municipal Boundaries
  `NAME='RIVERTON'` for the city outline; SLCo open data `gisdata-slco.opendata.arcgis.com`.
- → **Build `geo/address_to_district.py` directly against the official FeatureServer** (query
  `Hosted/Council_Districts_2022/FeatureServer/5` or `Council_Districts/FeatureServer/0`),
  with the 2019 layer as the pre-2022 vintage. **No precinct-derivation needed** (unlike
  Taylorsville/South Jordan/Millcreek).

---

## Retrieval plan (recommended order)

1. **Council minutes 2020→present:** enumerate via the Granicus **minutes RSS**
   (`ViewPublisherRSS.php?view_id=1&mode=minutes`) → for each Council clip pull the PMN
   `utah.gov/pmn/files/<id>.pdf` (born-digital) into `meeting_minutes/raw/<year>/`; Granicus
   MinutesViewer is the fallback. One combined Informal+Work+Regular doc per Tuesday.
2. **Vote extraction (council):** parse `<Name> MOVED … <Name> SECONDED … roll-call vote …
   The vote was as follows: Buroker-yes, Haymond-no, …` (named per-member; `Present:`/
   excused from the attendance header); **max tally 5, Mayor non-voting**; capture the
   **tie-break pattern** (`The motion ended in a tie … Mayor <X> … voted yes to break the
   tie`) as a Mayor `vote.note` (Park City model). Also carve **RDA** votes (Council convenes
   as the Redevelopment Agency — separate Granicus body).
3. **Planning Commission 2020→present:** same Granicus/PMN (body 5473), 2nd & 4th Thursday;
   named mover/seconder + "unanimous consent"; capture PC→Council recommendation + application
   numbers for the referral layer; verify contested-vote naming on the first divided PC vote.
4. **Comments:** build a labeled `minutes_speaker_log.csv` from the inline Citizen-Comment
   sections; document the SUBMIT-ONLY verdict (eComment + recorder email; no published
   archive) in `public_comments/AVAILABILITY.md` after the packet/eComment Phase-2 check.
5. **Elections:** reuse the canonical `slco_municipal_results_long.csv`
   (`contest LIKE '%RIVERTON%'`); **re-parse the raw 2019 SOVC** for D1/D2/D5.
6. **Geo:** build `address_to_district.py` against the official FeatureServer
   (`Hosted/Council_Districts_2022/FeatureServer`), 2019 layer for pre-2022 vintage.

---

## Risks / blockers

- **Two-portal split (LOW):** city CMS is **Revize**, but minutes live on a **separate
  Granicus** instance + **Utah PMN** mirror. Harvest from Granicus RSS / PMN, not the Revize
  meetings page (which only lists dates). PMN PDFs fetched cleanly with a browser UA this recon.
- **Mayor tie-break vote (STRUCTURAL — resolved):** six-member form → **Mayor non-voting,
  max tally 5, votes only to break ties**. Confirmed by a real 2-2 tie-break (2025-12-16).
  Model the Mayor tie-break as a `vote.note`, not a 6th roll-call slot.
- **Roster move Buroker councilmember→Mayor (2026):** normalize her person identity across the
  transition (votes as D3 councilmember through 2025, then tie-break Mayor). McCay→Smith (D4),
  Buroker→Johnson (D3) at Jan 2026 seating.
- **2019 election gap (D1/D2/D5):** absent from the shared CSV; those winners are the 2020–2023
  bench → raw-2019-SOVC re-parse needed.
- **PC contested-vote naming unconfirmed:** verified sample was unanimous-consent; confirm the
  named-roll format on the first divided PC vote before bulk extraction.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| City site (Revize CMS) | https://www.rivertonutah.gov/ |
| City Meetings landing | https://www.rivertonutah.gov/meetings/index.php |
| Public-comment procedure | https://www.rivertonutah.gov/meetings/public-comment.php |
| Granicus archive (all bodies, Dec 2020+) | https://rivertoncity.granicus.com/ViewPublisher.php?view_id=1 |
| Granicus minutes RSS (enumeration) | https://rivertoncity.granicus.com/ViewPublisherRSS.php?view_id=1&mode=minutes |
| Granicus minutes doc pattern | https://rivertoncity.granicus.com/MinutesViewer.php?view_id=1&clip_id=<clip>&doc_id=<uuid> |
| PMN minutes PDF pattern | https://www.utah.gov/pmn/files/<fileId>.pdf |
| PMN Planning Commission body | https://www.utah.gov/pmn/sitemap/publicbody/5473.html |
| Council minutes sample (5-member roll, mayor excused) | https://www.utah.gov/pmn/files/1111447.pdf (2024-04-02) |
| Council minutes sample (mayor tie-break, 2-2) | https://www.utah.gov/pmn/files/1380299.pdf (2025-12-16) |
| PC minutes sample | https://www.utah.gov/pmn/files/1455569.pdf (2026-06-11) |
| City Council page | https://www.rivertonutah.gov/government/city-council/index.php |
| Mayor page | https://www.rivertonutah.gov/government/mayor/index.php |
| Form-of-government / about | https://www.rivertonutah.gov/government/about.php |
| Elections (city) | https://www.rivertonutah.gov/government/elections/index.php |
| Canonical election CSV (Riverton in it) | salt_lake_county/elections/slco_municipal_results_long.csv (filter %RIVERTON%; 2019 GAP) |
| District FeatureServer (combined 2022) | https://gis.rivertoncity.com/arcgis/rest/services/Council_Districts/FeatureServer/0 |
| District FeatureServer (per-district) | https://gis.rivertoncity.com/arcgis/rest/services/Hosted/Council_Districts_2022/FeatureServer |
| District FeatureServer (pre-2022 / 2019 lines) | https://gis.rivertoncity.com/arcgis/rest/services/Hosted/City_Council_Voting_District_20191231/FeatureServer |
| GIS portal | https://gis.rivertoncity.com/portal/home/ |
| District map page | https://www.rivertonutah.gov/publicworks/gis/district-map.php |

```json
{"vendor":"Granicus (rivertoncity.granicus.com, view_id=1) for the meeting archive + Utah PMN mirror (utah.gov/pmn/files/<id>.pdf); city CMS itself is Revize","minutes_landing_url":"https://rivertoncity.granicus.com/ViewPublisher.php?view_id=1 (city page: https://www.rivertonutah.gov/meetings/index.php)","minutes_url_pattern":"Granicus MinutesViewer.php?view_id=1&clip_id=<clip>&doc_id=<uuid>; enumerate via ViewPublisherRSS.php?view_id=1&mode=minutes; PMN PDF https://www.utah.gov/pmn/files/<fileId>.pdf","coverage_years":"Granicus archive Dec 2020 -> present (2020 floor fully covered); PMN mirror current","format":"born-digital clean text PDF (no OCR)","votes_in_minutes":true,"vote_style":"named per-member roll call ('Buroker-yes, Haymond-no, ...'); mover+seconder named; contested/named-dissent format CONFIRMED","pc_portal":"same Granicus archive + Utah PMN body 5473 (utah.gov/pmn/sitemap/publicbody/5473.html)","pc_coverage":"Dec 2020 -> present; 2nd & 4th Thursday; votes present (named mover/seconder + 'unanimous consent'); recommends rezones to Council","council_weekday":"Tuesday (1st & 3rd); Informal 5:15pm + Work Session 6:00pm[->4:30pm 2026] + Regular 7:00pm, one combined minutes doc","num_districts":5,"at_large_seats":0,"mayor_votes":false,"max_tally":5,"mayor_note":"six-member council form: mayor is chair+executive, votes ONLY to break a 2-2/tie (verified 2025-12-16), on city-manager hire/fire, or to amend mayoral powers; model tie-break as vote.note (Park City pattern)","current_members":["Mayor Tish Buroker (citywide, tie-break only; was D3 councilmember through 2025)","D1 Andy Pierucci (2024-2028)","D2 Troy McDougal (2024-2028)","D3 Alexander Johnson (2026-2030, new)","D4 Shannon Smith (2026-2030, new)","D5 Spencer Haymond (2024-2028)"],"roster_drift":"2020-2025 bench = Buroker/Haymond/McCay/McDougal/Pierucci under Mayor Trent Staggs (left Dec 2025); Jan 2026: Buroker->Mayor, McCay->Smith(D4), Buroker's D3->Johnson","comments_published":"submit-only / honest-empty for all_comments_clean.csv (eComment via City Meetings + email recorder@rivertonutah.gov); public comment paraphrased inline in minutes -> minutes_speaker_log.csv; no standalone written-comment archive","elections":{"in_canonical_csv":true,"path":"salt_lake_county/elections/slco_municipal_results_long.csv","filter":"contest LIKE '%RIVERTON%'","rows":3495,"seats":"5 districts (D1/D2/D5 cycle 2015/2019/2023; D3/D4/Mayor cycle 2013/2017/2021/2025) + citywide Mayor","years_present":"2007,2009,2011,2013,2015,2017,2021,2023,2025","gap":"2019 general MISSING (D1/D2/D5) - re-parse raw SOVC; winners are the 2020-2023 bench","county":"Salt Lake (UGRC CountyID 18)"},"gis_source":"OFFICIAL city ArcGIS: https://gis.rivertoncity.com/arcgis/rest/services/Council_Districts/FeatureServer/0 (2022 combined) + Hosted/Council_Districts_2022/FeatureServer (layers 0-4 = District 1-5) + Hosted/City_Council_Voting_District_20191231/FeatureServer (pre-2022 vintage); Ordinance 22-07 redistricting; UGRC CountyID 18 fallback - NO precinct-derivation needed","blockers":["two-portal split: city CMS=Revize but minutes on separate Granicus + PMN mirror - harvest via Granicus RSS/PMN, not the Revize page","mayor tie-break vote (six-member form) - max tally 5, mayor votes only to break ties (verified) - store as vote.note","Buroker councilmember->Mayor 2026 + McCay->Smith/Buroker->Johnson roster move - normalize person identity","2019 election gap (D1/D2/D5) - raw SOVC re-parse; governs 2020-2023","PC contested-vote naming format unconfirmed (sample was unanimous consent)"],"confidence_notes":"HIGH on portal/format/votes/cadence/structure/mayor-tie-break (2 council minutes + 1 PC minutes text-verified; tie-break quoted verbatim; form-of-gov confirmed from city site) ; HIGH on GIS (FeatureServer endpoints hit live, layers enumerated) ; HIGH on elections presence (CSV grepped) with 2019 gap noted"}
```
