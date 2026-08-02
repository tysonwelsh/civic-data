# LEADS — options, expansion menus, and watches (created by the 2026-07-31 restructure)

**This is a MENU, not a queue.** Nothing here is owed; not doing an item is never a defect.
No checkboxes. Each bullet = date + what was observed + where the evidence lives. Agents: file
new leads HERE (one line each), never in TODO.md; a lead is promoted to TODO.md [DEBT] only
after verification at the primary source shows a wrong or missing value (≤3 promotions per
session). Prune freely at triage; full pre-restructure context for every bullet is in
`TODO_ARCHIVE.md` (anchor 2026-07-31-RESTRUCTURE) — old TODO.md line refs are noted as (L…).

## Capability options (build-when-valuable)

- **State-tier reintegration on its own terms** — owner-gated design task; tracked in TODO.md
  [GATED]. (L998)
- **WFRC-native holistic package, Phases 2–5** — plans capture + TIP funding parse,
  grant/cert/position tables, packets, MAG parity. Spec: docs/history/WFRC_NATIVE_SPEC.md. (L1434)
- **County content menu** (no county has enrichment modules yet): RDA/CRA project-area plans +
  tax-increment financials; interlocal & development agreements; legislative matter catalog;
  county campaign finance; CIP/impact-fee plans; building permits/housing starts. (L1492–1545)
- **Cross-tier analytical views** — county land-use actions ↔ member-city actions; RDA areas
  overlapping cities. The 4-tier model's headline promise has no shipped query surface. (L1547)
- **County Council rosters** — the roster layer generalized to counties. (L1549)
- **County referral / v_pc_divergence extension** — the referral layer is city-only today; the
  flagship divergence query silently returns nothing for counties. (old Phase-6 residual)
- **Disposition classifier for the remaining non-city entities** — salt_lake_county, summit,
  utah, weber, wfrc are at 0 (cache 2,949 + mag 577 are done); until then the per-entity
  coverage statement in CLAUDE.md + caveat rows are the guard. (L1304)
- **Legislator party/district backfill** — `person` has neither column; "how did Republicans
  vote on the ADU bill" is unanswerable in-db against 27,887 state votes. (L1372)
- **ut_state residuals** — 2025/26 committee-vote (mtgvotes) linkage; special-session sweep;
  AOs #102/#206 Wayback-dead + #142/#145 image-only; late-2025 AO series watch. (L1371–1375)
- **MPO residuals** — WFRC historical seat-tenure roster; MAG ~15 surname-only movers 2014–19;
  RTP2027 refresh seam (both MPOs); wfrc 2016 .WMA audio. (L1375–1378)
- **Draper campaign-finance structuring** — 125 filings (116 scanned) acquired but no
  structured layer; draper + slc are the only 2 of 31 cities absent from cf_cycle. (L2620)
- **Transcript/audio program** (owner-gated scope): Whisper leads — park_city 194 caption-less
  videos; taylorsville (audio-only city); copperton ×3; magna ×5 + 370 PMN MP3s; alta 348
  SoundCloud + 172 YT; st_george 2024-10-10; kearns 218 MP3s; EC 211 MP3s; holladay 75
  SuiteOne; SSL cliff-year videos; riverton 652 clips (2025-12-16 tie-break top candidate);
  draper/midvale/CH full harvests; the [OPTION] backfills provo 740 / west_jordan 647 /
  orem 111 / lehi URL-map. Owner ruled transcripts SAMPLE-ONLY 2026-07-05. (L1849, L2233…2740)
- **Spoken-comment transcript layer** for no-published-comment cities — XL, unpriced. (L1849)
- **Primary-document watch list** — cost/benefit gate before admitting any new doc class. (L1114)
- **Referral-guard rollout beyond ogden** — opt-in params proven no-op by default; enabling
  elsewhere needs per-city evidence review. (L1793)
- **Six-city prior-geometry acquisition** — 2019/2020 SLCo VistaBallotAreas snapshot would
  upgrade the LOW pre-2022 maps (WJ/tay/SJ/sandy/WVC/SLC). (L3146)
- **Roster boundary depth** — historical district-geometry acquisition, 7 of 9 done. (L1714)
- **gov-sample.db / gov-lite.db** — smaller release artifacts; the ~1.18 GB FTS content
  duplication in gov.db is the size lever (breaks snippet() — weigh before pursuing). (review)
- **fetch_new hardening idea** — Wayback-listing sweep for delisted-but-served CMS docs (the
  CH pattern). (L3013)
- **PMN JSON-POST/X-CSRF search channel** — fold into pmn_crosscheck/refresh tooling. (L1308)

## Acquisition backfills (bounded, source-dependent)

- **Phase-4 counties**: per-city election re-point to the 6 new county canonicals (evidence
  banked for 8 cities; the 7-city general half of L3200 lives here too); utah_county PC
  minutes 46 meetings 2020–24 (host NXDOMAIN); OCR-gated depth backfills (cache 2015–20 +
  1995–2014, weber 2000–2014, summit pre-2023); elections residue (cache 2024 image-only +
  GEMS eras, weber GEMS grids); summit PMN-1503 + 14 image-only PC minutes; cache PC 14
  minutes-less dates (PMN 1479); weber WWPC-2020 GRAMA; weber planning FTS→votes promotion;
  summit HA/RDA build-later. (L1282–1308)
- **COUNTY-ACQUISITION WAVE LEADS (2026-08-01 — 9-agent wave; per-county evidence in each
  `<county>/campaign_finance/RECON.md`/`AVAILABILITY.md` and
  `salt_lake_county/elections/RECON_COUNTY_2026-08-01.md`):**
  - *Metro-township CF (HIGH — closes a caveat):* SLCo clerk `metro-township-councils/` page
    holds 297 plain-GET PDFs (millcreek 75, magna 64, kearns 47, copperton 32, brighton 30,
    emigration_canyon 26, white_city 23, mostly 2016) + 57 EasyVote metro filings 2023/2026 —
    likely closes kearns `cf-blocked-cycles` (11 proven-existing filings) and adds below-floor
    city CF for 5 entities.
  - *SLCo CF 2016–2021 itemized (portal b):* BigIP-blocked to scripting; recovery = browser
    automation against the known `/Report/{id}` pattern, or GRAMA (turnkey).
  - *SLCo even-year canvass holds 56 MUNICIPAL contests below city data floors* — millcreek's
    2016 founding elections (mayor + 4 districts, primary+general), all five metro-township
    founding contests, INCORPORATION OF MILLCREEK (2012), Brighton incorporation (2018), CH
    2004 incorporation-era races, city bonds/props — parsed + gate-verified already, sitting
    in `contest_inventory.csv` with `retained=no`; regenerate via `--full`.
  - *election_race promotion, other counties:* summit/weber/utah/juab county-office tallies
    already in `election_result` have no audited `election_race` rows (SLCo now does — the
    Package-A pattern is the reference).
  - *City-CF acquisition feeds found in the state tree:* Logan (cache_2013/15/17/19/21/23
    folders — logan has NO campaign_finance dataset), Ogden (weber_2013 Municipal_Ogden +
    Wayback `documents/2016/*_ogden.pdf`), plus 16 SLCo cities' odd-year folders.
  - *GRAMA candidates:* juab 4-ask package (clerk contact in its AVAILABILITY.md); weber's 33
    county-published-then-lost 2018/2020 interim reports (names/dates citable from the
    captured portal table); washington `outpost` unlistable 2018–2022 folders (file-list ask).
  - *Shared CF form families worth building (specs in each agent's report/RECON):* the
    STATEWIDE 17-16-6.5 county sheet (juab carr_5_5_pg = wasatch's 65 older filings; summit
    variant has REVERSED Current|Last|Cumulative columns — a naive parse is silently wrong);
    `wasatch_disclosure_tableab` (44 born-digital); `weber_polimorphic` (5 born-digital with
    machine-readable itemized rows); `cache_cfd` (2022+, needs per-FILING is_incremental —
    a driver capability gap); `washco_split` (3-file filings + an `.xls` reader — 2014/2010
    hand-verified to reconcile exactly); `utahcounty_schedab` (2 modes). Driver finding to
    respect: is_incremental can vary per sheet-type within one filing (washington).
  - *Vision-transcription queue (owner scope decision):* office-line-only first tranche is
    the cheap high-yield move (utah 19 + washington 48 office-unresolved rows);
    full-dollar tranches: juab 18, wasatch 40, summit 20, washington ~90,
    utah ~249 scanned, SLCo 2022-cycle EasyVote PDFs + legacy era. `cf-vision-transcribe`
    needs a county-tier entry point (several county modules have no build_finance.py).
    ✅ **cache_county DONE 2026-08-01/02** — 171 caches over 213 ledger rows; offices
    resolved (128 illegible → 0; 234 county_confirmed / 5 undetermined, those 5 blank on the
    filing itself), 11 rows re-classified out on page evidence, both Rhodes false-positive
    flags adjudicated, and every filing's own stated totals transcribed (210/212 figures).
    Method notes worth reusing: transcribe ONCE per sha256 and apply via `applies_to`;
    screen `last+this=cumulative` to surface misreads (all 17 hits were filer arithmetic —
    zero transcription defects); render faxed pages at ≥600 dpi (a two-stroke open "4"
    reads as "1," at 150–200 dpi).
  - *Cache CF next step (the only remaining Cache CF work):* **itemized donor/vendor rows.**
    `contributions.csv`/`expenditures.csv` are header-only. The 2022+ born-digital
    `cache_cfd` subset is the tractable slice (Schedule A/B free-typed one-liners split on
    ` - `); the pre-2022 Carr era is handwriting and would need a second vision tranche.
  - *Tranche 3 (itemization) ENRICHED SPEC (2026-08-02, owner design session — the Green
    Book "enriched pipeline" pattern):* when the donor/vendor itemization tranche runs,
    (a) **row-level bounding boxes are mandatory in the vision cache contract** —
    coordinates stored (page, x, y, w, h, dpi), crops derived on demand, never
    pre-generated (IIIF-style evidential anchoring; library-science: coordinate-anchored
    transcription / ALTO-PAGE-XML lineage); exact geometry free from `pdftotext -bbox`
    on born-digital, model-estimated on scans; (b) **dual-channel line matching as the
    acceptance gate**: tesseract line-segmentation proposes geometry (its boxes are usable
    on handwriting even when its characters aren't), vision transcribes, then
    crop-and-re-read must reproduce donor+amount — with the CORRELATED-ERROR caveat
    (agreement-gating kills stochastic hallucination, not systematic misreading: the
    Rhodes 4-vs-1 fax specimen, cache CLAUDE.md) and a resolution-escalation rule
    (disagreement or low-contrast → ≥600 dpi + sibling-copy check); (c) arithmetic
    reconciliation vs the tranche-2 stated totals as the truly independent gate;
    (d) formalized human-review checkpoints on the summit-audit model; (e) parser
    families first (the born-digital third costs no vision at all), tiered models on the
    scan remainder. Phase-A engineering residuals for Phase B (families agent + sweep,
    2026-08-02): the tableab family needs a DATE-GRAMMAR extension ('17 Jan 2026',
    '1.2.26', '5May26' currently field-shift — sides withheld, see the calibration
    specimen); summit needs the PERIOD-vs-CUMULATIVE itemized-grain design decision
    (Harte-2026 class: ledgers sum to Current, cover states Cumulative — rows withheld
    with both figures named); summit 2014 wrapped contributor rows need `pdftotext
    -bbox`, not regex; multi-report PDFs (Park 2024-11) need one index row per bound
    report. Calibration-sample prerequisite BUILT 2026-08-02:
    `_audits/cf-calibration-suite/` (13 specimens + pass protocol; every configuration
    must pass before bulk rights). Phase A launched 2026-08-02 (shared families agent +
    this suite); Phase B (vision itemization waves) awaits per-wave owner approval.
  - *County cycle_totals design (DEFERRED BY DESIGN 2026-08-02 — cf_cycle stays
    city-only):* the vision wave proved the generic city rules would publish wrong county
    figures: regimes vary per CANDIDATE not per form (wasatch: three 2024/2026 filers
    restate cumulatively on the period sheet), officeholder carryover inflates cumulative
    totals (weber Harvey/Hatch/Froerer open from prior-cycle closings — 'raised in cycle
    N' must subtract the opening column), same-period amendments are mutually inconsistent
    (SLCo sheriff $68,605/$38,236/$31,019 overlapping April-5 reports), and cache's
    is_incremental varies per filing. A county rollup needs per-candidate regime
    detection + carryover subtraction + the supersede pairs (weber Froerer 2022 'Amended',
    Gibson 2026-07-23 re-file) — design task, per-county evidence in each AVAILABILITY.md.
  - *SLCo GRAMA addendum (2026-08-02):* 6 damaged/blank source PDFs incl. the wholly-blank
    dwilde_apr52006.pdf and two xref-broken files proven damaged AT SOURCE (re-fetch
    byte-identical) — fold into the SLCo portal-era GRAMA ask.
  - *Crop-defect date sweep (2026-08-02):* summit's audit proved the improvised top-80%
    render crop silently blanked signature dates (45 of 51 "blank" dates were legible at
    full page; 1 populated date misread). Elevated blank-`filing_date` rates elsewhere:
    utah_county 62/265, washington 19/206 (washington's older variant genuinely lacks a
    date line — separate the form property from the crop loss before re-reading).
  - *Tooling gaps:* `validate_finance.py` has no conformance mode for document-only CF
    modules; SLCo cycle_totals.csv not yet derived from its EasyVote structured layer;
    the desktop `normalize_sovc.py` could adopt the repo's new families E/G + SpreadsheetML
    reader (port is one-directional today).
  - *Small evidence-cited observations (verify before working):* summit 2014
    Recorder/Surveyor contest absent from `summit_county/elections/election_results_by_contest.csv`
    though two 2014 filings state candidacies (Richards, Trussell); weber
    `election_results_by_contest.csv` "Harvey, Jim" vs filings' "James H. 'Jim' Harvey"
    (4 lost joins); utah_county 2008 listing files Ellertson under Seat B, filename says
    SeatC (recorded, unadjudicated); 45 weber municipal filers later sought county office
    (career-path join).
- **County school-board CF — ledgered, out of scope (owner ruling 2026-08-01)**: the county
  clerk channels carry local school-board filings on the same forms as county offices; every
  county-acquisition wave agent classified them out by the in-form office line and LEDGERED
  them for zero-recon re-acquisition — utah_county `out_of_scope.csv` 89 rows (URL+sha256),
  washington `excluded_school_board.csv` 345, wasatch `out_of_scope.csv` 32, summit ~110
  enumerated (county page + state 2008 folder), weber 91+ identified in `RECON.md`, juab
  school-board raws already on disk. Any build first needs a modeling decision — school
  districts are not repo entities (no boards/votes/elections to join money to).
- **Below-floor / pre-2020 CF vision tranches** (murray 2017/19, magna 2016–19, etc.); CF
  acquisition riders (CH Prazen final, riverton Pierucci 10-24-23, kearns 2023/2025 blocked
  cycles — 11 filings proven to exist, magna 2023, bluffdale Robbins Oct-26, taylorsville
  received-stamp dates + 2025 re-probe + 47 annual itemizations). (L2822, L2878, L2503, …)
- **Per-city residuals** (each honestly ledgered in the city's own AVAILABILITY/unrecovered
  files): park_city captions; nephi PMN body-1788 ordinance harvest; vineyard 2023 CF
  (CMS-purged; re-fetch if re-posted); logan 2023 CF (unrecoverable online) + Ord 26-12
  next-fetch capture; orem Drive-archive packets 2020–21H1 + BoA minutes (owner-gated) +
  ordinance re-crawl; ogden CF 2025 (unpublished; re-fetch when posted); alta pre-2021
  ordinances; copperton OCR-upgrade lead + R2025 codification lag + purged-PMN file-IDs;
  magna CRA 2025-11-18 approved-copy re-check; kearns 2022-11-14 mis-filed audio→minutes
  check + 'Thomes'→'Thomas' person fold + 26 uncodified instruments; white_city 2025 CF
  vision + ~68 uncodified ordinances; SSL 429 index-only packets; holladay PC 2020/21/23
  minutes (89 unrecovered rows) + 102 motion-attested ordinance rows; CH ARC + Appeals
  Hearing Officer bodies (new-body modeling) + Ord 392/455/456/457 gaps; midvale ordinance
  gaps (106 year-only rows); riverton oversize exhibits (83 permanently 403); draper
  election-record notes + oversize exhibits + 2024-07-16 CRA packet; herriman caption fetch
  (~51 videos) + legacy S3 packet mirror (1.7 GiB) + 12 ordinance series holes + Appeal
  Authority body (2 docs); murray caption fetch (86 videos) + ordinance text gaps;
  taylorsville town-hall merges + precinct-derived districts (no official GIS exists) +
  2026 pending minutes + ordinance back-catalog. (L2233–2709, L1907/1911/1987)
- **Ogden referrals FP class** — two named CRAs sharing the generic 'Community Reinvestment
  Project Area' string. (L1801)
- **2026-07-31 (G8b wave): the vacated-date recovery class** — removing 17 phantom
  duplicate-ingests exposed ~10 REAL meetings whose minutes are genuinely unpublished, each
  ledgered in its entity's minutes_unrecovered.csv: weber 2021-06-01 (county mis-post, both
  channels verified), nephi 2024-10-01, vineyard PC 2023-04-19 (GRAMA-only), CH 2025-05-06
  (portal slot serves the wrong file, verified live), WVC PC 2024-07-10 + 2025-04-16, magna
  PC ×4 (approved but never posted; audio exists), summit ESPC 2022-08-04 (PMN body 1503),
  herriman 2021-03-12. Recovery channels: next-refresh re-probes, PMN, GRAMA drafts.
- **2026-08-01 (owner query test): donor-alias normalization** — `donor_normalized` does not
  merge organizational aliases: the Salt Lake Board of Realtors appears as three variants
  (SALT LAKE BOARD OF REALTORS $255,262 / SL BOARD OF REALTORS $29,050 / BOARD OF REALTORS
  $28,201 — likely one org, ~$312.5k combined, the collection's largest external donor by
  ~5×). A donor-alias crosswalk (like the candidate-name one) would make cross-city donor
  aggregation trustworthy without hand-merging; same class as the Natalie Hall casing note.
- **2026-08-01 (murray audit residuals):** PC extractor classes — the footer-RE misses the
  'Planning Commission Meeting Minutes /' header variant (B1) and the motion tail drops
  when the result sentence shares its physical line (B2); both classes' disposition impact
  is already corrected via overrides, so these are extractor polish, not open debt. Plus a
  vocabulary nuance: murray's 'The motion failed for a second' stores outcome='Fail' not
  'Died' (impact nil for carriage tests; a Died-class census undercounts murray by 2).
- **2026-08-01 (bluffdale residuals):** 9 motions still anchor-less (genuine OCR garble +
  one 'NOMINATED' verb-less motion — honest); referral RECALL now partially addressed by
  the census (precision 100%) but un-linked true referrals were not exhaustively hunted.
- **2026-08-01: lehi referral census** — bluffdale's ground-truth pass found its high-tier
  referral precision far below quotable (269→62 links); the failure mode (singleton-heavy
  apps + city-hall address in boilerplate) is generic, and lehi holds the LARGEST referral
  layer (~450 links) with no tuning pass ever run. Census lehi before quoting its chains.
  Unverified lead — do not act without the same ground-truth method.
- **2026-08-01: voting_method vocabulary crosswalk** — three RCV tokens coexist in
  election_race ('RCV' / 'ranked choice' / 'ranked choice (RCV)'); a crosswalks/ entry (not
  in-place edits) would make "which races were ranked-choice" one query.
- **2026-07-31 (weber residual): possible 2022-01-11 redate** — min_01112022.pdf prints
  'Tuesday, January 18, 2022' in its title block and the county lists NO 01-18 meeting
  anywhere; warrant-sequence evidence suggests a clerk header typo in a real Jan-11 meeting.
  Unresolved observation, deliberately not acted on; details in weber_county/CLAUDE.md.
- **2026-07-31: mag_mpo named-dissent parsing** — the G8a grammar fix recovered divided-vote
  result sentences that sometimes NAME dissenters (2015-11-05 twelve named nays; 2014-09-04
  three named + one abstain). Parsing those rare sentences into `vote` rows would give MAG a
  small honest named-dissent layer; today they live verbatim in `result_raw` only.
- **2026-07-31: wire comment redaction into the builders** — `scripts/redact_comments.py`
  currently runs as a documented post-step (GOTCHAS.md); folding it into the per-city
  comment-clean scripts + weeks_lib would remove the re-run-after-rebuild footgun.
- **2026-07-31: draper packet-text whitespace-bloat re-extraction** — one sidecar
  (`packets/text/2020-05-28_…att1624.txt`) is 110 MB holding only ~37k words (layout-mode
  padding); gitignored (over GitHub's limit). Re-extract that attachment with whitespace
  normalization from the retained raw packet to restore it to the committed text layer.
- **62 PC land-use recommendations still landing Other/low** — deferred classifier rider.
  (L1982)
- **west_jordan PC roster regeneration** over the merged 2020+ span (optional). (L3015)
- **Riverton Timberline DA staff report** — per-object auth-wall; GRAMA or portal change.
  (L1093)

## Routine (fold into the quarterly refresh — next run early Oct 2026)

- /audit-city-data after any large ingest (murray PC ~300 unaudited dispositions are queued
  as TODO [DEBT]); pending re-checks (magna CRA ×3, st_george PC 2026-03-10, vineyard ×2,
  SSL RDA, midvale RDA, SSL PC dup swap, 2024-08-06 midvale existence); ordinance
  codification-lag re-probes (copperton, kearns, white_city, orem); pending-adoption 60-day
  window revisit after 2–3 cycles; magna lower-confidence crosscheck flags (deliberate scope
  cut). (L2147–2153, L3018–3021, L2776, L3390)

## WATCHES — external events; check at each refresh, never "work"

| watch | where to check | trigger | last checked | status |
|---|---|---|---|---|
| lehi council minutes publishing lapse (~19-21 meetings since 2026-01-27) | Granicus | minutes appear | 2026-07-19 | GRAMA-only per evidence |
| st_george 2025-10-09 work meeting | Revize | correct PDF replaces wrong upload | 2026-07-19 | logged with city |
| orem PC 2025-10-15 minutes | CivicClerk | file distinct from 11-05 served | 2026-07-19 | mis-upload |
| alta 2025 SOVC | SLCo clerk | county posts | 2026-07-19 | 2025 election was CANCELLED (20A-1-206) — watch only certification artifacts |
| taylorsville 2026-06-17 minutes | CivicEngage | posted | 2026-07-19 | pending |
| magna 2025-11-18 CRA approved copy | PMN | approved version | 2026-07-20 | draft rejected |
| SLC 8 comment pages (5 content-filter + 3 other) | — | retry with newer models | 2026-07-16 | permanent-gap candidate |
| ogden/logan/orem CF cycle publications | city portals | 2025 cycles posted | 2026-07-19 | — |
| SLC campaign-finance portal | dotnet.slcgov.com | portal back up → harvest | 2026-07-13 | blocked; slc absent from cf layer (caveat added 2026-07-31) |
| millcreek even-year SOVC | SLCo | acquisition would unblock its re-point exception | 2026-07-19 | — |
| CivicPlus platform (murray/SSL/MSD 500s) | portals | re-verify, nothing marked dead | 2026-07-19 | correlated outage |
| `wasatch.utah.gov` legacy DNN host (serves 2018–2024-June wasatch CF PDFs live) | direct Portals/ URLs | host dies → 104 filings become archive-only; re-mirror check | 2026-08-01 | live; link-rot risk |
| cache CMS migration record-drop (live 2022 page ≠ Wayback 2022 page filer list) | cachecounty.gov financial-disclosures | future migrations dropping filings | 2026-08-01 | 2022 delta captured |
| county CF 2026 cycles (all 8 counties, finals due Dec 2026–Feb 2027) + SLCo Nov-2026 general canvass | county pages + SLCo clerk archive | post-certification refresh | 2026-08-01 | calendar-incomplete by design |
