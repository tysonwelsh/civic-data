# Public comments — availability & verdict (Vineyard, UT)

## VERDICT: SUBMIT-ONLY — genuine written public comments are NOT published

Vineyard accepts written public comment **only by email to the City Recorder**
(`robinr@vineyardutah.gov`) and does **not** publish a retrievable archive of
residents' own submitted text. There is **no eComment portal, no Open City Hall,
and no published written-comment / correspondence archive**. Therefore
`all_comments_clean.csv` is intentionally **header-only (0 rows)** — a legitimate
SUBMIT-ONLY result, not a gap.

What *does* exist is a **speaker log** of in-person public-comment speakers
paraphrased by the clerk in the meeting minutes → `minutes_speaker_log.csv`. Per
`extraction_standards.md`, those clerk paraphrases are **meeting-record notes, NOT
public-submitted written comments**, so they are kept strictly separate and never
placed in `all_comments_clean.csv`.

## Avenues hunted (all four standard sources checked)

1. **Dedicated published-comments page / archive** — NONE.
   - City site `agenda_minutes___public_notice.php` points to the CivicClerk portal
     for agendas/minutes only; it has **no** comment archive. The only comment-intake
     link is a one-off **Google Form** ("Submit your Floodplain Ordinance Public
     Comment", `forms.gle/...`) — a *submission* form for a single ordinance, not a
     published archive of resident text.
   - `city_council2.php` lists members + emails; no comment portal or archive.

2. **eComment / Open City Hall / Speak-Up portal (CivicClerk)** — NOT USED.
   - CivicClerk OData API `https://vineyardut.api.civicclerk.com/v1/`. Paged **all
     393 City/Town Council events 2014-01-08 → 2026-12-22**:
     `publicCommentsEnabled` is **`false` on every single event** (0 of 393 true).
   - The `$metadata` schema does define written-comment *submission* types
     (`PublicCommentWritten`, `EmailPublicCommentModel`, `SendEmailPublicComment`,
     `enableWrittenComment`), but these are **submission models, not retrievable
     entity sets** — probing `/PublicCommentWritten`, `/PublicComments`, `/Comments`,
     `/eComments`, `/EmailPublicComment`, `/SendEmailPublicComment` all returned
     **HTTP 404**. Vineyard has not enabled the eComment feature, so there are no
     submitted comments to retrieve.

3. **Agenda-packet attachments ("written comments received" / "correspondence")** —
   NONE FOUND (sampled, low-disk).
   - Per the disk rule (packets up to 258 MB), did NOT bulk-download. Sampled the
     **text-layer** (`plainText=true`, capped at 30 MB, each ~0.2–0.4 MB) of two
     recent City Council packets (fileId 3160 = 6/9/2026; fileId 3039 = 5/5/2026).
   - The packets' "PUBLIC COMMENTS" content is the **clerk paraphrase of in-person
     speakers** (third-person: "Cole Kelly expressed appreciation…", "Daria Evans…
     raised a concern…") — not residents' submitted text. The packet 3160 floodplain
     summary states verbatim: *"No public comments were received through email, online
     submissions, mailed correspondence, or in-person comments outside the Planning
     Commission and City Council presentations."* No "correspondence received" bundle
     of genuine written public comments was present.

4. **Records / transparency / council-correspondence archive** — NONE published.
   - Submission channel is plain email to the City Recorder; minutes themselves state
     *"Public comments can be submitted ahead of time to robinr@vineyardutah.gov."*
     No web archive of those emails is published.

## Where genuine written comments go (for the record)
Email to **City Recorder** (`robinr@vineyardutah.gov`). Not published online; not
retrievable via API or packet. Hence SUBMIT-ONLY.

## Files in this directory
| File | Contents |
|---|---|
| `all_comments_clean.csv` | **Header only (0 rows)** — genuine written/online comments; none are published (SUBMIT-ONLY). |
| `all_comments_dropped.csv` | Header only — no rows to drop (no genuine comments ingested). |
| `minutes_speaker_log.csv` | 283 IN-PERSON public-comment **speakers** paraphrased in the minutes (2020–2026). **MEETING-RECORD NOTES, NOT public-submitted written comments.** |
| `extract_speaker_log.py` | Deterministic extractor that builds the speaker log from the 138 minutes `.md` files. |
| `CLAUDE.md` | Orientation for this directory. |

## Reproduce
```bash
# eComment never enabled (0/393 events):
#   paged Events?$filter=(categoryName eq 'City Council' or categoryName eq 'Town Council')
#   all publicCommentsEnabled == false
python3 extract_speaker_log.py     # rebuilds minutes_speaker_log.csv
```
