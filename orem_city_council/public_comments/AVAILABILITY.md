# Public comments — availability (Orem, Utah)

**Verdict: IN-PACKETS** — genuine public-submitted **written** comments ARE
published, but only as **verbatim attachments embedded at the end of the
2020–2021 City Council minutes documents** (the COVID electronic-meeting era,
when the public submitted written comments in lieu of speaking in person). They
are not surfaced on any standalone comments page or eComment portal. Outside that
window, written comments are not published; in-person speakers survive only as
clerk paraphrases (see speaker log).

## What we found (the genuine dataset)

`all_comments_clean.csv` — **95 genuine resident written comments** across **9
meetings** (2020-07-14 → 2021-03-23). `source = minutes_attached_written`. During
the electronic-meeting period each minutes doc states:

> *"Those wishing to make a comment provided staff with written comments… The
> public comments submitted were read into the record. Comments… are attached to
> the end of the minutes in their entirety."*

— and the residents' **own verbatim submitted text** is printed at the end of the
PDF/markdown (name line + their full comment). That is genuine public-submitted
written text published by the city = it qualifies for `all_comments_clean.csv`.
`all_comments_dropped.csv` (4 rows) removes developers / applicant agents /
real-estate reps commenting in a business capacity, each with a `_drop_reason`.
`raw/` holds the 9 comment-bearing source `.md` files.

`date_normalized` is 100% populated (meeting date; `date_from_filename` flag).
9 anonymous submissions kept with `no_name` flag.

## Avenues checked

| # | Avenue | URL / endpoint | Result |
|---|---|---|---|
| 1 | Dedicated published-comments page | orem.gov (council recap, transparency) | **None.** `orem.gov/councilrecap/` is a staff blog. `orem.gov/transparency` returned HTTP 503 (bot-blocked) at check time; recon found no comment archive there. |
| 2 | CivicClerk written-public-comment feature | `https://oremut.api.civicclerk.com/v1/Events` — field `publicCommentsEnabled`; actions `PublicCommentWritten`, `SendEmailPublicComment`, `PublicCommentSignUp` | **PORTAL-GATED / never enabled.** Verified via OData filter: `publicCommentsEnabled eq true` → **0 events**; `eq false` → **254** (all of them). The submit/sign-up feature exists in the platform but is **disabled on every Orem event**, so no written comments are accepted or published through it. |
| 3 | Agenda-packet "Correspondence" / "Written Comments Received" attachments | CivicClerk `publishedFiles` (type `Agenda Packet`, 99 across CC events 2021–2026) **and** Google Drive "Agendas-City Council" (`1jCLlNKyu1yGkYyefk0YM6cPG3_d90unz`, year/meeting subfolders) | **No correspondence section.** CivicClerk packet files are SPA/auth-gated (portal stream URL returns the JS shell, not the PDF). Sampled 2 packets from Google Drive — **2022-02-22** (146 pp.) and **2024-09-17** (13 pp.): neither contains a "Correspondence"/"Written Comments Received" section or bundled resident emails (no `From:/Sent:/Subject:` blocks). Packets = staff reports / ordinances / resolutions / board-application forms only. (Each packet downloaded → scanned → **deleted immediately**; disk guard respected.) |
| 4 | Records / council-correspondence archive | — | None located. |

## Submit channel (how the public submits today)

The CivicClerk portal exposes written/email public comment + sign-up-to-speak
(`PublicComment*` OData actions), but `publicCommentsEnabled=false` everywhere, so
the present-day intake is effectively **submit-only / not published back**. The
only place genuine written comments were ever published is the 2020–2021 minutes
attachments captured here.

## Not counted (and why)

Clerk paraphrases of in-person speakers in the minutes (e.g. *"Ethan Harris stated
he lives in the Hillcrest historic neighborhood…"*) are **meeting-record notes,
not public-submitted text** — per `extraction_standards.md` they do NOT belong in
`all_comments_clean.csv`. They live in `minutes_speaker_log.csv` (60 rows) with a
header note. Never conflate the two.
