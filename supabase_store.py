from datetime import datetime, timezone

from supabase_config import get_supabase_credentials, is_supabase_configured

TABLE_NAME = 'tracked_products'
VALID_STATUSES = {'in_stock', 'out_of_stock', 'unknown'}

_CLIENT = None


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
    global _CLIENT
    _CLIENT = None


def list_tracked_products():
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
    """Save/update one tracked product in ideally 1 request (update), or 2 (update miss + insert).

    Avoids the old pattern of SELECT-then-UPDATE (was always 2+ requests).
    """
    if stock_status not in VALID_STATUSES:
        stock_status = 'unknown'

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


def update_tracked_stock_status(markaz_url, stock_status, title=None, shopify_handle=None):
    if stock_status not in VALID_STATUSES:
        stock_status = 'unknown'

    payload = {
        'stock_status': stock_status,
        'last_checked_at': datetime.now(timezone.utc).isoformat(),
    }
    if title:
        payload['title'] = title
    if shopify_handle:
        payload['shopify_handle'] = shopify_handle

    client = get_supabase_client()
    response = (
        client.table(TABLE_NAME)
        .update(payload)
        .eq('markaz_url', markaz_url)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


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
    """Update Shopify metadata for many products (one request each, shared client).

    items: [{'markaz_url': ..., 'shopify_product_id': ..., 'shopify_handle': ...}, ...]
    """
    updated = 0
    for item in items or []:
        markaz_url = (item or {}).get('markaz_url')
        if not markaz_url:
            continue
        result = update_tracked_shopify_metadata(
            markaz_url,
            shopify_product_id=item.get('shopify_product_id'),
            shopify_handle=item.get('shopify_handle'),
        )
        if result:
            updated += 1
    return updated


def delete_tracked_product(markaz_url):
    client = get_supabase_client()
    client.table(TABLE_NAME).delete().eq('markaz_url', markaz_url).execute()
    return True


def delete_tracked_products(markaz_urls):
    """Delete many tracked products in one Supabase request."""
    urls = [url for url in (markaz_urls or []) if url]
    if not urls:
        return True

    client = get_supabase_client()
    # Chunk to keep request size reasonable.
    chunk_size = 100
    for start in range(0, len(urls), chunk_size):
        chunk = urls[start:start + chunk_size]
        client.table(TABLE_NAME).delete().in_('markaz_url', chunk).execute()
    return True
