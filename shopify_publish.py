import os
import re
from html import escape

from requests.exceptions import RequestException, Timeout

from markaz_scraper import normalize_markaz_image_url
from pricing_rules import COMPARE_AT_EXTRA, get_default_price_adjustments
from shopify_config import is_shopify_configured
from shopify_sync import DEFAULT_IN_STOCK_QTY, ShopifyAPIError, get_shopify_client

VENDOR_NAME = 'at One Spot'


def _block_demo_shopify_api(action='publish to Shopify'):
    if os.environ.get('MARKAZ_DEMO_MODE') != '1':
        return
    from demo_mode.demo_guard import block_real_shopify_api

    block_real_shopify_api(action)


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
    skipped = 0
    errors = []
    position = len(existing_images)

    for url in image_urls:
        base = url.split('?')[0].rstrip('/')
        if base in existing_bases:
            continue
        position += 1
        try:
            client._request(
                'POST',
                f'products/{product_id}/images.json',
                json={'image': {'src': url, 'position': position}},
                timeout=(15, 90),
            )
            existing_bases.add(base)
            added += 1
        except Exception as exc:
            skipped += 1
            errors.append(str(exc)[:160])
            # Keep going — remaining images may still succeed.
            continue

    return {
        'added': added,
        'skipped': skipped,
        'errors': errors,
    }


def _sorted_product_images(images):
    return sorted(
        images or [],
        key=lambda img: (
            int(img.get('position') or 9999),
            int(img.get('id') or 0),
        ),
    )


def assign_variant_images(client, shopify_product, force=False):
    """Attach product images to variants so Shopify Admin shows a Variant image.

    Strategy:
    - Always assign the primary (position 1) image to every variant that has no image.
    - If option looks like Color/Colour and image count >= variant count, also map
      image[i] → variant[i] (common for color swatches).
    - Uses image `variant_ids` bulk update when possible (fewer API calls).
    """
    if not shopify_product or not shopify_product.get('id'):
        return {'assigned': 0, 'errors': ['Missing Shopify product']}

    product_id = shopify_product['id']
    images = _sorted_product_images(shopify_product.get('images'))
    variants = shopify_product.get('variants') or []
    if not images or not variants:
        return {'assigned': 0, 'errors': []}

    options = shopify_product.get('options') or []
    option1_name = ''
    if options:
        option1_name = (options[0].get('name') or '').strip().lower()
    is_color_option = option1_name in {'color', 'colour', 'colors', 'colours'}

    primary_image = images[0]
    primary_id = primary_image.get('id')
    if not primary_id:
        return {'assigned': 0, 'errors': ['Primary image has no id']}

    # Decide image_id per variant.
    assignments = {}  # image_id -> [variant_id, ...]
    for index, variant in enumerate(variants):
        variant_id = variant.get('id')
        if not variant_id:
            continue
        if variant.get('image_id') and not force:
            continue

        if is_color_option and index < len(images) and images[index].get('id'):
            image_id = images[index]['id']
        else:
            image_id = primary_id

        assignments.setdefault(image_id, []).append(variant_id)

    if not assignments:
        return {'assigned': 0, 'errors': [], 'skipped_already_set': True}

    assigned = 0
    errors = []

    # Prefer attaching via image.variant_ids (1 call per image).
    for image_id, variant_ids in assignments.items():
        # Merge with any existing variant_ids already on that image.
        existing_on_image = []
        for img in images:
            if img.get('id') == image_id:
                existing_on_image = list(img.get('variant_ids') or [])
                break
        merged_ids = list(dict.fromkeys([*existing_on_image, *variant_ids]))
        try:
            client._request(
                'PUT',
                f'products/{product_id}/images/{image_id}.json',
                json={
                    'image': {
                        'id': image_id,
                        'variant_ids': merged_ids,
                    }
                },
            )
            assigned += len(variant_ids)
            continue
        except Exception as bulk_exc:
            # Fallback: set image_id on each variant.
            fallback_ok = False
            for variant_id in variant_ids:
                try:
                    client._request(
                        'PUT',
                        f'variants/{variant_id}.json',
                        json={
                            'variant': {
                                'id': variant_id,
                                'image_id': image_id,
                            }
                        },
                    )
                    assigned += 1
                    fallback_ok = True
                except Exception as variant_exc:
                    errors.append(f'variant {variant_id}: {variant_exc}'[:160])
            if not fallback_ok:
                errors.append(str(bulk_exc)[:160])

    return {
        'assigned': assigned,
        'errors': errors,
        'primary_image_id': primary_id,
        'color_mapped': is_color_option and len(images) >= len(variants),
    }


def ensure_images_and_variant_images(client, shopify_product, image_urls):
    """Upload missing product images, then assign images onto variants."""
    if not shopify_product or not shopify_product.get('id'):
        return shopify_product, {
            'added': 0,
            'skipped': 0,
            'errors': [],
            'variants_assigned': 0,
            'variant_errors': [],
        }

    product_id = shopify_product['id']
    image_sync = {'added': 0, 'skipped': 0, 'errors': []}
    if image_urls:
        image_sync = sync_product_images(
            client,
            product_id,
            image_urls,
            existing_images=shopify_product.get('images', []),
        )

    # Refresh so new image IDs + variant IDs are available.
    handle = shopify_product.get('handle')
    refreshed = None
    if handle:
        refreshed = client.get_product_by_handle(handle)
    if not refreshed:
        try:
            data = client._request('GET', f'products/{product_id}.json')
            refreshed = data.get('product') or shopify_product
        except Exception:
            refreshed = shopify_product

    variant_sync = assign_variant_images(client, refreshed, force=True)
    image_sync['variants_assigned'] = variant_sync.get('assigned', 0)
    image_sync['variant_errors'] = variant_sync.get('errors') or []

    # One more refresh after assignment (optional but keeps counts accurate).
    if handle:
        refreshed = client.get_product_by_handle(handle) or refreshed

    return refreshed, image_sync


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


def build_shopify_product_payload(product, handle, include_images=False):
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

    payload = {
        'title': product.get('title') or 'Untitled Product',
        'body_html': convert_description_to_html(product.get('description', '')),
        'vendor': VENDOR_NAME,
        'product_type': product_type,
        'tags': tags,
        'handle': handle,
        'status': product_status,
        'variants': shopify_variants,
    }

    # Prefer attaching images after create — Shopify fetching many remote images
    # inline can exceed read timeouts even though the product was saved.
    if include_images and image_urls:
        payload['images'] = [{'src': url} for url in image_urls]

    if has_real_variants:
        payload['options'] = [{'name': option1_name}]
    else:
        payload['options'] = [{'name': 'Title'}]

    return payload


def _recover_published_product(client, handle, title, product, exc, action_hint='created'):
    """If Shopify saved the product but the HTTP response timed out, recover success."""
    try:
        existing = client.get_product_by_handle(handle)
    except Exception:
        existing = None

    if not existing:
        return None

    image_urls = normalize_product_image_urls(product)
    images_added = 0
    image_sync = {'added': 0, 'skipped': 0, 'errors': [], 'variants_assigned': 0, 'variant_errors': []}
    try:
        if image_urls or (existing.get('images') and existing.get('variants')):
            existing, image_sync = ensure_images_and_variant_images(
                client, existing, image_urls,
            )
            images_added = image_sync.get('added', 0) if isinstance(image_sync, dict) else image_sync
    except Exception:
        pass

    message = (
        f'Product {action_hint} on Shopify (request timed out waiting for response, '
        f'but the product exists). Original error: {exc}'
    )
    variants_assigned = image_sync.get('variants_assigned', 0) if isinstance(image_sync, dict) else 0
    if variants_assigned:
        message += f' Variant images assigned: {variants_assigned}.'
    return {
        'success': True,
        'action': action_hint,
        'title': title,
        'shopify_handle': existing.get('handle', handle),
        'shopify_product_id': str(existing.get('id', '')),
        'markaz_url': product.get('url'),
        'stock_status': product.get('stock_status', 'in_stock'),
        'variants_count': len(existing.get('variants', [])),
        'images_count': len(existing.get('images', [])),
        'images_added': images_added,
        'variants_images_assigned': variants_assigned,
        'product_status': existing.get('status'),
        'message': message,
        'timeout_recovered': True,
        'image_sync_errors': image_sync.get('errors') if isinstance(image_sync, dict) else [],
    }


def publish_product_to_shopify(product, client=None, fallback_index=0):
    _block_demo_shopify_api('publish products to Shopify')
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
            image_errors = []
            variants_assigned = 0
            if image_urls or existing.get('images'):
                refreshed, image_sync = ensure_images_and_variant_images(
                    client, existing, image_urls,
                )
                images_added = image_sync.get('added', 0)
                image_errors = (image_sync.get('errors') or []) + (
                    image_sync.get('variant_errors') or []
                )
                variants_assigned = image_sync.get('variants_assigned', 0)
            else:
                refreshed = existing
            message = 'Product updated; details refreshed and missing images added.'
            if sync_result:
                message = 'Product updated; details refreshed, stock synced, and missing images added.'
            elif stock_sync_warning:
                message = (
                    'Product updated and images synced, but inventory was not updated '
                    f'(needs `read_locations` scope): {stock_sync_warning}'
                )
            if variants_assigned:
                message += f' Variant images set: {variants_assigned}.'
            if image_errors:
                message += f' Some images failed ({len(image_errors)}).'
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
                'variants_images_assigned': variants_assigned,
                'message': message,
            }
            if stock_sync_warning:
                result['stock_sync_warning'] = stock_sync_warning
            if sync_result:
                result.update({k: v for k, v in sync_result.items() if k != 'success'})
            return result

        # Create without embedded images first (fast response), then attach images
        # and assign them onto variants.
        payload = build_shopify_product_payload(product, handle, include_images=False)
        try:
            data = client._request(
                'POST',
                'products.json',
                json={'product': payload},
                timeout=(15, 120),
            )
        except (Timeout, RequestException) as exc:
            recovered = _recover_published_product(
                client, handle, title, product, exc, action_hint='created',
            )
            if recovered:
                return recovered
            raise

        created = data.get('product', {})
        product_id = created.get('id')
        images_count = len(created.get('images', []))
        images_added = 0
        image_errors = []
        variants_assigned = 0

        if product_id and (image_urls or created.get('variants')):
            refreshed, image_sync = ensure_images_and_variant_images(
                client, created, image_urls,
            )
            images_added = image_sync.get('added', 0)
            image_errors = (image_sync.get('errors') or []) + (
                image_sync.get('variant_errors') or []
            )
            variants_assigned = image_sync.get('variants_assigned', 0)
            images_count = len(refreshed.get('images', []))
            created = refreshed or created

        result = {
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
            'variants_images_assigned': variants_assigned,
            'product_status': payload.get('status'),
        }
        notes = []
        if variants_assigned:
            notes.append(f'Variant images set: {variants_assigned}.')
        if image_errors:
            notes.append(f'{len(image_errors)} image(s) failed to upload/assign.')
            result['image_sync_errors'] = image_errors
        if notes:
            result['message'] = 'Product created. ' + ' '.join(notes)
        return result
    except ShopifyAPIError as exc:
        recovered = _recover_published_product(
            client, handle, title, product, exc, action_hint='created',
        )
        if recovered:
            return recovered
        return {
            'success': False,
            'title': title,
            'shopify_handle': handle,
            'markaz_url': product.get('url'),
            'error': str(exc),
        }
    except Exception as exc:
        recovered = _recover_published_product(
            client, handle, title, product, exc, action_hint='created',
        )
        if recovered:
            return recovered
        return {
            'success': False,
            'title': title,
            'shopify_handle': handle,
            'markaz_url': product.get('url'),
            'error': str(exc),
        }


def publish_products_to_shopify(products):
    _block_demo_shopify_api('publish products to Shopify')
    if not is_shopify_configured():
        raise RuntimeError('Shopify is not configured.')

    client = get_shopify_client()
    results = []
    for index, product in enumerate(products):
        results.append(
            publish_product_to_shopify(product, client=client, fallback_index=index)
        )
    return results
