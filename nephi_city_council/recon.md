# Nephi, Utah — Civic Data Recon

City seat of **Juab County** (~6,500 pop.). Small rural city — records are reasonably
complete online (CivicPlus portal back to 2020), which is better than typical for this size.
Recon date: 2026-06-26. Read-only source mapping; nothing bulk-downloaded.

---

## 1. Council minutes

- **Vendor / platform:** CivicPlus **CivicEngage** CMS with the standard **`/AgendaCenter`**
  module (the page footer/branding says "CivicEngage"). This is the CivicPlus AgendaCenter
  pattern in the portal playbook.
- **Host:** `https://www.nephi.utah.gov` (also resolves at `nephi.utah.gov`).
- **Base URL:** `https://www.nephi.utah.gov/AgendaCenter`
- **Minutes URL pattern:** `https://www.nephi.utah.gov/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<id>`
  (e.g. `/AgendaCenter/ViewFile/Minutes/_06172025-383`). Agenda equivalent is
  `ViewFile/Agenda/_...`. The trailing `<id>` is an internal sequential document id, not
  derivable from the date alone — must harvest from the listing/search pages.
- **Search endpoint (for enumerating by year):**
  `https://www.nephi.utah.gov/AgendaCenter/Search/?term=&CIDs=all&startDate=01/01/YYYY&endDate=12/31/YYYY`
  — returns dated rows with Agenda/Minutes links. Confirmed it returns 2020 minutes
  (e.g. `_12152020-148`, `_11032020-142`, `_10062020-138`).
- **Bodies / categories on AgendaCenter:**
  - **City Council** — agendas/minutes listed for 2002, 2018–2026 (continuous 2018→present).
    Minutes confirmed present (not agenda-only) back through **2020**.
  - **Planning Commission** — 2018–2026.
  - **Advisory Committees** (e.g. Airport Advisory Committee) — sparse, 2024.
  - **No Redevelopment Agency / RDA / CRA category** (see §3).
- **Mirror / fallback:** Utah Public Notice site **`utah.gov/pmn`** also hosts Nephi council
  minutes PDFs (e.g. `https://www.utah.gov/pmn/files/1280671.pdf` = May 20 2025;
  `.../1380339.pdf` = Jan 6 2026). Useful as a backup and for any year the AgendaCenter
  drops. The city's own site explicitly directs people to PMN for agendas/notices.
- **Format:** **Born-digital text-layer PDFs** (clean `pdftotext -layout`; NOT scanned/OCR).
  Verified on the June 17 2025 minutes and Jan 6 2026 minutes — crisp structured text.
  (WebFetch alone can't read them — flate-compressed streams; download + `pdftotext`.)
- **Meeting weekday:** **Tuesday**, 7:00 p.m., council chambers at 21 East 100 North.
  Stated schedule is **1st & 3rd Tuesdays** of each month; historically (2020) they met
  more frequently — multiple consecutive Tuesdays appear — plus work sessions and special
  meetings. Treat "Tuesday" as the rule with extra/special meetings mixed in.
- **Votes in minutes — IMPORTANT NUANCE:** Motions record the **mover and seconder by name**
  ("Councilor Shari Cowan moved... Councilor Jeramie Callaway seconded the motion"), but the
  **outcome is recorded as a narrative summary** — "The motion passed unanimously" /
  "passed on unanimous vote." There is **NO per-member roll-call Aye/Nay tally by name** on
  routine unanimous votes. Individual names would presumably only surface on a split/contested
  vote (dissenters named) — none observed in the sample. So: vote *outcomes* + mover/seconder
  are extractable, but a full named roll-call grid is generally NOT present. Plan vote
  extraction around mover/seconder + outcome, not an Aye/Nay-by-name matrix.

## 2. Council structure

- **Form:** Mayor + **5-member council**, all elected **at-large** (no districts/wards;
  standard small-Utah-city setup; confirmed at-large by the 2025 ballot wording "2 seats at
  large"). A professional **City Administrator** (Seth Atkinson) runs day-to-day ops.
- **Members (as of the June 2025 / current minutes):**
  - **Mayor:** Justin D. Seely (re-elected Nov 2025)
  - Shari Cowan
  - Jeramie Callaway
  - Travis "Skip" Worwood *(NOTE name ambiguity below)*
  - Travis L. Worwood
  - JD Parady
  - (Tate Douglas also appears on the current roster page — see ambiguity note)
- **Name ambiguity to resolve later:** City pages list members including both "Travis
  Worwood" and "Tate Douglas," while minutes name "Skip Worwood" and "Travis L. Worwood" as
  *distinct* attendees (one present, one absent in the June 17 2025 minutes). There appear to
  be **two Worwoods** (Skip vs. Travis L.). 2025 candidates per campaign-disclosure listing:
  Bart Stanley Miller, Justin Seely (mayor), Jeramie Callaway, Skip Worwood, Tate Douglas.
  The retrieval/cleaning pass must reconcile Skip Worwood vs Travis L. Worwood vs "Travis
  Worwood" and confirm the exact 5 seated members + which 2 seats were up in 2025.
- **Mayor votes?** Likely **only to break a tie** — under Utah's statutory small-city council
  forms the mayor presides but does not vote except on ties, and in every sampled meeting the
  mayor presided/opened hearings while only *council members* made and seconded motions. Not
  explicitly stated on the website; **flag as "presumed tie-breaker, verify in code/charter."**

## 3. RDA / CRA

- **No separate Redevelopment / Community Reinvestment Agency found.** No RDA/CRA category on
  the AgendaCenter, no RDA page on the city site, no Nephi entry surfaced in RDA searches.
- Conclusion: **none** (or, if any redevelopment action exists, it is handled inside the
  regular City Council meeting, not as a separately-noticed body). No separate minutes to
  collect. Low confidence only in the sense of proving a negative — but nothing indicates one
  exists.

## 4. Public comments

- **No separate published written-comment archive.** Public comment is handled **in-meeting**
  and recorded **only within the minutes** narrative (e.g. "Mayor Seely opened the meeting to
  public comment. There was no public comment." / "NO PUBLIC COMMENT"). Public hearings (e.g.
  budget) likewise note whether comment was received, summarized in the minutes.
- **Submission method:** in-person at the Tuesday meeting / public hearings. No online
  comment portal or published written-comment packet observed. Agenda packets on PMN *could*
  occasionally contain attached letters, but there is no dedicated comments dataset.
- Verdict: **published = no** as a standalone dataset; comments exist **in-minutes only**.

## 5. Elections (run by Juab County)

- **At-large**, vote-for-N. Nov 4 2025 municipal general had **Nephi City Council — 2 seats
  at large** plus **Mayor**. No districts. **No ranked-choice voting** (Nephi is not in
  Utah's RCV pilot; standard plurality/top-N).
- **Primary source — Utah state portal (Enhanced Voting), covers Juab:**
  - 2025 general landing: `https://electionresults.utah.gov/results/public/juab-county-ut/elections/general11042025`
    (renders via `app.enhancedvoting.com`; JS-driven — needs the Enhanced Voting JSON API or
    a headless fetch; the human-facing per-precinct view for the council race is at
    `https://app.enhancedvoting.com/results/public/juab-county-ut/elections/general11042025/ballot-items/01000000-e857-63d6-6193-08de10064808`).
  - Election slugs follow `…/elections/<type><MMDDYYYY>` (e.g. `general11042025`,
    and a 2025 municipal `primary`). Earlier cycles (2021, 2023) should be reachable via the
    same `juab-county-ut` path with their date slugs — confirm slugs during retrieval.
- **County source:** Juab County Clerk, 160 N Main, Nephi. County election pages:
  `https://juabcounty.gov/category/election/` and legacy `http://www.co.juab.ut.us/County/clerk/election.html`.
  The state Enhanced Voting portal is richer/cleaner than the county pages for a county this
  small — **use `electionresults.utah.gov` as the primary**, county clerk as backup/canvass.
- **City's own elections pages:** `https://www.nephi.utah.gov/269/Elections`,
  `/618/Candidates`, `/680/Disclosures` (candidate lists + campaign-finance disclosures —
  useful for name normalization, not vote totals).
- **Existing archive:** **none** for Juab County (no Desktop archive yet; build from scratch).
- **Cross-check / risk:** small at-large races are sometimes **uncontested or canceled**
  (≤N candidates for N seats → race may not appear or appears as a formality). Expect thin
  years. 2025 mayor (Seely) appears to have been re-elected; verify whether council was
  contested.

## 6. GIS

- **At-large city → no council districts.** The address tool degenerates to an
  **address → in/out of Nephi city limits** check (no precinct→district map needed), per the
  election playbook's at-large guidance.
- **City limits boundary:** UGRC **Utah Municipal Boundaries** layer, filter `NAME='NEPHI'`
  (ArcGIS FeatureServer; standard UGRC `opendata.gis.utah.gov` / `services1.arcgis.com` host).
- **Precincts (if needed for results joins):** UGRC **VistaBallotAreas** FeatureServer,
  **`CountyID = 12` (Juab)**. Request `outSR=4326` and sanity-check coords (~ -111.8, 39.7 for
  Nephi) to avoid the known UTM-mislabel CRS trap noted in the playbook.
- Boundaries available: **yes** (UGRC statewide coverage includes Nephi & Juab).

---

## What is NOT available / open questions
- No per-member **named roll-call** on routine votes (only mover/seconder + "unanimous").
- No **RDA/CRA** body or minutes (appears not to exist).
- No standalone **public-comment** dataset (in-minutes only).
- No existing **Juab election archive**; state portal is JS — needs API/headless extraction.
- **Mayor-vote rule** not stated online (presumed tie-breaker — verify).
- **Member roster name reconciliation** needed (Skip vs Travis L. Worwood; Tate Douglas).
- AgendaCenter `<id>` suffixes are non-derivable — must scrape listing pages per year.

```json
{"city":"Nephi","minutes":{"vendor":"CivicPlus CivicEngage (/AgendaCenter)","base_url":"https://www.nephi.utah.gov/AgendaCenter","minutes_years":"2020-2026 (City Council continuous 2018+; born-digital)","format":"born-digital text-layer PDF","votes_in_minutes":true,"meeting_weekday":"Tuesday"},"council":{"districts":0,"at_large":5,"mayor_votes":false,"members":["Justin D. Seely (Mayor)","Shari Cowan","Jeramie Callaway","Skip Worwood","Travis L. Worwood","JD Parady","Tate Douglas (roster-listed; reconcile)"]},"rda":{"separate_meetings":"none","where":"no RDA/CRA body found; any redevelopment handled in regular council meeting"},"comments":{"published":"no","where":"in-minutes only (narrative; public hearings noted)","submit":"in-person at Tuesday meeting / public hearings; no online portal"},"elections":{"county":"Juab","source_url":"https://electionresults.utah.gov/results/public/juab-county-ut/elections/general11042025","existing_archive":"none","district_based":false,"rcv":"no"},"geo":{"ugrc_county_id":12,"boundaries_available":true,"districts_or_atlarge":"at-large (no districts; address->in/out city limits via UGRC Municipal Boundaries NAME='NEPHI')"},"risks":["AgendaCenter doc <id> suffixes non-derivable - must scrape per-year listing pages","Routine votes recorded as 'passed unanimously' - no named Aye/Nay roll-call to extract","Member roster name ambiguity (Skip Worwood vs Travis L. Worwood vs 'Travis Worwood'; Tate Douglas) needs reconciliation","Mayor-vote rule (tie-breaker) presumed not confirmed - verify in Utah code/city charter","State election portal is JS/Enhanced-Voting - needs API or headless fetch; 2021/2023 slugs unconfirmed","Small at-large races may be uncontested/canceled in some years - expect thin coverage","mayor_votes set false on presumption - VERIFY"],"recommended_order":["1. Scrape AgendaCenter Search per year (2020-2026) to harvest City Council minutes ViewFile ids; PMN as fallback","2. Download born-digital minutes PDFs -> pdftotext -layout -> markdown","3. Extract motions (mover/seconder/outcome) - not a named roll-call grid","4. Pull Juab elections from electionresults.utah.gov (Enhanced Voting API) for 2021/2023/2025 - filter Nephi mayor+council at-large","5. Reconcile candidate<->member names (disclosures page helps)","6. Build geo as address->in/out Nephi city limits via UGRC Municipal Boundaries NAME='NEPHI' (no district map)","7. Confirm mayor-vote rule and final 5-member roster"]}
```
