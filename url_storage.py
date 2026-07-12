import json
import os
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
HISTORY_FILE = os.path.join(DATA_DIR, 'url_history.json')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_url_history():
    """Load saved product URLs from local JSON file."""
    _ensure_data_dir()
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_url_history(entries):
    """Persist the full URL history list."""
    _ensure_data_dir()
    with open(HISTORY_FILE, 'w', encoding='utf-8') as file:
        json.dump(entries, file, indent=2, ensure_ascii=False)


def save_url_entry(product_data):
    """Add or update a product URL in local history."""
    url = (product_data or {}).get('url', '').strip()
    if not url:
        return

    entries = load_url_history()
    entry = {
        'url': url,
        'title': product_data.get('title') or '',
        'base_sku': product_data.get('base_sku') or '',
        'price': str(product_data.get('price') or ''),
        'saved_at': datetime.now(timezone.utc).isoformat(),
    }

    updated = False
    for idx, existing in enumerate(entries):
        if existing.get('url') == url:
            entries[idx] = entry
            updated = True
            break

    if not updated:
        entries.insert(0, entry)

    save_url_history(entries)


def remove_url_entry(url):
    """Remove one URL from history."""
    entries = [item for item in load_url_history() if item.get('url') != url]
    save_url_history(entries)


def clear_url_history():
    """Delete all saved URLs."""
    save_url_history([])
