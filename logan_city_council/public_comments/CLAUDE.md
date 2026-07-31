# public_comments/ — Logan (Logan Municipal Council)

## TL;DR verdict: IN-MINUTES-ONLY (SUBMIT-ONLY / NOT PUBLISHED)
Logan takes public comment **in person only** (microphone, name + city, 3-minute limit).
The City Recorder paraphrases each speaker in the third person inside the minutes. There
is **no online eComment portal, no written-comment web form, no "correspondence received"
packet attachments, and no published verbatim resident text**. So there is **no genuine
published written-comments dataset** for this city. Full avenue-by-avenue audit in
`AVAILABILITY.md`.

## Files
| File | What it is |
|---|---|
| `all_comments_clean.csv` | **Header-only by design.** Genuine public-submitted written/online comments are NOT published by Logan, so there is nothing to put here. Do NOT populate it from minutes paraphrases. |
| `minutes_speaker_log.csv` | **MEETING-RECORD NOTES, NOT public comments.** Clerk third-person paraphrases of people who spoke IN PERSON under "QUESTIONS AND COMMENTS FOR MAYOR AND COUNCIL" and in PUBLIC HEARINGS. Columns: `date_normalized, contact_name, subject, comment, source_file, quality_flag`. |
| `build_speaker_log.py` | Regenerates `minutes_speaker_log.csv` from `../meeting_minutes/minutes/**/*.md` (preferred) or `raw/*.txt` (seed fallback). Deterministic / idempotent. |
| `raw/` | Seed source: sampled minutes PDFs + `pdftotext -layout` output used before the markdown corpus existed. |
| `AVAILABILITY.md` | Avenues checked (with URLs) + verdict + JSON. |

## CRITICAL distinction (do not violate)
`minutes_speaker_log.csv` is **not** a comments dataset. It is the clerk's third-person
summary of in-person speakers — the public's *reported* topics, not the public's *own
submitted words*. Never merge it into `all_comments_clean.csv`, never present it as
"public comments," and always carry the header NOTE line. (See
`references/extraction_standards.md`, "What counts as a public comment.")

## Regenerate if minutes change
The speaker log was built from the full minutes corpus (186 md files, 2020-01 → 2026-06,
**632 rows**). If the minutes agent adds/updates meetings in `../meeting_minutes/minutes/`,
re-run to refresh (idempotent):
```bash
python3 public_comments/build_speaker_log.py
# prints: source files: N | speaker rows: N | by date: {...}
```
The parser handles both minute phrasings: `"Name, a resident of Logan …"` (2020–2025) and
`"Logan resident Name addressed the Council …"` (2026). It excludes council/staff/mayor
response lines. It also reads RDA-meeting minutes that share the same evening; source_file
identifies the meeting/body.

## If revisited
The only way to obtain genuine submitted text would be a **GRAMA request** to the City
Recorder (`loganrecordrequest@loganutah.gov`) for any written materials entered into the
record — but Logan does not proactively publish such text, and routine comment is oral.
