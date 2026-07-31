# Vineyard PMN — confirmed entity & body IDs (as-of 2026-07-05)

Source: Utah Public Notice Website (`https://www.utah.gov/pmn/`). IDs confirmed by
walking the GLOBAL entity chain — **not** trusting the hand-noted recon id (a prior
Logan run found a recon body-id that belonged to a different city; here the recon id
`530` was re-derived and confirmed correct).

## Chain walked

1. `GET /pmn/list/entities.html?id=3&limit=2000` (govType 3 = Municipality)
   → **Vineyard entity id = `294`**.
2. `GET /pmn/list/publicBodies.html?id=294&limit=2000`
   → full Vineyard public-body roster (below).
3. `GET /pmn/list/notices.html?id=<bodyId>&page=300`
   → the body's ENTIRE notice history in one GET (the 6-month default disclaimer is
   printed on the page, but `page=300` returns the cumulative list back to 2006).

## Vineyard public bodies (entity 294)

| Body | PMN body id | Backfilled here | Notes |
|------|-------------|-----------------|-------|
| **City Council** | **530** | yes | recon id confirmed; notices 2006–2026 |
| **Planning Commission** | **531** | yes | notices 2008–2026 |
| **Redevelopment Agency** | **2598** | yes | notices 2009–2026; repo has NO RDA minutes layer, so all in-window RDA minutes are net-new |
| Administrative Law Judge/Hearing Officer | 6751 | no | not a minutes-producing deliberative body for housing/growth research |
| ARCH Commission | 8139 | no | out of scope |
| Board of Appeals - Building Department | 6178 | no | out of scope |
| Communities That Care Commission | 8137 | no | out of scope |
| Development Review Committee | 8517 | no | out of scope |
| Ordinance and Resolution Passage | 7359 | no | administrative posting body, not meetings |
| Public Notices | 7323 | no | administrative posting body |
| Resolutions | 7795 | no | administrative posting body |
| Vineyard Bicycle Advisory Commission | 7057 | no | out of scope |
| Vineyard Library Board | 8133 | no | out of scope |
| Youth Council | 8313 | no | out of scope |

## Attachment direct-download

Attachments resolve at `https://www.utah.gov/pmn/files/<fileId>.<ext>` (verified
sample `1124513.pdf` = 2024-01-10 CC Final Minutes). Attachment type labels on the
notice list distinguish `(Meeting Minutes)`, `(Audio Recording)`,
`(Public Information Handout)`, and `(Other)`. Only `Meeting Minutes` attachments were
harvested for this backfill.

## Central pitfall respected

A notice's **Event Date is not the meeting date of its minutes attachment.** Minutes
are routinely filed against the *next* meeting's notice, and cancelled-meeting notices
re-attach the last real meeting's minutes. Recoveries here are therefore keyed on the
meeting date printed **inside each PDF**, deduped by that internal date, not on the
notice date. The same minutes file (same fileId) attached to several notices was
fetched once.
