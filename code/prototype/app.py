#!/usr/bin/env python3
"""Whoops Tag - a one-day lost-property reunification prototype.

    python3 app.py                      # http://localhost:8000
    BASE_URL=https://xyz.ngrok.app python3 app.py

Stdlib only. No pip install, no API keys, no accounts. SQLite for storage and
server-sent events for live notification, so a live demo depends on nothing
outside this process. Optional extras, both off by default:

    WEBHOOK_URL=https://discord.com/api/webhooks/...   # also post to Discord
    RESEND_API_KEY=re_...  OWNER_FROM=you@yourdomain   # also send real email

Flow
  1.  /            create a tag, get the URL to write to the NFC sticker
  2.  /claim/CODE  owner binds the tag to themselves, gets a dashboard link
  3.  /i/CODE      finder taps phone on the item, one button notifies the owner
  4.  /o/TOKEN     owner's dashboard updates live, with no polling

The finder never sees who the owner is, and needs no app and no account.
"""

from __future__ import annotations

import json
import os
import queue
import re
import secrets
import sqlite3
import threading
import time
import urllib.request
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "bearwithme.db")
PORT = int(os.environ.get("PORT", "8000"))


def _lan_ip() -> str:
    """Best-guess LAN address of this machine.

    A tag encoding `localhost` is useless: the finder's phone cannot reach it.
    Defaulting to the LAN address means a phone on the same wi-fi works with no
    configuration. Opening a UDP socket to a public address never sends a
    packet; it just asks the kernel which interface it would route through.
    """
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


BASE_URL = os.environ.get("BASE_URL", f"http://{_lan_ip()}:{PORT}").rstrip("/")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
OWNER_FROM = os.environ.get("OWNER_FROM", "bearwithme@example.com")

# Where a finder can say they left the item. Edit for your campus.
PLACES = ["Main library", "Science library", "Student union", "Sports centre",
          "Lecture hall block", "Cafeteria", "Handed to security", "Still with me"]

_lock = threading.Lock()
_subscribers: dict[str, list[queue.Queue]] = {}


# ------------------------------------------------------------------ store --

def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS tag (
            code        TEXT PRIMARY KEY,
            label       TEXT NOT NULL DEFAULT '',
            owner_name  TEXT,
            owner_email TEXT,
            token       TEXT,
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sighting (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            code       TEXT NOT NULL,
            place      TEXT NOT NULL,
            note       TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        """)


def new_code() -> str:
    """Short, unambiguous, URL-safe. No vowels, so no accidental words."""
    alphabet = "BCDFGHJKLMNPQRSTVWXZ23456789"
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        with db() as con:
            if not con.execute("SELECT 1 FROM tag WHERE code=?", (code,)).fetchone():
                return code


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def pretty(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts).strftime("%d %b %H:%M UTC")
    except ValueError:
        return ts


# ----------------------------------------------------------- notification --

def publish(token: str, payload: dict) -> None:
    """Push an event to every open dashboard for this owner."""
    with _lock:
        subs = list(_subscribers.get(token, []))
    for q in subs:
        try:
            q.put_nowait(payload)
        except queue.Full:
            pass


def notify_external(tag: sqlite3.Row, place: str, note: str) -> None:
    """Best-effort Discord and email. Never allowed to break the request."""
    text = (f"Your {tag['label'] or 'item'} was found.\n"
            f"Where: {place}\n" + (f"Note: {note}\n" if note else "") +
            f"Dashboard: {BASE_URL}/o/{tag['token']}")
    if WEBHOOK_URL:
        try:
            req = urllib.request.Request(
                WEBHOOK_URL, data=json.dumps({"content": text}).encode(),
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=4).read()
        except Exception as exc:                                  # noqa: BLE001
            print(f"  [webhook failed: {exc}]")
    if RESEND_API_KEY and tag["owner_email"]:
        try:
            body = json.dumps({"from": OWNER_FROM, "to": [tag["owner_email"]],
                               "subject": "Someone found your item",
                               "text": text}).encode()
            req = urllib.request.Request(
                "https://api.resend.com/emails", data=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {RESEND_API_KEY}"})
            urllib.request.urlopen(req, timeout=6).read()
        except Exception as exc:                                  # noqa: BLE001
            print(f"  [email failed: {exc}]")


# ------------------------------------------------------------------- view --

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#f4f6f8;color:#12181f;font:16px/1.55 -apple-system,
BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:560px;margin:0 auto;padding:24px 20px 64px}
.card{background:#fff;border:1px solid #e3e8ee;border-radius:14px;padding:22px;
margin:16px 0;box-shadow:0 1px 2px rgba(18,24,31,.04)}
h1{font-size:1.55rem;margin:.2em 0 .1em;letter-spacing:-.01em}
h2{font-size:1.05rem;margin:1.4em 0 .3em}
p{margin:.6em 0}
.muted{color:#5b6673;font-size:.92rem}
.big{font-size:2.1rem;font-weight:750;letter-spacing:-.02em;margin:.1em 0}
label{display:block;font-weight:620;font-size:.86rem;margin:14px 0 5px;
letter-spacing:.02em}
input,select,textarea{width:100%;padding:12px 13px;border:1px solid #cdd5de;
border-radius:9px;font:inherit;background:#fff}
textarea{min-height:76px;resize:vertical}
button{width:100%;padding:15px;border:0;border-radius:10px;background:#2f5d9e;
color:#fff;font:inherit;font-weight:680;cursor:pointer;margin-top:18px}
button:active{transform:translateY(1px)}
button.alt{background:#12181f}
a{color:#2f5d9e}
code{background:#eef1f5;padding:2px 6px;border-radius:5px;font-size:.9em;
word-break:break-all}
.ok{background:#f1f8f4;border-color:#cbe4d6}
.warn{background:#fdf5f0;border-color:#f0d8c8}
.row{display:flex;gap:10px;align-items:center}
.dot{width:9px;height:9px;border-radius:50%;background:#3f8f6b;flex:none}
ul.feed{list-style:none;padding:0;margin:8px 0 0}
ul.feed li{padding:12px 0;border-top:1px solid #eef1f5}
ul.feed li:first-child{border-top:0}
.tagline{display:flex;justify-content:space-between;gap:12px;padding:10px 0;
border-top:1px solid #eef1f5;align-items:center}
img.qr{width:170px;height:170px;image-rendering:pixelated;background:#fff}
"""


def page(title: str, body: str, head: str = "") -> bytes:
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{escape(title)}</title><style>{CSS}</style>{head}</head>"
            f"<body><div class=wrap>{body}</div></body></html>").encode()


def qr_svg(data: str) -> str | None:
    """Return an inline SVG QR, or None. Never raises: the QR is only a backup,
    so a missing dependency must not take the page down mid-demo."""
    try:
        import io                                                 # noqa: PLC0415

        import segno                                              # noqa: PLC0415
        buf = io.BytesIO()
        segno.make(data, error="m").save(buf, kind="svg", scale=4, border=2,
                                         dark="#12181f", light="#ffffff",
                                         xmldecl=False, svgns=True)
        return buf.getvalue().decode("utf-8")
    except Exception as exc:                                      # noqa: BLE001
        print(f"  [qr unavailable: {exc}]")
        return None


# ---------------------------------------------------------------- handler --

class App(BaseHTTPRequestHandler):
    server_version = "bearwithme"

    def log_message(self, fmt: str, *args) -> None:
        print(f"  {self.address_string()} {fmt % args}")

    # -- helpers --
    def send(self, body: bytes, status: int = 200,
             ctype: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, to: str) -> None:
        self.send_response(303)
        self.send_header("Location", to)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def form(self) -> dict[str, str]:
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode("utf-8", "replace")
        return {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}

    # -- routing --
    def do_GET(self) -> None:                                     # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/":
            return self.home()
        if m := re.fullmatch(r"/i/([A-Z0-9]{6})", path):
            return self.finder(m.group(1))
        if m := re.fullmatch(r"/claim/([A-Z0-9]{6})", path):
            return self.claim_form(m.group(1))
        if m := re.fullmatch(r"/o/([A-Za-z0-9_-]{16,})", path):
            return self.dashboard(m.group(1))
        if m := re.fullmatch(r"/o/([A-Za-z0-9_-]{16,})/stream", path):
            return self.stream(m.group(1))
        if path == "/labels":
            return self.labels()
        if path == "/f":
            return self.type_code()
        if m := re.fullmatch(r"/write/([A-Z0-9]{6})", path):
            return self.web_writer(m.group(1))
        if m := re.fullmatch(r"/qr/([A-Z0-9]{6})\.svg", path):
            return self.qr(m.group(1))
        self.send(page("Not found", "<div class=card><h1>Not found</h1></div>"), 404)

    def do_POST(self) -> None:                                    # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/new":
            return self.create_tag()
        if m := re.fullmatch(r"/i/([A-Z0-9]{6})/found", path):
            return self.found(m.group(1))
        if m := re.fullmatch(r"/claim/([A-Z0-9]{6})", path):
            return self.claim(m.group(1))
        self.send(page("Not found", "<div class=card><h1>Not found</h1></div>"), 404)

    # -- pages --
    def home(self) -> None:
        with db() as con:
            tags = con.execute("SELECT * FROM tag ORDER BY created_at DESC").fetchall()
        rows = []
        for t in tags:
            who = escape(t["owner_name"]) if t["owner_name"] else \
                "<span class=muted>unclaimed</span>"
            link = f"/o/{t['token']}" if t["token"] else f"/claim/{t['code']}"
            rows.append(
                f"<div class=tagline><div><b>{escape(t['label'] or 'Untitled')}</b><br>"
                f"<span class=muted>{t['code']} &middot; {who}</span></div>"
                f"<a href='{link}'>open</a></div>")
        listing = "".join(rows) or "<p class=muted>No tags yet.</p>"
        self.send(page("Whoops Tag admin", f"""
        <h1>Whoops Tag</h1>
        <p class=muted>Write the tag URL to an NFC sticker, or
        <a href="/labels">print QR labels</a> if you have no tags. Then claim it.</p>
        <div class=card>
          <h2>New tag</h2>
          <form method=post action=/new>
            <label for=label>What is it?</label>
            <input id=label name=label placeholder="Blue water bottle" required>
            <button>Create tag</button>
          </form>
        </div>
        <div class=card><h2>Tags</h2>{listing}</div>"""))

    def create_tag(self) -> None:
        label = (self.form().get("label") or "").strip()[:60]
        code = new_code()
        with db() as con:
            con.execute("INSERT INTO tag(code,label,created_at) VALUES(?,?,?)",
                        (code, label, now()))
        self.redirect(f"/claim/{code}")

    def claim_form(self, code: str) -> None:
        with db() as con:
            tag = con.execute("SELECT * FROM tag WHERE code=?", (code,)).fetchone()
        if not tag:
            return self.send(page("Unknown", "<div class=card>Unknown tag.</div>"), 404)
        if tag["token"]:
            return self.redirect(f"/o/{tag['token']}")
        url = f"{BASE_URL}/i/{code}"
        svg = qr_svg(url)
        qr_block = (f"<p class=muted>Backup QR, in case NFC fails:</p>{svg}"
                    if svg else "")
        self.send(page("Claim tag", f"""
        <h1>Claim this tag</h1>
        <div class="card warn">
          <h2>1. Write this to the NFC sticker</h2>
          <p><code>{escape(url)}</code></p>
          <p class=muted>On <b>Chrome for Android</b> you can write it straight from
          the browser: <a href="/write/{code}">write this tag now</a>. Otherwise use
          NFC Tools or NXP TagWriter: new record &rarr; URL &rarr; paste &rarr;
          write. Do not lock the tag until you have tested it.</p>
          <p class=muted>No NFC at all? Print the code <b>{code}</b> on the label.
          A finder can enter it at <code>{escape(BASE_URL)}/f</code>.</p>
          {qr_block}
        </div>
        <div class=card>
          <h2>2. Tell us where to send finds</h2>
          <form method=post action=/claim/{code}>
            <label for=name>Your name</label>
            <input id=name name=name placeholder="Alex" required>
            <label for=email>Email (optional)</label>
            <input id=email name=email type=email placeholder="alex@uni.edu">
            <label for=label2>Item</label>
            <input id=label2 name=label value="{escape(tag['label'] or '')}"
                   placeholder="Blue water bottle">
            <button>Claim tag</button>
          </form>
        </div>"""))

    def claim(self, code: str) -> None:
        f = self.form()
        token = secrets.token_urlsafe(18)
        with db() as con:
            tag = con.execute("SELECT * FROM tag WHERE code=?", (code,)).fetchone()
            if not tag:
                return self.send(page("Unknown", "<div class=card>Unknown.</div>"), 404)
            if tag["token"]:
                return self.redirect(f"/o/{tag['token']}")
            con.execute("UPDATE tag SET owner_name=?,owner_email=?,label=?,token=? "
                        "WHERE code=?",
                        ((f.get("name") or "").strip()[:60],
                         (f.get("email") or "").strip()[:120],
                         (f.get("label") or "").strip()[:60], token, code))
        self.redirect(f"/o/{token}")

    def finder(self, code: str) -> None:
        with db() as con:
            tag = con.execute("SELECT * FROM tag WHERE code=?", (code,)).fetchone()
        if not tag:
            return self.send(page("Unknown", "<div class=card><h1>Unknown tag</h1>"
                                             "</div>"), 404)
        if not tag["token"]:
            return self.redirect(f"/claim/{code}")
        item = escape(tag["label"] or "item")
        opts = "".join(f"<option>{escape(p)}</option>" for p in PLACES)
        self.send(page("Found something?", f"""
        <h1>Thanks for picking this up</h1>
        <div class=card>
          <p>This <b>{item}</b> belongs to a student here. They have been told it
          is missing.</p>
          <p class=muted>You will not see who they are, and they will not see who
          you are. Just tell them where it is.</p>
          <form method=post action=/i/{code}/found>
            <label for=place>Where is it now?</label>
            <select id=place name=place>{opts}</select>
            <label for=note>Anything else? (optional)</label>
            <textarea id=note name=note
                      placeholder="Left it with the front desk"></textarea>
            <button>Tell the owner</button>
          </form>
        </div>"""))

    def found(self, code: str) -> None:
        f = self.form()
        place = (f.get("place") or "Somewhere on campus").strip()[:80]
        note = (f.get("note") or "").strip()[:300]
        with db() as con:
            tag = con.execute("SELECT * FROM tag WHERE code=?", (code,)).fetchone()
            if not tag or not tag["token"]:
                return self.send(page("Unknown", "<div class=card>Unknown.</div>"), 404)
            con.execute("INSERT INTO sighting(code,place,note,created_at) "
                        "VALUES(?,?,?,?)", (code, place, note, now()))
        print(f"  FOUND {code} at {place!r}")
        publish(tag["token"], {"place": place, "note": note, "at": now()})
        threading.Thread(target=notify_external, args=(tag, place, note),
                         daemon=True).start()
        self.send(page("Sent", f"""
        <h1>Done &mdash; thank you</h1>
        <div class="card ok">
          <p>The owner has just been told their <b>{escape(tag['label'] or 'item')}</b>
          is at <b>{escape(place)}</b>.</p>
          <p class=muted>You can put it down now. Nothing else needed.</p>
        </div>"""))

    def dashboard(self, token: str) -> None:
        with db() as con:
            tag = con.execute("SELECT * FROM tag WHERE token=?", (token,)).fetchone()
            if not tag:
                return self.send(page("Unknown", "<div class=card>Unknown.</div>"), 404)
            seen = con.execute("SELECT * FROM sighting WHERE code=? "
                               "ORDER BY id DESC LIMIT 25", (tag["code"],)).fetchall()
        feed = "".join(
            f"<li><b>{escape(s['place'])}</b><br>"
            + (f"{escape(s['note'])}<br>" if s["note"] else "")
            + f"<span class=muted>{pretty(s['created_at'])}</span></li>"
            for s in seen) or "<li class=muted>Nothing yet. Waiting.</li>"
        url = f"{BASE_URL}/i/{tag['code']}"
        self.send(page(f"{tag['label'] or 'Item'} - Whoops Tag", f"""
        <h1>{escape(tag['label'] or 'Your item')}</h1>
        <p class=muted>Tag <code>{tag['code']}</code> &middot; keep this page open
        during the demo.</p>
        <div class=card>
          <div class=row><span class=dot id=dot></span>
          <span class=muted id=status>Live &mdash; listening for finds</span></div>
          <ul class=feed id=feed>{feed}</ul>
        </div>
        <div class=card>
          <h2>Tag URL</h2><p><code>{escape(url)}</code></p>
          <p class=muted>Write this to the sticker. Open it yourself to simulate a
          finder.</p>
        </div>
        <script>
        const feed=document.getElementById('feed');
        const es=new EventSource('/o/{token}/stream');
        es.onmessage=e=>{{
          const d=JSON.parse(e.data);
          if(!d.place) return;
          const li=document.createElement('li');
          li.innerHTML='<b>'+d.place+'</b><br>'+(d.note?d.note+'<br>':'')+
                       '<span class=muted>just now</span>';
          if(feed.firstChild&&feed.firstChild.classList&&
             feed.firstChild.classList.contains('muted')) feed.innerHTML='';
          feed.prepend(li);
          document.getElementById('status').textContent='Found! Just now.';
          if(navigator.vibrate) navigator.vibrate([200,80,200]);
        }};
        es.onerror=()=>{{document.getElementById('status').textContent=
          'Reconnecting...';}};
        </script>"""))

    def stream(self, token: str) -> None:
        q: queue.Queue = queue.Queue(maxsize=32)
        with _lock:
            _subscribers.setdefault(token, []).append(q)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            while True:
                try:
                    item = q.get(timeout=15)
                    payload = json.dumps(item)
                except queue.Empty:
                    payload = "{}"                      # keep-alive ping
                self.wfile.write(f"data: {payload}\n\n".encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with _lock:
                subs = _subscribers.get(token, [])
                if q in subs:
                    subs.remove(q)

    def labels(self) -> None:
        """Printable sheet of QR + code labels. The no-NFC-hardware fallback.

        Each label carries a QR and the human-readable code, so a finder can
        scan it, or type the code at /f if their camera will not cooperate.
        """
        with db() as con:
            tags = con.execute("SELECT * FROM tag ORDER BY created_at DESC "
                               "LIMIT 24").fetchall()
        cells = []
        host = re.sub(r"^https?://", "", BASE_URL)
        for t in tags:
            url = f"{BASE_URL}/i/{t['code']}"
            svg = qr_svg(url) or "<div class=noqr>QR unavailable</div>"
            cells.append(
                f"<div class=lab><div class=q>{svg}</div>"
                f"<div class=t><b>Found this?</b><br>"
                f"<span class=c>{t['code']}</span><br>"
                f"<span class=u>{escape(host)}/f</span></div></div>")
        grid = "".join(cells) or "<p>No tags yet. Create some first.</p>"
        self.send(page("Print labels", f"""
        <style>
        @media print{{.noprint{{display:none}}body{{background:#fff}}
          .wrap{{max-width:none;padding:0}}}}
        .sheet{{display:flex;flex-wrap:wrap;gap:6mm}}
        .lab{{width:30mm;border:1px dashed #bbb;border-radius:2mm;padding:2mm;
          display:flex;flex-direction:column;align-items:center;gap:1mm;
          background:#fff;break-inside:avoid;text-align:center}}
        .lab .q svg{{width:22mm;height:22mm;display:block}}
        .lab .t{{font-size:6.4pt;line-height:1.25;width:100%}}
        .lab .c{{font-size:10pt;font-weight:700;letter-spacing:.08em;
          white-space:nowrap;font-family:ui-monospace,Menlo,Consolas,monospace}}
        .lab .u{{font-size:5.6pt;color:#555;word-break:break-all}}
        .noqr{{width:22mm;height:22mm;border:1px solid #ccc;font-size:6pt}}
        </style>
        <div class=noprint>
          <h1>Printable labels</h1>
          <p class=muted>QR is 22 mm here, comfortably above the ~20 mm floor for
          reliable phone scanning. Print at 100% scale &mdash; do not
          \u201cfit to page\u201d, it shrinks the code. Then laminate or cover with
          clear tape.</p>
          <button onclick="window.print()">Print</button>
          <p class=muted>Each label also carries the typed-code fallback, so it
          still works with no NFC and no camera.</p>
        </div>
        <div class=sheet>{grid}</div>"""))

    def type_code(self) -> None:
        """Last-resort fallback: no NFC, no camera, just type the code."""
        q = parse_qs(urlparse(self.path).query).get("c", [""])[0].strip().upper()
        if re.fullmatch(r"[A-Z0-9]{6}", q):
            return self.redirect(f"/i/{q}")
        self.send(page("Enter a code", """
        <h1>Found something?</h1>
        <div class=card>
          <p>Type the six characters printed on the tag.</p>
          <form method=get action=/f>
            <label for=c>Code</label>
            <input id=c name=c placeholder="MXFNV8" autocapitalize=characters
                   autocomplete=off required
                   style="font-size:1.6rem;letter-spacing:.22em;text-align:center">
            <button>Continue</button>
          </form>
          <p class=muted>Works with no NFC, no camera and no app.</p>
        </div>"""))

    def web_writer(self, code: str) -> None:
        """Write the tag straight from Chrome on Android. No NFC app needed.

        Uses the Web NFC API (NDEFReader.write), which needs HTTPS and Chrome
        for Android. Silently unavailable elsewhere, so we say so up front.
        """
        url = f"{BASE_URL}/i/{code}"
        self.send(page("Write tag", f"""
        <h1>Write this tag</h1>
        <div class=card>
          <p>Encoding <code>{escape(url)}</code></p>
          <p class=muted id=sup>Checking browser support&hellip;</p>
          <button id=go disabled>Hold a tag to the phone, then tap here</button>
          <p id=out></p>
        </div>
        <div class=card>
          <h2>If this is not supported</h2>
          <p class=muted>Web NFC is Chrome for Android only, and needs HTTPS.
          On iPhone or desktop, use the NFC Tools or NXP TagWriter app and paste
          the URL above.</p>
        </div>
        <script>
        const sup=document.getElementById('sup'), go=document.getElementById('go'),
              out=document.getElementById('out');
        if('NDEFReader' in window){{
          sup.textContent='Web NFC supported. Ready to write.';
          go.disabled=false;
          go.onclick=async()=>{{
            out.textContent='Hold the tag against the back of the phone\\u2026';
            try{{
              const w=new NDEFReader();
              await w.write({{records:[{{recordType:'url',data:{json.dumps(url)}}}]}});
              out.innerHTML='<b>Written.</b> Now tap it with another phone to test.';
            }}catch(e){{ out.textContent='Failed: '+e.message; }}
          }};
        }} else {{
          sup.textContent='This browser cannot write NFC tags. Use Chrome on '+
            'Android over HTTPS, or write the URL with an NFC app.';
        }}
        </script>"""))

    def qr(self, code: str) -> None:
        svg = qr_svg(f"{BASE_URL}/i/{code}")
        if svg is None:
            return self.send(b"segno not installed", 501, "text/plain")
        self.send(svg.encode(), 200, "image/svg+xml")


def main() -> None:
    init_db()
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), App)
    srv.daemon_threads = True
    print(f"\n  Whoops Tag running:  {BASE_URL}")
    print(f"  Admin:            {BASE_URL}/")
    print(f"  Webhook: {'on' if WEBHOOK_URL else 'off'}   "
          f"Email: {'on' if RESEND_API_KEY else 'off'}\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  bye")


if __name__ == "__main__":
    main()
