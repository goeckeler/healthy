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
   ```bash
   # Alle Rezepte herunterladen
   python3 scrape_recipes.py

   # Oder nur ein paar Beispielrezepte
   python3 scrape_sample.py
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
- `scrape_recipes.py` - Vollständiger Rezept-Scraper
- `scrape_sample.py` - Schneller Beispiel-Scraper

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
