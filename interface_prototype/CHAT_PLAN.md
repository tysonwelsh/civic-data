# Chat interface — design & build plan

**Audience: a working journalist.** Not a researcher who will read SQL, and not a
council member who wants a dashboard. Someone on deadline who needs a fact, needs to
know whether they can print it, and needs to find the document it came from.

That single decision drives everything below. Written 2026-08-07.

---

## 1. What a journalist needs that a researcher doesn't

| Need | What it forces in the design |
|---|---|
| **The answer, not the query** | Prose first. SQL exists but lives behind a disclosure, not in the reply. |
| **Sourcing they can cite** | Every factual claim carries entity + date + document. "Herriman City Council, 2024-03-13, minutes" — not "the database says". |
| **"Can I publish this?"** | The applicable caveat rows surface *with* the answer whenever they change how the number should be read. Confidence is stated, not implied. |
| **They don't know the schema** | No entity slugs, no table names, no `gov_level` in the reply. "Salt Lake" has to disambiguate itself between the city and the county. |
| **Speed** | Streaming, so text appears while tools are still running. |
| **A quote from the actual minutes** | The agent must be able to open primary text, not paraphrase a row. This is the `read_document` tool, and it matters more here than for any other audience. |

**The thing that must never happen:** a confident, clean-looking answer that rests on a
layer the source never published. Nephi's 2% dissent rate. South Jordan's zero comments.
A county's empty itemized campaign finance. Each of those is a *recording ceiling*, and a
journalist who prints it as a finding has been actively misled by the tool.

---

## 2. Architecture

**Guarded SQL with harness-injected caveats.** Claude writes read-only SQL; the executor
— not the model — is responsible for safety and for honesty.

```
chat.html  ──HTTP──>  server.py  ──>  agent/tools.py  ──>  guard.py ──> gov.db (mode=ro)
                                              │
                                              └──> caveats.py  (attaches caveat rows
                                                                 to every result)
```

The page never touches the filesystem; it calls `/api/*`. Local now, hosted later is
then a config change, not a rewrite.

### 2.1 The mechanism that makes this defensible

After any query runs, the executor scans the result set for `city` and `dataset` values,
looks up matching rows in `gov.db`'s `caveat` table (104 rows, `'*'` wildcards included),
and appends them to the tool result. **Claude cannot receive data without also receiving
its limits.**

This is the difference between "the model remembered to mention the caveat" and "the
caveat was structurally impossible to omit." It converts the `caveat` table from
documentation into a runtime component, and it is the single most important thing in
this build.

Corollary: prefer the caveat-aware views (`v_contested_all`, `v_member_record_all`,
`v_landuse_outcomes`, `v_coverage`) over raw tables — they already carry their own
`*_caveats` columns, so the injection is belt-and-braces rather than the only guard.

### 2.2 Guard rules (`agent/guard.py`)

- Connection opened `file:gov.db?mode=ro`.
- One statement only; must start `SELECT` or `WITH`. Reject `PRAGMA`, `ATTACH`,
  `CREATE`, and anything else outright.
- `LIMIT` injected when absent (default 200).
- Row and byte caps on the result; truncation reported to the model explicitly so it
  knows the answer is partial.
- Statement timeout via `sqlite3.set_progress_handler`.
- Every query logged with its result-row count — this is the audit trail a journalist
  needs if an editor asks where a number came from.

### 2.3 Tool surface (`agent/tools.py`)

| Tool | Why it exists |
|---|---|
| `run_sql(sql)` | The general capability. Guarded + caveat-injected per above. |
| `search_text(query, entity?, dataset?, date_from?, date_to?)` | FTS5 over `fts_minutes` / `fts_packet` / `fts_comment` / `fts_ordinance`, returning `snippet()` passages and **resolved** paths. Hides the tier-dependent path prefix so the model never has to reconstruct it. |
| `read_document(text_path)` | Opens a minutes / statute / advisory-opinion text file so the agent can quote the primary source. Path-confined to the repo root. |
| `get_schema(tables?)` | DDL on demand, so the system prompt stays small and cheap. |
| `list_coverage(entity?)` | `v_coverage` rows: what exists, what's deferred by design, where the floors are. The honest-gap answer. |
| `resolve_entity(name)` | "Salt Lake" → offers `slc` (city) and `salt_lake_county`. "Park City" → `park_city`, noting it sits in two counties. Prevents the most likely silent wrong answer in the whole system. |

### 2.4 System prompt (`agent/context.py`)

**Assembled from the repo at startup, never hand-copied.** Sources: `gov_db_SCHEMA.md`,
the cardinal rules and query rules from the root `CLAUDE.md`, `registry/entities.csv`,
and the distinct `caveat.code` values. A hand-written schema blurb drifts from the
database within two builds and then the agent reasons from stale docs.

Must contain, in the agent's own operating instructions:

- Never aggregate raw `result` / `motion_type` strings across entities.
- Never sum `cf_filing` dollar columns; `cf_cycle` is the only sanctioned per-candidate
  total, and it is **city-only**.
- `provenance` has two vocabularies by tier — the city-tier `provenance='minutes'` filter
  silently drops ~84% of county motions.
- `disposition` and `outcome` are orthogonal; compose at query time.
- Empty itemized campaign finance means NOT TRANSCRIBED, never "no donors".
- State legislators are a disjoint person population — never surname-join to municipal
  officials.
- MPO vote tables are empty **by source**, not by omission.
- RCV cities: take winners from `election_race`, not from tallies.

Plus the journalist-facing output contract: answer first, cite entity + date + document,
surface material caveats in the reply itself rather than only in the evidence drawer, and
say plainly when the data cannot support the question.

---

## 3. API decisions

Verified against the current API reference, 2026-08-07.

| Decision | Value | Why |
|---|---|---|
| Model | `claude-opus-5` | Default tier. $5/$25 per MTok. |
| Thinking | Adaptive — **on by default**; do not pass `budget_tokens` (400s) | Opus 5 thinks unless told otherwise. |
| Effort | `output_config={"effort": "medium"}` to start, then sweep | `low`/`medium` are unusually strong on this model; sweep before settling. |
| Streaming | `client.messages.stream()` → SSE to the browser | Required for perceived speed; also avoids HTTP timeouts. |
| `max_tokens` | 16000 streaming | Thinking + text share this cap. |
| Sampling params | **None** | `temperature` / `top_p` / `top_k` are rejected with a 400. |
| Caching | `cache_control: {"type": "ephemeral"}` on the last system block | Opus 5's minimum cacheable prefix is 512 tokens, so even a modest system prompt caches. Keep the prompt byte-stable — no timestamps, no per-request IDs. |
| Refusals | Check `stop_reason == "refusal"` before reading `content`; opt into `fallbacks: "default"` with beta `server-side-fallback-2026-07-01` | Opus 5 carries elevated safeguards. Cheap insurance. |
| Loop | Manual tool-use loop | The SDK tool runner is beta and we want SSE control. Revisit later. |

**Cost, roughly.** With the system prompt cached, a typical question runs a few cents —
call it **5–15¢**, dominated by output plus adaptive-thinking tokens rather than input.
Verify with `usage.cache_read_input_tokens` on the second request; if it's zero, a silent
cache invalidator is in the prompt.

**Prompt-tuning specific to Opus 5** (these are real, documented behaviours, not
speculation):

- It writes long by default. Include an explicit conciseness instruction — `effort` does
  **not** reliably shorten visible output.
- It verifies its own work. Do **not** add "double-check your answer" scaffolding; that
  causes over-verification with no accuracy gain.
- It can expand scope. Include the scope-discipline instruction.
- It narrates self-corrections at length. Include the corrections instruction.

---

## 4. Build phases

### Phase 0 — data layer, no API key required
`server.py` (stdlib `http.server`), `guard.py`, `caveats.py`, `tools.py`.
Endpoints: `/api/health`, `/api/query`, `/api/search`, `/api/schema`, `/api/coverage`,
`/api/document`, `/api/entity`.

*Done when:* every tool is exercisable with `curl`; a query touching `nephi` returns its
`tally-only-partial` caveat without anyone asking for it; a `DROP`/`ATTACH`/multi-statement
attempt is rejected; a 200-row cap holds. **Zero API spend to here.**

### Phase 1 — the agent loop
`context.py` (prompt assembled from repo docs), the tool-use loop, `/api/chat` over SSE.

*Done when:* five journalist-shaped questions answer end to end with sourcing, and one
question the data *cannot* answer gets an honest refusal instead of a fabrication. Log
token usage per turn.

### Phase 2 — the journalist UI
`chat.html`, matching `entity_tree.html`'s design language (same tokens, same
theme-awareness, same restraint).

- Streaming answer with inline citations
- **Evidence drawer**, collapsed: the SQL, the rows, the caveats, links to source docs
- Caveat banner when an answer rests on a limited layer
- Entity disambiguation chips when a name is ambiguous
- Starter questions, journalist-shaped
- Copy-for-notes export

*Done when:* someone who has never seen the repo can ask a question, get an answer, and
find the underlying document in two clicks.

### Phase 3 — trust features
"Check this" re-runs a claim and opens the primary document. Per-answer confidence.
Session transcript export for fact-checking.

---

## 5. Deliberately out of scope for the prototype

Auth, multi-user sessions, rate limiting, a hosted deployment, write access of any kind,
and any change to the data pipeline. This layer is **read-only against `gov.db`** and
touches no dataset.

---

## 6. Open questions for the owner

1. **Cost ceiling** — a per-session token budget, or run uncapped for now?
2. **Failure posture** — when the data can't support a question, should the agent
   refuse plainly, or answer with the ceiling attached? (Current plan: answer with the
   ceiling when one exists, refuse when the layer is absent entirely.)
3. **Hosting horizon** — does the eventual public version serve `gov.db` (1.6 GB) or
   `gov-sample.db` (21 MB)? Affects nothing in the prototype, but shapes Phase 3.
