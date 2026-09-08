from datetime import datetime, timezone

from pricing_rules import get_default_price_adjustments


def _now():
    return datetime.now(timezone.utc).isoformat()


DUMMY_TRACKED_PRODUCTS = [
    {
        'id': 'demo-tracked-1',
        'markaz_url': 'https://www.markaz.app/shop/product/blue-printed-cotton-lawn-2-piece-eid-set-medium/712539',
        'title': 'Blue Printed Cotton Lawn 2-Piece Eid Set Medium',
        'stock_status': 'in_stock',
        'shopify_handle': 'demo-blue-printed-cotton-lawn-2-piece-eid-set-medium-mz1119202481bybr',
        'shopify_product_id': '9000000000001',
        'last_checked_at': _now(),
        'created_at': _now(),
    },
    {
        'id': 'demo-tracked-2',
        'markaz_url': 'https://www.markaz.app/shop/product/long-printed-2pc-doria-lawn-suit-blue-white/',
        'title': 'Long Printed 2PC Doria Lawn Suit Blue White',
        'stock_status': 'in_stock',
        'shopify_handle': 'demo-long-printed-2pc-doria-lawn-suit-blue-white-mz71400000532cncn',
        'shopify_product_id': '9000000000002',
        'last_checked_at': _now(),
        'created_at': _now(),
    },
    {
        'id': 'demo-tracked-3',
        'markaz_url': 'https://www.markaz.app/shop/product/elegant-womens-stitched-raw-silk-shirt-and-trouser-set-2-pcs/',
        'title': "Elegant Women's Stitched Raw Silk Shirt And Trouser Set - 2 Pcs",
        'stock_status': 'out_of_stock',
        'shopify_handle': 'demo-elegant-womens-stitched-raw-silk-shirt-and-trouser-set-2-pcs-mz71400000304cncn',
        'shopify_product_id': '9000000000003',
        'last_checked_at': _now(),
        'created_at': _now(),
    },
]


def build_dummy_shopify_status_map(tracked_rows):
    status_map = {}
    for row in tracked_rows:
        row_key = row.get('markaz_url') or row.get('id')
        handle = row.get('shopify_handle')
        product_id = row.get('shopify_product_id')
        if not handle:
            status_map[row_key] = {'on_shopify': False, 'status': None}
            continue

        is_draft = row.get('stock_status') == 'out_of_stock'
        status_map[row_key] = {
            'on_shopify': True,
            'shopify_product_id': product_id,
            'shopify_handle': handle,
            'status': 'draft' if is_draft else 'active',
            'title': row.get('title'),
            'images_count': 8 if 'Blue Printed' in (row.get('title') or '') else 5,
            'variants_count': 1,
            'inventory_quantity': 0 if is_draft else 50,
            'updated_at': _now(),
            'published_at': None if is_draft else _now(),
            'admin_url': f'https://demo-store.myshopify.com/admin/products/{product_id}',
        }
    return status_map


def build_dummy_converter_product():
    price = 1899.0
    variant_adj, compare_adj = get_default_price_adjustments(price)
    return {
        'title': 'Simt - U3B Maroon Embroidered Lawn Suit for Women - 3 Pcs Set',
        'description': 'Demo product for reference.\n• Premium lawn fabric\n• 3-piece stitched set',
        'price': price,
        'image_urls': [
            'https://content.public.markaz.app/markazimagevideo/public/products/2587-10-733736-product-1.webp',
            'https://content.public.markaz.app/markazimagevideo/public/products/2587-10-733736-product-2.webp',
        ],
        'base_sku': 'MZ2587200012SASK',
        'variants': ['Default Title'],
        'option1_name': 'Title',
        'breadcrumb_items': ['Women', 'Lawn', '3 Piece'],
        'stock_status': 'in_stock',
        'url': 'https://www.markaz.app/shop/product/simt-u3b-maroon-embroidered-lawn-suit-for-women-3-pcs-set/',
        'status': 'success',
        'variant_price_adjustment': variant_adj,
        'compare_at_price_adjustment': compare_adj,
    }


DUMMY_CONVERTER_PRODUCTS = [build_dummy_converter_product()]
