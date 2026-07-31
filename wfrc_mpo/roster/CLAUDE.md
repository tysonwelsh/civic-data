# wfrc_mpo/roster — WFRC Council seat table

`council_seats.csv` maps each **WFRC Council seat** to its ex-officio office, the person
filling it, whether it is **voting**, and (where the office belongs to a repo entity) the
`member_entity_slug`. This is a SEAT-STRUCTURE snapshot, not a tenure history: WFRC is
nominally a 27-member council (**21 voting by charter** + 6 non-voting appointments), but
`council_seats.csv` enumerates the CURRENT member table as **28 seats (22 voting + 6
non-voting)** — the extra voting row is a second UTA trustee the 2026-01-22 member table
lists (reconciled 2026-07-20; the entity CLAUDE.md documents the same). Seats are held **ex
officio** by elected mayors/commissioners of member jurisdictions plus the UDOT Executive
Director and UTA trustees. Non-voting appointments come from the Utah League of Cities and
Towns, Utah Association of Counties, Envision Utah, the Legislature, and GOPB.

## Source + confidence

Derived from the **member table printed at the end of each Council minutes doc** (the most
authoritative roster WFRC publishes), anchored on the current **2026-01-22** table and
cross-checked against **2025-10-23**. Fields carry per-row `source` + `confidence`.
`voting` is the seat's WFRC voting status.

## Honest caveats

- **Seats rotate.** The Salt Lake County and county-city seats are held by *designated*
  member cities that change over time (e.g. the 2025 SL County seat held by Millcreek's
  Jeff Silvestrini is held in 2026 by Herriman's Lorin Palmer; the Davis seat held by
  Clinton in 2025 is Kaysville in 2026; the Weber seat held by Roy in 2025 is Hooper in
  2026). Other member-city mayors attend but do **not** hold the designated voting seat —
  their attendance is not a seat.
- **UDOT / UTA rows are `confidence=medium`**: the 2026 member table's UDOT/UTA columns are
  scrambled by the born-digital PDF's multi-column layout, so those names are carried from
  the clean 2025-10-23 table.
- **No historical seat tenure is modeled.** A full rolling roster (per-year seat occupants
  2016→) is a documented future item — the raw material is every meeting's member table.

## Repo-entity linkage

Seats resolving to a repo entity (`member_entity_slug`): **slc** (Mendenhall),
**south_jordan** (Ramsey, Council Chair), **sandy** (Zoltanski), **west_jordan** (Burton),
**taylorsville** (Overson), **herriman** (Palmer), **ogden** (Nadolski),
**salt_lake_county** (Wilson, Winder Newton), **draper** (Walker, non-voting ULCT), plus
**millcreek** (Silvestrini) in the 2025 roster. Cross-reference `registry/relationships.csv`
`member_of wfrc_mpo` edges. All other seats are external jurisdictions (Davis / Weber /
Box Elder / Morgan / Tooele counties and their cities, UDOT, UTA, the Legislature) — flagged
external, `member_entity_slug` blank; they are NEVER invented as repo entities.
