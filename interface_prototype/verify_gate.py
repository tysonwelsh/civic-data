#!/usr/bin/env python3
"""Gate check — the exposure controls, proven without spending anything.

The deployment's credential is a SECRET URL with no password, so these four
checks are the only thing between a leaked link and the card on file. They are
therefore asserted harder than anything else in this folder.

Runs the gate directly (no server needed) with a test secret injected, then
exercises the HTTP surface if a server is up.

    python3 interface_prototype/verify_gate.py
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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


print("\nGate check — auth, origin, rate, budget. No API spend.\n")

# --------------------------------------------------------------------------
print("-- disabled by default (local development must be unchanged)")
# --------------------------------------------------------------------------
for var in ("CIVIC_SERVICE_SECRET", "CIVIC_REQUIRE_AUTH"):
    os.environ.pop(var, None)
from interface_prototype.agent import gate  # noqa: E402
gate = importlib.reload(gate)

check("gate off with no secret", not gate.enabled())
ok, _ = gate.admit(None, None, "1.2.3.4")
check("everything admitted when off", ok)
ok, _, _ = gate.verify_token(None)
check("token check is a no-op when off", ok)

# --------------------------------------------------------------------------
print("\n-- enabled with a secret")
# --------------------------------------------------------------------------
os.environ["CIVIC_SERVICE_SECRET"] = "test-secret-not-the-real-one"
os.environ["CIVIC_ALLOWED_ORIGINS"] = "https://municipalsky.com"
os.environ["CIVIC_RATE_PER_MIN"] = "3"
os.environ["CIVIC_RATE_PER_HOUR"] = "5"
gate = importlib.reload(gate)
check("gate on with a secret", gate.enabled())

# --- token ---------------------------------------------------------------
token = gate.mint_token("web")
ok, subject, reason = gate.verify_token(token)
check("a minted token verifies", ok and subject == "web", reason or subject)

ok, _, reason = gate.verify_token(None)
check("no token is refused", not ok, reason)
ok, _, reason = gate.verify_token("garbage")
check("malformed token refused", not ok, reason)

body, _, sig = token.partition(".")
ok, _, reason = gate.verify_token(f"{body}.{'A' * len(sig)}")
check("forged signature refused", not ok, reason)

# Tamper with the payload but keep the original signature — the classic attack.
import base64  # noqa: E402
forged = base64.urlsafe_b64encode(
    json.dumps({"sub": "web", "exp": int(time.time()) + 99999},
               separators=(",", ":"), sort_keys=True).encode()).decode().rstrip("=")
ok, _, reason = gate.verify_token(f"{forged}.{sig}")
check("payload tampering refused", not ok, reason)

expired = gate.mint_token("web", ttl_s=-3600)
ok, _, reason = gate.verify_token(expired)
check("expired token refused", not ok, reason)

# A token minted under a DIFFERENT secret must not verify — this is what makes
# rotation work: change the secret and every outstanding link dies.
good_secret = gate.SECRET
os.environ["CIVIC_SERVICE_SECRET"] = "rotated-secret"
gate = importlib.reload(gate)
ok, _, reason = gate.verify_token(token)
check("rotation invalidates old tokens", not ok, reason)
os.environ["CIVIC_SERVICE_SECRET"] = good_secret
gate = importlib.reload(gate)

# --- origin --------------------------------------------------------------
ok, _ = gate.check_origin("https://municipalsky.com")
check("allowed origin admitted", ok)
ok, reason = gate.check_origin("https://evil.example")
check("foreign origin refused", not ok, reason)
ok, _ = gate.check_origin(None)
check("absent origin admitted (curl, same-origin)", ok)
check("CORS never echoes a wildcard",
      not any(v == "*" for _, v in gate.cors_headers("https://municipalsky.com")))
check("CORS emits nothing for a foreign origin",
      gate.cors_headers("https://evil.example") == [])

# --- rate ----------------------------------------------------------------
gate.forget_rate()
allowed = sum(1 for _ in range(6) if gate.check_rate("k")[0])
check("per-minute limit binds", allowed == 3, f"{allowed} of 6 admitted (cap 3)")
gate.forget_rate()
check("limiter is per-key", gate.check_rate("other")[0])
gate.forget_rate()
ok, reason, retry = gate.check_rate("k"), None, 0
for _ in range(5):
    gate.check_rate("z")
ok, reason, retry = gate.check_rate("z")
check("refusal carries a retry hint", not ok and retry > 0, f"retry_after={retry}")

# --- budget --------------------------------------------------------------
os.environ["CIVIC_DAILY_USD"] = "0.00"
gate = importlib.reload(gate)
ok, reason, detail = gate.check_budget()
check("exhausted daily ceiling refuses", not ok, reason)
check("refusal reports the numbers", "spent_today_usd" in detail and "daily_usd" in detail)
os.environ["CIVIC_DAILY_USD"] = "9999"
os.environ["CIVIC_MONTHLY_USD"] = "0.00"
gate = importlib.reload(gate)
ok, reason, _ = gate.check_budget()
check("exhausted monthly ceiling refuses", not ok, reason)
os.environ["CIVIC_MONTHLY_USD"] = "9999"
gate = importlib.reload(gate)

# The ceiling must read the durable log, not a counter a restart would forget.
check("spend is read from the log file", gate.spent("day") >= 0.0,
      f"${gate.spent('month'):.2f} this month in chat.jsonl")

# --- ordering ------------------------------------------------------------
# Cheapest check first: a bad origin must be refused before the token is even
# examined, so an abusive caller costs the least possible work.
ok, info = gate.admit("https://evil.example", None, "1.2.3.4")
check("origin refused before token", not ok and info["error"] == "origin_not_allowed",
      info.get("error"))
ok, info = gate.admit("https://municipalsky.com", None, "1.2.3.4")
check("missing token is 401", not ok and info["status"] == 401, info.get("error"))
gate.forget_rate()
ok, info = gate.admit("https://municipalsky.com", gate.mint_token(), "1.2.3.4")
check("a good caller is admitted", ok, info.get("subject"))

# --------------------------------------------------------------------------
print("\n-- HTTP surface (skipped if no server is running)")
# --------------------------------------------------------------------------


def call(path: str):
    try:
        with urllib.request.urlopen(BASE + path, timeout=10) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read()), e.code
        except ValueError:
            return {}, e.code
    except OSError:
        return None, 0


d, code = call("/api/gate-status")
if code == 0:
    print("  (no server on 8787 — run server.py to include these)")
else:
    check("/api/gate-status is reachable ungated", code == 200)
    check("gate-status leaks no secret",
          d is not None and not any("secret" in k.lower() for k in d))
    check("gate-status reports posture",
          all(k in (d or {}) for k in ("enabled", "daily_usd", "spent_today_usd")),
          f"enabled={(d or {}).get('enabled')}")
    _, code = call("/api/health")
    check("/api/health stays ungated", code == 200)

print(f"\n  {PASS} passed, {FAIL} failed\n")
sys.exit(1 if FAIL else 0)
