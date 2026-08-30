# Whoops Tag backend

This package is the product backend foundation; `code/prototype/` remains the
one-day demo and is intentionally not imported here.

## Module boundaries

- `config.py` — environment configuration and fail-closed secrets.
- `crypto.py` — AES-GCM envelope encryption and HMAC blind indexes.
- `database.py` — SQLite/PostgreSQL schema and transaction/read contexts.
- `identity.py` — owner/authority registration, magic links, and sessions.
- `items.py` — owner inventory and revocable/replacement tags.
- `finder.py` — public tag resolution, short-lived finder sessions, and reports.
- `chat.py` — anonymous owner/finder/authority message authorization.
- `notifications.py` — encrypted push-device registration and provider adapter.
- `authority.py` — manual invitations, least-privilege cases, and transitions.
- `calling.py` — optional short-lived LiveKit room tokens.
- `audit.py` — encrypted append-only security events.
- `container.py` — dependency composition only.
- `api.py` — HTTP serialization/auth extraction only.

## Invariants

1. User UUIDs and identity/contact fields are ciphertext; blind indexes are keyed
   and the master key never enters SQLite.
2. NFC/QR uses a long random secret. The short human code is only a finder alias.
3. Finder responses never include owner identity or private item proof.
4. Owner and authority message endpoints validate their respective relationship
   before reading or writing a conversation.
5. Platform admin authorization is an out-of-band secret; no API can promote a
   normal account to platform admin.
6. Optional providers fail explicitly. Chat and item recovery do not silently
   turn into fake calling or fake push delivery.

## Local API

```sh
BEARWITHME_MASTER_KEY=<base64-32-byte-key> \
BEARWITHME_PLATFORM_ADMIN_TOKEN=<long-secret> \
python -m uvicorn code.mvp.server:app --host 0.0.0.0 --port 8000
```

Set `BEARWITHME_DATABASE` to a local SQLite path or PostgreSQL URL. If it is
unset, `DATABASE_URL` is used, then Vercel's pooled `POSTGRES_URL`; otherwise
the local default is `bearwithme-mvp.db`. PostgreSQL is the production path
for a serverless deployment; SQLite is for local development and tests.

For production, set all secrets in the hosting secret manager. Never commit
values or place provider keys in mobile or browser bundles.

## Vercel + Supabase handoff

The checked-in code is deployable, but each environment still requires its own
managed database and secrets:

1. Create a Supabase PostgreSQL project and set its **Shared Pooler transaction
   mode** URI as Vercel's `DATABASE_URL` (normally port `6543`). This is the
   IPv4-compatible serverless path; the direct `db.*:5432` URI requires IPv6 or
   Supabase's paid IPv4 add-on.
2. Set `BEARWITHME_MASTER_KEY`, `BEARWITHME_PLATFORM_ADMIN_TOKEN`,
   `BEARWITHME_BASE_URL`, and `BEARWITHME_WEB_ORIGIN` in the Vercel project.
3. Add `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` only when
   calling is enabled. Leave them unset to keep chat reliable without calling.
4. Deploy from the repository root so `vercel.json` serves the static finder,
   owner, admin, and authority surfaces and routes `/api/*` to `api/index.py`.

The function initializes the idempotent schema on startup. Use a Supabase
connection pool for serverless traffic; do not put the database URL, service
role key, encryption key, or provider secrets in browser or mobile bundles.
