# vanderhamecologie.nl

De website van Van Der Ham Ecologie. Statische site, gegenereerd met een klein
Python-script en gepubliceerd via GitHub Pages.

## Hoe het in elkaar zit

```
content/        de teksten, één bestand per pagina
templates/      het raamwerk om elke pagina heen
tools/          eenmalig hulpmiddel voor de overstap van landingsite
build.py        bouwt content + template samen tot de site
docs/           het resultaat, dit is wat GitHub Pages publiceert
docs/assets/    stylesheet en foto's
```

De map `docs/` wordt door `build.py` opnieuw gevuld. Handmatige wijzigingen daarin
gaan bij de volgende build verloren. Pas dus altijd `content/` of `templates/` aan.

## Een pagina aanpassen

1. Open het bestand in `content/`, bijvoorbeeld `content/quickscan-flora-en-fauna.html`.
2. Bovenaan staat de paginatitel en de omschrijving voor Google, tussen de
   streepjes. Daaronder staat de inhoud.
3. Bouwen en publiceren:

```bash
python3 build.py && git add -A && git commit -m "Tekst quickscan bijgewerkt" && git push
```

GitHub Pages zet de wijziging binnen een minuut of twee live.

## Een pagina toevoegen

Maak een nieuw bestand in `content/`. De bestandsnaam wordt het webadres:
`content/nachtvlinderonderzoek-drenthe.html` wordt
`vanderhamecologie.nl/nachtvlinderonderzoek-drenthe`. Draai daarna `build.py`.

Staat de pagina ook in het menu? Voeg hem dan toe aan de lijsten bovenin `build.py`.

## Lokaal bekijken

```bash
python3 build.py && python3 -m http.server 4321 --directory docs
```

Daarna in de browser naar `http://localhost:4321`.

## Huisstijl

Kleuren en lettertypen staan bovenin `docs/assets/css/site.css` en komen overeen
met de bestaande huisstijl. Niet wijzigen zonder overleg.

## Aandachtspunten

- Twee foto's zijn stockbeelden van iStock, gelicentieerd via landingsite:
  `docs/assets/img/istock-invasieve-exoten.jpg` en `istock-inrichtingsadvies.jpg`.
  Vervang deze door eigen beeld voordat het landingsite-abonnement stopt.
- Het contactformulier loopt via Web3Forms, met dezelfde sleutel als hieon.nl.
