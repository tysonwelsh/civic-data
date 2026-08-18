"""The public-exposure layer: who may ask, how often, and how much may be spent.

CHAT_PLAN.md §5 put auth, rate limiting and spend ceilings out of scope for the
prototype. This is that scope, added for the hosted deployment.

Four independent checks, in the order the server applies them — cheapest first,
so an abusive caller is rejected before anything expensive happens:

1. **Origin** — the browser's ``Origin`` must be on the allow-list.
2. **Token** — an HMAC-SHA256 token minted by municipal-sky's PHP and verified
   here. Neither side ships the secret to the browser; only the short-lived
   token crosses.
3. **Rate** — per-token and per-IP, sliding window, in memory.
4. **Budget** — daily and monthly ceilings read from ``logs/chat.jsonl``, the
   file the cost sweep populates. Measured mean is $0.325/question, so the
   defaults below are set in questions-per-day rather than guessed dollars.

**Fails open only when unconfigured, and says so loudly.** With no
CIVIC_SERVICE_SECRET the gate is disabled and local development is unchanged —
which is exactly how a misconfigured production ends up wide open, so
``CIVIC_REQUIRE_AUTH=1`` makes the server refuse to start without one.

The deployment's credential is a SECRET URL with no password (owner decision).
That makes these ceilings the only thing standing between a leaked link and
your card, and it makes rotation the primary defence: change the secret, every
outstanding token and link dies within TOKEN_TTL_S.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import threading
import time
from collections import deque
from typing import Any

from . import config


# --------------------------------------------------------------------------
# configuration — environment, so a secret never lands in the repo
# --------------------------------------------------------------------------

def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


SECRET = _env("CIVIC_SERVICE_SECRET")
REQUIRE_AUTH = _env("CIVIC_REQUIRE_AUTH") in ("1", "true", "yes", "on")

# Comma-separated. Exact scheme+host+port matches, as the browser sends them.
ALLOWED_ORIGINS = tuple(
    o.strip().rstrip("/") for o in _env(
        "CIVIC_ALLOWED_ORIGINS",
        "https://municipalsky.com,https://www.municipalsky.com").split(",")
    if o.strip()
)

TOKEN_TTL_S = int(_env("CIVIC_TOKEN_TTL_S", "900"))          # 15 minutes
CLOCK_SKEW_S = 60                                            # tolerate drift

# Sliding windows. A question takes 10–70s, so these are generous for a human
# and immediately binding on a script.
RATE_PER_MIN = int(_env("CIVIC_RATE_PER_MIN", "4"))
RATE_PER_HOUR = int(_env("CIVIC_RATE_PER_HOUR", "30"))

# Ceilings, in dollars. $100/mo ÷ 30 ≈ $3.33/day; the daily default is set a
# little above that so one busy day does not trip on the monthly pace.
DAILY_USD = float(_env("CIVIC_DAILY_USD", "4.00"))
MONTHLY_USD = float(_env("CIVIC_MONTHLY_USD", "100.00"))


def enabled() -> bool:
    """Whether authentication is actually being enforced."""
    return bool(SECRET)


def status() -> dict:
    """What the gate would do right now — safe to expose, carries no secret."""
    return {
        "enabled": enabled(),
        "require_auth": REQUIRE_AUTH,
        "allowed_origins": list(ALLOWED_ORIGINS),
        "token_ttl_s": TOKEN_TTL_S,
        "rate_per_min": RATE_PER_MIN,
        "rate_per_hour": RATE_PER_HOUR,
        "daily_usd": DAILY_USD,
        "monthly_usd": MONTHLY_USD,
        "spent_today_usd": round(spent("day"), 4),
        "spent_month_usd": round(spent("month"), 4),
    }


# --------------------------------------------------------------------------
# 1. origin
# --------------------------------------------------------------------------

def check_origin(origin: str | None) -> tuple[bool, str | None]:
    """A missing Origin is allowed — curl and same-origin GETs send none, and
    the token is what actually authorises. This only blocks *other websites*
    driving the API from a visitor's browser."""
    if not enabled() or not origin:
        return True, None
    if origin.rstrip("/") in ALLOWED_ORIGINS:
        return True, None
    return False, f"origin {origin} is not allowed"


def cors_headers(origin: str | None) -> list[tuple[str, str]]:
    """Echo the origin only when it is allowed — never a bare ``*``, which
    would let any page on the internet spend the budget."""
    if not origin or origin.rstrip("/") not in ALLOWED_ORIGINS:
        return []
    return [
        ("Access-Control-Allow-Origin", origin),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type, X-Civic-Token"),
        ("Access-Control-Max-Age", "600"),
        ("Vary", "Origin"),
    ]


# --------------------------------------------------------------------------
# 2. token
# --------------------------------------------------------------------------
# Format:  base64url(json payload) + "." + base64url(hmac-sha256)
# Payload: {"sub": <opaque caller id>, "exp": <unix seconds>}
#
# municipal-sky's api/civic-token.php mints these with the same secret; see
# DEPLOY.md for the PHP that must stay byte-compatible with _sign().

def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(payload_b64: str) -> str:
    return _b64e(hmac.new(SECRET.encode("utf-8"),
                          payload_b64.encode("ascii"), hashlib.sha256).digest())


def mint_token(subject: str = "web", ttl_s: int | None = None) -> str:
    """Mint a token. Production mints in PHP; this exists for the gates and for
    verifying the PHP implementation agrees."""
    if not SECRET:
        raise RuntimeError("CIVIC_SERVICE_SECRET is not set")
    payload = {"sub": subject,
               "exp": int(time.time()) + (TOKEN_TTL_S if ttl_s is None else ttl_s)}
    body = _b64e(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    return f"{body}.{_sign(body)}"


def verify_token(token: str | None) -> tuple[bool, str | None, str | None]:
    """Returns ``(ok, subject, reason)``. Constant-time on the signature."""
    if not enabled():
        return True, "local", None
    if not token:
        return False, None, "missing token"
    body, _, signature = token.partition(".")
    if not body or not signature:
        return False, None, "malformed token"
    if not hmac.compare_digest(_sign(body), signature):
        return False, None, "bad signature"
    try:
        payload = json.loads(_b64d(body))
        expires = int(payload["exp"])
    except (ValueError, KeyError, TypeError):
        return False, None, "unreadable payload"
    if expires + CLOCK_SKEW_S < time.time():
        return False, None, "token expired"
    return True, str(payload.get("sub", "web"))[:64], None


# --------------------------------------------------------------------------
# 3. rate
# --------------------------------------------------------------------------

_hits: dict[str, deque] = {}
_hits_lock = threading.Lock()


def check_rate(key: str) -> tuple[bool, str | None, int]:
    """Sliding-window limiter. Returns ``(ok, reason, retry_after_s)``.

    In memory, so a restart clears it. That is an accepted weakness: the spend
    ceiling below is durable, and it is the one that bounds the damage.
    """
    if not enabled():
        return True, None, 0
    now = time.monotonic()
    with _hits_lock:
        window = _hits.setdefault(key, deque())
        while window and now - window[0] > 3600:
            window.popleft()
        in_minute = sum(1 for t in window if now - t <= 60)
        if in_minute >= RATE_PER_MIN:
            return False, f"more than {RATE_PER_MIN} questions in a minute", 60
        if len(window) >= RATE_PER_HOUR:
            return False, f"more than {RATE_PER_HOUR} questions in an hour", 600
        window.append(now)
        return True, None, 0


def forget_rate(key: str | None = None) -> None:
    """Drop rate state — used by the gates, and by an operator unblocking someone."""
    with _hits_lock:
        _hits.clear() if key is None else _hits.pop(key, None)


# --------------------------------------------------------------------------
# 4. budget
# --------------------------------------------------------------------------

def spent(period: str = "day") -> float:
    """Dollars recorded in logs/chat.jsonl for today or this month.

    Reads the log rather than holding a counter, so a restart cannot forget
    what was already spent — the property that makes this the durable ceiling.
    """
    prefix = time.strftime("%Y-%m-%d" if period == "day" else "%Y-%m")
    total = 0.0
    try:
        with config.CHAT_LOG.open("r", encoding="utf-8") as handle:
            for line in handle:
                if prefix not in line:              # cheap reject before parsing
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if str(row.get("ts", "")).startswith(prefix):
                    total += float(row.get("cost_usd") or 0.0)
    except OSError:
        return 0.0
    return total


def check_budget() -> tuple[bool, str | None, dict]:
    """Refuse a NEW question once a ceiling is reached.

    Checked before the request, so the ceiling can be exceeded by at most one
    question's cost — bounded by MAX_TURNS, not unbounded.
    """
    day, month = spent("day"), spent("month")
    detail = {"spent_today_usd": round(day, 4), "daily_usd": DAILY_USD,
              "spent_month_usd": round(month, 4), "monthly_usd": MONTHLY_USD}
    if not enabled():
        return True, None, detail
    if month >= MONTHLY_USD:
        return False, (f"the monthly ceiling of ${MONTHLY_USD:.2f} has been reached "
                       f"(${month:.2f} spent). It resets on the 1st."), detail
    if day >= DAILY_USD:
        return False, (f"today's ceiling of ${DAILY_USD:.2f} has been reached "
                       f"(${day:.2f} spent). It resets at midnight."), detail
    return True, None, detail


# --------------------------------------------------------------------------
# the whole gate, in the order the server applies it
# --------------------------------------------------------------------------

def admit(origin: str | None, token: str | None,
          client_ip: str) -> tuple[bool, dict[str, Any]]:
    """Run every check. Returns ``(ok, info)``; ``info['status']`` is the HTTP
    code to send on refusal and ``info['error']`` the machine-readable key."""
    ok, reason = check_origin(origin)
    if not ok:
        return False, {"status": 403, "error": "origin_not_allowed", "reason": reason}

    ok, subject, reason = verify_token(token)
    if not ok:
        return False, {"status": 401, "error": "unauthorized", "reason": reason}

    ok, reason, retry = check_rate(f"{subject}|{client_ip}")
    if not ok:
        return False, {"status": 429, "error": "rate_limited",
                       "reason": reason, "retry_after": retry}

    ok, reason, detail = check_budget()
    if not ok:
        return False, {"status": 429, "error": "budget_exhausted",
                       "reason": reason, **detail}

    return True, {"subject": subject, **detail}
