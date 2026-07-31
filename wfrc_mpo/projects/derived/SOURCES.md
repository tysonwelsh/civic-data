# wfrc_mpo / projects / derived — sources & method

**DERIVED, regenerate-only.** Built by `../build_project_history.py` from the raw ArcGIS
attribute snapshots in `../raw/TIP*.json` (8 TIP vintages 2020-2025 .. 2027-2032, 14 layers).
Canonical source of truth remains `../projects.csv` + `../raw/`; this layer adds a **project
lifecycle** view (one project across vintages: entry, exit, forecast slip, cost drift) that the
flat per-vintage `projects.csv` does not express. RTP rows are NOT re-derived here — TIP only.

Rerun: `python3 wfrc_mpo/projects/build_project_history.py` (stdlib only; idempotent; overwrites).
Gates + counts: `BUILD_REPORT.md`.

## Grain & scope

- **`project_vintage.csv`** — one row per **(pin, plan_vintage)**, TIP only. Rows with a
  null / empty / **0** `pin` are EXCLUDED (they cannot be tracked across vintages); they are NOT
  lost — they persist in `../projects.csv` as OID-fallback rows (or, for 2020-2025, as numeric
  project_id `"0"`). Per-vintage exclusion counts are in `BUILD_REPORT.md`.
- **`project_history.csv`** — one row per **pin**, summarizing that project's life across the
  vintages it appears in.

Within a single (pin, vintage), raw features whose **extracted attribute tuple is identical**
(e.g. the same project mirrored across the lines and points layers) are collapsed to one row.
If two features for the same (pin, vintage) carry **differing** attributes, the build **HARD-FAILS**
rather than silently choosing one — UNLESS the conflict has been adjudicated in
**`../vintage_overrides.csv`** (the repo's documented-override pattern; each row carries the
decision + reason + date). Two override actions exist:

- **`merge_dup`** — the conflict is a source duplicate (e.g. typo drift between two copies of
  the same project); the MOST COMPLETE tuple is kept (most non-blank fields, tie-break longest
  description — deterministic). Applied 2026-07-22: pin 19561 / 2027-2032.
- **`keep_both`** — the PIN genuinely bundles distinct sub-scopes (UDOT master-PIN behavior);
  every distinct tuple is emitted as its own row with `variant` = 1, 2, ... In
  `project_history.csv` such pins keep their PRESENCE fields (vintages, entry/exit) but have
  their single-trajectory numeric fields (forecast years, slip, costs, drift, last_status,
  RTP link) **blanked** — a single trajectory across mixed scopes would be fabricated;
  `name_latest` pipe-joins the variant names. Applied 2026-07-22: pin 21213 / 2027-2032
  ('Part of FrontRunner Forward' lines + 'FrontRunner Point Improvements' points).

Any conflict NOT covered by an override still hard-fails — new conflicts on a future refresh
surface loudly and must be adjudicated the same way.

## Field-name drift handled (case-insensitive)

`pin`; `pin_desc`/`PIN_DESC`; `pin_stat_nm`/`PIN_STAT_N`; `forecast_st_yr`/`FORECAST_S`;
`project_value`/`PROJECT_VA`; `cnty_name`/`CNTY_NAME`; `public_desc`/`PUBLIC_DES`;
`mstr_pin_desc`/`MSTR_PIN_D`. The **2020-2025** vintage lacks a funding-source field
(`funding_source_raw` is blank there) and lacks a project-type field. The **2027-2032** vintage
additionally carries a more granular `All_Funding_Sources` field (e.g. `"HSIP (100%)"`); per the
upstream spec `funding_source_raw` reflects `mstr_pin_desc` only — the finer field is intentionally
NOT captured here (query the raw layer if needed).

## project_vintage.csv columns

| column | meaning |
|---|---|
| entity | constant `wfrc_mpo` |
| plan_vintage | TIP service-year span, e.g. `2026-2031` |
| pin | WFRC Project Identification Number (never null/empty/0 in this file) |
| variant | blank normally; `1`,`2`,... for a `keep_both`-override pin whose distinct sub-scopes are each their own row |
| name | `pin_desc` |
| county | `cnty_name` (verbatim) |
| in_wfrc_region | `1` = one of the six WFRC counties (Salt Lake, Davis, Weber, Morgan, Box Elder, Tooele); `0` = any OTHER recognized Utah county (e.g. Utah, Wasatch, Carbon, Cache); blank = county missing or a non-county label (`Various`, `Statewide`, `O/L UA`, `SL UA`, `Region One`, ...) |
| forecast_start_year | `forecast_st_yr` (programmed forecast start; integer) |
| cost | `project_value` parsed to a number ($/commas stripped); blank if empty/unparseable |
| status | `pin_stat_nm` (delivery status — Scoping / Awarded / Under Construction / Close Out / ...) |
| funding_source_raw | `mstr_pin_desc` (verbatim; blank for 2020-2025) |
| description | `public_desc` |
| source_layer | raw filename stem(s) the row came from (pipe-joined if a collapsed row spanned layers) |

## project_history.csv columns

| column | meaning |
|---|---|
| entity | constant `wfrc_mpo` |
| pin | project id (grain) |
| name_latest | `name` from the NEWEST vintage the pin appears in |
| n_vintages | number of distinct vintages the pin appears in |
| first_vintage / last_vintage | earliest / latest vintage of appearance (chronological) |
| vintages | pipe-joined chronological list of every vintage the pin appears in |
| entered_tip | = first_vintage |
| left_censored | `1` if first_vintage == `2020-2025` (the observation window opens there — true entry may predate it); else blank |
| exited_tip | the vintage IMMEDIATELY AFTER last_vintage (the one the project failed to appear in). Blank if last_vintage == `2027-2032` (still programmed). **Also blank whenever `in_wfrc_region != 1`** — a statewide 2020-2025 project dropping out of the later WFRC-only vintages is a SCOPE change, not a lifecycle exit; encoding it as an exit would be fabrication |
| first_forecast_year / last_forecast_year | forecast_start_year at first / last vintage |
| slip_years | last_forecast_year − first_forecast_year (integer; **may be negative** = accelerated); blank if either year missing |
| first_cost / last_cost | cost at first / last vintage |
| cost_drift_pct | `round((last_cost − first_cost)/first_cost*100, 1)`; only when pin appears in ≥2 vintages AND both costs numeric AND first_cost > 0; else blank |
| last_status | status at last vintage |
| statuses | pipe-joined chronological DISTINCT status values |
| counties | pipe-joined DISTINCT counties across vintages |
| in_wfrc_region | `1` if the pin is ever in-region, else `0` if ever a named out-of-region county, else blank |
| rtp_unique_id | linked RTP project `unique_id` — set ONLY on a 1:1 unambiguous exact normalized-name match |
| rtp_match_confidence | `exact_name` when linked, else blank |

## RTP linkage — honest limits

RTP linkage joins TIP `name_latest` to `../projects.csv` RTP-family rows (`plan_kind='rtp'`) by
**exact normalized name** (casefold, punctuation stripped, whitespace collapsed). A link is set
ONLY when the normalized name maps to exactly one RTP `unique_id` AND exactly one TIP pin — any
one-to-many on either side yields NO match. **No fuzzy matching.** This is a conservative,
precision-first linkage; TIP and RTP name projects differently, so most TIP pins have no RTP link
(that is expected, not a gap). The match count is in `BUILD_REPORT.md`.

## Honest limits

- **TIP only.** RTP lifecycle is not modeled (a single adopted RTP vintage — no cross-vintage lifecycle).
- **2020-2025 is statewide-inclusive**; `in_wfrc_region` separates the six WFRC counties from the
  rest so out-of-region projects are never mistaken for regional exits.
- **Costs are verbatim programmed values** parsed to numbers; **blank (never 0)** when the source
  is empty / unparseable / **literally 0** (0 is the source's null placeholder — matches the
  `projects.csv` "blank never 0" rule; ~68 raw rows). cost_drift compares first vs last programmed
  value only, and requires first_cost > 0.
- **`forecast_start_year = 0` is treated as MISSING (blank)** — 0 is the source's "not set" marker
  (mixed in alongside 951 real years in 2020-2025), not calendar year 0. This prevents a fabricated
  `slip_years` of ~2026 from a 0-vs-real-year subtraction. slip_years is blank whenever either end is
  missing/0.
- **`exited_tip` is an OBSERVATION-WINDOW inference**, not a source field: a project absent from the
  next vintage may have been completed, deferred, re-scoped, or re-pinned. Read it as "no longer
  programmed under this pin", not "cancelled".
