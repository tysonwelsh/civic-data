# planning_commission/ — Bluffdale Planning Commission vote extraction

Turns **91 PC minutes** (2020-01-08 → 2026-06-03, CivicPlus/CivicEngage
AgendaCenter, CID=3) into structured motions + votes. Entry point
**`extract_votes.py`** (reads `minutes_index.csv`, PURE deterministic — no
LLM/network, resumable); validator **`validate_votes.py`** (writes
`votes/_validation_report.txt`). Same 13-column schema as council; every
`all_votes.csv` row `body=PlanningCommission`.

## Coverage (verified — `validate_votes.py`)
**91 meetings · 308 motions · 1,275 vote/placeholder rows · 1,255 named ·
288 named motions / 20 tally-only · 24 contested · 2020–2026.**
**68 `text` / 23 `ocr`** minutes (`format`), OCR concentrated 2024–2026 (+1 in
2020). 10 commissioners in `roster.csv`. The JSON layer reconciles exactly to the
CSV (308 motions).

## Bluffdale's PC is elected-style board of ~6–7 commissioners
The PC is an **appointed** board (no election). Chair & Vice-Chair vote like
members; **no mayor on the PC**. A full PC roll therefore caps at **6–7**, NOT 5
— so `validate_votes.py`'s generic `CEILING CHECK (<=5)` reports **FAIL** for the
PC. **This is a validator-threshold artifact, not a defect**: the `<=5` ceiling
is the *Council* rule (5 at-large members). The single PC motion above 5 is
**2020-12-02 motion 1 (6 named voters)** — a legitimate 6-commissioner roll,
verified against source. Read the PC ceiling as the board's seat count, not 5.

## Roster (`roster.csv`) — 10 observed voters (drift 2020→2026)
Debbie Cragun, Kori Luker, Ulises Flynn, Johnny Loomis Jr, Holly Brown, Stephen
Walston (early), → Erik Swanson (2022), Tina Griffis (2022), Michael Kraupp
(2023), Joel Woodruff (2025). Only these names map to a vote; an OCR-garbled
roll-call name too corrupt to resolve is left **blank**, never guessed.

## Vote grammar — named inline rolls + narrative tally-only
As with council: `Commissioner X moved … seconded by Commissioner Y`, then either
a **named inline roll** (`Commissioner Flynn – AYE, … Commissioner Luker – NAY`,
`names_recorded:true`, 288 motions) or a **narrative tally-only** (`passed
unanimously` / `passed 4-to-1` with no member block → EMPTY member list,
`names_recorded:false`, 20 motions). Recommendations to the Council
(`forward a POSITIVE/NEGATIVE recommendation`) and PC final actions are carried
verbatim in `result`; normalized categories live in `motions_std.csv` (308 rows).
**CARDINAL RULE — never fabricate**: a tally-only unanimous majority stays
unnamed.

## The ONE known OCR-garbled tally — surfaced honestly, NOT patched
**2025-10-15 motion 4** (R-SL Senior Living text-amendment recommendation): the
OCR mangled the printed result to `"The motion passed 4- 28 ~—to-1"`, while the
**counted named roll is 3-1** (Woodruff/Flynn/Swanson **Aye**, Griffis **Nay**).
This is the **only** printed-vs-counted mismatch in the PC dataset (validator:
`printed-vs-counted mism. 1`; council = 0). The garbled `result` string is kept
**verbatim** and the 3-1 named roll is retained — the source garble is preserved
as honest evidence, never silently "corrected". Any fix belongs in an override
file + rebuild, never an in-place edit.

## Run
```
python3 extract_votes.py     # writes votes/*.json then rebuilds all_votes.csv (resumable)
python3 validate_votes.py    # writes votes/_validation_report.txt + roster.csv
```
`all_votes.csv` is valid RFC-4180 (read with a real CSV parser, NOT `awk -F,`).
