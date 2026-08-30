#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
ENV_DIR="$(mktemp -d "${TMPDIR:-/tmp}/whoopstag-production.XXXXXX")"
ENV_FILE="$ENV_DIR/production.env"
trap 'rm -rf "$ENV_DIR"' EXIT

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  }
}

require_command vercel
UV_BIN="${UV_BIN:-$(command -v uv || true)}"
if [[ -z "$UV_BIN" && -x "$HOME/.local/bin/uv" ]]; then
  UV_BIN="$HOME/.local/bin/uv"
fi
[[ -n "$UV_BIN" ]] || {
  printf 'Missing required command: uv\n' >&2
  exit 1
}

if [[ "${WHOOPSTAG_CONFIRM_RESET:-}" != "1" ]]; then
  printf 'This clears production chat history, found reports, notifications, and finder sessions.\n'
  printf 'It keeps the tagged Black backpack, removes added test items, and restores the baseline to active.\n'
  printf 'Type RESET_RECORDING to continue: '
  read -r confirmation
  [[ "$confirmation" == "RESET_RECORDING" ]] || {
    printf 'Reset cancelled.\n'
    exit 1
  }
fi
cd "$REPO_DIR"

printf 'Pulling the production database connection temporarily…\n'
vercel env pull "$ENV_FILE" --environment production >/dev/null

printf 'Clearing recording data…\n'
RESET_FILE="$ENV_FILE" "$UV_BIN" run --no-project --with 'psycopg[binary]>=3.2.0' python3 -c '
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg

env_file = os.environ["RESET_FILE"]
postgres_url = None
for line in open(env_file, encoding="utf-8"):
    if line.startswith("POSTGRES_URL="):
        postgres_url = line.split("=", 1)[1].strip().strip("\"")
        break
if not postgres_url:
    raise SystemExit("POSTGRES_URL was not found in the production environment")

parts = urlsplit(postgres_url)
postgres_url = urlunsplit(parts._replace(
    query=urlencode([(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "supa"])
))

with psycopg.connect(postgres_url) as connection:
    with connection.transaction():
        row = connection.execute(
            "SELECT owner_ref,item_ref FROM demo_records WHERE demo_key=%s LIMIT 1",
            ("recording-black-backpack",),
        ).fetchone()
        if not row:
            raise SystemExit("recording owner baseline was not found")
        owner_ref,keep_item_ref = row
        connection.execute("DELETE FROM notifications WHERE owner_ref=%s", (owner_ref,))
        connection.execute(
            "DELETE FROM messages WHERE conversation_ref IN "
            "(SELECT conversation_ref FROM conversations WHERE owner_ref=%s)",
            (owner_ref,),
        )
        connection.execute("DELETE FROM conversations WHERE owner_ref=%s", (owner_ref,))
        connection.execute("DELETE FROM found_events WHERE owner_ref=%s", (owner_ref,))
        connection.execute(
            "DELETE FROM finder_sessions WHERE tag_ref IN "
            "(SELECT tag_ref FROM tags WHERE item_ref IN "
            "(SELECT item_ref FROM items WHERE owner_ref=%s))",
            (owner_ref,),
        )
        connection.execute(
            "DELETE FROM demo_records WHERE owner_ref=%s AND item_ref<>%s",
            (owner_ref,keep_item_ref),
        )
        connection.execute(
            "DELETE FROM tags WHERE item_ref IN "
            "(SELECT item_ref FROM items WHERE owner_ref=%s AND item_ref<>%s)",
            (owner_ref,keep_item_ref),
        )
        connection.execute(
            "DELETE FROM items WHERE owner_ref=%s AND item_ref<>%s",
            (owner_ref,keep_item_ref),
        )
        connection.execute("UPDATE items SET status=%s WHERE item_ref=%s", ("active",keep_item_ref))
        print("Production recording data reset.")
'

printf 'Done. The baseline Black backpack is active and added test items are removed.\n'
