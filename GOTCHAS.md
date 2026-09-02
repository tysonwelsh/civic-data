# GOTCHAS — standing operational rules (moved from HANDOFF.md, 2026-07-31 restructure)

Durable, hard-won rules. HANDOFF.md is now a single-session banner; these live here so they
survive every handoff. The cardinal rules themselves are in CLAUDE.md.

## Build & federation

- **Every BUILT entity db MUST carry the standard `referral` table** (empty is fine — create it
  in the entity's build_db.py; the federator hard-fails without it; cache_county incident
  2026-07-20).
- **Run repo-level builders with ABSOLUTE paths**; confirm success by "integrity_check: ok" +
  "Search layer done (reconciliation exact)" (federation) / "Derived chain rebuilt".
- **Never run `build_cities_db.py` while any city agent is live** — one federation at the end
  of a work package (held through 21-agent waves).
- **Run `python3 scripts/validate_entity.py --federation` before trusting any gov.db number**
  (compares counts + content digest; exits 1 if any entity db is ahead of gov.db — built after
  gov.db silently sat ~3,000 motions stale for 3 days).
- **Sanity-check `v_council_current` after federating** (193 seats / 31 entities as of
  2026-07-17).
- **A SHARED REDUCER'S TARGET LIST SILENTLY WIDENS WHEN A NEW TIER ARRIVES — gate it on
  `e.level`, not on "does the file exist".** `cycle_totals.py::all_cities()` selected every
  registry entity with a `campaign_finance/filing_totals.csv`, so the 2026-08-01 county-CF
  federation quietly added all 8 counties to a CITY-ONLY reducer whose output
  `build_search_layer.py` loads unconditionally into the CITY-ONLY `cf_cycle`. A single
  `--all` run would have published county figures computed by rules that are wrong for every
  county corpus (the regime filter drops ALL of utah/weber/wasatch, whose `filing_regime`
  holds an arithmetic basis rather than a statutory stream; summit's documented-cumulative
  reports get SUMMED — Brickey 2014 → 32,400.00 where the truth is 16,800.00). Fixed
  2026-08-23 by making the separation STRUCTURAL rather than conventional: `level=='city'` in
  `all_cities()`, a raise in `write_city()`, an `e.level` gate in the loader, and two
  DIFFERENTLY-NAMED artifacts (`cycle_totals.csv` vs `cycle_totals_county.csv`) so a county
  file cannot answer to the city loader's name. **Whenever a tier is added to a shared
  dataset, grep for every consumer that enumerates entities by artifact presence.**
- **Non-city ordinance federation reads `<entity>/ordinances/index.csv` with a DIRECT
  entity-db-local `motion_id` column** (loader applies the fed_index offset;
  matched_motion_date/no is the CITY convention only). Keep code-codification catalogs OUT of
  index.csv (Weber keeps them in `code_sources.csv`) or they federate as junk ordinance rows.
- **County-db projections/gis/development loaders do not gate on db_rel_path** (db-less thin
  counties federate those modules); election_result never gated.
- **Link-only catalog rows (no on-disk artifact, e.g. a StoryMap-only general plan) are
  legitimate** — build_fts guards null paths; don't "fix" them by fabricating a text sidecar.

## Re-extraction & derived layers

- **`motion_id` IS NOT STABLE ACROSS RE-EXTRACTION — never hand-write one.** Re-derive links
  (cache/summit have db/link_ordinances.py); when a linkage bug appears, re-derive and diff
  the WHOLE entity, don't fix flagged rows. Diff re-extractions at the
  `(source_file, date, body, motion_no, member, vote)` level.
- **After any `extract_votes.py` re-run, cities with an `extract_backfill_votes.py` MUST
  re-run it** (herriman would silently drop 949 pmn rows; run order documented per city).
- **CSV builders that glob `votes/*.json` resurrect stale JSONs** — delete a doc's JSON after
  removing it from an index.
- **`pdftotext -layout` COLUMN GEOMETRY IS NOT STABLE BETWEEN PAGES OF ONE DOCUMENT, and these
  ledgers print their column header only once** (washington CF, 2026-08-23). On
  `washington_county/campaign_finance/raw/wayback_2010elections/Expenditures - Rob Tersigni.pdf`
  the Amount column sits at character columns 40-47 on page 1 and 19-26 on page 2; a family that
  pins its column territories to the page-1 character grid then drops **every** row on pages 2+
  and the loss is SILENT (23 of 77 rows on one filing). In the PDF's own coordinates there is no
  drift at all — that file's amounts right-align to `x=305.0` on every page. Read positional
  ledgers from `pdftotext -bbox-layout` word boxes (recipe:
  `washington_county/campaign_finance/bbox_lib.py`), which also yields `pct:` geometry free.
- **Take a column's edge from a ROBUST statistic, never the MINIMUM.** One outlier token ruins a
  minimum, and CF forms supply them: washington's sub-$50 aggregate line prints its figure INSIDE
  the donor name (`Aggregate total under $50.00 contribution`), and that single `$50.00` at
  x=181.8 — in a table whose dates all begin at x=265.1 — pulled the name column's boundary left
  and truncated every donor address on the page. Median per column.
- **A ledger's continuation line that carries DIGITS is a street address, not a wrapped name.**
  `_looks_address`-style street-word/state hints alone are not enough (`460 N 2460 W, Hurricane
  UT 84737` matches none of them), and getting it wrong writes a street address into `donor_raw`
  — a wrong value AND a PRIVACY breach at once (PRIVACY.md: city/state only). Also check which
  way the layout STACKS: washington's 2014-15 workbooks print the name inline with the figures
  and the address below, while its 2012 generation prints the name ABOVE and the address on the
  figures' own row.
- **Derived layers (`db/`, `weeks/`, `roster/*.csv`, gov.db) are regenerated, never
  hand-edited.** Never hand-edit generated roster CSVs — edit the driver's `TENURES` or
  `roster_overrides.csv`.
- **Curated crosswalk rows go in `scripts/normalize_motions.py` CONSTANTS, never only the
  CSVs** — `write_crosswalks` regenerates `crosswalks/*.csv` from the in-script tables on
  every normalize run and silently drops CSV-only rows (kearns-CRA / EC-Recuse incident).
- **`normalize_motions.py` has a STRICT CLI**: `<city>` for one city, `--all` to sweep; bare
  runs and unknown args ERROR instead of silently sweeping all 31 cities.
- **CH + herriman refresh = `fetch_new.py --ingest` (append-only).** Their full-build paths
  (`--fetch` / `--build-md`) are DESTRUCTIVE and refuse without `--force-full-rebuild`
  (+auto-backup). herriman's `post_ingest` auto-chains extract → extract_backfill_votes →
  validate.
- **`referrals_lib.py` carries the ogden FP guard as OPT-IN params** — defaults are a proven
  no-op; only ogden enables it. Enabling elsewhere needs per-city evidence review.
- **draper `link_text_sidecars.py` is discard-row-SAFE (fixed 2026-07-19)** — the old
  do-not-rerun caveat is retired.
- **vote_overrides.csv has TWO kinds** (conflict-resolution and ADD-MEMBER); stale rows FAIL
  the build loudly. h.db formula: `expected = db_votes + conflict_overrides − add_overrides`.
- **ogden PC has a documented `planning_commission/vote_corrections.csv`** (post-parse,
  evidence-cited, snippet-anchored) for the failed-motion both-lists-"aye" clerk-typo class —
  corrections go there, never in the minutes markdown.

- **After any comment-layer rebuild (all_comments_clean.csv regeneration or weeks/
  rebuild for a comment-bearing city), re-run `python3 scripts/redact_comments.py`**
  (PRIVACY.md policy 2026-07-31: constructed comment layers ship email/phone-redacted;
  verbatim minutes and campaign_finance/text are NEVER redacted). Idempotent; then
  re-federate so gov.db's comment/fts_comment pick up the redacted text.

## Shell & SQL habits

- **`sqlite3 <path>` CLI CREATES the file on open** — resolve a city's db via
  `registry/entities.csv` `db_rel_path`; query read-only with `sqlite3 "file:<path>?mode=ro"`;
  delete any stray `.db` (the `glob("*.db")[0]` landmine).
- **cwd reverts when a compound `cd … && …` command fails** — prefer absolute paths.
- macOS has no `timeout` binary — use gtimeout or the harness timeout.

## Sources & portals

- **PMN/portal labels lie — verify from in-body content**: minutes embedded inside the next
  meeting's approval packet (magna); a "PC" doc that is a council work session (CH); a state
  CF PDF containing the WRONG CANDIDATE's report (riverton Pierucci); cancellations announced
  only in notice BODY prose.
- **The PMN browser search is captcha/erroring; the working path is a JSON POST to
  `/pmn/searchresult.html` with an `X-CSRF-TOKEN` header** (params JSON-stringified; paginate
  via startingRow; publicBodyName exact-match does NOT match "Planning Commission" — filter
  client-side).
- **Delisted-but-live-by-ID CMS docs (CH pattern):** a CMS can drop a doc from its listing
  while still serving it by ID — Wayback captures of the LISTING page recover the anchors.
- **Auth-walls can be per-object, not per-meeting** (riverton Granicus MediaManager):
  siblings on the same agenda fetch fine; walled rows use `fetch_status=error:auth_wall`.
- **CivicEngage is Akamai-403 to plain fetchers** — urllib + archive-browser UA works
  (taylorsville).
- **The PMN JSON search silently IGNORES a `keyword` param** and returns an unfiltered
  entity browse that LOOKS like a hit — a keyword-based negative is not a negative. Honored
  fields: entityName/publicBodyName/title/agenda/tags/startDate/endDate (dates YYYY-MM-DD),
  paginate via startingRow at 25/page (juab CF determination, 2026-08-01).
- **disclosures.utah.gov `/Municipal` folder labels lie BOTH ways** (2026-08-01 wave):
  county-office filings hide in candidate's-RESIDENCE-TOWN subfolders (juab sheriff under
  `juab_2014_Mona`; washington's whole 2010 county field under `2010 Elections`, commission
  filings under a `Local School Board` folder), AND the 17-16-6.5 county form header
  false-positives (clerks hand the county blank form to municipalities/special districts —
  summit 29, washington 6). Classify by the **office line inside the form** + even-year
  cycle parity; header = supporting evidence only. Files serve from `municipal.utah.gov`
  with **BACKSLASH paths** (URL-encode `%5C`); directory listings 403 but direct file URLs
  serve.
- **ZERO-GLYPH RULING (owner, 2026-08-02, repo-wide):** in any transcription, a glyph that
  DENOTES the digit zero — slashed zero `Ø`, `-0-`, or the written word "zero" — transcribes
  as **0** with the verbatim glyph preserved in the cache/notes; a bare dash, `N/A`, or an
  empty cell stays BLANK (a nil mark is not a numeral). Utah County's `-0-`/"Zero" whitelist,
  summit's 7 promoted Ø cells and wasatch's Kahler "zero" all follow it; weber's 10 dash
  balances correctly stay blank.
- **The Read tool DOWNSAMPLES large images (~2000px long edge) — raising pdftoppm -r on a
  FULL PAGE does nothing beyond ~185 effective dpi.** Real escalation = a TIGHT CROP of the
  disputed cell rendered at high dpi (1200dpi cell crops resolved what "600dpi full-page"
  could not — Opus pilot contender's root-cause finding on the Rhodes fax, 2026-08-02).
  Compose with the full-page rule: FIRST read is always the full page (field coverage);
  escalation crops tight. **AND: escalation resolves legibility, never truth — the
  document's own ARITHMETIC (schedule sums, page subtotals, balance closure) outranks
  any glyph re-read at any resolution** (Rhodes reversal 2026-08-02: a 600dpi
  sibling-copy 'settlement' validated the wrong digit; Form A's sum decided it).
- **Vision transcription renders FULL pages, never cropped** — an improvised "top 80%"
  crop silently cut the signature-date line off most Summit CF covers (45 recoverable
  dates lost until the 2026-08-02 re-read); a crop that saves tokens costs fields you
  didn't know were below the fold.
- **Wayback can return HTTP 200 with a ZERO-BYTE body on a valid capture** — check bytes,
  not status; an immediate re-request often recovers the file (washington CF, 2026-08-01).
- **SLCo EasyVote API** (saltlakecountyut.easyvotecampaignfinance.com): open JSON API, no
  auth — token via `GET /authentication/getwebsiteuser/saltlakecountyut`, itemized data via
  `/advancedsearch/{contributions,distributions}/{customerId}` with the
  `Easy-Vote-Authenticated-User` + `ZUMO-API-VERSION: 2.0.0` headers; **403 to
  `Python-urllib` UA — send a browser UA**. Full recipe:
  `salt_lake_county/campaign_finance/RECON.md`.
- **disclosure.saltlakecounty.gov (pre-2022 SLCo CF portal) — the APPLICATION IS DEAD, not
  WAF-blocked (RE-DIAGNOSED 2026-08-20; the prior "BigIP-dead to ALL scripting / browser
  automation or GRAMA" wording was wrong on both counts).** The failure is path-SELECTIVE and
  deterministic: paths the load balancer forwards to the app pool RST at a flat ~0.23 s, while
  every other path returns a clean catch-all 302. Anti-bot discriminates by CLIENT; this
  discriminates by PATH. **A real browser does NOT help** — Chrome with full TLS+JS over CDP
  gets the same reset, as does a request from unrelated infrastructure. Wayback's last HTTP 200
  is **2026-01-15** with the TLS cert still current: a maintained VIP in front of a dead pool.
  ⚠ The report route is **`/Search/PublicSearch/Report/{id}`** (ids 1069-2104), NOT `/Report/{id}`
  — the 2026-08-01 probe hit a non-route, so its Wayback 404 was never evidence about the
  reports. **GRAMA is the only route** to that era's 251 online-filed reports. Its 130
  PAPER-filed filings are a separate slice and are freely downloadable today from the county CMS
  `globalassets` path. Evidence: `salt_lake_county/campaign_finance/_recon/2026-08-20-portal-probe/`.
- **A URL family found on one page is a reason to re-check every SIBLING page.** The SLCo
  `globalassets` CF host was recorded on 2026-08-01 from the METRO-TOWNSHIP page and filed as an
  out-of-scope "BONUS"; nobody opened the county-offices page, which serves **130 in-scope
  county filings** that then sat unacquired for three weeks while the era was documented as an
  unreachable gap.
- **NEVER RELY ON THE SOURCE'S REDACTION — the discard-at-read-time rule is the wave's own.**
  Salt Lake County's `_redacted` marking is unreliable in every direction, measured across the
  2015-2021 paper slice (2026-08-23): 40 of 130 files lack the suffix, several that carry it are
  unredacted, two print contributor street addresses fully in the clear, the black bar
  **UNDER-COVERS** in every year of the slice (street numbers and street-type abbreviations
  escaping into the neighbouring Occupation column), one filer wrote a street address *into the
  Name of Contributor cell* outside the bar entirely, and — on the one genuinely born-digital
  document — **the redaction is COSMETIC**: bars drawn over an intact text layer, with 156
  ZIP-shaped tokens still extractable by `pdftotext` against exactly 156 contribution rows. Keep
  `donor_city`/`donor_state` only, discard street/ZIP/phone/email at READ TIME, and record
  *redacted at source* separately from *filer left it empty* — different facts.
- **`sha256`-DISTINCT IS NOT DOCUMENT-DISTINCT in a scanned corpus.** `2020_…_burdick-fin-report-3.pdf`
  is a SECOND SCAN of a Schedule B sheet bound inside another filing — identical rows, dates,
  amounts, printed grand total and even the same stray pencil line — differing only by one pixel
  row in the embedded raster (1654x2170 vs 1654x2171). A harvest sha256 check called all 130
  documents distinct. Summing such a pair double-counts; look for duplicate CONTENT, not bytes.
- **PAGE ROTATION IS PER PAGE-BLOCK, NOT PER FILE**, and `pdfinfo` will not tell you: one SLCo
  filing stores its Schedule A attachment needing a CLOCKWISE rotation and its Schedule B
  attachment upright, both reporting `rot: 0`; another has pp.4-9 rotated and pp.11-12 upright.
  A document-wide rotation silently mis-reads half such a filing, and a wrongly-rotated render
  stays fully READABLE — so orientation can never be judged by "can I read it". Check each page's
  header/title axis, and emit geometry in the un-rotated portrait frame poppler renders.
- **A RECONCILIATION ANCHOR'S SCOPE MUST BE TESTED PER PAGE — not per filer, not per filing.** A
  schedule's `TOTAL (Sum of subtotals from all pages)` cell can hold the CYCLE-CUMULATIVE figure
  while `SUBTOTAL FOR THIS PAGE` on the same sheet holds the PERIOD figure; the same schedule
  total can instead sit ABOVE the Summary figure because page subtotals exclude in-kind rows the
  schedule lists; and on some filings **Summary Column A is itself cumulative** with the period
  figure only at lines 4/6. Measured on six SLCo filings in BOTH directions, and **one filer flips
  convention between his original and his amendment**. Test which printed figure each anchor
  equals BEFORE reconciling; where the anchor and the published `stated_*` have different scopes,
  publish both and leave `reconciles_*` BLANK — a scope mismatch is a basis error, not a delta.
- **COMPLETION MUST BE MEASURED ON THE DERIVED QUANTITY, NEVER A PROXY.** An agent-completion
  notification proves an agent FINISHED, not that it STARTED (two chunks silently never launched
  after a concurrency-cap rejection, 2026-08-23), and a record FILE existing does not mean the
  chunk is done (agents are instructed to re-save every ~3 filings, so a partial save is
  indistinguishable from a finished one). Neither is visible to any data gate: append-only
  checkpoints only assert rows never shrink, additive-only proofs only compare to the pre-wave
  baseline, and conformance validators only check what IS there. Close a wave on the derived
  queue — `vision_coverage.py` reporting `remaining 0` — and nothing else.
- **A HANDWRITTEN CENTS GROUP IS A 100x HAZARD IN TWO DIRECTIONS, AND GROUP LENGTH IS THE ONLY
  THING THAT SEPARATES THEM** (cache+washington vision wave, 2026-08-24). Filers write cents
  three ways no text-layer parser ever had to meet: **space-separated** (`63 75`), **superscript
  over a rule** (`360.⁰⁰`, `52.8²`, `916.²⁴`), and **a dash or point in the cents position**
  (`200 —`, `1,000.-`, `7,200.`). Every module-local `dec()`/`money()` helper strips spaces —
  correctly, for the genuine thousands-space `2 844.02` — so `63 75` parses as **6375**. A
  3-digit group after the space is THOUSANDS; a 2-digit group is CENTS. Read handwritten cells
  with **`common.parse_vision_amount`**, an explicit whitelist that still refuses the malformed
  decimals the `utah-malformed-decimal` specimen requires to stay blank (`23,744,71`,
  `23.744.71`, washington's `$5,00.00`) — it does NOT delegate to `repair_money_line`, because
  that helper repairs any `$`-prefixed token and prefixing a bare filer cell would silently
  "fix" exactly those. Proof it is reading and not repair: on the 2006 Whitehead filing the nine
  rows sum to **916.24**, the figure printed in the schedule's own TOTAL cell; the naive
  space-stripping read gives 9,228.49 and closes against nothing.
- **A STATUTORY FORM THAT ITEMIZES ONLY ABOVE A THRESHOLD MUST BE RECONCILED AGAINST THE
  THRESHOLD LINE, NOT THE PUBLISHED TOTAL.** The 17-16-6.5 Form "A" itemizes only contributions
  **over $50**; the cover's line-2 `$50.00 or less` aggregate is never itemized, while
  `stated_total_contributions` publishes line 1 + line 2. Scoring the ledger against the
  published sum manufactures a false mismatch on every filing with a small-donor aggregate. The
  trap runs BOTH ways — many filers itemize their sub-$50 gifts anyway, and one **transposed her
  two cover lines** so each subset closed exactly, crosswise.
- **AN INDEX'S `election_year` DOES NOT MEAN THE SAME THING IN EVERY MODULE, and a shared
  validator that assumes it will fail good rows.** washington documents its `index.election_year`
  as *the year the DOCUMENT printed* — deliberately blank on 310 of 409 rows — with the cycle in
  a separate `cycle_year`, while `filing_totals.election_year` is documented as the cycle. An
  itemized row must carry the CYCLE, so `validate_finance.py`'s `(candidate, election_year)`
  check now also admits `cycle_year` where the index has that column. **Before "fixing" rows to
  satisfy a shared check, read what the module says its columns mean.**
- **A CURATED DETERMINATION FILE IS THE CORRECTION PATH FOR AN OCR'D INDEX FIELD, NOT JUST AN
  UNRESOLVED ONE.** washington's `office_determinations.csv` precedent was extended to
  `candidate_determinations.csv` when the vision wave read all 100 handwritten covers and found
  **36 `index.csv` candidate values that are tesseract noise** (`D A v 1 9) wh, TERE AD`). Same
  contract: the page's own line quoted as evidence, the OCR reading still retained verbatim in
  `document_candidate`, a file with no row untouched, and the change bounded by a column-level
  diff (36 rows x 3 derived columns, 0 other values moved). **Fix it in the layer that owns the
  field — never by writing the good value into a downstream row and leaving the index wrong.**
- **`sha256`-DISTINCT IS NOT DOCUMENT-DISTINCT, and the second class needs its own detector.**
  Cache's whole duplicate story is byte-identity (`applies_to` groups 42 cross-channel copies),
  which is BLIND to a re-scan: **26 cache filings are the same report published twice with
  different bytes** — including a photocopy of an earlier filing re-dated, betrayed by the
  earlier clerk stamp reproduced at its foot. Detect on an identical multiset of
  (date, name, amount) rows for one candidate+cycle, EXCLUDING groups that share a sha256, and
  flag rather than drop: both publications are real, but summing them double-counts.
- **Wix-hosted county sites** (weberelections.gov): `_files/ugd/` objects 429 plain urllib —
  send `Accept` + same-site `Referer`; some objects need a curl fallback
  (weber `fetch_cf.py`).

## Standing constraints (cardinal-rule corollaries)

Never fabricate (honest gaps are data; drafts stay sidecars; a cancelled meeting is an
EXCEPTION, never an unrecovered row — white_city/vineyard precedent; a mislabeled source
document is never transcribed under its label — riverton Pierucci precedent); city-faithful
values are never overwritten (fixes go in extractors or documented override files — the
add-member override is the sanctioned path for a garbled-value missing member); a defect found
in another layer while working is FLAGGED (TODO [DEBT] with evidence, or LEADS.md), never
fixed from the wrong layer.

- **NEVER RELY ON THE SOURCE'S REDACTION (standing rule, promoted 2026-09-02).** In any
  transcription, PII adjacent to a redaction bar (street addresses, ZIPs, emails, phones)
  is DISCARDED AT READ TIME — the county's bar contributes nothing to the repo's privacy
  guarantee; the wave's own discard rule is the guarantee. Corollary from the 2026-09-02
  adjudication: a shape COUNT is not evidence of concealment — only token GEOMETRY
  intersected with the bar is (the Staggs false positive: 156 visible ZIPs in a
  deliberately-unredacted column were read as concealed donor geography).
