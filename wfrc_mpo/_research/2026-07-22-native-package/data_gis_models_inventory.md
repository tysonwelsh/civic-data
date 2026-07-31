# WFRC Structured Data / GIS / Modeling Inventory (verified 2026-07-22)

**The single most important fact:** WFRC's entire GIS/data surface lives in one ArcGIS Online org — `services1.arcgis.com/taguadKoI1XFwivx` — whose REST services root (`.../arcgis/rest/services?f=json`) was fetched and which enumerates **1,046 public FeatureServer services**. The ArcGIS Hub front door is **https://data.wfrc.utah.gov** (title "WFRC Open Data"; alias `data.wfrc.org` — both appear in WFRC's own docs), which curates a subset of those services with multi-format downloads (CSV, Shapefile, GeoJSON, KML, FGDB). A second front door, **https://maps.wfrc.utah.gov** ("over 50 maps and data sets"), indexes the interactive apps. Everything below is verifiable by appending `?f=json` to the service URL pattern `https://services1.arcgis.com/taguadKoI1XFwivx/arcgis/rest/services/<NAME>/FeatureServer[/0]`.

## 1. Open data / GIS presence — significant feature services

### TIP (programmed projects)
| Item | Detail |
|---|---|
| Name | `TIP_2027_2032` (newest; also vintage services `TIP_2026_2031_gdb`, `TIP_2025_2030_gdb`, `TIP_2024_2029_gdb`, `TIP_2023_2028_gdb`, `TIP20222027_gdb`, `TIP20212026_gdb`, `TIP20202025_gdb` — **8 retained TIP vintages**, matching the repo's `regional_project` load) |
| Host | `services1.arcgis.com/taguadKoI1XFwivx/.../TIP_2027_2032/FeatureServer` — layers 0 `TIP_Projects_points`, 1 `TIP_Projects_lines`, table 2 `TIP_Comments` |
| Access | ArcGIS REST (query/CSV/GeoJSON export via Hub) |
| Fields (fetched from `TIP_2026_2031_gdb/FeatureServer/0`) | `pin` (Integer — **the UDOT ePM PIN**), `pin_desc` (Project Description), `proj_typ_nm`, `pin_stat_nm` (Project Status), `forecast_st_yr`, `project_value`, `mstr_pin_desc` (aliased "Funding Source"), `public_desc`, `cnty_name`, `GoogleStreetView`, `GlobalID` |
| Vintage/cadence | New service per TIP cycle (annual); service description on TIP_2027_2032 says verbatim: *"TIP projects, extracted from ePM, presented for the 2027-2032 TIP public comment period."* Layer-edit metadata on the 2026–2031 service: data last edited 2024-12-06, layer edited 2026-01-25 |
| Join keys | **PIN** (→ UDOT ePM/STIP), `cnty_name` |

### RTP (long-range plan projects)
- **`2023_2050_RTP_Roadway_Projects_lines`** (+ `_points`, and sibling `2023_2050_RTP_Transit_Projects_*`, `2023_2050_RTP_Active_Transportation_Projects_*`, roll-up `Final_2023_RTP_Projects`, `RTP_2023_Preferred_Scenario`). Fields fetched (49): `unique_id`, `plan_id`, `name`, `description`, `county`, `jurisdiction`, `route_name`, `route`, `bmp`/`emp` (mileposts), `miles`, `mode`, `improvement_type`, `bike_type_text/code`, `ped_type_text/code`, **`phase`** / `phase_needed` (RTP phasing), `cost` (aliased "Cost 2018"), `cost_phased`, `region` (UDOT Region), `current_lanes`/`future_lanes`, `begin_place`/`end_place`, `pel`, `factsheet`, `at_component`, `cor_pres` (corridor preservation), `status19vs23` (cross-vintage status). Join keys: `unique_id`/`plan_id`, county, jurisdiction, UDOT route + milepost.
- **Draft next cycle:** `RTP2027_PreferredScenario_062026` — fetched; description verbatim: *"Preferred Scenario for the 2027-2055 RTP. Data will be updated as needed."* 6 layers: Transit/Road/AT × PSPoints/PSLines. Dated predecessor snapshots (`RTP2027_PreferredScenario_07302025_gdb`, `_08282025`, `_ForPublicComment_2026`) plus UDOT-coordination views (`RTP2027_PSRefinement_view_forUDOT`, `RTP2027_PSRefinement_Road_forUDOT`) give a visible drafting history.
- `RTP_2019_Centers` and `WFRCForecasts_2019RTP_v831_20200508` preserve the prior plan cycle.

### Wasatch Choice centers & land use
- **`WCV_All_Centers_2023`** (layer `WCVCenters_2023`, polygon). Fields fetched: `CenterName2023`, `CenterType2023`, `CenterType2019` (cross-vintage), `MPO`, `Phase`, `CityPrimary`, `CityOther`, `CatchmentPop`, `NonResFAR`, `DwellingPerAcre`, `IndicatorLU`, `MinRoadway`, `Transit` (optimal transit level), `Walkable`, `Stories`. Join keys: city name (`CityPrimary`), MPO. Related: `Wasatch_Choice_2050_Centers_(Vision_Map)` (the Hub-listed 2050 vision layer), `WCV_Centers_and_Regional_Land_Uses` (LIVE), `WCV_2023_Refresh_*` series, `DraftRefinedCenters`, `WCVCenters_2025ExternalComments` — the 2025 Vision refresh is in-flight. The wasatchchoice.org interactive Vision map is the front-end for these layers.
- **`Generalized_Future_Land_Use_(2025)`** (layer `FutureLandUse2025`, polygon). Fields fetched: `CityLUType` (city's own designation — the "city-faithful" value), `GenLUType` (normalized), `City`, `County`, `MaxDUA`, `PlanYear`, `PlanSource`, `DataSource`, `AnnexArea`. Also `Generalized_Future_Land_Use_(MAG_and_WFRC_2025)` (two-MPO merge) and older vintages on the Hub. Join keys: city, county.
- `Regionally_Significant_Land_Use`, `LandUse_Centers`, `TODsites_gdb`, `HTRZs_2025` (housing & transit reinvestment zones), `HousingSuitability_Centers2025/202512_gdb`, `wfrc_hui_*` (housing unit inventory).

### Equity / community focus
- **`Equity_Focus_Areas_2023`** (layer `CommunityFocusAreas2023` — note the 2023 rename from "Equity Focus Areas" to "Community Focus Areas"). Fields fetched: `Geography`, `Population`, `TotalHH`, `Pov`/`PctPov`/`SD_Pov`/`Pct_Pov20` (poverty share + std-dev threshold flags), `Min_`/`PctMin`/`SD_Min`/`Pct_Min40` (minority share), `HighPct`, `PopDens`, `HighSD`. Census-block-group derived. Next-cycle version exists: **`Community_Focus_Areas_2027_RTP`**. Companion GitHub repo `APP-EquityFocusAreas` (R).

### Transit / station areas
- `Fixed_Guideway_Transit_022025`, `MajorTransitInvestmentCorridors_Jan2024` + `MajorTransitInvestment_Stations`, `SB34_Transit` / `SB34MajorTransitInvestmentCorridors` and `SB217_TransitBuffers_gdb` (Utah statute-defined station-area/transit buffers — join surface for HB/SB station-area-planning compliance), `FrontRunnerStationBuffers`, `FrontRunnerDoubleTrackSections`, `BRT_Stations_and_Buffers`, `TRAX or Streetcar Station Buffers half mile`, `Vision_Transit_Stations_LIVE`, `UTA_FiveYearServicePlan2023_OnDemandAreas`, `Green_Bike_Stations`, `transitlinks`/`transitnodes` (TDM transit network).

### Bike/ped
- `wfrc_bike_map_features_gdb` + `wfrc_bike_map_planned_features_gdb` (the regional bike map, existing vs planned), `Regional_Pathways_102024`, `BeehiveBikeways2024_gdb` (+ comments layer), `Active_Transportation_Lines`/`_Point_Projects`, `NetworkQuality_LTS` (level of traffic stress), `Sidewalk_Inventory_(2016)`, `Traffic_Signals_for_Bike_Comfort_Map`, `Golden_Spoke_Ride_2024/2025/2026`, `TooeleValley*` and `MorganRPO_042026` (RPO-level AT), plus MAG mirrors (`MAG_Regional_BikePed`, `MAG_ExistingBike_gdb`).

### Safety / traffic
- **usRAP star-rating segments**: `usRAP_Veh`, `usRAP_Bike`, `usRAP_Ped`, refreshed as `usRAP_062026` (polyline; fields not exposed in service-level JSON, layer 0 exists). Note: these are risk-rating layers; raw **crash** data is UDOT/DPS-side, not in the WFRC org.
- `Utah_Statewide_Traffic_Volume_Historic_and_Forecast` / `Traffic_Volume_Historic_and_Forecast` (the data behind unifiedplan.org/traffic-volume-map), `SegsWithAADTthru2021`, `Continuous_Count_Station_Locations`, `Roadway_Risk`, `resiliency_*` (resiliency projects/segments), and ~30 `VC_*` volume-to-capacity scenario services (e.g. `VC_Base23_2024_04`, `VC_RTP50_2024_04`, `VC_TIP28_2024_04` — naming encodes scenario + model run date).

### Boundaries / zones
- `Traffic_Analysis_Zones_(TAZ)_(Wasatch_Front)` and `_(Statewide)`, `WFv9_TAZ`, `WasatchFrontTAZ`, `TAZ_GeographyLookup_082025` (TAZ→geography crosswalk), `microzones`/`Microzones_032221` (ABM microzones), `CityOutlines`, `Municipalities(_WithTownships)`, `Counties`, `WFRC_Administrative_and_Planning_Area_Boundaries`, `Utah_MPO_Boundaries_2014`, `REMMBoundary`, `zone_set_WFSmallAnalysisDists`.

**Cadence pattern (observed):** WFRC versions by *new service per vintage* (TIP yearly, RTP per 4-year cycle, WCV per refresh) with dated suffixes (`_062026`, `_102024`) rather than in-place overwrite — old vintages stay queryable, which is why the repo could load 8 TIP vintages.

## 2. Socioeconomic forecasts (REMM outputs)

| Item | Detail |
|---|---|
| Current adopted vintage | **RTP 2023 cycle** — services `{Population, Household, All_Jobs, Retail, Office, Industrial, Typical, NonTypical} Jobs_Projections_(City_Area)` and `_(TAZ)` plus frozen `..._City_Area_RTP_2023` / `..._TAZ_RTP_2023` copies. These are the exact services WFRC's Models & Forecasting page links, and the source of the repo's `projection` table city-area grain |
| City-area fields (fetched, `Household_Projections_(City_Area)/0` = `HouseholdCityAreaProjections`) | `CityArea`, `ModelArea`, `SECategory`, `MAX_RELEASE` (vintage tag), **`SUM_YEAR2015`…`SUM_YEAR2050` (36 annual columns)**, `FIRST_MOREINFO` |
| TAZ fields (fetched, `Household_Projections_(TAZ)/0` = `HouseholdTAZProjections`, 57 fields) | **`TAZID`, `CO_TAZID`** (county-prefixed TAZ id — the join key), `CO_FIPS`, `CO_NAME`, `CityArea`, `ModelArea`, `DEVACRES`, `RELEASE`, `SECategory`, `YEAR2015`…`YEAR2050`, change columns `CH15TO50` etc., density variants `YEAR20xxD`, `IntPtPerKM2` |
| Draft next cycle (RTP 2027) | In the same org: `Forecasts_SE_RTP2027_Feedback` (jurisdiction-review feedback service; the RTP2023 twin `Forecasts_SE_RTP2023_Feedback_new` shows the recurring workflow), `RTP27`-suffixed geography sets `COUNTY_RTP27_gdb` / `DISTMED_RTP27_gdb` / `DISTSML_RTP27_gdb` / `CITYAREA_RTP27_gdb` / `TAZ_RTP27_gdb`, and GitHub `GIS_SE2025_H3` ("SE2025 H3 Socioeconomic Data Smoothing", active Jul 2026) — the SE2025 base-year/H3 workflow for the 2027–2055 plan. MAG's side: city-level SE forecast to **2055** in three RTP phases (2027-36 / 2037-46 / 2047-55), viewer at magutah.gov/se-forecast-viewer |
| Vintage history | `TAZ_SE_Forecasts_May_2015`, `WFRCForecasts_2019RTP_v831_20200508`, `StatewideForecasts_20200608/_withDixie/_withSummit/_withCache` (2020 statewide set), `Pop_Emp_Projections`, `Proj_TOTHH`/`Proj_TOTEMP`/etc., plus statewide grains `STATEWIDE_{CITYAREA,COUNTY,DISTLRG,DISTMED,PLANAREA,TAZ}_gdb` |
| REMM itself | **github.com/WFRCAnalytics/REMM-v3.0** (public; UrbanSim-based; active 2026-05) — production model was v2.x per the WFRC site, v3.0 is the public rewrite. Supporting: `REMM_Policy_Override_Polygons_gdb` service, `DATA-Historical-Parcels` repo, docs Google Doc linked from wfrc.utah.gov/programs/models-forecasting/. Contact: analytics@wfrc.org |
| Front-end | Household & Job Forecast viewer: wfrc.utah.gov/household-job-forecast-map/ |

Join keys: `CityArea` (≈ the repo's city-area grain — note it is a *model geography*, not exact municipal boundary), `CO_TAZID`/`TAZID`, `CO_FIPS`.

## 3. Wasatch Front Travel Demand Model (WF TDM)

- **Maintainer:** WFRC + MAG jointly (confirmed on wfrc.utah.gov/programs/models-forecasting/). Runs in **Cube Voyager**. Current production **v9.2.0** (reflects RTP Amendment #4); **v10.0.0 documentation is live**, and `WFv1000_MasterNet_20250821___Link`/`___Node` services show the v10 master network published Aug 2025.
- **Distribution:** the model itself is **request-only** (contact Suzie Swim, suzie.swim@wfrc.utah.gov) — not a public download. Documentation is fully public at **https://wfrc.utah.gov/wftdm-docs/** (versions 7.x→10.0.0: What's New, Validation Report, Model Process Report, Data Dictionary; fetched and confirmed no model download there).
- **Public structured outputs (verified in the AGOL org):** the `VC_*` V/C scenario layers (TIP/RTP/no-build/unfunded, 2019 base → 2050, run-dated), `Traffic_Volume_Historic_and_Forecast` + `Utah_Statewide_Traffic_Volume_Historic_and_Forecast` (segment volumes, historic + forecast — powering unifiedplan.org/traffic-volume-map), `Master_Segs_withForecasts_WFRCMAG_20211109`, `wfsegs20211117`, `WFv901_Segments`, `AverageTAZCommuteTimes`, `TravelSheds_gdb`/`TravelSheds_RTP2023_gdb`, model-QA comparison layers (`TDM_Daily_Volume_Comparison__v8_3_2_vs_v8_3_1_`). Transit ridership forecasts are a stated model product but published mainly through plan documents/vizTool rather than a standalone service.
- **GitHub (github.com/WFRCAnalytics, ~117 public repos):** `WF-TDM-Runs` ("reproducible, traceable, and publishable Cube Voyager model runs", active Jul 2026), `vizTool` (JS model-output viewer, beta), `TDM-GEO-AnalysisZones` ("source of truth for TAZ and MAZ"), `TDM-GEO-TrueShape` (network true-shape from UGRC centerlines), `TDM-INP-K-12-Enrollment`, `TDM-INP-College-Enrollment`, `DATA-Commercial-Vehicle-Observed-for-TDM`, `TDM-VAL-ModeShare-Boardings`, `TDM-VAL-Scenario-Comparison-Toolbox`, `GIS-GTFS-vs-LIN`, `DEMO-OpenPathsCube-Conversion`, `DEMO-quarto-tdm-report`.
- **Next generation:** Activity-Based Model implementation began March 2026 (framework PDF + "ABM Quick Guide" 2026-04-23 on wfrc.utah.gov); `ABM-INP-Microzones` repo + `microzones` services are its zone layer. Statewide model (USTM) zones appear as `simplified_USTM_TAZ_2021_09_22`. Community: utahmug.org (Utah Model Users Group).

## 4. UDOT ePM "PIN" linkage

- **Verified:** WFRC TIP services are *extracted from ePM* (service description, quoted above) and carry `pin` (Integer) — so the repo's TIP rows can key directly to UDOT's statewide project system.
- **Statewide PIN-keyed public data:** UDOT Open Data portal **https://data-uplan.opendata.arcgis.com** (ArcGIS Hub; "All Projects" map item ff0d0dbb65344331ace85118ae993d0e; tag `epm`). Documented behavior: ePM point + line layers, **refreshed nightly/daily**, "EPM - All Projects" shows all PIN statuses except Abandoned; "ePM - STIP Projects" shows proposed + funding-approved (RegionPriority=888). **Flag:** the legacy REST paths (`maps.udot.utah.gov/arcgis/rest/services/EPM_AllProjects/...` and `/central/rest/services/EPM/EPM_AllProjects/...`) returned **404 on direct fetch today**; the `/central/rest/services/EPM` folder now lists only `EPM/STIP_2023` and `EPM/STIP_2024` MapServers — UDOT has been shuffling these endpoints, so treat the **Hub item pages as the stable access path** and re-resolve the backing service ids from there.
- **STIP:** the STIP is published via ePM report tooling ("Program Project Report") + the STIP_20xx MapServers above; no independent non-ePM STIP database found.
- **Obligation/expenditure by PIN:** UDOT's **TIGS** service (`maps.udot.utah.gov/central/rest/services/TIGS/MapServer`, fetched) is the "Transparency in Government Spending" project layer — sourced from ePM, daily refresh, project lifecycle status — but its service metadata exposes **no expenditure amount fields**; actual dollar records live on the state's Transparent Utah portal keyed by state finance codes, **not PIN**. **Flag: no public PIN-keyed obligation/expenditure dataset was verifiable.** Project *value* appears only as coarse strings (`project_value` in the TIP layer; cost fields in RTP layers are planning-level estimates).

## 5. Surveys, counts, ATO, performance measures

- **2023 Utah Moves Transportation Survey** (household travel survey; MPOs+UDOT+UTA, RSG): 9,799 households / >25,000 persons, plus a university supplement (1,300+ students, 8 institutions) and a 3,250-respondent follow-on (attitudes, long-distance). Public products at **unifiedplan.org/household-travel-surveys/**: final report (rev. 2024-06-10), **frequency summary tables (23 MB, with geographic breakdowns)**, dataset guides/codebooks (core + follow-on), weighting memos (v1 2024-03, v2 2025-07), and two Shiny data explorers (`wfrc.shinyapps.io/2023-utah-household-travel-survey/` and `...-trip-length-distribution/`). **Microdata is request-only** (researcher inquiries → bgranberg@wfrc.org). Prior surveys: 2012 statewide HTS (report public). *(The dataset-guide deep URL 404'd; the hub page above is live.)*
- **Bike/ped counts:** thin as open data on the WFRC side — `Continuous_Count_Station_Locations` service + GitHub `DATA-Continuous-Count-Station` / `DEMO-Jupyter-Notebook-CCS-Data` (UDOT CCS data workflows); UDOT has Active Transportation Counters and WFRC licenses Strava Metro (not redistributable). **MAG is ahead here: a `MAG Trail Counters` dataset is on data.magutah.gov** (CSV/GeoJSON/etc.). UDOT traffic-side: AADT/VMT statistics, Freeway PeMS (`udot.iteris-pems.com`, 5-min bins), ATSPM (`udottraffic.utah.gov/atspm`); ClearGuide is access-restricted.
- **Access to Opportunities — yes, released as data:** `AccessToOpportunities` service (TAZ-based, work-related, "Updated August 2020"; layer `ATO` fields fetched: `TAZID`/`CO_TAZID`, `DEVACRES`, then per-horizon `HH_19/JOB_19`, **`JOBAUTO_*`, `HHAUTO_*`, `JOBTRANSIT_*`, `HHTRANSIT_*`, `COMPAUTO_*`, `COMPTRANSIT_*`** for years 2019/2030/2040/2050 — job/household access by auto and transit + composite). Successors: `TAZ_ATO_RTP2023`/`Areas_ATO_RTP2023`/`ATO_RTP2023_gdb` (note: `TAZ_ATO_RTP2023` layer 0 is geometry-only — scores live in the companion services), `Access_to_Parks_and_Trails_2024`, `Households_within_20min_Walk_to_{Parks,Trailheads,Transit}_by_TAZ`, and the **BIG5 metric services** (below). Tools: wfrc.utah.gov/ato-map/, housing-ATO calculator map; GitHub `ATO-Impact-Tool` + `ATO-Recalc-Exploration`.
- **Performance measures:** federal PM1/PM2/PM3 reporting is narrative (RTP Appendix J) + **UDOT Federal Measures Hub** (`federalmeasures-hub.udot.utah.gov`); WFRC's own tracked measures are the **Wasatch Choice "Big Five" progress indicators** (wasatchchoice.org/resources/progress-indicators/) with data services `BIG5_AccessToTransit_Metric_gdb`, `BIG5_AccessToJobs_Metric_gdb`, `BIG5_AccessToParks_Metric_gdb`, `BIG5_Housing_Jobs_Within_Centers_gdb`, `BIG5_Median_HT_Index_gdb`, `BIG5_Affordability_MedianIncome`/`_HT_2`/`_HT_3`, `Walk_Access_To_Public_Daily_Transit_10min_Metric_gdb`, plus `WFRC_Dashboard_Metrics_gdb` / `WFRC_PerformanceMetric_Boundaries` and GitHub `DATA-Regional-Metrics-Dashboard`.

## 6. GitHub — github.com/WFRCAnalytics

~117 public repos (100 on page 1 + 17 on page 2 of the org API). The org is genuinely active (multiple pushes the week of 2026-07-21). Naming convention encodes purpose: `TDM-*` (model), `TDM-INP-*`/`ABM-INP-*` (inputs), `TDM-VAL-*` (validation), `GIS-*`/`GIS_*`, `DATA-*` (reusable data pipelines), `APP-*` (web apps), `DEMO-*`. Most reusable:

| Repo | Why it matters |
|---|---|
| `REMM-v3.0` | The REMM (UrbanSim) implementation itself, public |
| `WF-TDM-Runs` | Publishable Cube Voyager run management — closest thing to public TDM outputs |
| `TDM-GEO-AnalysisZones` | **Source of truth for TAZ/MAZ geographies** (the join key for all TAZ data) |
| `GIS_SE2025_H3` | SE2025 forecast smoothing — the RTP-2027 SE vintage in progress |
| `ATO-Impact-Tool` | ATO change assessment |
| `BDM-Utah-Bike-Demand-Model` | Utah Bike Demand Model |
| `APP-Commute-Explorer` / `APP-WFRC-Commute-Patterns` | LEHD commute-flow explorers (DuckDB-WASM + H3) — pairs with `LEHDCommutePatterns20xx` services |
| `DATA-Continuous-Count-Station`, `DATA-Commercial-Vehicle-Observed-for-TDM`, `DATA-Historical-Parcels`, `DATA-IPUMS-Time-Series` | Data pipelines with fetchable inputs |
| `GIS-TIP-Public-Comment-Processing` | TIP comment workflow (pairs with the `TIP_Comments` table) |
| `vizTool` | The TDM output visualization front-end |

No separate "WFRC" org found; WFRCAnalytics is the one that matters.

## 7. MAG equivalents (brief)

- **Portal:** **https://data.magutah.gov** ("MAG Data Portal", ArcGIS Hub; `data.mountainland.org` 301-redirects there). DCAT feed fetched: **35 datasets**, all multi-format (CSV/SHP/GeoJSON/KML/FGDB/Excel/GeoPackage). AGOL org: `mountainland.maps.arcgis.com` (services on `services2.arcgis.com`).
- **Key datasets (from the DCAT feed):** `MAG TIP Projects`; `MAG 2023 RTP Highway/Transit/Active Transportation Projects` (points+lines); `MAG 2023 Unified Plan Data`; `Wasatch Back RPO 2023 Projects` (the TIP/RTP/RPO trio matching the repo's mag_mpo `regional_project` rows); `General Plan Land Use 2025`; `MAG Housing Unit Inventory`; `Utah County Parcels for Modeling`; `Population/Employment Projections by City`; `Traffic Projections (Utah, Summit, Wasatch Counties)`; **`MAG Trail Counters`** (no WFRC open equivalent); trails/bike lanes.
- **Modeling:** co-maintains WF TDM with WFRC; city-level SE forecast to **2055** in RTP phases 2027-36/2037-46/2047-55 (SE Forecast Viewer: magutah.gov/se-forecast-viewer); traffic forecast/LOS/transit-ridership outputs are **contact-the-analyst** (Tim Hereth), not open downloads. MAG mirror layers also sit inside WFRC's org (`MAG_LandUse_gdb`, `MAG_Roadway/Transit/AT_*`, `Generalized_Future_Land_Use_(MAG_and_WFRC_2025)`), so two-MPO merges are often easiest from the WFRC org.

## Flags / unverifiable items

1. **UDOT ePM REST endpoints are unstable** — both legacy `maps.udot.utah.gov` EPM layer URLs 404'd on direct fetch despite being search-indexed; only `EPM/STIP_2023`+`STIP_2024` remain in the `/central` EPM folder. Use data-uplan.opendata.arcgis.com item pages to re-resolve.
2. **No public PIN-keyed obligation/expenditure dataset** — TIGS (ePM-sourced, daily) tracks project lifecycle, not dollars-obligated; Transparent Utah is not PIN-keyed.
3. **HHTS microdata** is request-only; only summary tables + explorers are open.
4. **WF TDM model package** is request-only (docs public, model not).
5. `data.wfrc.utah.gov`'s DCAT feed truncated on fetch (12 of many datasets returned) — the services-root enumeration (1,046) is the authoritative census; the Hub curates a subset.
6. GitHub page-1 repo list was summarizer-truncated (~17 of 100 names captured); total count (~117) is solid, full enumeration would need `gh api` pagination.
7. Field lists above are exact where marked "fetched"; services described only by name (e.g. `usRAP_*` attributes, `Roadway_Risk`) were not field-verified.
