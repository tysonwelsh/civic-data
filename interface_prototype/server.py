#!/usr/bin/env python3
"""Local HTTP server for the civic-data chat interface — Phase 0.

Exposes the read-only data layer over ``/api/*`` so the page never touches the
filesystem. Hosting later is then a config change, not a rewrite.

    python3 interface_prototype/server.py            # 127.0.0.1:8787
    python3 interface_prototype/server.py --port 9000

Stdlib only. No API key, no model, no writes. Every endpoint is exercisable
with curl:

    curl -s localhost:8787/api/health
    curl -s -X POST localhost:8787/api/query \
         -H 'content-type: application/json' \
         -d '{"sql":"SELECT COUNT(*) FROM motion WHERE city=''nephi''"}'
    curl -s 'localhost:8787/api/search?q=%22accessory+dwelling%22&limit=3'
    curl -s 'localhost:8787/api/entity?name=Salt+Lake'
    curl -s 'localhost:8787/api/coverage?entity=nephi'
    curl -s 'localhost:8787/api/schema?tables=caveat'
    curl -s 'localhost:8787/api/document?path=CLAUDE.md&max_chars=200'
    curl -s 'localhost:8787/api/grep?pattern=tally-only&path=nephi_city_council'
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

if __package__ in (None, ""):                       # run as a script
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interface_prototype.agent import config, gate, tools  # noqa: E402

# Endpoints the gate does NOT protect: liveness for a monitor, and the gate's
# own posture so a deploy can be checked without a token. Neither spends money
# nor reveals data.
_UNGATED = {"/api/health", "/api/gate-status"}


# Tool error keys that are the caller's fault rather than the server's.
_STATUS_BY_ERROR = {
    "rejected": 400,
    "bad_corpus": 400,
    "empty_query": 400,
    "empty_name": 400,
    "empty_path": 400,
    "no_dataset_filter": 400,
    "no_date_filter": 400,
    "bad_path": 400,
    "outside_repo": 403,
    "not_text": 415,
    "unknown_entity": 404,
    "no_match": 404,
    "not_found": 404,
    "not_a_file": 404,
    "timeout": 504,
    "search_failed": 500,
    "read_failed": 500,
}


def _int(value: str | None, default: int | None = None) -> int | None:
    try:
        return int(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _flag(value, default: bool = False) -> bool:
    """Query strings carry booleans as text; a JSON body carries them as bools."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("1", "true", "yes", "on")


class Handler(BaseHTTPRequestHandler):
    server_version = "civic-data-phase0/0.1"
    protocol_version = "HTTP/1.1"

    # ---------------------------------------------------------------- plumbing

    def log_message(self, fmt, *args):  # quieter than the default
        sys.stderr.write("  %s %s\n" % (self.address_string(), fmt % args))

    def _send(self, payload: dict, status: int = 200,
              extra: list[tuple[str, str]] | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in extra or []:
            self.send_header(name, value)
        for name, value in gate.cors_headers(self.headers.get("Origin")):
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_tool(self, payload: dict) -> None:
        status = _STATUS_BY_ERROR.get(payload.get("error", ""), 200) if "error" in payload else 200
        self._send(payload, status)

    def _body(self) -> dict:
        length = _int(self.headers.get("Content-Length"), 0) or 0
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"body is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("body must be a JSON object")
        return parsed

    # ---------------------------------------------------------------- routing

    def do_GET(self) -> None:
        self._route("GET")

    def do_POST(self) -> None:
        self._route("POST")

    def do_OPTIONS(self) -> None:
        """CORS preflight — the browser sends this before a cross-origin POST."""
        origin = self.headers.get("Origin")
        headers = gate.cors_headers(origin)
        self.send_response(204 if headers else 403)
        for name, value in headers:
            self.send_header(name, value)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _route(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        # The gate runs before any handler, so a refused caller costs nothing
        # but the parse above. Static pages are ungated — the secret URL that
        # serves them is municipal-sky's business, not this service's.
        if path.startswith("/api/") and path not in _UNGATED:
            token = self.headers.get("X-Civic-Token") or query.get("token")
            ok, info = gate.admit(self.headers.get("Origin"), token,
                                  self.client_address[0] if self.client_address else "?")
            if not ok:
                status = info.pop("status", 403)
                extra = [("Retry-After", str(info["retry_after"]))] \
                    if info.get("retry_after") else []
                self._send(info, status, extra)
                return

        try:
            body = self._body() if method == "POST" else {}
        except ValueError as exc:
            self._send({"error": "bad_body", "reason": str(exc)}, 400)
            return

        args = {**query, **body}

        try:
            handler = getattr(self, f"api_{path[5:].replace('-', '_')}", None) \
                if path.startswith("/api/") else None
            if handler is not None:
                handler(args)
            elif path in ("/", "/index.html"):
                # chat.html is Phase 2; until it exists, / lands on the Phase 0
                # console so the data layer has a face.
                root = config.PROTOTYPE_DIR
                self._static("chat.html" if (root / "chat.html").is_file() else "console.html")
            elif not path.startswith("/api/"):
                self._static(path.lstrip("/"))
            else:
                self._send({"error": "no_such_endpoint", "path": path,
                            "endpoints": sorted(
                                n[4:] for n in dir(self) if n.startswith("api_"))}, 404)
        except BrokenPipeError:
            pass
        except Exception as exc:                     # never leak a traceback to the client
            traceback.print_exc()
            self._send({"error": "server_error", "reason": f"{type(exc).__name__}: {exc}"}, 500)

    # ---------------------------------------------------------------- endpoints

    def api_health(self, args: dict) -> None:
        self._send(tools.health())

    def api_gate_status(self, args: dict) -> None:
        """Whether exposure controls are on, and how much of the budget is left.
        Ungated on purpose — carries no secret and no data, so a deploy check
        and an uptime monitor can both reach it."""
        self._send(gate.status())

    def api_query(self, args: dict) -> None:
        sql = args.get("sql")
        if not sql:
            self._send({"error": "empty_query", "reason": "pass sql= (GET) or {\"sql\": ...} (POST)"}, 400)
            return
        self._send_tool(tools.run_sql(sql, limit=_int(args.get("limit"))))

    def api_search(self, args: dict) -> None:
        query = args.get("q") or args.get("query") or ""
        self._send_tool(tools.search_text(
            query,
            corpus=args.get("corpus", "minutes"),
            entity=args.get("entity"),
            dataset=args.get("dataset"),
            date_from=args.get("date_from"),
            date_to=args.get("date_to"),
            limit=_int(args.get("limit"), config.SEARCH_DEFAULT_LIMIT),
        ))

    def api_schema(self, args: dict) -> None:
        tables = args.get("tables")
        if isinstance(tables, str):
            tables = [t.strip() for t in tables.split(",") if t.strip()]
        counts = str(args.get("counts", "")).lower() in ("1", "true", "yes")
        self._send_tool(tools.get_schema(tables, with_counts=counts))

    def api_coverage(self, args: dict) -> None:
        self._send_tool(tools.list_coverage(args.get("entity")))

    def api_document(self, args: dict) -> None:
        self._send_tool(tools.read_document(
            args.get("path", ""),
            offset=_int(args.get("offset"), 0),
            max_chars=_int(args.get("max_chars"), config.DOC_MAX_CHARS),
        ))

    def api_entity(self, args: dict) -> None:
        self._send_tool(tools.resolve_entity(args.get("name", "")))

    def api_grep(self, args: dict) -> None:
        self._send_tool(tools.grep_repo(
            args.get("pattern") or args.get("q") or "",
            path=args.get("path"),
            glob=args.get("glob"),
            regex=_flag(args.get("regex")),
            ignore_case=_flag(args.get("ignore_case"), default=True),
            limit=_int(args.get("limit"), config.GREP_DEFAULT_LIMIT),
        ))

    def api_chat(self, args: dict) -> None:
        """The agent loop, streamed to the browser as Server-Sent Events."""
        from interface_prototype.agent import chat

        question = (args.get("q") or args.get("question") or "").strip()
        if not question:
            self._send({"error": "empty_question",
                        "reason": 'pass {"question": "..."} or ?q=...'}, 400)
            return

        history = args.get("history") or []
        if not isinstance(history, list):
            self._send({"error": "bad_history", "reason": "history must be a list"}, 400)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        # Nginx/Caddy buffering would hold the stream until it completed,
        # turning a streamed answer into a 60-second blank page.
        self.send_header("X-Accel-Buffering", "no")
        for name, value in gate.cors_headers(self.headers.get("Origin")):
            self.send_header(name, value)
        self.end_headers()

        def emit(event: dict) -> None:
            payload = json.dumps(event, ensure_ascii=False, default=str)
            self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
            self.wfile.flush()

        try:
            for event in chat.run(question, history=history):
                emit(event)
        except BrokenPipeError:
            pass                                  # the reader navigated away
        except Exception as exc:
            traceback.print_exc()
            try:
                emit({"type": "error", "fatal": True,
                      "message": f"{type(exc).__name__}: {exc}"})
            except OSError:
                pass

    def api_chat_status(self, args: dict) -> None:
        """Whether the agent loop can run at all — checked before any spend."""
        from interface_prototype.agent import chat, context

        caps = chat.sdk_capabilities()
        if not caps.get("installed"):
            creds = {"ready": False, "source": None,
                     "reason": "the `anthropic` package is not installed "
                               "(pip install -U anthropic)"}
        else:
            creds = chat.credentials_status()

        return self._send({
            "ready": creds["ready"],
            "reason": creds.get("reason"),
            "credential_source": creds.get("source"),
            "model": chat.MODEL,
            "effort": chat.EFFORT,
            "max_tokens": chat.MAX_TOKENS,
            "max_turns": chat.MAX_TURNS,
            "sdk": caps,
            "system_prompt": context.prompt_stats(),
        })

    # ---------------------------------------------------------------- static

    _CONTENT_TYPES = {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
    }

    def _static(self, rel: str) -> None:
        """Serve a file from interface_prototype/ — for the Phase 2 page."""
        root = config.PROTOTYPE_DIR.resolve()
        target = (root / unquote(rel)).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            self._send({"error": "not_found", "path": rel,
                        "hint": "the API lives under /api/*"}, 404)
            return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",
                         self._CONTENT_TYPES.get(target.suffix.lower(), "text/plain; charset=utf-8"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--host", default=config.DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=config.DEFAULT_PORT)
    args = parser.parse_args()

    if not config.DB_PATH.exists():
        print(f"gov.db not found at {config.DB_PATH}", file=sys.stderr)
        return 1

    # Fail closed on purpose. An unset secret disables the gate, which is right
    # for local development and catastrophic in production — so production sets
    # CIVIC_REQUIRE_AUTH=1 and the service refuses to start unprotected.
    if gate.REQUIRE_AUTH and not gate.enabled():
        print("CIVIC_REQUIRE_AUTH=1 but CIVIC_SERVICE_SECRET is unset — refusing "
              "to start unprotected.", file=sys.stderr)
        return 2

    info = tools.health()
    print(f"civic-data Phase 0 — read-only data layer")
    print(f"  db      {info['database']}  ({info['db_bytes'] / 1e9:.2f} GB, built {info['built_at']})")
    print(f"  loaded  {info['entities']} entities · {info['motions']:,} motions · "
          f"{info['caveat_rows']} caveat rows")
    if gate.enabled():
        print(f"  gate    ON · origins {', '.join(gate.ALLOWED_ORIGINS)} · "
              f"{gate.RATE_PER_MIN}/min · ${gate.DAILY_USD:.2f}/day, "
              f"${gate.MONTHLY_USD:.2f}/mo "
              f"(${gate.spent('day'):.2f} spent today)")
    else:
        print("  gate    OFF — no CIVIC_SERVICE_SECRET. Fine locally; NEVER expose "
              "this to the internet.")
    # Flush explicitly: stdout is block-buffered when redirected, so under
    # systemd this banner would otherwise sit unwritten and the journal would
    # never record whether the gate came up ON or OFF.
    print(f"  serving http://{args.host}:{args.port}/api/health", flush=True)

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
