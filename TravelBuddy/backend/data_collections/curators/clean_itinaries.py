import json
import os
import uuid
from pathlib import Path

ROOT = Path(_file_).resolve().parents[2]


def _load_candidate(paths):
    for p in paths:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding='utf-8'))
            except Exception:
                # try to repair simple trailing commas or return None
                try:
                    txt = p.read_text(encoding='utf-8')
                    return json.loads(txt)
                except Exception:
                    raise
    return None


def normalize_itinerary(itin, idx):
    # Ensure structure and sensible defaults
    out = {}
    out['id'] = itin.get('id') or itin.get('uid') or str(uuid.uuid4())
    out['name'] = (itin.get('name') or itin.get('title') or f'Itinerary {idx}').strip()

    # Days / route
    raw_days = itin.get('days') or itin.get('route') or itin.get('itinerary') or []
    days = []
    if isinstance(raw_days, dict):
        # sometimes day keys are numeric strings
        for k, v in raw_days.items():
            days.append({'day': k, 'location': v.get('location') or v.get('place') or '', 'desc': v.get('description') or v.get('desc') or ''})
    else:
        for i, d in enumerate(raw_days, start=1):
            if isinstance(d, dict):
                location = d.get('location') or d.get('place') or d.get('title') or ''
                desc = d.get('description') or d.get('desc') or d.get('notes') or ''
                days.append({'day': i, 'location': location, 'desc': desc})
            else:
                days.append({'day': i, 'location': str(d), 'desc': ''})

    out['route'] = days
    out['duration_days'] = int(itin.get('duration_days') or itin.get('days_count') or len(days) or 0)

    # Budget
    budget = itin.get('budget') or itin.get('budget_range') or itin.get('budget_range_inr')
    if isinstance(budget, dict):
        out['budget'] = {
            'min': budget.get('min') or budget.get('low'),
            'max': budget.get('max') or budget.get('high'),
            'avg': budget.get('avg') or budget.get('mean')
        }
    else:
        try:
            out['budget'] = {'avg': float(budget)} if budget is not None else None
        except Exception:
            out['budget'] = None

    out['best_months'] = list(itin.get('best_months') or itin.get('best_time') or [])
    out['interests'] = list(itin.get('interests') or itin.get('themes') or itin.get('tags') or [])
    out['target_audience'] = list(itin.get('target_audience') or itin.get('target') or [])

    # Keep any extra notes
    out['notes'] = itin.get('notes') or itin.get('description') or ''

    return out


def main():
    raw_candidates = [
        ROOT / 'data' / 'raw' / 'kerala_itinerary_templates.json',
        ROOT / 'data' / 'raw' / 'kerala_itineraries.json',
        ROOT / 'data' / 'processed' / 'kerala_itineraries_clean.json',
        ROOT / 'data' / 'processed' / 'kerala_itineraries.json'
    ]

    data = _load_candidate(raw_candidates)
    if data is None:
        print('No itinerary source file found. Tried candidates:')
        for p in raw_candidates:
            print(' -', p)
        return 1

    # data may be a dict with key 'itineraries' or 'templates'
    if isinstance(data, dict):
        items = data.get('itineraries') or data.get('templates') or data.get('items') or []
    else:
        items = data

    cleaned = []
    for i, itin in enumerate(items, start=1):
        try:
            cleaned.append(normalize_itinerary(itin or {}, i))
        except Exception as e:
            print(f'Failed to normalize itinerary at index {i}:', e)

    # Ensure output directories exist
    (ROOT / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
    (ROOT / 'data' / 'raw').mkdir(parents=True, exist_ok=True)

    processed_path = ROOT / 'data' / 'processed' / 'kerala_itineraries_clean.json'
    raw_out_path = ROOT / 'data' / 'raw' / 'kerala_itineraries.json'

    processed_path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding='utf-8')
    raw_out_path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'Cleaned {len(cleaned)} itineraries -> {processed_path}')
    if len(cleaned) > 0:
        print('Sample:', json.dumps(cleaned[0], ensure_ascii=False, indent=2))
    return 0


if _name_ == '_main_':
    raise SystemExit(main())
"""Cleaner for itinerary templates
Normalizes data/raw/kerala_itinerary_templates.json and writes processed copy.
"""
import json
from pathlib import Path


def clean_itineraries(raw_path=None, out_path=None):
    if raw_path is None:
        raw_path = Path(_file_).parents[2] / 'data' / 'raw' / 'kerala_itinerary_templates.json'
    if out_path is None:
        out_path = Path(_file_).parents[2] / 'data' / 'processed' / 'kerala_itineraries_clean.json'

    if not raw_path.exists():
        raise FileNotFoundError(f"Itineraries raw file not found: {raw_path}")

    doc = json.loads(raw_path.read_text(encoding='utf-8'))
    templates = doc.get('itineraries') if isinstance(doc, dict) else doc
    cleaned = []
    for t in (templates or []):
        if not isinstance(t, dict):
            continue
        tid = t.get('id') or t.get('name') and f"it_{abs(hash(t.get('name'))) % 100000}"
        days = t.get('duration_days') or t.get('days') or len(t.get('days_content', [])) if isinstance(t.get('days_content'), list) else None
        cleaned.append({
            'id': tid,
            'name': t.get('name') or t.get('title'),
            'duration_days': int(days) if days is not None else None,
            'interests': t.get('interests') or [],
            'budget': t.get('budget') or t.get('price_category') or None,
            'days': t.get('days') or t.get('days_content') or []
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({'itineraries': cleaned}, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Cleaned {len(cleaned)} itineraries -> {out_path}")
    return {'itineraries': cleaned}


if _name_ == '_main_':
    clean_itineraries()
