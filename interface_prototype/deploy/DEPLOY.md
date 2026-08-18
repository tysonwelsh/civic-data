# Deploying civic-data behind Municipal Sky

The service is stdlib Python plus `anthropic` — no framework, no build step.
What makes this deployment unusual is the payload (**3.65 GB**: 1.97 GB of text
plus a 1.68 GB SQLite file) and the fact that the credential is a **secret URL
with no password**, which makes the spend ceiling load-bearing rather than
precautionary.

```
browser ──► municipalsky.com/civic-data/<key>        (PHP page + token minting)
        └─► data.municipalsky.com/api/chat           (Python service, SSE)
```

The secret never reaches the browser. PHP mints a 15-minute HMAC token; the
Python service verifies it. Both halves are asserted against each other by
`verify_token_parity.php` — run it before shipping, and after any change to
either signing implementation.

---

## 1. The box

Any Ubuntu 24.04 VPS with ≥25 GB disk and ≥2 GB RAM. Hetzner CX22 (~€4/mo,
40 GB) and DigitalOcean's $6 basic droplet (25 GB) both fit; nothing below
depends on which.

```sh
sudo adduser --system --group --home /srv/civic-data civic
sudo apt update
sudo apt install -y python3 python3-pip ripgrep caddy rsync
sudo -u civic pip3 install --break-system-packages 'anthropic>=0.51'
sudo install -d -o civic -g civic /srv/civic-data
```

**ripgrep is not optional.** Without it `grep_repo` falls back to a stdlib scan
that cannot finish a repo-wide sweep inside its 15s deadline — measured 2.5s
versus 15s-and-truncated. Truncated sweeps make the model retry, which costs
real money: the most expensive question in the cost sweep ($1.29, 70s, six grep
calls) was that failure mode.

Confirm both engines agree on the box after install:

```sh
cd /srv/civic-data && python3 interface_prototype/verify_phase1.py | grep engines
```

## 2. Secrets and ceilings

`/etc/civic-data.env`, `chmod 600`, **never** in the repo:

```sh
ANTHROPIC_API_KEY=sk-ant-...
CIVIC_SERVICE_SECRET=<64 hex chars: openssl rand -hex 32>
CIVIC_REQUIRE_AUTH=1
CIVIC_ALLOWED_ORIGINS=https://municipalsky.com,https://www.municipalsky.com
CIVIC_DAILY_USD=4.00
CIVIC_MONTHLY_USD=100.00
CIVIC_RATE_PER_MIN=4
CIVIC_RATE_PER_HOUR=30
```

```sh
sudo chmod 600 /etc/civic-data.env && sudo chown root:root /etc/civic-data.env
```

`CIVIC_REQUIRE_AUTH=1` makes the service **refuse to start** without a secret.
Unset secret means the gate is off, which is right locally and catastrophic
here, so failure is made loud rather than silent.

Ceilings are sized from measurement, not guesswork: the 15-question cost sweep
gave **mean $0.325, median $0.195, max $1.291**. $4/day ≈ 12 questions;
$100/mo ≈ 300.

## 3. Service and TLS

```sh
sudo cp interface_prototype/deploy/civic-data.service /etc/systemd/system/
sudo cp interface_prototype/deploy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl daemon-reload
sudo systemctl enable --now civic-data
sudo systemctl reload caddy
journalctl -u civic-data -n 20 --no-pager     # must print "gate ON"
```

Point `data.municipalsky.com`'s A record at the box **before** reloading Caddy —
the ACME challenge fails without it and no certificate is issued.

## 4. Shipping the data

From your Mac:

```sh
interface_prototype/deploy/sync.sh civic@<ip> --dry-run
interface_prototype/deploy/sync.sh civic@<ip>
```

The manifest is `git ls-files` plus `gov.db` — derived from the repo's existing
`.gitignore`, so `raw/` (42 GB) and `_backups/` (7.7 GB) are excluded by the
same rule that keeps them off GitHub, and cannot drift out of sync with a
hand-maintained list. Verified: no `raw/`, no `_backups/`, no `.env`.

After a federation rebuild, `--db-only` ships just the database.

## 5. The Municipal Sky side

Add to `/home1/tdrivemy/private_config/secrets.php`:

```php
'civic_service_secret' => '<the SAME value as CIVIC_SERVICE_SECRET>',
'civic_url_key'        => '<openssl rand -hex 12 — the secret path segment>',
'civic_service_url'    => 'https://data.municipalsky.com',
```

Copy `deploy/civic-token.php` to `municipal-sky-site/api/civic-token.php`. It
mints a token only when the caller presents the same `civic_url_key` that
served the page, compared with `hash_equals` — so the endpoint cannot become an
open token vending machine, and a timing oracle cannot leak the key.

It returns **404** rather than 403 on a bad key: an unlisted page should be
indistinguishable from one that does not exist.

## 6. Verify before announcing

```sh
curl -s https://data.municipalsky.com/api/gate-status          # enabled: true
curl -s -o /dev/null -w '%{http_code}\n' \
     https://data.municipalsky.com/api/query?sql=SELECT+1      # 401
curl -s -o /dev/null -w '%{http_code}\n' -H 'Origin: https://evil.example' \
     https://data.municipalsky.com/api/query?sql=SELECT+1      # 403
```

Then open the real page and ask one question. Confirm the answer **streams**
rather than arriving all at once — if it arrives in one lump, response
buffering is on somewhere and `flush_interval -1` is not taking effect.

## 7. Operating it

**Check spend** — `curl -s .../api/gate-status | python3 -m json.tool`, or on
the box `jq -s 'map(.cost_usd) | add' /srv/civic-data/interface_prototype/logs/chat.jsonl`.

**Rotate the link.** This is the primary defence, because with no password the
URL *is* the credential. Change `civic_url_key` in `secrets.php` and the old
link 404s immediately. Change `CIVIC_SERVICE_SECRET` on **both** sides and every
outstanding token dies within 15 minutes — asserted by the gate suite.

**If a link leaks**, the ceiling bounds the damage to `CIVIC_DAILY_USD` before
you notice. Lower it, rotate, redeploy.

**Refresh the data**: rebuild `gov.db` locally, `sync.sh --db-only`, done. The
service reopens the file read-only on each query, so no coordination is needed
beyond the restart `sync.sh` already performs.

---

## What is deliberately not here

No accounts, no history persistence, no write path of any kind. The service is
read-only against `gov.db` (`mode=ro`, a SQLite authorizer, a textual prefilter
and result caps — `guard.py`), and `read_document`/`grep_repo` are confined to
the repository by a shared helper. Those properties are asserted by
`verify_phase0.sh`, `verify_phase1.py`, `verify_console.py`, `verify_gate.py`
and `verify_token_parity.php` — 182 checks. Run them all before any deploy.
