# Mountainland Association of Governments — MPO source reconnaissance (2026-07-20)

The repo's first **regional** entity (`gov_level='regional'`, fed_index 202,
`aog-mpo`). Mountainland Association of Governments (MAG) is the AOG serving **Utah,
Summit, and Wasatch counties**; its federally-designated Metropolitan Planning
Organization (MPO) covers the **Provo–Orem urbanized area — Utah County only**. This
build targets the **MPO policy board** (the transportation decision body that adopts the
Unified Planning Work Program, Regional Transportation Plan, Transportation Improvement
Program, and air-quality conformity) and, as a second body, the **MPO Technical Advisory
Committee (TAC)**.

**CRITICAL SCOPE CAVEAT.** The MPO Board seats **Utah-County** member cities + Utah
County commissioners + UDOT/UTA/FHWA/FTA/air-quality ex-officio. It is **NOT** a
Summit/Wasatch body — `summit_county` and `park_city` belong to MAG's **AOG/RPO** side
(Wasatch Back Regional/Rural Planning), NOT the MPO Board. Never imply they sit on this
board. Repo member-city relationships that DO sit here: `provo`, `orem`, `lehi`,
`vineyard`, `utah_county`; plus `draper` and `bluffdale` appear as **ex-officio /
adjacent** members (Draper and Bluffdale straddle the Salt Lake/Utah county line — they
attend, Bluffdale is starred = non-voting/liaison). Most member cities (Alpine, American
Fork, Eagle Mountain, Saratoga Springs, Springville, Payson, Lindon, Highland, Pleasant
Grove, Spanish Fork, Cedar Hills, …) are **not repo entities** — their `entity_slug` is
blank with a note, never invented.

## Governance form

MAG is governed by an **Executive Council** (the AOG's top board of chief elected
officials across all three counties). Under it sit standing committees/boards, of which
this build covers the **MPO Board** (Utah-County transportation policy) and its **TAC**
(staff-level technical advisory). Other MAG bodies (Wasatch Back RPO, Aging, Community &
Economic Development) are out of scope for this transportation-forward build. The MPO
Board **meets monthly, second Thursday-ish, 5:30 pm** at the Utah County Health & Justice
Building, 151 S University Ave, Provo (schedule varies; cancellations advertised).

The board was named **"Mountainland MPO Regional Planning Committee"** through ~2019 and
**"MPO Board"** from 2020 (same body, renamed) — both eras are treated as one body
`MPO Board` in the db, with the historical name noted.

## Primary source ✅ — the MAG website static file tree (born-digital PDFs)

- Site: `magutah.gov` (formerly mountainland.org / magutah.org → 301). MPO Board landing
  page `magutah.gov/mpoboard/` is **JS-rendered** — the year accordions are empty in the
  static HTML and populate via an AJAX call. **Do NOT scrape the rendered HTML.**
- **The listing endpoint** (discovered in the page JS):
  `GET https://magutah.gov/sitefiles/minutes-list/?dir=files/committees/mpo_board/meetings/<YEAR>/`
  returns an HTML fragment with every file link for that year (minutes, agendas,
  recordings, packets). Older years live under `.../meetings/Older/<YEAR>/`. TAC is a
  parallel tree: `.../committees/tac/meetings/<YEAR>/`.
- **File URLs** are static and directly downloadable, e.g.
  `https://magutah.gov/static/files/committees/mpo_board/meetings/2025/2025_11_13/MPO%20Board%20Minutes%2011.13.2025.pdf`
  (HTTP 200, `application/pdf`, born-digital — clean text extraction, no OCR needed).
  Directory index listing itself is OFF (a bare dir path 404s); enumerate via the
  endpoint above.

### Archive depth FOUND (probed the full static tree 2014→2026)

**MPO Board minutes: 104 PDFs, floor = 2014, continuous through 2026-06.**

| year | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 |
|------|----|----|----|----|----|----|----|----|----|----|----|----|----|
| min. | 7  | 7  | 8  | 8  | 9  | 10 | 7  | 8  | 6  | 7  | 9  | 12 | 6  |

Pre-2020 minutes (verified honestly by reading 2014-10-02 and 2017-11-09) carry the
header **"Mountainland MPO Regional Planning Committee"**, born-digital, same motion
grammar — the format is stable across the whole 2014–2026 span; **no pre-2017 format
break, no OCR floor**. 2014 files are named `"<D> <Mon> <YY> rp minutes.pdf"`; 2017+ are
`"Minutes <M.D.YY> APPROVED.pdf"`; 2024+ are `"MPO Board Minutes <M.D.YYYY>.pdf"`.

**MPO TAC minutes: 50 PDFs, 2020–2026** (2026:4, 2025:10, 2024:10, 2023:8, 2022:7,
2021:7, 2020:4). **No TAC minutes exist pre-2020** on the site (honest floor — the TAC
tree's `Older/` years return zero minutes). Harvested as a second body via the same
endpoint (cheap — identical mechanism).

**Total harvest: 154 minutes PDFs.** Not every monthly meeting has posted minutes
(cancellations + a few unposted dates) — gaps are logged in `minutes_index.csv`, never
invented.

## Recovery / backup channel — Utah Public Notice (provenance only)

PMN (`pmn.utah.gov`) carries MAG notices: **body 8083** (current "MPO Board") and the
older **body 1480** ("Mountainland MPO Regional Planning"). The MAG site is COMPLETE and
born-digital back to 2014, so PMN is a **documented recovery fallback**, not harvested
here. Any future PMN-recovered minute would carry `provenance='pmn_minutes'` /
`'pmn_roa'`; site-sourced minutes carry `provenance='magutah_site'`.

## THE VOTE-RECORDING CEILING (verified — quoted from 2025-11-13 minutes, 7 pp)

The board is **ex-officio and high-consensus**; minutes are **tally-only with named
mover + seconder, NO roll call, NO individual vote attribution, and usually not even a
numeric count** — just "the motion passed all in favor". Attendance is a **named table**
(member + city/title, alternates, a ✓ present-mark) but that is presence, not a vote.

> "Minutes – Action  Mayor Denise Andersen moved to approve the minutes from October 9,
> 2025. Mayor Miller seconded the motion, and the motion passed all in favor."
> … "Councilmember Stacy Beck moved to approve this Spanish Fork Corridor Preservation
> Fund request for $1,402,500. Mayor Brad Frost seconded the motion, and the motion
> passed all in favor."

So the **db `vote` table is honestly EMPTY** (an attribution ceiling, exactly like alta /
nephi voice votes / west_jordan PC): motions carry `names_recorded=0`, a verbatim
`result_raw` ("the motion passed all in favor" / "the motion failed" etc.), a derived
`outcome`, and **full-name mover/seconder person links**. Motion titles are kept
information-rich (TIP modifications, RTP amendments + air-quality conformity, corridor
preservation buys, functional-classification submittals, funding awards with dollar
amounts). Older-era (2014–2019) motion prose often names movers by **surname only**
("Mayor Acerson moved") — resolved to full names against that same meeting's named
attendance roster (within-meeting-unique), never surname-guessed across meetings.

## Members seen on the 2025-11-13 board (for the roster seat table)

Voting: mayors of Alpine, American Fork, Cedar Fort, Cedar Hills, Draper, Eagle Mountain,
Elk Ridge, Fairfield, Genola, Goshen, Highland, Lehi, Lindon, Mapleton, Orem, Payson
(Chair), Pleasant Grove, Provo, Salem, Santaquin, Saratoga Springs, Spanish Fork
(councilmember), Springville, Vineyard, Woodland Hills; 3 Utah County Commissioners
(Beltran, Gordon, Powers Gardner); 2 state legislators (Rep. Shallenberger, Sen. McKell).
Ex-officio / starred (non-voting liaison): Bluffdale (Mayor Hall), Camp Williams, FHWA
(Marrero), FTA (Hadley), MPO TAC Chair (Jered Johnson), plus standing agency reps UDOT
(Braceras), UTA (Trustee Acerson), Utah Division of Air Quality (Bird). Repo person-row
overlaps exist (Kaufusi/Provo, Young/Orem, Johnson/Lehi, Fullmer/Vineyard, Walker/Draper)
but each db is independent — persons are resolved within `mag_mpo` by full name.

## Module status

| module | source | status |
|---|---|---|
| `legislative/` | MAG site (MPO Board 101 + TAC 50 = 151 kept) → minutes md + motions | BUILT |
| `roster/` | attendance tables + member-city registry (38-row seat table) | BUILT |
| `db/` | build_db.py → mag_mpo.db (standard 8-table; 635 motions, vote empty by ceiling) | BUILT |
| `projects/` | MAG ArcGIS Hub TIP/RTP/RPO → `projects.csv` **571 rows** (tip 225/rtp 262/rpo 84) | BUILT |
| `projections/` | MAG 2023 RTP by-city → `mag_mpo_projections.csv` **328 rows** (pop+jobs) | BUILT |
| `gis/` | MAG hub `data.magutah.gov` → catalog of **20** growth/land-use layers (link-only) | BUILT |

**Note on the harvest count:** the static tree held 104 Board + 50 TAC PDFs (154); 3 Board
files were dropped with reason (1 foreign-body doc + 2 exact duplicates), leaving **101 Board +
50 TAC = 151 meetings** in `minutes_index.csv` and the db. Federated: `regional_project` (571),
`projection` (328), `motion` (635).
