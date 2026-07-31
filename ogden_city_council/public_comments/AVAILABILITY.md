# Public comments availability — Ogden, Utah (City Council, 2020–present)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED.**

Ogden City accepts genuine written/online public comment, but it does **not publish the
submitted text anywhere public**. Comments are forwarded to the Council and "entered into
the record," but no verbatim written-comment document, page, portal, or packet attachment
exists. `all_comments_clean.csv` is therefore header-only (legitimate empty result).

> The only public-facing record of public input is the City Recorder's **third-person
> paraphrase** of in-person speakers in the meeting minutes. That is a *meeting-record note*,
> NOT a public-submitted comment, and lives in `minutes_speaker_log.csv` — never in
> `all_comments_clean.csv`. See `references/extraction_standards.md` ("What counts as a
> public comment").

---

## Avenues checked (auditor brief items 1–6)

### 1. Dedicated published-comment page — NONE
- `https://www.ogdencity.gov/736/Ways-to-Comment` (a.k.a. `…/publicinput`, which 301-redirects
  here) is a **submission** page only: it explains how to comment in person, lists the online
  form, the voicemail line **801-629-8158**, and email **citycouncil@ogdencity.com**. It
  publishes **no** previously-received comments. Key text: *"Submitted forms and messages will
  be forwarded to the City Council and entered into the record of the next Council Meeting."*
  Nothing about posting/publishing the text.
- Site search ("public comments received", "written comments", "correspondence") returns no
  comment-archive document; the search itself is JS-driven and surfaces only the procedural
  pages above.

### 2. Inside the minutes — PARAPHRASE ONLY (a speaker log, not comments)
- Regular council-meeting minutes contain a **"Public Comments"** section, but it is the
  Recorder's **3rd-person summary** of who spoke in person and what they raised
  (e.g. *"Robert Hunter discussed the importance of addressing climate change…"*). These are
  meeting-record notes, not the public's own submitted words. Extracted to
  `minutes_speaker_log.csv` (635 rows / 164 meetings / 2020–2026; rebuilt 2026-07-02 after the 2022 minutes re-carve recovered missing meetings), clearly labeled.
- Public-hearing comment on specific agenda items is likewise paraphrased inline; not
  captured here (item-specific, not the general comment period).

### 3. Agenda packets / DocumentCenter attachments — NO "written comments received" doc
- City Council agendas/packets live in the CivicPlus **DocumentCenter** (the QR-code "packet"
  target), e.g. `…/DocumentCenter/View/32188/01-21-25-Packet`. Sampled packets
  (disk-disciplined: HEAD-checked ~80–190 KB, downloaded one 3-page/122 KB packet, extracted,
  deleted):
  - The "Packet" PDF is a **thin agenda cover** whose embedded links point to **individual
    staff-report / exhibit PDFs by item name** (e.g. `…-CC-Gina-Arellano`, `…-CC-Randy-Stain`,
    `…-WS-Dino-Park-2024-Annual-Report`). These are applicant/proponent staff items, **not**
    public correspondence.
  - The only "Public Comments" content in the agenda is the **procedural notice** (item 7:
    "…limited to three minutes per person…"). No "public comments received" / "correspondence"
    attachment exists.
  - The CivicPlus **AgendaCenter** (`brand.ogdencity.com/AgendaCenter`) serves only `Agenda`
    and `Minutes` file types — no Packet/Attachment/Item types, and no correspondence entries.
    (Planning Commission agendas there have a "Review of Correspondence (if any)" agenda *line*,
    but no published comment documents are attached.)

### 4. eComment / Open City Hall / Speak-Up portal — NONE
- No PrimeGov / Granicus / CivicClerk / NovusAgenda eComment feature. Comment intake is a
  plain web form + voicemail + email (item 1). No public submission archive or export.
- **FlashVote** (`https://www.flashvote.com/ogdenut`) is a structured **survey** tool
  (anonymous, aggregate sentiment) — not free-text council comments; explicitly secondary and
  not a public-comment archive.

### 5. Records / transparency / council-correspondence archive — NONE
- `council.ogdencity.com` Archive contains only newsletters, budgets, CAFR/ACFR, action plans,
  and annual reports — **no** "public comments" or "correspondence" category.
- No open-data portal hosting council correspondence.

### 6. Email-only / phone submission — CONFIRMED, but unpublished
- Email (`citycouncil@ogdencity.com`), online form (`ogdencity.com/publicinput`), and
  voicemail (801-629-8158) are the intake channels. The city states comments are *entered into
  the record* but publishes none of the submitted text. This is a legitimate
  **SUBMIT-ONLY / NOT PUBLISHED** outcome.

---

## What would change the verdict
A **GRAMA / public-records request** to the City Recorder for the written comments "entered
into the record" for specific meetings would likely surface the actual submitted text (the
city evidently retains them as record material), but they are not proactively published. Video
transcription of spoken comment is out of scope.

## Files in this directory
- `all_comments_clean.csv` — **header-only** (no genuine published written comments exist).
- `all_comments_dropped.csv` — header-only audit trail (nothing dropped; none found).
- `minutes_speaker_log.csv` — 635 in-person speaker paraphrases from minutes
  (MEETING-RECORD NOTES, NOT public-submitted comments).
- `build_speaker_log.py` — regenerates the speaker log from `meeting_minutes/minutes/`.

```json
{"verdict":"SUBMIT-ONLY / NOT PUBLISHED","locations":[],"notes":"Genuine written/online comment is accepted via web form (ogdencity.com/publicinput), email (citycouncil@ogdencity.com), and voicemail (801-629-8158) and 'entered into the record,' but Ogden publishes no verbatim text anywhere: no dedicated page, no DocumentCenter 'comments received' doc, no AgendaCenter packet/correspondence attachment, no eComment portal, no council-correspondence archive. Minutes contain only a 3rd-person clerk paraphrase of in-person speakers -> minutes_speaker_log.csv (635 rows, 2020-2026), NOT the comments dataset. A GRAMA request would be needed to obtain submitted text."}
```
