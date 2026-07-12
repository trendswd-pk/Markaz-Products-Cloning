import re
from html import escape

from markaz_scraper import normalize_markaz_image_url
from pricing_rules import COMPARE_AT_EXTRA, get_default_price_adjustments
from shopify_config import is_shopify_configured
from shopify_sync import DEFAULT_IN_STOCK_QTY, ShopifyAPIError, get_shopify_client

VENDOR_NAME = 'Markaz'


def slugify(text):
    if not text:
        return ''
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def generate_shopify_handle(title, base_sku, fallback_index=0):
    title_slug = slugify(title) if title else ''
    if base_sku:
        base_sku_lower = base_sku.lower()
        handle = f'{title_slug}-{base_sku_lower}' if title_slug else base_sku_lower
    else:
        handle = title_slug if title_slug else f'product-{fallback_index}'

    handle = handle.lower()
    handle = re.sub(r'[^a-z0-9-]', '-', handle)
    handle = re.sub(r'-+', '-', handle)
    return handle.strip('-')


def convert_description_to_html(description):
    if not description:
        return ''

    lines = description.split('\n')
    html_parts = []
    in_list = False

    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            continue

        is_list_item = re.match(r'^[\u2022\u2023\u25E6\u2043\u2219\-\*•]\s+|^\d+[\.\)]\s+', line)
        if is_list_item:
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            list_text = re.sub(r'^[\u2022\u2023\u25E6\u2043\u2219\-\*•]\s+|^\d+[\.\)]\s+', '', line)
            html_parts.append(f'<li>{escape(list_text)}</li>')
        else:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<p>{escape(line)}</p>')

    if in_list:
        html_parts.append('</ul>')

    return ''.join(html_parts) if html_parts else f'<p>{escape(description)}</p>'


def _product_tags_and_type(product):
    breadcrumb_items = product.get('breadcrumb_items', []) or []
    cleaned = []
    for item in breadcrumb_items:
        item = item.strip()
        if item and re.search(r'[a-zA-Z]', item):
            cleaned.append(item)

    tags = ', '.join(cleaned) if cleaned else ''
    product_type = ''
    if cleaned:
        product_type = re.sub(r'[^a-zA-Z0-9\s-]', '', cleaned[-1]).strip()
    return tags, product_type


def normalize_product_image_urls(product):
    urls = []
    for url in product.get('image_urls') or []:
        normalized = normalize_markaz_image_url(url)
        if normalized and normalized not in urls:
            urls.append(normalized)
    return urls


def sync_product_images(client, product_id, image_urls, existing_images=None):
    existing_images = existing_images or []
    existing_bases = {
        (img.get('src') or '').split('?')[0].rstrip('/')
        for img in existing_images
    }
    added = 0
    position = len(existing_images)

    for url in image_urls:
        base = url.split('?')[0].rstrip('/')
        if base in existing_bases:
            continue
        position += 1
        client._request(
            'POST',
            f'products/{product_id}/images.json',
            json={'image': {'src': url, 'position': position}},
        )
        existing_bases.add(base)
        added += 1

    return added


def _pricing_for_product(product):
    original_price = float(product.get('price', 0) or 0)
    variant_adjustment = float(product.get('variant_price_adjustment', 0) or 0)
    compare_adjustment = float(product.get('compare_at_price_adjustment', 0) or 0)

    if variant_adjustment == 0:
        variant_adjustment, _ = get_default_price_adjustments(original_price)
    if compare_adjustment == 0:
        compare_adjustment = variant_adjustment + COMPARE_AT_EXTRA

    return {
        'original_price': original_price,
        'variant_price': original_price + variant_adjustment,
        'compare_at_price': original_price + compare_adjustment,
    }


def build_shopify_product_payload(product, handle):
    variants = product.get('variants') or ['Default Title']
    option1_name = product.get('option1_name') or 'Title'
    has_real_variants = not (
        len(variants) == 1 and variants[0] == 'Default Title'
    )

    pricing = _pricing_for_product(product)
    base_sku = (product.get('base_sku') or '').strip()
    stock_status = product.get('stock_status', 'in_stock')
    inventory_qty = DEFAULT_IN_STOCK_QTY if stock_status == 'in_stock' else 0
    product_status = 'active' if stock_status != 'out_of_stock' else 'draft'

    shopify_variants = []
    for variant_value in variants:
        if variant_value and base_sku and variant_value != 'Default Title':
            variant_sku = f'{base_sku}-{variant_value}'
        else:
            variant_sku = base_sku

        shopify_variants.append({
            'option1': variant_value,
            'price': f'{pricing["variant_price"]:.2f}',
            'compare_at_price': f'{pricing["compare_at_price"]:.2f}',
            'sku': variant_sku,
            'inventory_management': 'shopify',
            'inventory_quantity': inventory_qty,
            'inventory_policy': 'continue',
            'fulfillment_service': 'manual',
            'requires_shipping': True,
            'taxable': True,
        })

    tags, product_type = _product_tags_and_type(product)
    image_urls = normalize_product_image_urls(product)
    images = [{'src': url} for url in image_urls]

    payload = {
        'title': product.get('title') or 'Untitled Product',
        'body_html': convert_description_to_html(product.get('description', '')),
        'vendor': VENDOR_NAME,
        'product_type': product_type,
        'tags': tags,
        'handle': handle,
        'status': product_status,
        'variants': shopify_variants,
        'images': images,
    }

    if has_real_variants:
        payload['options'] = [{'name': option1_name}]
    else:
        payload['options'] = [{'name': 'Title'}]

    return payload


def publish_product_to_shopify(product, client=None, fallback_index=0):
    client = client or get_shopify_client()
    handle = generate_shopify_handle(
        product.get('title', ''),
        product.get('base_sku', ''),
        fallback_index=fallback_index,
    )
    title = product.get('title') or handle
    image_urls = normalize_product_image_urls(product)

    try:
        existing = client.get_product_by_handle(handle)
        if existing:
            stock_status = product.get('stock_status', 'in_stock')
            product_status = 'active' if stock_status != 'out_of_stock' else 'draft'
            sync_result, stock_sync_warning = client.try_sync_stock_for_handle(handle, stock_status)
            client._request(
                'PUT',
                f'products/{existing["id"]}.json',
                json={
                    'product': {
                        'id': existing['id'],
                        'title': product.get('title') or existing.get('title'),
                        'body_html': convert_description_to_html(product.get('description', '')),
                        'vendor': VENDOR_NAME,
                        'tags': _product_tags_and_type(product)[0],
                        'product_type': _product_tags_and_type(product)[1],
                        'status': product_status,
                    }
                },
            )
            images_added = 0
            if image_urls:
                images_added = sync_product_images(
                    client,
                    existing['id'],
                    image_urls,
                    existing_images=existing.get('images', []),
                )
            refreshed = client.get_product_by_handle(handle) or existing
            message = 'Product updated; details refreshed and missing images added.'
            if sync_result:
                message = 'Product updated; details refreshed, stock synced, and missing images added.'
            elif stock_sync_warning:
                message = (
                    'Product updated and images synced, but inventory was not updated '
                    f'(needs `read_locations` scope): {stock_sync_warning}'
                )
            result = {
                'success': True,
                'action': 'updated',
                'title': title,
                'shopify_handle': handle,
                'shopify_product_id': str(existing['id']),
                'markaz_url': product.get('url'),
                'stock_status': stock_status,
                'images_count': len(refreshed.get('images', [])),
                'images_added': images_added,
                'message': message,
            }
            if stock_sync_warning:
                result['stock_sync_warning'] = stock_sync_warning
            if sync_result:
                result.update({k: v for k, v in sync_result.items() if k != 'success'})
            return result

        payload = build_shopify_product_payload(product, handle)
        data = client._request('POST', 'products.json', json={'product': payload})
        created = data.get('product', {})
        images_count = len(created.get('images', []))
        images_added = 0

        if image_urls and images_count < len(image_urls):
            images_added = sync_product_images(
                client,
                created['id'],
                image_urls,
                existing_images=created.get('images', []),
            )
            refreshed = client.get_product_by_handle(handle) or created
            images_count = len(refreshed.get('images', []))

        return {
            'success': True,
            'action': 'created',
            'title': title,
            'shopify_handle': created.get('handle', handle),
            'shopify_product_id': str(created.get('id', '')),
            'markaz_url': product.get('url'),
            'stock_status': product.get('stock_status', 'in_stock'),
            'variants_count': len(created.get('variants', [])),
            'images_count': images_count,
            'images_added': images_added,
            'product_status': payload.get('status'),
        }
    except ShopifyAPIError as exc:
        return {
            'success': False,
            'title': title,
            'shopify_handle': handle,
            'markaz_url': product.get('url'),
            'error': str(exc),
        }
    except Exception as exc:
        return {
            'success': False,
            'title': title,
            'shopify_handle': handle,
            'markaz_url': product.get('url'),
            'error': str(exc),
        }


def publish_products_to_shopify(products):
    if not is_shopify_configured():
        raise RuntimeError('Shopify is not configured.')

    client = get_shopify_client()
    results = []
    for index, product in enumerate(products):
        results.append(
            publish_product_to_shopify(product, client=client, fallback_index=index)
        )
    return results
