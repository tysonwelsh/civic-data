# summit_county / land_use — VERIFICATION

## 2026-07-25 — PC divided-vote recovery (`build_votes.py` v2 → v3)

**Driver:** `_audits/2026-07-25/report.md` defect F2; plan + owner ruling in
`_audits/2026-07-25/remediation.md`. Backups: `_backups/2026-07-25-summit-pc/`.

### Premise correction found during source verification

The audit reported the PC roll calls as sitting unparsed in retained Granicus HTML. **They
are in HTML comments the portal never renders** — 545 of 545 `AYES` occurrences are
comment-enclosed, 0 rendered; the original converter stripped comments, which is correct.

Before deciding anything, the hidden data was tested rather than assumed:

| test | result |
|---|---|
| blocks paired to the published prose tally by document order | **520 / 520 agree exactly**; 0 disagree |
| empty template blocks (no names either side) | 25, excluded |
| divided motions whose dissenter is ALSO named in rendered text | **25 / 25** |
| dissent recoverable ONLY from the hidden block | **0** |

**Owner ruling 2026-07-25: published prose only.** The hidden blocks are real but
unpublished and add no contested signal, so they are not ingested. Recorded here and in
TODO.md so the "gap" is not re-opened by a future pass.

### Causes fixed (all four verified against source before patching)

1. **Result/tally taken from anywhere in the segment.** v2 searched to the next motion
   anchor — up to 40k chars — and took the first `Pass` keyword found. 2020-06-23 m1
   inherited `MOTION CARRIED (6-1)` from ~10k chars downstream while its own item had
   FAILED. v3 binds result+tally to the nearest **tally-bearing** marker line (a bare prose
   "The motion carried." no longer wins over the formal `MOTION CARRIED (5-1) …` line).
2. **Four unparsed divided-vote grammars** — leading (`Opposed were X, Y and Z`,
   `Voting against were …`, `Those voting in approval were:`), trailing (`… objected.`,
   bare `… against.`), dotted-leader line wraps, and the 2020 two-column poll grid
   (`Commissioner Stevens- Nay   Commissioner Simons- Yea`), which a running page header
   can interrupt mid-poll.
3. **En-dash tallies** (`(6 – 0)`) were invisible to the tally regex.
4. **Name fabrication risk introduced and removed mid-pass**: an initial patch used `re.I`,
   which defeats the leading-capital constraint and produced members like `on`,
   `is going into`, `Henrie said`, `Christopher Conabee seconded`. `re.I` was dropped and
   trailing-verb tokens added to `STOP`. **Final state: 0 non-name-shaped members.**

### Before → after

| measure | v2 | v3 |
|---|---|---|
| motions | 1,526 | **1,526** (unchanged) |
| motion text / mover / seconder | — | **byte-identical on all 1,526** |
| named-roll motions | 256 | **270** |
| named vote rows (`all_votes.csv`) | 409 | **469** |
| result `Pass` → honest blank | — | 15 (no result printed; v2 had borrowed one) |
| result `Pass` → `Fail` | — | 1 (2015-08-20 m5) |
| tally recovered (was blank) | — | 52 (en-dash form) |
| impossible attributions removed | — | 2 (Nay rows against a `(7-0)` tally) |

### Gates

- **Named votes never exceed their own tally: 0 violations.**
- **Every `member` value name-shaped: 0 fragments.**
- `db/build_db.py` — foreign_key_check OK, integrity_check ok; vote 518 → **578**
  (Council 109 + PC 469); named-roll motions 279 → **293**.
- `link_applications.py` / `link_ordinances.py` reproduce **link-for-link** (70 unique app
  links, 67 `application_id`s, ordinances 962→302 / 968→402 / 980→874 / 1003→1633).
- **FILES-WIN reconciliation exact**: `all_votes.csv` 469 rows == gov.db PC vote rows 469.
- `validate_entity.py summit_county` → **10 PASS / 0 WARN / 0 FAIL**.
- `screen_corpus.py` on `land_use/minutes` unchanged (extractor only reads the corpus).

### Residual after v3 — CLOSED by v4, below.

## 2026-07-25 (same day) — marker-anchored segmentation (`build_votes.py` v3 → v4)

**Driver:** the v3 residual above. v3 still found items by their "X made a motion" verb and
then looked for a result; where the clerk phrased an item differently the item vanished and
its printed outcome was inherited by whichever item *was* found.

**The change.** v4 pairs two streams in document order — motion verbs and printed outcomes —
instead of hunting outward from one. Every printed outcome gets its own item; an item with
no printed outcome keeps an honest blank. Supporting fixes found while proving it:

- **Marker de-duplication by bound tally.** `• MOTION CARRIED (7-0)  All voted in favor.`
  is one outcome announced twice; markers binding to the *same* tally collapse, markers
  binding to *different* tallies never do (an early rule merged distinct votes on
  consecutive short items and inflated blank results 147 → 461).
- **Tab-separated OCR files.** `made a motion` was written with literal spaces, so
  tab-separated minutes matched nothing — **2016-11-03 eastern yielded 0 motions and now
  yields 6**, all with movers, tallies and named dissenters. Every gap in the anchor,
  seconder and motion-text patterns is now `\s+`. (Same lesson as the utah_county anchor bug.)
- **Unicode hyphens.** `(7‐0)` uses U+2010, invisible to an ASCII-only dash class; the tally
  class now covers `- ‐ ‑ ‒ – —`.
- **Poll-grid name pattern.** `NAMEC` admits internal hyphens and spans newlines, so
  `Kucera-Nay \nCommissioner Harte` was swallowed as one name and lost 4 of 7 voters.
  The grid now uses a hyphen-free, single-line name pattern.
- **Tally orientation from evidence.** Where a full named roll contradicts the parsed
  orientation (`MOTION FAILED (6-1)` over a roll of 1 Yea / 6 Nay — prevailing side printed
  first), the **names win**; the verbatim `tally` string is still stored exactly as printed.
- **Motion-text fragments.** `…made the motion, which was seconded by X to approve Y` needed
  a comma to strip; without one the text became the fragment `which was`. **26 → 2.**

### Decisive measure

Every printed tally line should have exactly one motion carrying it:

| | v3 | v4 |
|---|---|---|
| meetings where tallied motions == tally lines | 303/342 (89%) | **339/342 (99%)** |
| — AgendaCenter era (the broken one) | 82% | **99%** |
| — Granicus era (already clean) | 100% | 100% |

### Before → after (v3 → v4)

| measure | v3 | v4 |
|---|---|---|
| motions | 1,526 | **1,575** (+49, **all gains — 34 meetings, 0 losses**) |
| named vote rows | 469 | **497** |
| named-roll motions | 270 | **282** |
| `which was` text fragments | 26 | **2** |
| db vote rows (Council + PC) | 578 | **606** |
| federated contested | 292 | **304** |

### Gates (all re-run on v4)

- named Ayes/Nays never exceed the motion's own tally: **0 violations**
- every `member` value name-shaped: **0 fragments**
- no member voting twice on one motion: **0**
- `foreign_key_check` OK · `integrity_check` ok
- **application/ordinance links reproduce link-for-link despite full PC renumbering** —
  70 unique app links / 67 `application_id`s, ordinances 962→302 / 968→402 / 980→874 /
  1003→1633. (`link_*.py` recompute from motion text rather than reading stored ids, so
  renumbering is absorbed.)
- **FILES-WIN exact**: `all_votes.csv` 497 == gov.db PC votes 497; `motions_tally.csv`
  1,575 == gov.db PC motions 1,575
- `validate_entity.py summit_county` → **10 PASS / 0 WARN / 0 FAIL**

### Worked example

`2020-06-23` Snyderville: v2 recorded 4 motions, the first carrying a `Pass` and a `(6-1)`
tally borrowed from a *different* motion ~10k characters downstream, while the item that
actually failed was missing entirely. v4 records 5 motions — m1 `Fail (6-1)` with the full
7-member poll (Simons the lone Yea) and m2 `Pass (6-1)` with its own poll (Simons the lone
Nay). Both match the source line for line.

### Motion-text fragments — fully closed

`which was` **26 → 0** (the strip pattern required `to approve …`; the clerk also writes
`…seconded by X, THAT the Commission approves …`), and `All voted in approval` ×4 removed —
an outcome sentence the action-picker was mistaking for the motion's substance because
`ACTION` matches the word "approval". Remaining short texts are all legitimate: `adjourn`
(195), `adjourn the meeting` (37), `approve the minutes` (2).

### Repo-wide check: do these bug classes bite other entities?

Two of the four bugs are generic, so the corpora — not the code — were scanned for the
triggers (a vulnerable regex only matters if the data exercises it). Of 41 entity trees:

| trigger | entities hit | verdict |
|---|---|---|
| U+2010/11 hyphen inside a tally | summit (fixed), herriman ×1 file, park_city ×1 file | **herriman + park_city are FALSE POSITIVES** — herriman's `(10‑1)`/`(6‑0)` are *state legislature committee* counts quoted in a bill report (council max roll is 6); park_city's `(5‐7 )` is item numbering in a list. Neither is a council tally, and neither should be extracted. |
| tab-separated words | summit (fixed), midvale ×5 files, wfrc_mpo ×1 | No loss: all 8 affected meetings extract motions with **0 blank results** (midvale 7–19 motions each with named vote rows; wfrc 4). |

**36 of 41 trees show neither trigger.** So these two classes were, in practice,
summit-only. Not a clean bill of health for midvale/wfrc — the check was a count sanity
test, not a source diff — but there is no sign of the summit failure mode there.

### Residual

`2017-09-12` is the one meeting where the count check still disagrees, and **the extractor
is right**: the tally there is `(4-1-1)`, which the *verification* regex can't parse. 20
motions carry a blank motion text — items the clerk recorded a vote for but never phrased
as a motion; the vote and tally are faithful and the text is honestly blank rather than
invented.

## 2026-07-25 (same day) — the remaining audit items for this entity

Closing pass over every other summit finding in `_audits/2026-07-25/report.md`.
Backups: `_backups/2026-07-25-summit-council/`.

**Council motions — 11 recovered (audit D2 + a defect the audit missed).**
`legislative/extract_votes.py` reads the Granicus HTML and only saw motions wrapped in a
bold/`<strong>` div. Two other wrappings existed: a **MediaPlayer deep-link**
(`<div><a href=…MediaPlayer.php…><strong>`) and a **plain `<div>` with no emphasis at all**
(the closed-session motions that open a meeting). 2026-06-03 published 10 tallies and
yielded **2** motions; 2026-04-22 published 14 and yielded 11. Fixed by allowing the link
wrapper and adding a second pass keyed on the motion **grammar** (mover + verb + printed
tally) rather than on markup. **Council motions 1,820 → 1,831; meetings where motions equal
published tallies: 0 now under-extracted** (was 2, missing 11). Duplicate check: 21 dup keys
/ 30 rows before and after — the second pass introduced **none**; on FULL motion text only
**3** duplicate rows exist repo-side, all pre-existing.

**The audit's D2 hidden-block half is NOT actionable.** All 10 `AYES` blocks in clip 1370
are inside HTML comments (0 rendered) — the same unpublished markup as the PC layer, so the
2026-07-25 owner ruling (published prose only) applies unchanged.

**PC duplicate motions (audit D3) — the finding was 90% false positive.** The audit reported
"31 duplicated motion rows". Tested by measuring repeated-long-line density per meeting:
only **2015-01-08 eastern** is a genuinely doubled document (68% repeated lines; its page
footers run 2..22 then 2..22 again). The other 23 duplicate-bearing meetings sit at 0–5% —
their repeats are real. Verified at source: 2017-06-27 carries three *separate* minute
approvals (March 28 / April 25 / May 9) that the clerk mislabelled "March 28" in all three
headings — different seconders confirm; **source-faithful, correctly kept**. Fixed only the
real one, via `strip_duplicate_body()` (cuts at a page-footer restart on the same page
TOTAL; fires on exactly **1 of 393** files). 2015-01-08: 8 motions → **4**, matching the 4
outcome markers in the first copy.

**Ordinance adoption dates (audit D4) — both corrected.**
- **Ord 1003**: `2025-12-04` → **`2025-12-17`**. That date appears in the ordinance text only
  as unrelated prose ("with comments as of December 4, 2025", line 209); the enactment clause
  (line 26) reads *"Enacted this 17th day of December, 2025"* and the enacting roll call
  (motion 1633) is 2025-12-17.
- **Ord 968**: `2023-09-12` → **blank**. It had no source: the signature block is
  OCR-unreadable (`Enacted this)" day of Guplumdpentoos,`) and the enacting roll call
  (motion 402) is 2023-09-20. Blanked per the module's own 912/936 precedent rather than
  assert an unevidenced day; both facts recorded in `notes`.
- 962 and 980 were verified correct and left alone.

**Packet sidecars (audit D8) — 58 repaired.** Two font-cmap pathologies: PUA glyphs
(U+F0xx − 0xF000, the Sandy class) and a **CID shift of −0x1D** that stored
*"J-U-B SHALL RETAIN ALL COMMON LAW, STATUTORY, COPYRIGHT"* as
`-\x108\x10%\x036+$//\x035(7$,1…`. `decode_cmap()` in `packets/build_packets.py` repairs
both, applied **per line and only when the shift raises that line's dictionary-word ratio**
— so it can never make a line worse. Sidecars above 2% control characters: **6 → 4**; the
residual 4 are pure CAD coordinate text where no shift helps. Wired into the build path and
applied to existing sidecars without re-fetching 1.8 GB of packets.

**Development types (audit D7) — 104 rows reclassified.** `dev_type` was matched over the
whole 2,500-char item block, so a project's NAME and even public-comment text outranked the
actual application: *"Conditional Use Permit for a 'Vehicle control gate' … White Pine
Ranches Subdivision"* was typed `subdivision`. Now classified from the item **title**,
taking the **earliest-matching** type (an application's kind leads its title), falling back
to the block only when the title names no type. `subdivision` 212 → 147, `plat_amendment`
39 → 88, `conditional_use_permit` 147 → 177. Ground-truthed 8 random changes against source
titles: 7 unambiguously correct, 1 genuinely dual ("31-lot Preliminary Subdivision Plat/MPD"
— either label defensible).

**Caveat rows (audit D9) — seeded for the whole non-city tier.** 7 of 9 entities had none,
so `v_member_record_all` returned county rows with an EMPTY `record_caveats`. Added to
`scripts/build_cities_db.py`: summit ×2, utah/weber/cache/washington/juab ×1, ut_state ×2.
Verified the mechanism now works — the exact row the audit flagged
(`Clyde | Eastern Summit County PC | 38 nays`) now carries
`record_caveats=tally-only-partial,vote-ceiling`.

**Doc drift (audit D12).** `recon.md` 195 → 198 meetings and 1,820 → 1,831 motions;
`elections/CLAUDE.md` no longer claims the entity is unregistered (it is, fed_index 105).

### Final state

PC motions **1,571** · PC named vote rows **496** · Council motions **1,831** ·
db motion **3,402** · vote **605** (Council 109 + PC 496) · named-roll motions **304** ·
applications **576** · federated contested **303** · `validate_entity` 10 PASS / 0 WARN /
0 FAIL · FK/integrity OK · FILES-WIN exact (496 == 496) · app/ordinance links reproduce
link-for-link · `build_votes.py` byte-stable on re-run.

**Every summit finding in `_audits/2026-07-25/report.md` is now closed or ruled out.**
