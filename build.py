#!/usr/bin/env python3
"""Sitegenerator voor vanderhamecologie.nl.

Leest content/*.html (frontmatter + HTML-body), giet dat door
templates/base.html en schrijft het resultaat naar docs/.
docs/ is de map die GitHub Pages publiceert.

Draaien:  python3 build.py
"""

import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
TEMPLATES = os.path.join(ROOT, "templates")
OUT = os.path.join(ROOT, "docs")

# Het eigen domein. GitHub Pages leest dit uit docs/CNAME en stuurt de
# apex (vanderhamecologie.nl) automatisch door naar www.
CUSTOM_DOMAIN = "www.vanderhamecologie.nl"

CSS_VERSIE = "0"

# Bezoekersstatistiek, cookieloos. Leeg laten = geen enkel script op de site.
# Vul PLAUSIBLE in met het domein zoals het in het dashboard heet
# ("vanderhamecologie.nl"), of UMAMI met de scriptbron en de website-id.
# Beide meten zonder cookies en zonder persoonsgegevens, dus er is geen
# cookiebanner nodig. Zet er nooit Google Analytics bij zonder banner.
PLAUSIBLE = ""
UMAMI = {"src": "", "id": ""}

# GoatCounter, hetzelfde account dat hieon.nl al gebruikt. Cookieloos en zonder
# persoonsgegevens, dus geen cookiebanner nodig. Omdat beide sites naar dezelfde
# teller schrijven, krijgen de paden van deze site het voorvoegsel /vdhe, zodat
# ze in het dashboard gescheiden blijven van HIEON. Maakt Wouter later een eigen
# GoatCounter-site aan, dan kan het voorvoegsel eruit.
GOATCOUNTER = "https://hieon.goatcounter.com/count"
GOATCOUNTER_PREFIX = "/vdhe"


def css_versie():
    """Korte hash van de stylesheet, als ?v= achter de CSS-URL.

    GitHub Pages serveert assets met tien minuten cache en zonder deze hash
    zien terugkerende bezoekers na een deploy oude opmaak bij nieuwe HTML.
    Verandert de CSS, dan verandert de URL en haalt de browser hem opnieuw op.
    """
    pad = os.path.join(OUT, "assets", "css", "site.css")
    if not os.path.exists(pad):
        return "0"
    with open(pad, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]


def analytics_html():
    if GOATCOUNTER:
        pad = ""
        if GOATCOUNTER_PREFIX:
            pad = ('\n<script>window.goatcounter = {path: function(p){ return "%s" + p; }};</script>'
                   % GOATCOUNTER_PREFIX)
        return (pad + '\n<script data-goatcounter="%s" async src="https://gc.zgo.at/count.js"></script>'
                % GOATCOUNTER)
    if PLAUSIBLE:
        return ('\n<script defer data-domain="%s" '
                'src="https://plausible.io/js/script.js"></script>' % PLAUSIBLE)
    if UMAMI.get("src") and UMAMI.get("id"):
        return ('\n<script defer src="%s" data-website-id="%s"></script>'
                % (UMAMI["src"], UMAMI["id"]))
    return ""

SITE = {
    "name": "Van Der Ham Ecologie",
    "url": "https://www.vanderhamecologie.nl",
    "phone": "06-23002037",
    "phone_link": "+31623002037",
    "email": "info@vanderhamecologie.nl",
    "kvk": "88425789",
    "btw": "NL004604823B13",
    "street": "Koepellaan 11",
    "postcode": "3705 ZS",
    "city": "Zeist",
    "year": date.today().year,
}

# Diensten, gegroepeerd zoals in het menu van de huidige site.
DIENSTEN = [
    ("Bouw en ruimtelijke ontwikkeling", [
        ("/quickscan-flora-en-fauna", "Quickscan flora en fauna"),
        ("/vleermuisonderzoek", "Vleermuisonderzoek"),
        ("/huismusonderzoek", "Huismusonderzoek"),
        ("/gierzwaluwonderzoek", "Gierzwaluwonderzoek"),
        ("/amfibieen-reptielenonderzoek", "Amfibieën- &amp; reptielenonderzoek"),
        ("/beschermde-planten-onderzoek", "Beschermde planten onderzoek"),
        ("/dagvlinderonderzoek", "Dagvlinderonderzoek"),
        ("/zoogdieronderzoek", "Grondgebonden zoogdieren en marters"),
        ("/broedvogelonderzoek", "Broedvogelonderzoek"),
        ("/libellenonderzoek", "Libellenonderzoek"),
    ]),
    ("Beheer, waterschappen en TBO's", [
        ("/flora-en-faunacheck", "Flora- en faunacheck"),
        ("/ecologische-begeleiding", "Ecologische begeleiding"),
        ("/invasieve-exoten", "Invasieve exoten"),
        ("/inventarisaties-monitoring", "Inventarisatie en monitoring"),
        ("/nachtvlinderonderzoek", "Nachtvlinderonderzoek"),
    ]),
    ("Advies, gebied en vergunning", [
        ("/gebiedsbescherming", "Gebiedsbescherming"),
        ("/inrichtingsadvies", "Inrichtingsadvies"),
        ("/vergunningstraject", "Vergunning en soortenmanagement"),
    ]),
]

DOELGROEPEN = [
    ("/voor-waterschappen", "Waterschappen &amp; TBO's"),
    ("/voor-gemeenten", "Gemeenten"),
    ("/voor-aannemers", "Aannemers &amp; ontwikkelaars"),
    ("/voor-evenementen", "Evenementen"),
    ("/voor-particulieren", "Particulieren"),
]

ARROW = (
    '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true" focusable="false">'
    '<path d="M2.5 8h11m0 0L9 3.5M13.5 8 9 12.5" stroke="currentColor" stroke-width="1.6" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>'
)

NAAST_WERK = [
    ("/projects#invested-birding", "Invested Birding"),
    ("/projects#natuurspeld", "Natuurspeld"),
    ("/projects#big-week", "Big Week"),
]

# Provinciepagina's heten <dienst>-<provincie>. De volgorde hieronder is de
# volgorde waarin de doorverwijzingen onderaan zo'n pagina verschijnen.
PROVINCIES = [
    ("gelderland", "Gelderland"),
    ("utrecht", "Utrecht"),
    ("overijssel", "Overijssel"),
    ("noord-brabant", "Noord-Brabant"),
    ("limburg", "Limburg"),
    ("zuid-holland", "Zuid-Holland"),
    ("noord-holland", "Noord-Holland"),
    ("zeeland", "Zeeland"),
    ("flevoland", "Flevoland"),
    ("drenthe", "Drenthe"),
    ("groningen", "Groningen"),
    ("fryslan", "Fryslân"),
]

# Kop waaronder de doorverwijzingen komen te staan, per dienst.
PROVINCIE_DIENSTEN = {
    "quickscan-flora-en-fauna": "Quickscan",
    "vleermuisonderzoek": "Vleermuisonderzoek",
    "huismusonderzoek": "Huismusonderzoek",
    "gierzwaluwonderzoek": "Gierzwaluwonderzoek",
    "ecologisch-advies": "Ecologisch advies",
}

# Oude URL's van de vorige sitegenerator waar nog zoekverkeer op staat.
# Een statische host kent geen serverredirects: een pagina hernoemen zonder
# doorverwijzing is een stille verwijdering. Voor elke oude slug schrijft de
# bouw daarom een minimale doorverwijsstub in docs/. De stubs komen bewust
# niet in de sitemap en niet in de navigatie of provincielijsten terecht.
REDIRECTS = {
    "/ecologische-begeleiding-bouw": "/ecologische-begeleiding/",
    "/natuuronderzoek-bouwen-verbouwen": "/quickscan-flora-en-fauna/",
    "/vdhe": "/",
}


def schrijf_redirects(bestaande_slugs):
    """Schrijft voor elke oude slug een doorverwijsstub naar het nieuwe adres.

    Kaal en zonder sitechrome of statistiek: de meta-refresh stuurt de
    bezoeker meteen door, de zichtbare link is het vangnet voor wie niet
    automatisch doorgaat, en de canonical wijst zoekmachines naar het doel.
    """
    for oud, doel in REDIRECTS.items():
        if oud in bestaande_slugs:
            print("let op: redirect %s botst met een bestaande pagina, overgeslagen" % oud)
            continue
        doel_url = SITE["url"] + doel
        stub = (
            "<!doctype html>\n"
            '<html lang="nl">\n'
            "<head>\n"
            '<meta charset="utf-8">\n'
            '<meta http-equiv="refresh" content="0; url=%(url)s">\n'
            '<link rel="canonical" href="%(url)s">\n'
            "<title>Doorverwijzing | Van Der Ham Ecologie</title>\n"
            "</head>\n"
            "<body>\n"
            '<p>Deze pagina is verhuisd. U vindt de informatie op '
            '<a href="%(url)s">%(url)s</a>.</p>\n'
            "</body>\n"
            "</html>\n"
        ) % {"url": doel_url}
        stubmap = os.path.join(OUT, oud.strip("/"))
        os.makedirs(stubmap, exist_ok=True)
        with open(os.path.join(stubmap, "index.html"), "w", encoding="utf-8") as f:
            f.write(stub)


def split_provincie_slug(slug):
    """Splitst '/huismusonderzoek-utrecht' in ('huismusonderzoek', 'utrecht')."""
    naam = slug.strip("/")
    for suffix, _ in PROVINCIES:
        if naam.endswith("-" + suffix):
            dienst = naam[: -len(suffix) - 1]
            if dienst in PROVINCIE_DIENSTEN:
                return dienst, suffix
    return None, None


def provincie_links_html(slug, bestaande_slugs):
    """Chips naar dezelfde dienst in de andere provincies.

    Alleen provincies waarvoor de pagina ook echt bestaat, zodat er nooit
    naar een niet-bestaande pagina wordt gelinkt.
    """
    dienst, huidige = split_provincie_slug(slug)
    if not dienst:
        return ""
    label = PROVINCIE_DIENSTEN[dienst]
    chips = []
    for suffix, naam in PROVINCIES:
        if suffix == huidige:
            continue
        doel = "/%s-%s" % (dienst, suffix)
        if doel in bestaande_slugs:
            chips.append('<a class="provlink" href="%s">%s</a>' % (doel, naam))
    if not chips:
        return ""
    return (
        '<section class="section section--cream">\n'
        '  <div class="wrap">\n'
        '    <div class="head head--center">\n'
        '      <h2>%s in andere provincies</h2>\n'
        '    </div>\n'
        '    <div class="provlinks" style="justify-content:center">%s</div>\n'
        '  </div>\n'
        '</section>\n\n' % (label, "".join(chips))
    )


# De dienstenlijstjes tonen een foto in een vakje van 84 bij 62 pixels, maar
# laadden het origineel van 800 tot 1000 pixels breed: achttien daarvan is
# bijna vier megabyte per pagina. De bouw maakt er een kleine variant van.
THUMB = (210, 155)
THUMB_MAP = os.path.join(OUT, "assets", "img", "thumbs")
_THUMB_IMG = re.compile(r'(?is)<img class="entry__thumb"[^>]*>')
_THUMB_SRC = re.compile(r'src="/assets/img/([^"/]+)"')


def maak_thumb(bestandsnaam):
    """Maakt (indien nodig) een kleine variant en geeft het pad terug.

    Zonder Pillow gebeurt er niets en blijft het origineel staan; de bouw mag
    hier niet op stuklopen.
    """
    bron = os.path.join(OUT, "assets", "img", bestandsnaam)
    if not os.path.exists(bron):
        return None
    doel = os.path.join(THUMB_MAP, bestandsnaam)
    if os.path.exists(doel) and os.path.getmtime(doel) >= os.path.getmtime(bron):
        return "/assets/img/thumbs/" + bestandsnaam
    try:
        from PIL import Image
    except ImportError:
        return None
    os.makedirs(THUMB_MAP, exist_ok=True)
    im = Image.open(bron).convert("RGB")
    bw, bh = im.size
    schaal = max(THUMB[0] / bw, THUMB[1] / bh)
    im = im.resize((max(1, round(bw * schaal)), max(1, round(bh * schaal))), Image.LANCZOS)
    nw, nh = im.size
    links, boven = (nw - THUMB[0]) // 2, (nh - THUMB[1]) // 2
    im = im.crop((links, boven, links + THUMB[0], boven + THUMB[1]))
    im.save(doel, quality=80, optimize=True, progressive=True)
    return "/assets/img/thumbs/" + bestandsnaam


def verklein_thumbs(html):
    """Laat elke entry__thumb naar de kleine variant wijzen."""

    def vervang(m):
        tag = m.group(0)
        s = _THUMB_SRC.search(tag)
        if not s:
            return tag
        klein = maak_thumb(s.group(1))
        if not klein:
            return tag
        tag = _THUMB_SRC.sub('src="%s"' % klein, tag, count=1)
        tag = re.sub(r'width="\d+"', 'width="%d"' % THUMB[0], tag, count=1)
        tag = re.sub(r'height="\d+"', 'height="%d"' % THUMB[1], tag, count=1)
        return tag

    return _THUMB_IMG.sub(vervang, html)


# Externe links (hieon.nl en wat er later bijkomt) openen in een nieuw tabblad,
# zodat de bezoeker de site niet kwijtraakt. rel="noopener" hoort daarbij: het
# voorkomt dat de geopende pagina via window.opener aan deze pagina kan komen.
_EXTERN = re.compile(r'(?is)<a\s([^>]*href="https?://([^"/]+)[^"]*"[^>]*)>(.*?)</a>')


def externe_links(html):
    eigen = CUSTOM_DOMAIN.replace("www.", "")

    def vervang(m):
        attrs, host, tekst = m.group(1), m.group(2), m.group(3)
        if eigen in host or "target=" in attrs.lower():
            return m.group(0)
        return ('<a %s target="_blank" rel="noopener">%s'
                '<span class="sronly"> (opent in een nieuw tabblad)</span></a>'
                % (attrs, tekst))

    return _EXTERN.sub(vervang, html)


def provincie_hub_html(slug, bestaande_slugs, dienst=None):
    """De provincielijst op een dienst-hoofdpagina, bijvoorbeeld /huismusonderzoek.

    Handmatig bijgehouden lijsten raakten achterop zodra er een provincie
    bijkwam, dus de bouw stelt ze samen uit de pagina's die er echt zijn.
    Met `dienst` kan een pagina de lijst van een andere dienst opnemen; dat
    gebeurt via {{provincies:<dienst>}} en is nodig voor ecologisch advies,
    dat zelf geen hoofdpagina heeft.
    """
    dienst = dienst or slug.strip("/")
    if dienst not in PROVINCIE_DIENSTEN:
        return ""
    label = PROVINCIE_DIENSTEN[dienst]
    links = []
    for suffix, naam in PROVINCIES:
        doel = "/%s-%s" % (dienst, suffix)
        if doel in bestaande_slugs:
            links.append('      <a href="%s">%s {{arrow}}</a>' % (doel, naam))
    if not links:
        return ""
    return (
        '<section class="section section--cream">\n'
        '  <div class="wrap">\n'
        '    <div class="head head--center">\n'
        '      <h2>%s per provincie</h2>\n'
        '      <p>Wij werken door heel Nederland. Voor deze provincies hebben wij een aparte pagina.</p>\n'
        '    </div>\n'
        '    <div class="linkrow" style="justify-content:center">\n%s\n    </div>\n'
        '  </div>\n'
        '</section>\n\n' % (label, "\n".join(links))
    )


# De handmatige provinciesectie op een dienst-hoofdpagina; wordt vervangen door
# de gegenereerde versie hierboven.
_HUB_SECTIE = re.compile(
    r'(?is)<section class="section">\s*<div class="wrap">\s*<div class="head head--center">\s*'
    r'<h2>[^<]*per provincie</h2>.*?</section>\s*'
)

# De kop stond op veel provinciepagina's zonder links eronder; de bouw zet er
# nu altijd een complete, kloppende lijst neer (of haalt de kop weg).
_PROV_KOP = re.compile(
    r'(?is)<h3>[^<]*in andere provincies</h3>\s*(?:<p>(?:\s*<a href="/[^"]*"[^>]*>[^<]*</a>)+\s*</p>)?'
)


def nav_html(current):
    """Bouwt de hoofdnavigatie. `current` is het pad van de huidige pagina."""

    def aria(path):
        return ' aria-current="page"' if path == current else ""

    diensten_cols = []
    for title, items in DIENSTEN:
        links = "".join(
            '<a href="%s"%s>%s</a>' % (h, aria(h), label) for h, label in items
        )
        diensten_cols.append(
            '<div><p class="dropdown__col-title">%s</p>%s</div>' % (title, links)
        )

    doelgroep_links = "".join(
        '<a href="%s"%s>%s</a>' % (h, aria(h), label) for h, label in DOELGROEPEN
    )
    naast_links = "".join('<a href="%s">%s</a>' % (h, l) for h, l in NAAST_WERK)

    caret = (
        '<svg class="nav__caret" viewBox="0 0 12 12" aria-hidden="true" focusable="false">'
        '<path d="M2 4.5 6 8.5 10 4.5" fill="none" stroke="currentColor" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )

    return """
      <nav class="nav" id="hoofdmenu" aria-label="Hoofdmenu">
        <div class="nav__item"><a class="nav__link" href="/about"%(a_about)s>Over ons</a></div>

        <div class="nav__item" data-dropdown>
          <button class="nav__link" type="button" aria-expanded="false">Voor wie %(caret)s</button>
          <div class="dropdown"><div class="dropdown__inner">%(doelgroepen)s</div></div>
        </div>

        <div class="nav__item" data-dropdown>
          <button class="nav__link" type="button" aria-expanded="false">Diensten %(caret)s</button>
          <div class="dropdown dropdown--wide"><div class="dropdown__inner">%(diensten)s</div></div>
        </div>

        <div class="nav__item"><a class="nav__link" href="/projecten"%(a_projecten)s>Projecten</a></div>

        <div class="nav__item" data-dropdown>
          <button class="nav__link" type="button" aria-expanded="false">Naast mijn werk %(caret)s</button>
          <div class="dropdown"><div class="dropdown__inner">%(naast)s</div></div>
        </div>

        <div class="nav__item"><a class="nav__link" href="/contact"%(a_contact)s>Contact</a></div>

        <div class="nav__mobile-cta">
          <a class="btn btn--primary btn--sm" href="/contact">Neem direct contact op</a>
        </div>
      </nav>
    """ % {
        "caret": caret,
        "doelgroepen": doelgroep_links,
        "diensten": "".join(diensten_cols),
        "naast": naast_links,
        "a_about": aria("/about"),
        "a_projecten": aria("/projecten"),
        "a_contact": aria("/contact"),
    }


def footer_html():
    soortgericht = [
        ("/vleermuisonderzoek", "Vleermuisonderzoek"),
        ("/huismusonderzoek", "Huismusonderzoek"),
        ("/gierzwaluwonderzoek", "Gierzwaluwonderzoek"),
        ("/amfibieen-reptielenonderzoek", "Amfibieën- &amp; reptielenonderzoek"),
        ("/beschermde-planten-onderzoek", "Beschermde planten onderzoek"),
        ("/nachtvlinderonderzoek", "Nachtvlinderonderzoek"),
        ("/dagvlinderonderzoek", "Dagvlinderonderzoek"),
        ("/zoogdieronderzoek", "Zoogdieren &amp; marters"),
        ("/broedvogelonderzoek", "Broedvogelonderzoek"),
        ("/libellenonderzoek", "Libellenonderzoek"),
    ]
    onderzoek_advies = [
        ("/quickscan-flora-en-fauna", "Quickscan flora en fauna"),
        ("/flora-en-faunacheck", "Flora- en faunacheck"),
        ("/aanvullend-onderzoek", "Aanvullend onderzoek"),
        ("/inventarisaties-monitoring", "Inventarisatie en monitoring"),
        ("/invasieve-exoten", "Invasieve exoten"),
        ("/gebiedsbescherming", "Gebiedsbescherming"),
        ("/ecologische-begeleiding", "Ecologische begeleiding"),
        ("/inrichtingsadvies", "Inrichtingsadvies"),
        ("/vergunningstraject", "Vergunning en soortenmanagement"),
        ("/kosten-en-doorlooptijd", "Kosten en doorlooptijd"),
    ]

    def ul(items):
        return "".join('<li><a href="%s">%s</a></li>' % (h, l) for h, l in items)

    return """
    <footer class="footer">
      <div class="wrap">
        <div class="footer__grid">
          <div>
            <a class="footer__wordmark" href="/" aria-label="%(name)s, naar de homepage">Van Der Ham<span>Ecologie</span></a>
            <p>Ecologisch adviesbureau gespecialiseerd in flora- en faunawerkzaamheden,
               inventarisaties en ecologische begeleiding. Met ervaring bij waterschappen
               en terreinbeherende organisaties.</p>
            <p class="footer__meta">KVK: %(kvk)s<br>BTW: %(btw)s</p>
          </div>
          <div>
            <h4>Soortgericht onderzoek</h4>
            <ul>%(soort)s</ul>
          </div>
          <div>
            <h4>Onderzoek en advies</h4>
            <ul>%(advies)s</ul>
          </div>
          <div>
            <h4>Voor wie</h4>
            <ul>%(doelgroep)s<li><a href="https://hieon.nl">HIEON: heb ik onderzoek nodig?</a></li></ul>
            <h4 style="margin-top:26px">Contact</h4>
            <ul>
              <li><a href="mailto:%(email)s">%(email)s</a></li>
              <li><a href="tel:%(phone_link)s">%(phone)s</a></li>
              <li>Werkgebied: heel Nederland</li>
            </ul>
          </div>
        </div>
        <div class="footer__bottom">
          <span>&copy; %(year)s %(name)s. Alle rechten voorbehouden.</span>
          <span><a href="/privacyverklaring">Privacyverklaring</a></span>
        </div>
      </div>
    </footer>
    """ % {
        "name": SITE["name"],
        "kvk": SITE["kvk"],
        "btw": SITE["btw"],
        "email": SITE["email"],
        "phone": SITE["phone"],
        "phone_link": SITE["phone_link"],
        "year": SITE["year"],
        "soort": ul(soortgericht),
        "advies": ul(onderzoek_advies),
        "doelgroep": ul([(h, "Voor " + l.lower()) for h, l in DOELGROEPEN]),
    }


def eyebrow_html(meta):
    """Pill boven de paginatitel, alleen als de frontmatter een eyebrow geeft."""
    tekst = meta.get("eyebrow")
    if not tekst:
        return ""
    return '<p class="pagehead__eyebrow">%s</p>' % tekst


# De eyebrow vlak vóór de <h1> in de paginakop zetten.
_H1 = re.compile(r'(<section class="pagehead">.*?)(<h1>)', re.S)


def inject_eyebrow(html, meta):
    pill = eyebrow_html(meta)
    if not pill:
        return html
    return _H1.sub(lambda m: m.group(1) + pill + "\n    " + m.group(2), html, count=1)


_CRUMBS = re.compile(r'(?is)<p class="crumbs">(.*?)</p>')


def trim_crumbs(html):
    """Laat de breadcrumb alleen de weg naar de pagina zien, niet de pagina zelf.

    De laatste kruimel was steeds dezelfde tekst als de <h1> eronder, wat de
    paginakop onnodig druk maakte. We knippen alles na de laatste link weg.
    Blijft er alleen nog "Home" over, dan voegt de breadcrumb niets toe en
    verdwijnt hij helemaal.
    """
    def fix(m):
        inner = m.group(1)
        eind = inner.rfind("</a>")
        if eind == -1:
            return ""
        inner = inner[:eind + 4]
        if inner.count("<a ") <= 1:
            return ""
        return '<p class="crumbs">%s</p>' % inner

    return _CRUMBS.sub(fix, html, count=1)


_CRUMB_LINK = re.compile(r'(?is)<a href="([^"]+)"[^>]*>(.*?)</a>')
_TAGS = re.compile(r'(?is)<[^>]+>')


def breadcrumb_ld(body, url):
    """BreadcrumbList-markup uit de kruimels van de pagina.

    De zichtbare breadcrumb laat de pagina zelf weg (zie trim_crumbs), maar in
    de structured data hoort de huidige pagina er juist wél bij: dat is wat
    Google nodig heeft om het kruimelpad in de zoekresultaten te tonen in
    plaats van de kale URL. Pagina's zonder bovenliggende pagina krijgen niets,
    want een pad van één stap zegt niets.
    """
    m = _CRUMBS.search(body)
    if not m:
        return ""
    inner = m.group(1)

    items = []
    for href, label in _CRUMB_LINK.findall(inner):
        naam = _TAGS.sub("", label).strip()
        pad = SITE["url"] if href == "/" else SITE["url"] + "/" + href.strip("/")
        items.append((naam, pad))

    # De huidige pagina staat als platte tekst achter de laatste link, met het
    # scheidingsteken ervoor. Dat streepje hoort niet in de naam.
    eind = inner.rfind("</a>")
    huidig = _TAGS.sub("", inner[eind + 4:]).strip().lstrip("/").strip() if eind != -1 else ""
    if huidig:
        items.append((huidig, url))

    # Alleen markup waar ook een zichtbare breadcrumb staat: dat is Home plus
    # ten minste één bovenliggende pagina, plus de pagina zelf. Structured data
    # die niets op de pagina weerspiegelt, wil je niet.
    if len(items) < 3:
        return ""

    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": naam, "item": pad}
            for i, (naam, pad) in enumerate(items, 1)
        ],
    }
    return ('\n<script type="application/ld+json">\n%s\n</script>'
            % json.dumps(data, ensure_ascii=False))


_FAQ_ITEM = re.compile(r'(?is)<div class="faq__item">(.*?)</div>')
_FAQ_VRAAG = re.compile(r'(?is)<h3[^>]*>(.*?)</h3>')
_FAQ_ANTWOORD = re.compile(r'(?is)<p[^>]*>(.*?)</p>')


def faq_ld(body):
    """FAQPage-markup uit de zichtbare vraag-en-antwoordblokken.

    Alleen wat ook echt op de pagina staat: structured data die iets anders
    beweert dan de bezoeker ziet, is in strijd met de richtlijnen van Google.
    """
    vragen = []
    for blok in _FAQ_ITEM.findall(body):
        v = _FAQ_VRAAG.search(blok)
        antwoorden = _FAQ_ANTWOORD.findall(blok)
        if not v or not antwoorden:
            continue
        vraag = _TAGS.sub("", v.group(1)).strip()
        antwoord = " ".join(_TAGS.sub("", a).strip() for a in antwoorden).strip()
        antwoord = re.sub(r"\s+", " ", antwoord)
        if vraag and antwoord:
            vragen.append((vraag, antwoord))
    if len(vragen) < 2:
        return ""
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": v,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for v, a in vragen
        ],
    }
    return ('\n<script type="application/ld+json">\n%s\n</script>'
            % json.dumps(data, ensure_ascii=False))


# Alle dienstpagina's uit het menu, zodat de lijst niet apart bijgehouden hoeft.
DIENST_SLUGS = {h: label for _, items in DIENSTEN for h, label in items}


def service_ld(meta, url, slug):
    """Service-markup op een dienstpagina, met het werkgebied erbij.

    Op een provinciepagina is dat de provincie zelf; dat is precies het
    onderscheid dat zo'n pagina wil maken.
    """
    dienst, provincie = split_provincie_slug(slug)
    if dienst:
        naam = PROVINCIE_DIENSTEN[dienst]
        gebied = {"@type": "State",
                  "name": dict(PROVINCIES)[provincie]}
    elif slug in DIENST_SLUGS:
        naam = re.sub(r"&amp;", "en", DIENST_SLUGS[slug])
        gebied = {"@type": "Country", "name": "Nederland"}
    else:
        return ""
    data = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": naam,
        "serviceType": naam,
        "description": meta.get("description", ""),
        "url": url,
        "areaServed": gebied,
        "provider": {
            "@type": "ProfessionalService",
            "name": SITE["name"],
            "url": SITE["url"] + "/",
            "telephone": SITE["phone"],
            "email": SITE["email"],
        },
    }
    return ('\n<script type="application/ld+json">\n%s\n</script>'
            % json.dumps(data, ensure_ascii=False))


_BLOCK = re.compile(r'(?is)<(h2|h3|p|ul|ol)\b[^>]*>.*?</\1>')
_TXT = re.compile(r'(?is)<[^>]+>')


def _plain_len(html):
    return len(_TXT.sub('', html).strip())


def enrich_prose(inner):
    """Zet rijtjes 'kopje + kort zinnetje' om naar een kaartraster.

    Veel dienstpagina's bestaan uit reeksen van een <h3> met een korte
    <p> eronder. Los leest dat als een lang document; als kaartjes in een
    raster oogt het als de rest van de site. Alleen korte, opsommende
    reeksen worden omgezet; echte tekstsecties blijven ongemoeid.
    """
    blocks = [(m.group(1).lower(), m.group(0)) for m in _BLOCK.finditer(inner)]
    if not blocks:
        return inner

    # Bouw 'units': een h3 met de eropvolgende korte alinea's.
    units, i = [], 0
    while i < len(blocks):
        tag, html = blocks[i]
        if tag == "h3":
            ps, j = [], i + 1
            while j < len(blocks) and blocks[j][0] == "p":
                ps.append(blocks[j][1])
                j += 1
            total = _plain_len(html) + sum(_plain_len(p) for p in ps)
            cardable = 1 <= len(ps) <= 2 and total <= 240 and "<a " not in html
            units.append({"kind": "unit", "cardable": cardable, "h3": html, "ps": ps})
            i = j
        else:
            units.append({"kind": "block", "html": html})
            i += 1

    out, k = [], 0
    while k < len(units):
        u = units[k]
        if u["kind"] == "unit" and u["cardable"]:
            run = []
            while k < len(units) and units[k].get("cardable"):
                run.append(units[k])
                k += 1
            if len(run) >= 2:
                cards = "".join(
                    '<div class="minicard">%s%s</div>' % (r["h3"], "".join(r["ps"]))
                    for r in run
                )
                out.append('<div class="minigrid">%s</div>' % cards)
            else:
                r = run[0]
                out.append(r["h3"] + "".join(r["ps"]))
        elif u["kind"] == "unit":
            out.append(u["h3"] + "".join(u["ps"]))
            k += 1
        else:
            out.append(u["html"])
            k += 1
    return "\n".join(out)


_PROSE = re.compile(r'(?is)(<div class="prose">)(.*?)(</div>)')


def enrich_prose_in(html):
    return _PROSE.sub(lambda m: m.group(1) + enrich_prose(m.group(2)) + m.group(3), html, count=1)


def parse_page(path):
    """Splitst een contentbestand in frontmatter-dict en HTML-body."""
    raw = open(path, encoding="utf-8").read()
    meta, body = {}, raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            head = raw[3:end]
            body = raw[end + 4:].lstrip("\n")
            for line in head.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
    return meta, body


def schema_ld(meta, url):
    """LocalBusiness-markup op de homepage, WebPage elders."""
    if meta.get("slug") == "/":
        return """<script type="application/ld+json">
{"@context":"https://schema.org","@type":"ProfessionalService",
"name":"%(name)s","url":"%(url)s","image":"%(url)s/assets/img/logo.png",
"email":"%(email)s","telephone":"%(phone)s",
"description":"Ecologisch adviesbureau voor quickscans flora en fauna, soortgericht onderzoek en ecologische begeleiding.",
"address":{"@type":"PostalAddress","streetAddress":"%(street)s","postalCode":"%(postcode)s","addressLocality":"%(city)s","addressCountry":"NL"},
"vatID":"%(btw)s","areaServed":{"@type":"Country","name":"Nederland"},
"knowsAbout":["Quickscan flora en fauna","Vleermuisonderzoek","Omgevingswet","Natura 2000","Soortenmanagementplan"]}
</script>""" % dict(SITE, url=SITE["url"])
    return ""


def build():
    if not os.path.isdir(CONTENT):
        sys.exit("content/ ontbreekt")
    base = open(os.path.join(TEMPLATES, "base.html"), encoding="utf-8").read()

    # Bestaande output opruimen, assets laten staan.
    for name in os.listdir(OUT):
        p = os.path.join(OUT, name)
        if name == "assets":
            continue
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)

    bestanden = sorted(fn for fn in os.listdir(CONTENT) if fn.endswith(".html"))
    bestaande_slugs = {"/" if fn == "index.html" else "/" + fn[:-5] for fn in bestanden}

    # Eén keer bepalen: de stylesheet verandert niet tijdens de bouw.
    global CSS_VERSIE
    CSS_VERSIE = css_versie()

    pages = []
    for fn in bestanden:
        meta, body = parse_page(os.path.join(CONTENT, fn))
        slug = "/" if fn == "index.html" else "/" + fn[:-5]
        meta["slug"] = slug
        # 404.html hoort op de root en wordt door GitHub Pages getoond bij elke
        # onbekende URL, ook diep in de site. De links erin blijven daarom
        # absoluut en de pagina komt niet in de sitemap.
        is_404 = fn == "404.html"

        # Doorverwijzing naar dezelfde dienst in de andere provincies: de oude
        # (vaak lege) kop weghalen en onderaan de lopende tekst een complete
        # lijst neerzetten.
        # Dienst-hoofdpagina: de provincielijst opnieuw opbouwen, zodat een
        # nieuwe provincie er vanzelf bij komt te staan.
        hub = provincie_hub_html(slug, bestaande_slugs)
        if hub:
            if _HUB_SECTIE.search(body):
                body = _HUB_SECTIE.sub(lambda m: hub, body, count=1)
            elif '<section class="section cta">' in body:
                body = body.replace(
                    '<section class="section cta">', hub + '<section class="section cta">', 1
                )
            else:
                body += "\n" + hub

        # {{provincies:<dienst>}} op een willekeurige pagina.
        body = re.sub(
            r'\{\{provincies:([a-z-]+)\}\}',
            lambda m: provincie_hub_html(slug, bestaande_slugs, m.group(1)),
            body,
        )

        body = _PROV_KOP.sub("", body)
        links = provincie_links_html(slug, bestaande_slugs)
        if links:
            # Als eigen sectie vlak vóór de afsluitende CTA, zodat de lopende
            # tekst niet onderbroken wordt.
            if '<section class="section cta">' in body:
                body = body.replace(
                    '<section class="section cta">', links + '<section class="section cta">', 1
                )
            else:
                body += "\n" + links
        # Met afsluitende slash: GitHub Pages serveert /slug/ en stuurt /slug
        # met een 301 daarheen. Canonical, og:url en sitemap moeten de URL
        # noemen die zelf 200 geeft, anders staat de hele site in Search
        # Console als "pagina met omleiding".
        url = SITE["url"] + ("/" if slug == "/" else slug + "/")

        html = base
        for key, value in {
            "title": meta.get("title", SITE["name"]),
            "description": meta.get("description", ""),
            "canonical": url,
            "og_image": SITE["url"] + "/assets/img/" + meta.get("og_image", "og-default.jpg"),
            "nav": nav_html(slug),
            "footer": footer_html(),
            "content": body,
            "schema": (schema_ld(meta, url) + breadcrumb_ld(body, url)
                       + service_ld(meta, url, slug) + faq_ld(body)),
            "analytics": analytics_html(),
            "cssversie": CSS_VERSIE,
            "phone": SITE["phone"],
            "phone_link": SITE["phone_link"],
            "email": SITE["email"],
            "sitename": SITE["name"],
            "arrow": ARROW,
        }.items():
            html = html.replace("{{%s}}" % key, str(value))

        # Eyebrow-pill in de paginakop zetten (indien opgegeven).
        html = inject_eyebrow(html, meta)

        # Breadcrumb inkorten: alleen de weg ernaartoe, niet de pagina zelf.
        html = trim_crumbs(html)

        # Opsommende kopje-plus-zinnetje-reeksen omzetten naar kaartjes.
        html = enrich_prose_in(html)

        # Lopende tekst centreren op de pagina (geen stijve zijbalk meer).
        html = html.replace('<div class="prose">', '<div class="prose prose--center">')

        # Interne links relatief maken, zodat de site zowel op de root
        # (eigen domein) als op een submap (github.io-preview) werkt.
        # Alle pagina's zitten één niveau diep (/, of /slug/), dus de
        # basis is "./" op de homepage en "../" op de binnenpagina's.
        if is_404:
            # Absolute links behouden: de pagina wordt op elk URL-niveau
            # getoond, dus "../" zou naar de verkeerde map wijzen.
            html = html.replace(
                "</title>", "</title>\n<meta name=\"robots\" content=\"noindex\">", 1
            )
            with open(os.path.join(OUT, "404.html"), "w", encoding="utf-8") as f:
                f.write(html)
            continue

        # Lijstfoto's naar hun kleine variant laten wijzen.
        html = verklein_thumbs(html)

        # Externe links in een nieuw tabblad.
        html = externe_links(html)

        # Paginalinks krijgen een afsluitende slash, zodat een klik of een
        # crawl niet eerst een 301 hoeft te volgen. Bestanden (met extensie)
        # en links met een anker blijven zoals ze zijn.
        def _paginalink(m):
            attr, pad = m.group(1), m.group(2)
            laatste = pad.rstrip("/").rsplit("/", 1)[-1]
            if pad and "#" not in pad and "?" not in pad and "." not in laatste:
                pad = pad.rstrip("/") + "/"
            return '%s="/%s"' % (attr, pad)

        html = re.sub(r'(href|src)="/([^"]*)"', _paginalink, html)

        basis = "./" if slug == "/" else "../"
        html = re.sub(r'(href|src)="/(?!/)', r'\1="' + basis, html)

        target = OUT if slug == "/" else os.path.join(OUT, slug.strip("/"))
        os.makedirs(target, exist_ok=True)
        with open(os.path.join(target, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        pages.append((url, meta.get("priority", "0.7")))

    # Doorverwijsstubs voor oude URL's; bewust niet in `pages`, dus ook
    # niet in de sitemap.
    schrijf_redirects(bestaande_slugs)

    # sitemap.xml
    today = date.today().isoformat()
    entries = "".join(
        "\n  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (u, today, p)
        for u, p in sorted(pages)
    )
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s\n</urlset>\n' % entries)

    # robots.txt
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE["url"])

    # GitHub Pages: geen Jekyll-verwerking.
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    # Browsers en bookmarkservices vragen /favicon.ico op de root op, ook als
    # de pagina een <link> meegeeft. De root wordt bij elke build geleegd,
    # dus de kopie hoort hier en niet in de map assets.
    ico = os.path.join(OUT, "assets", "img", "favicon.ico")
    if os.path.exists(ico):
        shutil.copyfile(ico, os.path.join(OUT, "favicon.ico"))

    # Eigen domein alleen vastleggen als de overstap gemaakt is.
    cname_pad = os.path.join(OUT, "CNAME")
    if CUSTOM_DOMAIN:
        with open(cname_pad, "w") as f:
            f.write(CUSTOM_DOMAIN + "\n")
    elif os.path.exists(cname_pad):
        os.remove(cname_pad)

    print("%d pagina's gebouwd naar docs/ (custom domain: %s)"
          % (len(pages), CUSTOM_DOMAIN or "nog niet, github.io-preview"))
    missing = [u for u, _ in pages if "  " in u]
    if missing:
        print("let op:", missing)


if __name__ == "__main__":
    build()
