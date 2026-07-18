import os
import threading
import time

import requests

from shopify_auth import get_shopify_access_token
from shopify_config import DEFAULT_API_VERSION, get_shopify_credentials, is_shopify_configured

DEFAULT_IN_STOCK_QTY = 50
# Product create/update with images often exceeds 30s while Shopify fetches remote URLs.
DEFAULT_REQUEST_TIMEOUT = (15, 120)
# Shopify Admin API bucket: ~2 calls/second for many apps.
SHOPIFY_MIN_REQUEST_INTERVAL = 0.55
SHOPIFY_MAX_RETRIES = 5
SHOPIFY_IDS_CHUNK_SIZE = 50
# Include draft/archived — default list filters can hide unpublished products.
SHOPIFY_PRODUCT_LIST_PARAMS = {
    'status': 'active,draft,archived',
    'published_status': 'any',
}

_RATE_LOCK = threading.Lock()
_LAST_REQUEST_AT = 0.0


def _block_demo_shopify_api(action='access Shopify'):
    if os.environ.get('MARKAZ_DEMO_MODE') != '1':
        return
    from demo_mode.demo_guard import block_real_shopify_api

    block_real_shopify_api(action)


def _throttle_shopify_request():
    """Keep request rate under Shopify's ~2 calls/second limit."""
    global _LAST_REQUEST_AT
    with _RATE_LOCK:
        now = time.monotonic()
        wait = SHOPIFY_MIN_REQUEST_INTERVAL - (now - _LAST_REQUEST_AT)
        if wait > 0:
            time.sleep(wait)
        _LAST_REQUEST_AT = time.monotonic()


class ShopifyAPIError(Exception):
    def __init__(self, message, status_code=None, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after

    @property
    def is_rate_limited(self):
        return self.status_code == 429


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
        last_error = None

        for attempt in range(SHOPIFY_MAX_RETRIES):
            _throttle_shopify_request()
            response = self.session.request(
                method,
                f'{self.base_url}/{path}',
                timeout=timeout if timeout is not None else DEFAULT_REQUEST_TIMEOUT,
                **kwargs,
            )

            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                try:
                    sleep_s = float(retry_after) if retry_after else (1.0 * (attempt + 1))
                except ValueError:
                    sleep_s = 1.0 * (attempt + 1)
                sleep_s = max(sleep_s, 1.0)
                last_error = ShopifyAPIError(
                    f'Shopify API 429: {response.text[:300]}',
                    status_code=429,
                    retry_after=sleep_s,
                )
                time.sleep(sleep_s)
                continue

            if not response.ok:
                raise ShopifyAPIError(
                    f'Shopify API {response.status_code}: {response.text[:300]}',
                    status_code=response.status_code,
                )

            if response.text:
                return response.json()
            return {}

        raise last_error or ShopifyAPIError(
            'Shopify API rate limit exceeded after retries.',
            status_code=429,
        )

    def graphql(self, query, variables=None, timeout=None):
        """Run a GraphQL Admin API call (needed for Product Category taxonomy)."""
        _block_demo_shopify_api('call Shopify GraphQL API')
        last_error = None
        payload = {'query': query, 'variables': variables or {}}

        for attempt in range(SHOPIFY_MAX_RETRIES):
            _throttle_shopify_request()
            response = self.session.post(
                f'https://{self.store_url}/admin/api/{self.api_version}/graphql.json',
                json=payload,
                timeout=timeout if timeout is not None else DEFAULT_REQUEST_TIMEOUT,
            )

            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                try:
                    sleep_s = float(retry_after) if retry_after else (1.0 * (attempt + 1))
                except ValueError:
                    sleep_s = 1.0 * (attempt + 1)
                sleep_s = max(sleep_s, 1.0)
                last_error = ShopifyAPIError(
                    f'Shopify GraphQL 429: {response.text[:300]}',
                    status_code=429,
                    retry_after=sleep_s,
                )
                time.sleep(sleep_s)
                continue

            if not response.ok:
                raise ShopifyAPIError(
                    f'Shopify GraphQL {response.status_code}: {response.text[:300]}',
                    status_code=response.status_code,
                )

            data = response.json() if response.text else {}
            if data.get('errors'):
                messages = '; '.join(
                    err.get('message', str(err)) for err in data['errors']
                )
                raise ShopifyAPIError(f'Shopify GraphQL errors: {messages[:300]}')
            return data.get('data') or {}

        raise last_error or ShopifyAPIError(
            'Shopify GraphQL rate limit exceeded after retries.',
            status_code=429,
        )

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
        data = self._request(
            'GET',
            'products.json',
            params={
                'handle': handle,
                **SHOPIFY_PRODUCT_LIST_PARAMS,
            },
        )
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

    def snapshot_from_product(self, product):
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

    def get_products_by_ids(self, product_ids):
        """Fetch many products in few requests: GET products.json?ids=...

        Includes draft/archived. Any IDs missing from the list response are
        fetched individually via GET products/{id}.json (always returns drafts).
        """
        ids = []
        seen = set()
        for raw in product_ids or []:
            pid = str(raw or '').strip()
            if not pid or pid in seen:
                continue
            seen.add(pid)
            ids.append(pid)

        products_by_id = {}
        for start in range(0, len(ids), SHOPIFY_IDS_CHUNK_SIZE):
            chunk = ids[start:start + SHOPIFY_IDS_CHUNK_SIZE]
            data = self._request(
                'GET',
                'products.json',
                params={
                    'ids': ','.join(chunk),
                    'limit': len(chunk),
                    **SHOPIFY_PRODUCT_LIST_PARAMS,
                },
            )
            for product in data.get('products', []) or []:
                products_by_id[str(product.get('id'))] = product

        # List endpoints can still omit drafts in some API/app setups.
        missing_ids = [pid for pid in ids if pid not in products_by_id]
        for pid in missing_ids:
            try:
                data = self._request('GET', f'products/{pid}.json')
                product = data.get('product')
                if product and product.get('id') is not None:
                    products_by_id[str(product.get('id'))] = product
            except ShopifyAPIError as exc:
                if getattr(exc, 'is_rate_limited', False):
                    raise
                continue

        return products_by_id

    def get_product_status_snapshot(self, handle=None, product_id=None):
        product = None
        if product_id:
            try:
                data = self._request('GET', f'products/{product_id}.json')
                product = data.get('product')
            except ShopifyAPIError as exc:
                if getattr(exc, 'is_rate_limited', False):
                    raise
                # 404 / other — try handle fallback below
                product = None

        if not product and handle:
            try:
                product = self.get_product_by_handle(handle)
            except ShopifyAPIError as exc:
                if getattr(exc, 'is_rate_limited', False):
                    raise
                raise

        return self.snapshot_from_product(product)


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


def _linked_but_unchecked_snapshot(row, error=None):
    """When API fails (e.g. 429), do not pretend the product is missing."""
    handle = (row.get('shopify_handle') or '').strip()
    product_id = (row.get('shopify_product_id') or '').strip()
    return {
        'on_shopify': True,
        'status_unknown': True,
        'status': None,
        'shopify_handle': handle or None,
        'shopify_product_id': product_id or None,
        'admin_url': get_shopify_admin_product_url(product_id) if product_id else '',
        'error': error,
        'rate_limited': bool(error and '429' in str(error)),
    }


def fetch_shopify_status_map(tracked_rows, existing_map=None):
    """Build Shopify status map with bulk ID lookups + rate-limit-safe fallbacks.

    Prefer GET products.json?ids=... (few calls) over one request per product.
    On 429, keep previous successful snapshot when available instead of "Not on Shopify".
    """
    if not is_shopify_configured():
        return {}

    client = get_shopify_client()
    status_map = {}
    existing_map = existing_map or {}

    rows_with_ids = []
    rows_handle_only = []
    rows_unlinked = []

    for row in tracked_rows or []:
        row_key = row.get('markaz_url') or row.get('id')
        handle = (row.get('shopify_handle') or '').strip()
        product_id = (row.get('shopify_product_id') or '').strip()
        if product_id:
            rows_with_ids.append((row_key, row, product_id))
        elif handle:
            rows_handle_only.append((row_key, row, handle))
        else:
            rows_unlinked.append(row_key)

    for row_key in rows_unlinked:
        status_map[row_key] = {'on_shopify': False, 'status': None}

    # Bulk fetch by Shopify product IDs (1 API call per ~50 products).
    try:
        products_by_id = client.get_products_by_ids(
            [product_id for _, _, product_id in rows_with_ids]
        )
    except ShopifyAPIError as exc:
        products_by_id = {}
        for row_key, row, _product_id in rows_with_ids:
            previous = existing_map.get(row_key)
            if previous and previous.get('on_shopify') and not previous.get('status_unknown'):
                status_map[row_key] = previous
            else:
                status_map[row_key] = _linked_but_unchecked_snapshot(row, error=str(exc))
        rows_with_ids = []

    found_ids = set()
    for row_key, row, product_id in rows_with_ids:
        product = products_by_id.get(str(product_id))
        if product:
            snapshot = client.snapshot_from_product(product)
            snapshot['admin_url'] = get_shopify_admin_product_url(snapshot.get('shopify_product_id'))
            status_map[row_key] = snapshot
            found_ids.add(row_key)
        else:
            # ID saved but product missing from bulk — try direct ID + handle.
            handle = (row.get('shopify_handle') or '').strip()
            rows_handle_only.append((row_key, row, handle))

    # Handle-only rows (and ID misses): prefer product_id GET, then handle.
    for row_key, row, handle in rows_handle_only:
        if row_key in found_ids or row_key in status_map:
            continue
        product_id = (row.get('shopify_product_id') or '').strip() or None
        try:
            snapshot = client.get_product_status_snapshot(
                handle=handle or None,
                product_id=product_id,
            )
            if snapshot.get('on_shopify'):
                snapshot['admin_url'] = get_shopify_admin_product_url(
                    snapshot.get('shopify_product_id')
                )
            status_map[row_key] = snapshot
        except ShopifyAPIError as exc:
            previous = existing_map.get(row_key)
            if previous and previous.get('on_shopify') and not previous.get('status_unknown'):
                status_map[row_key] = previous
            elif row.get('shopify_product_id') or row.get('shopify_handle'):
                status_map[row_key] = _linked_but_unchecked_snapshot(row, error=str(exc))
            else:
                status_map[row_key] = {
                    'on_shopify': False,
                    'status': None,
                    'error': str(exc),
                }
        except Exception as exc:
            previous = existing_map.get(row_key)
            if previous and previous.get('on_shopify') and not previous.get('status_unknown'):
                status_map[row_key] = previous
            else:
                status_map[row_key] = _linked_but_unchecked_snapshot(row, error=str(exc))

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
