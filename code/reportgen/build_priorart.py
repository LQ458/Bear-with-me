#!/usr/bin/env python3
"""Build the Whoops Tag prior-art and competitive landscape report.

    python3 research/build_priorart.py  ->  research/prior-art.html

One file, no external assets, no JavaScript. Charts are inline SVG from
`charts.py`; styling from `shell.py`. Data and citations from
`data_priorart.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import data_priorart as D  # noqa: E402
from charts import ACCENT, NEGATIVE, POSITIVE, Bar, hbar  # noqa: E402
from shell import REPORTS, Doc  # noqa: E402

OUT = REPORTS / "prior-art.html"
S = D.SOURCES
LEAD = D.VERIFIED_BY_LEAD


def cite(*keys: str, extra: str = "") -> str:
    bits = []
    for k in keys:
        t, org, url, kind, yr = S[k]
        tick = " &#10003;" if k in LEAD else ""
        bits.append(f'<a href="{url}">{org}, <i>{t}</i></a> ({yr}){tick}')
    s = "<b>Source:</b> " + "; ".join(bits) + "."
    return f'<p class="srcnote">{s}{" " + extra if extra else ""}</p>'


def chip(kind: str, txt: str) -> str:
    cls = {"no": "c-none", "yes": "c-strong", "part": "c-mod",
           "vendor": "c-ven", "official": "c-off", "academic": "c-aca"}[kind]
    return f'<span class="chip {cls}">{txt}</span>'


d = Doc()

MASTHEAD = """
<div class="masthead">
  <div class="kicker">Prior Art &middot; Lost-Property Reunification</div>
  <h1>The tap is taken. The campus is not.</h1>
  <div class="standfirst">Scan-a-tag-and-notify-the-owner is a solved, crowded,
  commodity product category &mdash; Apple, Samsung, Tile and at least eight tag
  vendors already ship it, and one of them proxies identity exactly as you
  planned to. What nobody has built is the institutional half. Here is who
  occupies what, with prices and mechanisms from primary sources, and the
  narrow ground that is genuinely still empty.</div>
  <div class="meta">
    <div><b>Scope</b>Consumer tags, trackers, lost-property SaaS, campus schemes</div>
    <div><b>Evidence base</b>__NSRC__ primary sources</div>
    <div><b>Figures</b>__NFIG__ charts, __NTAB__ tables</div>
    <div><b>Prepared</b>29 August 2026</div>
  </div>
</div>"""

# =============================================================== VERDICT ====

d.h2("Verdict", "verdict")
d.p("Your mechanism is not novel and you should stop planning to claim it is. "
    "A finder tapping or scanning a passive tag with no app, and an owner being "
    "notified, is shipped today by <b>Apple, Samsung, Tile, PetHub, ReturnMe, "
    "ByteTag, Boomerang, Dynotag and Okoban</b>. Your privacy relay is not novel "
    "either &mdash; <b>ReturnMe proxies contact by default and PetHub offers an "
    "anonymised phone bridge</b>. What is genuinely unoccupied is narrow, real, "
    "and worth more than either: <b>nobody has connected the tag to the "
    "institution</b>.", "lede")

d.box("warn", "Three objections a judge will raise, in the order they will raise them",
      "<ol>"
      "<li><b>&ldquo;This is AirTag Lost Mode.&rdquo;</b> A fair hit on the "
      "interaction. Any NFC phone can tap an AirTag in Lost Mode with no app and "
      "see the owner's message. The difference is real but must be stated "
      "precisely: Apple <i>displays</i> the owner's chosen phone or email, and "
      "the generic tap also shows the serial and the last four digits of the "
      "registered number. That is disclosure, not a relay &mdash; and it is a "
      "$29 battery-powered Bluetooth device.</li>"
      "<li><b>&ldquo;This is PetHub for students.&rdquo;</b> Also fair. PetHub is "
      "a $9.95 QR tag, no app for the finder, with a privacy model close to "
      "yours. The honest answer is that PetHub has no institution behind it "
      "&mdash; there is no organisation that already knows every pet owner's "
      "contact details and sees every found pet.</li>"
      "<li><b>&ldquo;Tile already does the scan-and-notify.&rdquo;</b> True, and "
      "the least known of the three. Tile's <i>Scan Me If Found</i> lets a "
      "finder scan a QR, leave a note and share a one-time location; the owner "
      "gets an email. Know this before someone tells you.</li>"
      "</ol>"
      + cite("airtag_found", "airtag_lost", "pethub_privacy", "tile_scan"))

d.box("insight", "The one-sentence version",
      "<p>Every competitor solves <b>the item telling someone who owns it</b>. "
      "None solves <b>the institution already knowing, and already holding the "
      "item</b> &mdash; which on a campus is where the property actually ends "
      "up.</p>")

# ========================================================= CONSUMER TAGS ====

d.h2("1. The tag market is crowded and cheap", "tags")
d.p("Eight vendors, all passive, all app-free for the finder. This is a "
    "commodity category, not a frontier. Prices are per tag from the vendor's "
    "own store page; blank cells are where the page would not expose a price.")

d.table(
    ["Product", "Carrier", "Finder app?", "Identity model", "Price",
     "Recovery claim"],
    [[f"<b>{n}</b>", m, a, i, p, r] for n, m, a, i, p, r in D.CONSUMER_TAGS],
    title="Passive lost-and-found tags",
    sub="Every recovery claim in the right-hand column is the vendor's own "
        "marketing. None is an independent study, and none publishes a "
        "denominator.",
    source=cite("pethub_price", "pethub_pricing", "returnme_home", "bytetag",
                "crashtag", "okoban", "tile_lf", "boomerang", "dynotag"))

d.box("caveat", "Read the recovery claims with a cold eye",
      "<p><b>PetHub: &ldquo;96% of recovered pets home within 24 hours.&rdquo;</b> "
      "Note the word <i>recovered</i>. That is a statistic about pets that were "
      "already found, not the share of lost pets that come home. "
      "<b>ReturnMe: &ldquo;115,000+ recoveries.&rdquo;</b> A numerator with no "
      "denominator &mdash; out of how many tags sold? Neither number tells you "
      "whether tagging works, and if you quote either on stage without the "
      "caveat, the first sharp judge will take the rest of your evidence less "
      "seriously.</p>"
      "<p>The other six vendors publish <b>no recovery figure at all</b>. In a "
      "category twenty years old, that absence is itself informative.</p>"
      + cite("pethub_pricing", "returnme_home"))

# ============================================================== TRACKERS ====

d.h2("2. Bluetooth trackers: your strongest structural argument", "trackers")
d.p("This is the comparison to lead with, because it is the one where the "
    "numbers are unambiguous and in your favour.")

d.fig(hbar([Bar(n, p, color=NEGATIVE) for n, p, _, _, _ in D.TRACKERS]
           + [Bar("Passive NFC sticker, 1,000 units", 0.58,
                  color=POSITIVE)],
           unit="", dp=2, label_w=210, width=560, row_h=30),
      "Per-unit hardware cost, vendor list prices",
      "The passive tag is 43&ndash;60&times; cheaper and has no battery to die.")

d.table(
    ["Tracker", "Price", "Battery", "Finder-contact path", "Network claimed"],
    [[f"<b>{n}</b>", f"${p:.2f}", b, f, w] for n, p, b, f, w in D.TRACKERS],
    title="What $25–35 actually buys",
    source=cite("airtag_buy", "airtag_page", "smarttag2", "tile_mate",
                "chipolo", "pebblebee", "gototags"))

d.box("insight", "The argument that survives scrutiny",
      "<p>A tracker answers <b>where is it</b>. It does not answer <b>how do I "
      "get it back</b>, and on a campus those are different problems. Reporting "
      "shows the gap plainly: a tracker can put a stolen object inside a "
      "building, and the owner still cannot retrieve it &mdash; location is not "
      "probable cause, and police need more before they can act.</p>"
      "<p>Samsung concedes the physical limit in its own product copy: accuracy "
      "degrades when the tag is <b>in a drawer, behind a wall, or in a car</b>. "
      "A lost-property drawer is all three. <b>The moment your item reaches the "
      "place it is most likely to be, the tracker is at its worst and a passive "
      "tag is unaffected.</b></p>"
      + cite("smarttag2", "unwanted"))

d.box("win", "One regulatory advantage you get for free",
      "<p>Apple and Google's cross-platform unwanted-tracking standard alerts a "
      "user when an <b>unknown Bluetooth tracker travels with them</b>. Every "
      "product in the table above lives inside that regime and inherits the "
      "stalking problem it exists to mitigate.</p>"
      "<p><b>A passive tag is outside it entirely</b> &mdash; no battery, no "
      "broadcast, no autonomous tracking, nothing to follow anyone with. It "
      "reveals itself only when someone deliberately holds a phone against it. "
      "Say this out loud; it is a genuine and permanent structural advantage."
      "</p>"
      "<p class=\"muted\">Do not overclaim it. Your <i>server</i> still logs "
      "scans, and scan logs tied to students are personal data under FERPA in "
      "the US and GDPR in Europe. The tag is exempt. Your database is not.</p>"
      + cite("unwanted", "ferpa", "gdpr"))

# =========================================================== INSTITUTIONAL ==

d.h2("3. The institutional systems all start too late", "saas")
d.p("This is the finding that matters most, and it is unusually clean. I had "
    "eight lost-property platforms opened and read. <b>Every single one begins "
    "when an item is already in a staff member's hands.</b>")

d.table(
    ["Platform", "What it is", "Workflow begins", "Identifies the item itself?",
     "Named universities", "Price"],
    [[f"<b>{n}</b>", w, b, chip("no", "No") if i == "No" else i, u, p]
     for n, w, b, i, u, p in D.SAAS],
    title="Institutional lost-property software",
    sub="Matching is by photograph, description, keyword or an internal "
        "inventory barcode applied after hand-in \u2014 never by a code the "
        "owner put on the object beforehand.",
    source=cite("chargerback", "chargerback_start", "repoapp", "repoapp_price",
                "pixit", "pixit_price", "reclaimhub", "notlost", "troov",
                "novafind", "novafind_price", "missingx"))

d.box("win", "State the gap this precisely, and it will hold",
      "<p><b>Wrong:</b> &ldquo;Existing lost-and-found systems cannot identify "
      "items.&rdquo; A judge who knows the market will correct you, and they "
      "will be right.</p>"
      "<p><b>Right:</b> &ldquo;Every deployed system is an <i>inventory and "
      "matching</i> tool. It assumes the item has already reached a desk, and "
      "then tries to pair it with an owner who has separately filed a loss "
      "report. Both halves have to happen. We remove the guessing by putting "
      "the identity on the object.&rdquo;</p>"
      "<p>NotLost's own FAQ states the boundary for you: it is a software "
      "provider, the venue physically manages the items, and the public cannot "
      "even see the inventory.</p>"
      + cite("notlost", "chargerback"))

d.box("caveat", "And they are not cheap, which is your opening",
      "<p>RepoApp publishes <b>$999.99 to $1,999.99 per year, for a single "
      "campus</b> &mdash; each additional building is a separate account. Pixit "
      "is <b>$35&ndash;37 per user per month</b>. Nova Find starts at "
      "<b>&euro;1,500 a year</b>. These are real budgets already being spent on "
      "the second half of the problem, by universities that have no tool at all "
      "for the first half.</p>"
      + cite("repoapp_price", "pixit_price", "novafind_price"))

# =============================================================== CAMPUS =====

d.h2("4. On campus, bikes are solved and everything else is not", "campus")
d.p("Universities already run property schemes. Understanding exactly what they "
    "do is what lets you say &ldquo;this is new&rdquo; without being wrong.")

d.table(
    ["Institution", "Scheme", "What is physically on the item", "Who can read it"],
    [[f"<b>{i}</b>", s, o, r] for i, s, o, r in D.CAMPUS_SCHEMES],
    title="Campus property programmes",
    sub="Note the fourth column. In every general-property scheme, the only "
        "reader is law enforcement, after recovery.",
    source=cite("towson", "usc_id", "duke_engrave", "vcu_reg", "utaustin",
                "cuboulder"))

d.box("insight", "The bike registries prove your model — for one object type",
      f"<p>Bike Index runs <b>{D.BIKE_INDEX['registered']:,} registered bikes</b> "
      f"with <b>{D.BIKE_INDEX['recovered']:,} recovered</b>, uses <b>QR "
      "stickers</b>, and is deployed at CU Boulder, Penn State, Princeton, UC "
      "Davis, UCSD, UCLA, Maryland, Pittsburgh and Washington. Project 529 "
      f"claims <b>{D.P529['searchable']} searchable bikes</b> across "
      f"<b>{D.P529['campus_partners']} campus and community partners</b>, with a "
      f"scannable tamper-evident QR shield.</p>"
      f"<p>Project 529 reports <b>{D.P529['shield_recovery']}% recovery with the "
      f"shield against {D.P529['no_shield_recovery']}% without</b>, over "
      f"{D.P529['cases']:,} theft cases. Treat that as a vendor figure, not a "
      "trial &mdash; but the direction is consistent and the scale is real.</p>"
      "<p><b>This is the best possible news for you.</b> The exact mechanism you "
      "propose is already proven at scale on campuses. It has simply never been "
      "applied to anything that is not a bicycle.</p>"
      + cite("bikeindex", "bikeindex_schools", "p529_le", "p529_schools"))

d.fig(hbar([Bar("Reported the theft to police", float(D.IU["reported"]),
                color=NEGATIVE),
            Bar("Bike was registered", float(D.IU["registered"]), color=ACCENT),
            Bar("Bike was recovered", float(D.IU["recovered"]),
                color=POSITIVE)],
           unit="%", dp=0, label_w=210, width=560, row_h=30),
      "Indiana University bike-theft survey, autumn 2024",
      "590 respondents, 387 bike owners. Registration is free and it still "
      "reaches barely a third of them \u2014 and one bike in ten comes back.",
      source=cite("iubike"))

d.box("warn", "The single best number in this entire report",
      f"<p>UT Austin recovers bikes and then <b>auctions roughly "
      f"{D.UT_AUSTIN_AUCTIONED} of them a year as surplus, because they cannot "
      "be traced to an owner</b>. The university has the property. The owner "
      "wants it. The university has an identity system containing that owner. "
      "And the item is sold anyway, because there is no link between the object "
      "and the record.</p>"
      "<p><b>That is your product, described by the problem it solves, in one "
      "sentence, using a university's own published figure.</b> Open with it."
      "</p>"
      + cite("utaustin", "iubike"))

# ============================================================== NOVELTY =====

d.h2("5. What is actually unoccupied", "gap")

d.table(
    ["Claim you might make", "Occupied by", "Safe to claim?"],
    [["Passive tag, finder needs no app",
      "AirTag, SmartTag2, Tile, PetHub, ReturnMe, ByteTag, Boomerang, Dynotag",
      chip("no", "No")],
     ["Finder scans, owner is notified",
      "Tile Scan Me If Found, PetHub, ReturnMe, Okoban", chip("no", "No")],
     ["Finder never learns the owner's identity",
      "ReturnMe proxies by default; PetHub offers a phone bridge",
      chip("part", "Weakly")],
     ["Cheaper than a Bluetooth tracker",
      "Every passive tag vendor, equally", chip("part", "True, not yours")],
     ["QR/registry recovery works on campus",
      "Bike Index and Project 529 &mdash; but bikes only",
      chip("part", "Precedent, not competition")],
     ["<b>Tag resolves against the institution's own identity system</b>",
      "<b>Nobody found</b>", chip("yes", "Yes")],
     ["<b>Institution's chokepoints are the scanner network</b>",
      "<b>Nobody found</b>", chip("yes", "Yes")],
     ["<b>Item-side identity feeding an existing lost-property desk</b>",
      "<b>Nobody found</b>", chip("yes", "Yes")]],
    title="Novelty, claim by claim",
    sub="Rows marked No are commodity. The three in bold are the report's "
        "actual finding.")

d.box("win", "The defensible sentence",
      "<p>&ldquo;Consumer tags make an item say <i>call this stranger</i>. "
      "Lost-property software helps staff sort things that already reached a "
      "desk. <b>We make the item say <i>I belong to a student at this "
      "university</i> &mdash; to the university, which already has a way to "
      "reach them, and already has the item.</b>&rdquo;</p>"
      "<p>Every clause there survived checking against a primary source. Do not "
      "add a fourth.</p>")

d.box("caveat", "The closest thing to a direct competitor is academic, not commercial",
      "<p>A 2025 project at USTP Panaon built a QR-plus-database lost-and-found "
      "system for a campus and evaluated it as <i>Very Good</i> on "
      "functionality, reliability, usability, efficiency and security. A 2024 "
      "IEEE paper proposes personalised QR item registration for campuses "
      "without a measured deployment. Neither is a product, and neither reports "
      "recovery outcomes &mdash; but they are proof the idea occurs to people, "
      "so cite them as related work rather than being told about them.</p>"
      + cite("ustp", "lostnet"))

# ============================================================ ON STAGE =====

d.h2("6. How to handle this on stage", "pitch")

d.table(
    ["If a judge says\u2026", "Do not say", "Say"],
    [["&ldquo;Isn't this an AirTag?&rdquo;",
      "&ldquo;AirTags are expensive&rdquo;",
      "&ldquo;An AirTag <i>shows the finder your phone number</i> and costs $29 "
      "with a battery. Ours costs under a dollar, has no battery, and the "
      "finder never learns who you are. And in a lost-property drawer the "
      "Bluetooth is useless &mdash; Samsung says so in their own spec.&rdquo;"],
     ["&ldquo;PetHub does this.&rdquo;",
      "&ldquo;We're different&rdquo;",
      "&ldquo;They do, and it works. They have no institution. We do &mdash; the "
      "university already knows how to reach every student and already holds "
      "the item.&rdquo;"],
     ["&ldquo;Universities have lost-and-found already.&rdquo;",
      "&ldquo;Theirs is bad&rdquo;",
      "&ldquo;They do, and they pay $1,000&ndash;2,000 a year for it. It starts "
      "when the item hits the desk. UT Austin still auctions 350 recovered "
      "bikes a year they cannot trace.&rdquo;"],
     ["&ldquo;Who scans a random QR?&rdquo;",
      "&ldquo;People are helpful&rdquo;",
      "&ldquo;In the largest field experiment ever run, 17,303 wallets across "
      "40 countries, adding money <i>raised</i> return rates. Finders try. The "
      "constraint is that they cannot work out who to return it to.&rdquo;"]],
    title="Objection handling",
    sub="Every right-hand answer is backed by a source in this report.",
    source=cite("airtag_found", "smarttag2", "pethub_privacy", "repoapp_price",
                "utaustin", "cohn"))

# =========================================================== LIMITATIONS ====

d.h2("Limitations of this report", "limits")
d.ul([
    "<b>Vendor claims dominate this market.</b> Of the recovery figures found, "
    "not one is an independent study. PetHub, ReturnMe, Chargerback, Troov, "
    "NotLost and Project 529 all publish self-reported numbers with no "
    "denominator and no methodology.",
    "<b>Absence of evidence is not proof of absence.</b> &ldquo;Nobody found&rdquo; "
    "means no public source surfaced in this search. A private pilot, an "
    "unlaunched startup or a non-English deployment would not appear.",
    "<b>Four sources could not be opened</b> and nothing from them is asserted "
    "here: " + "; ".join(D.UNREACHABLE) + ".",
    "<b>The named university customers are vendor logos.</b> They evidence a "
    "commercial relationship, not satisfaction or scale.",
    "<b>Prices move.</b> All vendor prices were read on 29 August 2026 and "
    "several pages are region-dependent.",
])

# =============================================================== SOURCES ====

d.h2("Sources", "sources")
rows = []
for k, (t, org, url, kind, yr) in sorted(S.items(), key=lambda x: x[1][1]):
    tick = " &#10003;" if k in LEAD else ""
    rows.append([f"<b>{org}</b>{tick}", f'<a href="{url}">{t}</a>',
                 chip("vendor" if kind == "vendor" else
                      "official" if kind == "official" else "academic", kind),
                 yr])
d.table(["Organisation", "Document", "Grade", "Year"], rows,
        title=f"{len(S)} primary sources",
        sub="&#10003; marks sources the lead agent opened and read personally. "
            "Everything else was opened by a research agent that reported the "
            "literal wording.")

d.h2("Reverting this document", "revert")
d.p("This report is generated. Delete <code>research/prior-art.html</code>, "
    "<code>research/build_priorart.py</code> and "
    "<code>research/data_priorart.py</code>; nothing outside those three files "
    "was touched. Rebuild with <code>python3 research/build_priorart.py</code>.")

# ================================================================= WRITE ====

_mast = (MASTHEAD.replace("__NSRC__", str(len(S)))
         .replace("__NFIG__", str(d.fig_n)).replace("__NTAB__", str(d.tab_n)))
OUT.write_text(d.html("Prior art: lost-property reunification", _mast),
               encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes, {d.fig_n} figures, "
      f"{d.tab_n} tables, {len(S)} sources)")
