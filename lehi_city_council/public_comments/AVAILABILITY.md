# Public comments — availability & verdict (Lehi, UT)

## VERDICT: IN-MINUTES-ONLY (genuine written comments) + SUBMIT-ONLY (the live portal)

Two findings, kept distinct:

1. **Genuine published written/online comments DO exist — but only inside the 2020
   COVID-era minutes.** During the virtual-meeting period (spring–summer 2020) Lehi
   reproduced residents' **own verbatim** written/online/email/eComment text as an
   appendix to (or inline in) the council minutes. That reproduced text is the
   public's own words, published by the city → it belongs in `all_comments_clean.csv`.
   **42 such comments** were extracted from 4 meetings (2020-03-30, 2020-04-13,
   2020-06-08, 2020-06-22). This practice **stopped once in-person meetings resumed**;
   no later minutes reproduce submitted written comments.

2. **The ongoing eComment / SpeakUp portal is SUBMIT-ONLY (not published).** Lehi runs
   Granicus **SpeakUp** (`lehi.granicusideas.com`) as a per-meeting eComment tool.
   Residents pick a position (Support/Oppose/Neutral) and type a comment on an agenda
   item before the meeting; that text is routed to the clerk/council for the record but
   is **never publicly displayed or archived** on the portal. There is no published
   written-comment archive, no correspondence page, and the minutes only *note* who
   spoke in person.

So: `all_comments_clean.csv` is **populated (42 rows, 2020 only)**, and a separate
`minutes_speaker_log.csv` (148 rows) captures the clerk's paraphrases of in-person
Citizen-Input speakers — which are **meeting-record notes, NOT** public-submitted
written comments and are kept out of the comments CSV per extraction_standards.md.

## Avenues hunted (all standard sources checked, with URLs)

1. **eComment / SpeakUp portal (the key question)** — `https://lehi.granicusideas.com/`
   (linked from the Granicus archive: "To add comments to a meeting that is in progress,
   please visit our SpeakUp site").
   - `…/meetings?scope=past` lists **266 past meetings** (City Council, RDA, Local
     Building Authority, Planning Commission). Opened multiple **City Council** meetings
     (e.g. `/meetings/1101-city-council`, 1100, 1082, 1078, 1041) and their per-agenda-item
     pages (e.g. `…/agenda_items/693b713bf2b6702bec000186-3-20-minute-citizen-input`).
   - **Closed meetings show only** `"The online Comment window has expired"` — no
     archived submissions.
   - On the **open** upcoming meeting (`/meetings/1138-planning-commission`) every agenda
     item renders only an **empty submission form** (position selector + empty textarea +
     a spam-honeypot field). No other resident's submitted comment text or author name is
     shown (`comment_author` tokens = 0). The `…ecomments` comment section is empty/hidden.
     → submissions are **not** publicly displayed. **eComment is submit-only.**
   - Probed AJAX endpoints (`/agenda_items/<id>/ecomments`, `/ecomments?agenda_item_id=…`)
     → 404/500; no public read API for submitted comments.

2. **Granicus archive / agenda packets** — `https://lehi.granicus.com/ViewPublisher.php?view_id=1`.
   The archive table exposes an **"eComment / Register to speak"** column only for
   *Upcoming* events (a submission button → SpeakUp); past rows offer Video/Agenda/Minutes
   only. Agenda documents are served via `DocumentViewer.php`. No "correspondence received"
   / "written comments received" bundle of resident text was found attached.

3. **City website** — `https://www.lehi-ut.gov/government/meetings-and-agendas/`
   instructs residents to "select eComment next to the Agenda" or **email elected officials
   directly**; in-person 3-minute Citizen Input rules at
   `https://www.lehi-ut.gov/wp-content/uploads/2024/01/Citizen-Speaker-Rules.pdf`.
   **No published public-comment / correspondence archive** anywhere on the city site.

4. **Inside the minutes** — Born-digital minutes PDFs (Granicus `DocumentViewer`).
   - **2020 (COVID, virtual):** submitted written/online/email/eComment text was
     **reproduced verbatim** — e.g. 2020-03-30 "Comments for the March 31st City Council
     Meeting" appendix (Dancing Moose Montessori daycare controversy), 2020-04-13
     forwarded-email appendix (Bull River Road rezoning), and inline items
     ("There was a comment submitted online by Steve Moulton: …", 2020-06-08; "Below are
     the public comments submitted online through eComment", 2020-06-22). → **harvested into
     `all_comments_clean.csv`.**
   - **2021–present:** the minutes only **paraphrase** in-person Citizen-Input and
     public-hearing speakers ("Casey Glade expressed concerns with …") — clerk records, not
     residents' own text → `minutes_speaker_log.csv`, never the comments CSV.

5. **Records / transparency** — submission channels are the SpeakUp eComment tool, email to
   officials, or in-person speaking. None of these produce a published written-comment
   archive (GRAMA request would be required for the raw eComment submissions).

## How the public submits (for the record)
Granicus **SpeakUp eComment** per meeting (`lehi.granicusideas.com`, written comment due by
noon on meeting day), OR **email the Mayor/Council directly**, OR **in-person** 3-minute
Citizen Input / public-hearing testimony. Only the **2020 virtual-meeting** submissions were
ever published (reproduced in the minutes).

## Files
| File | Contents |
|---|---|
| `all_comments_clean.csv` | **42** genuine verbatim written/online/email/eComment comments the city published in the 2020 minutes (SLC schema). |
| `all_comments_dropped.csv` | 9 segmentation artifacts dropped (minutes attest blocks + signature tails). |
| `minutes_speaker_log.csv` | **160** in-person Citizen-Input speakers (2020–2026), clerk PARAPHRASES — **NOT** written comments. |
| `extract_comments.py` | Deterministic extractor for the 2020 reproduced written comments (copies text verbatim). |
| `extract_speaker_log.py` | Deterministic extractor for the in-person speaker log. |
| `raw/` | Raw text of the 2020 comment appendices / inline comments as pulled from the minutes. |

## Caveat on extraction fidelity
Comment **text is verbatim** from the minutes. The 2020 appendices are irregularly
formatted (mixed forwarded-email headers + informal first-name sign-offs + a few
unsigned letters), so a small number of long rows may bundle more than one resident's
letter where the minutes gave no clear separator, and a few names are first-name-only or
blank (anonymous). No text was invented; uncertain fragments were routed to
`all_comments_dropped.csv`.

```json
{"verdict":"in-minutes-only","locations":["2020 COVID-era council minutes (reproduced verbatim written/online/email/eComment) -> all_comments_clean.csv","Granicus SpeakUp eComment portal https://lehi.granicusideas.com = submit-only, not published","minutes Citizen-Input paraphrases -> minutes_speaker_log.csv (not comments)"],"notes":"42 genuine published written comments, all 2020 (4 meetings). Ongoing eComment/SpeakUp is submit-only: residents submit position+text per agenda item but nothing is publicly displayed or archived; closed meetings show only 'comment window has expired'. 2021-present minutes only paraphrase in-person speakers (160-row speaker log)."}
```
