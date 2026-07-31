# Remediation — summit_county land_use (2026-07-25)

Driving audit: `_audits/2026-07-25/report.md` defect **F2**. Scope set by owner: **published
prose only** (option A). Read-only sources; fixes at the extractor layer.

## Premise correction (found during step-2 source verification)

The audit reported "127 of 130 retained Granicus HTMLs carry full `AYES:` roll blocks; 0 of
393 markdown contain them" and framed it as a straightforward parse of retained source.
**All 545 of those blocks are inside HTML comments** (`<!-- <div>Moved by: …`) that Granicus
never renders. The original converter stripped comments — correct behavior, not a bug.

Evidence gathered before deciding:
- 545/545 `AYES` occurrences are comment-enclosed; **0 rendered**.
- Paired structurally by document order, **520/520 blocks agree exactly with the published
  prose tally** (25 further blocks are empty templates, excluded). The hidden data is real,
  not fabricated.
- **All 25 divided motions already name their dissenter in the rendered text** — the hidden
  blocks add **0** dissent attribution, only aye-rosters on unanimous motions.

**Owner ruling 2026-07-25: recover from published prose only.** The 3,001 comment-hidden
named positions are NOT ingested. Rationale: they add no contested signal, and the county
did not publish them. Logged in TODO.md so this is not re-discovered as a "gap."

## Defects to fix (all verified at source)

| # | Defect | Count | Evidence |
|---|---|---|---|
| **S-1** | Divided motions whose dissent IS named in published prose but uncaptured | 29 | `motions_tally.csv` `no>0 AND names_recorded=false` |
| **S-2** | Source says `MOTION FAILED` but repo stores `result=Pass` | 3 | 2016-02-18 m3, m5; 2020-06-23 m1 |
| **S-3** | Tally stored prevailing-side-first, inverting `yes`/`no` | 3 (same rows) | 2016-02-18 m3/m5 source names 3 approving / 4 opposed under "(4-3)"; 2020-06-23 poll = 1 Yea / 6 Nay under "(6-1)" |
| **S-4** | Three docs assert an unliftable named-vote ceiling | 3 files | `summit_county/CLAUDE.md:43-46`, `land_use/CLAUDE.md:44-47`, `land_use/build_votes.py:3` |

## The three uncaptured prose grammars

1. **2015–2016 eastern, wrapped + dotted-leader** —
   `• MOTION FAILED (3-4) Chair Ure, Commissioner Wharton, Commissioner Hanson,`
   `,……..…………………………    Commissioner Clyde voted against.`
   Names wrap across lines separated by dotted leaders.
2. **2016 two-sided** — `MOTION FAILED (4-3) Commissioners Willoughby, Commissioner Vernon,
   and Chair Ure voted in approval  Commissioners Henrie, … opposed.` Both sides named;
   **this is where the tally is prevailing-side-first** (4 = the opposed side).
3. **2020 snyderville roll-call grid** — a two-column `Commissioner X- Nay   Commissioner Y- Yea`
   poll, **interrupted by a running page header**, terminated by `• MOTION FAILED (6-1)`.

## Discipline

Backups → `_backups/2026-07-25-summit-pc/`. Fix in `land_use/build_votes.py`, regenerate,
prove the diff is exactly the expected rows (multiset compare on all others), re-run
`screen_corpus.py` + `validate_entity.py`, then document in VERIFICATION.md + correct S-4.
