import re
from urllib.parse import urlparse

from pricing_rules import get_default_price_adjustments

DEMO_IMAGE = (
    'https://content.public.markaz.app/markazimagevideo/public/products/'
    '2587-10-733736-product-1.webp'
)


def _empty_result(url, status):
    return {
        'title': None,
        'description': None,
        'price': None,
        'image_urls': [],
        'base_sku': None,
        'variants': ['Default Title'],
        'option1_name': 'Title',
        'breadcrumb_items': [],
        'stock_status': None,
        'url': url,
        'status': status,
    }


def _title_from_url(url):
    path = urlparse(url).path.strip('/')
    parts = [part for part in path.split('/') if part]
    if not parts:
        return 'Demo Product'

    slug = parts[-1]
    if slug.isdigit() and len(parts) >= 2:
        slug = parts[-2]

    slug = re.sub(r'-\d+$', '', slug)
    return slug.replace('-', ' ').strip().title() or 'Demo Product'


def _demo_sku(url):
    path = urlparse(url).path.strip('/')
    parts = [part for part in path.split('/') if part]
    slug = parts[-2] if parts and parts[-1].isdigit() and len(parts) >= 2 else (parts[-1] if parts else 'demo')
    token = re.sub(r'[^a-zA-Z0-9]', '', slug.upper())[:12] or 'DEMO'
    return f'DEMO-{token}'


def scrape_markaz_product_demo(url):
    """Simulate a Markaz scrape in demo mode (no Playwright, no network)."""
    url = (url or '').strip()
    if not url:
        return _empty_result(url, 'Error: URL is empty')

    if 'markaz.app' not in url.lower():
        return _empty_result(url, 'Error: Demo mode accepts Markaz product URLs only')

    title = _title_from_url(url)
    price = 1899.0
    variant_adj, compare_adj = get_default_price_adjustments(price)

    return {
        'title': title,
        'description': (
            'Demo Mode preview product.\n'
            '• Simulated from pasted URL\n'
            '• Not scraped from live Markaz\n'
            '• Shopify publish stays simulated'
        ),
        'price': price,
        'image_urls': [DEMO_IMAGE],
        'base_sku': _demo_sku(url),
        'variants': ['Default Title'],
        'option1_name': 'Title',
        'breadcrumb_items': ['Demo', 'Products'],
        'stock_status': 'in_stock',
        'url': url,
        'status': 'success',
        'variant_price_adjustment': variant_adj,
        'compare_at_price_adjustment': compare_adj,
        'demo_simulated': True,
    }


def scrape_product_from_page_demo(page, url):
    """Drop-in replacement for bulk fetch loops in demo mode."""
    return scrape_markaz_product_demo(url)
