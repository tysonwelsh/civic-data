#!/usr/bin/env python3
"""Measure what a real question costs — the evidence a spend ceiling is set from.

Runs a set of journalist questions through the live agent loop, one at a time,
and reports the distribution of cost, turns, tool calls and latency. Every run
also lands in logs/chat.jsonl via chat.log_question, so a later sweep adds to
the record rather than replacing it.

THIS SPENDS REAL MONEY. Nothing else in interface_prototype/ does. It prints an
estimate and waits for confirmation before the first request.

    python3 interface_prototype/cost_sweep.py --dry-run   # show the set, spend nothing
    python3 interface_prototype/cost_sweep.py             # run it, with a prompt
    python3 interface_prototype/cost_sweep.py -n 5        # first five only
    python3 interface_prototype/cost_sweep.py --yes       # no prompt (scripted use)

The question set is deliberately mixed: cheap lookups that should resolve in one
or two tool calls, cross-entity comparisons that need several, and questions
answerable ONLY from the repo's own documentation — the last group is the test
of whether the model reaches for grep_repo instead of forcing an FTS query.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interface_prototype.agent import chat, config  # noqa: E402


# (label, question) — `expects` is a hint for the reader, not an assertion.
QUESTIONS: list[tuple[str, str]] = [
    ("lookup",      "How many motions has Nephi's city council recorded?"),
    ("lookup",      "Who is on the Millcreek city council right now?"),
    ("lookup",      "Which Utah cities in this database have no published public comments?"),
    ("thematic",    "What have Utah cities said about accessory dwelling units since 2023?"),
    ("thematic",    "Find discussions of density bonuses in planning commission minutes."),
    ("cross",       "Which city council most often overrides its planning commission?"),
    ("cross",       "Compare contested vote rates across Salt Lake County cities."),
    ("cross",       "Did any council approve something its planning commission recommended denying in 2024?"),
    ("money",       "Who were the largest campaign donors to Murray city council candidates?"),
    ("money",       "Is there any relationship between campaign contributions and land-use votes in Sandy?"),
    ("repo-docs",   "What does this repository say about Nephi's coverage gaps and why they exist?"),
    ("repo-docs",   "Which entities have known unrecovered minutes, and how is that recorded?"),
    ("repo-docs",   "How was the campaign finance data for Salt Lake County actually assembled?"),
    ("trap",        "What was the total campaign spending across every county?"),
    ("trap",        "How did state legislators vote compared to their city councils?"),
]


def run_one(label: str, question: str) -> dict:
    """Drive the agent loop to completion, returning the `done` record."""
    started = time.monotonic()
    done: dict = {}
    tools_used: list[str] = []
    text_chars = 0
    error = None

    for event in chat.run(question):
        kind = event.get("type")
        if kind == "tool_use":
            tools_used.append(event.get("name", "?"))
        elif kind == "text":
            text_chars += len(event.get("text", "") or "")
        elif kind == "error":
            error = event.get("message")
        elif kind == "refusal":
            error = "refusal"
        elif kind == "done":
            done = event

    return {
        "label": label,
        "question": question,
        "cost_usd": done.get("cost_usd", 0.0),
        "turns": done.get("turns", 0),
        "tools": tools_used,
        "tool_calls": len(tools_used),
        "answer_chars": text_chars,
        "elapsed_s": done.get("elapsed_s", round(time.monotonic() - started, 1)),
        "cache_hit": done.get("cache_hit"),
        "error": error,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("-n", type=int, default=0, help="run only the first N questions")
    ap.add_argument("--dry-run", action="store_true", help="list the set and exit")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = ap.parse_args()

    questions = QUESTIONS[: args.n] if args.n else QUESTIONS

    if args.dry_run:
        print(f"{len(questions)} questions, nothing will be sent:\n")
        for label, q in questions:
            print(f"  [{label:9}] {q}")
        return 0

    ready = chat.credentials_status()
    if not ready.get("ready"):
        print(f"no usable credential: {ready.get('reason')}", file=sys.stderr)
        return 1

    print(f"\ncivic-data cost sweep — {len(questions)} questions")
    print(f"  model   {chat.MODEL}  effort={chat.EFFORT}  max_turns={chat.MAX_TURNS}")
    print(f"  log     {config.CHAT_LOG}")
    print(f"\n  THIS SPENDS REAL MONEY. A rough ceiling at {chat.MAX_TURNS} turns is a "
          f"few dollars per\n  question; a typical one should land far below that. "
          f"That gap is the point\n  of measuring.\n")
    if not args.yes:
        if input("  proceed? [y/N] ").strip().lower() not in ("y", "yes"):
            print("  nothing sent.")
            return 0
    print()

    results = []
    for i, (label, question) in enumerate(questions, 1):
        print(f"  [{i:>2}/{len(questions)}] {label:9} {question[:58]:<58} ", end="", flush=True)
        try:
            row = run_one(label, question)
        except Exception as exc:                     # a bad run must not lose the sweep
            print(f"ERROR {type(exc).__name__}")
            results.append({"label": label, "question": question, "cost_usd": 0.0,
                            "turns": 0, "tools": [], "tool_calls": 0,
                            "elapsed_s": 0, "error": f"{type(exc).__name__}: {exc}"})
            continue
        flag = "  " if not row["error"] else " !"
        print(f"${row['cost_usd']:>6.3f} {row['turns']:>2}t {row['tool_calls']:>2}c "
              f"{row['elapsed_s']:>5.1f}s{flag}")
        results.append(row)

    costs = [r["cost_usd"] for r in results if r["cost_usd"]]
    if not costs:
        print("\n  no successful runs — nothing to summarise.")
        return 1

    total = sum(costs)
    print(f"\n  {'-' * 66}")
    print(f"  total ${total:.2f} over {len(costs)} questions")
    print(f"  mean  ${statistics.mean(costs):.3f}   median ${statistics.median(costs):.3f}   "
          f"max ${max(costs):.3f}")
    print(f"  turns mean {statistics.mean([r['turns'] for r in results]):.1f}   "
          f"tool calls mean {statistics.mean([r['tool_calls'] for r in results]):.1f}")

    # Which tools actually got used — the routing question grep_repo raises.
    used: dict[str, int] = {}
    for r in results:
        for t in r["tools"]:
            used[t] = used.get(t, 0) + 1
    print("\n  tool usage: " + (", ".join(f"{k}×{v}" for k, v in
                                          sorted(used.items(), key=lambda kv: -kv[1])) or "none"))
    docs = [r for r in results if r["label"] == "repo-docs"]
    if docs:
        reached = sum(1 for r in docs if "grep_repo" in r["tools"])
        print(f"  repo-docs questions that reached for grep_repo: {reached}/{len(docs)}")

    print(f"\n  budget at $20–100/mo:")
    for cap in (20, 100):
        print(f"    ${cap:>3}/mo  ≈ {int(cap / statistics.mean(costs)):>5,} questions "
              f"({int(cap / statistics.mean(costs) / 30):>3}/day)")

    failed = [r for r in results if r["error"]]
    if failed:
        print(f"\n  {len(failed)} question(s) errored:")
        for r in failed:
            print(f"    [{r['label']}] {str(r['error'])[:80]}")

    out = config.LOG_DIR / "cost_sweep.json"
    out.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\n  per-question detail: {out}")
    print(f"  appended to:         {config.CHAT_LOG}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
