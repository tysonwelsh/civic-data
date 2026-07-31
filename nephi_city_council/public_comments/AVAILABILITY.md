# Public comments — availability & verdict (Nephi, UT)

## VERDICT: IN-MINUTES-ONLY — genuine published written comments do NOT exist

Nephi handles public comment **in-meeting only**. The city publishes **no genuine
written / online public comments** anywhere: no dedicated comment page, no
"correspondence / written comments received" archive, no eComment / Speak-Up / Open
City Hall portal, and no comment bundles attached to agenda packets. The only trace of
public comment is the **clerk's third-person paraphrase of in-person speakers inside the
council minutes** (e.g. "PUBLIC COMMENT:" sections, public-hearing testimony). Per
`extraction_standards.md`, those paraphrases are **meeting-record notes, NOT
public-submitted written comments**, so:

- `all_comments_clean.csv` is intentionally **header-only (0 rows)** — the correct
  IN-MINUTES-ONLY result, not a gap.
- The in-person speakers are captured separately in `minutes_speaker_log.csv`
  (`116` rows) and must **never** be moved into the comments CSV.

This matches and confirms the recon finding ("comments are in-minutes only").

## Avenues hunted (all standard sources checked, with URLs)

1. **Dedicated published-comments / correspondence page** — NONE.
   - City site is CivicPlus **CivicEngage** (`https://www.nephi.utah.gov`). Searched the
     site and the City Council pages (`/580/City-Council`, `/268/Mayor-and-City-Council`,
     `/345/City-Councilmembers`) — no "public comment", "written comment", "public
     input", "correspondence", or "communications received" page or archive exists.
   - No instructions for submitting written comment are published; participation is
     in-person at the Tuesday meeting / public hearings (City Hall, 21 E 100 N;
     435-623-0822).

2. **CivicPlus AgendaCenter — agenda packets / attachments** — NO written-comment bundles.
   - `https://www.nephi.utah.gov/AgendaCenter`. City Council exposes only **Agenda** and
     **Minutes** document types (plus Videos / Previous Versions). There is **no**
     "Agenda Packet", "Correspondence", or "Written Comments Received" document type or
     category for City Council. (Advisory Committees offer a "Packet" format, but no
     correspondence content.)
   - Downloaded and inspected a representative City Council **agenda** PDF
     (`/AgendaCenter/ViewFile/Agenda/_06172025-383`): it is a plain **2-page** agenda
     listing "7. Public Comment" as an agenda item — **no attached resident letters /
     correspondence**. Agendas are thin lists, not packets with exhibits.

3. **eComment / Speak-Up / Open City Hall portal** — DOES NOT EXIST.
   - Nephi's CivicEngage AgendaCenter has **no eComment feature enabled** and there is no
     Granicus SpeakUp / PrimeGov / CivicClerk Open City Hall portal linked anywhere on
     the site. Small rural city (~6,500 pop.) — no online-comment intake at all.

4. **Inside the minutes (where comment actually lives)** — TRANSCRIBED AS PARAPHRASE.
   - Born-digital text-layer minutes PDFs (2020–present), harvested to
     `meeting_minutes/minutes/**/*.md`. Public comment appears two ways:
     - a flush-left **"PUBLIC COMMENT:"** section; most meetings record **"NO PUBLIC
       COMMENT"** or **"There was no public comment."**, but some list speakers
       paraphrased in third person (e.g. the 2021-06-15 Clothes Spin RV Park discussion:
       "Bobby Luckau who is a resident … asked …", "Janet Johnson asked the council …");
     - inline under a hearing: "Mayor … opened the meeting up for public comment.
       <Name> addressed the council about …" (e.g. Jaboe Garret re: a slaughterhouse).
   - These are the **clerk's words about who spoke**, not residents' own submitted
     written text → captured in `minutes_speaker_log.csv`, kept OUT of the comments CSV.

5. **State Public Notice mirror (PMN)** — agendas/notices only, no comment archive.
   - `https://www.utah.gov/pmn` mirrors Nephi agendas/minutes/notices. It carries public
     **hearing notices**, not residents' submitted written comments.

6. **Records / transparency / email-only submission** — no published archive.
   - Comment is accepted in person (and presumably by phone/email to City Hall), but the
     city publishes **nothing in writing**; the minutes only *note who spoke*. This is a
     legitimate "not published in writing" outcome.

## How the public participates (for the record)
In-person at the 1st & 3rd Tuesday 7:00 p.m. council meeting / public hearings (21 E 100
N). No online comment portal, no published written-comment or correspondence archive.

## Files in this directory
| File | Contents |
|---|---|
| `all_comments_clean.csv` | **Header only (0 rows)** — genuine written/online comments; none are published (IN-MINUTES-ONLY). SLC schema. |
| `all_comments_dropped.csv` | Header only — no genuine comments ingested, nothing to drop. |
| `minutes_speaker_log.csv` | **116** in-person public-comment **speakers** paraphrased in the minutes (2020–present). **MEETING-RECORD NOTES, NOT public-submitted written comments.** |
| `extract_speaker_log.py` | Deterministic extractor that builds the speaker log from `meeting_minutes/minutes/**/*.md` (verbatim; no fabrication). |
| `CLAUDE.md` | Orientation for this directory. |

## Reproduce
```bash
python3 extract_speaker_log.py     # rebuilds minutes_speaker_log.csv
```

```json
{"verdict":"in-minutes-only","locations":["council minutes 'PUBLIC COMMENT:' sections + inline hearing comments -> minutes_speaker_log.csv (clerk paraphrases, NOT comments)","no published written-comment/correspondence archive on nephi.utah.gov","CivicPlus AgendaCenter: City Council has Agenda+Minutes only, no packet/correspondence attachments","no eComment/Speak-Up/Open City Hall portal"],"notes":"Genuine published written/online comments = NONE (header-only all_comments_clean.csv). Public comment is in-person only and survives solely as clerk paraphrase inside the minutes; most meetings record 'NO PUBLIC COMMENT'. 116 speaker-log rows extracted."}
```
