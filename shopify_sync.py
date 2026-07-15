import os

import requests

from shopify_auth import get_shopify_access_token
from shopify_config import DEFAULT_API_VERSION, get_shopify_credentials, is_shopify_configured

DEFAULT_IN_STOCK_QTY = 50
# Product create/update with images often exceeds 30s while Shopify fetches remote URLs.
DEFAULT_REQUEST_TIMEOUT = (15, 120)


def _block_demo_shopify_api(action='access Shopify'):
    if os.environ.get('MARKAZ_DEMO_MODE') != '1':
        return
    from demo_mode.demo_guard import block_real_shopify_api

    block_real_shopify_api(action)


class ShopifyAPIError(Exception):
    pass


class ShopifyClient:
    def __init__(self, store_url, access_token, api_version=DEFAULT_API_VERSION):
        self.store_url = (
            store_url.replace('https://', '')
            .replace('http://', '')
            .strip()
            .strip('/')
        )
        self.access_token = access_token.strip()
        self.api_version = api_version or DEFAULT_API_VERSION
        self.base_url = f'https://{self.store_url}/admin/api/{self.api_version}'
        self.session = requests.Session()
        self.session.headers.update({
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json',
        })
        self._location_id = None

    def _request(self, method, path, timeout=None, **kwargs):
        _block_demo_shopify_api(f'call Shopify API ({method} {path})')
        response = self.session.request(
            method,
            f'{self.base_url}/{path}',
            timeout=timeout if timeout is not None else DEFAULT_REQUEST_TIMEOUT,
            **kwargs,
        )
        if not response.ok:
            raise ShopifyAPIError(
                f'Shopify API {response.status_code}: {response.text[:300]}'
            )
        if response.text:
            return response.json()
        return {}

    def test_connection(self):
        data = self._request('GET', 'shop.json')
        shop = data.get('shop', {})
        return {
            'name': shop.get('name'),
            'domain': shop.get('domain'),
            'email': shop.get('email'),
        }

    def get_primary_location_id(self):
        if self._location_id:
            return self._location_id

        data = self._request('GET', 'locations.json')
        locations = data.get('locations', [])
        active_locations = [location for location in locations if location.get('active')]
        if not active_locations:
            raise ShopifyAPIError('No active Shopify location found for inventory sync.')

        self._location_id = active_locations[0]['id']
        return self._location_id

    def get_product_by_handle(self, handle):
        data = self._request('GET', 'products.json', params={'handle': handle})
        products = data.get('products', [])
        return products[0] if products else None

    def delete_product_by_id(self, product_id):
        self._request('DELETE', f'products/{product_id}.json')

    def delete_product_by_handle(self, handle):
        product = self.get_product_by_handle(handle)
        if not product:
            return None
        self.delete_product_by_id(product['id'])
        return product

    def set_inventory_for_product(self, product, available_qty):
        location_id = self.get_primary_location_id()
        updated_variants = 0

        for variant in product.get('variants', []):
            inventory_item_id = variant.get('inventory_item_id')
            if not inventory_item_id:
                continue
            self._request(
                'POST',
                'inventory_levels/set.json',
                json={
                    'location_id': location_id,
                    'inventory_item_id': inventory_item_id,
                    'available': available_qty,
                },
            )
            updated_variants += 1

        return updated_variants

    def set_product_status(self, product_id, status):
        self._request(
            'PUT',
            f'products/{product_id}.json',
            json={'product': {'id': product_id, 'status': status}},
        )

    def sync_stock_for_handle(self, handle, stock_status):
        if not handle:
            return {'success': False, 'error': 'Missing Shopify handle'}

        if stock_status == 'unknown':
            return {'success': False, 'error': 'Markaz stock status is unknown'}

        product = self.get_product_by_handle(handle)
        if not product:
            return {'success': False, 'error': f'Shopify product not found for handle: {handle}'}

        if stock_status == 'in_stock':
            available_qty = DEFAULT_IN_STOCK_QTY
            product_status = 'active'
        else:
            available_qty = 0
            product_status = 'draft'

        variants_updated = self.set_inventory_for_product(product, available_qty)
        self.set_product_status(product['id'], product_status)

        return {
            'success': True,
            'shopify_product_id': str(product['id']),
            'shopify_handle': handle,
            'stock_status': stock_status,
            'inventory_qty': available_qty,
            'product_status': product_status,
            'variants_updated': variants_updated,
        }

    def try_sync_stock_for_handle(self, handle, stock_status):
        """Sync stock when scopes allow; return warning instead of raising."""
        try:
            result = self.sync_stock_for_handle(handle, stock_status)
            if result.get('success'):
                return result, None
            return None, result.get('error', 'Stock sync failed')
        except ShopifyAPIError as exc:
            return None, str(exc)
        except Exception as exc:
            return None, str(exc)

    def get_product_status_snapshot(self, handle=None, product_id=None):
        product = None
        if product_id:
            try:
                data = self._request('GET', f'products/{product_id}.json')
                product = data.get('product')
            except ShopifyAPIError:
                product = None

        if not product and handle:
            product = self.get_product_by_handle(handle)

        if not product:
            return {
                'on_shopify': False,
                'status': None,
                'error': 'Not found on Shopify',
            }

        variants = product.get('variants', [])
        total_inventory = sum(int(variant.get('inventory_quantity') or 0) for variant in variants)

        return {
            'on_shopify': True,
            'shopify_product_id': str(product.get('id', '')),
            'shopify_handle': product.get('handle'),
            'status': product.get('status'),
            'title': product.get('title'),
            'images_count': len(product.get('images', [])),
            'variants_count': len(variants),
            'inventory_quantity': total_inventory,
            'updated_at': product.get('updated_at'),
            'published_at': product.get('published_at'),
        }


def get_shopify_client():
    _block_demo_shopify_api('connect to Shopify')
    if not is_shopify_configured():
        raise RuntimeError(
            'Shopify is not configured. Add client_id + client_secret in .streamlit/secrets.toml '
            'under [shopify].'
        )

    creds = get_shopify_credentials()
    access_token = get_shopify_access_token()
    return ShopifyClient(
        store_url=creds['store_url'],
        access_token=access_token,
        api_version=creds.get('api_version', DEFAULT_API_VERSION),
    )


def sync_tracked_rows_to_shopify(tracked_rows):
    client = get_shopify_client()
    results = []

    for row in tracked_rows:
        handle = (row.get('shopify_handle') or '').strip()
        stock_status = row.get('stock_status', 'unknown')
        title = row.get('title') or handle or row.get('markaz_url', '')

        try:
            result = client.sync_stock_for_handle(handle, stock_status)
            result['title'] = title
            result['markaz_url'] = row.get('markaz_url')
        except Exception as exc:
            result = {
                'success': False,
                'title': title,
                'markaz_url': row.get('markaz_url'),
                'shopify_handle': handle,
                'error': str(exc),
            }
        results.append(result)

    return results


def get_shopify_admin_product_url(product_id):
    creds = get_shopify_credentials()
    store_url = (creds.get('store_url') or '').strip().rstrip('/')
    if not store_url or not product_id:
        return ''
    if not store_url.startswith('http'):
        store_url = f'https://{store_url}'
    return f'{store_url}/admin/products/{product_id}'


def fetch_shopify_status_map(tracked_rows):
    if not is_shopify_configured():
        return {}

    client = get_shopify_client()
    status_map = {}

    for row in tracked_rows:
        row_key = row.get('markaz_url') or row.get('id')
        handle = (row.get('shopify_handle') or '').strip()
        product_id = (row.get('shopify_product_id') or '').strip()

        if not handle and not product_id:
            status_map[row_key] = {'on_shopify': False, 'status': None}
            continue

        try:
            snapshot = client.get_product_status_snapshot(
                handle=handle or None,
                product_id=product_id or None,
            )
            if snapshot.get('on_shopify'):
                snapshot['admin_url'] = get_shopify_admin_product_url(snapshot.get('shopify_product_id'))
            status_map[row_key] = snapshot
        except Exception as exc:
            status_map[row_key] = {
                'on_shopify': False,
                'status': None,
                'error': str(exc),
            }

    return status_map


def delete_tracked_row_from_shopify(row):
    if not is_shopify_configured():
        return {'success': False, 'skipped': True, 'error': 'Shopify is not configured'}

    handle = (row.get('shopify_handle') or '').strip()
    product_id = (row.get('shopify_product_id') or '').strip()
    title = row.get('title') or handle or row.get('markaz_url', '')

    if not handle and not product_id:
        return {
            'success': True,
            'skipped': True,
            'title': title,
            'message': 'No Shopify product linked.',
        }

    client = get_shopify_client()

    try:
        if product_id:
            try:
                client.delete_product_by_id(product_id)
            except ShopifyAPIError:
                if handle:
                    deleted = client.delete_product_by_handle(handle)
                    if not deleted:
                        return {
                            'success': True,
                            'not_found': True,
                            'title': title,
                            'message': 'Product was not found on Shopify.',
                        }
                else:
                    raise
        elif handle:
            deleted = client.delete_product_by_handle(handle)
            if not deleted:
                return {
                    'success': True,
                    'not_found': True,
                    'title': title,
                    'message': 'Product was not found on Shopify.',
                }

        return {
            'success': True,
            'title': title,
            'shopify_product_id': product_id,
            'shopify_handle': handle,
        }
    except ShopifyAPIError as exc:
        return {
            'success': False,
            'title': title,
            'shopify_handle': handle,
            'error': str(exc),
        }
    except Exception as exc:
        return {
            'success': False,
            'title': title,
            'shopify_handle': handle,
            'error': str(exc),
        }
