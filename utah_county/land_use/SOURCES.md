# utah_county / land_use — SOURCES

Land-use authority minutes and votes for **Utah County**: the **Utah County Planning
Commission** (the county's only planning commission; unincorporated-area land use only —
most Utah County population lives inside incorporated cities). The PC meets the **3rd
Tuesday monthly at 5:30 p.m.** (100 E Center St, Suite 1400, Provo) and **recommends to the
3-member Utah County Board of Commissioners** (Utah County is a commission-form county — no
county council). Retrieved 2026-07-20.

## Reachable source channels (two)

1. **Utah Public Notice — pmn.utah.gov, public body 1711** ("Utah County Planning
   Commission"). The reliable public channel. Notices carry born-digital **agendas** for
   **2015–2026**, and **signed minutes PDFs only for 2025–2026** (11 files). Enumerated with
   `enumerate_pmn.py` (PMN keyword search POST, windowed per calendar year — the public-body
   page shows only a ~6-month rolling window). File URLs: `https://www.utah.gov/pmn/files/<id>.pdf`.
   Raw notice enumeration saved as `pmn_notices.csv`.
2. **The county's own CMS — `https://codev.utahcounty.gov/api/meetings`** (Payload CMS, tenant
   "Community Development"). Gives the authoritative **meeting spine 2020-02 → 2026** (68 PC
   meetings) with per-meeting `minutes[]` and `documents[]` file metadata. **BUT the media
   host `cms.utahcounty.gov` is not publicly resolvable (NXDOMAIN) as of 2026-07-20** — a
   live county-side migration gap (the CMS launched 2026-06-04). So the 2020–2024 minutes are
   *catalogued* (we know they exist, their filenames, and their meeting dates) but the PDF
   bodies are **not currently retrievable** from any channel.

The old county website (`utahcounty.gov/dept/comdev/planning/`) hosted only plans/maps; its
Laserfiche WebLink is not publicly browsable and Wayback holds no pre-2025 PC minutes PDFs.

## What was retrieved and extracted

**11 meetings, 2025-01-21 → 2026-05-19** — every PC meeting with a minutes PDF reachable on
PMN. All are **SCANNED, image-only** signed-minutes PDFs (pypdf yields zero text), so they
were transcribed with **Claude vision** (the Read tool) rather than OCR/pypdf. Raw PDFs are
retained in `raw/<date>_<pmnfileid>_minutes.pdf`; markdown in `minutes/<year>/`; the
`extraction:` front-matter field records `claude-vision (scanned signed minutes)`.

## The recording ceiling — HIGH ATTRIBUTION (named roll call)

Utah County PC minutes name **every Aye voter AND every Nay voter explicitly** on every
substantive motion:

> "The motion passed with the following vote: `Aye` Glen Roberts, Shayne Pierce, Lorraine
> Davis, Sullivan Love, Robert McMullin, Chris Herrod. `Nay` none."

This is a **fully-named roll call**, not tally-only — the strongest attribution class. Of 73
extracted motions, **71 are fully named** (382 named vote rows) and only **2 are tally-only**
(the 2026-01-20 Chair/Vice-Chair elections held *by acclamation*, which printed no roll —
honest blanks). Recusals are printed only as narrative ("stated a conflict … and left the
meeting"); we captured 9 such recusals as `vote=Recuse` rows (Sullivan Love on the Timpanogos
SSD biosolids items; Lorraine Davis on the Hight 4.44 item) even though the vote line simply
omits the recused member. **Never invented a name** — where the printed vote line omits a
present member (a few clerk omissions, noted per meeting in the markdown), the line is
reproduced as printed.

## Honest gaps (never fabricate to fill these)

- **2015–2019 (52 meeting dates): agenda-only.** PMN carries the agenda notices but **no
  minutes** — minutes for this pre-CMS era were never published to any reachable channel.
  Logged in `minutes_index.csv` with `minutes_status=no_minutes`.
- **2020–2024 + a few 2025 (46 meetings): catalogued but media host offline.** Minutes exist
  in the county CMS (`cms_minutes_file` column names the exact PDF) but `cms.utahcounty.gov`
  is NXDOMAIN. `minutes_status=catalogued_media_offline`. **Backfillable** the moment the
  county wires up its media host (or via a future Wayback pass) — the highest-value follow-on.
- **Cancelled meetings (10)** — real "no meeting" records (`minutes_status=Cancelled`).
- **Scheduled/future (6)** and recently-held-pending-approval meetings carry no approved
  minutes yet — not a defect.

## MPDPC verdict (recon open question — RESOLVED)

The PMN "MPDPC" agenda stream (e.g. `utah.gov/pmn/files/1461115.pdf`) is a **Salt Lake County**
body, **not** Utah County. That file's header reads "Mountainous Planning District Planning
Commission," references the **Salt Lake County** Resource Management Plan and Municipal Code,
and lists Taylorsville / 2001 South State Street (SLCo Government Center) locations. It is
SLCo's existing MPDPC (PMN body 712), already covered by `salt_lake_county/land_use/`. **Utah
County has no Mountainous Planning District PC** — it runs a single Planning Commission.
Nothing was built for it here.

## Files

- `enumerate_pmn.py` — reproducible PMN body-1711 enumeration (per-year search POST).
- `pmn_notices.csv` — raw enumeration output (notice_id, date, attachment labels/urls).
- `minutes_index.csv` — one row per PC meeting date 2015–2026 (145 rows), with
  `minutes_status`, the PMN `agenda_url`, and the offline `cms_minutes_file` where known.
- `all_votes.csv` / `motions_tally.csv` — extracted votes (see below).
- `raw/`, `minutes/<year>/` — source PDFs and vision transcriptions.
