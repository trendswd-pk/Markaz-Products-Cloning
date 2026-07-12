from demo_mode.demo_guard import DEMO_SHOPIFY_ALERT, demo_shopify_handle
from demo_mode.demo_store import update_tracked_shopify_metadata
from demo_mode.dummy_data import build_dummy_shopify_status_map
from shopify_publish import generate_shopify_handle


class DemoShopifyClient:
    def test_connection(self):
        return {
            'name': 'Demo Store',
            'domain': 'demo-store.myshopify.com',
            'email': 'demo@example.com',
        }


def get_shopify_client():
    return DemoShopifyClient()


def fetch_shopify_status_map(tracked_rows):
    return build_dummy_shopify_status_map(tracked_rows)


def sync_tracked_rows_to_shopify(tracked_rows):
    results = []
    for row in tracked_rows:
        handle = (row.get('shopify_handle') or '').strip()
        title = row.get('title') or handle or row.get('markaz_url', '')
        stock_status = row.get('stock_status', 'unknown')

        if not handle:
            results.append({
                'success': False,
                'title': title,
                'markaz_url': row.get('markaz_url'),
                'shopify_handle': handle,
                'error': 'No Shopify handle saved for this demo product.',
            })
            continue

        if stock_status == 'unknown':
            results.append({
                'success': False,
                'title': title,
                'markaz_url': row.get('markaz_url'),
                'shopify_handle': handle,
                'error': 'Markaz stock status is unknown',
            })
            continue

        inventory_qty = 50 if stock_status == 'in_stock' else 0
        product_status = 'active' if stock_status == 'in_stock' else 'draft'
        product_id = row.get('shopify_product_id') or f'9{abs(hash(handle)) % 10_000_000_000}'

        update_tracked_shopify_metadata(
            row.get('markaz_url'),
            shopify_product_id=product_id,
            shopify_handle=handle,
        )

        results.append({
            'success': True,
            'title': title,
            'markaz_url': row.get('markaz_url'),
            'shopify_handle': handle,
            'shopify_product_id': str(product_id),
            'stock_status': stock_status,
            'inventory_qty': inventory_qty,
            'product_status': product_status,
            'variants_updated': 1,
            'message': 'Demo stock sync simulated (no real Shopify API call).',
            'demo_simulated': True,
        })
    return results


def delete_tracked_row_from_shopify(row):
    handle = (row.get('shopify_handle') or '').strip()
    title = row.get('title') or handle or row.get('markaz_url', '')
    if not handle and not row.get('shopify_product_id'):
        return {
            'success': True,
            'skipped': True,
            'title': title,
            'message': 'No Shopify product linked.',
        }

    return {
        'success': True,
        'title': title,
        'shopify_handle': handle,
        'shopify_product_id': row.get('shopify_product_id'),
        'message': 'Demo delete simulated (no real Shopify API call).',
    }


def publish_product_to_shopify(product, client=None, fallback_index=0):
    handle = demo_shopify_handle(
        generate_shopify_handle(
            product.get('title', ''),
            product.get('base_sku', ''),
            fallback_index=fallback_index,
        )
    )
    title = product.get('title') or handle
    product_id = f'9{abs(hash(handle)) % 10_000_000_000}'
    markaz_url = product.get('url')
    image_urls = product.get('image_urls') or []

    if markaz_url:
        update_tracked_shopify_metadata(
            markaz_url,
            shopify_product_id=product_id,
            shopify_handle=handle,
        )

    return {
        'success': True,
        'action': 'updated' if fallback_index % 2 else 'created',
        'title': title,
        'shopify_handle': handle,
        'shopify_product_id': product_id,
        'markaz_url': markaz_url,
        'stock_status': product.get('stock_status', 'in_stock'),
        'images_count': len(image_urls),
        'images_added': max(len(image_urls) - 1, 0),
        'demo_simulated': True,
        'message': DEMO_SHOPIFY_ALERT,
    }


def publish_products_to_shopify(products):
    results = []
    for index, product in enumerate(products):
        results.append(
            publish_product_to_shopify(product, fallback_index=index)
        )
    return results
