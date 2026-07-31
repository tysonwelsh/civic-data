# SETUP — environment for the civic-data repo

Everything here was verified working 2026-07-02 on macOS (Apple Silicon).

## Python

- **Python 3.11+** (built and verified on 3.11.5, anaconda). All core pipeline
  scripts — extractors, `build_db.py`, `build_referrals.py`, `build_weeks.py`,
  `scripts/validate_city.py`, `scripts/normalize_motions.py`,
  `scripts/build_coverage.py`, the audit screener — are **stdlib-only**.
- Third-party packages are needed only for the SLC LLM/vision extraction, the SLC
  PrimeGov scraper, the geo tools, and the polite fetcher:

```
pip install -r requirements.txt
```

See `requirements.txt` for what uses each package.

## System tools (Homebrew or conda)

```
brew install poppler      # pdftotext + pdftoppm (PDF text extraction / page rendering)
brew install tesseract    # OCR for scanned minutes (5.5.0 used for the Ogden 2022 re-OCR)
```

The audit skill also uses `/usr/share/dict/words` (present on stock macOS).

## API keys (.env files — never commit, never print)

Two gitignored `.env` files hold `ANTHROPIC_API_KEY=...` (KEY=VAL lines, loaded by the
sibling `config.py` in each dir):

- `slc_city_council/meeting_minutes/.env` — used by `extract_votes.py`
  (Anthropic Batch API vote extraction).
- `slc_city_council/public_comments/.env` — used by `vision_extract.py` and
  `check_new_comments.py` (vision extraction of comment PDFs).

If missing, create each file with a single `ANTHROPIC_API_KEY=<your key>` line.
No other dataset needs a key — all other cities' extractors are deterministic parsers.

## Validators (read-only; run any time)

```
python3 scripts/validate_city.py <city>_city_council/    # conformance vs SCHEMA_SPEC.md (exit code = FAILs)
python3 .claude/skills/audit-city-data/scripts/screen_corpus.py <minutes dir> [--json]
                                                          # statistical anomaly screen on a text corpus
python3 <city>_city_council/meeting_minutes/validate_votes.py
                                                          # per-city vote sanity report (where present)
```

## Regeneration entrypoints (derived layers only — never touch source-faithful data)

```
python3 <city>_city_council/db/build_db.py           # rebuild db/*.db core (idempotent, fail-loud)
python3 <city>_city_council/db/build_referrals.py    # rebuild the cross-body referral layer
python3 <city>_city_council/build_weeks.py           # rebuild weeks/ (run after ANY CSV change)
python3 scripts/normalize_motions.py --all           # regenerate motions_std.csv + crosswalks/ (all cities; --all required to sweep)
python3 scripts/build_coverage.py                    # regenerate coverage.json from disk
```

Refresh: SLC comments via `slc_city_council/public_comments/check_new_comments.py`
(the `check-slc-comments` skill); per-city `fetch_new.py` incremental drivers are the
REMEDIATION_PLAN.md 3.3 rollout.

## Path conventions

- The repo lives at `/Users/tysonwelsh/civic-data/` (moved from `~/Desktop/` in 2026-06).
- The shared county election archives intentionally still live at
  `~/Desktop/slco-election-archive/` and `~/Desktop/utah-elections-archive/`
  (referenced by sandy / west_valley / west_jordan election docs and
  `west_valley_city_council/geo/build_precinct_district_map.py`). If those archives
  move, update the paths noted there and in the `build-city-data-repo` skill.
