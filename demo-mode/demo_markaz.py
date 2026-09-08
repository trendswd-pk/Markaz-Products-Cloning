from pricing_rules import get_default_price_adjustments


def fetch_demo_products_from_tracked_rows(tracked_rows):
    """Build converter-ready products from demo tracked rows (no live Markaz scrape)."""
    products = []
    processed_urls = set()
    failed = []

    for row in tracked_rows:
        link = (row.get('markaz_url') or '').strip()
        if not link:
            continue

        title = row.get('title') or 'Demo product'
        price = 1899.0
        variant_adj, compare_adj = get_default_price_adjustments(price)
        stock_status = row.get('stock_status', 'in_stock')

        products.append({
            'title': title,
            'description': (
                'Demo Mode sample product.\n'
                '• Not scraped from live Markaz\n'
                '• Shopify publish is simulated only'
            ),
            'price': price,
            'image_urls': [
                'https://content.public.markaz.app/markazimagevideo/public/products/2587-10-733736-product-1.webp',
            ],
            'base_sku': 'DEMO-SKU-001',
            'variants': ['Default Title'],
            'option1_name': 'Title',
            'breadcrumb_items': ['Demo', 'Products'],
            'stock_status': stock_status,
            'url': link,
            'status': 'success',
            'variant_price_adjustment': variant_adj,
            'compare_at_price_adjustment': compare_adj,
        })
        processed_urls.add(link)

    return products, processed_urls, failed
