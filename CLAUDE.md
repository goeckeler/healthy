# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A German-language single-page web app for browsing NDR Ernährungs-Docs recipes. No build step, no frameworks, no dependencies — pure HTML/CSS/vanilla JS served as static files, with a Python scraper to populate the data.

## Running locally

```bash
python3 -m http.server 8000
# Open http://localhost:8000
```

## Updating recipe data

```bash
python3 scrape_recipes.py --sample   # 10 hardcoded sample recipes (fast, for dev)
python3 scrape_recipes.py --all      # Full crawl from NDR overview page
```

The scraper writes two files:
- `recipes.json` — full data loaded by the app
- `recipes_minimal.json` — lightweight version (no ingredients/instructions) for list rendering

## Architecture

**Data flow:** NDR website → `scrape_recipes.py` → `recipes.json` → `index.html` (fetched at startup)

**`index.html`** is the entire frontend (~1,500 lines, all inline). It:
- Fetches `recipes.json` at load time
- Renders a filterable, searchable recipe list grouped alphabetically
- Opens a detail modal with ingredient scaling on recipe click

**`scrape_recipes.py`** uses only Python stdlib (`urllib`, `html.parser`, `re`, `json`). The `RecipeLinkExtractor` HTMLParser discovers recipe URLs from the overview page; extraction functions pull structured data from JSON-LD and custom HTML patterns.

## Key frontend logic

| Function | What it does |
|---|---|
| `filterRecipes()` | Combines text search, tag filters, and health condition filters |
| `wildcardMatch()` | Supports `*` as a wildcard in the search box |
| `scaleIngredients()` / `parseIngredient()` | Parses and scales ingredient amounts by servings |
| `toFraction()` | Converts decimal amounts to display fractions (½, ¾, etc.) |
| `openModal()` | Renders the recipe detail overlay |
| `getAllTags()` / `getAllSuitableForTags()` | Counts and ranks tags for the filter UI |

## Recipe data shape

```json
{
  "title": "", "url": "", "author": "", "description": "", "image": "",
  "prepTime": "PT50M", "servings": 4,
  "ingredients": ["200 g Zucchini", ...],
  "instructions": "...",
  "categories": ["Hauptspeise"],
  "tags": ["..."],
  "suitableFor": ["Diabetes", "COPD", ...],
  "nutrition": "...",
  "pdfUrl": "https://..."
}
```

`suitableFor` values are normalized in the scraper via `normalize_suitable()` — canonical names like `"Colitis ulcerosa"`, `"Migräne"`, `"Fruktoseintoleranz"`.

## Scraper notes

- 3-retry logic with 1 s backoff on fetch failures
- 0.5 s delay between recipe fetches (be polite to NDR servers)
- `extract_pdf_url()` first looks for a real `.pdf` link, falls back to `?printview=true`
- If JSON-LD parsing fails for a recipe, basic info (title, URL) is still saved as a stub
