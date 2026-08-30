"""Idempotent public demo bootstrap backed by the real production database."""

from __future__ import annotations


from .errors import ConflictError
from .models import ItemStatus
from .util import generate_human_code, hash_token, new_public_ref, now


DEMO_EMAIL = "demo@whoopstag.app"
DEMO_NAME = "Whoops Tag Demo"
DEMO_LABEL = "Demo return bottle"
DEMO_DESCRIPTION = "Use this item to demonstrate the live owner/finder connection."
DEMO_SECRET = "whoopstag-demo-tag-2026"
DEMO_KEY = "judge"


def bootstrap(services) -> dict[str, str]:
    """Create or reuse a safe demo account, item, and tag, then issue a session."""
    database = services.database
    cipher = services.cipher
    email_lookup = cipher.blind_index(DEMO_EMAIL)

    with database.read() as connection:
        demo_row = connection.execute(
            "SELECT owner_ref,item_ref,tag_ref,secret_ciphertext FROM demo_records WHERE demo_key=?",
            (DEMO_KEY,),
        ).fetchone()
        user_row = connection.execute(
            "SELECT user_ref FROM users WHERE email_lookup=?",
            (email_lookup,),
        ).fetchone()

    if demo_row:
        owner_ref = demo_row["owner_ref"]
        item_ref = demo_row["item_ref"]
        secret = cipher.open(demo_row["secret_ciphertext"])
    else:
        if user_row:
            owner_ref = user_row["user_ref"]
        else:
            try:
                user, _ = services.identity.register(DEMO_EMAIL, DEMO_NAME)
                owner_ref = user.user_ref
            except ConflictError:
                with database.read() as connection:
                    owner_ref = connection.execute(
                        "SELECT user_ref FROM users WHERE email_lookup=?",
                        (email_lookup,),
                    ).fetchone()["user_ref"]

        items = services.items.list_items(owner_ref)
        demo_item = next((item for item in items if item.label == DEMO_LABEL), None)
        if demo_item:
            item_ref = demo_item.item_ref
        else:
            item_ref = services.items.create_item(
                owner_ref, DEMO_LABEL, DEMO_DESCRIPTION
            ).item_ref

        secret = DEMO_SECRET
        tag_hash = hash_token(secret)
        with database.transaction() as connection:
            tag_row = connection.execute(
                "SELECT tag_ref FROM tags WHERE secret_hash=?",
                (tag_hash,),
            ).fetchone()
            if tag_row:
                tag_ref = tag_row["tag_ref"]
            else:
                tag_ref = new_public_ref("tag")
                connection.execute(
                    "INSERT INTO tags(tag_ref,item_ref,secret_hash,human_code_hash,status,created_at) VALUES(?,?,?,?,?,?)",
                    (
                        tag_ref,
                        item_ref,
                        tag_hash,
                        hash_token(generate_human_code()),
                        "active",
                        now(),
                    ),
                )
                services.audit.record(
                    connection,
                    owner_ref,
                    "owner",
                    "tag.provisioned",
                    "tag",
                    tag_ref,
                    {"source": "demo-bootstrap"},
                )
            connection.execute(
                "INSERT INTO demo_records(demo_key,owner_ref,item_ref,tag_ref,secret_ciphertext,created_at) VALUES(?,?,?,?,?,?)",
                (DEMO_KEY, owner_ref, item_ref, tag_ref, cipher.seal(secret), now()),
            )

    session_token = services.identity.issue_session(owner_ref)
    return {
        "session_token": session_token,
        "item_ref": item_ref,
        "label": DEMO_LABEL,
        "finder_url": f"{services.settings.base_url}/f/{secret}",
    }
