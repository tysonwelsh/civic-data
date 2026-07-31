# public_comments — Murray City: availability audit

**Verdict: NO published written-comment archive. `all_comments_clean.csv` is header-only
(an honest empty), the SCHEMA_SPEC standard for a city that publishes no comments dataset.**

Murray City accepts public comment only **live at meetings** (in person / via the
`murraycitylive.com` livestream) and **by email** to council/commission staff. It does
**not** operate an eComment / Open City Hall / "correspondence received" portal, and it
does **not** post a written-comment or letters-received archive anywhere on its site.
The only comment *content* that reaches the public record is the **clerk's inline
paraphrase** of who spoke, transcribed inside the meeting minutes (see "Inline speaker
notes" below) — those are meeting-record speaker notes, **not genuine written comments**,
so they are deliberately **not** materialized into a comments table (fabricating one would
violate the repo's no-invention rule).

This matches, and closes, the Phase-2 lead left open in `../recon.md` §4.

## What was checked (2026-07-11, browser UA `Mozilla/5.0 … Chrome/120`)

| # | Target | URL | Result |
|---|--------|-----|--------|
| 1 | City homepage — eComment / Open City Hall / "comment" feature | `https://www.murray.utah.gov/` | HTTP 200; **no** eComment / Open City Hall / public-comment-portal feature present. |
| 2 | CivicPlus **City Council Agenda Packet** archive | `https://www.murray.utah.gov/Archive.aspx?AMID=83` | HTTP 200; **180 agenda packets**. Packets are agenda + staff reports only. |
| 3 | One full Council Agenda Packet, opened + full-text scanned | `https://www.murray.utah.gov/Archive/ViewFile/Item/8343` (July 2021 packet, **303 pp**, 15.9 MB) | Contains agenda + staff reports; **zero** "public comment", "correspondence", "written comment", "letters received", or "public input" sections. → packets bundle **no** emailed correspondence. |
| 4 | CivicPlus **Planning Commission Agendas and Attachments** archive | `https://www.murray.utah.gov/Archive.aspx?AMID=32` | HTTP 200; PC agendas + attachments only. No correspondence/comment category. |
| 5 | Council/PC minutes markdown on disk — inline comment sections | `../meeting_minutes/minutes/**/*.md` | "Citizen Comments:" and "Public Hearings" sections **are systematically present**, but they are clerk *paraphrase* of speakers (often "No comments were given"), **not** written comments. |
| 6 | Dedicated comment/correspondence Archive category | Archive Center sidebar (`Archive.aspx`) | No "Public Comment" / "Correspondence" / "Citizen Input" / "Letters" category exists among the archive types. |

## Inline speaker notes (systematically present — logged, not tabled)

Every regular Council (and PC) minutes doc carries a **`Citizen Comments:`** block and, for
each noticed item, a **`Public Hearings:`** block recording — in the clerk's words — who
approached and a one-line paraphrase (e.g. *"Ms. Simper, a lifetime Murray resident, spoke
about an issue with her neighbor and requested help from the City"*), or the standard
*"The public hearing was open for public comments. No comments were given."* These live in
the **minutes bodies** (`../meeting_minutes/minutes/`) and are searchable there. They are
**not** genuine written public comments (no author-submitted text, subject, or attachment),
so per the collection standard they are **not** reconstructed into `all_comments_clean.csv`.
Building a labeled `minutes_speaker_log.csv` from them is a possible future enhancement
(noted in `recon.md`), deliberately not done here.

## Bottom line

`all_comments_clean.csv` intentionally holds **only the 14-column header** — Murray is one
of the collection's honest-zero comment cities (like the submit-only SLCo siblings
south_jordan / taylorsville). This is a true source limit, **not** a scraping gap.
