from datetime import datetime, timezone

from supabase_config import get_supabase_credentials, is_supabase_configured

TABLE_NAME = 'tracked_products'
VALID_STATUSES = {'in_stock', 'out_of_stock', 'unknown'}


def get_supabase_client():
    if not is_supabase_configured():
        raise RuntimeError(
            'Supabase is not configured. Add credentials to .streamlit/secrets.toml '
            'or set SUPABASE_URL and SUPABASE_KEY environment variables.'
        )

    from supabase import create_client

    url, key = get_supabase_credentials()
    return create_client(url, key)


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
    user_id=None,
):
    if stock_status not in VALID_STATUSES:
        stock_status = 'unknown'

    now = datetime.now(timezone.utc).isoformat()
    existing = get_tracked_product_by_url(markaz_url)
    client = get_supabase_client()

    if existing:
        payload = {
            'stock_status': stock_status,
            'last_checked_at': now,
        }
        if title:
            payload['title'] = title
        if shopify_handle:
            payload['shopify_handle'] = shopify_handle
        response = (
            client.table(TABLE_NAME)
            .update(payload)
            .eq('id', existing['id'])
            .execute()
        )
    else:
        payload = {
            'markaz_url': markaz_url,
            'stock_status': stock_status,
            'last_checked_at': now,
        }
        if title:
            payload['title'] = title
        if shopify_handle:
            payload['shopify_handle'] = shopify_handle
        if user_id:
            payload['user_id'] = user_id
        response = client.table(TABLE_NAME).insert(payload).execute()

    rows = response.data or []
    return rows[0] if rows else payload


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


def delete_tracked_product(markaz_url):
    client = get_supabase_client()
    client.table(TABLE_NAME).delete().eq('markaz_url', markaz_url).execute()
    return True
