# Campaign-finance vision transcription — two methods

Scanned / handwritten CF filings that OCR can't reconcile are escalated to Claude vision to
transcribe their contribution/expenditure rows. There are **two interchangeable methods**. Both
produce the **same output** — a `vision/<sha1(index_path)[:8]>.json` cache that each city's
`build_finance.py` reads via its `rows_override_fn` — so switching between them needs **no build
code change**.

## DEFAULT (as of 2026-07-06): Read-tool method — bills to the Claude Code plan
Use the **`cf-vision-transcribe` skill** (`.claude/skills/cf-vision-transcribe/SKILL.md`). It launches
agents that render pages with `pdftoppm` and view them with the **`Read` tool** — inference runs on the
**Claude Code allotment**, NOT the API credit balance. Chunked to keep image context bounded.

  Invoke: the skill, with `city` (+ optional filing list). It writes the `vision/*.json` caches, then
  rebuilds + validates + regenerates `cycle_totals`.

**Why this is the default:** the API credit balance was exhausted 2026-07-06 during the West Jordan
2021 backfill (~$25 cumulative vision spend across the 12-city build). Owner directive: use the
Claude-Code-allotment method until further notice.

## FALLBACK: API method — bills to the ANTHROPIC_API_KEY credit balance
The per-city **`<city>_city_council/campaign_finance/<city>_vision_extract.py`** scripts (modeled on
SLC's `public_comments/vision_extract.py`) load `ANTHROPIC_API_KEY` from `.env` and call the Anthropic
**Messages / Message Batches API** (`claude-sonnet-5`). Faster + more parallel than Read for large sets,
but **costs API credit**. **These scripts are retained, not deleted** — to switch back, just run the
per-city `vision_extract.py` (it writes the identical `vision/*.json` cache) instead of the skill.

  Trade-offs: API = fast/parallel/paid; Read = free-on-plan/context-bounded/serial. Same model, same
  transcription discipline (transcribe exactly, mark illegible, never infer), same cache output.

## Currently queued for (re)transcription (do via the Read method)
- **West Jordan** — 8 multi-report 2021 bundles left as PARTIAL undercounts (each PDF bundles interim +
  final; only one report captured before credit ran out).
- **Ogden** — 6 large scanned filings at the OCR floor (Castillo-2019 53pp, Graf, Van Wagoner, Andersen,
  Myers, Choberka).
- **West Valley** — 4 large scans at the OCR floor (Steve Buhler 2021 ×3, Amitonu Amosa 2025).
- **SLC** — campaign finance is a separate portal-blocked gap (no filings harvested yet; not a vision task).
