import os
import time

import requests

from shopify_config import get_shopify_credentials

_TOKEN_CACHE = {
    'token': None,
    'expires_at': 0.0,
}


class ShopifyAuthError(Exception):
    pass


def _is_placeholder(value):
    placeholders = (
        'YOUR_STORE',
        'YOUR_CLIENT_ID',
        'YOUR_CLIENT_SECRET',
        'YOUR_SHOPIFY_ACCESS_TOKEN',
        'shpat_your',
        'your-client-id',
        'your-client-secret',
        'your-store',
        'PASTE_',
    )
    lowered = (value or '').lower()
    return not lowered or any(token.lower() in lowered for token in placeholders)


def fetch_access_token_via_client_credentials():
    if os.environ.get('MARKAZ_DEMO_MODE') == '1':
        from demo_mode.demo_guard import block_real_shopify_api

        block_real_shopify_api('authenticate with Shopify')
    creds = get_shopify_credentials()
    store_url = (
        creds.get('store_url', '')
        .replace('https://', '')
        .replace('http://', '')
        .strip()
        .strip('/')
    )
    client_id = (creds.get('client_id') or '').strip()
    client_secret = (creds.get('client_secret') or '').strip()

    if not store_url or not client_id or not client_secret:
        raise ShopifyAuthError('Missing store_url, client_id, or client_secret in Shopify config.')

    response = requests.post(
        f'https://{store_url}/admin/oauth/access_token',
        data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30,
    )

    if not response.ok:
        raise ShopifyAuthError(
            f'Token request failed ({response.status_code}): {response.text[:300]}'
        )

    data = response.json()
    access_token = data.get('access_token')
    if not access_token:
        raise ShopifyAuthError('Shopify token response did not include access_token.')

    expires_in = int(data.get('expires_in', 86399))
    return access_token, expires_in


def get_shopify_access_token(force_refresh=False):
    """Return a valid Admin API access token (client credentials or legacy static token)."""
    if os.environ.get('MARKAZ_DEMO_MODE') == '1':
        from demo_mode.demo_guard import block_real_shopify_api

        block_real_shopify_api('authenticate with Shopify')
    creds = get_shopify_credentials()
    client_id = (creds.get('client_id') or '').strip()
    client_secret = (creds.get('client_secret') or '').strip()
    static_token = (creds.get('access_token') or '').strip()

    if client_id and client_secret and not _is_placeholder(client_id) and not _is_placeholder(client_secret):
        now = time.time()
        if (
            not force_refresh
            and _TOKEN_CACHE['token']
            and _TOKEN_CACHE['expires_at'] > now
        ):
            return _TOKEN_CACHE['token']

        token, expires_in = fetch_access_token_via_client_credentials()
        _TOKEN_CACHE['token'] = token
        # Refresh 5 minutes before expiry (tokens last ~24 hours).
        _TOKEN_CACHE['expires_at'] = now + max(expires_in - 300, 60)
        return token

    if static_token and not _is_placeholder(static_token):
        return static_token

    raise ShopifyAuthError(
        'Shopify auth not configured. Add client_id + client_secret (new Dev Dashboard app) '
        'or access_token (legacy) in .streamlit/secrets.toml.'
    )


def clear_shopify_token_cache():
    _TOKEN_CACHE['token'] = None
    _TOKEN_CACHE['expires_at'] = 0.0
