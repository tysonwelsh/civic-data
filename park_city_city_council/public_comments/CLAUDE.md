# public_comments/ — Park City (Park City Municipal Corporation, City Council)

## TL;DR verdict: PUBLISHED
Park City **publishes genuine written/online public comments**, in two places:
1. **Verbatim inside the council minutes** — eComment submissions and emails are transcribed
   word-for-word, in quotation marks, attributed by name
   (`Jane Doe eComment: "…"` / `Name via Email: "…"`). Primary source.
2. **Forwarded resident correspondence bundled in CivicClerk agenda-packet PDFs**
   ("correspondence received" exhibits of `[External]` emails to council/planning/
   public_comments). Secondary source, intermittent.

Both are extracted to `all_comments_clean.csv` (**459 rows**, 2020–2026). The minutes *also*
paraphrase in-person speakers in the third person — those are a **separate speaker log, NOT
comments**. Full avenue-by-avenue audit in `AVAILABILITY.md`.

## Files
| File | What it is |
|---|---|
| `all_comments_clean.csv` | **The comments dataset.** 459 genuine public-submitted written/online comments. 433 quoted **verbatim** from council minutes (420 eComment + 13 email); 26 forwarded resident emails / form submissions harvested from agenda packets. SLC schema. Every row traceable via `source_file`. |
| `all_comments_dropped.csv` | Drop log — 3 rows (packet emails that exactly duplicated a minutes eComment from the same person; `_drop_reason=duplicate_name+comment_across_sources`). |
| `minutes_speaker_log.csv` | **MEETING-RECORD NOTES, NOT public comments.** 1,055 clerk third-person paraphrases of people who spoke **IN PERSON** under "PUBLIC INPUT (any matter of city business not scheduled…)". Columns: `date, meeting, section, speaker, affiliation, topic, summary, source, source_file`. Has a `#` header note. |
| `raw/` | Provenance: the build scripts + `packet_comments_cache.json` (harvested packet comments) + `packetlist.json` / `scan_results.json` (packet inventory & scan). No PDFs (disk-safe). |
| `AVAILABILITY.md` | Avenues 1–6 checked (with URLs) + verdict + JSON. |

`raw/` build scripts: `build_comments.py`, `build_speaker_log.py`, `packet_parse.py`,
`harvest_packets.py`.

## SLC schema (`all_comments_clean.csv`)
`date, contact_name, subject, topic, comment, district, source, has_attachment,
source_file, page_numbers, period_start, period_end, date_normalized, quality_flag`
- `district` always empty — Park City council is **all at-large** (no districts).
- `source` distinguishes the three origins: `eComment (… verbatim in council meeting minutes)`,
  `Email correspondence (… verbatim in council meeting minutes)`, or
  `Agenda packet correspondence (forwarded resident email / eComment-form submission; …)`.
- `comment` = the verbatim submitted text.
- For minutes comments, `date` = meeting date. For packet comments, `date` = the email's
  Sent date when available (else the packet/meeting date, flagged `date_from_packet`);
  `period_start/end` = the packet meeting date.
- `quality_flag` ∈ {``, `name_inferred`, `unbalanced_quote_recovered`,
  `unbalanced_quote_open`, `short_comment`, `from_agenda_packet`,
  `truncated_at_attachment`, `date_from_packet`} — minor extraction-confidence notes.
  `name_inferred` (17): a resident who spoke in person *also* submitted a written comment
  introduced as "He/She also submitted the following…"; the writer's name was resolved from
  the immediately preceding speaker and spot-checked against the minutes context.
  `truncated_at_attachment` (6): a packet email body was cut where its attached PDF began
  (≤5,000 chars kept); the substantive comment is intact at the start.

## CRITICAL distinction (do not violate)
`minutes_speaker_log.csv` is **not** a comments dataset. It is the clerk's third-person
summary of in-person speakers — the public's *reported* topics, not their *submitted words*.
Never merge it into `all_comments_clean.csv`, never present it as "public comments." Only the
verbatim quoted `eComment:` / `via Email:` minutes submissions and the forwarded packet
correspondence belong in `all_comments_clean.csv`.
(See `references/extraction_standards.md`, "What counts as a public comment.")
- Edge case: a few residents *read their eComment / a prepared statement aloud in person*.
  They appear in `minutes_speaker_log.csv` as in-person speakers (correct); their separately
  submitted written text, if present, is captured in `all_comments_clean.csv`.

## How it was built / regenerate
Datasets are derived deterministically. From the repo root:
```
python3 public_comments/raw/harvest_packets.py     # (optional) re-harvest packet correspondence
python3 public_comments/raw/build_comments.py       # -> all_comments_clean.csv + dropped
python3 public_comments/raw/build_speaker_log.py     # -> minutes_speaker_log.csv
```
(`build_comments.py` reads `packet_comments_cache.json`; if absent it still emits the 433
minutes comments. Paths in the scripts point at the live repo + the scratch cache copy in
`raw/`; adjust `PKT_CACHE`/paths if relocating.)

- **Minutes comments:** scan every `../meeting_minutes/minutes/**/*.md` for the marker
  `(?:via )?(eComment|Email)\s*:?\s*“`, take the verbatim text to the matching closing `”`
  (curly-quote **depth counting** to keep nested quotes; structural-boundary fallback when a
  comment's quotes are unbalanced), recover the commenter name from the text before the
  marker (with backward resolution for "He/She also submitted…" cases), scrub page/header
  artifacts, dedup on (name, comment).
- **Packet correspondence:** all 239 council agenda packets fetched as **plaintext** via the
  CivicClerk API (`GetMeetingFileStream(fileId=…,plainText=true)` — never a PDF on disk),
  parse Outlook `From: Name <non-staff-email>` … `Sent:` … `Subject:[External]` blocks routed
  to council/planning/public_comments, plus CivicPlus "Submitted by:" form relays; cut bodies
  at the attachment boundary; dedup against the minutes comments.
- **Speaker log:** within each "PUBLIC INPUT (any matter…)" section ("opened …" → "closed the
  public input"), capture paragraphs that begin `Name <speak-verb> …` (stated, asked,
  commented, urged, …). Excludes written eComment/email paragraphs (those are comments),
  sitting council (`Council Member X` / `Mayor X` / "Board Member X"), and a staff/officials
  blocklist (City Manager Matt Dias, Planning Director Erickson, City Recorder Kellogg,
  department presenters, etc.), plus agenda-heading/table false positives. **Scope limit:**
  only the dedicated PUBLIC INPUT sections are logged — speakers at specific public hearings
  are NOT separately captured because in the minutes they are interleaved with staff/applicant
  presentations and council deliberation, which cannot be split out without fabricating
  attributions. Residents who later became council members (e.g. Bill Ciraco pre-2023) are
  correctly retained for the years they spoke as members of the public.

## Provenance note
An earlier attempt was interrupted (only `raw/` existed). This run rebuilt all datasets from
scratch, reusing the prior packet inventory/scan and minutes corpus. No fabrication: every
minutes comment traces to its `source_file`; nested-quote and unbalanced-quote cases are
flagged; the 17 `name_inferred` rows were each verified against the surrounding minutes text;
packet correspondence was deduped against the minutes to avoid double-counting.
