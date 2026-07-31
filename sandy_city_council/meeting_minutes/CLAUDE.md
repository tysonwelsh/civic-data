# meeting_minutes/ — Sandy City Council vote pipeline

## What's here
- `minutes/<year>/<week-monday>/<date>_city-council-meeting.md` — 274 Granicus/Legistar
  council-meeting minutes, 2020-01 → 2026-06. Council meets weekly on Tuesdays; the
  folder is keyed on that week's Monday. Indexed in `minutes_index.csv` (`format` =
  `text` for 153 born-digital text-layer files, `text_pua_decoded` for 63 born-digital
  files repaired 2026-07-02 (see **PUA repair** below), `ocr` for 58 scanned/OCR'd
  files — slightly lower fidelity, flattened whitespace).
- `raw/<date>_city-council-meeting.pdf` — the 274 retained source PDFs (never modified).

## PUA repair (2026-07-02)
63 of the 274 minutes (2021-08-17 → 2023-11-14: 8×2021, 21×2022, 34×2023) were majority-
encoded in Unicode Private Use Area characters (U+F020–U+F0FF) — the source PDFs for that
span carry a **broken font ToUnicode cmap**, so text extraction emitted `codepoint+0xF000`
instead of ASCII (verified: `pdftotext` on the retained raw PDFs yields the identical PUA
garble). The defect was mechanically reversed in place on 2026-07-02 by mapping every char
in U+F020–U+F0FF to `chr(ord(c)-0xF000)`; nothing else was touched. Verification: decoded
files match the decoded raw-PDF text at 1.0000 similarity; three files (2021-09-21,
2022-05-17, 2023-03-07) were also visually checked page-by-page against the rendered PDFs
(names, motions, roll calls exact). No unreadable stretches remain (0 PUA chars, 0 U+FFFD
corpus-wide; decoded dict-word ratio 0.774 ≈ corpus median 0.768). These rows carry
`format=text_pua_decoded` in `minutes_index.csv`. Originals preserved under
`_backups/2026-07-02/`. The vote extractor had captured **zero** votes from these files;
re-extraction recovered **+178 motions / +123 named roll-call motions** (2021 +21/+14,
2022 +58/+34, 2023 +99/+75). Together with the roster fix below, member-vote rows went
2,974 → **3,975** and contested motions 79 → **131** (2022: 1 → 24; 2023: 0 → 24).

## Roster fix (2026-07-02, same pass)
The decoded 2022–23 files surfaced a member missing from the extractor's name table:
**Scott Earl**, appointed District 4 council member Jan 2022 (after Zoltanski became
Mayor) until end of 2023 (lost the 2023 D4 race to Houseman) — 155 vote rows, first
2022-01-25, last 2023-12-19. Three **source clerk typos** were also added as normalization
aliases, each verified against the raw PDF: "Cyndi Shakey" (→ Sharkey; 2021-08-17,
2025-08-26), "Ryan Mecahm" (→ Mecham; 2024-02-13 ×2), "Alison Stoud" (→ Stroud;
2021-07-13, 2023-05-30). One faithful-capture consequence: **2021-08-17 motion 5** lists
Sharkey in BOTH the Yes list (as "Cyndi Shakey") and the No list — a contradiction in the
official minutes themselves (verified on raw PDF p.7); both rows are kept, so the
duplicate-member integrity check reads 1 (documented, not a parser bug).
- `extract_votes.py` — the parser (run it to regenerate everything below).
- `votes/<year>/<week>/<date>_*.json` — one structured JSON per meeting (the resumable
  intermediate; `all_votes.csv` is rebuilt from these).
- `votes/_validation_report.txt` — integrity checks, per-year roster, contested-vote list.
- `all_votes.csv` — long format, **one row per member-vote**, schema:
  `date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`

## Run
```
python3 extract_votes.py        # writes all votes/*.json then rebuilds all_votes.csv
```
The script overwrites every JSON each run. `all_votes.csv` is valid RFC-4180 (motion text
contains commas/quotes — read it with a real CSV parser, NOT `awk -F,`).

## Council composition / the Mayor does NOT vote
Sandy is a **strong-mayor** city: **7 voting council members** (4 districts + 3 at-large);
the **Mayor does not vote** and the council elects its own Chair. The Mayor appears in the
minutes' Administration roster but is **excluded from every vote list**. Member name
synonyms are normalized to one canonical spelling (e.g. "Kris Nicholl" / "Kris Coleman
Nicholl" → "Kristin Coleman-Nicholl"; "D'Souza" → "D'Sousa").

Roster note: **Monica Zoltanski** was the elected District 4 council member (voting
2020–2021), then became **Mayor in Jan 2022** (non-voting thereafter). **Scott Earl** was
appointed to the vacated District 4 seat and voted from 2022-01-25 through 2023-12-19
(he lost the 2023 D4 race to Houseman). The only places a Mayor's name appears in a vote
roster are **Board of Municipal Canvassers** election-canvass actions, where the minutes
themselves list the Mayor as a canvasser: 2023-12-06 (m3/m4, Excused), 2025-08-26 (m5),
and 2025-11-18 (m6) — faithful to the source and left as-is (tagged `body=Council`).

## `body` column (RDA / CRA / MBA)
Default `Council`. In Utah the council usually sits **as the Redevelopment Agency board**.
In Sandy's minutes the **substantive RDA business is held in SEPARATE RDA meetings whose
minutes are a distinct Legistar body and are NOT on disk** — the council files literally
say *"Official RDA Board action will be reflected in the RDA meeting minutes."* So inside
these council files the only RDA-related item is normally the **procedural "recess the
Council and convene the RDA" motion**, which is a *Council* vote (taken before the body
actually changes) and is therefore tagged `body=Council`. Only genuine RDA substance voted
**inline** is tagged `body=RDA` — there is exactly **1** such motion in the whole corpus
(2021-06-01, RDA Resolution RD 21-03, 7-0). No CRA/MBA blocks appear. See the
**acquisition gap** note below.

## Vote-format variants the parser handles
- Named roll-call: `Yes: 7- <names>` / `No: 1- <name>` / `Abstain: 1 <name>` /
  `Excused: N <names>` (→ `absent`). OCR variants `Yes-6` / `Yes 6` (no colon).
- **Present/Excused-only** roll-call (no `Yes:` line) on a passing motion → the Present
  members are recorded as `aye`, Excused as `absent`.
- Inline tally + minority callout: `…carried by a roll call vote of 5 - 2. X and Y opposed.`
  (and `…abstaining`) → tally captured, minority names captured, majority left unnamed.
- Wrapped result phrases (`…The motion` / `carried by the` / `following vote:` split across
  page-break lines) are **stitched** before parsing, and page footers/headers are stripped,
  so trailing names aren't dropped.
- Unanimous **voice vote** / `motion carried` with no names → `names_recorded:false`, empty
  member lists (one CSV row with blank `member`/`vote`). Never invents who voted how.
- `…failed for lack of a second` / `died` → recorded, no members.

`motion_type` uses the fixed 12-category taxonomy (Ordinance, Resolution, Budget Amendment,
Grant-Funding, Interlocal, Appointment, Public Hearing Action, Procedural/Administrative,
Ceremonial, Contract/Purchase, Land-Use/Zoning, Other).

## Acquisition gap (flagged, not re-acquired)
Sandy holds **separate RDA meetings** as a distinct Legistar body. Those RDA minutes were
**not acquired** — every file on disk is a `city-council-meeting`. The council minutes
reference ~25+ "convene the RDA" recesses across 2020-2026, each implying a separate RDA
meeting with its own (un-captured) substantive votes (TIF / developer-subsidy / project-area
budget decisions — the high-value "follow the money" data). To close the gap, harvest the
RDA meeting body from the same Granicus/Legistar portal. CRA/MBA bodies were not observed.

## Validation summary (see `votes/_validation_report.txt`, regenerated 2026-07-02)
274 meetings · 833 motions · 531 with named members · 302 tally-only/voice · 3,975
member-vote rows · 131 contested · result-vs-named-tally mismatches: **0** · >7-voter
motions: **0** · duplicate-member-in-a-motion: **1** (the documented 2021-08-17 source
clerk error, above) · Mayor in ordinary council votes: **0** (the three canvass actions
excepted, above). The 16 narrative inline-tally motions (11×2020, 5×2021) whose Aye
majorities are unnamed were re-verified against source 2026-07-02: the Aye names are
**not printed in the minutes** (narrative form, dissenters only) — an honest gap, not a
page-break parsing drop.
