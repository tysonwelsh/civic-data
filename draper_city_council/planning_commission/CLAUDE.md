# planning_commission/ — Draper City Planning Commission subtree

Parallel dataset for Draper's **Planning Commission**, sibling of `meeting_minutes/`, built to the
same schemas (SCHEMA_SPEC.md applies in full). Every `all_votes.csv` row is
`body=PlanningCommission`. Data floor **2020**.

## Files
- `minutes/<year>/<week>/<date>_planning-commission*.md` — **143** PC minutes, **2020-01-09 →
  2026-05-28**. The PC meets **Thursday**. Indexed in `minutes_index.csv` (`source=granicus` — 141;
  `source=pmn` — the 2 former broken-stub dates **2020-12-10** and **2024-10-10**, recovered from
  Utah Public Notice and promoted 2026-07-16; `format=text` — all born-digital). Meetings noticed
  but with no posted / broken minutes live in `minutes_unrecovered.csv`. Raw PDFs in `raw/`.
- `all_votes.csv` — long format, one row per member-vote (or one placeholder per tally-only motion),
  the standard 13 columns **+ a documented trailing 14th `provenance` column** (`minutes` |
  `pmn_minutes`, 2026-07-16). **911 motions across 143 meetings; 4,324 rows (4,114 named)**
  (the 2026-07-17 narrative-era recovery added 32 named rows — see the dated note below).
- `votes/<year>/<week>/<date>_*.json` — the resumable per-meeting intermediate; `all_votes.csv` is
  rebuilt from these. `votes/_validation_report.txt` from `validate_votes.py`.
- `roster.csv` — commissioners observed with first/last vote + count.
- `extract_votes.py` / `validate_votes.py` — deterministic parser + sanity report.

Run: `python3 extract_votes.py` then `python3 validate_votes.py`.

## The PC is the busy, contested body
Draper's Planning Commission runs a heavy land-use docket: **220 contested** motions vs the
Council's 15 (was 214 before the 2026-07-17 narrative recovery surfaced 6 more real dissents).
Vote values: **Aye 3,227 · Absent 558 · Recuse 179 · Abstain 76 · Nay 74** (+ 210
tally-only placeholders). The named grid is `Yes / No / Abstained / Not-Participating / Absent`
(**Not-Participating → `Recuse`**); the parser reads it directly per member.

## Recommendation vs Final Action — preserved in `result`
The PC issues two kinds of decision, both kept **verbatim** in `result`:
- **Positive/Negative Recommendation** — rezones, general-plan / code-or-text amendments,
  annexations forwarded to the City Council (db `stage=pc_recommendation`, **232 motions**).
- **Final Action (Approved/Denied)** — CUP, site plan, plat, subdivision, variance items the PC
  decides itself (db `stage=pc_final_action`, **679 motions**).

So a `5-0 Positive Recommendation` and a `5-0 Approved (Final Action)` are different decision types
on the same grid — don't collapse them. The `outcome`/type normalization lives **alongside** in
`motions_std.csv`; `result` and the numeric tally are never overwritten.

## Case numbers — the land-use key
PC land-use motions cite case numbers **`YYYY-NNNN-TYPE`** — **184 distinct** in the motion text —
with type suffixes `USE` (conditional/permitted use), `SUB` (subdivision), `MA` (map amendment /
rezone), `VAR` (variance), `SP` (site plan), etc. These are a potentially exact within-body key.
(The db currently resolves applications by `singleton`/`name`, not by the case number — a
case-number tier is a natural future upgrade; see `db/SCHEMA.md`.)

## Roster (commissioners, appointed not elected)
Long-tenure: **Squire, Fowler, Ogden, Nixon** (2020/2021 → 2026). Others across eras: Hawker, Tonks,
Bingham, Player, Gundersen, Van Hoff (early); Shirey (2022+), Fidler (2023+), Shah (2024–2025),
Green, Adams (2024+), Best (2026). No mayor; the Chair/Vice-Chair vote like any member (denominator
derived empirically per meeting). Resolve by surname against `roster.csv` — note `Commissioner Green`
here is a **different person** from `Councilmember Green` on the Council.

## Known gaps (faithful, logged — NOT stubbed)
`minutes_unrecovered.csv`: **2026-06-11 / 2026-06-25 / 2026-07-09** (too recent — minutes not yet
adopted, `pending_adoption`) — the only rows left. **2020-12-10** & **2024-10-10** (the broken
~299-byte Granicus stubs) were RECOVERED from Utah Public Notice and promoted 2026-07-16
(`source=pmn`, `provenance=pmn_minutes`); the former **2024-03-14** row was STALE (that doc has
been in the index all along — `minutes/2024/2024-03-11/2024-03-14_planning-commission.md`) and was
removed in the same pass (see `VERIFICATION.md` addendum). Every indexed PC meeting carries ≥1
motion (0 vote-less PC meetings).

### The promoted 2020-12-10 COVID-era doc (source quirks, kept verbatim)
The 2020-12-10 electronic meeting uses a one-off block-list vote form (`Vote: AYE: <full names>` /
`NAY: Members: none` / `Absent: None`) plus `Moved by: X   Seconded by: Y` summary lines — the
extractor was extended additively for both (grep-verified absent from every other doc; **zero-diff
proven over the 141 audited docs**). Its vote blocks name **SIX** ayes (incl. seated Alternate
Fowler) while the prose prints "passed with a 5 to 0 vote" — both source facts; the named roll is
kept (result `6-0`), the printed-tally discrepancy is a preserved source contradiction. The
"passed with a N to M vote" tally phrasing itself was NOT parsed corpus-wide until the 2026-07-17
narrative-era recovery below.

## 2026-07-17 — 2020-21 narrative-era vote recovery (extraction follow-up)
The audited **2020-01 → 2021-10** PC minutes record roll-call outcomes in a NARRATIVE grammar the
grid-oriented parser and the primary `NARR_VOTE_RE` (which needs a quoted `"Aye"`/`"No"`) did not
see. Three additive grammars are now captured on a **recovery path** in `extract_votes.py`
(`parse_narrative_recovery`), **gated to `year <= 2021`** and run **only when the primary narrative
parse found NO attribution** — so every already-named motion (and the entire 2022+ grid era) is
byte-identical:
1. **Named in-favor list** — `Commissioners Hawker, Player, Ogden and VanHoff voting in favor of the
   motion.` → ayes. (A bare `Commissioners voting in favor` with no name captures nothing.)
2. **Named dissent** — `Commissioner Squire voted in opposition to the motion.` / `voting nay` /
   `voted no`. Plus a lowercase-tolerant `voted "nay"` variant (`NARR_VOTE_CI_RE`, e.g. Player
   2020-09-03) that the case-sensitive primary regex missed.
3. **Oriented item tally** — `This item passed with a 4 to 1 vote.` / `item passed with a vote of
   3 to 2.` / `The item did not pass with a 2 to 3 vote.` → tally + Pass/Fail. Also recovers the
   already-present-but-discarded `voting N-M in favor` tally (previously dropped when no names).

**The named roll is authoritative:** the item tally only supplies the numeric outcome — it never
invents or overrides a named voter (cf. **2020-04-02 m9**, where a `5 to 0` boilerplate line sits
over a truthful named 4-1; that motion is untouched and still reads 4-1). Per the sandy/magna
precedent, a named dissenter over an **unnamed majority** is honest data with
`names_recorded=False` (the in-favor list left blank by the clerk) — e.g. **2020-07-23 m4** (Van
Hoff Nay / 4-1) and **2020-09-03 m4,m5** (Player Nay / 4-1). Name normalization was extended for
the narrative full-name lists: `VanHoff` (unspaced) and `Von Hoff` (OCR/typo) both fold to the
canonical `Van Hoff`.

**The recovered hidden dissent (the spec ground-truth), 2021-02-25 m3** — Van Hoff moved / Hawker
seconded, `Application SPR-1126-2021` (Christensen Office Building Phase Two amended site plan).
Source: *"A roll call vote was taken with Commissioners Hawker, Player, Ogden and VanHoff voting in
favor of the motion. Commissioner Squire voted in opposition to the motion. This item passed with a
4 to 1 vote."* Now `4-1 Approved (Final Action)`, aye = Hawker/Player/Ogden/Van Hoff, **nay =
Squire**, `names_recorded=True`. Was `Approved (Final Action) (voice/tally-only)` (dissent invisible).

**Diff (audited, expected-rows-only):** 911 motions unchanged (none added/removed); no new member
names; **90 motions changed, all in 2020-01→2021-10** — **81 result-string-only** (tally-only →
oriented `N-M`, e.g. many unanimous `5-0`/`4-0`) and **9 with new named rows** (2020-07-23 m4;
2020-09-03 m4,m5; 2020-09-10 m3 [3-1]; 2021-02-25 m3 [the 4-1], m4,m5,m6; 2021-05-13 m4 [4-1]).
Net **+23 rows / +32 named** (4,301→4,324 / 4,082→4,114). `validate_votes.py` **PASS**; the
tally-vs-named mismatch set is the **same 7** pre-existing source contradictions as before (zero
new). `scripts/validate_city.py` 0 FAIL. Backup:
`_backups/2026-07-17-extraction-followups/draper/planning_commission/`.

**Derived-chain rebuild completed 2026-07-19** (the step deferred above). Ran `db/build_db.py`
→ `db/build_referrals.py` → `build_weeks.py` → `scripts/normalize_motions.py draper`; the
extractor re-ran byte-identical (determinism confirmed), 2022+ rows proven byte-stable vs the
pre-recovery backup, and all 9 named-row changes were re-source-verified (incl. 2021-02-25 m3
Squire 4-1). `scripts/validate_city.py` now **0 FAIL** with `h.db` **reconciling exactly (+0)** —
the former +32 delta is closed. PC contested (named dissent) 214 → **220**. Backup:
`_backups/2026-07-19-lm-wave/draper/`.
