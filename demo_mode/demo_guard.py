import os

DEMO_SHOPIFY_ALERT = (
    '**Demo Mode:** No real Shopify connection. This action was simulated only — '
    'nothing was sent to your live store.'
)


class DemoModeShopifyBlocked(Exception):
    """Raised when production code tries to call Shopify API in demo mode."""


def is_demo_mode():
    return os.environ.get('MARKAZ_DEMO_MODE') == '1'


def block_real_shopify_api(action='access Shopify'):
    if is_demo_mode():
        raise DemoModeShopifyBlocked(
            f'Demo Mode: cannot {action}. Use production app (streamlit run app.py) for live Shopify.'
        )


def demo_shopify_handle(handle):
    """Namespace handles so demo never collides with a real Shopify product."""
    handle = (handle or '').strip().lower()
    if not handle:
        return 'demo-product'
    if handle.startswith('demo-'):
        return handle
    return f'demo-{handle}'
