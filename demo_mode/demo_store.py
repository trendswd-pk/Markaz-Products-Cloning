import uuid
from datetime import datetime, timezone

from demo_mode.demo_config import TRACKED_PRODUCTS_KEY
from demo_mode.local_storage import get_current_storage
from markaz_scraper import canonicalize_markaz_product_url, extract_markaz_product_id

VALID_STATUSES = {'in_stock', 'out_of_stock', 'unknown'}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _load_rows():
    storage = get_current_storage()
    return storage.get(TRACKED_PRODUCTS_KEY, []) or []


def _save_rows(rows):
    storage = get_current_storage()
    storage.set(TRACKED_PRODUCTS_KEY, rows)


def _norm(url):
    return canonicalize_markaz_product_url(url or '') or (url or '').strip()


def list_tracked_products():
    rows = _load_rows()
    return sorted(rows, key=lambda row: row.get('created_at', ''), reverse=True)


def get_tracked_product_by_url(markaz_url):
    markaz_url = _norm(markaz_url)
    product_id = extract_markaz_product_id(markaz_url)
    for row in _load_rows():
        if _norm(row.get('markaz_url')) == markaz_url:
            return row
        if product_id and extract_markaz_product_id(row.get('markaz_url')) == product_id:
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
    shopify_product_id=None,
    user_id=None,
    prefer_existing_url=None,
):
    if stock_status not in VALID_STATUSES:
        stock_status = 'unknown'

    markaz_url = _norm(markaz_url)
    rows = _load_rows()
    now = _now()
    existing = None
    if prefer_existing_url:
        existing = get_tracked_product_by_url(prefer_existing_url)
    if not existing:
        existing = get_tracked_product_by_url(markaz_url)

    if existing:
        existing['markaz_url'] = markaz_url
        existing['stock_status'] = stock_status
        existing['last_checked_at'] = now
        if title:
            existing['title'] = title
        if shopify_handle:
            existing['shopify_handle'] = shopify_handle
        if shopify_product_id:
            existing['shopify_product_id'] = str(shopify_product_id)
        # Drop other same-id rows
        product_id = extract_markaz_product_id(markaz_url)
        if product_id:
            rows = [
                r for r in rows
                if r is existing or extract_markaz_product_id(r.get('markaz_url')) != product_id
            ]
            if existing not in rows:
                rows.append(existing)
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
    if shopify_product_id:
        row['shopify_product_id'] = str(shopify_product_id)
    if user_id:
        row['user_id'] = user_id

    rows.append(row)
    _save_rows(rows)
    return row


def update_tracked_stock_status(markaz_url, stock_status, title=None, shopify_handle=None):
    return upsert_tracked_product(
        markaz_url=markaz_url,
        stock_status=stock_status,
        title=title,
        shopify_handle=shopify_handle,
    )


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
    return delete_tracked_products([markaz_url])


def delete_tracked_products(markaz_urls):
    urls = {_norm(url) for url in (markaz_urls or []) if url}
    urls |= {url for url in (markaz_urls or []) if url}
    if not urls:
        return True
    rows = [
        row for row in _load_rows()
        if row.get('markaz_url') not in urls and _norm(row.get('markaz_url')) not in urls
    ]
    _save_rows(rows)
    return True


def batch_upsert_tracked_products(items):
    results = []
    for item in items or []:
        row = upsert_tracked_product(
            markaz_url=item.get('markaz_url'),
            stock_status=item.get('stock_status', 'unknown'),
            title=item.get('title'),
            shopify_handle=item.get('shopify_handle'),
            shopify_product_id=item.get('shopify_product_id'),
            user_id=item.get('user_id'),
        )
        if row:
            results.append(row)
    return results


def update_tracked_shopify_metadata_batch(items):
    updated = 0
    for item in items or []:
        result = update_tracked_shopify_metadata(
            item.get('markaz_url'),
            shopify_product_id=item.get('shopify_product_id'),
            shopify_handle=item.get('shopify_handle'),
        )
        if result:
            updated += 1
    return updated


def count_duplicate_tracked_products(rows=None):
    rows = list(rows if rows is not None else list_tracked_products())
    by_id = {}
    for row in rows:
        pid = extract_markaz_product_id(row.get('markaz_url')) or _norm(row.get('markaz_url'))
        by_id.setdefault(pid, []).append(row)
    groups = sum(1 for g in by_id.values() if len(g) > 1)
    extra = sum(max(0, len(g) - 1) for g in by_id.values())
    return groups, extra


def dedupe_tracked_products(rows=None):
    rows = list(rows if rows is not None else list_tracked_products())
    by_id = {}
    for row in rows:
        pid = extract_markaz_product_id(row.get('markaz_url')) or _norm(row.get('markaz_url'))
        by_id.setdefault(pid, []).append(row)

    kept = []
    removed = 0
    for group in by_id.values():
        if len(group) == 1:
            kept.append(group[0])
            continue
        group_sorted = sorted(
            group,
            key=lambda r: (
                1 if r.get('shopify_product_id') else 0,
                1 if r.get('shopify_handle') else 0,
                r.get('last_checked_at') or '',
            ),
            reverse=True,
        )
        keeper = dict(group_sorted[0])
        for other in group_sorted[1:]:
            removed += 1
            if not keeper.get('shopify_product_id') and other.get('shopify_product_id'):
                keeper['shopify_product_id'] = other['shopify_product_id']
            if not keeper.get('shopify_handle') and other.get('shopify_handle'):
                keeper['shopify_handle'] = other['shopify_handle']
        keeper['markaz_url'] = _norm(keeper.get('markaz_url'))
        kept.append(keeper)

    _save_rows(kept)
    return {
        'groups': sum(1 for g in by_id.values() if len(g) > 1),
        'removed': removed,
        'kept_urls': [r.get('markaz_url') for r in kept],
        'removed_urls': [],
    }