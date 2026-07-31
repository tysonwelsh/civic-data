# planning_commission/ — Town of Copperton Planning Commission

Planning Commission minutes + extracted votes for the **Town of Copperton** (body
`PlanningCommission`, MSD-staffed). **18 minutes docs, 2019-03-12 → 2025-07-02; 57 motions.**

## Thin BY DESIGN — most PC meetings are CANCELLED

Copperton's Planning Commission is **nominal**. It is scheduled ~1st Wednesday monthly but **most
sittings are cancelled** (tiny land-use volume; long-range planning support runs through the
Greater Salt Lake MSD). The 18 docs across 2019–2025 are **all the PC minutes that exist** — the
sparse corpus is an honest reflection of the body's activity, **not** a harvest gap. No meetings
were fabricated to fill cadence, and `minutes_unrecovered.csv` is empty (header only).

## Provenance

- **Source:** Utah **PMN body 1560** only (`utah.gov/pmn/files/<id>.pdf`; the town GoDaddy site
  has no PC minutes archive). `source` = `pmn`.
- **Format:** all `text` (born-digital `pdftotext`); screener clean (dict_ratio 0.748,
  split_word 0, weird_char 0 across all 18). Raw originals retained under `raw/`.
- `minutes_index.csv` + `all_votes.csv` are the collection-standard 8-col / 13-col schemas.

## Votes — consensus, mover-only, tally-only, NO mayor

`all_votes.csv` records **mover-only narrative tally**: a motion names the **mover** and records
"Vote: Commissioners voted unanimous in favor" (or "of commissioners present"). Distinctive vs the
Council dataset:

- **No seconder field is ever printed** (the `seconder` column is blank for PC).
- **No presiding-mayor vote** — this is a commission, not the council; tallies are of
  commissioners present.
- **Uniformly consensus.** The only per-member rows are **3 named Breinholt abstentions**
  (2020-09-23 ×2, 2022-12-13); every other motion is tally-only (`member`/`vote` blank). A blank
  member list is the SOURCE FORMAT, not an extraction miss.
- Commissioners appear **surname-only** in the minutes (Taylor, Alder, Winkler, Green, Breinholt,
  Pazell, Pratt) — `roster.csv` reflects that; do not attempt full-name resolution beyond what the
  source prints.
- `result`/`motion_type` are city-verbatim; `motions_std.csv` holds the normalized layer.

## Regenerate

```
python3 extract_votes.py && python3 validate_votes.py   # RESULT: PASS
```

Rebuild `db/` + `weeks/` afterward. Corrections go through the derived-layer rebuild, never
in-place edits to the flat CSVs.
