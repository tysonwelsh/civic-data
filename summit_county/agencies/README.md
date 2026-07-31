# Summit County — agencies (deferral ledger)

Both county agencies are **deferred** in this MID-tier build (not built into
`summit_county.db`). This is the honest ledger of what exists and where, so a later pass can
pick them up. Nothing here is fabricated; nothing here is in the federated DB yet.

## Redevelopment Agency (RDA) — deferred

- **Source:** Utah Public Notice (`pmn.utah.gov`) **public body 1277**. (No separate Granicus
  Council-style HTML minutes stream.)
- **Why deferred:** thin by design — a single active project area (**Silver Creek**), with a
  minimal minutes history. Low unique value relative to build cost; the Council itself acts on
  the substantive redevelopment questions (captured in `legislative/`).
- **Follow-on:** harvest PMN 1277 → `agencies/minutes/`, prose-extract like the Council
  (same tally-primary ceiling), append to `summit_county.db` via a `db/staging_pc`-style
  staging dir so Council motion_ids never renumber.

## Summit County Housing Authority (SCHA) — deferred (formed 2025, ~no history)

- **Source:** Granicus `view_id=1` ("Summit County Housing Authority Minutes" / "SCHA") and a
  just-beginning PMN presence. It is a **County-board body** here (not a separately
  incorporated authority with its own portal, unlike salt_lake_county's Housing Connect).
- **History:** the board **began meeting mid-2025** — **10 minutes documents 2025-08-20 →
  2026-06-15** (monthly), the earliest being 2025-08-20. There is essentially **no historical
  record to backfill** — the body is new.
- **Why deferred:** per build scope; and the record is nascent. When built, it is a
  standard prose-extraction append (Granicus HTML, same MinutesViewer format as the Council,
  so `legislative/extract_votes.py` adapts directly).
- **Follow-on:** harvest the 10 SCHA clips → `agencies/housing_authority/minutes/`, extract
  motions/votes, append to the db.

## Not deferred here — owned by other agents

The two **Planning Commissions** (Snyderville Basin PC, Eastern Summit County PC) are the
`land_use/` module (another agent). Elections, plans, projections, gis, ordinances, packets,
development are their own modules. See `../recon.md`.
