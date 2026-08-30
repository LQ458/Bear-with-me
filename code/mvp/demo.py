"""Idempotent recording workspace bootstrap backed by the real database."""

from __future__ import annotations

from .errors import ConflictError
from .util import generate_human_code, hash_token, new_public_ref, now


RECORDING_EMAIL = "recording@whoopstag.app"
RECORDING_NAME = "Whoops Tag Owner"
RECORDING_ITEMS = (
    (
        "recording-water-bottle",
        "Blue water bottle",
        "A blue water bottle with a Whoops Tag attached.",
        "whoopstag-blue-water-bottle-2026",
    ),
    (
        "recording-black-backpack",
        "Black backpack",
        "A black backpack with a Whoops Tag attached.",
        "whoopstag-black-backpack-2026",
    ),
)


def bootstrap(services) -> dict:
    """Create or reuse the recording owner, inventory, and finder tags."""
    database = services.database
    cipher = services.cipher
    email_lookup = cipher.blind_index(RECORDING_EMAIL)

    with database.read() as connection:
        user_row = connection.execute(
            "SELECT user_ref FROM users WHERE email_lookup=?",
            (email_lookup,),
        ).fetchone()

    if user_row:
        owner_ref = user_row["user_ref"]
    else:
        try:
            user, _ = services.identity.register(RECORDING_EMAIL, RECORDING_NAME)
            owner_ref = user.user_ref
        except ConflictError:
            with database.read() as connection:
                owner_ref = connection.execute(
                    "SELECT user_ref FROM users WHERE email_lookup=?",
                    (email_lookup,),
                ).fetchone()["user_ref"]

    records = []
    for recording_key, label, description, secret in RECORDING_ITEMS:
        with database.read() as connection:
            record = connection.execute(
                "SELECT item_ref,tag_ref,secret_ciphertext FROM demo_records WHERE demo_key=?",
                (recording_key,),
            ).fetchone()

        if record:
            item_ref = record["item_ref"]
        else:
            items = services.items.list_items(owner_ref)
            item = next((item for item in items if item.label == label), None)
            item_ref = item.item_ref if item else services.items.create_item(
                owner_ref, label, description
            ).item_ref

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
                        {"source": "recording-bootstrap"},
                    )
                connection.execute(
                    "INSERT INTO demo_records(demo_key,owner_ref,item_ref,tag_ref,secret_ciphertext,created_at) VALUES(?,?,?,?,?,?)",
                    (recording_key, owner_ref, item_ref, tag_ref, cipher.seal(secret), now()),
                )

        records.append(
            {
                "item_ref": item_ref,
                "label": label,
                "finder_url": f"{services.settings.base_url}/f/{secret}",
            }
        )

    session_token = services.identity.issue_session(owner_ref)
    return {
        "session_token": session_token,
        "items": records,
        "item_ref": records[0]["item_ref"],
        "label": records[0]["label"],
        "finder_url": records[0]["finder_url"],
    }
