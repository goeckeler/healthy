#!/usr/bin/env python3
"""
Scraper for NDR Ernährungs-Docs recipes.

Usage:
  python scrape_recipes.py --sample   Download a small set of sample recipes
  python scrape_recipes.py --all      Download all recipes from the overview page
"""

import json
import re
import sys
import time
import urllib.request
from html.parser import HTMLParser

BASE_URL = "https://www.ndr.de"
RECIPES_LIST_URL = "https://www.ndr.de/ratgeber/kochen/rezepte/Rezepte-von-den-Ernaehrungs-Docs,edocsrezepte102.html"

SAMPLE_URLS = [
    "https://www.ndr.de/ratgeber/kochen/rezepte/zucchini-mandel-suppe,zucchinimandelsuppe-104.html",
    "https://www.ndr.de/ratgeber/kochen/rezepte/haferbratlinge-mit-moehre-und-paprika,haferbratlinge-100.html",
    "https://www.ndr.de/ratgeber/kochen/rezepte/vegetarische-bohnen-pizza-mit-spinat,bohnenpizza-102.html",
    "https://www.ndr.de/ratgeber/kochen/rezepte/kraeutersalz,kraeutersalz-102.html",
    "https://www.ndr.de/ratgeber/kochen/rezepte/zitronen-chili-oel,chilioel-100.html",
    "https://www.ndr.de/ratgeber/kochen/rezepte/quinoasalat-vegan-mit-edamame-und-avocado,quinoasalat-106.html",
    "https://www.ndr.de/ratgeber/kochen/rezepte/Gemuesespiesse-mit-Kraeuterquark-oder-Hummus,rezept2780.html",
    "https://www.ndr.de/ratgeber/kochen/rezepte/quark-mit-frischen-kraeutern,kraeuterquark-106.html",
    "https://www.ndr.de/ratgeber/kochen/rezepte/fruchtige-paprika-tomatensuppe-mit-tofu,paprikatomatensuppe-102.html",
    "https://www.ndr.de/ratgeber/kochen/rezepte/vegane-tempeh-frikadellen-mit-kartoffelsalat,tempehbratlinge-104.html",
]

class RecipeLinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.recipes = []
        self.in_link = False
        self.current_href = None
        self.current_title = None
        self.current_aria_label = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_dict = dict(attrs)
            href = attrs_dict.get('href', '')
            # Match recipe URLs
            if '/ratgeber/kochen' in href and '.html' in href and 'edocsrezepte102' not in href:
                self.in_link = True
                self.current_href = href
                self.current_aria_label = attrs_dict.get('aria-label', '')

    def handle_data(self, data):
        if self.in_link:
            self.current_title = data.strip()

    def handle_endtag(self, tag):
        if tag == 'a' and self.in_link:
            self.in_link = False
            title = self.current_aria_label or self.current_title
            if title and self.current_href:
                # Make absolute URL
                href = self.current_href
                if href.startswith('/'):
                    href = BASE_URL + href
                elif href.startswith('http'):
                    pass
                else:
                    href = BASE_URL + '/' + href

                # Skip duplicates
                if not any(r['url'] == href for r in self.recipes):
                    self.recipes.append({
                        'title': title,
                        'url': href
                    })
            self.current_href = None
            self.current_title = None
            self.current_aria_label = None

def fetch_url(url, retries=3):
    """Fetch URL content with retries."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            if attempt == retries - 1:
                print(f"Failed to fetch {url}: {e}")
                return None
            time.sleep(1)
    return None

def extract_json_ld(html):
    """Extract JSON-LD Recipe data from HTML."""
    pattern = r'<script type="application/ld\+json">(.*?)</script>'
    matches = re.findall(pattern, html, re.DOTALL)

    for match in matches:
        try:
            data = json.loads(match)
            if isinstance(data, dict) and data.get('@type') == 'Recipe':
                return data
        except json.JSONDecodeError:
            continue
    return None

def extract_nutrition(html):
    """Extract nutrition info from HTML."""
    # Look for Nährwerte section
    pattern = r'<h2[^>]*>Nährwerte[^<]*</h2>.*?<p[^>]*>(.*?)</p>'
    match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def extract_tags(html):
    """Extract tags from tagbox."""
    tags = []
    # Match tagbox links
    pattern = r'<div class="tagbox".*?</div>'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        tagbox_html = match.group(0)
        # Extract links
        tag_pattern = r'<a[^>]*>(.*?)</a>'
        for tag_match in re.finditer(tag_pattern, tagbox_html):
            tag = tag_match.group(1).strip()
            if tag:
                tags.append(tag)
    return tags

def normalize_suitable(tag):
    """Normalize a suitableFor tag: truncate at (, , or /, trim, capitalize, apply canonical names."""
    truncated = re.split(r'[,(\/]', tag)[0].strip()
    if not truncated:
        return None
    capitalized = truncated[0].upper() + truncated[1:]

    # correct typos in categories
    if capitalized == 'Colitis Ulcerosa' or capitalized == 'Coltis ulcerosa':
        return 'Colitis ulcerosa'
    if capitalized == 'Dünndarm-Fehlbesiedlung':
        return 'Dünndarmfehlbesiedlung'
    if capitalized == 'Kopfschmerzen':
        return 'Migräne'
    if capitalized == 'Lymphozytärer Kolitis':
        return 'Lymphozytäre Kolitis'
    if capitalized == 'Magen-Verkleinerung':
        return 'Magenverkleinerung'

    # shortcut similar categories
    if capitalized.startswith('Arthrose'):
        return 'Arthrose'
    if capitalized.startswith('COPD'):
        return 'COPD'
    if capitalized.startswith('Fettwechelstörung'):
        return 'Fettwechselstörung'
    if capitalized.startswith('Fruktose'):
        return 'Fruktoseintoleranz'
    if capitalized.startswith('Histamin'):
        return 'Histaminintoleranz'
    if capitalized.startswith('Metabolisch'):
        return 'Metabolisches Syndrom'
    if capitalized.startswith('Nierengesund'):
        return 'Nierengesunde Ernährung'
    if capitalized.startswith('Nierenstein'):
        return 'Nierensteine'
    if capitalized.startswith('Potenzstörung'):
        return 'Potenzstörung'
    if capitalized.startswith('Zöl'):
        return 'Zöliakie'

    if 'Sklerose' in capitalized:
        return 'Multiple Sklerose'

    return capitalized

def extract_suitable_for(html):
    """Extract "Geeignet u. a. bei" tags (suitableFor conditions)."""
    suitable = []
    # Match the h2 heading followed by a p with links
    pattern = r'<h2[^>]*>Geeignet[^<]*</h2>.*?<p[^>]*>(.*?)</p>'
    match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
    if match:
        # Extract text from links and <br> separated items
        content = match.group(1)
        # First try to extract from <a> tags
        link_pattern = r'<a[^>]*>(.*?)</a>'
        for link_match in re.finditer(link_pattern, content):
            text = link_match.group(1).strip()
            # Clean up any <br> or other tags inside
            text = re.sub(r'<[^>]+>', '', text)
            normalized = normalize_suitable(text)
            if normalized and normalized not in suitable:
                suitable.append(normalized)
        # Also get <br> separated items that might not be in links
        br_items = re.split(r'<br\s*/?>', content)
        for item in br_items:
            clean = re.sub(r'<[^>]+>', '', item).strip()
            normalized = normalize_suitable(clean)
            if normalized and len(normalized) > 2 and normalized not in suitable:
                suitable.append(normalized)
    return suitable

def extract_pdf_url(html, recipe_url):
    """Extract or construct PDF URL."""
    # Try to find a direct PDF link
    pattern = r'href="([^"]*\.pdf)"'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        pdf_url = match.group(1)
        if pdf_url.startswith('/'):
            return BASE_URL + pdf_url
        return pdf_url

    # Try print view URL pattern
    if '?printview' not in recipe_url:
        return recipe_url.replace('.html', '.html?printview=true')
    return recipe_url

def parse_recipe(html, url):
    """Parse a recipe page and extract all relevant data."""
    json_data = extract_json_ld(html)

    if not json_data:
        return None

    # Handle instructions - can be list of objects, list of strings, or just a string
    instructions = json_data.get('recipeInstructions', '')
    if isinstance(instructions, list) and len(instructions) > 0:
        if isinstance(instructions[0], dict):
            instructions = '\n\n'.join([step.get('text', '') for step in instructions if isinstance(step, dict)])
        else:
            instructions = '\n\n'.join(instructions)

    # Handle image
    image = json_data.get('image', '')
    if isinstance(image, list) and len(image) > 0:
        image = image[0].get('url', '') if isinstance(image[0], dict) else str(image[0])
    elif isinstance(image, dict):
        image = image.get('url', '')

    recipe = {
        'title': json_data.get('name', ''),
        'url': url,
        'author': json_data.get('author', {}).get('name', '') if isinstance(json_data.get('author'), dict) else '',
        'description': json_data.get('description', ''),
        'image': image,
        'prepTime': json_data.get('totalTime', ''),
        'servings': json_data.get('recipeYield', 2),
        'ingredients': json_data.get('recipeIngredient', []),
        'instructions': instructions,
        'categories': json_data.get('recipeCategory', '').split(', ') if json_data.get('recipeCategory') else [],
        'nutrition': extract_nutrition(html),
        'tags': extract_tags(html),
        'suitableFor': extract_suitable_for(html),
        'pdfUrl': extract_pdf_url(html, url)
    }

    return recipe

def run_sample():
    """Fetch a small hardcoded set of sample recipes."""
    recipes = []
    for url in SAMPLE_URLS:
        print(f"Fetching: {url.split('/')[-1]}")
        html = fetch_url(url)
        if html:
            recipe = parse_recipe(html, url)
            if recipe:
                recipes.append(recipe)
                print(f"  OK: {recipe['title'][:50]}")
            else:
                print(f"  Could not parse recipe")
        else:
            print(f"  Failed to fetch")

    recipes.sort(key=lambda x: x['title'].lower())

    with open('recipes.json', 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(recipes)} sample recipes to recipes.json")


def main():
    print("Fetching recipe list...")
    list_html = fetch_url(RECIPES_LIST_URL)
    if not list_html:
        print("Failed to fetch recipe list")
        return

    # Extract recipe links
    extractor = RecipeLinkExtractor()
    extractor.feed(list_html)

    print(f"Found {len(extractor.recipes)} recipes")

    # Fetch each recipe
    recipes = []
    for i, recipe_info in enumerate(extractor.recipes):
        print(f"Fetching {i+1}/{len(extractor.recipes)}: {recipe_info['title']}")

        html = fetch_url(recipe_info['url'])
        if html:
            recipe = parse_recipe(html, recipe_info['url'])
            if recipe:
                recipes.append(recipe)
            else:
                # Try to at least save basic info
                recipes.append({
                    'title': recipe_info['title'],
                    'url': recipe_info['url'],
                    'author': '',
                    'description': '',
                    'image': '',
                    'prepTime': '',
                    'servings': 2,
                    'ingredients': [],
                    'instructions': '',
                    'categories': [],
                    'nutrition': '',
                    'tags': [],
                    'suitableFor': [],
                    'pdfUrl': recipe_info['url']
                })

        # Be nice to the server
        time.sleep(0.5)

    # Sort by title
    recipes.sort(key=lambda x: x['title'].lower())

    # Save to JSON
    with open('recipes.json', 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(recipes)} recipes to recipes.json")

    # Also save a minimal version for the web app
    minimal_recipes = []
    for r in recipes:
        minimal_recipes.append({
            'title': r['title'],
            'url': r['url'],
            'author': r['author'],
            'image': r['image'],
            'servings': r['servings'],
            'prepTime': r['prepTime'],
            'categories': r['categories'],
            'tags': r['tags'],
            'suitableFor': r['suitableFor'],
            'nutrition': r['nutrition']
        })

    with open('recipes_minimal.json', 'w', encoding='utf-8') as f:
        json.dump(minimal_recipes, f, ensure_ascii=False, indent=2)

    print(f"Saved minimal version to recipes_minimal.json")

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('--sample', '--all'):
        print(__doc__.strip())
        sys.exit(1)

    if sys.argv[1] == '--sample':
        run_sample()
    else:
        main()
