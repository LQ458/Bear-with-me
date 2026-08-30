"""Owner push-device registration and provider-neutral notifications."""

from __future__ import annotations
import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from .config import Settings
from .crypto import Cipher
from .database import Database
from .errors import ProviderUnavailable, ValidationError
from .models import FoundReport
from .util import clean_text, hash_token, new_public_ref, now


@dataclass(frozen=True)
class PushResult:
    device_ref: str
    status: str


class PushSender:
    def send(self, token: str, payload: dict) -> None:
        raise NotImplementedError


class ExpoPushSender(PushSender):
    def __init__(self, settings: Settings):
        self.settings = settings

    def send(self, token: str, payload: dict) -> None:
        if not self.settings.push_url:
            raise ProviderUnavailable("push provider is not configured")
        request = urllib.request.Request(
            self.settings.push_url,
            data=json.dumps({"to": token, **payload}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                if response.status >= 300:
                    raise ProviderUnavailable("push provider rejected notification")
                body = json.loads(response.read() or b"{}")
                result = body.get("data", {})
                if not isinstance(result, dict) or result.get("status") != "ok":
                    raise ProviderUnavailable("push provider rejected notification")
        except (OSError, urllib.error.URLError, ValueError) as exc:
            raise ProviderUnavailable("push provider unavailable") from exc


class MemoryPushSender(PushSender):
    """Deterministic sender used by tests and local smoke scenarios."""

    def __init__(self):
        self.sent: list[tuple[str, dict]] = []

    def send(self, token: str, payload: dict) -> None:
        self.sent.append((token, payload))


class NotificationService:
    def __init__(self, database: Database, cipher: Cipher, sender: PushSender):
        self.database = database
        self.cipher = cipher
        self.sender = sender

    def register_device(self, owner_ref: str, token: str, platform: str) -> str:
        token = clean_text(token, "push token", 512)
        if platform not in {"ios", "android", "web"}:
            raise ValidationError("platform must be ios, android, or web")
        device_ref = new_public_ref("dev")
        token_hash = hash_token(token)
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO push_devices(device_ref,owner_ref,token_ciphertext,token_hash,platform,created_at,last_seen_at) "
                "VALUES(?,?,?,?,?,?,?) ON CONFLICT(token_hash) DO UPDATE SET owner_ref=excluded.owner_ref,platform=excluded.platform,last_seen_at=excluded.last_seen_at",
                (device_ref, owner_ref, self.cipher.seal(token), token_hash, platform, now(), now()),
            )
            row = connection.execute(
                "SELECT device_ref FROM push_devices WHERE token_hash=?", (token_hash,)
            ).fetchone()
        return row["device_ref"]

    def notify_found(self, report: FoundReport) -> list[PushResult]:
        payload = {
            "title": "Whoops Tag",
            "body": "Someone reported your item found.",
            "data": {
                "found_ref": report.found_ref,
                "conversation_ref": report.conversation_ref,
            },
        }
        with self.database.read() as connection:
            devices = connection.execute(
                "SELECT device_ref,token_ciphertext FROM push_devices WHERE owner_ref=?",
                (report.owner_ref,),
            ).fetchall()
        results: list[PushResult] = []
        for device in devices:
            notification_ref = new_public_ref("ntf")
            status = "queued"
            error = ""
            try:
                self.sender.send(self.cipher.open(device["token_ciphertext"]), payload)
                status = "sent"
            except ProviderUnavailable as exc:
                status = "failed"
                error = str(exc)
            with self.database.transaction() as connection:
                connection.execute(
                    "INSERT INTO notifications(notification_ref,owner_ref,found_ref,payload_ciphertext,status,created_at,sent_at,error_ciphertext) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (
                        notification_ref,
                        report.owner_ref,
                        report.found_ref,
                        self.cipher.seal(json.dumps(payload, sort_keys=True)),
                        status,
                        now(),
                        now() if status == "sent" else None,
                        self.cipher.seal(error) if error else None,
                    ),
                )
            results.append(PushResult(device["device_ref"], status))
        return results
