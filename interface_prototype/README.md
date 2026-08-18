# interface_prototype

Browser-facing work: the exploration interface, plus the explanatory and pitch material
that goes with it. Everything here **reads the repo as it exists locally** but is written
as if the data were served — so the same pages can point at a hosted `gov.db` later
without being rewritten.

Nothing in this folder is part of the data pipeline. It never writes to any dataset; it
only reads the flat files, `registry/entities.csv`, and `gov.db` in read-only mode.

## What's here

| file | what it is |
|---|---|
| `build_entity_tree.py` | Measures an entity's on-disk tree and emits annotated JSON + the HTML graphic. Stdlib only. |
| `entity_tree.template.html` | The tree renderer. Data is inlined at build time so the page opens straight from `file://`. |
| `entity_tree.html` | **Generated.** The current build — open this in a browser. |
| `data/<slug>_tree.json` | **Generated.** One measured tree per entity; reusable by later interface pieces. |
| `CHAT_PLAN.md` | The chat interface's design, API decisions, and phased build. |
| `CHAT_HANDOFF.md` | Briefing for the session building it: environment, live db facts, the traps. |
| `agent/` | **The read-only data layer** (Phase 0) **plus the agent loop** (Phase 1). Stdlib only except `anthropic`. |
| `server.py` | Stdlib `http.server` exposing that layer over `/api/*`, and serving this folder's pages. |
| `chat.html` | **The journalist interface** — ask a question in plain language. Served at `/`. |
| `console.html` | **The console** — a browser face for the data layer alone, no model, no spend. At `/console.html`. |
| `agent/gate.py` | **The exposure layer**: origin, token, rate limit, spend ceiling. Off unless `CIVIC_SERVICE_SECRET` is set. |
| `cost_sweep.py` | Runs a mixed question set and reports the cost distribution. **The only thing here that spends money.** |
| `deploy/` | systemd unit, Caddyfile, `sync.sh`, the PHP token minter, and `DEPLOY.md`. |
| `verify_phase0.sh` | The Phase 0 gate: 46 curl checks against a running server. |
| `verify_console.py` | Contract check: every field `console.html` reads, asserted on the live API. |
| `verify_phase1.py` | The Phase 1 gate: 70 checks including the whole agent loop against a stub model. No spend. |
| `verify_gate.py` | 30 checks on the exposure layer — auth, origin, rate, budget, rotation. No spend. |
| `verify_token_parity.php` | 7 checks that PHP and Python sign tokens byte-identically. Needs `php`. |

## The data layer (`agent/`, Phase 0)

Read-only against `gov.db`, no API key, no model. Four modules:

| module | what it does |
|---|---|
| `config.py` | Paths and caps — row/byte/timeout ceilings in one place. |
| `guard.py` | Guarded SQL. Four independent layers: `mode=ro`, a SQLite authorizer, a textual prefilter, and result caps. Logs every query with its row count. |
| `caveats.py` | Scans the SQL *and* the returned rows for entity/dataset signals and attaches the matching `caveat` rows. Also raises query-shape notes for the traps no caveat row covers. |
| `tools.py` | The seven tools: `run_sql`, `search_text`, `read_document`, `get_schema`, `list_coverage`, `resolve_entity`, `grep_repo`. |

```sh
python3 interface_prototype/server.py            # 127.0.0.1:8787 — chat at /, console at /console.html
bash    interface_prototype/verify_phase0.sh     # 39 gates, exits non-zero on failure
python3 interface_prototype/verify_console.py    # 26 page↔API contract checks
python3 interface_prototype/verify_phase1.py     # 61 agent-loop checks, no API spend
```

The console has a tab per tool — SQL, search, grep, entity resolution, coverage, a
document reader, schema — and renders the caveats beside every result rather
than behind a disclosure. It needs no API key and spends nothing, so it stays
the way to browse the data layer directly.

### `grep_repo` — the layer FTS does not index

`search_text` sweeps what governments *published*: 14,696 minutes documents and
their sibling corpora. It does not index what the **repository** says about its
own coverage — `CLAUDE.md`, `TODO.md`, `LEADS.md`, `COVERAGE.md`,
`AVAILABILITY.md`, the per-dataset `index.csv` provenance manifests, the build
scripts. Those are 63,733 committed text files (~2 GB), and before this tool
they were reachable only by a path you already knew.

Two engines behind one contract. **ripgrep** when a real `rg` binary is on PATH —
what a deployment should install, because its matcher is a finite automaton and
so a hostile pattern cannot backtrack. The **stdlib** fallback is correct but
slower: a measured repo-wide literal sweep runs ~16s against ripgrep's ~2s.
Both obey `GREP_DEADLINE_MS` and report *why* a result stopped —
`truncation_reason` is `limit`, `deadline`, or `bytes`, never silence. **A
deadline-truncated sweep is a partial result, and absence in one is not
evidence of absence**; the payload carries a `hint` saying exactly that.

Scope with `path=` (an entity directory) and it returns in single-digit
milliseconds. Matched lines carry their entity's caveat rows, the same as every
other tool — a line quoted out of Nephi's docs arrives with Nephi's tally-only
ceiling attached.

Path confinement is shared with `read_document` through `tools._confine()`, so
the two cannot drift apart; the escape rules are asserted from both directions
in `verify_phase0.sh` and `verify_phase1.py`.

## The agent (`agent/context.py`, `agent/chat.py`, Phase 1)

`context.py` assembles the system prompt **from the repo at startup** —
`gov_db_SCHEMA.md`, the cardinal and cross-entity rules out of `CLAUDE.md`, the
entity registry, and the live `caveat.code` vocabulary. Nothing is hand-copied,
because a copied schema blurb drifts from the database within two builds. The
result is byte-stable so it caches.

`chat.py` is a manual tool-use loop over the six Phase 0 tools, streaming
Server-Sent Events to the page: text deltas, tool calls, tool results with their
caveats, and a closing usage/cost record. Model configuration is pinned in one
place at the top of the file.

**Requires `anthropic` ≥ 0.121** for native `output_config` and `fallbacks`;
older versions still work — the same fields go out through `extra_body`. It also
needs a credential: `ANTHROPIC_API_KEY`, or an `ant auth login` profile.
`GET /api/chat-status` reports exactly which of those is missing, and the page
disables the composer rather than failing mid-answer.

The point of `caveats.py` is that **Claude cannot receive data without also
receiving its limits**. A query counting Nephi's motions comes back with
Nephi's `tally-only` ceiling attached even though the result set has no `city`
column and nobody asked for it. That converts the `caveat` table from
documentation into a runtime component, and it is the load-bearing idea in the
whole interface — see `CHAT_PLAN.md` §2.1.

## Regenerating

```sh
python3 interface_prototype/build_entity_tree.py                 # slc (default)
python3 interface_prototype/build_entity_tree.py slc lehi alta   # named entities
python3 interface_prototype/build_entity_tree.py --all-cities    # all 31 cities
python3 interface_prototype/build_entity_tree.py --all           # every built entity
```

Every entity named in one run lands in a single `entity_tree.html` with a picker at the
top. A full-repo run takes a few seconds; the measured directory sizes come from a real
`os.walk`, so run it after any refresh if you want the numbers current.

## What the graphic is arguing

The tree is colour-coded by the **role a file plays**, not by its extension — because the
repo's central claim is about provenance discipline, and that claim is only visible when
you can see the layers apart:

- **canonical** — the primary record. City-faithful values are never overwritten.
- **derived** — regenerated by a script, never hand-edited (`db/`, `weeks/`, `motions_std.csv`).
- **override** — documented correction files. Fixes live *beside* the source, not on top of it.
- **gap** — things known to be missing, recorded as data (`minutes_unrecovered.csv`).
- **index** — provenance manifests: every file, its date, and where it came from.
- **code / doc / raw** — the pipeline, the documentation, and the uncommitted originals.

The panel at the bottom of the page prints that entity's rows from `gov.db`'s `caveat`
table — what its data *cannot* tell you — on the same footing as what it can.

## Conventions for anything added here

- Read-only against the repo. Open `gov.db` as `file:gov.db?mode=ro`.
- Measured numbers over asserted ones: if a figure appears on a page, a script counted it.
  Headline totals should come from `build_info` or a live query, never hardcoded — the
  published docs lag the live database between builds.
- Generated files are disposable and rebuildable from the committed generators.
