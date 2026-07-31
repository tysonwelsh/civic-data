# public_comments/ — Vineyard, UT

## TL;DR
Vineyard publishes **no genuine written/online public comments**. Written comment is
**email-only** to the City Recorder (`robinr@vineyardutah.gov`); there is no eComment
portal and no published comment/correspondence archive. → **SUBMIT-ONLY verdict.**

- `all_comments_clean.csv` is **header-only (0 rows)** on purpose — this is the correct
  result, not a missing dataset. Do NOT backfill it with minutes paraphrases.
- The only public-comment material that exists is a **speaker log** of in-person
  speakers paraphrased by the clerk in the minutes → `minutes_speaker_log.csv`. Per
  `extraction_standards.md`, those are **meeting-record notes, NOT public-submitted
  written comments**, and must never be presented as the comments dataset.

See `AVAILABILITY.md` for the full hunt (all four standard sources checked: city page,
CivicClerk eComment API, agenda packets, correspondence archive).

## Files
| File | What it is |
|---|---|
| `all_comments_clean.csv` | Genuine written/online comments — **header only, 0 rows** (SUBMIT-ONLY; none published). SLC schema. |
| `all_comments_dropped.csv` | Drop log — header only (no genuine comments were ingested, so nothing to drop). |
| `minutes_speaker_log.csv` | **285** in-person public-comment speakers, 2020–2026, paraphrased from the 172 minutes `.md` (re-run 2026-07-19 over the full current corpus; was 210 when derived from 138 files, then 283, then **285** after the 2026-07-19 compound-title recall fix). **Clerk paraphrases — NOT residents' own written text.** First line is a header note stating this; columns: `date_normalized, contact_name, subject, topic, comment, source, source_file, quality_flag`. |
| `extract_speaker_log.py` | Deterministic extractor (no fabrication) that builds the speaker log. |
| `AVAILABILITY.md` | Avenues + SUBMIT-ONLY verdict. |
| `raw/` | (empty) reserved for any raw comment files — none exist for Vineyard. |

## Speaker log: what it is and isn't
- **IS:** a who-spoke / what-topic index of the minutes' PUBLIC COMMENTS sections —
  useful for "who shows up to council" analysis. `comment` holds the clerk's
  third-person paraphrase verbatim from the minutes.
- **IS NOT:** the public's own submitted words. `quality_flag =
  clerk_paraphrase_not_written_comment` on every row.
- Note: several recurring speakers (e.g. David Lauret, Jacob Holdaway, Sara Cameron)
  later joined the council but spoke here **as residents** during public comment
  (framed "living on … / resident of …"). Names are kept verbatim from the minutes,
  including the source's own spelling variants (e.g. "Cornelius" / "Cornelious").

## Reproduce
```bash
python3 extract_speaker_log.py   # → minutes_speaker_log.csv (285 rows)
```
**2026-07-19 compound-title recall fix:** the `Resident NAME` pattern now also matches a
compound title between "Resident" and the name — `Resident and <Title Words> NAME` (e.g.
"*Resident and Alternate Planning Commissioner Amber Rasmussen explained…*"). The optional
middle requires a lowercase "and" + 1–4 Capitalized role words, so it fires only on a genuine
"Resident and <role> <Name>" introduction and cannot change any bare-`Resident NAME` row.
Corpus-wide re-run added exactly **2** rows (283→285), both manually verified genuine
public-comment speakers at source (2020-09-23 Amber Rasmussen; 2023-01-11 Tyler Haroldsen,
"living on Mill Road") — **zero** new false positives, zero baseline rows changed.

## Don't
- Don't move speaker-log rows into `all_comments_clean.csv`. They are different things.
- Don't treat the header-only `all_comments_clean.csv` as a bug — it is the verdict.
- Don't bulk-download agenda packets to hunt for comments (they are up to 258 MB and
  contain only paraphrases anyway — verified). Range/size-check + sample text-layer only.
