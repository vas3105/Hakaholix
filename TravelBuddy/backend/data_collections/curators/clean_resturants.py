"""Cleaner for restaurants dataset
Normalizes data/raw/kerala_restaurants.json to a consistent shape and writes a processed copy.
"""
import json
import re
from pathlib import Path


def clean_restaurants(raw_path=None, out_path=None):
    if raw_path is None:
        raw_path = Path(_file_).parents[2] / 'data' / 'raw' / 'kerala_restaurants.json'
    if out_path is None:
        out_path = Path(_file_).parents[2] / 'data' / 'processed' / 'kerala_restaurants_clean.json'

    if not raw_path.exists():
        raise FileNotFoundError(f"Restaurants raw file not found: {raw_path}")

    text = raw_path.read_text(encoding='utf-8')
    try:
        doc = json.loads(text)
    except Exception:
        raise ValueError("Unable to parse restaurants JSON; please check file")

    items = []
    if isinstance(doc, dict):
        # try common keys
        if 'restaurants' in doc and isinstance(doc['restaurants'], list):
            items = doc['restaurants']
        else:
            # flatten any lists inside
            for v in doc.values():
                if isinstance(v, list):
                    items = v
                    break
    elif isinstance(doc, list):
        items = doc

    cleaned = []
    seen = set()
    for r in items:
        if not isinstance(r, dict):
            continue
        name = r.get('name') or r.get('title') or r.get('restaurant_name')
        if not name:
            continue
        # build id
        rid = r.get('id') or f"rest_{abs(hash(name))%100000}"
        if rid in seen:
            continue
        seen.add(rid)

        # normalize rating
        rating = r.get('rating') or r.get('avg_rating') or None
        try:
            rating = float(rating) if rating is not None else None
        except Exception:
            rating = None

        # sanitize address coordinates
        loc = r.get('location', {}) or {}
        coords = loc.get('coordinates') or {}
        try:
            lat = float(coords.get('lat')) if coords and coords.get('lat') is not None else None
            lng = float(coords.get('lng')) if coords and coords.get('lng') is not None else None
        except Exception:
            lat = lng = None

        cleaned.append({
            'id': rid,
            'name': name,
            'location': {
                'city': loc.get('city') or loc.get('town') or None,
                'coordinates': {'lat': lat, 'lng': lng}
            },
            'cuisine': r.get('cuisine') or r.get('cuisines') or [],
            'rating': rating,
            'price_range': r.get('price_range') or r.get('pricing') or None,
            'details': r.get('details') or {}
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({'restaurants': cleaned}, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Cleaned {len(cleaned)} restaurants -> {out_path}")
    return {'restaurants': cleaned}


if _name_ == '_main_':
    clean_restaurants()
