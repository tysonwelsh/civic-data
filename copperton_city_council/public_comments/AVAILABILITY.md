# Public comments — Town of Copperton — HONEST ZERO (submit-only)

**Verdict: SUBMIT-ONLY / no published written-comment archive.** Copperton publishes **no**
standalone public-comment corpus (no eComment archive, no correspondence page, no
downloadable comment log). `all_comments_clean.csv` is therefore **header-only by design**
— a legitimate honest zero, not a data gap. (Matches Alta / Taylorsville / South Jordan.)

## Audit (browser-UA + `curl -k`, 2026-07-12)

The town site (`https://copperton.utah.gov/`, GoDaddy Website Builder — the cert covers
`secureserversites.net`, so it must be fetched with `curl -k` + a browser UA) exposes **no
public-comment archive**:

| Probe | Result |
|---|---|
| `https://copperton.utah.gov/` | **200** (home; only a generic "Contact Us" affordance) |
| `https://copperton.utah.gov/public-comment` | **404** |
| `https://copperton.utah.gov/public-comments` | **404** |
| `https://copperton.utah.gov/comment` | **404** |
| homepage scan for `ecomment` / `public comment` / `comment form` / `correspondence` | **none present** |

There is no page, feed, or document on the town site that lists past written comments, and no
eComment/correspondence portal.

## How comment actually enters the record

Public comment at Copperton is taken **in person** at the monthly Council meeting (3rd
Wednesday, Bingham Canyon Lions Club). The minutes carry a **"COMMUNITY INPUT"** section and
an **"Others Present:"** attendee list, where the clerk **paraphrases** speakers inline. Those
are **meeting-record speaker notes, not genuine standalone written comments**, and they live in
`meeting_minutes/` — **not here**. Do **not** re-mine minutes speaker paraphrase into this
file; it would misrepresent clerk summary as verbatim public comment.

## If this ever changes

If Copperton stands up an eComment portal or publishes a written-comment archive, harvest it
into `all_comments_clean.csv` using the collection-standard 14-column schema (header already in
place) and update this file. Until then the honest-zero verdict stands.
