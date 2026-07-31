---
name: cf-vision-transcribe
description: Transcribe scanned/handwritten campaign-finance filings that OCR can't reconcile, using the Read tool (billed to the Claude Code plan/allotment) INSTEAD of the Anthropic API. Renders each filing's PDF pages to images, reads them natively, and writes the exact `vision/<hash>.json` cache the per-city `build_finance.py` already consumes — so no build code changes. Use for the queued needs_review/OCR-floor filings, or any new scanned CF city, whenever API-credit-free operation is wanted (this is the DEFAULT method until further notice; the API method is the fallback).
---

# cf-vision-transcribe — Read-tool vision transcription for scanned campaign-finance filings

## Why this exists (the credit distinction — READ THIS)
The structured campaign-finance layer escalates unreadable (scanned/handwritten) filings to
Claude vision. There are **two ways to do that vision**, and they bill to different places:

- **API method (FALLBACK):** the per-city `vision_extract.py` loads `ANTHROPIC_API_KEY` from
  `.env` and calls the Anthropic **Messages/Batches API** → billed to your **API credit balance**.
- **Read-tool method (THIS SKILL — the DEFAULT until further notice):** an agent renders the pages
  to images and uses the **`Read` tool** to view them. That inference runs on your **Claude Code
  plan/allotment**, not the API credit balance. Same model, same "look at the page and transcribe"
  task — just no API call.

**Output is identical** either way: a `vision/<hash>.json` cache file that `build_finance.py` reads
via its `rows_override_fn`. So this method is a drop-in — never edit the build to use it.

To switch back to the API method, see `scripts/campaign_finance/VISION.md`.

## Inputs
- **city** (required) — e.g. `west_jordan`, `ogden`.
- **filings** (optional) — the specific `index.csv` `path`s / candidates to (re)transcribe.
  Default = every filing in that city's `filing_totals.csv` whose `reconciles_*` is False/blank or
  `extraction_confidence=low`/`needs_review=1` and is `format=scanned` (i.e. the honest OCR-floor set).

## The exact cache contract
Before transcribing, READ, for the target city: `campaign_finance/build_finance.py` (the
`_vision_rows`/`_vision_result`/`rows_override_fn` section), its `*_vision_extract.py` (the JSON
schema it emitted, if one exists), and one existing `campaign_finance/vision/*.json`. Match the
schema **byte-for-byte**.
- **Filename — ONE repo-wide convention (standardized 2026-07-19, all legacy doc-id keys
  migrated): `vision/<sha1(index.csv path)[:8]>.json`** — sha1 of the dataset-relative `path`
  value exactly as printed in `index.csv`, first 8 hex (`scripts/campaign_finance/
  vision_lib.cache_key`). The only variant: a city where ONE PDF holds multiple logical filings
  appends the per-filing discriminator inside the sha1 — st_george `sha1(path + "|" + candidate)`,
  nephi `sha1(path + "|" + page_range)` (nephi's pipe is always present, even for an empty
  page_range — use its build's own helper). Trailing-filename-hex keys are BANNED (they collide —
  the holladay finding). After writing, **verify the build consumes it** (cheapest proof: a
  rebuild changes the filing's rows).
- **Body:** `{"contributions":[{"date","name","amount","in_kind"}...], "expenditures":[{"date","payee"|"name","amount","in_kind","purpose"}...]}`.
  If the filing **bundles multiple reports** (interim + final in one PDF — common for the 2021 city
  forms), use the city's **multi-report `reports[]` schema** (each report its own contributions/
  expenditures + the report's printed cover totals) so the build sums per report, not once.
- Amounts are **strings, verbatim as printed**; `in_kind` is the printed flag.

## Procedure (the launched agent follows this)
1. **Resolve the target filings** for `city` (the flagged/OCR-floor set, or the passed list). Map each to
   its `raw/…pdf` and its `index.csv` `path` (for the cache hash).
2. **Render pages:** `pdftoppm -jpeg -r 150 <pdf> <workdir>/<city>_<did8>_p` into a **city-unique
   working dir** in the scratchpad (NOT `/tmp` — tesseract/pdftoppm can't always read `/tmp` here; and
   use city-unique names — the scratchpad is shared across agents).
3. **Read + transcribe:** `Read` each rendered page image and transcribe every contribution/expenditure
   line + the printed cover TOTALs into the cache schema. **Return printed TOTALs verbatim; the build
   sums the itemized rows in code — never sum or compute a total yourself.**
   - **Strict discipline (anti-fabrication):** transcribe EXACTLY what's printed. A digit you can't read
     → `null` / omit + it stays a flagged undercount. **NEVER infer, complete, or "clean up" a figure.**
     Preserve source typos. Mark in-kind per the printed flag only.
4. **Write** `vision/<did8>.json` for each filing (matching the contract above).
5. **Rebuild + verify:** `python3 <city>_city_council/campaign_finance/build_finance.py`, then
   `python3 scripts/campaign_finance/validate_finance.py <city>_city_council/campaign_finance` (→ PASS),
   then `python3 scripts/campaign_finance/cycle_totals.py <city>` (regenerate the rollup).
6. **Report:** filings transcribed, reconcile before→after, any still-flagged (honest), and note
   **cost = $0 API (Claude Code allotment via Read)**.

## Chunking (mandatory — Read images are context-heavy)
Each page image consumes input tokens in the agent's context, so ONE agent cannot ingest a huge scan set.
The orchestrator chunks the work and launches **multiple `general-purpose` agents**, each bounded:
- **≤ ~15 page-images per agent.** So one agent handles either several small (1–3pp) filings **or** one
  large multi-page filing (up to ~15pp). Split a 30+pp filing across 2 agents by page range (each writes
  a partial `reports[]`; the last to run merges — or assign disjoint reports of a bundle to disjoint agents).
- Give each agent **disjoint filings** (no two agents write the same `vision/<did8>.json`).
- Agents may run in parallel (they read different images) BUT must all write only their own city's
  `vision/` cache; the **build_finance.py rebuild happens ONCE, by the orchestrator, after all chunk
  agents finish** (a single rebuild reads every cache) — do not have each chunk agent rebuild.

## Orchestrator agent-prompt template
Launch each chunk as a `general-purpose` agent with a prompt like:
> Transcribe these scanned campaign-finance filings for **<city>** using the **Read tool only — NO
> Anthropic API / no vision_extract.py / no `messages.create`** (this must run on the Claude Code
> allotment). Filings: <list of raw pdf paths + their index `path` for the cache hash>. First read
> `<city>_city_council/campaign_finance/build_finance.py` + one existing `vision/*.json` to learn the
> exact cache schema + hash. For each filing: `pdftoppm -jpeg -r 150` the pages into a `<city>`-unique
> scratchpad dir, `Read` each image, transcribe rows + printed cover TOTALs verbatim into
> `vision/<sha1(path)[:8]>.json` (multi-report `reports[]` schema if the PDF bundles >1 report).
> Transcribe EXACTLY — illegible → null, NEVER infer. Do NOT rebuild/validate (the orchestrator does one
> rebuild after all chunks). Return: which filings you wrote caches for + any pages you couldn't read.

After all chunk agents finish: rebuild once, validate, regenerate `cycle_totals`, report.

## Non-negotiables (inherited from expand-city-sources / the CF SCHEMA)
- Never fabricate — an unreadable figure is a flagged gap, not a guess.
- Additive only — write `vision/*.json` + regenerate the DERIVED CSVs; never hand-edit contributions/
  expenditures/filing_totals or any CORE dataset.
- `donor_type` incl `family-of-candidate`; `donor_raw` verbatim; blank-donor → `unknown`+`needs_review`.
- The API method stays in place as the fallback — do not delete `vision_extract.py`; see `VISION.md`.
