#!/usr/bin/env python3
"""Phase 1 gate — the agent loop, proven without spending anything.

The one thing that cannot be checked for free is whether Claude gives a *good*
answer. Everything else can: the tool schemas, the dispatch table, the system
prompt assembled from the repo, the tool-use loop, the caveat plumbing, the
usage accounting, and the SSE wire format.

So this drives the real :func:`agent.chat.run` against a **stub client** that
replays a scripted two-turn exchange — one tool call, then an answer. The loop,
the tool execution, the caveat attachment and the event stream are the genuine
code paths; only the model is fake.

    python3 interface_prototype/server.py &
    python3 interface_prototype/verify_phase1.py
"""

from __future__ import annotations

import json
import sys
import types
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interface_prototype.agent import chat, context, tools  # noqa: E402

BASE = "http://127.0.0.1:8787"
PASS, FAIL = 0, 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  \033[32mPASS\033[0m  {label:<52} {detail}")
    else:
        FAIL += 1
        print(f"  \033[31mFAIL\033[0m  {label:<52} {detail}")


print(f"\nPhase 1 gate — agent loop, no API spend\n")

# --------------------------------------------------------------------------
print("-- tool surface")
# --------------------------------------------------------------------------
names = [t["name"] for t in chat.TOOL_SCHEMAS]
check("seven tools defined", len(chat.TOOL_SCHEMAS) == 7, ", ".join(names))
check("every tool has a dispatch entry", set(names) == set(chat.DISPATCH),
      f"{len(chat.DISPATCH)} handlers")

wellformed = all(
    t.get("name") and len(t.get("description", "")) > 60
    and t.get("input_schema", {}).get("type") == "object"
    and isinstance(t["input_schema"].get("properties"), dict)
    for t in chat.TOOL_SCHEMAS
)
check("schemas well-formed with real descriptions", wellformed)

# Every tool must survive being called with its documented arguments.
probes = {
    "run_sql": {"sql": "SELECT COUNT(*) AS n FROM motion WHERE city='nephi'"},
    "search_text": {"query": '"accessory dwelling"', "limit": 2},
    "read_document": {"path": "CLAUDE.md", "max_chars": 200},
    "get_schema": {"tables": ["caveat"]},
    "list_coverage": {"entity": "nephi"},
    "resolve_entity": {"name": "Salt Lake"},
    "grep_repo": {"pattern": "tally-only", "path": "nephi_city_council", "limit": 3},
}
for name, args in probes.items():
    out = chat.DISPATCH[name](args)
    check(f"dispatch {name}", isinstance(out, dict) and "error" not in out,
          out.get("error", "ok"))

# grep_repo reaches the documentation layer no FTS corpus indexes, and is
# confined to the repo by the same helper read_document uses.
grep = chat.DISPATCH["grep_repo"]
hit = grep({"pattern": "Never fabricate", "glob": "CLAUDE.md", "limit": 5})
check("grep_repo finds repo docs FTS cannot", hit.get("match_count", 0) > 0,
      f"{hit.get('match_count')} lines in {hit.get('files_matched')} files "
      f"via {hit.get('engine')}")
check("grep_repo attaches entity caveats",
      any(m["entity"] for m in grep(
          {"pattern": "tally-only", "path": "nephi_city_council", "limit": 3}
      )["matches"]))
# Engine parity. ripgrep and the stdlib fallback must return the SAME matches,
# or a result silently depends on which machine ran it. This caught a real bug:
# ripgrep omits the filename when given a single explicit file, so `path=<file>`
# returned a confident zero under rg and 10 matches under stdlib.
if tools.ripgrep_path():
    parity_fail = []
    for pat, kw in (
        ("tally-only", {"path": "nephi_city_council"}),
        ("DEBT", {"path": "TODO.md"}),                      # the explicit-file case
        ("Never fabricate", {"glob": "CLAUDE.md"}),
        (r"tally[- ]only", {"path": "nephi_city_council", "regex": True}),
    ):
        tools._RG_CACHE = False
        rg = tools.grep_repo(pat, limit=300, **kw)
        tools._RG_CACHE = None                              # force stdlib
        py = tools.grep_repo(pat, limit=300, **kw)
        tools._RG_CACHE = False
        if {(m["path"], m["line_no"]) for m in rg["matches"]} != \
           {(m["path"], m["line_no"]) for m in py["matches"]}:
            parity_fail.append(f"{pat} ({rg['match_count']} vs {py['match_count']})")
    check("grep engines agree (ripgrep vs stdlib)", not parity_fail,
          "; ".join(parity_fail) or "4 cases identical")
else:
    check("grep engine parity", True, "ripgrep not installed — stdlib only, skipped")

for label, args, expect in (
    ("parent-dir escape", {"pattern": "x", "path": "../../../../etc"}, "outside_repo"),
    ("absolute escape", {"pattern": "x", "path": "/etc"}, "outside_repo"),
    ("empty pattern", {"pattern": "  "}, "empty_query"),
    ("invalid regex", {"pattern": "(unclosed", "regex": True}, "rejected"),
    ("overlong pattern", {"pattern": "a" * 500}, "rejected"),
):
    check(f"grep_repo rejects {label}", grep(args).get("error") == expect,
          grep(args).get("error"))

# A tool must never raise into the loop, even on nonsense input.
safe = True
for name in names:
    try:
        chat.DISPATCH[name]({})
    except Exception as exc:
        safe = False
        print(f"        {name} raised {type(exc).__name__}: {exc}")
check("tools return errors instead of raising", safe)

# --------------------------------------------------------------------------
print("\n-- system prompt (assembled from the repo, not hand-copied)")
# --------------------------------------------------------------------------
prompt = context.system_prompt()
stats = context.prompt_stats()
check("assembled and cacheable", stats["cacheable"],
      f"{stats['chars']:,} chars ≈ {stats['approx_tokens']:,} tokens")
check("byte-stable across calls", context.system_prompt() == prompt,
      "no timestamps or per-request ids")

required = {
    "cardinal rules from CLAUDE.md": "Never fabricate",
    "cross-entity query rules": "Never aggregate raw",
    "live schema": "gov.db — the federated",
    "entity registry": "salt_lake_county | Salt Lake County",
    "caveat vocabulary": "tally-only-partial",
    "cf_filing trap": "Never sum `cf_filing` dollar columns",
    "provenance tier trap": "two vocabularies by tier",
    "disposition orthogonality": "ORTHOGONAL",
    "disjoint state persons": "DISJOINT person population",
    "MPO empty-by-source": "empty BY SOURCE",
    "RCV winners": "election_race",
    "journalist output contract": "working journalist on deadline",
    "conciseness instruction": "Be brief",
    "scope discipline": "at the scope intended",
    "corrections instruction": "No apologies",
}
for label, needle in required.items():
    check(f"prompt carries {label}", needle in prompt)

check("no self-verification scaffolding", "double-check" not in prompt.lower(),
      "Opus 5 verifies its own work; telling it to causes over-verification")

# --------------------------------------------------------------------------
print("\n-- model configuration (verified against the current API reference)")
# --------------------------------------------------------------------------
check("model is claude-opus-5", chat.MODEL == "claude-opus-5", chat.MODEL)
# Look for actual *use* (a kwarg or a dict key), not prose — chat.py's docstring
# deliberately names these parameters to explain why they are absent.
src = Path(chat.__file__).read_text()
banned_use = [p for p in ("temperature", "top_p", "top_k", "budget_tokens")
              if f"{p}=" in src or f'"{p}"' in src or f"'{p}'" in src]
check("no sampling params or budget_tokens passed", not banned_use,
      "all four are rejected with a 400 on Opus 5"
      if not banned_use else f"found: {banned_use}")
check("effort set via output_config", chat.EFFORT in ("low", "medium", "high", "xhigh", "max"),
      f"effort={chat.EFFORT}")
check("max_tokens leaves room for thinking + text", chat.MAX_TOKENS >= 32000,
      f"{chat.MAX_TOKENS:,}")
check("refusal fallback opted into",
      "server-side-fallback-2026-07-01" in chat.BETAS, ", ".join(chat.BETAS))
caps = chat.sdk_capabilities()
check("SDK present", caps.get("installed"), f"anthropic {caps.get('version')}")

# --------------------------------------------------------------------------
print("\n-- the loop, driven by a scripted stub model")
# --------------------------------------------------------------------------

class _Block(dict):
    """A content block that answers both attribute and mapping access."""
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as exc:
            raise AttributeError(k) from exc


class _Msg:
    def __init__(self, content, stop_reason, usage):
        self.content = content
        self.stop_reason = stop_reason
        self.usage = usage
        self.stop_details = None


class _Usage:
    def __init__(self, i, o, cr=0, cc=0):
        self.input_tokens, self.output_tokens = i, o
        self.cache_read_input_tokens, self.cache_creation_input_tokens = cr, cc


class _Stream:
    def __init__(self, events, message):
        self._events, self._message = events, message
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def __iter__(self): return iter(self._events)
    def get_final_message(self): return self._message


def _delta(text):
    return types.SimpleNamespace(
        type="content_block_delta",
        delta=types.SimpleNamespace(type="text_delta", text=text))


def _start(block_type, name=None):
    return types.SimpleNamespace(
        type="content_block_start",
        content_block=types.SimpleNamespace(type=block_type, name=name))


class _StubMessages:
    """Turn 1 calls run_sql on nephi; turn 2 writes the answer."""
    def __init__(self): self.calls = []
    def stream(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            tool = _Block(type="tool_use", id="toolu_1", name="run_sql",
                          input={"sql": "SELECT COUNT(*) AS n FROM motion WHERE city='nephi'"})
            return _Stream([_start("thinking"), _start("tool_use", "run_sql")],
                           _Msg([tool], "tool_use", _Usage(1200, 90, cc=13000)))
        text = "Nephi's council recorded 1,319 motions. "
        return _Stream([_delta(text)],
                       _Msg([_Block(type="text", text=text)], "end_turn",
                            _Usage(300, 120, cr=13000)))


stub = types.SimpleNamespace(beta=types.SimpleNamespace(messages=_StubMessages()))
real_client, real_creds = chat._client, chat.credentials_status
chat._client = lambda: stub
chat.credentials_status = lambda: {"ready": True, "source": "stub"}
try:
    events = list(chat.run("How many motions has Nephi recorded?", log=False))
finally:
    chat._client, chat.credentials_status = real_client, real_creds

kinds = [e["type"] for e in events]
check("loop completes", kinds[-1] == "done", " → ".join(kinds))
check("emits a tool_use event", "tool_use" in kinds)
check("emits a tool_result event", "tool_result" in kinds)
check("streams text deltas", "text" in kinds)

result_ev = next(e for e in events if e["type"] == "tool_result")
codes = [c["code"] for c in result_ev["caveats"]]
check("THE GATE: nephi caveats reach the model unbidden", "tally-only" in codes,
      ", ".join(codes))
check("tool result carries renderable SQL evidence",
      result_ev["summary"]["kind"] == "sql" and result_ev["summary"]["row_count"] == 1,
      f"rows={result_ev['summary']['rows']}")

done = events[-1]
check("usage accumulated across turns",
      done["usage"]["input_tokens"] == 1500 and done["usage"]["output_tokens"] == 210,
      str(done["usage"]))
check("cost computed", done["cost_usd"] > 0, f"${done['cost_usd']}")
check("cache hit detected on the second turn", done["cache_hit"] is True)
check("two turns taken", done["turns"] == 2)

sent = stub.beta.messages.calls[0]
check("system prompt sent with cache_control",
      sent["system"][0].get("cache_control") == {"type": "ephemeral"})
check("tools sent to the model", len(sent["tools"]) == len(chat.TOOL_SCHEMAS),
      f"{len(sent['tools'])} schemas")
body = {**(sent.get("extra_body") or {}), **sent}
check("output_config.effort sent", body.get("output_config", {}).get("effort") == chat.EFFORT)
check("fallbacks sent", body.get("fallbacks") == "default")
check("no sampling params in the request",
      not ({"temperature", "top_p", "top_k"} & set(sent)))

# Refusals must be caught before content is read.
class _RefusingMessages:
    def stream(self, **kwargs):
        return _Stream([], _Msg([], "refusal", _Usage(10, 0)))

chat._client = lambda: types.SimpleNamespace(
    beta=types.SimpleNamespace(messages=_RefusingMessages()))
chat.credentials_status = lambda: {"ready": True, "source": "stub"}
try:
    refusal_events = list(chat.run("test", log=False))
finally:
    chat._client, chat.credentials_status = real_client, real_creds
check("refusal handled without reading content",
      any(e["type"] == "refusal" for e in refusal_events),
      " → ".join(e["type"] for e in refusal_events))

# A tool that raises must not kill the turn.
class _BadToolMessages:
    def __init__(self): self.n = 0
    def stream(self, **kwargs):
        self.n += 1
        if self.n == 1:
            tool = _Block(type="tool_use", id="t1", name="run_sql", input={"sql": "SELECT 1"})
            return _Stream([], _Msg([tool], "tool_use", _Usage(10, 5)))
        return _Stream([_delta("ok")], _Msg([_Block(type="text", text="ok")], "end_turn", _Usage(5, 5)))

boom = lambda a: (_ for _ in ()).throw(RuntimeError("exploded"))
chat._client = lambda: types.SimpleNamespace(
    beta=types.SimpleNamespace(messages=_BadToolMessages()))
chat.credentials_status = lambda: {"ready": True, "source": "stub"}
saved = chat.DISPATCH["run_sql"]
chat.DISPATCH["run_sql"] = boom
try:
    bad_events = list(chat.run("test", log=False))
finally:
    chat.DISPATCH["run_sql"] = saved
    chat._client, chat.credentials_status = real_client, real_creds
check("a raising tool is reported, not fatal",
      bad_events[-1]["type"] == "done"
      and any(e["type"] == "tool_result" and e["summary"].get("kind") == "error"
              for e in bad_events))

# --------------------------------------------------------------------------
print("\n-- HTTP surface")
# --------------------------------------------------------------------------

def get(path):
    try:
        with urllib.request.urlopen(BASE + path) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code
    except OSError as e:
        return {"_unreachable": str(e)}, 0


status, code = get("/api/chat-status")
if status.get("_unreachable"):
    check("server reachable", False, status["_unreachable"])
else:
    check("/api/chat-status reports readiness honestly",
          set(("ready", "reason", "model", "sdk", "system_prompt")) <= set(status),
          f"ready={status['ready']} ({status.get('reason') or status.get('credential_source')})")
    check("status reports the model config",
          status["model"] == chat.MODEL and status["max_turns"] == chat.MAX_TURNS)

    req = urllib.request.Request(
        BASE + "/api/chat", method="POST",
        data=json.dumps({"question": "test"}).encode(),
        headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            ctype = r.headers.get("Content-Type", "")
            first = r.readline().decode()
        check("/api/chat streams SSE", ctype.startswith("text/event-stream"), ctype)
        payload = json.loads(first[6:]) if first.startswith("data: ") else {}
        if status["ready"]:
            check("SSE first event is well-formed", "type" in payload, str(payload)[:70])
        else:
            check("no credentials → one clean fatal event, not a crash",
                  payload.get("type") == "error" and payload.get("fatal") is True,
                  str(payload.get("message", ""))[:60])
    except OSError as e:
        check("/api/chat responds", False, str(e))

    empty, code = get("/api/chat?q=")
    check("empty question rejected", code == 400 and empty["error"] == "empty_question")

    page = (Path(__file__).resolve().parent / "chat.html").read_text()
    check("chat.html is self-contained", "//" not in page.split("<script>")[0].split("src=")[-1][:8]
          and 'href="http' not in page and 'src="http' not in page)
    for endpoint in ("/api/chat", "/api/chat-status", "/api/health", "/api/document"):
        check(f"chat.html calls {endpoint}", endpoint in page)

print(f"\n  {PASS} passed, {FAIL} failed\n")
sys.exit(1 if FAIL else 0)
