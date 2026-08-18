#!/usr/bin/env bash
# Ship the repo to the civic-data VPS.
#
#   interface_prototype/deploy/sync.sh civic@1.2.3.4
#   interface_prototype/deploy/sync.sh civic@1.2.3.4 --db-only     # after a federation rebuild
#   interface_prototype/deploy/sync.sh civic@1.2.3.4 --code-only   # after editing agent/
#   interface_prototype/deploy/sync.sh civic@1.2.3.4 --dry-run
#
# WHAT SHIPS: exactly `git ls-files` plus gov.db. The repo's .gitignore already
# encodes the distinction the deployment needs — committable text stays, the
# 42 GB of re-fetchable raw/ originals and 7.7 GB of _backups/ do not — so the
# manifest is derived from git rather than maintained by hand and drifting.
#
# Payload: ~63,700 files / 1.97 GB text + 1.68 GB gov.db = ~3.65 GB.
set -euo pipefail

REMOTE="${1:-}"
MODE="${2:-}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="/srv/civic-data"

if [ -z "$REMOTE" ]; then
    echo "usage: $0 user@host [--db-only|--code-only|--dry-run]" >&2
    exit 2
fi

cd "$REPO"
DRY=""
[ "$MODE" = "--dry-run" ] && DRY="--dry-run"

RSYNC=(rsync -az --info=progress2 --human-readable $DRY)

ship_text() {
    echo "==> text layer (git ls-files)"
    # -0/--from0 so paths with spaces survive; --files-from means rsync copies
    # exactly this list and nothing else.
    git ls-files -z > /tmp/civic-manifest.z
    "${RSYNC[@]}" --files-from=/tmp/civic-manifest.z --from0 \
        ./ "$REMOTE:$DEST/"
    rm -f /tmp/civic-manifest.z
}

ship_db() {
    echo "==> gov.db (1.68 GB — delta-transferred)"
    # gov.db is rebuilt wholesale, but rsync's delta algorithm still moves far
    # less than the full file when most pages are unchanged. --partial so an
    # interrupted transfer resumes instead of restarting.
    "${RSYNC[@]}" --partial --inplace ./gov.db "$REMOTE:$DEST/gov.db"
}

ship_code() {
    echo "==> service code only"
    "${RSYNC[@]}" --delete \
        ./interface_prototype/agent/ "$REMOTE:$DEST/interface_prototype/agent/"
    "${RSYNC[@]}" ./interface_prototype/server.py ./interface_prototype/chat.html \
        ./interface_prototype/console.html "$REMOTE:$DEST/interface_prototype/"
}

case "$MODE" in
    --db-only)   ship_db ;;
    --code-only) ship_code ;;
    *)           ship_text; ship_db ;;
esac

if [ -z "$DRY" ]; then
    echo "==> restarting"
    ssh "$REMOTE" "sudo systemctl restart civic-data && sleep 2 && \
        systemctl is-active civic-data && \
        curl -sS localhost:8787/api/gate-status | head -c 400 && echo"
fi

echo "==> done"
