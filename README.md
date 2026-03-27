# NDR Ernährungs-Docs Rezept-App

Eine mobile-freundliche Web-App zum Durchsuchen der Rezepte von den NDR Ernährungs-Docs.

## Features

- 📱 Vollständig responsive - optimiert für Smartphones
- 🔍 Suche mit Wildcard-Unterstützung (z.B. `Zucchini*` oder `*suppe`)
- 🏷️ Filter nach Tags/Kategorien
- 📊 Alphabetische Sortierung
- 👥 Portionen-Anpassung
- 📄 Direktlink zum PDF

## Installation

1. **Rezepte scrapen (optional):**
   Achtung, derzeit werden über 600 Rezepte der Ernährungsdocs verfügbar gemacht. Einige Rezepte, die auf der [Webseite des NDRs](https://www.ndr.de/ratgeber/kochen/rezepte) gefunden werden, sind hier noch nicht aufgeführt, da sie nicht in der Einstiegsliste enthalten sind.

   Wenn also wieder die Lust nach [Dinkelwaffeln](https://www.ndr.de/ratgeber/kochen/rezepte/Dinkel-Waffeln-mit-Banane-und-frischen-Fruechten,rezept5262.html) groß ist, bitte direkt auf die Seiten des NDRs gehen oder warten, bis diese Rezepte auch hier dargestellt werden können.

   ```bash
   # Alle Rezepte herunterladen
   python3 scrape_recipes.py --all

   # Oder nur ein paar Beispielrezepte
   python3 scrape_recipes.py --sample
   ```

2. **Webserver starten:**
   ```bash
   # Mit Python 3
   python3 -m http.server 8000

   # Oder mit Node.js
   npx serve .
   ```

3. **Im Browser öffnen:**
   http://localhost:8000

## Dateistruktur

- `index.html` - Hauptanwendung (Single Page App)
- `recipes.json` - Rezeptdaten (wird vom Scraper erzeugt)
- `scrape_recipes.py` - Rezept-Scraper (`--sample` für Beispieldaten, `--all` für alle Rezepte)

## Suchtipps

- **Textsuche:** Geben Sie einfach einen Begriff ein (z.B. "Zucchini")
- **Wildcard `*`:** Verwenden Sie `*` als Platzhalter
  - `Zucchini*` - findet alles was mit "Zucchini" beginnt
  - `*suppe` - findet alles was auf "suppe" endet
  - `*kartoffel*` - findet alles was "kartoffel" enthält
- **Tags:** Klicken Sie auf einen Tag um zu filtern
- **Kombiniert:** Suche + Tag-Filter können zusammen verwendet werden

## Technologien

- Vanilla JavaScript (keine Frameworks)
- Responsive CSS mit Flexbox
- Schema.org Recipe JSON-LD Daten

## Hinweis

Dies ist ein inoffizieller Viewer. Alle Rezepte und Bilder gehören dem NDR.
