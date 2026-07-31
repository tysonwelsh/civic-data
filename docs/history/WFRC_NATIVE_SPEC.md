# WFRC-NATIVE SPEC — research, own-terms assessment, and structured-data plan

**Date: 2026-07-22. Status: RESEARCH COMPLETE — implementation plan for owner review.**
This is the research deliverable for the TODO item "WFRC-NATIVE HOLISTIC PACKAGE"
(drafted 2026-07-20). Method: three parallel web-research passes (institutional role /
publication series / structured-data-GIS-model surface), all verified against primary
sources (wfrc.utah.gov, le.utah.gov, the WFRC ArcGIS org, UDOT, GitHub), cross-checked
against the existing `wfrc_mpo/` build. Load-bearing URLs inline; unverified claims
flagged. Companion TODO item stays open until the package is built.

---

## 1. What WFRC actually is — the researched account

### 1.1 Dual legal identity

WFRC is **two overlapping things in one organization**:

1. **An Association of Governments (AOG)** — a voluntary interlocal entity organized
   March 1969 by Davis/Salt Lake/Weber county officials (Tooele 1969, Morgan 1972) under
   the Interlocal Cooperation Act (UCA Title 11 Ch. 13 — stated by WFRC; founding
   agreement itself not located). https://wfrc.utah.gov/about/detailed-history
2. **The federally designated MPO** for the Salt Lake and Ogden–Layton urbanized areas,
   designated 1973-12-26 (23 U.S.C. §134; Utah Code **§72-1-208.5** defines MPOs, obliges
   UDOT cooperation, and — load-bearing — requires **contiguous MPOs to coordinate and
   submit plans jointly**, the statutory root of the WFRC–MAG JPAC machinery; it also
   grants MPOs access to UI employer records for modeling).
   https://le.utah.gov/xcode/Title72/Chapter1/C72-1-S208.5_1800010118000101.xml

Board: 27 nominal members — 19 local elected officials **appointed by county councils of
governments** (seats population-scaled) + UDOT + UTA voting, 6 non-voting (legislators,
GOPB, Envision Utah). Cities reach WFRC **through their county COG**, and WFRC's funding
calls route candidate-project lists back through the COGs — the COG is the hidden hinge
of the whole allocation process. (Matches the repo's `roster/council_seats.csv`.)

### 1.2 The federal MPO product set

- **RTP** — long-range fiscally-constrained plan, 4-year cycle (2023-2050 adopted May
  2023, amended ≥4×; **2027-2055 in development**, preferred scenario published).
  **RTP Phase-1 listing is a programming GATE**: WFRC's own STP rules require major
  capacity projects to be in Phase 1 before programming; RTP inclusion also qualifies
  projects for county corridor-preservation money.
- **TIP** — 6-year program, annual vintages (adopted 2026-2031; draft 2027-2032 in
  comment). Rolls into UDOT's STIP (FHWA/FTA concurrence letters).
- **UPWP** (annual work program w/ budget-by-funding-source), **air-quality conformity
  memoranda** (numbered series #27→43a), **Public Participation Plan** (2026 update in
  comment), **Title VI plan** (2023).

### 1.3 The money WFRC itself programs (~$40–50M/yr federal)

Verified against the FY25 Funding Programs Packet
(https://wfrc.utah.gov/Programs/FY25%20WFRC%20Funding%20Programs%20Packet.pdf) — WFRC
sub-allocates the urbanized-area shares of four federal formula programs (**STP/STBG
~$31–35M, CMAQ ~$7–8M, TAP ~$2–3M, Carbon Reduction ~$3–4M**), split Ogden-Layton vs
Salt Lake UZA. One selection pipeline for all four: **September Letter of Intent → COG
circulation → December concept report + cost estimate (CMAQ/CRP add emissions form) →
staff field review + technical scoring → Technical Advisory Committees → Trans Com →
Council approval (spring)**. WFRC brands itself as running **nine funding programs**
(the four federal + TLC + SAP-TA + CDBG + CIB assistance + WFEDD/EDA).

**What WFRC does NOT control:** state TIF/TTIF capacity money (Utah Transportation
Commission), UDOT statewide programs (NHPP/HSIP/freight), UTA's FTA formula funds,
USDOT discretionary (though the 2024 **Comprehensive Safety Action Plan** was adopted
expressly to make the region SS4A-eligible).

### 1.4 State-law roles (the influence machinery)

- **HB462 (2022) SAP certification — WFRC's hardest power.** UCA §10-9a-403.1 (2025
  recodification → Title 10-20): cities with fixed-guideway stations must adopt station
  area plans (vision, map, **5-year implementation plan** naming zoning changes); the
  **MPO provides written certification of compliance**; deadline 2025-12-31 for existing
  stations; new stations must comply before service begins. Flow: adopted plan submitted
  ≥2 wks before an RGC meeting → staff review → **RGC → Council certifies/denies** at
  the Jan/Mar/May/Aug/Oct meetings. Scale (Mar-2025 joint WFRC/MAG progress report):
  **127 station areas / 38 certified / 49 in prep; ~34,000 housing units planned in the
  first 33 certified SAPs; 79/127 got TA**; later news: **72 certified plans, 75,000+
  homes**. Negative finding, verified: **the statute attaches no direct funding penalty**
  — the teeth are deadlines, MPO gatekeeping, and adjacent incentives (HTRZ, TA money).
  Whether post-2022 HTRZ amendments make certification a formal HTRZ prerequisite:
  UNVERIFIED (flagged).
- **SB34 (2019) MIH linkage.** Cities' moderate-income-housing reports go to the state
  housing division **and to their AOG** (i.e., WFRC); non-compliance blocks TIF/TTIF
  programming. WFRC's role here is TA/coordination, NOT certification. (HB436 (2026)
  paused MIH reporting for a year.)
- **Corridor preservation** — planner/gatekeeper, not fund-holder: RTP inclusion
  qualifies projects for the county Local Corridor Preservation Funds; WFRC sits on
  UDOT's revolving-fund advisory council.
- **WFEDD/CEDS** — WFRC is the EDA-designated Economic Development District (2013 or
  Aug-2014 — WFRC's own pages disagree; flagged); CEDS listing is the doorway to EDA
  grants.
- **CDBG small-cities** — since 1983 WFRC administers the state-delegated program for
  **Morgan, Tooele, Weber (excl. Ogden)** counties, ~$1M/yr; a Regional Review Committee
  of COG-nominated elected officials scores and ranks applicants (the annual **Rating &
  Rankings spreadsheet** — a genuinely structured allocation record).

### 1.5 Wasatch Choice + the vision levers

Wasatch Choice (2040 → 2050 → "**Wasatch Choice for 2054**" for the 2027 cycle) is the
shared land-use/transportation/economy vision, organized around a **centers hierarchy**.
It is voluntary for land use — WFRC has no zoning power — so implementation runs through:
(a) the RTP as the vision's transportation element (money follows centers); (b) **TLC
grants** funding the city plans/codes that operationalize centers; (c) SAP certification
(HB462 gave one slice of the vision statutory force — SAP objectives are expressly
Wasatch-Choice-consistent); (d) toolkits + the **Generalized Future Land Use layer**, by
which WFRC actively tracks city general-plan alignment with the vision; (e) the **"Big
Five" progress indicators**, published as ArcGIS metric services (see §3.3).

### 1.6 TLC — the flagship planning-money program

Partnership of WFRC + Salt Lake County + UDOT + UTA (current page adds GOPB; roster has
drifted — flagged). **~$1.9–2.1M/yr; lifetime $15.5M / 180 projects / 62 communities;
local match ≥6.77%.** Funds plans, small-area plans, code rewrites, TOD/first-last-mile
studies — **not** capital. Same Sept-LOI → Dec-application → ~March-award cycle. For most
Wasatch Front suburbs **this is how general-plan updates and code rewrites get paid for**
— the region's soft editorial presence inside local planning documents, and the repo's
best cross-tier trace target (award → city minutes → adopted plan → rezone).
SAP-TA is the sibling pot: **$5M from GOEO**, WFRC+MAG+UTA programmed, rolling;
25 awards / $3.722M as of Mar-2025.

### 1.7 Ecosystem + advocacy

JPAC (WFRC+MAG 2002, +Cache/Dixie MPOs 2007) → **Utah's Unified Transportation Plan**
(UDOT + UTA + 4 MPOs, the shared 30-yr statewide needs picture the Legislature has
repeatedly funded against). Government Affairs: a public per-session **bill tracker with
explicit WFRC positions**, appropriations tracker, session wrap-ups 2022-2026 — a
structured record of the region lobbying the state (join surface to `ut_state`).

### 1.8 How things flow (the two canonical chains)

**(a) Project:** RTP phase (gate) → Sept LOI → COG → concept report → TAC → Trans Com →
Council TIP adoption (+30-day comment + conformity) → STIP → **UDOT ePM PIN** (status
Proposed → STIP → Funding; Master PINs created by UDOT Program Development during STIP
development) → obligation → construction. The PIN is the statewide join key; WFRC's TIP
services are "extracted from ePM."
**(b) Plan:** TLC/SAP-TA award → consultant/city produce plan (WFRC/UTA/UDOT at the
table) → council adopts → RGC review → **WFRC Council certifies** → city executes the
5-yr implementation plan (rezones) → HTRZ value capture concentrates there.

---

## 2. The own-terms assessment — what kind of entity this is

The current build models WFRC as "a council whose minutes we read" plus two data layers.
The research shows WFRC's native work products are **five distinct roles**, only some of
which are motion-shaped:

| Role | Native artifact | Repo status |
|---|---|---|
| **Allocator** (~$50M/yr federal + TLC/SAP-TA/CDBG) | award lists, TIP funding tables, obligation reports, rating/ranking sheets | ❌ dollars not structured (TIP rows lack funding source; grants un-tabled) |
| **Certifier** (HB462 SAP) | certification actions + the statewide SAP pipeline roster | ⚠️ 15 cert motions extracted; no ledger, no station-area grain |
| **Forecaster** (REMM/TDM) | city-area + TAZ projections, ATO, V/C scenarios | ✅ projections federated; ATO/metrics catalog-only |
| **Visionary/scorekeeper** (Wasatch Choice) | centers, GFLU, Big-Five metric services | ⚠️ partial GIS catalog |
| **Convener/advocate** (JPAC, Unified Plan, bill tracker) | committee record, legislative positions | ❌ positions un-captured; packets un-captured |

**The corrective conclusion confirmed:** votes are the wrong spine for this entity. The
native spine is **the project (PIN) and the dollar** on the transportation side, and
**the plan/certification** on the land-use side. Both spines join outward: PIN → UDOT
statewide; city/station → repo member cities; bill → `ut_state`. The package should make
those three joins first-class, and the caveat table should keep saying what the motion
layer honestly is (an adoption record).

Two hard external limits, now verified, that the schema must respect:

- **No public PIN-keyed obligation/expenditure dataset exists.** UDOT's TIGS layer is
  lifecycle-only (no dollars); Transparent Utah is not PIN-keyed; UDOT's legacy ePM REST
  endpoints 404 (re-resolve via https://data-uplan.opendata.arcgis.com item pages).
  Obligation reality = the **Federal Obligation Report PDFs, which exist online for 2023
  and 2024 only** (both already captured). The obligation layer will therefore be thin
  and honest, not continuous.
- **The models are request-only** (WF-TDM package, HTS microdata). Public = docs +
  derivative services. We catalog, never mirror, never request-gate the build.

---

## 3. Publications & data — inventory verdicts

Full agent catalogs are condensed here into include/defer/exclude verdicts. The single
structural fact: WFRC's entire data surface is **one ArcGIS org
(`services1.arcgis.com/taguadKoI1XFwivx`) with 1,046 public FeatureServices** (Hub front
door data.wfrc.utah.gov curates a subset; vintages are versioned as NEW services, never
overwritten — why 8 TIP vintages were loadable). The repo's 18-layer catalog is a
curated sliver; §3.3 adds the analytically-live remainder. GitHub org **WFRCAnalytics**
(~117 public repos, active) documents the pipelines.

### 3.1 INGEST — structured data targets (new/extended gov.db tables, §4)

| Source | What it carries | Feeds |
|---|---|---|
| 8 in-repo TIP vintages (raw JSON, `pin` field) | project × vintage × forecast-year × cost × status | `project_vintage` + `project_history` (A) |
| **TIP Project Table Listing PDFs** (per vintage; current linked, older at predictable URLs `…/<yyyy>_<yyyy>TIP/…`) | per-project **funding program** (STP/CMAQ/TAP/CRP/state) + year-by-year $ | `project_funding` (A+) |
| Federal Obligation Reports 2023, 2024 (captured) | obligated federal $ per project per FFY | `project_obligation` (A+) |
| **RTP Appendix H** — live Google Sheets phased project list (docs.google.com/spreadsheets/d/1eiiMX_ZeI-_6f8gLD3QxOBnqXlLYv9y6A7EWQLYIvjc) | all RTP projects w/ phase/cost/mode, WFRC's own tabular form | reconciliation + `project_history` RTP side |
| TLC award rollups 2020-2026 (captured) + **TLC Report Card 2024** (captured; carries per-award $) + award news | award × community × year × type (+$ where printed) | `regional_grant` (B) |
| SAP progress updates (Mar-2022 / Jan-2024 / Mar+Jun-2025; 2 captured) + the 15 extracted cert motions + SAP ArcGIS map | station-area pipeline + certification actions | `sap_certification` (B) |
| **CDBG Rating & Rankings XLSX 2023-2026** (direct download) | scored/ranked applicants + awarded $ | `regional_grant` (B) |
| **Legislative Bill Tracker + Appropriations Tracker (Google Sheets, per session + archive)** | WFRC position per bill; requested/funded appropriations $ | `legislative_position` (B) — joins to `ut_state` |
| SAP-TA award lists (in progress updates + packets) | recipient / $ / date | `regional_grant` (B) |

### 3.2 CAPTURE — plans-corpus additions (text layer, existing `plans/` pattern)

Core (high value, ~25 docs): RTP **appendices E, F, G, I, J** (selection criteria,
revenue/cost assumptions, revenue sources, phasing criteria, system performance) + **the
RTP amendments page resolutions** (≥4 — NOTE: this CLOSES the "no RTP amendments log"
gap currently ledgered in `plans/SOURCES.md`; the page exists:
https://wfrc.utah.gov/regional-plans/regional-transportation-plan/adopted-rtp/amendments/);
TIP table PDFs for the older vintages (also the §3.1 parse source); SAP Certification
Policy + Requirements Checklist + the Mar-2025 progress update; **CSAP** (Apr-2024 final
+ exec summary + appendices D/E — focus areas, cost estimates); FY24-FY27 budgets +
FY22-FY25 audited financials (SEFA = per-grant federal $) + UPWP FY26/27 + Activities &
Accomplishments FY22-FY24 (task-level UPWP completion); AQ memo backfill (#27-41; series
runs 27→43a, 2 captured); legislative session wrap-ups 2022-2026; CDBG Consolidated
Plan 2025-2030 + Annual Action Plan (page filenames are SWAPPED — verify on capture).

Optional (second pass): Zero-Fare Transit Study, Transit Fresh Look corridor profiles
(2026), Beehive Bikeways technical docs, RPO long-range plans (Morgan/Ogden Valley +
Tooele Valley — WFRC staffs both), Public Participation Plan, prior-RTP archive
(full docs back to 2007 at /past-regional-transportation-plans/).

### 3.3 CATALOG — GIS additions (link-only, existing `gis/` pattern, ~12 layers)

BIG5 metric services (AccessToTransit/Jobs/Parks, Housing_Jobs_Within_Centers already
present, Median_HT_Index, Affordability) + `WFRC_Dashboard_Metrics_gdb`; `ATO_RTP2023`
successors (the 2020 `AccessToOpportunities` TAZ service carries JOBAUTO/HHTRANSIT/COMP
scores for 2019/2030/2040/2050); `Generalized_Future_Land_Use_(MAG_and_WFRC_2025)`
merge; the statute-geometry layers **SB34MajorTransitInvestmentCorridors,
SB217_TransitBuffers, HTRZs_2025, TODsites** (the legal join surface for HB462/SB34
questions); `usRAP_Veh/Bike/Ped` star-rating segments; `Community_Focus_Areas_2027_RTP`
(EFA renamed "Community Focus Areas" — update the catalog note);
`TAZ_GeographyLookup_082025` (the TAZ↔geography crosswalk); `Traffic_Volume_Historic_
and_Forecast`; `RTP2027_PreferredScenario_062026` (refresh seam, already noted).

### 3.4 DEFER / EXCLUDE (with reasons — ledger these, don't silently drop)

- **Committee packets beyond Council** (Trans Com/RGC/Budget/ATC/JPAC/WFEDD full
  packets): DEFER to Workstream C — high value (the $-rich amendment tables + award
  approvals live there) but bulky; Council packets first.
- **WF-TDM model package, HTS microdata**: request-only — EXCLUDE from acquisition;
  catalog the public docs (wfrc.utah.gov/wftdm-docs/, unifiedplan.org HTS hub).
- **The 1,046-service full mirror, VC_* scenario runs, model QA layers**: EXCLUDE
  (model exhaust, not decisions); catalog pattern documented here is sufficient.
- **HTS frequency tables, 2012 travel study, Utah Moves report**: DEFER (reference
  corpus, low join value).
- **Newsletters, news posts, social**: EXCLUDE (no analytic content).
- **Crash raw data**: UDOT/DPS-side, not WFRC's — out of entity scope.
- **Strava Metro**: licensed, not redistributable — EXCLUDE.
- **CEDS annual performance reports**: not publicly posted (verified) — honest gap.
- **Pre-2023 Federal Obligation Reports**: not online (verified) — honest gap; note
  GRAMA as the only channel, low value.

---

## 4. The structured-database plan (gov.db)

All tables federate with the existing `city`/`gov_level` convention (`city='wfrc_mpo'`),
carry per-row `source_doc`/`source_url` + `confidence` where extraction is non-trivial,
and get `caveat` rows so mis-comparisons surface. Derived, regenerated, never hand-edited
(cardinal rule 3). MAG inherits every table at its smaller scale.

### 4.1 `project_vintage` + `project_history` (Workstream A — zero acquisition)

Long observation table, then a derived summary:

```
project_vintage:  entity, pin, plan_kind, plan_vintage, name, forecast_start_year,
                  cost, status, county, funding_source_raw (mstr_pin_desc), source_layer
project_history:  entity, pin, name_latest, n_vintages, first_vintage, last_vintage,
                  entered_tip, exited_tip (vintage after last-seen, NULL if current),
                  slip_years (last minus first forecast_start_year),
                  first_cost, last_cost, cost_drift_pct, last_status,
                  rtp_plan_id (where matched), counties
```

Build: re-parse `projects/raw/*.json` (the raw attrs carry `pin`, `PROJECT_VA`,
`FORECAST_S`, `PIN_STAT_N`, `MSTR_PIN_D` — richer than the 15-col projects.csv).
Sharp edges: (a) the 2020-2025 vintage is statewide-inclusive — flag non-WFRC counties,
don't let them read as "exited the region"; (b) some rows are OID-fallback where pin was
null — exclude from lifecycle claims, count them in the build report; (c) TIP↔RTP
linkage (pin↔plan_id) only where an explicit attribute or exact-name match exists,
confidence-gated — never fuzzy-guessed. Gates: row counts reconcile to projects.csv per
vintage; pin-coverage report printed; idempotent.

### 4.2 `project_funding` (TIP tables parse) + `project_obligation`

```
project_funding:    entity, pin, tip_vintage, funding_program, fiscal_year, amount,
                    sponsor, source_doc, page
project_obligation: entity, pin_or_null, project_name_raw, sponsor, funding_program,
                    ffy, obligated_amount, source_doc
```

Parse the born-digital TIP Project Table PDFs (pdfplumber-class tabular extraction;
per-vintage layout drift expected — same discipline as county minutes eras). Reconcile
each vintage's PIN set against `project_vintage` (coverage %, printed in build report).
Obligation reports: 2023 + 2024 only (honest ceiling); check whether rows print PINs —
if not, name-match with confidence column, never force.

### 4.3 `regional_grant` (Workstream B)

```
regional_grant: entity, program (tlc|sap_ta|cdbg), cycle_year, recipient_raw,
                recipient_slug (registry match, NULL for non-repo jurisdictions),
                project_title, project_type, amount, match_amount,
                amount_source (report_card|packet|news|null), source_doc, confidence
```

TLC 2020-2026 rollups give recipient/title/type (~180 lifetime awards; 16 repo cities
already named — see `plans/SOURCES.md`); **amounts come from the Report Card + packets +
news, NOT the rollups (verified: rollup PDFs print no $)** — amount stays NULL where no
source prints it. CDBG XLSX 2023-2026 load directly (scores + $ — keep the score columns,
they're the allocation record). SAP-TA from progress updates. Downstream-trace fields
(city minutes/ordinance mentions) are a QUERY pattern via fts_minutes, not columns.

### 4.4 `sap_certification` (Workstream B)

```
sap_certification: entity, station_area_raw, city_slug (nullable), action
                   (certified|denied|extension), decision_date, body (RGC|Council),
                   motion_id (join to motion where matched), plan_title,
                   source (minutes|progress_update|news), confidence
```

Spine: the 15 extracted SAP motions (2022-10→) × the progress-update rosters (127
station areas; 38→72 certified over 2025) × the SAP ArcGIS map. This completes the
HB462 → WFRC → city-SAP → rezone chain: `sap_certification.city_slug` joins to member
cities' motions/ordinances, where the 5-year implementation plans land as rezones.
Multi-station certifications in one motion get one row per station area, same motion_id.

### 4.5 `legislative_position` (new — the advocacy layer)

```
legislative_position: entity, session_year, bill_number, bill_title_raw, position
                      (support|oppose|neutral|track|null-verbatim), notes, source_doc
```

From the Bill Tracker Sheets (current + prior-year archive) + session wrap-ups
2022-2026. **Joins to `ut_state`'s 264-bill subset on (session_year, bill_number)** —
"did the Legislature pass what the region asked for, and how did local legislators
vote?" becomes a two-join query. Cheap, novel, high-value. Positions are Council-derived
("established by Council members who choose to participate") — caveat row says they are
organizational positions, not member votes.

### 4.6 Registry work

Register **`udot`** and **`uta`** as **registered-only** entities (the wasatch_county
pattern): they sit on WFRC's board, hold the PIN system and the transit assets, and are
referenced by `project_*` tables — honest references, no builds. Add `relationships.csv`
edges (member_of wfrc_mpo, external-flag preserved) + regenerate HIERARCHY.md. Document
the pin→STIP statewide expansion path in `wfrc_mpo/projects/SOURCES.md`.

### 4.7 Workstream C — deliberative record

Council **full packets** (53 meetings, same file tree as minutes) → `document` catalog +
FTS (the "why" layer: staff memos, amendment tables, award approvals). Then Trans Com +
RGC packets (where TIP amendments and TLC/SAP awards are actually decided — the Council
motions are often ratifications). Familiar pattern (county packets); bulky; second phase.

### 4.8 Doc corrections surfaced by this research (do with Phase 1)

- `plans/SOURCES.md`: the "no RTP amendments log" gap is WRONG-as-stated — an amendments
  page with resolutions exists (URL in §3.2); re-ledger as "capture queued."
- `gis/` catalog: EFA layer renamed "Community Focus Areas" (2023); 2027-RTP successor
  service exists.
- `wfrc_mpo/CLAUDE.md`: note "Wasatch Choice for 2054" as the 2027-cycle vision name;
  note the obligation-report set (2023+2024) is COMPLETE as published, not partial.
- TLC partner roster drift (SLCo vs GOPB) — record both, don't guess.
- WFEDD designation year discrepancy (2013 vs Aug-2014) — record both.

---

## 5. Sequencing, effort, MAG parity

| Phase | Content | Effort | Acquisition |
|---|---|---|---|
| **1** | §4.1 derivation + §4.8 doc corrections + §4.6 registry | cheap-moderate | ZERO |
| **2** | §3.2 core plans capture + §4.2 TIP-table parse + obligation load | moderate (parse QA is the cost) | ~30 docs |
| **3** | §4.3–4.5 grant/cert/position tables + §3.3 GIS catalog adds | moderate | small (Sheets/XLSX + already-captured PDFs) |
| **4** | §4.7 Council packets → Trans Com/RGC | familiar-pattern, bulky | ~53+ packets |
| **5** | MAG parity pass: same tables from data.magutah.gov (35-dataset DCAT: TIP/RTP/RPO trio, GP land use, Housing Unit Inventory, **MAG Trail Counters** — a dataset WFRC has no open equivalent of) + MAG TLC/SAP analogs | scaled-down template | small |

Phases 1–3 deliver the analytic package; 4–5 complete the record. After each phase:
rebuild `gov.db`, add `caveat` rows, update `coverage.json`, run
`validate_entity.py wfrc_mpo`, and ledger every drop/gap in the module SOURCES.md.
This spec + the built package become the repo's REGIONAL-ENTITY METHOD (future
Dixie/Cache MPO builds inherit).

## 6. Honest-limits ledger (carry into caveat rows)

1. No public PIN-keyed obligation/expenditure data (TIGS = lifecycle only; Transparent
   Utah not PIN-keyed) → obligation layer = 2 FFYs of PDF reports, by construction.
2. TLC per-award dollars are unevenly published → `amount` NULL is a source property.
3. UDOT ePM REST endpoints unstable (404s observed 2026-07-22) → always re-resolve via
   data-uplan.opendata.arcgis.com item pages; never hard-code legacy URLs.
4. Models + microdata request-only → docs cataloged, artifacts excluded.
5. SAP certification counts move fast (38→72 during 2025) → progress updates are
   snapshots; the motion layer is the authoritative action record.
6. `CityArea` is a MODEL geography, not municipal boundary — never equate to city
   totals without the existing projection caveats.
7. Bill-tracker positions are organizational, not member votes.
