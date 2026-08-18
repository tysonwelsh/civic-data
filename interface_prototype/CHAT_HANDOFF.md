# CHAT HANDOFF — briefing for the session that builds the chat interface

Scoped to `interface_prototype/`. **This is not the repo's root `HANDOFF.md`** — that one
is the data-pipeline session banner and must not be overwritten by this work.

Written 2026-08-07. Owner: Tyson Welsh.

---

## Read in this order

1. **`interface_prototype/CHAT_PLAN.md`** — the design and the phased build. This is the spec.
2. **Root `CLAUDE.md`** — how the repo answers questions. The "Cross-city comparisons — the
   rules" section is the source of the agent's guardrails.
3. **`gov_db_SCHEMA.md`** — the federated schema, the views, the caveat table.
4. **`interface_prototype/README.md`** — conventions for this folder.
5. **`GOTCHAS.md`** — standing operational rules for the repo.

Skip `TODO.md` / `LEADS.md` / root `HANDOFF.md` unless the owner points you there; they
track data work, not this.

---

## What already exists in this folder

| File | State |
|---|---|
| `build_entity_tree.py` | **Working.** Measures an entity's on-disk tree → annotated JSON + HTML. Stdlib only. |
| `entity_tree.template.html` | **Working.** The tree renderer. Design language to match in `chat.html`. |
| `entity_tree.html` + `data/*.json` | Generated artifacts (south_jordan, slc, lehi, alta). |
| `CHAT_PLAN.md` | The spec for what you're building. |
| `README.md` | Folder conventions. |

Nothing of the chat interface is built yet. Phase 0 in the plan is the starting point.

---

## Environment

- **Python 3.11** (anaconda). Core pipeline is deliberately stdlib-only; `anthropic` is
  already in `requirements.txt` (used by SLC's extraction scripts).
- **`ANTHROPIC_API_KEY` is not yet configured for this work.** The owner will set it up.
  Phase 0 requires no key at all — build and verify the whole data layer first.
  If the key is unset when you reach Phase 1, run `ant auth status` before asking for one;
  an OAuth profile may already be active, in which case a bare `Anthropic()` just works.
- **`gov.db`** is at the repo root, 1.6 GB. **Always open it `file:gov.db?mode=ro`** — the
  sqlite3 CLI creates files on open, and this database is expensive to rebuild.
- The database is DERIVED. Never write to it. Never write to any dataset from this layer.

---

## Facts you'll need, verified against the live database on 2026-08-07

Do not trust counts printed in the markdown docs — they lag the live build. Read
`build_info`, or query.

```
entity 44 · motion 78,561 · vote 247,459 · meeting 12,574 · person 1,638
document 54,686 · comment 14,202 · ordinance 7,550
election_race 810 · election_result 5,820
cf_filing 3,810 · cf_contribution 40,115 · cf_expenditure 28,274 · cf_cycle 805
regional_project 5,717 · projection 10,952 · term 641 · motion_std 77,353
caveat 104 · fts_minutes 14,696 · fts_packet 13,725
```

**Path resolution** — `fts_minutes.path` and `document.text_path` are entity-relative with
a tier-dependent prefix:

```sql
CASE WHEN gov_level='city' THEN city || '_city_council/' ELSE city || '/' END || path
```

`fts_minutes` carries no `gov_level` column — derive it via `JOIN entity e ON e.slug = city`
using `e.level`. Use `text_path` (99.96% resolvable), not `path` (34% points into the
gitignored `raw/` tree). The `search_text` tool should resolve this so the model never has to.

---

## The traps the agent must not fall into

These are why the guarded-SQL-plus-caveat-injection design exists. All are documented in
the root `CLAUDE.md`; all produce confident wrong answers if missed.

- Aggregating raw `result` / `motion_type` strings across entities — each city has its own
  labels (8–33 distinct result strings).
- Summing `cf_filing` dollar columns — filings overlap (interim + summary). `cf_cycle` is
  the only sanctioned per-candidate total, and it is **city-only**.
- Applying the city-tier `provenance='minutes'` filter across tiers — silently drops ~84%
  of county motions, because `provenance` holds extractor names on the non-city tier.
- Reading `disposition` as if it implied `outcome` — they're orthogonal.
- Treating empty itemized campaign finance as "no donors" — it means NOT TRANSCRIBED.
- Surname-joining state legislators to municipal officials — disjoint person populations.
- Reading an MPO's empty vote table as a gap — it's a source property.
- Taking RCV winners from tallies instead of `election_race`.
- Comparing dissent rates across cities without the recording-ceiling caveats (Nephi is
  ~80% tally-only; West Jordan's PC names only dissenters; Orem records Aye/Nay only).

---

## Working agreements

- **Read-only, always.** This layer never writes to a dataset, never mutates `gov.db`.
- **Measured over asserted.** If a number appears in the UI, a query produced it. No
  hardcoded headline totals — they drift between builds.
- **Assemble the system prompt from repo docs**, don't hand-copy the schema. A copied
  blurb goes stale within two builds and the agent then reasons from stale docs.
- **Match `entity_tree.html`'s design language** in `chat.html` — same CSS tokens, same
  theme-awareness (light/dark/system), same restraint.
- **Verify before claiming done.** Phase gates are in `CHAT_PLAN.md` §4; each is a
  runnable check, not a vibe.
- **Owner approves agent launches.** If any part of this benefits from subagents, present
  the plan — count, model, effort — before running.
- **Backlog entries are hypotheses.** Anything filed in this repo as a defect is a past
  session's guess; verify at the source before acting on it.

---

## Suggested first move

Phase 0, in this order, since each piece is testable without spending a cent:

1. `agent/guard.py` — read-only SQL execution with the caps. Unit-test the rejections.
2. `agent/caveats.py` — result-set → applicable caveat rows. Test with a `nephi` query
   and confirm `tally-only-partial` comes back unbidden.
3. `agent/tools.py` — the six tools over those two.
4. `server.py` — stdlib `http.server` exposing them; verify each with `curl`.

Then stop and show the owner before starting Phase 1, since that's where API spend begins.
