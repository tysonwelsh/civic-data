# Utah County — agencies (honest ledger)

Unlike Salt Lake County (a Redevelopment Agency + Municipal Building Authority + the
richly-published Housing Connect board), Utah County's agency landscape is **thin**. This
ledger records what was VERIFIED to publish minutes (2026-07-20) and what does not — built
only where minutes actually exist.

## Housing Authority of Utah County (HAUC) — BUILT

- **Separate legal entity** (`housinguc.org`, 485 N Freedom Blvd, Provo), NOT part of the
  county commission portal. It is the only Utah County agency that publishes board minutes.
- Governing board minutes live on its **own site** under yearly pages
  `https://housinguc.org/<year>-public-notices-and-documents/` (PMN body **2728** carries
  agendas only, no minutes — so the site is authoritative).
- **26 board minutes fetched, 2023-12 → 2026-03** (2023: 1, 2024: 10, 2025: 12, 2026: 3) —
  all **born-digital** PDFs.
- **Recording ceiling: TALLY-ONLY, named mover/seconder (FIRST names).** Grammar:
  *"April made a motion to approve the minutes. Amelia seconded the motion. The motion
  passed unanimously."* Individual member votes are NOT enumerated → `names_recorded=0`,
  no per-member vote rows (honest ceiling). Resolutions are numbered
  (`Resolution 2025-05-01`).
- Federated in `utah_county.db` as body **"Housing Authority of Utah County"**
  (`kind='agency'`). Minutes markdown + provenance:
  `agencies/housing_authority/minutes/<year>/<date>_housing_authority.md`;
  index `agencies/housing_authority/minutes_index.csv`.
- **Honest gaps:** the site's "Archived" page exposes no minutes before 2023-12 via static
  links (older years not published online); pre-2023 HAUC minutes are a genuine acquisition
  gap (queueable via GRAMA request — see root TODO).

## Redevelopment Agency / Municipal Building Authority — NONE FOUND

Utah County's **3-member Board of Commissioners acts directly** as the county's legislative
+ executive authority; there is **no separate RDA/CRA or MBA body** in the commission
portal archive (2015–2026) and none surfaced on Utah Public Notice for the county. This is
NOT a coverage gap — the county simply does not operate those agencies as distinct minuted
bodies (redevelopment in Utah County is handled at the municipal level by its cities). If a
county Economic Development / redevelopment body is later found to publish minutes, add it
here as a new agency body.

## Other special-service districts

The county posts vacancy/hearing notices for numerous special service districts (North
Pointe Solid Waste, Timpanogos SSD, water conservancy districts, etc.) via PMN body 2731,
but these are **independently-governed districts**, not county agencies, and are out of
scope for this entity (they would each be their own entity if ever built).
