# public_comments/ — Ogden City Council

## TL;DR verdict: SUBMIT-ONLY / NOT PUBLISHED
Ogden accepts written/online public comment (web form `ogdencity.com/publicinput`, email
`citycouncil@ogdencity.com`, voicemail 801-629-8158) and "enters it into the record," but
publishes **no verbatim text** anywhere. There is **no genuine published written-comments
dataset** for this city. See `AVAILABILITY.md` for the full avenue-by-avenue audit.

## Files
| File | What it is |
|---|---|
| `all_comments_clean.csv` | **Header-only by design.** Genuine public-submitted written/online comments are NOT published by Ogden, so there is nothing to put here. Do not populate it from minutes paraphrases. |
| `all_comments_dropped.csv` | Header-only audit trail (nothing was dropped; none found). |
| `minutes_speaker_log.csv` | **MEETING-RECORD NOTES, NOT public comments.** 635 rows: the City Recorder's 3rd-person paraphrase of people who spoke in person during the general "Public Comments" period of council meetings, 2020–2026. Columns: `date_normalized, contact_name, subject, comment, source_file, quality_flag`. |
| `build_speaker_log.py` | Regenerates `minutes_speaker_log.csv` from `../meeting_minutes/minutes/`. Deterministic/idempotent. |
| `AVAILABILITY.md` | Avenues checked + verdict + JSON. |

## CRITICAL distinction (do not violate)
`minutes_speaker_log.csv` is **not** a comments dataset. It is the clerk's third-person
summary of in-person speakers — the public's *reported* topics, not the public's *own
submitted words*. Never merge it into `all_comments_clean.csv`, never present it as
"public comments," and always carry the header note. (See
`references/extraction_standards.md`, "What counts as a public comment.")

## Regenerating the speaker log
```bash
python3 public_comments/build_speaker_log.py
# files scanned: 504 | files with speakers: 164 | speaker rows: 635  (rebuilt 2026-07-02 after the 2022 minutes re-carve/re-OCR)
```
The parser: finds the `Public Comments` heading, reads to the next section
(`Mayor Comments` / `Council member Comments` / `Public Hearing` / `Adjourn` / …),
splits paragraphs on a Capitalized name-lead followed by a speech verb, and rejects
mis-splits (council/staff titles, place/org words, pronoun leads, sentence-boundary
fragments). Mis-split fragments are re-appended to the prior real speaker so no
paraphrase text is lost.

## If revisited
The only way to get genuine submitted comment text is a **GRAMA request** to the City
Recorder for the comments "entered into the record" of specific meetings — they are
retained but not proactively published.
