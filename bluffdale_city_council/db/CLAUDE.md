# bluffdale `db/` — build notes + the referral-layer precision audit

Read `SCHEMA.md` first for the table/column contract. This file records what a
consumer of the **`referral`** table must know before quoting a cross-body chain.

Rebuild (idempotent, in this order):

```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer — reads db/referral_overrides.csv
```

`build_db.py` DROPS and rebuilds the referral table, so `build_referrals.py` must
follow it. Both are thin stubs over the shared `scripts/db_build_lib.py` /
`scripts/referrals_lib.py`; **neither carries bluffdale-specific parameters** —
all bluffdale tuning lives in `db/referral_overrides.csv` (see below).

## Referral precision audit — 2026-07-31

**Finding: the untuned referral layer was 9.5% precise in its `high` tier.** It
has been ground-truthed link-by-link and tuned. Current state:

| tier | pre-audit | post-audit | precision (audited) |
|---|---|---|---|
| high (`address+subject`) | 189 | **18** | 18/189 = **9.5%** → 18/18 = 100% |
| medium (`subject`) | 69 | **41** | 41/69 = **59.4%** → 41/41 = 100% |
| low (`address`) | 11 | **3** | 3/11 = **27.3%** → 3/3 = 100% |
| **total** | **269** | **62** | **62/269 = 23.0%** → 62/62 = 100% |

Coverage was **not** the problem — 207 of the 269 links were false. Every link in
the old layer was reviewed (the ~180-link boilerplate class by a verified rule +
source spot-checks; all others read individually against the minutes), so these
are census figures, not sample estimates. By body pair the post-audit set is
**Council ← PlanningCommission 61** and **Council ← RDA 1**.

### Why it failed — the root cause is UPSTREAM, in the motion-text layer

`application.rep_title` is the motion text, and **92% of bluffdale's applications
(488 of 530) are per-motion `singleton` buckets** — `project_name()` finds no name
in the prose, so the app's whole identity is a ~600-character window of raw
minutes text. Two classes of that window carry **no matter at all**:

1. **Agenda-notice header bleed (94 motions).** For the first motion of a meeting
   the extractor's text window starts at the top of the document, so `motion_no=1`
   rows carry the meeting-notice preamble ("Notice is hereby given that the
   Bluffdale City … will hold a public meeting … at the Bluffdale City Hall
   located at **2222 West 14400 South**") instead of the motion sentence. Verified
   at source: PC 2020-01-08 motion 1 is *approval of the December 4, 2019 minutes*;
   Council 2020-01-15 motion 1 is *approval of the consent agenda*.
   Consequence: **every such application carries City Hall's own street address**,
   the referral engine reads it as a shared parcel, and any two of them clear the
   `address + subject≥0.20` bar. **171 of the 189 `high` links (90.5%) were
   boilerplate↔boilerplate joined on `2222 w 14400 s`** — plus 8 of the 11 `low`
   and 4 `medium`. All 50 applications behind them are `motion_no=1`.
2. **Procedural prose blobs.** In-session RDA/LBA sections produce motions whose
   window is an adjournment / roll-call / call-to-order / "Mayor's Report"
   continuation, and the 2022+ terse-minutes era produces motions like *"Board
   Member Aston moved to ADJOURN"* or *"…APPROVE RDA Resolution 2025-28 – Budget
   Adjustment"*. These matched unrelated Council ordinances on shared
   motion/budget vocabulary. **39 of the 40 agency-tier links audited were false**;
   the single true one is retained (below).

The referral engine is behaving correctly on the input it is given. **Do not
"fix" this by loosening or re-scoring the referral thresholds** — the fix belongs
in the vote-extraction motion-text window. Flagged as a lead for the vote layer;
until it lands, the override ledger is what holds precision.

### What was tried and rejected (do not repeat)

`scripts/referrals_lib.py` exposes opt-in per-city knobs. Both were tested here
and **both made bluffdale worse or did nothing** — they are deliberately NOT
enabled, and bluffdale's `build_referrals.py` stub is left at library defaults:

- **`extra_stopwords` (+ guard)** — stripping the notice vocabulary empties the
  boilerplate token sets, which *shrinks the Jaccard union* and **inflates** the
  score. Result: 162 links / 81 `high`, worse than the override route.
- **`content_veto` + `template_stopwords` + `member_names`** — a no-op here (269
  links, unchanged). The veto only fires when the *entire* shared-token overlap is
  template; notice preambles always share enough incidental prose to defeat it.
  It also cannot help at all in the `address` branch, which is where the dominant
  false-positive class lives.
- The structural blocker for both: **the boilerplate contains a real street
  address (City Hall), structurally identical to a project address.** There is no
  address-blocklist parameter, so no scoring knob can separate the classes.

### How the tuning is expressed — `db/referral_overrides.csv`

**365 rows, all `action=suppress`, keyed by stable `primary_app_key` /
`related_app_key`** (content-derived; integer `application_id`s drift on rebuild).
Every row carries a note prefixed `[2026-07-31 referral precision audit]` naming
its evidence class. The four classes:

| class | rows | basis |
|---|---|---|
| agenda-notice header bleed | bulk | both sides are `motion_no=1` notice-preamble apps; only shared "address" is City Hall |
| procedural prose blob | bulk | one side is an adjournment / roll-call / call-to-order / Mayor's-Report window |
| agency budget/terse boilerplate | bulk | RDA/LBA annual-budget or terse motions matched to an unrelated Council matter |
| hand-adjudicated | 2 | see below |

The two hand-adjudicated rows:

- **Council Ord 2021-21 (Centrum) ✗ PC 2021-07-07 (Holiday Park)** — different
  projects (LH Perry app 2021-31 vs Wagstaff, 15228 S Porter Rockwell); the
  overlap is only the Title 11 ch. 11.110.120 ordinance-structure phrasing. The
  Centrum's genuine PC recommendations (2021-09-29, 2021-10-20) are retained.
- **Council Ord 2023-04 (MIH) ✗ PC 2022-08-17 (MIH)** — wrong round. Ord 2023-04
  was recommended by PC 2023-01-04 (retained); the 2022-08-17 PC item produced
  Ord 2022-15 (retained).

**One agency link is deliberately RETAINED** and is the only verified Council↔RDA
co-action in the corpus: the **Jordan Crossing Community Reinvestment Project Area
Plan, 2020-02-26** — the RDA adopted the plan by resolution and the Council
adopted the same plan by ordinance in the same meeting. Its Council-side
application is a procedural blob, so the mechanical procedural rule would suppress
it; it is protected on purpose. **If you regenerate the override ledger, protect
this pair.**

### Cardinal-rule notes for anyone re-tuning

- The suppression list is a **strict subset filter**: the post-audit 62 links are
  all present in the pre-audit 269. **No link was invented**, re-scored, or had
  its confidence changed — verified by an app_key-level diff.
- Suppressing a link **promotes the next-best candidate in its group** (the
  `SECONDARY_MARGIN` / best-per-related-body cap in `referrals_lib.evaluate`).
  The ledger was therefore iterated to a **fixed point** (11 rounds) — a partial
  suppression list silently backfills with fresh false positives. Re-run
  `build_referrals.py` until the link count stops moving.
- Override app_keys are **fail-loud**: a re-extraction that renumbers motions will
  make these keys unresolvable and `build_referrals.py` will exit non-zero rather
  than silently drop the tuning. That is intended — regenerate the ledger, don't
  delete rows.

## Incidental, same session

Rebuilding `civic.db` also refreshed **14 `motion_std` rows** that had gone stale
against the canonical on-disk `meeting_minutes/motions_std.csv` /
`planning_commission/motions_std.csv` (13 PC `rule:rec-not-ceremonial` rows +
1 council `Ceremonial`→`Resolution` row). The db now agrees with the flat CSVs;
no CSV was edited. All other tables are byte-identical in row count
(motion 1279, vote 3793, application 530, meeting 295, person 56, role 41).
