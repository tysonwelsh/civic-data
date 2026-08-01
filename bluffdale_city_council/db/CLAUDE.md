# bluffdale `db/` — build notes + the referral-layer precision audit

Read `SCHEMA.md` first for the table/column contract. This file records what a
consumer of the **`referral`** table must know before quoting a cross-body chain.

Rebuild (idempotent, in this order):

```
python3 ../../scripts/normalize_motions.py bluffdale   # motions_std.csv (reads motion text)
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer — reads db/referral_overrides.csv
```

`build_db.py` DROPS and rebuilds the referral table, so `build_referrals.py` must
follow it. Both are thin stubs over the shared `scripts/db_build_lib.py` /
`scripts/referrals_lib.py`; **neither carries bluffdale-specific parameters** —
all bluffdale tuning lives in `db/referral_overrides.csv` (see below).

## 2026-08-01 — the motion-text window was FIXED upstream; this layer was rebuilt

The 2026-07-31 audit (below, kept for the record) found the referral layer was
9.5% precise in its `high` tier and traced the cause **upstream, to the vote
extractor's motion-text window**. That defect was fixed on 2026-08-01 in
`meeting_minutes/extract_votes.py` + `planning_commission/extract_votes.py`
(same file, both datasets) and the whole chain was re-extracted and rebuilt.

**What the defect was.** `MOTION_INTRO` only matched a mover printed with a role
word and a ONE-token name (`Council Member Kallas moved`). Bluffdale's dominant
form is a **bare full name** (`Dave Kallas moved to approve the consent agenda.`)
— and the role-prefixed form usually carries the full name too
(`Council Member Dave Kallas moved`), which the one-token pattern also missed.
**376 of 971 council motions matched no intro at all**; for those the text window
opened at the previous motion's result — and at **byte 0 for `motion_no=1`**, so
the stored `motion` was the meeting's **agenda-notice preamble** (including City
Hall's own address, `2222 West 14400 South`). The in-session RDA/LBA "procedural
prose blob" class had the **same single root cause**: those motions
(`Mark Hales moved to approve Resolution 2020-05 …`) are also bare-name movers, so
their window opened on the preceding adjournment / roll-call / public-hearing text.

**The fix** (all city-faithful — it changes only WHICH verbatim span is stored):

- `WINDOW_INTRO` — role-prefix **optional**, 1–3 name tokens, **roster-gated**
  (`intro_key()`; staff and members of the public named in the narrative never open
  a window), plus an unambiguous first-name map (`Wendy moved …`), the OCR verb
  variant `mo[vy]ed`, and `made a/an <adj> motion`.
- tier-2 anchor `MOVED_ANY` for the handful of OCR-garbled mover names
  (`Debbie C ragun moved`) — window opens at the start of the sentence carrying the
  verb; a final bounded 400-char sentence-snapped fallback when no verb is printed.
- the window now **ends** at the first of: the roll-call clause, `seconded by <name>`,
  `<Name> seconded`, `The motion was seconded`, or the `Second:` label form.
- `classify_motion` Ceremonial: `commend` → `\bcommend` (**re**commend*ation* was
  matching `commend`).

**Proof the vote layer is untouched.** The re-extraction is a motion-TEXT fix and
nothing else: both `all_votes.csv` files are **identical on the
`(source, date, body, motion_no, member, vote)` key set and on the `result`
column** (2,996 council + 1,275 PC rows, byte-identical `votes/_validation_report.txt`
for both datasets: 971/308 motions, 513/288 named, 458/20 tally-only, body split
Council 872 / RDA 77 / LBA 22, 2 genuine mayor tie-breaks, 0 off-roster).

What DID change, all downstream of the corrected text:

| | before | after |
|---|---|---|
| motion text rows changed | — | 948 council / 292 PC |
| `motion.motion_type` | — | 214 council / 85 PC reclassified |
| `motions_std` classification cols | — | 180/52 `motion_type_std` (outcome + tallies UNCHANGED) |
| `person` | 56 | **29** |
| `application` | 530 | **325** |
| `referral` | 62 (tuned from 269) | **38** (tuned from 38) |
| `referral_overrides.csv` | 365 rows | **2 rows** |

`person` fell because `mover` was previously stored as a **bare surname straight
out of the regex** — including OCR variants (`KaUas`, `Kalias`, `WUding`,
`Griffls`), each of which became its own `person` row. Movers are now resolved to
canonical roster full names. (The residue `Astin`/`CouncU`/`Dave`/`Wendy`/… comes
from the **seconder** column, which this fix deliberately left alone — the
`seconder` values are byte-identical before and after.)

## Referral layer — post-fix re-audit, 2026-08-01

**With real motion text the false-positive flood simply does not occur.** The
UNTUNED layer is now **38 links**, not 269, and shared council↔non-council
addresses fell from the City-Hall boilerplate flood to **4 real parcels**.

| tier | 2026-07-31 untuned | 2026-07-31 tuned | **2026-08-01 untuned** | **2026-08-01 final** |
|---|---|---|---|---|
| high (`address+subject`) | 189 | 18 | 8 | **8** (+1 `override`) |
| medium (`subject`) | 69 | 41 | 29 | **28** |
| low (`address`) | 11 | 3 | 1 | **1** |
| **total** | **269** | **62** | **38** | **38** |

By body pair: **Council ← PlanningCommission 36**, **Council ← RDA 2**.
By method: `subject` 28 · `address+subject` 8 · `address` 1 · `override` 1.
30 of 109 council applications (27%) carry at least one cross-body link; the rest
are correctly UNLINKED.

**Precision — census, not sample.** All 38 untuned links were adjudicated
individually against the (now verbatim) motion text, with the ambiguous ones read
back at the source minutes (`2021-07-14`, `2022-01-05`, `2025-09-03`, `2025-10-15`,
`2025-11-12`, `2026-02-04`, `2026-02-18`, `2023-01-04`). **37 of 38 = 97.4% were
correct**; one was false. After the single suppression the layer is **38/38 = 100%**
(37 scored + 1 forced coverage link).

Two honest properties of the retained set, so nobody over-reads a chain:

1. **Project-level, not instrument-level, exactness.** Four links pair *companion
   applications on the same parcel considered at the same two meetings* rather than
   the exact counterpart instrument — e.g. the Council's zoning-map ordinance
   matched to the PC's **General-Plan-map** recommendation for the same 2022-01
   Tri-City Center parcels (13855/13937 S 2950 W; 13820 S 2700 W). The projects are
   the same and the exact-instrument pairs are ALSO present; treat these as
   "same matter package", not "this PC vote produced that ordinance".
2. **Multi-round PC histories are represented in full.** A matter that went to the
   PC more than once carries a link per round (Ord 2024-26 satellite stations: PC
   TABLE 2024-10-02 + TABLE + POSITIVE 2024-11-06; Ord 2026-01 WUI standards: PC
   POSITIVE 2026-02-04 + CONTINUE + TABLE 2026-02-18). These are real, not duplicates.

### The ledger — `db/referral_overrides.csv`, now **2 rows**

The 365-row suppression ledger is **retired**: 363 of its rows existed only to
mop up preamble/procedural-blob false positives that the window fix eliminated at
source, and their app_keys were stale against the new extraction anyway (the build
failed loudly on 346 of 366 — working as designed). The replacement ledger is two
evidence-cited rows, both prefixed `[2026-08-01 post-window-fix referral re-audit]`:

- **`suppress`** — Council Ord 2023-04 (MIH Element amendments, 2023-01-25)
  ✗ PC 2022-08-17. **Wrong round**: Ord 2023-04 was recommended by PC 2023-01-04
  (retained) and the 2022-08-17 PC item produced Ord 2022-15, adopted 2022-09-14
  (retained). This is the one survivor of the old ledger's hand-adjudicated pairs,
  re-verified at source. (The old ledger's other hand-adjudicated pair — Ord 2021-21
  Centrum ✗ PC 2021-07-07 Holiday Park — **no longer arises**; with real motion text
  the 2021-07-07 PC recommendation now correctly matches Ord **2021-41**, which is
  the Holiday Park SD-C zone at 15228 S Porter Rockwell.)
- **`link`** (forced) — Council Ord 2025-26 (R-SL Senior Living Zone basements,
  2025-11-12) ← PC **2025-10-15** POSITIVE recommendation. A **coverage** row, not a
  precision one: the R-SL amendment went to the PC twice (2025-09-03 NEGATIVE —
  that scored link is retained; 2025-10-15 POSITIVE, after a negative motion died
  for lack of a second). The scorer missed the second round because that minutes
  page is line-numbered and the stray digits depress the Jaccard subject score.
  Without this row the chain shows only the negative round and reads as a
  PC/Council divergence the record does not support.

**The Jordan Crossing pair is safe and needs no protection any more.** With real
motion text the only verified Council↔RDA co-action —
`Council|project area plan` ← `RDA|community reinvestment project area plan`,
**2020-02-26**, the Jordan Crossing Community Reinvestment Project Area Plan
adopted by RDA resolution and Council ordinance in the same meeting — **scores
naturally** (subject 0.697) and no procedural rule touches it. A **second** genuine
Council↔RDA co-action surfaced once the blobs were gone: **2022-03-09**, Council
Ord 2022-06 / RDA Res 2022-03 **dissolving** that same project area (subject 1.000).

### Cardinal-rule notes for anyone re-tuning

- Override app_keys are **fail-loud**: a re-extraction that changes motion text (and
  therefore application bucketing) makes the keys unresolvable and
  `build_referrals.py` exits non-zero rather than silently dropping the tuning. That
  is intended — **regenerate the ledger against the new extraction, don't delete rows.**
- Suppressing a link **promotes the next-best candidate in its group** (the
  `SECONDARY_MARGIN` / best-per-related-body cap in `referrals_lib.evaluate`), so
  re-run `build_referrals.py` until the link count stops moving. It was run to a
  fixed point here (stable at 38 over three consecutive rounds).
- **Do not loosen or re-score the referral thresholds.** The 2026-07-31 experiments
  with `extra_stopwords` and `content_veto` + `template_stopwords` + `member_names`
  are still **not enabled** and should stay that way; the library defaults now
  produce a 97.4%-precise untuned layer on this city. (Those knobs were tried
  against the BROKEN text and made bluffdale worse or did nothing — the structural
  blocker they could not clear, boilerplate carrying City Hall's own street
  address, no longer exists.)

## Historical — the 2026-07-31 precision audit (superseded, kept for provenance)

Finding: the untuned referral layer was **9.5% precise in its `high` tier**
(189 → 18 after tuning; 269 links → 62 total; every link reviewed). Coverage was
not the problem — 207 of 269 links were false. Root cause: `application.rep_title`
is the motion text and **92% of applications (488/530) were per-motion `singleton`
buckets**, so an app's identity was a ~600-char raw-minutes window. Two classes of
that window carried no matter at all — the **agenda-notice header bleed** (94
motions, all `motion_no=1`; 171 of the 189 `high` links were boilerplate↔boilerplate
joined on `2222 w 14400 s`) and **procedural prose blobs** (in-session RDA/LBA
adjournment / roll-call / Mayor's-Report continuations; 39 of 40 agency-tier links
false). That audit correctly diagnosed the cause as upstream and refused to fix it
by re-scoring; the 2026-08-01 window fix above is the repair it flagged.
