"""Cleaner for attractions dataset
Normalizes data/raw/kerala_attractions.json and writes data/processed/kerala_attractions_clean.json.
"""
import json
from pathlib import Path


def clean_attractions(raw_path=None, out_path=None):
    if raw_path is None:
        raw_path = Path(_file_).parents[2] / 'data' / 'raw' / 'kerala_attractions.json'
    if out_path is None:
        out_path = Path(_file_).parents[2] / 'data' / 'processed' / 'kerala_attractions_clean.json'

    if not raw_path.exists():
        raise FileNotFoundError(f"Attractions raw file not found: {raw_path}")

    doc = json.loads(raw_path.read_text(encoding='utf-8'))
    items = []
    if isinstance(doc, dict):
        items = doc.get('attractions') or []
    elif isinstance(doc, list):
        items = doc

    cleaned = []
    seen = set()
    for a in items:
        if not isinstance(a, dict):
            continue
        aid = a.get('id') or a.get('name') and f"attr_{abs(hash(a.get('name'))) % 100000}"
        if aid in seen:
            continue
        seen.add(aid)

        # normalize coordinates
        loc = a.get('location') or {}
        coords = loc.get('coordinates') or {}
        lat = coords.get('lat')
        lng = coords.get('lng')
        try:
            lat = float(lat) if lat is not None else None
            lng = float(lng) if lng is not None else None
        except Exception:
            lat = lng = None

        details = a.get('details') or {}
        # ensure duration_hours exists
        duration = details.get('duration_hours') or details.get('duration') or None
        try:
            duration = int(duration) if duration is not None else None
        except Exception:
            duration = None

        cleaned.append({
            'id': aid,
            'name': a.get('name'),
            'location': {'city': loc.get('city') or None, 'coordinates': {'lat': lat, 'lng': lng}},
            'details': {**details, 'duration_hours': duration},
            'insider_tips': a.get('insider_tips') or [],
            'best_months': a.get('best_months') or []
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({'attractions': cleaned}, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Cleaned {len(cleaned)} attractions -> {out_path}")
    return {'attractions': cleaned}


if _name_ == '_main_':
    clean_attractions()
