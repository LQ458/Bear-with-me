# Whoops Tag — one-day lost-property prototype

Tap an NFC tag on a lost item → the owner is told where it is. The finder needs no
app and no account, and never learns who the owner is.

## Run it

```
python3 app.py
```

That is the whole install. Standard library only — no pip, no API keys, no
accounts.

On start it prints the address it is actually reachable on. It auto-detects this
machine's LAN address rather than `localhost`, because **a tag encoding
`localhost` is useless — the finder's phone cannot resolve it**:

```
  Whoops Tag running:  http://10.0.0.42:8000
```

Any phone on the same wi-fi can now scan a printed label and reach it.

For a public HTTPS URL that works off cell data, use any tunnel. With Tailscale
Funnel, once enabled on your tailnet:

```
tailscale funnel --bg 8000
BASE_URL=https://your-machine.ts.net python3 app.py
```

**Set `BASE_URL` before creating any tags.** Whatever it is at creation time is
baked into that tag's QR and NFC payload; change it afterwards and every printed
label is dead. HTTPS also matters for `/write/CODE`, since Web NFC only runs on
a secure origin.

## No NFC tags? You are still fine

- **`/labels`** — printable sheet of QR labels (22 mm QR + typed code on each).
  Print at **100% scale**, do not "fit to page".
- **`/f`** — a finder types the six-character code. No NFC, no camera, no app.
- **`/write/CODE`** — if you do get a tag, write it straight from **Chrome on
  Android** via Web NFC. No writing app needed.

## The loop

1. **`/`** — create a tag. You get a six-character code.
2. **`/claim/CODE`** — shows the URL to write to the NFC sticker, plus a backup QR.
   Fill in your name to claim the tag; you get a private dashboard link.
3. **`/i/CODE`** — what the finder sees when they tap. Names the item, hides the
   owner, one button plus a building dropdown.
4. **`/o/TOKEN`** — the owner dashboard. Updates **live** over server-sent events.

Keep the dashboard open on a second phone during the demo. It pings instantly with
no external service involved, which is why it cannot fail on venue wifi or an email
delay.

## Writing the tag

Use **NFC Tools** or **NXP TagWriter** (both free):

> Write tags → New dataset → LINK → paste the URL → SAVE & WRITE → tap the tag

Test it with a *different* phone before you lock anything. Locking is permanent.

Requires NTAG213/215/216. iPhone XS and later pop a notification with no app
installed; iPhone 7+ can write tags but older models will not do the background read.

## Optional extras

Both off by default. Neither is needed for a demo.

```
WEBHOOK_URL=https://discord.com/api/webhooks/...     # also post to Discord
RESEND_API_KEY=re_...  OWNER_FROM=you@yourdomain     # also send real email
```

Do **not** use Twilio SMS for a demo: trial accounts only send to pre-verified
numbers, so a judge's phone will not receive anything.

## Customising

- `PLACES` at the top of `app.py` — the building dropdown. Put your campus in it.
- `CSS` — one string, restyle freely.

## Known limits

- A plain tag will not read on steel or aluminium. Use a ferrite on-metal tag, or
  stick it to a plastic surface.
- SQLite file `bearwithme.db` is created next to `app.py`. Delete it to reset.
- Single process, no auth beyond unguessable tokens. It is a prototype.
