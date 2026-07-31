# Public-comment availability — Midvale City

**Verdict: SUBMIT-ONLY / HONEST-EMPTY.** Midvale publishes no standalone written-public-comment
archive. `all_comments_clean.csv` is intentionally header-only.

## What was checked (2026-07-12)
- **Revize city site** (`midvale.utah.gov`) — Recorder's Office and Council/Planning pages:
  agendas, minutes, packets, and presentations are posted, but **no eComment / public-comment /
  correspondence document type** exists in the Document Center.
- **Meeting minutes** — carry an inline **"Public Comments"** heading that names speakers and
  paraphrases their remarks. These are **clerk speaker notes inside the meeting record**, not a
  published written-comment submission set, and are not extracted into the comments table
  (doing so would invent structure and attribute paraphrase as verbatim comment).
- **Agenda packets** — no embedded written-comment compilation (unlike Provo's letters-in-packet
  model).

## Why header-only, not absent
Per the collection's cardinal rule (honest gaps are data), the empty-but-present
`all_comments_clean.csv` with the full standard header is the deliberate signal that Midvale
was audited and found to publish none — distinct from a city not yet processed.

## Re-check triggers
Re-run this audit if Midvale adopts an eComment/portal (e.g. a CivicPlus/Granicus comment
widget) or begins posting correspondence packets. If found, populate the CSV to schema and
rebuild `weeks/`.
