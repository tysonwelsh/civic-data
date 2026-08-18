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

- 2026-08-14 — **`webdme.slcgov.com` is a NEW, undocumented SLC Laserfiche WebLink host
  (v11.0.2411.10) carrying EIGHT live, anonymously-readable public apps**: `AgendasMinutes`
  (City Council, RDA, CRA, LBA, Board of Canvassers, Redistricting Committee, Mayor Boards),
  `OrdinancesResolutions`, `AdoptedLegislation`, `BoardsCommissions` (47 bodies incl. Planning
  Commission + Historic Landmark), `PlanningBoardsCommissions`, `Planning`, `GeneralBusiness`,
  `BldgPermitHistory`. OBSERVED: anonymous full-text search works (`SearchService.aspx/
  GetSearchListing`, `{LF:Basic~="…", option="DFANLT"}` → 397 hits for "campaign finance"),
  as does folder walking (`FolderListingService.aspx/GetFolderListing2` + `GetRootFolderId`);
  call shapes recovered from `app/dist/browse/main.js`. Rights are PER-ENTRY, so each app
  exposes only its own subtree. Relevant because slc's `packets/` layer records Council
  packets as INDEX-ONLY/monolithic on PrimeGov and `fts_packet` has 0 SLC rows — this host
  serves the same Meeting Materials as addressable Laserfiche entries. Discovered via the
  2021 declared-candidates roster's "Declaration Packet" links. Evidence:
  `slc_city_council/campaign_finance/RECON_2026-08-02.md` §2026-08-14 addendum.
- 2026-08-14 — **`CityElections` is the one RETIRED app on that host** (404 while all eight
  siblings return 200; its 2021 `DocView` ids resolve to id 0 / name null from a live app
  session). Its 2021 subtree held per-candidate Declaration-of-Candidacy packets, linked from
  the city's own roster page and captured 30× by Wayback (DocView shells only, no PDFs). A
  GRAMA ask for the CityElections subtree would cover the declaration packets; NOT campaign
  finance — no CF or elections-filings subtree is publicly exposed anywhere on the host
  (checked all 8 app roots; the only election-adjacent folders are Board of Canvassers and
  Board of Municipal Canvassers, i.e. certification).
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
    report; GEOMETRY family fixes (found by make_snippet.py's validation, 2026-08-02):
    washco_split must STAMP the part file its span is relative to, and summit_form's
    line origin is off by one vs the stored sidecar — both currently compensated by
    amount-validated resolution in the utility, both should be fixed at emission +
    re-swept; weber_polimorphic misses single-entry filings (headerless — Allred
    1,147.66 gated out).
  - *Region-URL publication checklist (when the itemized layer goes online):* geometry
    is IIIF-region-ready by design (`pct:` form preferred; `make_snippet.py` converts
    the exact text-span forms on demand) — remaining at publish time: choose serving
    (IIIF Image API server vs pre-cut static crops/Level-0 tiles from the coordinates),
    stable image identifiers (document sha256 + page — already in the ledgers), and ONE
    PRIVACY.md sentence acknowledging that served row-crops surface donor street
    addresses already public in the verbatim raws. Calibration-sample prerequisite BUILT 2026-08-02:
    `_audits/cf-calibration-suite/` (13 specimens + pass protocol; every configuration
    must pass before bulk rights). Phase A DONE 2026-08-02; Phase B wave B2
    (SLCo legacy) DONE 2026-08-03 — 496/496 filings, 22,871 rows, federated. REMAINING
    Phase B (per-wave owner approval): utah 245 scanned · summit 116 · weber 93 ·
    wasatch ~40 · juab 18 · cache pre-2022 Carr era · washington scan generations.
    New specimen candidates from the B2 close (add to the suite when next grown):
    the "no gate available is a claim to test" attachment-total case (McAdams/simgill);
    rule-detection row counting for subtotal-less spreadsheets (rowbands.py); the
    shared-temp-glob liveness trap; the wave-stamp clobber.
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
  - *SLCo GRAMA addendum (2026-08-02, extended 08-03 at B2 close):* 6 damaged/blank source
    PDFs incl. the wholly-blank dwilde_apr52006.pdf and two xref-broken files proven damaged
    AT SOURCE (re-fetch byte-identical), PLUS the B2 final gap ledger — 8 sides across 5
    filings whose schedules are missing from slco.org's own PDFs (~$121,789 C + $120,455 E;
    4 of 8 exactly reproduced by itemized sibling filings, 4 not) — fold all into the SLCo
    portal-era GRAMA ask alongside the SLC-city 2005–2017 request.
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
- 2026-08-14 (juab itemization wave, county CLOSED — 24 filings, +160 rows, 34/48 sides
  exact): five observations, evidence in `_backups/2026-08-14-tranche3-juab/` + the county
  AVAILABILITY verification section:
  - the amount-cell ink screen shows a systematic −1-row bias on ruled handwritten forms
    (filers write ABOVE the rule) — a future geometry gate should score against the ink
    centroid, not the band (geocheck2.py: 21 false −1 flags vs 2 true +1).
  - no automated ROW-COUNT gate exists for handwritten ruled county forms — two detectors
    built and rejected (firstink.py header false-positives; amountbands.py 33/39 pages
    mis-counted).
  - juab GRAMA ask gains two citable targets: Painter's earlier 2014 report (proved to
    exist by his own cumulative column) and Garrett-2014's missing Form A page ($250.00
    stated, no schedule in the county's 2-page scan).
  - donor-alias candidate: Juab County Democratic Party under 3 spellings across 4 rows —
    fold into the donor-alias crosswalk lead above.
  - the Carr 5-5-PG contribution basis (line 1 >$50 itemized + line 2 ≤$50 aggregate never
    itemized) is a STATEWIDE property of the 17-16-6.5 form — wasatch/summit/washington
    itemization will hit the same false `reconciles_contrib=False` pattern; candidate for
    a shared `recon_basis` column instead of per-module notes. (CONFIRMED same-day by the
    wasatch wave, which met it independently and made its reconciliation anchor-aware.)
- 2026-08-14 (wasatch itemization wave, county CLOSED — 111/111 filings itemized, 851 rows,
  168 sides exact / 20 verbatim deltas / 0 withheld; evidence in the county AVAILABILITY
  verification section + `_backups/2026-08-14-tranche3-phaseb/wasatch/`):
  - `index.csv.needs_review=1` on all 111 rows is now STALE (both layers complete) —
    retire/redefine in `build_index.py` (derived; not a hand edit).
  - Searle 2022-06 contributions −$50.00: the wave's only unexplained residual (the closing
    reading was REJECTED — born-digital prints $230.00 unambiguously).
  - Park 2024-11 binds two apparently IDENTICAL report faces (same figures/boxes/10-11-24
    signature) — needs an owner call on true-duplicate status.
  - Armer 2020-10 p5 "The Peak radio Ad": amount cell genuinely empty; filing arithmetic
    implies exactly $268.00 — would need a documented override, never a transcription.
  - Woodard 2026-06 donor "Marte Bona": bistable r/u at the scan's native ceiling; needs
    the paper original.
  - the county's 2018/2020 Form B template MISLABELS its payee column "Name of Contributor"
    — carry this if anyone parses `wasatch_fcr_3line`.
  - `_backups/` is gitignored yet wasatch's + SLCo's CLAUDE.md cite it as the rebuild
    recipe — move the records somewhere tracked or say the recipe depends on an untracked
    local dir.
  - `donor_state` name→USPS normalization implemented module-locally; likely wanted in the
    shared `normalize_donors`.
  - Woodard 2026-03's Table-A In-Kind column holds DESCRIPTIONS ("Loan", "Candidate
    Filing") of cash contributions; `in_kind=True` follows the column as printed — repo-wide
    question about that column's semantics.
- 2026-08-14 (summit itemization wave, CHECKPOINT — 24 of 116 scans itemized, 335 rows,
  39 sides exact / 5 deltas traced / 3 withheld on the grain question; resume kit at
  `_backups/2026-08-14-tranche3/summit-b/` incl. AGENT_BRIEF + per-filing shapes; residue
  derived by `wave_stats.py --residue`: 2014×20 · 2016×10 · 2018×16 · 2020×12 · 2022×19 ·
  2024×4 · 2026×11 — finishing the 4-filing 2024 residue closes that cycle):
  - **RULING RATIFIED BY THE OWNER 2026-08-17 — see the RECONCILIATION-BASIS RULE block
    below; this lead is CLOSED.** Original framing retained verbatim for the record:
  - the [GATED] period-vs-cumulative grain question is now DECIDABLE ON EVIDENCE:
    24390 Wolbach prints a period-only contribution page AND a fully reconciled cumulative
    expense page on ONE filing (the form gives no cumulative contribution ledger);
    24384 McKenna's period figures are provable to the cent by differencing its two covers.
    Proposed rule for owner ratification: publish the cumulative ledger where the form
    prints one; withhold where only a period ledger exists; never difference covers to
    synthesize rows. Withheld transcriptions are PARKED in `_meta_itemized.withheld_rows`
    so a ruling applies without re-reading pages.

- 2026-08-17 (summit wave CLOSED + **RECONCILIATION-BASIS RULE RATIFIED BY THE OWNER**):
  the summit scan queue closed at 116/116 (131/131 filings itemized; 2,519 rows;
  165 of 196 sides exact) and the owner ratified the rule that unblocks the parked sides:
  > **Reconcile each itemized side against the printed cover figure that MATCHES ITS OWN
  > SCOPE** — the cover's CURRENT-REPORT column for a period-scoped ledger, the CUMULATIVE
  > column for a cumulative ledger. Tag published rows with `is_incremental` accordingly.
  > **Never synthesize a figure by differencing covers.** Withhold only where NEITHER
  > printed figure closes.
  The decisive facts: period rows are DISJOINT from the prior filing's rows (they do not
  overlap, so publishing both does not double-count — McKenna 24232's 176 rows run to
  10/29 and 24384's 5 rows run 10/29-12/5, summing to the cover's cumulative exactly);
  the period figure is **printed natively in the cover's Current Report column**, so no
  differencing is required; and `is_incremental` is an EXISTING repo-wide column
  (populated across ~all entities; summit already carried 42 True rows), so the rule needs
  no schema change. What had actually blocked publication was a RECONCILIATION-BASIS
  MISMATCH — the gate compared a period ledger against the cumulative `stated_total_*` —
  not any defect in the rows.
  - **in-kind treatment is PER-FILER, not a form property** (wave finding, 2026-08-17,
    narrows the leg-1 McKenna precedent): in-kind is a separate schedule with a
    monetary-only cover on some filings (24232/24384) and entered INLINE inside both the
    schedule total and the cover on others (4020, 4278, 8191, 1268, 11110, 20758,
    24234/24708). Since `itemized_contrib_sum` is monetary-only, the inline filings publish
    a sum below their stated total BY CONSTRUCTION. The contract should settle in-kind per
    filing from its own arithmetic, never from cycle or form family. Applies beyond summit.
  - the `<=$50` aggregate is sometimes itemized after all (1082 second sheet, 1098
    interleaved, 1244 as anonymised "$50 or less donor" rows).
  - rotated/transposed scans (20641 90 deg, 26742 `/Rotate 270`) handled by an explicit
    `"transposed": true` geometry path.
  - **1250 Trussell 2014 — the Amount column is physically OFF THE SCAN** (landscape sheet
    fed portrait); the same sheet is complete on 1058, so a better county copy or a GRAMA
    request is the only honest recovery. Withheld as a scanner defect, NOT a grain case.
  - two vocabularies for `recon.result` on withheld/`none` sides (`withheld`/`none` on 24
    sides vs `unknown` on 12); `_meta_itemized.sides` is authoritative — a normalization
    candidate before the weber/utah waves.
  - new CALIBRATION SPECIMEN candidates: *20762 Furse* (printed right-hand columns sit one
    row high — field-shift positive control, only two independent arithmetic gates settle
    it); *1250 Trussell* (cropped amount column — negative control, correct behaviour is
    WITHHOLD, recovery = fail); *4278 Adair* (the printed total's cents sit OUTSIDE the box
    rule, so a box-tight escalation crop clips them — escalation-crop trap); *4020 Adair*
    (in-kind required INSIDE the printed total — positive control against the monetary-only
    assumption).

- 2026-08-17 (summit RECONCILIATION-BASIS RULE applied — 16 sides / 81 rows promoted,
  5 correctly still withheld):
  - **SHARED-SCRIPT CHANGE, owner should review:** `scripts/campaign_finance/`
    `validate_finance.py` check 6 asserted `reconciles_*=True ⇒ itemized_sum ~=
    stated_total_*`, which a PERIOD-basis reconciliation structurally cannot satisfy
    against a cumulative stated total (17 FAILs on first run). It now admits ONE declared
    and evidenced exception: every published row on the side carries `is_incremental=True`
    AND `filing_totals.notes` contains the literal marker `ITEMIZED <side> PERIOD-SCOPED
    (is_incremental=True)`; then `recon_delta_*` carries the test. Absent that declaration
    the original test is unchanged. All 38 CF modules re-run: every one still PASSes, none
    newly relaxed, summit is the only opt-in. **SCHEMA.md §4 was NOT updated to record the
    exception — that is owed.** A future revision could add a machine-readable
    `stated_period_*` column so the basis is not carried only in `notes`.
  - **`split50` structural ceiling:** on the pre-2022 sheet the ledger itemizes only the
    `>$50` donors while the module's contribution figure sums BOTH printed lines, so a
    split50 CONTRIBUTION side can close on the period basis only when the `<=$50` Current
    cell is 0 or blank (1264/1265/1274/4278 closed; 1268 did not). Worth a documented
    sub-rule if more such filings appear.
  - **1268 Yost 2014** — the filer's cover Current `<=$50` cell (75.00) contradicts the
    schedule's own `<=$50` box (25.00); neither figure closes, so the side stays withheld.
    Candidate for a targeted re-read.
  - **4278 Adair 2016 expenditures** — a single **+0.30** keeps 10 rows unpublished; all
    amounts were already escalated, so this is almost certainly filer arithmetic. Candidate
    for extending the vision-tier "delta, published with reconciles=False" contract to
    withheld-then-promoted sides (owner call).
  - **Donor-type gap:** Wolbach 24390's `donor_raw` is literally "Personal Contribution",
    so `normalize_donors` does not type it `candidate-self` and `self_funded_amount` stays
    0.00 though it is plainly the filer's own money. Generic-self-label handling belongs in
    the SHARED normalizer.
  - **REPO-WIDE SURVEY NOW WORTH RUNNING:** the same period-ledger-under-a-cumulative-cover
    shape is described in washington_county's caveat ("summary rows are per-period, ledgers
    restate cycle-to-date") and possibly wasatch/weber. Now that the rule exists, survey
    every county for sides withheld or mis-gated on this basis.

- 2026-08-17 (weber wave resumed — 83 of 93 scans itemized, 3 chunk agents; NOT fully
  closed, 10 scans + 18 geometry re-measures outstanding, see TODO [DEBT]):
  - **the "93 vs 197" discrepancy is RESOLVED and neither prior number was the queue:**
    `index.csv`'s 197 rows = 98 county-office + 91 school-board + 7 `unclear` + 1
    document-grain duplicate; of the 98 county filings 5 are born-digital Polimorphic
    e-filings owned by `weber_polimorphic`. 197 − 91 − 7 − 1 − 5 = **93** = the vision queue.
    The school-board/`unclear` rows are INVENTORY of the county's mixed compilation PDFs,
    not coverage — do not read them as a gap.
  - **WEBER ALREADY IMPLEMENTED THE RATIFIED BASIS RULE** (`period-exact` IS
    "reconcile against the matching-scope printed figure"; nothing is ever differenced) —
    the ruling codified existing practice. ONE divergence found and corrected: a verified
    period side used to leave `reconciles_*` BLANK, under-reporting a real reconciliation as
    unknown. 64 sides now publish `reconciles_*=True` + `is_incremental=True` + the check-6
    marker. Bolos closes only WITH in-kind — the per-filer in-kind finding holds here too.
  - **strongest cross-channel evidence yet for the vision tier:** Harvey's 2016 filing
    exists on TWO channels and two agents transcribed them hours apart with no knowledge of
    each other — **all 60 donor and 101 vendor rows agree on name and amount**, differing
    only in whitespace.
  - the workdir's `checkpoint.py` is SUMMIT's copy (points at `summit_county`,
    `_meta_itemized`, a `cover_totals.csv` weber lacks) — a `checkpoint_weber.py` was
    written; the wave-kit copies are not county-portable and should not be assumed so.
  - CALIBRATION-SPECIMEN candidates: the **swapped-cover pair** (two internally consistent
    covers filed under each other's key — detectable ONLY by chaining Last-Report to
    Cumulative); **rows running right-to-left** on a rotated schedule; **"0 in every
    This-Report cell"** making a final report cumulative-scoped (the `exact` case reached
    from the opposite direction); and the **wrong-column pointer that still sums correctly**
    — a negative control for GEOMETRY, since arithmetic closure cannot detect it.
  - smaller finds: Harvey's 2024 blank cover cell resolves to 24,300.00 and could be filled;
    `8a163a02`'s cache note still mislabels it a second June-16 report; 2024 covers carry a
    stale 2022 template year; 2026 filings begin carrying **"Ogden Valley City"**,
    incorporated off the 2024 ballot (registry/entities.csv implication — new Utah city).
  - **CROSS-COUNTY SWEEP THIS WAVE EARNED (act before the utah wave):** the swapped Gibson
    pair proves the 2026-08-01 vision-totals tranche can file a CORRECT reading under the
    WRONG KEY — both covers were internally consistent, so no arithmetic gate could see it.
    Cheap detector, no vision cost: for every candidate with consecutive filings in a cycle,
    chain **Last-Report vs the prior filing's Cumulative** and flag breaks. Run it over all
    8 counties' cover tranches (1,911 cf_filing stated-totals rows), not just weber.

- 2026-08-18 (post-consolidation): **UTAH COUNTY PHASE B WAVE BRIEF WRITTEN** —
  `utah_county/campaign_finance/WAVE_BRIEF_PHASEB.md` (scope, the inverted per-period regime,
  8 document traps, prerequisites, the B2 contract, sizing, and a paste-ready launch prompt).
  Two prerequisites are called out as blocking-by-judgment: fix the `rowbands.py` [DEBT]
  before promoting it to `scripts/campaign_finance/` for this wave, and run a FRESH
  calibration pre-flight — **no utah pre-flight has ever been recorded, and the configuration
  changed 2026-08-18** (make_snippet rotation + oversized-mediabox fixes), which triggers the
  standing re-run rule on its own.
  - THREE new calibration-specimen candidates: `summit-specimen-row` (the blank form's
    printed Jon-and-Jane-Doe example rows — correct answer DROP, proof = the total closes
    only without them); `summit-two-digit-bistable` (1065 Martin — TWO different re-readings
    each close the page exactly, so arithmetic alone is insufficient and tight-crop
    escalation is REQUIRED); `summit-swapped-pages` (expense p2 / contributions p3 —
    page position is not a classifier).
  - utah_county index may carry one row binding TWO reports: a 2018 Schedule B bound into
    `2020_SakievichTom6.23.20_Redacted.pdf` p6 (verify before the utah wave).
  - `rowbands.py`/`fitgrid.py` (printed-rule detection → measured pct: geometry + a
    row-count gate) are county-agnostic — promotion candidates for
    `scripts/campaign_finance/` before the weber/utah waves.

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
| SLC campaign-finance portal | dotnet.slcgov.com | **WebAPI answers → harvest is turnkey** (endpoints in slc AVAILABILITY.md; JSON-native) | 2026-08-14 | shell 200 / API still 503 (re-probed 2026-08-14, `GetElections`). **No movement in 12 days:** the 503 body is byte-identical to the 2026-08-02 retained snapshot except Cloudflare's rotating email-obfuscation token, and its embedded balance table still reads "Balance as of April 2026" — the city has not refreshed even its own rendered figures. Predecessor `CandidateReporting` still HTTP 500; sibling candidate app still 401 (server + DB alive, public read surface off). The twice-daily cron watcher was CANCELED by the owner 2026-08-03 — refresh-time checks of THE API, not the landing page. slc holds the 2003 cycle only; GRAMA covers 2005–2017 + 2019+ if the API stays down |
| millcreek even-year SOVC | SLCo | acquisition would unblock its re-point exception | 2026-07-19 | — |
| CivicPlus platform (murray/SSL/MSD 500s) | portals | re-verify, nothing marked dead | 2026-07-19 | correlated outage |
| `wasatch.utah.gov` legacy DNN host (serves 2018–2024-June wasatch CF PDFs live) | direct Portals/ URLs | host dies → 104 filings become archive-only; re-mirror check | 2026-08-01 | live; link-rot risk |
| cache CMS migration record-drop (live 2022 page ≠ Wayback 2022 page filer list) | cachecounty.gov financial-disclosures | future migrations dropping filings | 2026-08-01 | 2022 delta captured |
| county CF 2026 cycles (all 8 counties, finals due Dec 2026–Feb 2027) + SLCo Nov-2026 general canvass | county pages + SLCo clerk archive | post-certification refresh | 2026-08-01 | calendar-incomplete by design |
