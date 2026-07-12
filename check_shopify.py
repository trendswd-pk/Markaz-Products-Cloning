"""Quick check after pasting Shopify Client ID + Secret into .streamlit/secrets.toml"""

from shopify_auth import ShopifyAuthError, clear_shopify_token_cache, get_shopify_access_token
from shopify_config import get_shopify_credentials, is_shopify_configured, uses_client_credentials_flow
from shopify_sync import ShopifyAPIError, get_shopify_client


def main():
    if not is_shopify_configured():
        print('Shopify credentials are missing or still placeholders.')
        print('Edit: .streamlit/secrets.toml')
        print('Required: store_url + client_id + client_secret')
        return

    creds = get_shopify_credentials()
    print(f"Store: {creds['store_url']}")

    if uses_client_credentials_flow():
        print('Auth mode: Client ID + Secret (Dev Dashboard app)')
    else:
        print('Auth mode: Legacy static access_token')

    try:
        clear_shopify_token_cache()
        token = get_shopify_access_token(force_refresh=True)
        shop = get_shopify_client().test_connection()
    except (ShopifyAuthError, ShopifyAPIError) as exc:
        print(f'Shopify connection failed: {exc}')
        return
    except Exception as exc:
        print(f'Shopify connection failed: {exc}')
        return

    print('Shopify connection OK.')
    print(f"Shop name: {shop.get('name')}")
    print(f"Domain: {shop.get('domain')}")
    print(f"Access token received ({len(token)} chars, auto-refreshes every ~24h)")


if __name__ == '__main__':
    main()
