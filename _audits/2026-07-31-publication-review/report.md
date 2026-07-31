# Publication-readiness review — 2026-07-31

**Question asked:** which TODO items actually matter for publishing this repo, which don't, what
else stands between the repo and a (possibly provisional) publication, and how should the TODO be
managed from here.

**Method:** 13 parallel agents, all read-only. Eight walked every open item and open sub-item in
TODO.md (245 triage rows) and verified each claim against the repo and gov.db — per the standing
rule that a backlog entry is evidence, not fact. Five reviewed publication dimensions:
first-time-user usability, publication logistics/risk, live data integrity, TODO-growth process
dynamics, and architecture. Companion file: `triage_full.md` (all 245 rows with evidence).

---

## 1. Verdict

**The data is publishable now; the packaging is not.** `validate_entity.py --federation` is green
44/44, `PRAGMA integrity_check` = ok, foreign keys clean, and every realistic research query an
outside reviewer tried (FTS sweep, contested rates, PC divergence, campaign-finance join) worked.
The honesty apparatus — caveat table joined into the views, provenance columns, honest-gap
ledgers, 99.98% source-URL coverage — is unusually strong and is what makes a provisional publish
defensible.

**The TODO is not the obstacle.** Of 245 verified rows, **10 are fix-before-publish** and only
**4 are true blockers** — and the blockers are almost all *packaging* (git, license, stale docs,
stale caveats), not data work. 86 rows (~35%) are already done or were never issues. The
2026-07-29 taxonomy's "~9 real debt items" claim is roughly honest.

**The felt regression is real but misread.** Open boxes fell 89 → 56 over the last 10 days while
the file grew 2,549 → 3,786 lines. 53% of TODO.md's lines sit under closed `[x]` boxes; the file
grows in proportion to work *finished*, not work *found*, because every closure adds a 10–50 line
evidence record and the archive protocol has run exactly once (2026-07-19). The repo got closer to
ready every session; the ledger made it look further away.

---

## 2. The pre-publish gate (do these, then ship)

Ordered. Items 1–2 are urgent independent of publishing.

1. **`git init` (private) today — with the .gitignore fixed FIRST.** The largest latent risk in
   the repo: 51 GB of work, dozens of hand-adjudicated override files, protected only by
   `_backups/` on the same disk. And the existing `.gitignore` predates the 2026-07-20 rename: it
   ignores `/cities.db` (now a 6-byte symlink) while the real **1.64 GB `gov.db` is unignored** —
   a naive `git add -A` stages it and GitHub hard-rejects at 100 MB. A second offender:
   `draper_city_council/packets/text/2020-05-28_…att1624.txt` (105 MB, in the *committed* text
   layer). Also add: `*/pmn_backfill/work/` (63 MB copperton scratch), `_backup_*/` (weber
   singular-named dir), `*.bak`, and decide `mag_mpo/legislative/raw_pdf/` (named `raw_pdf`, so
   the `raw/` rule misses it). Verify both live `.env` files are ignored
   (`git check-ignore`), rotate the ANTHROPIC_API_KEY as cheap insurance, inspect
   `git count-objects -vH` before the first commit. Measured publishable tree: **2.01 GB /
   ~60k files → ~300–450 MB packed** (compression measured, not guessed). No secrets found in
   committable code; no filename hazards; zero history to scrub — an advantage that survives
   exactly until the first careless commit.

2. **Re-federate with corrected caveats — the stale-caveat pair is the worst data-adjacent
   defect found.** The caveat table is the repo's credibility mechanism, and two rows now assert
   the *opposite* of the data: `utah_county/vote-ceiling` still says the entity is "BLIND to every
   divided Board vote after 2018" (the repair landed 2026-07-25: 11,218 motions / 4,705 votes / 84
   contested, named divided votes every year 2019–2026), and `weber_county/tally-only-partial`
   still claims 21 scans "never OCR'd" (all 21 OCR'd 2026-07-26). Root CLAUDE.md's utah_county
   bullet carries the same falsified warning. In the same pass: re-file south_jordan's
   `dissent-only` caveat from `meeting_minutes` to `planning_commission` (today
   `v_member_record_all` shows a South Jordan PC commissioner at a **100.0% nay rate with an
   empty caveat column**), fix the millcreek comments caveat (claims the CSV is empty; db holds
   27 rows), and back-fill caveats for the **16 built entities that have none** — including the
   five township-origin cities that are effectively 100% tally-only (magna's Audrey Pierce shows
   a 73.1% nay rate, uncaveated). Each city's own CLAUDE.md already documents these ceilings in
   prose; this is transcription into the CAVEATS block of `build_cities_db.py` + one federation
   run. Consider the reviewer's suggested build-time assertion: any (city, body) with >30 vote
   rows and zero named Ayes, or vote-rows-per-motion < ~1.0, must carry a matching caveat row.

3. **LICENSE + CITATION + METHODS + PRIVACY.** No LICENSE, no citation statement, no
   methods statement anywhere — the repo is legally unusable and uncitable as published.
   Conventional split: MIT/Apache-2.0 for `scripts/`, CC-BY-4.0 or CC0 for the derived data
   layers (with an explicit note that the underlying public records aren't yours to license and
   third-party plans/GIS keep their own terms — the GIS index.csv files already carry a license
   column). CITATION.cff + a Zenodo DOI minted from the first release solves citability and
   versioning at once. METHODS.md: per-layer extraction method (deterministic parser / OCR / LLM /
   Vision) and audit regime — README currently never discloses that SLC council votes are
   LLM-extracted and the 13,334 SLC comments came via Claude Vision; that belongs in front of a
   citing researcher, and the VERIFICATION.md files already contain the material. PRIVACY.md:
   see §5.

4. **The doc-consistency pass (~half a day, highest credibility leverage).** Every number a
   visitor will quote first is currently wrong somewhere:
   - README's headline table shows pre-07-26 numbers (county motions 24,346 vs actual **27,269**;
     votes 35,318 vs **38,597**), and its projections row is misaligned by one column.
   - CLAUDE.md overshoots the other way (27,376 / 39,237 / motion_std 77,507 vs actual 77,400 —
     the un-propagated cache 107-motion dedup). Four docs give three different entity counts
     (correct: **44 registered / 41 built**). HANDOFF.md is the accurate one.
   - `cities_db_SCHEMA.md` — the file README says to read first — describes the 2026-07-11
     database (16 cities, "every row is gov_level='city'", caveat 35 rows) and omits six live
     tables including the flagship `regional_project` and `projection`. Rename to
     gov_db_SCHEMA.md and regenerate its counts from `build_info`.
   - CLAUDE.md's "County motions have NULL disposition" is false (cache_county 2,949 + mag_mpo
     577 classified; the other five non-city entities 0) — state coverage per entity.
   - The `provenance='minutes'` audited-only advice is city-tier-only; at the county tier the
     same column holds extractor names, and the filter silently drops 84% of county motions.
     Scope the advice to `gov_level='city'` and document the second vocabulary.
   - Kill the two live pointers to the SUPERSEDED NEXT_SESSION_PLAN.md; banner or move the six
     closed planning docs (REFACTOR_PLAN, REMEDIATION_PLAN, PRIMARY_DOCS_*, WFRC_NATIVE_SPEC,
     sources_summary, refresh_status) to `docs/history/`.
   Permanent fix: generate every headline count from `build_info` at release time so drift is
   structural rather than disciplinary.

5. **One search-layer fix: 935 recovered minutes are invisible to FTS.** A doc_type filter at
   `scripts/build_search_layer.py:642-644` excludes every text-bearing `pmn_minutes` document
   from `fts_minutes` (provo 391, murray 80, vineyard 80, herriman 72, …) while CLAUDE.md and the
   schema doc promise full minutes coverage — the flagship keyword workflow silently misses whole
   recovered eras. Related smalls in the same file: the 200-char floor silently drops 4 real
   (short) LUDMA statute sections; ut_state FTS is 519 not the documented 525.

6. **Consumer packaging (fast, high-adoption-leverage).** A README QUICKSTART (three commands to
   first query, read-only `file:gov.db?mode=ro` idiom); ship `gov.db.gz` (**measured 3.75× to
   399 MiB**) as a GitHub **Release asset — not LFS** (free LFS is 1 GB bandwidth/month; one
   clone exhausts it); document the FTS/document `path` prefix rule (paths are entity-relative:
   `city||'_city_council/'` for cities, `city||'/'` otherwise — currently documented nowhere and
   the advertised "open the path" workflow fails on first try); note that `document.path` resolves
   only in a full local build (34% point into gitignored `raw/`) and `text_path`/`source_url` are
   the published-form pointers; a DATA_DICTIONARY.md generated from PRAGMA; one example notebook
   reproducing the marquee queries (doubles as a regression test); a few-MB `gov-sample.db`.

7. **Two ~20-line build-hardening wires** (protects strangers and future you):
   `build_cities_db.py` currently deletes gov.db then rebuilds in place — build to `gov.db.tmp` +
   `os.replace()`, plus a lockfile; and auto-run the federation-staleness gate at the end of every
   federation (the gate is good code but nothing invokes it — the exact combination behind the
   3,000-motion silent-staleness incident).

**Data defects worth fixing pre-publish (the only ones where a published number is WRONG):**
- **mag_mpo divided-tally loss — worse than filed.** The db stores one *inverted* outcome
  (2015-11-05: source "Motion failed with 10 yes and 12 no votes by [12 named mayors]" stored as
  `outcome='Pass'`), one missing divided motion, and truncated `result_raw` on others — while
  mag_mpo/CLAUDE.md asserts dissent is never named. Cardinal-rule-2 territory.
- **Mis-dated duplicate meetings — a repo-wide class, not a midvale bug.** The filed midvale
  Revize `M DD YY` triple is confirmed, plus a fourth midvale PC pair, magna PC, weber
  2021-06-01, holladay 2025-05-01 (~20+ motions under wrong dates across 4 entities). The
  deliverable is the date-collision detector the entry itself proposes.
- weber 2019-07-30 Solar Overlay motion never extracted (confirmed as filed, S effort).

Everything else — including every acquisition gap, every honest ceiling, the ut_state
`application`-table wart (verified: gov_level + self-describing app_keys + caveats make it
non-silent; add a 3-sentence README note and ship), county referral/disposition extension, the
WFRC-native package, the county content menu, Whisper, GRAMA — **ships as-is with its caveat or
waits behind the publish.** Blocking v1 on any of it is exactly the refinement-creep to stop.

---

## 3. What the triage found about the TODO itself

Counts over 245 verified rows: **10 fix-before-publish · 24 fix-soon-after · 124 backlog-ok ·
62 close-as-done · 25 drop.** Status: 125 real-open · **61 stale-already-done · 28 not-an-issue** ·
20 partially-done · 11 unverified.

**The backlog's error runs in both directions, again.** Three filed defect sections are
*falsified at source* — most dangerously holladay's "10 duplicated PC roll-call rows (Layton)":
the rows are **two real people** (Chair Howard Layton and Commissioner Chris Layton, both printed
in the 2022-05-16 minutes); executing the filed dedup would have deleted 10 genuine votes.
Riverton's two "dropped" votes are present in the db; midvale's "duplicate" is two distinct
same-day meetings (already called a false alarm 27 lines below its own filing). The alta 2025
election item prescribes re-pulling an SOVC for an election that was *cancelled* under Utah Code
20A-1-206. Meanwhile items the TODO never filed (the stale caveat pair, the FTS exclusion, the
mag_mpo inversion) outrank nearly everything it did file.

**Fix-soon-after highlights** (real, but publishable-with-caveat): legislator party/district
backfill (the `person` table has neither — "how did Republicans vote on the ADU bill" is
unanswerable today); draper + SLC are the only 2 of 31 cities absent from the CF layer, and no
caveat row or schema note says so; ogden election_race has zero primary rows while ten peers
carry primaries (raw PDFs on disk); SSL 2021 mayoral primary missing; draper 2025
canceled-uncontested race absent (two sitting councilmembers invisible to election queries);
midvale Erikson/Erickson person split; the `recommendation`-vs-disposition contradiction is ~68
rows, not the filed 13; `motion_std` and the FTS tables lack `gov_level`, making tier-safe
queries harder than unsafe ones.

Full rows with evidence: `triage_full.md`.

---

## 4. Why the TODO grows — and the redesign

Measured dynamic: 797 lines (07-12) → 2,549 (07-19, 89 open / 33 closed) → 3,786 (07-29, 56 open
/ 63 closed). Closures *outpaced* filings ~10:1 in the last 10 days; the growth is record mass.
Generative mechanisms: closure-in-place (every finish adds 10–50 lines); the archive protocol ran
once; **umbrella items** (185 lettered children, 66 explicitly done — 19 [TAIL] expansion
umbrellas held open by one residual letter each); watches wearing checkboxes (cannot be closed by
work); wave records (150–200 lines each) living in the queue because, with no git, TODO.md is
forced to be queue + changelog + provenance ledger at once. The 2026-07-29 taxonomy is
analytically right but structurally defeated: only 11 of 56 boxes carry item-level tags, sections
are internally mixed, and the ~9 DEBT items are interleaved with ~2,600 lines of history.

**Redesign (execute as one session, after git init so the sweep is a reviewable commit):**

1. **Four files, four functions.**
   - `TODO.md` → ~150–250 lines: the taxonomy preamble (keep), the ~9–13 [DEBT]+[GATED] boxes
     (each ≤15 lines, greppable tag, primary-source citation, observed-not-diagnosed phrasing),
     one-line changelog table pointing at archive anchors. The open-box count becomes a true
     work-owed metric.
   - `LEADS.md` (new) → the [OPTION] menu, [TAIL] residuals, and all future agent-filed leads as
     one-line dated bullets with evidence pointers. Explicitly a menu; no checkboxes; pruned
     freely. Watches become a table (item | where to check | trigger | last checked) folded into
     the quarterly-refresh checklist.
   - `TODO_ARCHIVE.md` → everything closed, verbatim, under stable dated anchors (kills the
     "referenced by name" stub exception). Grows forever; costs nothing.
   - `HANDOFF.md` → the current banner ONLY (~60–80 lines); prior banners to an archive; the
     operational gotchas + standing constraints move to CLAUDE.md or a stable GOTCHAS.md. Today
     it stacks 13 banners on a stale second document whose imperative queue describes 2026-07-20.
2. **Standing agent-instruction changes (CLAUDE.md):** leads go to LEADS.md, never TODO.md; an
   item enters TODO.md only as [DEBT] with a primary-source citation or as [GATED] by the owner;
   closing an item moves its record to the archive *in the same session*; no umbrella items; at
   most 3 leads promoted to DEBT per session, each verified at the primary source first; any
   closure that falsifies a CLAUDE.md/README claim updates that claim in the same session.
3. **SHIP_GATE.md (~30 lines):** the three state predicates as runnable checks —
   (1) `validate_entity.py --federation` exits 0; (2) ceilings-vs-caveats reconciliation;
   (3) doc-number sweep vs gov.db — plus the policy line: *open DEBT blocks publish only if it
   makes a published value WRONG; incompleteness ships with its caveat.* Declare ship against
   the state, not against an empty list.
4. **Post-publish:** [DEBT] → GitHub issues with taxonomy labels; leads/options → unmilestoned
   enhancement issues or a discussion; wave records → commit messages + release notes; and
   **never** convert honest data ceilings into issues — they are caveat rows, and an issue
   backlog of source properties would recreate the unbounded-pile illusion in public.

---

## 5. Conscious decisions for the owner (not blockers — decide and document)

- **Comment PII.** 17,970 comment rows carry `contact_name`; ~103 email / ~83 phone / ~233
  street-address lines sit in the CSVs (public record, but aggregation into an indexable repo is
  a real change). Cheapest defensible posture: strip emails/phones (186 lines), keep names, say
  so in PRIVACY.md with a takedown contact.
- **campaign_finance/text/** reproduces donor names *with street addresses* (lehi 98, ogden 371
  lines) while the structured layer deliberately stores only city/state. Accept-and-document,
  exclude the 7.6 MB text layer, or scrub — any is defensible; the undocumented inconsistency
  is not.
- **TODO.md/HANDOFF.md in the public repo?** Candid per-city assessments and unsent GRAMA drafts
  are honest but read as an unfinished-work list; consider a `_working/` directory at publish
  time so the front door is README + SCHEMA_SPEC + coverage.json.
- **udot/uta**: add a `build_status` column to entities.csv so registered-only entities are
  machine-detectable (their dirs don't exist; a naive registry walk breaks).
- The **~/Desktop election archives**: vendor the 12 KB one; for the 1.2 GB SLCo archive, add a
  SOURCES.md stating the derived `election_result` table is the published form.
- 46 committed .py files hardcode `/Users/tysonwelsh` — mechanical sweep, post-publish is fine.

---

## 6. Suggested sequence

| When | What |
|---|---|
| Now (½ day) | .gitignore fix → `git init` private → verify staged set → first commit → private remote |
| Session 2 (1 day) | Caveat refresh + re-federation (§2.2) · doc-consistency pass (§2.4) · FTS fix (§2.5) |
| Session 3 (1 day) | LICENSE/CITATION/METHODS/PRIVACY (§2.3, §5 decisions) · README quickstart + packaging (§2.6) · build hardening (§2.7) |
| Session 4 (½ day) | mag_mpo + date-collision + weber data fixes (§2 tail) · re-federate · SHIP_GATE.md green |
| Session 5 (½ day) | TODO restructure (§4) — after git, as one reviewable commit |
| Then | **Publish provisionally**: public repo + gov.db.gz release asset + Zenodo DOI + municipalsky.com link |
| After | Everything else via GitHub issues + the quarterly refresh; state-tier reintegration on its own schedule |

Roughly 3½–4 focused days of work stands between the current state and a defensible provisional
publication. Nothing on that path is data acquisition; it is packaging, honesty-maintenance, and
process. The 89→56 trajectory says the debt engine is already winning — it just needs the ledger
to stop hiding it.
