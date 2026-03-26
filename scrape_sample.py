#!/usr/bin/env python3
"""
Sample scraper to get a few recipes quickly for development.
"""

import json
import re
import urllib.request
from html.parser import HTMLParser

BASE_URL = "https://www.ndr.de"

def fetch_url(url):
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode('utf-8')

def extract_json_ld(html):
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
    pattern = r'<h2[^>]*>Nährwerte[^<]*</h2>.*?<p[^>]*>(.*?)</p>'
    match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def extract_tags(html):
    tags = []
    pattern = r'<div class="tagbox".*?</div>'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        tag_pattern = r'<a[^>]*>(.*?)</a>'
        for tag_match in re.finditer(tag_pattern, match.group(0)):
            tag = tag_match.group(1).strip()
            if tag:
                tags.append(tag)
    return tags

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
            # Strip parenthetical qualifiers so "Adipositas (mit Kräuterquark)" → "Adipositas"
            text = re.sub(r'\s*\(.*?\)', '', text).strip()
            if text and text not in suitable:
                suitable.append(text)
        # Also get <br> separated items that might not be in links
        br_items = re.split(r'<br\s*/?>', content)
        for item in br_items:
            # Remove any HTML tags
            clean = re.sub(r'<[^>]+>', '', item).strip()
            clean = re.sub(r'\s*\(.*?\)', '', clean).strip()
            # Skip empty and very short items, and items already found
            if clean and len(clean) > 2 and clean not in suitable:
                suitable.append(clean)
    return suitable

def parse_recipe(html, url):
    json_data = extract_json_ld(html)
    if not json_data:
        return None

    instructions = json_data.get('recipeInstructions', '')
    if isinstance(instructions, list) and len(instructions) > 0:
        if isinstance(instructions[0], dict):
            instructions = '\n\n'.join([step.get('text', '') for step in instructions if isinstance(step, dict)])
        else:
            instructions = '\n\n'.join(instructions)

    image = json_data.get('image', '')
    if isinstance(image, list) and len(image) > 0:
        image = image[0].get('url', '') if isinstance(image[0], dict) else str(image[0])
    elif isinstance(image, dict):
        image = image.get('url', '')

    pdf_url = url.replace('.html', '.html?printview=true')

    return {
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
        'pdfUrl': pdf_url
    }

# Sample recipe URLs to fetch
sample_urls = [
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

recipes = []
for url in sample_urls:
    print(f"Fetching: {url.split('/')[-1]}")
    try:
        html = fetch_url(url)
        recipe = parse_recipe(html, url)
        if recipe:
            recipes.append(recipe)
            print(f"  ✓ Got: {recipe['title'][:50]}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Sort by title
recipes.sort(key=lambda x: x['title'].lower())

with open('recipes.json', 'w', encoding='utf-8') as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(recipes)} sample recipes to recipes.json")
