import json
from datetime import datetime, timezone

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
    client = get_supabase_client()
    response = (
        client.table(TABLE_NAME)
        .select('*')
        .eq('markaz_url', markaz_url)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


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
):
    """Save/update one tracked product in 1 request (RPC or update+insert fallback)."""
    if stock_status not in VALID_STATUSES:
        stock_status = 'unknown'

    if _rpc_available():
        response = _execute_rpc(
            'upsert_tracked_product_rpc',
            {
                'p_markaz_url': markaz_url,
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
        if data:
            return data

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        'stock_status': stock_status,
        'last_checked_at': now,
    }
    if title:
        payload['title'] = title
    if shopify_handle:
        payload['shopify_handle'] = shopify_handle
    if shopify_product_id:
        payload['shopify_product_id'] = str(shopify_product_id)

    client = get_supabase_client()
    update_response = (
        client.table(TABLE_NAME)
        .update(payload)
        .eq('markaz_url', markaz_url)
        .execute()
    )
    updated_rows = update_response.data or []
    if updated_rows:
        return updated_rows[0]

    insert_payload = {
        'markaz_url': markaz_url,
        **payload,
    }
    if user_id:
        insert_payload['user_id'] = user_id

    insert_response = client.table(TABLE_NAME).insert(insert_payload).execute()
    rows = insert_response.data or []
    return rows[0] if rows else insert_payload


def batch_upsert_tracked_products(items):
    """Upsert many products in 1 HTTP call when RPC is available.

    items: list of dicts with markaz_url, stock_status, title, shopify_handle, ...
    Returns list of row dicts.
    """
    if not items:
        return []

    if _rpc_available():
        response = _execute_rpc(
            'batch_upsert_tracked_products_rpc',
            {'p_items': items},
        )
        data = response.data
        if isinstance(data, str):
            data = json.loads(data)
        return data or []

    results = []
    for item in items:
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

    client = get_supabase_client()
    response = (
        client.table(TABLE_NAME)
        .update(payload)
        .eq('markaz_url', markaz_url)
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
        markaz_url = (item or {}).get('markaz_url')
        if not markaz_url:
            continue
        if not item.get('shopify_product_id') and not item.get('shopify_handle'):
            continue
        valid_items.append({
            'markaz_url': markaz_url,
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
    urls = [url for url in (markaz_urls or []) if url]
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
