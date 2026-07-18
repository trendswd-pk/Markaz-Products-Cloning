import json
from datetime import datetime, timezone

from markaz_scraper import (
    canonicalize_markaz_product_url,
    extract_markaz_product_id,
)
from supabase_config import get_supabase_credentials, is_supabase_configured

TABLE_NAME = 'tracked_products'
VALID_STATUSES = {'in_stock', 'out_of_stock', 'unknown'}

_CLIENT = None
_USE_RPC = None  # None = auto-detect on first call


def get_supabase_client():
    """Reuse one Supabase client for the process (avoids reconnect overhead)."""
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    if not is_supabase_configured():
        raise RuntimeError(
            'Supabase is not configured. Add credentials to .streamlit/secrets.toml '
            'or set SUPABASE_URL and SUPABASE_KEY environment variables.'
        )

    from supabase import create_client

    url, key = get_supabase_credentials()
    _CLIENT = create_client(url, key)
    return _CLIENT


def clear_supabase_client_cache():
    global _CLIENT, _USE_RPC
    _CLIENT = None
    _USE_RPC = None


def _rpc_available():
    """Detect once whether RPC functions are installed in Supabase."""
    global _USE_RPC
    if _USE_RPC is not None:
        return _USE_RPC

    try:
        client = get_supabase_client()
        client.rpc('list_tracked_products_rpc').execute()
        _USE_RPC = True
    except Exception:
        _USE_RPC = False
    return _USE_RPC


def _execute_rpc(function_name, params=None):
    client = get_supabase_client()
    request = client.rpc(function_name, params or {})
    return request.execute()


def _normalize_tracked_url(markaz_url):
    return canonicalize_markaz_product_url(markaz_url or '') or (markaz_url or '').strip()


def _row_product_id(row):
    if not row:
        return None
    return extract_markaz_product_id(row.get('markaz_url') or '')


def _row_sort_key(row):
    """Higher score = better keeper when merging duplicates."""
    score = 0
    if row.get('shopify_product_id'):
        score += 100
    if row.get('shopify_handle'):
        score += 40
    if row.get('title'):
        score += 10
    if row.get('stock_status') and row.get('stock_status') != 'unknown':
        score += 5
    # Prefer newest activity
    stamp = row.get('last_checked_at') or row.get('created_at') or ''
    return (score, stamp)


def find_tracked_duplicates(rows=None):
    """Group tracked rows that represent the same Markaz product (or same Shopify handle)."""
    rows = list(rows if rows is not None else list_tracked_products())
    by_product_id = {}
    by_handle = {}
    no_id = []

    for row in rows:
        product_id = _row_product_id(row)
        handle = (row.get('shopify_handle') or '').strip().lower()
        if product_id:
            by_product_id.setdefault(product_id, []).append(row)
        else:
            no_id.append(row)
        if handle:
            by_handle.setdefault(handle, []).append(row)

    duplicate_groups = []
    seen_row_ids = set()

    for product_id, group in by_product_id.items():
        if len(group) < 2:
            continue
        duplicate_groups.append({
            'key': f'markaz:{product_id}',
            'kind': 'markaz_product_id',
            'rows': group,
        })
        for row in group:
            seen_row_ids.add(row.get('id') or row.get('markaz_url'))

    for handle, group in by_handle.items():
        # Only count as duplicate if multiple distinct Markaz URLs share one handle.
        unique_urls = {
            _normalize_tracked_url(r.get('markaz_url'))
            for r in group
            if r.get('markaz_url')
        }
        if len(unique_urls) < 2:
            continue
        # Skip if already covered by product-id group membership entirely.
        group_ids = {r.get('id') or r.get('markaz_url') for r in group}
        if group_ids and group_ids.issubset(seen_row_ids):
            continue
        duplicate_groups.append({
            'key': f'handle:{handle}',
            'kind': 'shopify_handle',
            'rows': group,
        })

    return duplicate_groups


def count_duplicate_tracked_products(rows=None):
    groups = find_tracked_duplicates(rows)
    extra = 0
    for group in groups:
        extra += max(0, len(group['rows']) - 1)
    return len(groups), extra


def _merge_row_fields(keeper, others):
    merged = dict(keeper)
    for row in others:
        if not merged.get('shopify_product_id') and row.get('shopify_product_id'):
            merged['shopify_product_id'] = row['shopify_product_id']
        if not merged.get('shopify_handle') and row.get('shopify_handle'):
            merged['shopify_handle'] = row['shopify_handle']
        if not merged.get('title') and row.get('title'):
            merged['title'] = row['title']
        if (
            (not merged.get('stock_status') or merged.get('stock_status') == 'unknown')
            and row.get('stock_status')
            and row.get('stock_status') != 'unknown'
        ):
            merged['stock_status'] = row['stock_status']
    merged['markaz_url'] = _normalize_tracked_url(merged.get('markaz_url'))
    return merged


def dedupe_tracked_products(rows=None):
    """Merge duplicate Markaz links into one row each. Returns summary dict."""
    rows = list(rows if rows is not None else list_tracked_products())
    groups = find_tracked_duplicates(rows)
    if not groups:
        return {
            'groups': 0,
            'removed': 0,
            'kept_urls': [],
            'removed_urls': [],
        }

    removed_urls = []
    kept_urls = []
    processed_ids = set()

    for group in groups:
        group_rows = group['rows']
        # Avoid deleting the same row twice across overlapping groups.
        fresh = []
        for row in group_rows:
            key = row.get('id') or row.get('markaz_url')
            if key in processed_ids:
                continue
            fresh.append(row)
        if len(fresh) < 2:
            continue

        ordered = sorted(fresh, key=_row_sort_key, reverse=True)
        keeper = ordered[0]
        others = ordered[1:]
        merged = _merge_row_fields(keeper, others)

        # Persist keeper with merged fields + canonical URL.
        upsert_tracked_product(
            markaz_url=merged.get('markaz_url'),
            stock_status=merged.get('stock_status', 'unknown'),
            title=merged.get('title'),
            shopify_handle=merged.get('shopify_handle'),
            shopify_product_id=merged.get('shopify_product_id'),
            prefer_existing_url=keeper.get('markaz_url'),
        )
        kept_urls.append(merged.get('markaz_url'))

        urls_to_delete = []
        for row in others:
            url = row.get('markaz_url')
            if url and _normalize_tracked_url(url) != _normalize_tracked_url(merged.get('markaz_url')):
                urls_to_delete.append(url)
                removed_urls.append(url)
            processed_ids.add(row.get('id') or url)

        processed_ids.add(keeper.get('id') or keeper.get('markaz_url'))
        if urls_to_delete:
            delete_tracked_products(urls_to_delete)

    return {
        'groups': len(groups),
        'removed': len(removed_urls),
        'kept_urls': kept_urls,
        'removed_urls': removed_urls,
    }


def list_tracked_products():
    """Fetch all tracked products — prefers 1 RPC call."""
    if _rpc_available():
        response = _execute_rpc('list_tracked_products_rpc')
        data = response.data
        if isinstance(data, str):
            data = json.loads(data)
        return data or []

    client = get_supabase_client()
    response = (
        client.table(TABLE_NAME)
        .select('*')
        .order('created_at', desc=True)
        .execute()
    )
    return response.data or []


def get_tracked_product_by_url(markaz_url):
    markaz_url = _normalize_tracked_url(markaz_url)
    client = get_supabase_client()
    response = (
        client.table(TABLE_NAME)
        .select('*')
        .eq('markaz_url', markaz_url)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if rows:
        return rows[0]

    product_id = extract_markaz_product_id(markaz_url)
    if not product_id:
        return None

    # Same product may exist under a different slug / host.
    response = (
        client.table(TABLE_NAME)
        .select('*')
        .like('markaz_url', f'%/{product_id}')
        .execute()
    )
    for row in response.data or []:
        if extract_markaz_product_id(row.get('markaz_url')) == product_id:
            return row
    return None


def get_tracked_product_by_handle(shopify_handle):
    client = get_supabase_client()
    response = (
        client.table(TABLE_NAME)
        .select('*')
        .eq('shopify_handle', shopify_handle)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def upsert_tracked_product(
    markaz_url,
    stock_status='unknown',
    title=None,
    shopify_handle=None,
    shopify_product_id=None,
    user_id=None,
    prefer_existing_url=None,
):
    """Save/update one tracked product (1 product id = 1 row).

    Matches existing rows by Markaz product id (not only exact URL string), so
    slug/host variants do not create duplicates.
    """
    if stock_status not in VALID_STATUSES:
        stock_status = 'unknown'

    canonical_url = _normalize_tracked_url(markaz_url)
    product_id = extract_markaz_product_id(canonical_url)
    existing = None
    if prefer_existing_url:
        existing = get_tracked_product_by_url(prefer_existing_url)
    if not existing:
        existing = get_tracked_product_by_url(canonical_url)

    # Also collapse by Shopify handle when Markaz id is missing/ambiguous.
    if not existing and shopify_handle:
        by_handle = get_tracked_product_by_handle(shopify_handle)
        if by_handle:
            existing_id = extract_markaz_product_id(by_handle.get('markaz_url'))
            if not product_id or not existing_id or existing_id == product_id:
                existing = by_handle

    target_url = _normalize_tracked_url(
        (existing or {}).get('markaz_url') or canonical_url
    )
    # Prefer newest canonical URL when existing slug differs but id matches.
    if existing and product_id and extract_markaz_product_id(existing.get('markaz_url')) == product_id:
        target_url = canonical_url or target_url

    if _rpc_available():
        response = _execute_rpc(
            'upsert_tracked_product_rpc',
            {
                'p_markaz_url': target_url,
                'p_stock_status': stock_status,
                'p_title': title,
                'p_shopify_handle': shopify_handle,
                'p_shopify_product_id': shopify_product_id,
                'p_user_id': user_id,
            },
        )
        data = response.data
        if isinstance(data, str):
            data = json.loads(data)

        # If we matched an older URL string, update/delete the old exact URL after RPC.
        if existing and existing.get('markaz_url') and existing.get('markaz_url') != target_url:
            old_url = existing['markaz_url']
            # Ensure new canonical row exists, then remove old duplicate URL row.
            if data:
                try:
                    delete_tracked_products([old_url])
                except Exception:
                    pass
            else:
                # Fall through to table update path below.
                existing = existing
                data = None

        if data:
            # If another row still shares this product id, clean it.
            _delete_other_rows_for_product_id(product_id, keep_url=target_url)
            return data

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        'stock_status': stock_status,
        'last_checked_at': now,
        'markaz_url': target_url,
    }
    if title:
        payload['title'] = title
    if shopify_handle:
        payload['shopify_handle'] = shopify_handle
    if shopify_product_id:
        payload['shopify_product_id'] = str(shopify_product_id)

    client = get_supabase_client()

    if existing and existing.get('markaz_url'):
        update_response = (
            client.table(TABLE_NAME)
            .update(payload)
            .eq('markaz_url', existing['markaz_url'])
            .execute()
        )
        updated_rows = update_response.data or []
        if updated_rows:
            # If URL changed, also try update by new URL path / cleanup old
            if existing['markaz_url'] != target_url:
                # Row updated in place with new markaz_url in payload — good.
                pass
            _delete_other_rows_for_product_id(product_id, keep_url=target_url)
            return updated_rows[0]

    # Exact URL update (no prior match via id)
    update_response = (
        client.table(TABLE_NAME)
        .update({k: v for k, v in payload.items() if k != 'markaz_url'})
        .eq('markaz_url', target_url)
        .execute()
    )
    updated_rows = update_response.data or []
    if updated_rows:
        _delete_other_rows_for_product_id(product_id, keep_url=target_url)
        return updated_rows[0]

    insert_payload = {
        'markaz_url': target_url,
        **{k: v for k, v in payload.items() if k != 'markaz_url'},
    }
    if user_id:
        insert_payload['user_id'] = user_id

    insert_response = client.table(TABLE_NAME).insert(insert_payload).execute()
    rows = insert_response.data or []
    _delete_other_rows_for_product_id(product_id, keep_url=target_url)
    return rows[0] if rows else insert_payload


def _delete_other_rows_for_product_id(product_id, keep_url):
    if not product_id:
        return
    keep_url = _normalize_tracked_url(keep_url)
    client = get_supabase_client()
    response = (
        client.table(TABLE_NAME)
        .select('markaz_url')
        .like('markaz_url', f'%/{product_id}')
        .execute()
    )
    to_delete = []
    for row in response.data or []:
        url = row.get('markaz_url')
        if not url:
            continue
        if extract_markaz_product_id(url) != product_id:
            continue
        if _normalize_tracked_url(url) != keep_url:
            to_delete.append(url)
    if to_delete:
        delete_tracked_products(to_delete)


def batch_upsert_tracked_products(items):
    """Upsert many products; collapses same Markaz product id to one row."""
    if not items:
        return []

    # Collapse batch itself first (same product id twice in one Refresh All).
    collapsed = {}
    for item in items:
        url = _normalize_tracked_url((item or {}).get('markaz_url'))
        if not url:
            continue
        product_id = extract_markaz_product_id(url) or url
        previous = collapsed.get(product_id) or {}
        merged = {**previous, **{k: v for k, v in item.items() if v is not None}}
        merged['markaz_url'] = url
        collapsed[product_id] = merged

    normalized_items = list(collapsed.values())

    if _rpc_available():
        # Still upsert one-by-one via smart upsert so product-id merge works.
        # (Batch RPC matches exact URL only.)
        results = []
        for item in normalized_items:
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

    results = []
    for item in normalized_items:
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


def update_tracked_stock_status(markaz_url, stock_status, title=None, shopify_handle=None):
    return upsert_tracked_product(
        markaz_url=markaz_url,
        stock_status=stock_status,
        title=title,
        shopify_handle=shopify_handle,
    )


def update_tracked_shopify_metadata(markaz_url, shopify_product_id=None, shopify_handle=None):
    payload = {}
    if shopify_product_id:
        payload['shopify_product_id'] = str(shopify_product_id)
    if shopify_handle:
        payload['shopify_handle'] = shopify_handle
    if not payload:
        return None

    existing = get_tracked_product_by_url(markaz_url)
    target_url = (existing or {}).get('markaz_url') or _normalize_tracked_url(markaz_url)

    client = get_supabase_client()
    response = (
        client.table(TABLE_NAME)
        .update(payload)
        .eq('markaz_url', target_url)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def update_tracked_shopify_metadata_batch(items):
    """Update Shopify metadata for many products (1 RPC call when available).

    items: [{'markaz_url': ..., 'shopify_product_id': ..., 'shopify_handle': ...}, ...]
    """
    valid_items = []
    for item in items or []:
        markaz_url = _normalize_tracked_url((item or {}).get('markaz_url'))
        if not markaz_url:
            continue
        if not item.get('shopify_product_id') and not item.get('shopify_handle'):
            continue
        existing = get_tracked_product_by_url(markaz_url)
        valid_items.append({
            'markaz_url': (existing or {}).get('markaz_url') or markaz_url,
            'shopify_product_id': item.get('shopify_product_id'),
            'shopify_handle': item.get('shopify_handle'),
        })

    if not valid_items:
        return 0

    if _rpc_available():
        response = _execute_rpc(
            'batch_update_shopify_metadata_rpc',
            {'p_items': valid_items},
        )
        return int(response.data or 0)

    updated = 0
    for item in valid_items:
        result = update_tracked_shopify_metadata(
            item['markaz_url'],
            shopify_product_id=item.get('shopify_product_id'),
            shopify_handle=item.get('shopify_handle'),
        )
        if result:
            updated += 1
    return updated


def delete_tracked_product(markaz_url):
    return delete_tracked_products([markaz_url])


def delete_tracked_products(markaz_urls):
    """Delete many tracked products in one Supabase request."""
    urls = [_normalize_tracked_url(url) for url in (markaz_urls or []) if url]
    # Also delete non-canonical originals if caller passed raw URLs.
    raw_urls = [url for url in (markaz_urls or []) if url]
    urls = list(dict.fromkeys([*urls, *raw_urls]))
    if not urls:
        return True

    if _rpc_available():
        _execute_rpc('delete_tracked_products_rpc', {'p_markaz_urls': urls})
        return True

    client = get_supabase_client()
    chunk_size = 100
    for start in range(0, len(urls), chunk_size):
        chunk = urls[start:start + chunk_size]
        client.table(TABLE_NAME).delete().in_('markaz_url', chunk).execute()
    return True
