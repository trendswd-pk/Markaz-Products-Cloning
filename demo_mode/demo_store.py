import uuid
from datetime import datetime, timezone

from demo_mode.demo_config import TRACKED_PRODUCTS_KEY
from demo_mode.local_storage import get_current_storage

VALID_STATUSES = {'in_stock', 'out_of_stock', 'unknown'}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _load_rows():
    storage = get_current_storage()
    return storage.get(TRACKED_PRODUCTS_KEY, []) or []


def _save_rows(rows):
    storage = get_current_storage()
    storage.set(TRACKED_PRODUCTS_KEY, rows)


def list_tracked_products():
    rows = _load_rows()
    return sorted(rows, key=lambda row: row.get('created_at', ''), reverse=True)


def get_tracked_product_by_url(markaz_url):
    for row in _load_rows():
        if row.get('markaz_url') == markaz_url:
            return row
    return None


def get_tracked_product_by_handle(shopify_handle):
    for row in _load_rows():
        if row.get('shopify_handle') == shopify_handle:
            return row
    return None


def upsert_tracked_product(
    markaz_url,
    stock_status='unknown',
    title=None,
    shopify_handle=None,
    user_id=None,
):
    if stock_status not in VALID_STATUSES:
        stock_status = 'unknown'

    rows = _load_rows()
    now = _now()
    existing = get_tracked_product_by_url(markaz_url)

    if existing:
        existing['stock_status'] = stock_status
        existing['last_checked_at'] = now
        if title:
            existing['title'] = title
        if shopify_handle:
            existing['shopify_handle'] = shopify_handle
        _save_rows(rows)
        return existing

    row = {
        'id': f'demo-{uuid.uuid4().hex[:8]}',
        'markaz_url': markaz_url,
        'stock_status': stock_status,
        'last_checked_at': now,
        'created_at': now,
    }
    if title:
        row['title'] = title
    if shopify_handle:
        row['shopify_handle'] = shopify_handle
    if user_id:
        row['user_id'] = user_id

    rows.append(row)
    _save_rows(rows)
    return row


def update_tracked_stock_status(markaz_url, stock_status, title=None, shopify_handle=None):
    if stock_status not in VALID_STATUSES:
        stock_status = 'unknown'

    existing = get_tracked_product_by_url(markaz_url)
    if not existing:
        return None

    existing['stock_status'] = stock_status
    existing['last_checked_at'] = _now()
    if title:
        existing['title'] = title
    if shopify_handle:
        existing['shopify_handle'] = shopify_handle

    _save_rows(_load_rows())
    return existing


def update_tracked_shopify_metadata(markaz_url, shopify_product_id=None, shopify_handle=None):
    existing = get_tracked_product_by_url(markaz_url)
    if not existing:
        return None

    if shopify_product_id:
        existing['shopify_product_id'] = str(shopify_product_id)
    if shopify_handle:
        existing['shopify_handle'] = shopify_handle

    _save_rows(_load_rows())
    return existing


def delete_tracked_product(markaz_url):
    rows = [row for row in _load_rows() if row.get('markaz_url') != markaz_url]
    _save_rows(rows)
    return True
