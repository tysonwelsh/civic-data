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

## Standing constraints (cardinal-rule corollaries)

Never fabricate (honest gaps are data; drafts stay sidecars; a cancelled meeting is an
EXCEPTION, never an unrecovered row — white_city/vineyard precedent; a mislabeled source
document is never transcribed under its label — riverton Pierucci precedent); city-faithful
values are never overwritten (fixes go in extractors or documented override files — the
add-member override is the sanctioned path for a garbled-value missing member); a defect found
in another layer while working is FLAGGED (TODO [DEBT] with evidence, or LEADS.md), never
fixed from the wrong layer.
