"""Verified source data for the Whoops Tag prior-art and competitive report.

Same discipline as `data.py` and `data_opportunistic.py`: every figure below was
read out of the cited primary source by the lead agent or by a scout that opened
the page and reported the literal wording. `VERIFIED_BY_LEAD` marks the ones I
opened personally.

Evidence grading, used throughout the report:
  official   - platform or institution documentation (Apple, Google, a university)
  academic   - peer-reviewed or archived research output
  vendor/PR  - the company's own marketing. Never treated as measurement.

The single most important discipline in this file: consumer lost-and-found
vendors publish recovery numbers with **no denominator**. "115,000 recoveries"
is not a recovery *rate*. Those are tagged vendor/PR and the report says so.
"""

from __future__ import annotations

VERIFIED_BY_LEAD = {
    "apple_mifare_family", "android_mifare_optional", "mfrc522_ntag",
}

# ---------------------------------------------------------------- sources ---

SOURCES: dict[str, tuple[str, str, str, str, str]] = {
    # --- consumer tags -----------------------------------------------------
    "pethub_privacy": ("QR Pet ID Tags & Privacy: What You Need to Know", "PetHub",
                       "https://www.pethub.com/articles/4070545/"
                       "qr-pet-id-tags-privacy-what-you-need-to-know",
                       "vendor", "2026"),
    "pethub_price": ("QR ID Pet Tag, Classic Aluminum", "PetHub",
                     "https://shop.pethub.com/products/qr-id-pet-tag-aluminum",
                     "vendor", "2026"),
    "pethub_pricing": ("PetHub pricing and plans", "PetHub",
                       "https://www.pethub.com/pricing?language=en", "vendor", "2026"),
    "returnme": ("ReturnMe \u2014 why ReturnMe", "ReturnMe",
                 "https://www.return.me/page/why-returnme", "vendor", "2026"),
    "returnme_home": ("ReturnMe \u2014 pricing and recovery claims", "ReturnMe",
                      "https://www.return.me/", "vendor", "2026"),
    "okoban": ("Okoban universal lost and found registry", "Okoban / Travel Sentry",
               "https://www.okoban.com/en", "vendor", "2026"),
    "bytetag": ("ByteTag Explorer Silicone", "ByteTag",
                "https://shop.bytetag.co/products/explorer", "vendor", "2026"),
    "boomerang": ("BoomerangTag frequently asked questions", "Boomerang",
                  "https://theboomerangtag.com/pages/faqs", "vendor", "2026"),
    "dynotag": ("Dynotag pricing and service model", "Dynotag",
                "https://dynoverse.dynotag.com/welcome/about/pricing/",
                "vendor", "2026"),
    "crashtag": ("Crashtag details", "Crashtag",
                 "https://www.crashtag.me/details/", "vendor", "2026"),
    "tile_lf": ("Tile Lost and Found: contact owner by scanning a code",
                "Tile / Life360",
                "https://www.tile.com/blog/tile-lost-and-found-contact-owner-scan-code",
                "vendor", "2026"),

    # --- Apple -------------------------------------------------------------
    "airtag_lost": ("Mark an item as lost in Find My", "Apple",
                    "https://support.apple.com/guide/iphone/"
                    "mark-an-item-as-lost-iph1b451b75f/ios", "official", "2026"),
    "airtag_found": ("If you find an AirTag or Find My accessory", "Apple",
                     "https://support.apple.com/en-us/119874", "official", "2026"),
    "apple_mifare_family": ("NFCMiFareFamily \u2014 Core NFC", "Apple",
                            "https://developer.apple.com/documentation/corenfc/"
                            "nfcmifarefamily", "official", "2026"),

    # --- platform ----------------------------------------------------------
    "android_mifare_optional": ("MifareClassic \u2014 Android NFC reference", "Google",
                                "https://developer.android.com/reference/android/"
                                "nfc/tech/MifareClassic", "official", "2026"),
    "mfrc522_ntag": ("MFRC522 standard performance MIFARE and NTAG frontend",
                     "NXP Semiconductors",
                     "https://www.nxp.com/docs/en/data-sheet/MFRC522.pdf",
                     "official", "2016"),

    # --- institutional SaaS -------------------------------------------------
    "chargerback": ("Chargerback \u2014 how it works", "Chargerback",
                    "https://www.chargerback.com/how-it-works.asp", "vendor", "2026"),
    "chargerback_start": ("Chargerback \u2014 getting started and pricing",
                          "Chargerback",
                          "https://www.chargerback.com/getting-started.asp",
                          "vendor", "2026"),
    "repoapp": ("RepoApp lost and found software", "RepoApp",
                "https://www.repoapp.com/", "vendor", "2026"),
    "reclaimhub": ("ReclaimHub lost property software", "ReclaimHub",
                   "https://reclaimhub.com/", "vendor", "2026"),
    "notlost": ("NotLost lost property software", "NotLost",
                "https://notlost.com/", "vendor", "2026"),
    "pixit": ("Pixit lost and found (formerly Crowdfind)", "Pixit",
              "https://www.pixithq.com/", "vendor", "2026"),
    "pixit_price": ("Pixit pricing", "Pixit",
                    "https://www.pixithq.com/pricing", "vendor", "2026"),
    "troov": ("Troov lost and found platform", "Troov",
              "https://troov.com/", "vendor", "2026"),
    "novafind": ("Nova Find features", "Nova Find / RUBICON",
                 "https://www.nova-find.eu/en/features/", "vendor", "2026"),
    "novafind_price": ("Nova Find prices", "Nova Find / RUBICON",
                       "https://www.nova-find.eu/en/prices/", "vendor", "2026"),
    "missingx": ("MissingX for business", "MissingX",
                 "https://www.missingx.com/en/missingx/business", "vendor", "2026"),

    # --- bike registries ----------------------------------------------------
    "bikeindex": ("Bike Index \u2014 registry home and live counters", "Bike Index",
                  "https://bikeindex.org/", "vendor", "2026"),
    "bikeindex_schools": ("Bike Index for schools", "Bike Index",
                          "https://bikeindex.org/for_schools", "vendor", "2026"),
    "p529_le": ("Project 529 Garage for law enforcement", "Project 529",
                "https://project529.com/garage/law_enforcement", "vendor", "2026"),
    "p529_schools": ("Project 529 Garage for schools", "Project 529",
                     "https://project529.com/garage/schools", "vendor", "2026"),

    # --- university deployments ---------------------------------------------
    "utaustin": ("Bicycle and scooter registration", "University of Texas at Austin",
                 "https://police.utexas.edu/community-safety/"
                 "bicycle-scooter-registration", "official", "2026"),
    "cuboulder": ("Bike registration", "University of Colorado Boulder",
                  "https://www.colorado.edu/police/crime-prevention/safety-tips/"
                  "bike-registration", "official", "2026"),
    "iubike": ("Bike theft survey results", "Indiana University",
               "https://transportation.indiana.edu/about-us/news/"
               "bike-theft-survey.html", "official", "2024"),
    "towson": ("Personal property registration", "Towson University Police",
               "https://www.towson.edu/public-safety/police/services/"
               "personal-property.html", "official", "2026"),
    "usc_id": ("ID engraving \u2014 Operation Identification",
               "University of Southern California DPS",
               "https://dps.usc.edu/services/id-engraving/", "official", "2026"),
    "duke_engrave": ("Engraving service", "Duke University Police",
                     "https://police.duke.edu/services/engraving/", "official", "2026"),
    "vcu_reg": ("Computer registration", "Virginia Commonwealth University Police",
                "https://police.vcu.edu/services/computer-registration/",
                "official", "2026"),

    # --- academic -----------------------------------------------------------
    "ustp": ("QR-based lost and found system for an academic setting",
             "USTP Panaon (Zenodo record)",
             "https://zenodo.org/records/15045175", "academic", "2025"),
    "lostnet": ("LostNet: a fast and accurate lost-and-found system",
                "PLOS ONE",
                "https://journals.plos.org/plosone/article?id=10.1371/"
                "journal.pone.0310998", "academic", "2024"),
    "wechat": ("Field and online experiments on lost-wallet reporting",
               "Scientific Reports",
               "https://doi.org/10.1038/s41598-025-87804-z", "academic", "2025"),
    "cohn": ("Civic honesty around the globe", "Science",
             "https://www.science.org/doi/10.1126/science.aau8712",
             "academic", "2019"),
}

# ------------------------------------------------------- consumer tag table -

# name, mechanism, finder needs app?, identity model, price, recovery claim
CONSUMER_TAGS = [
    ("PetHub", "QR", "No", "proxy available",
     "$9.95", "96% of recovered pets home <24h"),
    ("ReturnMe", "Printed ID number", "No", "full proxy",
     "$9.99", "115,000+ recoveries, 14h average"),
    ("ByteTag", "QR", "No", "owner chooses", "$24.95", "none published"),
    ("Crashtag", "QR", "No", "display only", "$29.90", "none published"),
    ("Okoban", "12-digit UID", "No", "registry relay",
     "free for life", "none published"),
    ("Tile Lost &amp; Found", "QR", "No", "display only",
     "not exposed", "none published"),
    ("Boomerang", "QR", "No", "owner chooses", "not exposed", "none published"),
    ("Dynotag", "QR / NFC", "No", "owner chooses", "not exposed", "none published"),
]

# ------------------------------------------------------- institutional SaaS -

# name, what it is, starts when, item-side identity?, named universities, price
SAAS = [
    ("Chargerback", "Hotel and airline lost property", "Item reaches a desk",
     "No", "\u2014", "free to partner, per-shipment fee"),
    ("RepoApp", "Inventory and claims", "Item reaches a desk", "No",
     "UMBC, UT Dallas, UCSD, Tulane, Cal Poly, Calgary, Full Sail, Adelphi",
     "not published"),
    ("Pixit <small>(was Crowdfind)</small>", "Photo-first logging",
     "Item reaches a desk", "No", "Michigan, Virginia Tech",
     "$35&ndash;37 per user per month"),
    ("ReclaimHub", "Cloud lost property", "Item reaches a desk", "No",
     "Florida State", "trial, then not published"),
    ("NotLost", "AI image cataloguing", "Item reaches a desk", "No",
     "\u2014 <small>(TfL, O2, Westfield, Uber)</small>", "not published"),
    ("Troov", "Declaration matching", "Item reaches a desk", "No",
     "\u2014 <small>(SNCF, Louvre, Nice Airport)</small>", "not published"),
    ("Nova Find", "Municipal and transport", "Item reaches a desk", "No",
     "\u2014", "from \u20ac1,500 per year"),
    ("MissingX", "Cloud workflow", "Item reaches a desk", "No", "\u2014",
     "quote only"),
]

# ------------------------------------------------------------ bike registry -

BIKE_INDEX = {
    "registered": 1_814_590,
    "stolen": 179_349,
    "recovered": 18_158,
    "value": 38_252_589,
    "partners": 1_856,
}

P529 = {
    "searchable": "3.3M",
    "agencies": 791,
    "campus_partners": 789,
    "shield_recovery": 17.8,
    "no_shield_recovery": 8.5,
    "cases": 35_000,
}

# Indiana University Fall 2024 survey, 590 respondents / 387 bike owners
IU = {"registered": 36, "recovered": 10, "reported": 58}

# --------------------------------------------------- campus property schemes -

# institution, scheme, what is on the item, who reads it
CAMPUS_SCHEMES = [
    ("Towson", "Personal property registration",
     "Nothing \u2014 serials in a database", "Law enforcement only"),
    ("USC", "Operation ID engraving",
     "Engraved student ID or licence number", "Police, after recovery"),
    ("Duke", "Free engraving",
     "Engraved driver's licence number", "Police, after recovery"),
    ("VCU", "Computer registration",
     "Visible licence code, MAC on file", "Police, via DMV query"),
    ("UT Austin", "Mandatory bike and scooter registration",
     "Registration decal", "UTPD"),
    ("CU Boulder", "Bike Index, since Spring 2021",
     "QR sticker", "Anyone who scans"),
]

UT_AUSTIN_AUCTIONED = 350  # recovered bikes per year, auctioned as untraceable

# ------------------------------------------------------- bluetooth trackers -

# name, price USD, battery, finder-contact feature, network claim
TRACKERS = [
    ("Apple AirTag", 29.00, "&gt;1 year, CR2032",
     "Lost Mode NFC tap shows owner's contact", "&gt;1 billion Apple devices"),
    ("Samsung SmartTag2", 29.99, "up to 500 days, CR2032",
     "Lost Mode NFC shows owner's contact", "not disclosed"),
    ("Tile Mate", 24.99, "3 years, sealed",
     "Scan Me If Found QR, note + one-time location", "not disclosed"),
    ("Chipolo ONE", 25.00, "up to 2 years, CR2032",
     "community search only", "not disclosed"),
    ("Pebblebee Clip 5", 34.99, "rechargeable, ~1 year",
     "via Find My or Find Hub", "not disclosed"),
]

# GoToTags custom-printed NTAG213, volume pricing
PASSIVE_COST = {500: None, 1_000: 0.58, 10_000: 0.35, 50_000: 0.24}

SOURCES.update({
    "airtag_buy": ("Buy AirTag", "Apple",
                   "https://www.apple.com/shop/buy-airtag/airtag/1-pack",
                   "vendor", "2026"),
    "airtag_page": ("AirTag", "Apple", "https://www.apple.com/airtag/",
                    "vendor", "2026"),
    "smarttag2": ("Galaxy SmartTag2", "Samsung",
                  "https://www.samsung.com/us/mobile-accessories/"
                  "galaxy-smarttag2-black-sku-ei-t5600bbegus/", "vendor", "2026"),
    "tile_mate": ("Tile Mate", "Life360 / Tile",
                  "https://www.life360.com/tile-trackers/product/black-mate",
                  "vendor", "2026"),
    "tile_scan": ("Scan Me If Found", "Life360 / Tile",
                  "https://support.life360.com/hc/en-us/articles/"
                  "30882597089559-Scan-Me-If-Found", "official", "2026"),
    "chipolo": ("Chipolo ONE", "Chipolo",
                "https://chipolo.net/en-us/products/chipolo-one", "vendor", "2026"),
    "pebblebee": ("Pebblebee Clip 5", "Pebblebee",
                  "https://pebblebee.com/products/clip-5", "vendor", "2026"),
    "gototags": ("Printed NFC sticker, NTAG213 \u2014 volume pricing", "GoToTags",
                 "https://store.gototags.com/printed-nfc-sticker-ntag213/",
                 "vendor", "2026"),
    "unwanted": ("Apple and Google deliver support for unwanted tracking alerts",
                 "Apple / Google",
                 "https://www.apple.com/newsroom/2024/05/apple-and-google-deliver-"
                 "support-for-unwanted-tracking-alerts-in-ios-and-android/",
                 "official", "2024"),
    "ferpa": ("Personally identifiable information in education records",
              "US Department of Education",
              "https://studentprivacy.ed.gov/content/"
              "personally-identifiable-information-education-records",
              "official", "2026"),
    "gdpr": ("GDPR Article 4 \u2014 definitions", "EUR-Lex",
             "https://eur-lex.europa.eu/eli/reg/2016/679/art_4/oj/eng",
             "official", "2016"),
    "repoapp_price": ("RepoApp pricing", "RepoApp",
                      "https://www.repoapp.com/pricing/", "vendor", "2026"),
})

# RepoApp published yearly pricing, one campus per account
REPOAPP_PRICE = [("Basic", 999.99, "20 users, 6,000 records"),
                 ("Plus", 1_399.99, "10,000 records, webcam photos"),
                 ("Premium", 1_999.99, "18,000 records, public claim forms")]

# Sources that could not be opened. Named so the report can admit them.
UNREACHABLE = ["Have It Back (timed out)", "iLost (HTTP 403)",
               "BoomerangIt B2U (TLS failure)",
               "Tile Lost &amp; Found label price (page redirects)"]
