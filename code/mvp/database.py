"""SQLite persistence setup and transaction boundaries.

The schema stores only opaque references in relations. Identity/contact values are
ciphertexts produced by :mod:`code.mvp.crypto`; public tag values are blind-indexed.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_ref TEXT PRIMARY KEY,
    uuid_ciphertext TEXT NOT NULL,
    uuid_lookup TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'authority')),
    name_ciphertext TEXT NOT NULL,
    email_ciphertext TEXT NOT NULL,
    email_lookup TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_hash TEXT PRIMARY KEY,
    user_ref TEXT NOT NULL REFERENCES users(user_ref) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_ref);

CREATE TABLE IF NOT EXISTS magic_links (
    token_hash TEXT PRIMARY KEY,
    user_ref TEXT NOT NULL REFERENCES users(user_ref) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    consumed_at TEXT
);

CREATE TABLE IF NOT EXISTS items (
    item_ref TEXT PRIMARY KEY,
    owner_ref TEXT NOT NULL REFERENCES users(user_ref) ON DELETE CASCADE,
    label_ciphertext TEXT NOT NULL,
    description_ciphertext TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'lost', 'recovered')),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_items_owner ON items(owner_ref, created_at DESC);

CREATE TABLE IF NOT EXISTS tags (
    tag_ref TEXT PRIMARY KEY,
    item_ref TEXT NOT NULL REFERENCES items(item_ref) ON DELETE CASCADE,
    secret_hash TEXT NOT NULL UNIQUE,
    human_code_hash TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('active', 'revoked', 'replaced')),
    replaced_by TEXT REFERENCES tags(tag_ref),
    created_at TEXT NOT NULL,
    revoked_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_tags_item ON tags(item_ref, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tags_status ON tags(status);
CREATE TABLE IF NOT EXISTS demo_records (
    demo_key TEXT PRIMARY KEY,
    owner_ref TEXT NOT NULL REFERENCES users(user_ref) ON DELETE CASCADE,
    item_ref TEXT NOT NULL REFERENCES items(item_ref) ON DELETE CASCADE,
    tag_ref TEXT NOT NULL REFERENCES tags(tag_ref) ON DELETE CASCADE,
    secret_ciphertext TEXT NOT NULL,
    created_at TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS finder_sessions (
    session_hash TEXT PRIMARY KEY,
    tag_ref TEXT NOT NULL REFERENCES tags(tag_ref) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_finder_sessions_tag ON finder_sessions(tag_ref);

CREATE TABLE IF NOT EXISTS found_events (
    found_ref TEXT PRIMARY KEY,
    tag_ref TEXT NOT NULL REFERENCES tags(tag_ref),
    item_ref TEXT NOT NULL REFERENCES items(item_ref),
    owner_ref TEXT NOT NULL REFERENCES users(user_ref),
    finder_session_hash TEXT NOT NULL REFERENCES finder_sessions(session_hash),
    place TEXT NOT NULL,
    note_ciphertext TEXT NOT NULL,
    authority_requested INTEGER NOT NULL DEFAULT 0 CHECK (authority_requested IN (0, 1)),
    organization_ciphertext TEXT,
    organization_lookup TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_found_owner ON found_events(owner_ref, created_at DESC);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_ref TEXT PRIMARY KEY,
    found_ref TEXT NOT NULL UNIQUE REFERENCES found_events(found_ref) ON DELETE CASCADE,
    owner_ref TEXT NOT NULL REFERENCES users(user_ref),
    finder_session_hash TEXT NOT NULL REFERENCES finder_sessions(session_hash),
    status TEXT NOT NULL CHECK (status IN ('open', 'closed')),
    created_at TEXT NOT NULL,
    closed_at TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    message_ref TEXT PRIMARY KEY,
    conversation_ref TEXT NOT NULL REFERENCES conversations(conversation_ref) ON DELETE CASCADE,
    sender_role TEXT NOT NULL CHECK (sender_role IN ('owner', 'finder', 'authority')),
    body_ciphertext TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_ref, created_at ASC);

CREATE TABLE IF NOT EXISTS push_devices (
    device_ref TEXT PRIMARY KEY,
    owner_ref TEXT NOT NULL REFERENCES users(user_ref) ON DELETE CASCADE,
    token_ciphertext TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    platform TEXT NOT NULL CHECK (platform IN ('ios', 'android', 'web')),
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_push_devices_owner ON push_devices(owner_ref);

CREATE TABLE IF NOT EXISTS notifications (
    notification_ref TEXT PRIMARY KEY,
    owner_ref TEXT NOT NULL REFERENCES users(user_ref),
    found_ref TEXT REFERENCES found_events(found_ref),
    payload_ciphertext TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'sent', 'failed')),
    created_at TEXT NOT NULL,
    sent_at TEXT,
    error_ciphertext TEXT
);
CREATE INDEX IF NOT EXISTS idx_notifications_owner ON notifications(owner_ref, created_at DESC);

CREATE TABLE IF NOT EXISTS authority_invites (
    invite_ref TEXT PRIMARY KEY,
    organization_ciphertext TEXT NOT NULL,
    organization_lookup TEXT NOT NULL,
    email_ciphertext TEXT NOT NULL,
    email_lookup TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    consumed_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_authority_invites_org ON authority_invites(organization_lookup);

CREATE TABLE IF NOT EXISTS authority_users (
    authority_ref TEXT PRIMARY KEY,
    user_ref TEXT NOT NULL UNIQUE REFERENCES users(user_ref) ON DELETE CASCADE,
    organization_ciphertext TEXT NOT NULL,
    organization_lookup TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'suspended')),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_authority_users_org ON authority_users(organization_lookup);

CREATE TABLE IF NOT EXISTS authority_cases (
    case_ref TEXT PRIMARY KEY,
    found_ref TEXT NOT NULL UNIQUE REFERENCES found_events(found_ref) ON DELETE CASCADE,
    organization_ciphertext TEXT NOT NULL,
    organization_lookup TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('requested', 'in_custody', 'released', 'closed')),
    custody_place_ciphertext TEXT NOT NULL,
    case_number_ciphertext TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_authority_cases_org ON authority_cases(organization_lookup, updated_at DESC);

CREATE TABLE IF NOT EXISTS audit_events (
    audit_ref TEXT PRIMARY KEY,
    actor_ref TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_ref TEXT NOT NULL,
    metadata_ciphertext TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_events(target_type, target_ref, created_at DESC);
"""

POSTGRES_SCHEMA = SCHEMA.replace("PRAGMA foreign_keys = ON;\n", "")


def _normalize_postgres_dsn(value: str) -> str:
    """Drop Vercel/Supabase routing metadata unsupported by libpq."""
    parsed = urlsplit(value)
    query = [(key, item) for key, item in parse_qsl(parsed.query, keep_blank_values=True) if key != "supa"]
    return urlunsplit(parsed._replace(query=urlencode(query)))


class _Connection:
    """Normalize the small DB-API surface used by domain services."""

    def __init__(self, raw, postgres: bool):
        self.raw = raw
        self.postgres = postgres

    def execute(self, sql: str, params=()):
        return self.raw.execute(sql.replace("?", "%s") if self.postgres else sql, params)

    def executescript(self, script: str):
        if not self.postgres:
            return self.raw.executescript(script)
        for statement in script.split(";"):
            if statement.strip():
                self.raw.execute(statement)

    def commit(self):
        return self.raw.commit()

    def rollback(self):
        return self.raw.rollback()

    def close(self):
        return self.raw.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()



class Database:
    """Own SQLite or PostgreSQL connections behind one small DB-API surface."""

    def __init__(self, path: str):
        self.path = path
        self.is_postgres = path.startswith(("postgres://", "postgresql://"))

    def connect(self) -> _Connection:
        if self.is_postgres:
            try:
                import psycopg
                from psycopg.rows import dict_row
            except ImportError as exc:
                from .errors import ConfigurationError

                raise ConfigurationError(
                    "psycopg is required when using a PostgreSQL database URL"
                ) from exc
            return _Connection(
                psycopg.connect(
                    _normalize_postgres_dsn(self.path),
                    row_factory=dict_row,
                    autocommit=False,
                    prepare_threshold=None,
                ),
                True,
            )
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return _Connection(connection, False)

    def initialize(self) -> None:
        with self.connect() as connection:
            if not self.is_postgres:
                connection.execute("PRAGMA foreign_keys = ON")
                connection.execute("PRAGMA busy_timeout = 10000")
            connection.executescript(POSTGRES_SCHEMA if self.is_postgres else SCHEMA)

    @contextmanager
    def transaction(self) -> Iterator[_Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN" if self.is_postgres else "BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @contextmanager
    def read(self) -> Iterator[_Connection]:
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()
