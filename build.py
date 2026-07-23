#!/usr/bin/env python3
"""Sitegenerator voor vanderhamecologie.nl.

Leest content/*.html (frontmatter + HTML-body), giet dat door
templates/base.html en schrijft het resultaat naar docs/.
docs/ is de map die GitHub Pages publiceert.

Draaien:  python3 build.py
"""

import os
import re
import shutil
import sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
TEMPLATES = os.path.join(ROOT, "templates")
OUT = os.path.join(ROOT, "docs")

# Zet dit op "www.vanderhamecologie.nl" op het moment van de DNS-overstap.
# Zolang het None is, draait de site testbaar op de github.io-URL en wordt
# er geen CNAME-bestand geschreven (anders leidt github.io door naar het
# eigen domein, dat nog bij landingsite hangt).
CUSTOM_DOMAIN = None

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
"name":"%(name)s","url":"%(url)s","image":"%(url)s/assets/img/logo.jpg",
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

    pages = []
    for fn in sorted(os.listdir(CONTENT)):
        if not fn.endswith(".html"):
            continue
        meta, body = parse_page(os.path.join(CONTENT, fn))
        slug = "/" if fn == "index.html" else "/" + fn[:-5]
        meta["slug"] = slug
        url = SITE["url"] + ("" if slug == "/" else slug)

        html = base
        for key, value in {
            "title": meta.get("title", SITE["name"]),
            "description": meta.get("description", ""),
            "canonical": url,
            "og_image": SITE["url"] + "/assets/img/" + meta.get("og_image", "logo.jpg"),
            "nav": nav_html(slug),
            "footer": footer_html(),
            "content": body,
            "schema": schema_ld(meta, url),
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
        basis = "./" if slug == "/" else "../"
        html = re.sub(r'(href|src)="/(?!/)', r'\1="' + basis, html)

        target = OUT if slug == "/" else os.path.join(OUT, slug.strip("/"))
        os.makedirs(target, exist_ok=True)
        with open(os.path.join(target, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        pages.append((url, meta.get("priority", "0.7")))

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
