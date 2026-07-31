# mag_mpo/roster — MPO Board seat table (authoritative for this module)

`seats.csv` is a **point-in-time seat/office table** for the **MPO Board** as composed
on **2025-11-13** (the verified reference minutes — the only date read in full for the
roster; earlier compositions differ as mayors turn over and are NOT back-filled here).
It is a **seat table, not the rolling `council_terms` interval layer** the cities carry:
the MPO Board is an **ex-officio body** (members sit by virtue of holding a city
mayoralty / county-commission seat / legislative seat / agency post), so "tenure" is
governed by the underlying office, tracked in each member entity's own roster where the
member is a repo entity.

## Columns

`seat_type, office, jurisdiction, entity_slug, member_full_name, voting_status,
term_note, source`

- **entity_slug** is filled ONLY where the member jurisdiction is a repo entity —
  `draper, lehi, orem, provo, vineyard, bluffdale` (cities) and `utah_county` (county,
  3 commissioner seats). **Most member cities are NOT in the repo** (Alpine, American
  Fork, Cedar Fort, Cedar Hills, Eagle Mountain, Elk Ridge, Fairfield, Genola, Goshen,
  Highland, Lindon, Mapleton, Payson, Pleasant Grove, Salem, Santaquin, Saratoga
  Springs, Spanish Fork, Springville, Woodland Hills) — their `entity_slug` is **blank**,
  never invented.
- **voting_status** ∈ `voting` | `ex-officio-nonvoting`. The 5 starred (`*`) attendees on
  the source table (Bluffdale, Camp Williams, FHWA, FTA, MPO TAC Chair) are the
  non-voting liaisons; the three standing agency members (UDOT, UTA, Utah Division of Air
  Quality) sit unstarred and are treated as voting. Note the ceiling: minutes record NO
  roll call, so voting_status is the seat's designation, not observed per-motion votes.

## Scope caveat (critical)

These seats are the **Provo–Orem Urbanized-Area MPO — Utah County only**. `draper` and
`bluffdale` appear because they straddle the Salt Lake/Utah county line. **Do NOT** read
any Summit/Wasatch entity (`summit_county`, `park_city`) onto this board — those are
MAG's **AOG / Wasatch Back RPO** side, a different body not built here.

## Executive Council (noted, not built)

Above the MPO Board sits MAG's **Executive Council** — the AOG's top board of chief
elected officials spanning all three member counties (Utah, Summit, Wasatch). It is the
association's governing board; the MPO Board is the Utah-County transportation policy
committee under the MAG umbrella. The Executive Council roster is out of scope for this
transportation-forward build (no seat table harvested).
