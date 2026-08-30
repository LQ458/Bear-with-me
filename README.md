# Whoops Tag

Lost-property reunification for university campuses. A cheap passive label on an
ordinary item; a finder taps or scans it with no app; the owner is notified;
neither side learns who the other is.

**This file is the main document.** Everything else in the project is either
evidence feeding it or code implementing it. Edit this file; do not let the plan
live in chat.

**Deadline:** Sunday 30 August 2026, 08:00.

---

> ### Resuming work, or handing this to someone new
>
> **Read this file top to bottom first.** It is deliberately self-sufficient:
> every decision below carries the evidence and the source that produced it, so
> nothing important lives only in a chat log or in someone's head.
>
> Then, in order:
>
> 1. **§8 Open decisions** — what is unresolved right now, and the one item
>    flagged as the riskiest untested assumption in the project.
> 2. **§7 Current state** — what is built, what is verified, and how to run it
>    so a phone can actually reach it.
> 3. **§9 Evidence index** — nine reports. Open one only when you need to
>    challenge a specific number; the headline figures are quoted inline here.
>
> If a claim in this file is not followed by a source, treat it as unverified
> and check it before putting it in front of a judge.

## Where everything lives

```
bear-with-me/
├── README.md                 you are here — plan, decisions, evidence index
├── LICENSE                   MIT
├── code/
│   ├── prototype/            the working demo
│   │   ├── app.py            single-file server, stdlib only
│   │   └── README.md         how to run it, write tags, and demo it
│   └── reportgen/            toolchain that generates the reports
│       ├── charts.py         dependency-free SVG charts
│       ├── shell.py          page CSS, layout, and the REPORTS output path
│       ├── data*.py          verified source data, one module per report
│       └── build_*.py        one builder per report
└── reports/                  generated HTML — offline, self-contained
```

**Run the demo**

```
python3 code/prototype/app.py
```

Stdlib only — no pip, no keys, no accounts. It prints the LAN address it is
actually reachable on, so a phone on the same wi-fi can scan a label
immediately. See [`code/prototype/README.md`](code/prototype/README.md) for
tunnels and tag writing.

**Rebuild every report**

```
for f in code/reportgen/build_*.py; do python3 "$f"; done
```

Reports are written to `reports/`. The output directory is defined once, as
`REPORTS` in `code/reportgen/shell.py` — change it there, not in nine builders.

---

## 1. What we are building, in one paragraph

A **soft NFC inlay, 0.11&ndash;0.2 mm thick**, goes *inside* an ordinary personal
item — sewn into a hoodie seam, laminated under a care label, tucked inside the
lid of an AirPods case. Nothing sticks out and nothing looks different. A finder
taps it with no app and no account. The code resolves against the **university's
own identity system**. The owner is notified in real time. **Neither party learns
who the other is.**

Two things follow from that, and they are the whole product:

- **It is invisible**, so people will actually put it on things they care about
  how they look. Every competitor is a rigid sticker on the outside.
- **It costs about $0.27**, so you tag everything you own rather than one
  precious object.

A printed QR stays as the fallback for anything that cannot take an inlay, and
for phones that will not tap.

**The one sentence that survived every check:**

> Consumer tags make an item say *call this stranger*. Lost-property software
> helps staff sort things that already reached a desk. **We make the item say
> *I belong to a student at this university*** — to the university, which
> already has a way to reach them, and already has the item.

---

## 2. "Is it too simple? We're just slapping an NFC tag on a label."

Answering this properly, because it is the right question and the framing inside
it is wrong.

### The mechanism is simple. That is not the defect you think it is.

You are correct that tag-plus-scan-plus-notify is trivial, and the prior-art work
proves it: **seven verified products already sell it for about a dollar**, Apple
and Samsung and Tile all ship a version, and **students at UVA have sold 900+
NFC stickers at $2.50**. If your pitch is "we invented the NFC sticker" you will
be beaten by someone naming a competitor from the audience.

### But "slapping an NFC tag on a label" is the wrong description of the product.

Three things in the evidence say the hardware was never the interesting part:

- **Cost.** A passive tag is $0.24–0.58 at volume against $24.99–34.99 for a
  Bluetooth tracker — 43× to 60× cheaper, no battery. The cheap tag is a
  *consequence* of the design, not the invention.
- **Physics.** A tracker answers *where is it*. It does not answer *how do I get
  it back*. Samsung concedes accuracy collapses when a tag is "in a drawer,
  behind a wall, or in a car" — a lost-property drawer is all three. At the exact
  moment your item is most findable, the expensive device is at its worst.
- **The actual failure.** UT Austin **auctions roughly 350 recovered bikes a
  year** because it cannot trace them. The university has the property. The owner
  wants it. The university holds that owner's contact details. It is sold anyway.
  Nothing about that is a hardware problem.

### So what is the thing that is actually hard?

**Nobody has connected the item to the institution.** That claim survived two
full rounds of prior-art research against roughly 90 sources:

- Every consumer tag sells to an individual and knows nothing about a campus.
- Every institutional lost-property platform — Chargerback, RepoApp, NotLost,
  Pixit, ReclaimHub, Troov, Nova Find, MissingX — **begins only when an item
  already reached a staff desk.**
- Bike registries do the item-side half properly, at real scale, on real
  campuses — **but only for bicycles**.

The gap is narrow and it is real. Build for the gap, not for the tag.

### The simplicity is the thesis. Say it out loud.

The pitch is not "look at our clever tag". It is: **the hard part was never the
hardware, which is why a two-cent label beats a $29 tracker.** A simple
mechanism that closes a documented institutional failure is a stronger story
than a complicated one that does not.

### What makes this a better-than-average hackathon project

Not the idea. The evidence. Most teams bring an assertion; you can bring
Boise State's own policy table reading **"Will Not Accept — Immediate
Disposal"** next to Texas A&M reuniting **573 of 1,675 items** when it has
something to work with. That contrast is the project.

---

## 3. Form factor: tiny, soft, invisible

This is the real differentiator, and it is **not** "small". Small is taken.
What is not taken is **soft, thin and hidden**.

### Small is already claimed. Do not lead with it.

Every dimension below is from the vendor's own page.

| Product | Size | Targets small electronics? |
|---|---|---|
| **ReturnMe Mini** | **20.3 × 10.2 mm** | sunglasses, phones, wallets |
| **Boomerang Mini** | **21 × 25 mm** | *"fits between the AirPod 2 charger port and light"* |
| **SeQR** | **25.4 × 19.05 mm** | *"wallet, laptop, tablet, phone, **AirPods**"* |
| If Found Standard | 25 × 25 mm, IP67 | electronics pack of 3 |
| Pebblebee Link | 27.5 × 27.5 mm | water bottles, books |
| **Papertags** (UVA) | **50.8 × 50.8 mm** | the genuinely huge one |

For scale: an AirPods Pro 2 case is **45.2 × 60.7 mm**, each earbud
**30.9 × 21.8 × 24.0 mm**. Three shipping products already fit that case and
**two name AirPods in their own marketing.** If you claim "small enough for
AirPods" on stage, someone can pull up SeQR's page and read it back to you.

### What nobody sells: soft, sub-millimetre, and inside

Every product above is a **rigid printed sticker applied to the outside**. Across
every official page read, **not one describes placement inside a case, under an
existing label, or in a seam.** That is the gap, and NFC is what opens it,
because unlike a QR it does not need line of sight.

Real parts, real prices, all from datasheets:

| Part | Size | Thickness | Phone read range | Price |
|---|---|---|---|---|
| **GoToTags NTAG213 wet inlay** | 20 × 10 mm | **0.2 mm** | not stated | **$0.27** at 1,000 |
| **Seritag ST848 wet inlay** | 15 mm ⌀ | **0.11 mm** | **21–25 mm** | — |
| Seritag ST1036 | 22 mm ⌀ | 0.136 mm | 31–40 mm | — |
| Seritag ST710 | 29 mm ⌀ | 0.11 mm | 41–50 mm | — |
| **SCIVAS woven NFC + QR** | 50 mm woven | fabric | sew-on or iron-on | **$0.11**, MOQ 100 |

**0.11 mm is thinner than a sheet of paper.** A 15 mm disc at that thickness
reads at 21–25 mm from an ordinary phone — straight through the plastic lid of
an AirPods case, or through a garment's care label. For clothing the part
already exists as a **woven NFC tag you sew in**, from eleven cents.

> Seritag's "Real ScanStrength" is measured across 12 popular phones and
> reported as an average in millimetres, not a reference-reader figure. It also
> notes iPhone scanning outside an app runs at lower power than in-app.

### The physics floor: do not go below 15 mm

Range is driven by **antenna area, not label size**, and it falls off steeply.

- **6 mm** — reads at about **2 mm**. Contact only. Useless for a tap.
- **10 mm** — 16–25 mm depending on antenna. Adafruit's 15.6 × 6 mm part says
  outright it must be *"right up against"* the phone.
- **15 mm** — 21–25 mm. **This is the smallest size with real alignment
  tolerance, and it is the floor you should design to.**
- **22 mm and up** — 31–50 mm. Comfortable, if you have the room.

Seritag's own guidance is that anything under 25 mm "needs careful
consideration". 15 mm works; 6 mm is a demo that fails in front of a judge.

### The cost of invisible, stated honestly

Hiding the tag solves aesthetics and creates a worse problem: **nobody knows to
tap.** The NFC Forum says so in its own Wayfinding guidelines —

> marks that simply indicate existence … are not sufficient … must guide users
> to the tapping location

And the usability evidence on people who have never tapped a tag is brutal. In a
peer-reviewed study of 40 novices: **60% opened a phone menu first**, **73% made
a touch error**, and **38% tried to photograph the NFC symbol as if it were a
barcode**.

Apple's background read also is not ambient magic: iPhone XS and later read an
NDEF tag with no app, but only while the phone is **in use**, and the top of the
phone must be brought to the tag deliberately.

**So a fully invisible tag depends entirely on someone already knowing it is
there** — which means trained staff, not a random finder. And the one real
institutional trial found NFC intake was **slower than QR and cost over 50×
more to set up**, so do not assume the staff route is free either.

### The resolution: unobtrusive but announced

This is the same conclusion `covert-marking-feasibility.html` reached, arrived at
from a different direction. Do not aim for invisible. Aim for **unnoticeable
until you look, unmissable once you do.**

- The NFC Forum's compact N-Mark has a **3 mm minimum height**, plus half its
  height as clear space on each side — roughly a **6 mm footprint**. Smaller
  than a shirt button.
- The newer directional Wayfinding marks need **8 mm**. Both are free to use
  under a click-through licence.

**A 0.11 mm inlay hidden inside the case, plus a 3 mm mark on the outside, is a
product nobody currently sells.** It is invisible at arm's length, obvious to
anyone actually looking for it, and it costs about thirty cents.

---

## 4. What goes on the tag, and what it resolves to

### The sticker question: it is four formats, not one

"NFC sticker" is one of four ways to carry the same chip. You do not pick one;
you pick per surface, and they all resolve to the same code system.

| Format | Part | Price | Use it for |
|---|---|---|---|
| **Bare wet inlay** | 20 × 10 × **0.2 mm** NTAG213 | **$0.27** at 1,000 | hidden inside a case or under a label |
| Printed adhesive sticker | NTAG213 printed | $0.58 at 1,000 | flat non-metal, where visible is fine |
| On-metal tag | 29 mm ⌀ with ferrite | $0.81 at 1,000 | steel bottles, laptop lids |
| **Woven sew-in** | NTAG213/215/216 + QR | **$0.11**, MOQ 100 | clothing |

The visible printed sticker is the *worst* of the four for this product, because
it throws away the one advantage NFC has over QR: it does not need to be seen.
Use it only where you cannot get a tag inside or underneath.

### The real question: a phone number, or an ID?

**Put an opaque ID on the tag. Do not put a phone number on it.** Five
independent lines of evidence, and one honest argument the other way.

**1. Phone numbers rot, and this is the single biggest failure mode in the
closest real-world system.** In the pet-microchip data — 53 shelters, 23 US
states — the largest reason a chipped animal was *not* reunited was a **wrong or
disconnected phone number, 35.4%**. The chip worked. The number did not.

**2. The churn is enormous.** The FCC puts roughly **35 million numbers
disconnected and made available for reassignment every year**, and residential
numbers may be aged **no more than 90 days** before reassignment. A number
printed on a hoodie in freshman year is a coin flip by graduation.

**3. Police guidance is against visible names on belongings.** Chatham County
law enforcement, on labelling children's school items: *"instead of putting your
child's name on their backpack as a billboard, try putting initials, or even
their name somewhere less obvious."* You are labelling students, not children,
but a name and number on a visible tag is the pattern they warn about.

**4. A phone number is an account-recovery credential.** CISA describes SIM
swap — convincing a carrier to move a number to an attacker's SIM — and rates
SMS and voice MFA a **"last resort"** because of it. The UK's NCSC notes
criminals use published personal detail to make phishing convincing. Publishing
your number on your possessions is the wrong direction.

**5. A number cannot be revoked.** An ID can be rotated, reassigned or killed.
A printed number is permanent until you throw the item away.

### The honest argument for the dumb number

**It works when your service is dead.** No server, no internet, no company, no
subscription. And this is not hypothetical — **PetHub's own notice reads
*"Your PetQRTag.com tag will no longer work after September 30, 2014"***, with
every ID invalidated after an acquisition. A registry-backed tag is only as
durable as the registry.

Take that seriously, and answer it: publish a plain-text fallback on the claim
page and commit to an export. But it does not overturn the other five points.

### What the university gives you that neither option does

**The registrar maintains the contact details, for free, forever.** Penn states
the University is responsible for accurate student contact information and puts
a **hold on the account** if required fields are missing. Yale expects students
to review their details **every term**.

That is the direct answer to failure mode 1. Every consumer tag inherits the
35.4% dead-number problem. **A code that resolves through the university does
not**, because somebody else is already paying to keep it current.

### What competitors actually put on the tag

| Product | On the tag | Owner contact shown? |
|---|---|---|
| Okoban | 12-digit UID, typed in | no — registry alerts owner |
| Pebblebee Link | URL to `pebblebee.link/locator` | no — anonymous notify |
| SeQR | unique QR | no — anonymous messaging |
| Boomerang | unique QR | owner chooses; finder's number never shown |
| Tile | printed QR | **only if "Notify When Found" is on** |

**None of them prints a raw phone number, and none rotates the identifier.**
Boomerang's "rehome" reassigns the account behind a code rather than changing
the code.

### Engineering notes for whoever writes the tag

- **Capacity.** NTAG213 has **144 user bytes**. NDEF URI overhead is 8 bytes, so
  a bare URL gets ~136 characters — but the URI record's prefix byte for
  `https://` is free, which buys you back to ~144. Plenty. Do not buy NTAG215
  for this.
- **Apple's requirement.** A no-app background read needs a **well-known type
  `U` URI record**, and it takes the **first** URI if there are several. HTTP and
  HTTPS work; custom schemes do not.
- **The tag cannot prove it is genuine.** NTAG21x can mirror its UID and a read
  counter into the URL, and it carries an NXP ECC originality signature readable
  with `READ_SIG` — but a browser tap never verifies any of it. **A copied URL
  behaves identically to the real tag.**
- **Password protection is a speed bump, not security.** The 32-bit `PWD`/`PACK`
  pair is described by NXP itself as convenient rather than secure.
- **So treat the tag URL as a bearer credential** — anyone who taps once can
  revisit forever, exactly as RFC 6750 defines the term. Every competitor lives
  with this. The defence is server-side: reveal nothing sensitive on the finder
  page, rate-limit, and allow the owner to kill a code.

### Our code space is too small. Fix it after the demo.

`new_code()` currently draws **6 characters from a 28-symbol alphabet** — no
vowels, so no accidental words. That is 28⁶ = **482 million**, about **2²⁹**.

With 10,000 live tags, a script at a modest **10 requests per second finds a
valid code in about 1.3 hours**. What it gets is only the finder page, which
names the item and never the owner — so the realistic abuse is **spamming false
"I found it" reports**, not a privacy breach.

Good enough to demo, wrong to ship. **Ten Crockford Base32 characters gives
2⁵⁰** — 36 years to exhaust at a million guesses a second — and Crockford
already excludes `I`, `L`, `O` and `U` and defines a mod-37 check symbol so
typos in the `/f` fallback are caught rather than misrouted.

---

## 5. How NFC works, and can a competitor free-ride?

### How NFC actually works

Worth knowing properly, because the security answer falls straight out of it.

**It is not radio in the sense you are thinking.** ISO/IEC 14443-2 specifies a
carrier of **13.56 MHz ± 7 kHz**, and the reader generates an **alternating
magnetic field**, not a radiating wave. Field strength is **1.5–7.5 A/m rms**
for a reference tag.

**The tag has no battery and no transmitter.** It has a coil. Sitting in the
reader's field, that coil picks up energy by induction, which a rectifier and
regulator on the chip turn into a supply. The field must stay on continuously —
it is both the power source and the clock.

**The tag answers by changing how much it loads the reader.** It switches a load
across its own coil, and the reader senses that as a disturbance in the field it
is itself producing. That is **load modulation**, and for Type A the reply rides
a **subcarrier at fc/16 = 847.5 kHz**, OOK with Manchester coding, at
106 kbit/s. Reader-to-tag goes the other way as ~100% ASK with modified Miller.

**Which is why range is centimetres.** In the near field the magnetic field
falls off as **1/r³**, and the useful coupled power roughly as **1/r⁶**. Doubling
the distance does not halve the signal; it guts it. This is also why antenna
area matters more than sticker size, as covered in §3.

Above the physical layer: **ISO 14443-3** handles polling and anticollision and
resolves the 7-byte UID; **ISO 14443-4** carries the block transmission
protocol; and NDEF, the message format your URL lives in, sits on top as an
**NFC Forum Type 2 Tag** for NTAG213. A phone reading your sticker is in
**reader/writer mode**.

> **Short range is not a security control.** NIST's Mobile Threat Catalogue
> entry LPN-12 documents NFC **relay attacks** — an attacker proxies the session
> over distance, and proximity buys you nothing. Do not put "it only works at
> 2 cm" in a security argument.

### The free-riding problem, stated precisely

Today, an NTAG213 holds a plain URL. Plain memory, readable by anyone, provable
by nothing. A competitor buys $0.27 inlays, writes **your** URL onto them, sells
at $1.50, and your server cannot tell their tag from yours. **You are right that
nothing currently stops this.**

### Yes, there is a chip that fixes it: NTAG 424 DNA

NXP built exactly this. It uses **AES-128** and a feature called **SUN**, Secure
Unique NFC, with **five customer-defined AES keys**. On every tap the chip
composes a **fresh** URL:

```
https://your.server/t?picc_data=EF963FF7828658A599F3041510671E88&cmac=94EED9EE65337086
```

- **`picc_data`** is `AES-128-CBC(SDMMetaReadKey, PICCDataTag ‖ UID ‖ SDMReadCtr ‖ random padding)`.
- **`SDMReadCtr`** is a 24-bit counter that **increments once per tap**.
- **`cmac`** is an **8-byte truncated AES-CMAC** over the dynamic part, under a
  session key derived per tap:
  `SV1 = C33C 0001 0080 ‖ UID ‖ SDMReadCtr`, then `CMAC(key, SV1)`.
  That is NIST SP 800-108 key derivation over SP 800-38B CMAC.

Your server decrypts `picc_data`, re-derives the session key, recomputes the
CMAC and compares. **Any standard AES library does this.** No app is needed on
Android — it is still an ordinary HTTPS link, the phone just opens it.

**A competitor with a generic NTAG213 cannot produce a valid `cmac`, because
they do not have your key.** That is a genuine cryptographic answer to your
question.

### Three caveats, and the third is fatal to the plan

**1. Replay is still possible unless you do the work.** NXP warns explicitly
that a free read lets someone capture a valid URL and replay it. The counter is
what saves you: **your server must record the highest counter seen per tag and
reject anything equal or lower.** Crypto alone does not do it.

**2. It costs 2.5×.** A 25 mm NTAG 424 DNA inlay is **$0.77 at 100, $0.68 at
1,000, $0.45 at 10,000** against **$0.27** for NTAG213. At 1,000 units that is
**+$0.41 a tag**. On a $2 tag, affordable.

**3. Your QR fallback destroys all of it.** A QR code is ink. Scantrust, who
sell anti-counterfeit QR for a living, put it plainly: an original and a
photocopy **encode the same URL and are visually indistinguishable**, so there
is no mechanism to tell a genuine scan from a fake one. Serialised codes only
let you notice *afterwards*, once duplicate scans show up. The only real fix is
a **copy-detection pattern** — a printed random texture that degrades when
photocopied — and even that is bypassed if the counterfeiter simply prints
*their own* code pointing at *their own* domain.

So if a competitor's cheap tag can reach you through the QR path, or by typing
the code at `/f`, the AES on the NFC path is decoration. **You cannot have both
an authenticated tag and an open fallback.** Pick.

### And the business answer, which matters more

Crypto stops *a competitor's tag from working with your service*. It does not
stop the competitor existing. What you are actually proposing is a **walled
garden**, and that is a strategy choice, not a security fix. Look at what the
market does:

| Service | Accepts codes it did not sell? | Basis |
|---|---|---|
| **Bike Index** | **Yes** | states it outright — *"Everyone can register bikes, for free"*, 1.8M registered |
| **Okoban** | **Yes, apparently** | registration takes any valid unregistered 12-digit UID and never asks for proof of purchase |
| Dynotag | No | activation needs an 8-digit Tag ID **and** a 4-character Key Code printed on the packaging |
| Tile | No | you must press the button on a physical Tile to activate |
| Boomerang, PetHub, ByteTag | No documented route | their workflows only ever link a tag they issued |

> Read that last row precisely. **None of those three publishes a policy refusing
> third-party codes** — the gate is implied by the activation flow, not stated.
> Okoban's openness is likewise inferred from its form, not an affirmative
> policy. Do not claim on stage that a named competitor "blocks" anything.

**The two largest and most open are the two that do not gate.** The gated ones
are small consumer products competing on hardware.

Where authenticated NFC genuinely earns its cost is **anti-counterfeiting** —
Treiber Timepieces embeds NTAG 424 DNA in watch certificates of authenticity,
where the tag *is* the product's proof of value. Your tag is not the product.
**Your tag is a pointer, and §2 already established the pointer was never the
moat.**

### What to actually do

**Do not gate the tag. Gate nothing. Sell the service, and let the university be
the moat.** A campus does not want a walled garden where only tags from one
vendor work — it wants *everything* tagged. A competitor selling cheaper inlays
that resolve against your registry is **free distribution**, exactly as it is for
Bike Index.

Keep NTAG 424 DNA in your back pocket for one specific case: if you ever need a
tag whose authenticity itself matters — a university-issued asset, a laptop in an
equipment-loan scheme — the chip exists, it costs forty cents more, and you now
know precisely how it works.

---

## 6. Can we patent it?

**No, realistically — and one of the three reasons should worry you more than
the patent question itself.** Nothing here is legal advice; it is sourced
material to take to the free clinic named at the end of this section.

### Reason 1: there is an active patent, and it is worth reading properly

**US8973813B2 — "System for facilitating return of lost property"**
Inventors Nadine Wendy Penny and Todd Penny. Assignee **GoCodes Inc**.
Priority **19 April 2011**, granted **10 March 2015**, **status active**,
adjusted expiry **4 July 2032**. 26 claims, four of them independent.
<https://patents.google.com/patent/US8973813B2/en>

GoCodes is still trading, and markets itself on *"patented QR codes… trusted by
1,000+ companies since 2011."* Their business today is B2B equipment tracking
rather than consumer lost-and-found, but the patent is live either way.

**Claim 1, verbatim in the parts that matter:**

> …creating a return profile for each individual portable asset that includes
> privacy preferences elected by the property owner, **the return profile
> including a owner nickname** … **generating a tag that displays both the
> owner nickname and a visual code** … the visual code including embedded
> information that links directly to the unique property page … **directly
> accessing the unique property page when a finder … accesses the embedded
> information of the visual code by photographing the visual code with a smart
> device**, and wherein a communication protocol previously dictated by the
> privacy preferences … is established without any additional input from the
> finder.

Dependent **claim 3** adds *"acting as an intermediate to maintain anonymity for
one or both of the property owner and the finder."* Dependent **claim 6** adds
transmitting the scanning device's location. **Claim 7** specifies GPS and IP.

#### Two details that materially change the picture

**1. Claims 1 and 9 require an owner nickname printed on the tag.** Both say the
tag *"displays both the owner nickname and a visual code"*, and that the
nickname be *"recognizable by persons familiar with the property owner."*
Whoops Tag's label carries a code and nothing else — deliberately, because the
entire point is that the finder learns nothing. **A tag with no nickname does
not appear to practise claim 1**, and since claim 3's anonymity limitation hangs
off claim 1, the anonymity claim carries the nickname requirement with it.

Claims **14** and **19** have no nickname requirement, and those are the closer
ones: claim 14 is the finder-side method, claim 19 the system.

**2. The whole patent is about a camera reading a visual code. NFC is nowhere
in it.** Counting terms across the full document:

| Term | Occurrences |
|---|---|
| barcode | 79 |
| camera | 23 |
| QR | 20 |
| photograph | 2 |
| **NFC** | **0** |
| **near field** | **0** |
| **RFID** | **0** |
| **radio frequency** | **0** |

Claim 14 requires *"photographing a visual tag … with a camera device."*
Claim 19 requires *"a visual tag including a symbol … accessible to capture by a
camera device."* **An NFC tap is not photographing, and an NFC inlay is not a
symbol captured by a camera.**

> **So the NFC-first decision looks materially better than the QR fallback here,
> for a reason we did not anticipate.** The QR path sits squarely in what this
> patent describes. The NFC path does not appear to be addressed by it at all.
>
> Claim construction is a legal exercise, the doctrine of equivalents exists,
> and none of this is legal advice. **Take this exact paragraph to the clinic.**

Others found, all opened and with claim 1 read:

| Patent | Owner | Status | Why it matters |
|---|---|---|---|
| **US8973813B2** | GoCodes | **Active to 2032** | Tag → item page → anonymised relay → location |
| **US9763053B2** | XY Persistent | **Active to 2035** | Anonymous contact options + finder message + location |
| US20140019566A1 | Four Gauchos | Abandoned | Claim 4: **anonymised email forwarding** |
| US20100223245A1 | Travel Sentry → Okoban | Abandoned | Privacy engine restricting finder results |
| US6259367B1 | Klein | **Expired 2020** | RFID code → owner lookup → auto-notify, filed **1999** |
| US20180098523A1 | Master Vet Products | Abandoned | QR pet tag → server record → owner alert + GPS |
| US20140306005A1 | Forever Yours | Abandoned | 2D barcode → DB/URL, notification + scanner location |
| US7956744B2 | TrackItBack | Expired | Digital ID for lost electronics; registration and finder report |

**Read those last two rows together with the NFC finding above.** The radio
version of this idea — an RFID tag carrying a unique code that resolves to an
owner record and auto-notifies them — was patented by Klein in **1999** and
**expired in 2020**. Expiry cuts both ways, and here both directions help and
hurt in a useful pattern:

- It is **prior art**, so it helps destroy any novelty claim you might make.
  That is one more nail in the patent question, which is already settled.
- It is **expired**, so it no longer blocks anyone from practising it. The
  radio-tag approach is in the public domain.

So the picture that emerges is: **the NFC route is old enough to be free, and
the camera route is owned until 2032.** That is an argument for building on NFC
that has nothing to do with user experience.

Two distinctions that matter and are easy to get wrong:

- **Abandoned and expired patents still destroy novelty.** They no longer stop
  you *practising* the idea, but they are prior art and they block you
  *patenting* it. The 1999 Klein patent alone is a serious problem for novelty.
- **Active patents are the reverse.** They do not stop you filing, they stop you
  operating. This is the part that should worry you more than patentability:
  freedom-to-operate is a real question if this ever becomes a company.

**The one thing not claimed anywhere.** Across nine documents read at claim
level, **no reviewed claim requires integration with an institution's own
identity system**. Every one of them is a tag, a server and two strangers. That
is the same gap the prior-art work found commercially, now confirmed in the
patent record — and it is the only direction in which a narrow, specific claim
might survive. Treat that as a question for the clinic, not a plan.

### Reason 2: obviousness. This is the one that kills it.

*KSR v. Teleflex*, 550 U.S. 398, 416 (2007), in the Supreme Court's own words:

> "Such a combination of familiar elements according to known methods is likely
> to be obvious when it does no more than yield predictable results."

NFC tag: familiar. Adhesive label: familiar. Database lookup: familiar. Sending
a notification: familiar. Combining them produces exactly the result anyone
would predict. KSR also removed the escape route — the reason to combine can
come from market demand or ordinary background knowledge, not just an explicit
teaching. This is close to the textbook example of an obvious combination.

### Reason 3: eligibility. A second, independent problem.

Under the *Alice/Mayo* two-step framework in **MPEP 2106**, a claim to
scan → database lookup → notify reads as collecting, organising and
transmitting information. The MPEP states plainly that a generic computer or
the Internet does not make an abstract idea non-abstract. Without a specific
unconventional technical improvement, this is a serious §101 risk on top of the
other two.

### One thing to actually be careful about this weekend

**Demoing publicly starts a clock.** Under §102(b)(1) the inventor's own public
disclosure gets a **one-year US grace period** — file within twelve months or
your own demo becomes prior art against you. Outside the US there is generally
**no grace period at all**, so a public demo can end foreign rights immediately.

This is not a reason to hide anything. It is a reason to know the date.

### What filing would actually cost

USPTO government fees, micro entity: **provisional $65**; through grant
**$723**; maintenance to full term brings it to **$3,617**. Average total
pendency was **26.3 months** in FY2025. None of that includes attorney
drafting or prosecution, which is where the real money goes.

**Spending $65 on a provisional for an idea with an active patent over it and a
textbook obviousness problem is not a bet — it is a donation.**

### What to do instead

| Tool | Protects | Cost |
|---|---|---|
| **Trademark** | The name *Whoops Tag* as a brand | $350 per class |
| **Copyright** | Your actual code, automatically on writing it | free; register to sue |
| **Trade secret** | Implementation, anti-abuse rules — only while secret | free |
| **Campus contracts** | The relationship and the integration | time |

**The real moat is the institution, and it is the same thing that makes the
product good.** WashU IT procurement requires a formal process for anything
integrating with university systems or WUSTL Key, or giving a third party access
to student data, plus an information-security vendor review. That is a barrier
to a competitor — and to you. Nothing in the policy requires exclusivity, so the
moat is adoption and switching cost, not a contract clause.

> Note: **Project 529 already has a WashU partner page**, with Danforth bike
> registration limited to WashU students, faculty and staff. A competitor
> already holds a campus relationship here, for bikes. Worth knowing.

### Free legal help, on your own campus

- **WashU Law Entrepreneurship Clinic** — in its own words, *"free legal
  assistance to qualifying entrepreneurs and organizations in the St. Louis
  area"*: entity formation, tax structure, governing documents, commercial
  agreements. Director Jonathan Smith, Professor of Practice.
  <https://law.washu.edu/academics/clinical-programs/entrepreneurship-clinic/>
  **Intake form** — this is the actionable one:
  <https://washu.qualtrics.com/jfe/form/SV_3gXVRX295f45YDc>
- **Skandalaris Center** — Entrepreneurship & IP Law Clinic, plus free
  *Experts on Call*. 314-935-9134, sc@wustl.edu
- **Not** the Office of Technology Management — OTM handles University-owned IP,
  not student ventures.

**Do not let any of this block the build.** Patentability is a question for next
month. A working demo is a question for tonight.

### And on the worry itself

Published rubrics say the thing you are anxious about is worth surprisingly
little. Novelty is **never a standalone criterion** in any rubric checked. Where
it is quantified at all it is roughly **20%** (Cal Hacks) or **33% bundled with
impact** (HackMIT). HackMIT's own page invites hackers to *"dust off old ideas
or try something completely new."* MLH's judging guide says to focus on learning
over profit, and calls the **demo the most important factor**. The only
resemblance rule MLH actually imposes is a ban on reskinning an existing AI tool.

**Nobody is going to disqualify you for building something that exists. They
will mark you down for a demo that does not run.**

---

## 7. Current state

### Built and verified

`code/prototype/app.py` — pure standard-library Python, SQLite, no pip
install, no API keys, no accounts. Full loop tested end to end.

| Route | Purpose | Status |
|---|---|---|
| `/` | Admin: create tags, see claims | works |
| `/i/<code>` | Finder page — reports the find | works |
| `/claim/<code>` | Owner claims a tag | works |
| `/o/<token>` | Owner dashboard, live via SSE | works |
| `/labels` | Printable QR label sheet | works |
| `/f` | Six-character typed code, no NFC, no camera | works |
| `/write/<code>` | Writes an NFC tag from Chrome on Android | works |

Verified: tag created → QR generated → owner claimed → finder page names the
item without leaking the owner → owner notified live over server-sent events.

### Hardware position

No NTAG available locally in time. Micro Center Brentwood has **no NTAG in any
form**; its only writable tags are MIFARE Classic, which **iPhone cannot read at
all** and Android supports only optionally. QR is the primary path. See
[`reports/thirty-hour-plan.html`](reports/thirty-hour-plan.html).

### Running it so a phone can actually reach it

This is the part that turns a laptop demo into a system. A tag encoding
`localhost` is useless — the finder's phone cannot resolve it.

**Same wi-fi (works right now, zero setup).** `app.py` binds `0.0.0.0` and now
auto-detects this machine's LAN address, so every tag URL, QR and label is
already reachable from a phone on the same network:

```
python3 code/prototype/app.py
#   Whoops Tag running:  http://192.0.2.17:8000
```

That address changes with the network. The server prints the live one on start;
trust that over anything written here.

**Public HTTPS (one click, then it works from cell data).** Any tunnel works. With Tailscale, enable Funnel once on your tailnet
(`tailscale funnel` prints the enable link if it is off), then:

```
tailscale funnel --bg 8000
BASE_URL=https://<your-machine>.ts.net python3 code/prototype/app.py
```

**Do this before writing any tags.** Whatever `BASE_URL` is when a tag is
created is baked into its QR and its NFC payload. Change the URL afterwards and
every printed label is dead.

Why HTTPS matters beyond looking tidy: the in-browser tag writer at
`/write/CODE` uses Web NFC, which **only runs on HTTPS**. Over plain LAN HTTP
the rest of the system works fine, but you will have to write tags with the NFC
Tools app instead.

---

## 8. Open decisions

- [ ] **Confirm or kill the Beacon Tags question.** A WashU student reportedly
      already gives out QR labels for campus items. The article 403s. Find out
      locally — if it is real it is the first question a judge asks.
- [ ] **Which surface for the demo object?** QR has no metal problem; NFC needs
      a ferrite on-metal tag for a steel bottle. Pick the object before writing
      the script.
- [ ] **How far to push the institutional claim** without a real campus
      integration built. Honest framing beats a fake integration.
- [ ] **Whether to show the prior-art work to judges.** It is unusually thorough
      and it pre-empts every objection — but it also names competitors out loud.
- [x] **How small can the tag be?** Settled: **15 mm is the floor** for a
      reliable phone tap. Below that you lose alignment tolerance; at 6 mm it is
      contact-only. See §3.
- [ ] **Order a 15 mm wet inlay and prove the through-plastic tap.** The whole
      differentiator rests on a 0.11 mm inlay reading from inside a closed
      AirPods case. **This is untested and it is the riskiest assumption in the
      project.** Test it before it goes in a slide.
- [ ] **Pick the visible cue.** Fully invisible means nobody taps. Options are a
      3 mm N-Mark, an 8 mm directional Wayfinding mark, or relying on trained
      staff at intake. Decide, because it changes the industrial design.

### Product MVP direction

The MVP has two client surfaces and one backend:

- **Finder web** — a normal browser opened by NFC, QR, or a short typed code. No
  finder account or app.
- **Owner mobile app** — React Native with Expo and TypeScript, built for iOS and
  Android with EAS. This is the notification source of truth.
- **Web backend** — hosted on Vercel, backed by a managed PostgreSQL database.

A PWA can receive system notifications, but on iOS it must be added to the Home
Screen and the user must grant permission through a user gesture. That is a
platform-dependent onboarding path, so it is not sufficient as the only owner
notification path. Keep a responsive owner web view as a fallback, but use the
native owner app for the MVP's notification guarantee. See WebKit's
[Web Push guidance](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/).

**Identity and database encryption**

- Generate a random internal user UUID. Never expose it in NFC/QR payloads,
  URLs, HTML, notifications, or chat.
- Store the UUID only as application-layer ciphertext using envelope encryption.
  The encryption key must live outside the database, in a managed secret/KMS
  boundary. Database disk encryption and TLS are additional layers, not a
  replacement for field encryption.
- Store a keyed HMAC of the UUID beside its ciphertext when lookup is required.
  The HMAC permits equality lookup without storing a plaintext or using
  reversible deterministic encryption.
- Store contact details, authority identities, private item proof, and push
  metadata as encrypted fields where appropriate. Keep the encryption keys out
  of the database and out of client bundles.
- Use non-identifying database references for relationships. The public
  application must never derive a user identity from a tag or database row ID.

**Short tag access without weakening owner security**

Use two tag identifiers:

1. A random tag secret, at least 128 bits, is used in the NFC/QR URL and stored
   only as a hash. This long, untypeable secret is the strongest carrier when
   the phone can tap or scan; NFC/QR must never use the short human alias.
2. A human code is an eight-character Crockford-style code with a check symbol,
   formatted in groups for typing. It is an alias that reaches only the safe
   `/f` finder route; it is not an owner login or an authority credential.

This keeps manual entry short while ensuring that guessing a code cannot reveal
owner contact information or private item proof. Apply aggressive per-IP,
per-session, and per-code throttling to `/f`; add a challenge after repeated
failures. Revoke both lookup paths when a tag is deactivated. A replacement gets
a new secret and human code while preserving the same item history.

Do not place a phone number, email address, internal UUID, serial number, or
owner name on the tag.

**MVP records**

`user`, `item`, `tag`, `found_event`, `finder_session`, `conversation`, `message`,
`push_device`, `authority_user`, `authority_case`, and `audit_event`. A tag is
separate from an item so it can be revoked and replaced. Store coarse handoff
places, not live finder GPS. Keep receipts, serial numbers, and private
descriptions owner-only unless selectively released for a handoff.

**Finder → owner flow**

1. The finder taps NFC, scans QR, or enters the short code in the finder website.
2. The finder sees only a safe item description and the anonymous-return
   explanation.
3. The finder submits a coarse place, optional note, and optionally chooses
   campus security/police handoff.
4. The backend creates a `found_event` and an anonymous conversation.
5. The owner app receives a real system notification:
   “Someone reported your item found.”
6. The notification opens the item and conversation in the owner app. Do not put
   location, notes, or identity data in the lock-screen payload.
7. The finder chats in the browser; the owner replies in the app. Use random
   participant/session identifiers and escape all rendered message content.
8. The owner can mark the item recovered, close the conversation, revoke the tag,
   or provision a replacement.

Use ordinary authenticated API requests for writes. For the presentation, use
short polling or a managed realtime channel rather than depending on a
long-lived custom SSE process on serverless hosting. Push notification, unread
state, and message retrieval must remain correct even if a live connection
drops.

**Native notification implementation**

The owner app uses `expo-notifications` and EAS credentials for APNs and FCM,
then registers one or more device tokens with the backend. The server sends a
minimal push through Expo Push Service or directly through APNs/FCM later.
Permission denial must degrade to in-app unread state and email fallback; it
must not silently report that notification delivery succeeded.

Expo's official setup requires a physical-device-capable development build and
platform push credentials:
[Expo push setup](https://docs.expo.dev/push-notifications/push-notifications-setup/).

**Calling decision**

Include voice calling as a bounded extension after anonymous chat works. Use a
provider that supports both browser and React Native audio rooms, preferably
LiveKit Cloud for this cross-platform flow:

- backend creates a short-lived room token only after an owner/finder
  conversation exists;
- finder browser and owner app join the same temporary room;
- either side can mute and end the call;
- room tokens expire and the room is closed with the conversation;
- neither side learns the other's phone number.

LiveKit's Expo integration requires native dependencies and an Expo development
build, not Expo Go. Therefore calling is easy enough to prototype after the
native app exists, but it must not block the tag → notify → chat demonstration.
Acceptance requires two physical devices/browsers to complete a short audio call;
otherwise ship chat as the reliable fallback. See the
[LiveKit Expo quickstart](https://docs.livekit.io/transport/sdk-platforms/expo/).

**Hosting and database**

- Host the finder website, owner web fallback, admin portal, and API routes on
  Vercel.
- Use Supabase PostgreSQL for the relational database and, if useful, its
  authentication and managed realtime facilities. Client code must not receive
  database service-role credentials.
- Put encryption keys, push credentials, LiveKit secrets, and the immutable
  platform-admin allowlist in Vercel environment secrets or a dedicated KMS;
  never commit them or store them in PostgreSQL.
- Keep server operations in server-only Vercel routes. Apply row-level
  authorization and explicit ownership checks even when the client is
  authenticated.
- Do not promise durable custom SSE connections on Vercel. Use request-based
  message retrieval or a managed realtime channel for chat.

**Authority and administrator security**

Authority users are manually invited campus-security or police users. SheerID
is not the authority authorization mechanism. An administrator approves the
organization and invite, and every authority action is audited.

The platform administrator is a control-plane role, not a normal editable
profile:

- no route can create, promote, demote, or delete the platform administrator;
- authority users cannot invite administrators;
- normal admins cannot alter the immutable admin allowlist;
- bootstrap and rotation happen out of band through deployment secrets or a
  restricted operator procedure;
- MFA, short sessions, server-side authorization, and append-only audit events
  are required;
- admin contact and identity data are encrypted at rest.

This protects against application-level privilege escalation. It cannot make a
database superuser or a compromised runtime harmless; those keys and the
encryption boundary must therefore remain outside the database.

Authority cases expose only:

- exact tag/item reference and safe item description;
- owner verification state and selected recovery details;
- custody location, handoff instructions, case number, and case status;
- anonymous conversation relay;
- audit history.

The authority can record custody, send relay messages, add a case number, and
mark the item released/recovered. Owner contact disclosure requires explicit
logged consent or a documented legal/policy basis.

**Build order and presentation acceptance**

1. Create the Vercel web shell, Expo owner app, Supabase schema, server-only
   secrets, authentication, encrypted UUID vault, and owner inventory.
2. Add hashed tag secrets, short human codes, QR/NFC/typed entry, revocation,
   replacement, and audit events.
3. Add finder sessions, found events, anonymous chat, unread state, and message
   retrieval.
4. Add native push registration and a real system notification on both iOS and
   Android test devices.
5. Add the manually invited authority case flow and least-privilege views.
6. Run the optional LiveKit call spike. Keep it only if the two-device acceptance
   test passes; otherwise keep the call action out of the core demo.
7. Test copied-tag abuse, code throttling, session expiry, CSRF/XSS, key
   separation, backup/restore, QR size, NFC material compatibility, and
   iPhone/Android finder paths.

The presentation script is deterministic: owner registers a bottle and receives
its tag; finder scans or types the short code; owner receives a system
notification; both sides chat anonymously; finder selects security handoff;
authority records custody; owner marks recovered; old tag is revoked and a
replacement is issued.

**Explicitly out of the core MVP:** a PWA-only notification guarantee, public
owner phone numbers, live GPS tracking, automatic police discovery, NTAG424
cryptographic authentication, and a calling feature that has not passed the
two-device test. The current stdlib/SQLite prototype remains the demo reference;
it is not the authenticated multi-tenant product backend.


---

## 9. Evidence index

Everything below is self-contained HTML, offline, and prints to PDF.

| Document | What it establishes |
|---|---|
| [`theft-and-property-loss-report.html`](reports/theft-and-property-loss-report.html) | How property is lost and stolen; 17 charts, 32 sources |
| [`opportunistic-theft-report.html`](reports/opportunistic-theft-report.html) | Unattended-property theft; 24 charts, 49 sources |
| [`what-gets-lost.html`](reports/what-gets-lost.html) | What people actually leave behind; Tokyo's 4.85M-item dataset |
| [`loss-and-reunification.html`](reports/loss-and-reunification.html) | Finder behaviour and the identifiability pivot |
| [`prior-art.html`](reports/prior-art.html) | Competitive landscape; 54 sources |
| [`universal-label.html`](reports/universal-label.html) | Does the universal sticker already exist? 37 sources |
| [`covert-marking-feasibility.html`](reports/covert-marking-feasibility.html) | Why invisible marking fails |
| [`thirty-hour-plan.html`](reports/thirty-hour-plan.html) | Sourcing reality and the QR contingency |
| [`one-day-build.html`](reports/one-day-build.html) | Build guide with the demo script |

### Numbers worth memorising

- **350** — bikes UT Austin auctions yearly because they cannot be traced
- **"Will Not Accept — Immediate Disposal"** — Boise State, on water bottles
- **573 of 1,675** (34%) — Texas A&M reunification when it has something to work with
- **82.8% vs 1.4%** — Tokyo return rate, phones versus umbrellas
- **43×–60×** — how much cheaper a passive tag is than a Bluetooth tracker
- **36% / 10%** — Indiana University: bikes registered, bikes recovered

---

## 10. Reverting

This file is documentation only; deleting it changes no behaviour.

- **Prototype** — all runtime behaviour is in `code/prototype/app.py`. The
  SQLite file `bearwithme.db` sits beside it and is regenerated on first run;
  delete it to reset to an empty database.
- **Reports** — each one regenerates from its pair in `code/reportgen/`. To drop
  a report, delete its `build_*.py`, its `data_*.py` if it has a dedicated one,
  and the HTML in `reports/`.
- **The move itself** — this project was previously a flat `research/` folder at
  the workspace root. To undo the reorganisation, move `code/reportgen/*` and
  `reports/*.html` back into one directory, revert `OUT = REPORTS / "…"` to
  `OUT = HERE / "…"` in each builder, and drop the `REPORTS` definition from
  `shell.py`. Nothing outside `bear-with-me/` was touched.
