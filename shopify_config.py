import os
from pathlib import Path

_SECRETS_PATH = Path(__file__).resolve().parent / '.streamlit' / 'secrets.toml'
DEFAULT_API_VERSION = '2024-10'
DEFAULT_SCOPES = (
    'read_products,write_products,read_inventory,write_inventory,read_locations'
)


def _load_from_secrets_file():
    if not _SECRETS_PATH.exists():
        return {}

    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    with _SECRETS_PATH.open('rb') as secrets_file:
        data = tomllib.load(secrets_file)

    return data.get('shopify', {})


def _normalize_shopify_section(section):
    return {
        'store_url': section.get('store_url', ''),
        'client_id': section.get('client_id', ''),
        'client_secret': section.get('client_secret', ''),
        'access_token': section.get('access_token', ''),
        'api_version': section.get('api_version', DEFAULT_API_VERSION),
        'scopes': section.get('scopes', DEFAULT_SCOPES),
    }


def get_shopify_credentials():
    """Load Shopify credentials from Streamlit secrets, env vars, or secrets.toml."""
    try:
        import streamlit as st

        if hasattr(st, 'secrets') and 'shopify' in st.secrets:
            return _normalize_shopify_section(st.secrets['shopify'])
    except Exception:
        pass

    store_url = os.getenv('SHOPIFY_STORE_URL', '')
    client_id = os.getenv('SHOPIFY_CLIENT_ID', '')
    client_secret = os.getenv('SHOPIFY_CLIENT_SECRET', '')
    access_token = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
    api_version = os.getenv('SHOPIFY_API_VERSION', DEFAULT_API_VERSION)
    scopes = os.getenv('SHOPIFY_SCOPES', DEFAULT_SCOPES)

    if store_url and (client_id and client_secret or access_token):
        return _normalize_shopify_section({
            'store_url': store_url,
            'client_id': client_id,
            'client_secret': client_secret,
            'access_token': access_token,
            'api_version': api_version,
            'scopes': scopes,
        })

    return _normalize_shopify_section(_load_from_secrets_file())


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


def is_shopify_configured():
    creds = get_shopify_credentials()
    store_url = (creds.get('store_url') or '').strip()
    if not store_url or _is_placeholder(store_url):
        return False

    client_id = (creds.get('client_id') or '').strip()
    client_secret = (creds.get('client_secret') or '').strip()
    if client_id and client_secret and not _is_placeholder(client_id) and not _is_placeholder(client_secret):
        return True

    access_token = (creds.get('access_token') or '').strip()
    return bool(access_token and not _is_placeholder(access_token))


def uses_client_credentials_flow():
    creds = get_shopify_credentials()
    client_id = (creds.get('client_id') or '').strip()
    client_secret = (creds.get('client_secret') or '').strip()
    return bool(
        client_id
        and client_secret
        and not _is_placeholder(client_id)
        and not _is_placeholder(client_secret)
    )
