#!/usr/bin/env python3
"""Zet de gecrawlde pagina's van de oude site om naar contentbestanden.

Eenmalig hulpmiddel voor de overstap van landingsite naar de eigen site.
Per pagina worden titel, beschrijving, koppen, alinea's en lijsten
overgenomen en in de nieuwe opmaak gezet.

De oude HTML bevat niet-gesloten <p>-tags, dus er wordt met een echte
HTML-parser gelezen in plaats van met reguliere expressies.

Draaien:  python3 tools/converteer.py <map-met-gecrawlde-html>
"""

import html as ht
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "content")

# Pagina's die met de hand zijn gemaakt en niet overschreven mogen worden.
HANDGEMAAKT = {"index"}

# Alles binnen deze elementen is navigatie, script of decoratie.
NEGEER = {"header", "footer", "nav", "script", "style", "svg", "noscript",
          "button", "form", "select", "template"}

BLOKKEN = {"h1", "h2", "h3", "h4", "p", "li"}
LIJSTEN = {"ul", "ol"}
INLINE = {"a", "strong", "b", "em"}

# Tekst die alleen navigatie, knop of voettekst was op de oude site.
RUIS = re.compile(
    r"^(over ons|voor wie|diensten|contact|naast mijn werk|home|menu|"
    r"neem direct contact op|direct quickscan aanvragen|alle diensten|"
    r"bekijk alle diensten|lees meer|meer over ons|offerte aanvragen|"
    r"waterschappen.*tbo'?s|gemeenten|aannemers.*ontwikkelaars|particulieren|"
    r"invested birding|natuurspeld|big week|privacyverklaring|"
    r"kvk:?\s*\d+|btw:?\s*[a-z0-9]+|e-?mail|telefoon|werkgebied|heel nederland|"
    r"©\s*\d{4}.*|bel(:| direct).*|\d{2}-\d{8}|info@.*)$",
    re.I,
)


def net(tekst):
    tekst = re.sub(r"\s+", " ", tekst).strip()
    # Gedachtestreepjes zijn niet toegestaan in Wouters teksten.
    tekst = re.sub(r"\s+[—–]\s+", ", ", tekst)
    return tekst


class Lezer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.negeer = 0
        self.blokken = []          # (soort, inhoud)
        self.huidig = None         # soort van het lopende blok
        self.buffer = []
        self.lijst = None          # verzamelde <li>-teksten
        self.inline = []           # open inline-tags binnen het blok

    # -- hulp --------------------------------------------------------------
    def _sluit_blok(self):
        if self.huidig is None:
            return
        tekst = net("".join(self.buffer))
        soort = self.huidig
        self.huidig, self.buffer, self.inline = None, [], []
        if not tekst or RUIS.match(re.sub(r"<[^>]+>", "", tekst)):
            return
        if soort == "li":
            if self.lijst is not None:
                self.lijst.append(tekst)
            return
        self.blokken.append((soort, tekst))

    # -- parser ------------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if tag in NEGEER:
            self.negeer += 1
            return
        if self.negeer:
            return
        if tag in LIJSTEN:
            self._sluit_blok()
            self.lijst = []
            return
        if tag in BLOKKEN:
            self._sluit_blok()          # vangt niet-gesloten <p> op
            self.huidig = tag
            return
        if self.huidig and tag in INLINE:
            if tag == "a":
                href = dict(attrs).get("href", "")
                # alleen interne links behouden
                if href.startswith("/"):
                    self.buffer.append('<a href="%s">' % href)
                    self.inline.append("a")
                else:
                    self.inline.append(None)
            else:
                self.buffer.append("<%s>" % tag)
                self.inline.append(tag)
        elif tag == "br" and self.huidig:
            self.buffer.append(" ")

    def handle_endtag(self, tag):
        if tag in NEGEER:
            self.negeer = max(0, self.negeer - 1)
            return
        if self.negeer:
            return
        if tag in LIJSTEN:
            self._sluit_blok()
            if self.lijst:
                self.blokken.append(("ul", list(self.lijst)))
            self.lijst = None
            return
        if tag in BLOKKEN:
            if self.huidig == tag:
                self._sluit_blok()
            return
        if self.huidig and tag in INLINE and self.inline:
            open_tag = self.inline.pop()
            if open_tag:
                self.buffer.append("</%s>" % open_tag)

    def handle_data(self, data):
        if self.negeer or self.huidig is None:
            return
        self.buffer.append(data)

    def close(self):
        super().close()
        self._sluit_blok()


def uniek(blokken):
    """De oude site toonde sommige koppen dubbel. Die eruit."""
    resultaat, gezien = [], set()
    for soort, inhoud in blokken:
        sleutel = (soort, str(inhoud)[:140].lower())
        if sleutel in gezien:
            continue
        gezien.add(sleutel)
        resultaat.append((soort, inhoud))
    return resultaat


def converteer(pad, slug):
    rauw = open(pad, encoding="utf-8").read()
    titel = re.search(r"(?is)<title[^>]*>(.*?)</title>", rauw)
    desc = re.search(r'(?is)<meta name="description" content="(.*?)"', rauw)
    titel = net(ht.unescape(titel.group(1))) if titel else slug
    desc = net(ht.unescape(desc.group(1))) if desc else ""

    lezer = Lezer()
    lezer.feed(rauw)
    lezer.close()
    items = uniek(lezer.blokken)
    if not items:
        return None

    kop = next((c for s, c in items if s == "h1"), titel.split("|")[0].strip())
    kop = re.sub(r"<[^>]+>", "", kop)

    rest, h1_gehad = [], False
    for soort, inhoud in items:
        if soort == "h1" and not h1_gehad:
            h1_gehad = True
            continue
        rest.append((soort, inhoud))

    lead = ""
    if rest and rest[0][0] == "p":
        lead = re.sub(r"<[^>]+>", "", rest.pop(0)[1])

    regels = []
    for soort, inhoud in rest:
        if soort == "ul":
            regels.append("      <ul>")
            regels += ["        <li>%s</li>" % i for i in inhoud]
            regels.append("      </ul>")
        elif soort == "h2":
            regels.append("      <h2>%s</h2>" % inhoud)
        elif soort in ("h3", "h4"):
            regels.append("      <h3>%s</h3>" % inhoud)
        else:
            regels.append("      <p>%s</p>" % inhoud)

    kop_kort = kop[0].lower() + kop[1:] if kop else "dit onderzoek"
    return """---
title: {titel}
description: {desc}
---
<section class="pagehead">
  <div class="wrap">
    <p class="crumbs"><a href="/">Home</a><span>/</span>{kop}</p>
    <h1>{kop}</h1>
    <p>{lead}</p>
    <a class="btn btn--onDark" href="/contact">Vrijblijvend overleggen {{{{arrow}}}}</a>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="prose">
{body}
    </div>
  </div>
</section>

<section class="section cta">
  <div class="wrap">
    <div class="cta__inner">
      <div>
        <h2>Vragen over {kop_kort}?</h2>
        <p>Bel of mail gerust. Samen bepalen we wat er nodig is voor uw situatie.</p>
      </div>
      <div class="cta__actions">
        <a class="btn btn--onDark" href="/contact">Neem contact op {{{{arrow}}}}</a>
        <a class="btn btn--outlineDark" href="tel:{{{{phone_link}}}}">Bel {{{{phone}}}}</a>
      </div>
    </div>
  </div>
</section>
""".format(titel=titel, desc=desc, kop=kop, kop_kort=kop_kort,
           lead=lead or desc, body="\n".join(regels))


def main():
    bron = sys.argv[1] if len(sys.argv) > 1 else None
    if not bron or not os.path.isdir(bron):
        sys.exit("gebruik: python3 tools/converteer.py <map-met-gecrawlde-html>")
    gedaan, overgeslagen = 0, []
    for fn in sorted(os.listdir(bron)):
        if not fn.endswith(".html"):
            continue
        slug = fn[:-5]
        if slug in HANDGEMAAKT:
            continue
        resultaat = converteer(os.path.join(bron, fn), slug)
        if resultaat is None:
            overgeslagen.append(slug)
            continue
        with open(os.path.join(OUT, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(resultaat)
        gedaan += 1
    print("%d pagina's omgezet naar content/" % gedaan)
    if overgeslagen:
        print("overgeslagen:", ", ".join(overgeslagen))


if __name__ == "__main__":
    main()
