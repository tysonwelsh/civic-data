# Public-comment availability audit — Logan (Logan Municipal Council)

Scope: 2020–present. Audited 2026-06-26. Question: does Logan publish **genuine
public-submitted written/online comments** to the City Council anywhere public, before we
conclude they are unavailable?

## TL;DR verdict: IN-MINUTES-ONLY (a.k.a. SUBMIT-ONLY / NOT PUBLISHED)

Logan accepts public comment **in person only** — step to the microphone, give name +
city of residence for the record, 3-minute limit. The City Recorder then **paraphrases**
each speaker in the third person inside the meeting minutes (under "QUESTIONS AND COMMENTS
FOR MAYOR AND COUNCIL" and within PUBLIC HEARING sections). There is **no online eComment
portal, no written-comment web form, no "correspondence received" packet attachments, and
no published verbatim resident-submitted text** anywhere. The minutes paraphrases are a
**speaker log** (the public's *reported* topics, recorded by the clerk), NOT the public's
own submitted words — so they are NOT the public-comments dataset and live only in
`minutes_speaker_log.csv`. `all_comments_clean.csv` is header-only by design.

This is an honest "in-minutes-only" outcome, not a failure to find a portal.

## Avenues checked (brief items 1–6)

| # | Avenue | Checked | Result |
|---|--------|---------|--------|
| 1 | Dedicated comment / correspondence page | City Council page `https://www.loganutah.gov/government/city_council/index.php`; "Notices and Hearings" `https://www.loganutah.gov/government/city_council/notices_and_hearings.php` | **None.** No "public comment", "written comment", "public input", "correspondence", or "communications received" page. Council page lists members, agendas, minutes, audio/video, notices only — no comment-submission guidance. |
| 2 | Inside the minutes (transcribed/paraphrased) | Read 8 sampled minutes PDFs (2023-11-07, 2023-11-21, 2023-12-05, 2026-01-06, 2026-02-03, 2026-03-03, 2026-04-07, 2026-05-05); full md corpus being processed in `../meeting_minutes/minutes/` | **YES — clerk paraphrase only.** Every regular meeting has "QUESTIONS AND COMMENTS FOR MAYOR AND COUNCIL"; named in-person speakers + their topics are summarized in the third person. Public-hearing speakers likewise (name + "a resident of Logan"). These are speaker-log records, **not** published written comments. Captured in `minutes_speaker_log.csv`. |
| 3 | Agenda packets — "written comments received" / correspondence attachments | Per-year packet pages, e.g. `https://www.loganutah.gov/government/city_council/2025_council_agendas_and_packets.php` | **None.** Packet listings contain agendas, resolutions, ordinances, notices, staff memos, and "DRAFT Minutes" — **no** documents labeled correspondence / written comments / public comments received / communications / letters. |
| 4 | eComment / Open City Hall / SpeakUp / portal feature | Vendor check (recon): site is a custom **Revize CMS**, no Granicus/Legistar/PrimeGov/CivicClerk/NovusAgenda. Web searches for Logan eComment / Open City Hall / SpeakUp | **None enabled.** No online-comment feature exists; nothing to export or recover via Wayback. Comment is in-person at the microphone (verbatim from minutes: "stepping to the microphone and giving his or her name and address for the record … limited to … three (3) minutes"). |
| 5 | Records / transparency / GRAMA / open-data | City Recorder `https://www.loganutah.gov/government/mayor_s_office/city_recorder/index.php`; GRAMA form `https://cms9files.revize.com/loganut/departments/comdev/GRAMA%20Request3.pdf`; records email `loganrecordrequest@loganutah.gov` | **Records access only, not a comments archive.** GRAMA is a records-request channel (minutes, ordinances, contracts), not a published correspondence/comment dataset. No open-data / "council correspondence" archive. |
| 6 | Email-only submission with no publication | Council member emails listed on the Council page; no comment intake address | **Confirmed not published.** No dedicated comment email that is then published; the only writing the city publishes about a comment is the clerk's paraphrase in the minutes. |

## What the minutes give (speaker log, not comments)

- Section: **"QUESTIONS AND COMMENTS FOR MAYOR AND COUNCIL"** (non-agenda items) and
  per-item **PUBLIC HEARING** sections.
- Two phrasings across years, both parsed:
  - 2020–2025: `"Name, a resident of Logan <verb> …"`
  - 2026: `"Logan resident Name addressed the Council …"`
- Captured to `minutes_speaker_log.csv` (columns
  `date_normalized, contact_name, subject, comment, source_file, quality_flag`) by
  `build_speaker_log.py`. Verbatim example (2023-11-07): *"Keaton Papke, a resident of
  Logan is in opposition to the proposed Woodsonia development…"* — a third-person clerk
  summary, not a resident-submitted document.

## Status / regeneration note

The council-minutes markdown corpus (`../meeting_minutes/minutes/`) was being populated by
the minutes agent during this audit and filled in to near-complete by the end: 186 minutes
files spanning 2020-01 through 2026-06, yielding **632 speaker rows** across the full
window. If the minutes agent adds any remaining meetings, **re-run** to refresh:

```bash
python3 public_comments/build_speaker_log.py
```

The script is idempotent, prefers `../meeting_minutes/minutes/**/*.md`, and falls back to
the sampled `public_comments/raw/*.txt` only if no markdown exists.

## Verdict

```json
{"verdict":"in-minutes-only","locations":["Logan Municipal Council minutes — 'QUESTIONS AND COMMENTS FOR MAYOR AND COUNCIL' and PUBLIC HEARING sections (clerk third-person paraphrase of in-person speakers); NOT published written comments"],"notes":"No online eComment/Open City Hall/SpeakUp portal (custom Revize CMS). No written-comment web form or comment email that is published. No 'correspondence received'/'written comments' attachments in agenda packets. GRAMA records channel exists but is not a comments archive. Comment is in-person only (name + city, 3-min). Therefore all_comments_clean.csv is header-only; in-person speakers are recorded in minutes_speaker_log.csv as a speaker log, never as the comments dataset."}
```
