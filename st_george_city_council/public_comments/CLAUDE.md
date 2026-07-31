# Public Comments — St. George, Utah

This directory holds the public-comment data in a **final two-file structure**. The two
files are kept strictly separate and must never be conflated:

| file | what it is | rows |
|---|---|---|
| **`all_comments_clean.csv`** | **THE canonical comments dataset** — genuine public-submitted **written/online** comments (`source=written_published`), 2023→2026 | **136** |
| **`minutes_speaker_log.csv`** | **Meeting-record notes, NOT public comments** — in-person speaker names/dates/topics extracted from the minutes (`source=in_person_minutes`) | **132** |
| `all_comments_dropped.csv` | audit trail of rows removed from the clean set, each with `_drop_reason` | 11 |

At-large city → `district` is always blank.

> ### Header note for `minutes_speaker_log.csv` — READ THIS
> **`minutes_speaker_log.csv` is NOT a public-comment dataset.** It is a log of
> **meeting-record notes**: the third-person speaker entries that the St. George minutes
> record for the in-person "COMMENTS FROM THE PUBLIC" section. The minutes do **not**
> transcribe what speakers said — each row captures only the **speaker's name + meeting
> date + topic (when stated)** plus a video timestamp. These are the clerk's record of who
> spoke, not the public's own submitted words. Per the extraction standard
> (`build-city-data-repo/references/extraction_standards.md`, "What counts as a public
> comment"), clerk paraphrases of in-person speakers are **not** public comments and are
> deliberately kept OUT of `all_comments_clean.csv`. Never present this speaker log as the
> comments dataset.

## Canonical schema (`all_comments_clean.csv`, SLC schema)

```
date,contact_name,subject,topic,comment,district,source,has_attachment,source_file,page_numbers,period_start,period_end,date_normalized,quality_flag
```

`source` is always `written_published`. `date_normalized` is 100% populated (ISO).

### Per-year counts (`all_comments_clean.csv`, by submission date)

| year | written comments | published PDFs in raw/ |
|---|---|---|
| 2023 | 32 | 13 |
| 2024 | 39 | 13 |
| 2025 | 40 | 18 |
| 2026 (partial, thru ~Jun) | 25 | 9 |
| **total** | **136** | **53** |

~121 unique written commenters. See `AVAILABILITY.md` for the availability verdict and the
pre-2023 gap.

---

## `all_comments_clean.csv` — written, published  (`source=written_published`)

The city publishes written public comments by year on
`https://sgcityutah.gov/government/city_council/public_comments.php`. Residents submit via a
JotForm / email to `public-comments@sgcity.org`; the recorder batches each ~weekly
**noon-to-noon window** into one PDF ("Public Comments Received noon on <date> – noon on
<date>.pdf") and posts it. Many windows are empty ("No comments received") and simply aren't
posted.

- **Scraped** the page HTML → **53 unique comment PDFs** → downloaded verbatim to
  `raw/<year>/` (2023: 13, 2024: 13, 2025: 18, 2026: 9). Files also exist on the Revize
  host `cms3.revize.com/revize/stgeorge/...`; we pulled from the canonical `sgcityutah.gov`
  path. URL/window manifest: `comments_json/_manifest.json`. A June 2026 re-scan of the
  page confirmed **all published written-comment files 2023→2026 are captured** — 0 missed.
- **Extracted** each PDF into individual comment rows (one row per distinct
  submitter-submission) by reading the PDF directly. A single PDF bundles many forwarded
  comments.
- **Formats:** born-digital JotForm/email forwards (2024-2026, clean text) **and scanned
  image PDFs** (most of 2023 + a few 2024) containing typed letters *and handwritten
  letters* — these were transcribed via vision (`[illegible]` where unreadable).
- Per-PDF structured intermediates live in `comments_json/<pdf-basename>.json`
  (`comments[]` + `dropped[]`); the CSV is rebuilt from them by `build_clean_csv.py`.

### Genuineness verification

A ~12-row sample spanning 2023→2026 was traced back to the raw PDFs. Every sampled row is a
genuine member of the public submitting their own written comment via web form, email, or
letter (e.g. Betty Kincaid, April McKee, Martin Lane (2023); the Mojave Crossing/SunRiver
hotel wave and airport-hangar wave (2024–25); Jami Leavitt endorsements, utility and
traffic-safety complaints (2026)). City-manager "Fwd:" wrappers on some resident emails are
administrative routing only; the substance is the resident's. Non-comment material —
petition signature sheets, attachment-only exhibits (billing records, internal city policy
docs, research PDFs), and duplicate forwards — was routed to `all_comments_dropped.csv`.
The verification caught one row that had slipped through (a "Mike McKee" May 2023 entry that
was actually a bare cover note attached to a third-party academic paper, "Effectiveness of a
Citizen Review Board" by James Dilmore, with no citizen comment text) — moved to the dropped
CSV as `attachment_only`. **All remaining 136 rows are confirmed genuine public comments.**

## `minutes_speaker_log.csv` — in-person speaker notes  (`source=in_person_minutes`)

Extracted from the **Regular-meeting minutes** (see header note above — these are
meeting-record notes, **not** public comments, and are NOT part of `all_comments_clean.csv`).

> **The minutes do NOT transcribe the body of in-person public comments.** St. George's
> "COMMENTS FROM THE PUBLIC" section records, per speaker, only a line like
> `Link to comments [made] by|from resident <Name> [regarding <topic>]: <HH:MM:SS>` — the
> speaker's name and (rarely) a topic, plus a video timestamp. The actual spoken words live
> only in the meeting recording.

- `comment` = the stated topic when present, otherwise a placeholder noting the text isn't
  transcribed; such rows carry `quality_flag = minutes_pointer_no_text`. No comment text was
  fabricated.
- Procedural / staff lines ("Mayor … outlining the rules for speaking", "… thanking those
  that have commented") are filtered out, not emitted.
- This source is the **only** trace of public participation for **2022** (24 rows) and for
  in-person speakers in 2023+. It does NOT count toward the 137 written comments.

---

## Cleaning rules applied (mirror SLC `clean_comments.py`)
- One row per submitter-submission; a multi-page letter = one row; a mass form-letter sent
  by different people = one row per signer.
- OCR / forwarding artifacts scrubbed (`sgcity. org`→`sgcity.org`, jotform/comments email
  headers stripped, wrapped lines re-joined).
- Dates normalized to ISO `date_normalized`; when a comment has no own date it falls back to
  the window end date (`quality_flag=date_from_filename`).
- Flags (`|`-joined): `no_name`, `short_comment`, `date_from_filename` (written);
  `minutes_pointer_no_text` (speaker log).
- **Routed out / dropped → `all_comments_dropped.csv`** (`_drop_reason`), 11 rows:
  - `petition_signature_sheet` ×4 — ~194 pages of the May 2023 "Restoring Trust in
    Washington County" petition (signed hardcopy + online form rosters with identical canned
    text). Represented once via its organizational comment; individual signers are not
    emitted as separate comment rows.
  - `attachment_only` ×4 — referenced report/slide-deck/exhibit attachments with no comment
    body (e.g. "Washington County at a Crossroads", a hotel-crime research doc, the Jennifer
    Wilson utility-billing exhibit packet, and the "Mike McKee" Citizen-Review-Board research
    paper caught during genuineness verification).
  - `duplicate_forward` ×3 — exact duplicate forwards of a comment already captured.

## Deduplication
- **Within written**: same `contact_name` + `date_normalized` + comment gist (overlapping
  windows) → keep one.
- The written stream and the in-person speaker log are kept in **separate files**, so no
  cross-source merge/dedup is applied to the clean comments dataset.

## Notable comment waves (signal)
- **Dec 2024 – Feb 2025:** large opposition wave to the **Mojave Crossing / SunRiver hotel**
  (107-room hotel by a 55+ community), ~30+ written comments.
- **Feb–Mar 2025 & May 2025:** opposition to the **non-commercial airport hangar leasing
  policy** (pilots/SUAA asking to table the vote).
- **May 2023:** reaction to the council **limiting in-person public comment**, plus the
  county election-integrity petition drive.
- Recurring themes: water supply / overdevelopment, traffic & pedestrian safety,
  parks/pickleball, the Northern Corridor / public-lands.

## Gaps / honest caveats
- **No 2022 written comments** (not published) and **no pre-2023 written comments** anywhere
  online (see `AVAILABILITY.md`). 2022 is covered by the in-person speaker log only.
- Speaker-log rows are **names + topics, not verbatim text** — by the nature of the minutes.
  Video transcription of spoken comment is a deferred future option (out of scope).
- 2026 is a **partial year** (data through ~June 2026).
- Commenter contact info (email/phone/address) is redacted in the source PDFs and is not in
  the dataset.

## Regenerate
```
python3 public_comments/build_clean_csv.py       # rebuild CSVs from comments_json/*.json
```
Raw PDFs in `raw/` are the immutable source of truth; re-extract a written PDF by reading it
and overwriting its `comments_json/<basename>.json`.

> Do NOT run `extract_comments.py` to (re)build the comments dataset — it pulls in-person
> minutes speakers and would mix meeting-record notes into the written-comment stream. The
> canonical `all_comments_clean.csv` is written-only.
