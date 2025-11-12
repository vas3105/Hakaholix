import json
import re
from pathlib import Path


def _extract_json_objects(text: str):
    """Heuristic: extract top-level JSON objects by scanning braces.
    Returns list of JSON strings."""
    objs = []
    i = 0
    n = len(text)
    while i < n:
        # find next '{'
        if text[i] == '{':
            depth = 0
            start = i
            j = i
            while j < n:
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                    if depth == 0:
                        # extract
                        objs.append(text[start:j+1])
                        i = j
                        break
                j += 1
        i += 1
    return objs


def _sanitize_string_fields(obj):
    # sanitize common noise patterns
    if 'reviews' in obj and isinstance(obj['reviews'], dict):
        tr = obj['reviews'].get('total_reviews')
        if isinstance(tr, str):
            m = re.search(r"(\d+)", tr)
            if m:
                obj['reviews']['total_reviews'] = int(m.group(1))
        # normalize sentiment keys to keep original if unknown
        sd = obj['reviews'].get('sentiment_breakdown')
        if isinstance(sd, dict):
            # remove any stray percent strings
            for k, v in list(sd.items()):
                if isinstance(v, str):
                    mv = re.search(r"(\d+(?:\.\d+)?)", v)
                    if mv:
                        try:
                            sd[k] = float(mv.group(1))
                        except Exception:
                            pass

    # clean amenities contentReference noise
    features = obj.get('features', {})
    if isinstance(features, dict):
        amenities = features.get('amenities')
        if isinstance(amenities, list):
            clean_amen = []
            for a in amenities:
                if isinstance(a, str):
                    a_clean = re.sub(r":contentReference\[.?\]\{.?\}", "", a)
                    a_clean = a_clean.replace("\n", " ").strip()
                    clean_amen.append(a_clean)
                else:
                    clean_amen.append(a)
            features['amenities'] = clean_amen

    return obj


def clean_hotels(raw_paths=None, out_path=None):
    """Read existing raw hotel JSON (robust to malformed file), normalize and write cleaned JSON.

    - raw_paths: iterable of candidate file paths to try
    - out_path: where to write cleaned JSON (defaults to data/raw/kerala_hotels.json)
    """
    if raw_paths is None:
        raw_paths = [
            Path(_file_).parents[2] / 'data' / 'raw' / 'kerala_hotels.json',
            Path(_file_).parents[2] / 'data' / 'raw' / 'Kerala_hotels.json'
        ]

    raw_text = None
    raw_file = None
    for p in raw_paths:
        if p.exists():
            raw_text = p.read_text(encoding='utf-8')
            raw_file = p
            break

    if raw_text is None:
        raise FileNotFoundError(f"No raw hotels JSON found in: {raw_paths}")

    # try parse directly
    hotels = []
    try:
        doc = json.loads(raw_text)
        if isinstance(doc, dict) and 'hotels' in doc and isinstance(doc['hotels'], list):
            hotels = doc['hotels']
        elif isinstance(doc, list):
            hotels = doc
        else:
            # look for objects inside dict
            for v in doc.values():
                if isinstance(v, list):
                    hotels = v
                    break
    except Exception:
        # fallback: extract all top-level JSON objects heuristically
        objs = _extract_json_objects(raw_text)
        for s in objs:
            try:
                o = json.loads(s)
                # Only grab hotel-like objects
                if isinstance(o, dict) and o.get('id', '').startswith('hotel'):
                    hotels.append(o)
            except Exception:
                continue

    # sanitize and normalize
    cleaned = []
    seen_ids = set()
    for h in hotels:
        # basic shape guard
        if not isinstance(h, dict):
            continue
        if 'id' not in h:
            # skip entries without id
            continue
        if h['id'] in seen_ids:
            continue
        seen_ids.add(h['id'])

        # ensure coordinates are floats
        loc = h.get('location', {})
        coords = loc.get('coordinates') if isinstance(loc, dict) else None
        if isinstance(coords, dict):
            try:
                coords['lat'] = float(coords.get('lat'))
                coords['lng'] = float(coords.get('lng'))
            except Exception:
                # remove invalid coordinates
                loc['coordinates'] = None

        # sanitize string fields and nested issues
        h = _sanitize_string_fields(h)

        cleaned.append(h)

    out_path = Path(out_path) if out_path else Path(_file_).parents[2] / 'data' / 'raw' / 'kerala_hotels.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_doc = {'hotels': cleaned}
    out_path.write_text(json.dumps(out_doc, indent=2, ensure_ascii=False), encoding='utf-8')

    # also save a processed copy
    proc = Path(_file_).parents[2] / 'data' / 'processed' / 'kerala_hotels_clean.json'
    proc.parent.mkdir(parents=True, exist_ok=True)
    proc.write_text(json.dumps(out_doc, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f"Cleaned {len(cleaned)} hotels -> {out_path}")
    return out_doc


if _name_ == '_main_':
    clean_hotels()
