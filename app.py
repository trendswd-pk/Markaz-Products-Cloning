import streamlit as st
import pandas as pd
import re
import os
import copy
import time
from html import escape
from pathlib import Path

from auth import init_auth_session, is_authenticated, render_login_page, render_logout_control
from pricing_rules import get_default_price_adjustments
from shopify_config import is_shopify_configured
from shopify_sync import (
    delete_tracked_row_from_shopify,
    fetch_shopify_status_map,
    get_shopify_client,
    sync_tracked_rows_to_shopify,
)
from shopify_publish import publish_products_to_shopify
from markaz_scraper import canonicalize_markaz_product_url, extract_markaz_product_id
from supabase_config import is_supabase_configured
from supabase_store import (
    batch_upsert_tracked_products,
    count_duplicate_tracked_products,
    dedupe_tracked_products,
    delete_tracked_product,
    delete_tracked_products,
    list_tracked_products,
    update_tracked_shopify_metadata_batch,
    update_tracked_stock_status,
    upsert_tracked_product,
)

_IS_DEMO = os.environ.get('MARKAZ_DEMO_MODE') == '1'


def show_product_image(image_url, **kwargs):
    """Avoid st.image in demo mode (native image decode can segfault on some Linux setups)."""
    if _IS_DEMO:
        st.caption(f"Demo preview image: `{str(image_url)[:80]}`")
        return
    if image_url:
        st.image(image_url, **kwargs)


def render_shopify_tab_icon():
    if is_shopify_configured():
        st.markdown('<span style="font-size:1.4rem;" title="Shopify">🛍️</span>', unsafe_allow_html=True)


if _IS_DEMO:
    from demo_mode.demo_scrape import scrape_markaz_product_demo as scrape_markaz_product
    from demo_mode.demo_scrape import scrape_product_from_page_demo as scrape_product_from_page
    from demo_mode.demo_scrape import scrape_category_product_urls_demo as scrape_category_product_urls
else:
    from playwright.sync_api import sync_playwright
    from markaz_scraper import (
        launch_browser_for_serverless,
        scrape_category_product_urls,
        scrape_markaz_product,
        scrape_product_from_page,
    )

# Playwright Browser Installation: Install chromium browser if missing
# Skipped in demo mode (demo uses simulated scrape, no browser needed)
if not os.environ.get('MARKAZ_DEMO_MODE'):
    os.system('playwright install chromium')

# Page configuration (skipped in demo_mode/app.py — that entry sets config first)
if not os.environ.get('MARKAZ_DEMO_MODE'):
    st.set_page_config(
        page_title="Markaz to Shopify CSV Converter",
        page_icon="🛍️",
        layout="wide"
    )

# Initialize session state (products_list at very top for multiple fetch)
if 'products_list' not in st.session_state:
    st.session_state.products_list = []
if 'processed_urls' not in st.session_state:
    st.session_state.processed_urls = set()  # URLs we've already added (avoid duplicates)
if 'fetched_product_data' not in st.session_state:
    st.session_state.fetched_product_data = None
if 'show_product_dialog' not in st.session_state:
    st.session_state.show_product_dialog = False
if 'add_mode' not in st.session_state:
    st.session_state.add_mode = 'multiple'  # 'single' | 'multiple' | 'category'
if 'converter_import_message' not in st.session_state:
    st.session_state.converter_import_message = None
if 'shopify_publish_feedback' not in st.session_state:
    st.session_state.shopify_publish_feedback = None

init_auth_session()

def slugify(text):
    """Convert text to URL-friendly handle"""
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters, keep only alphanumeric, spaces, and hyphens
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    # Remove leading/trailing hyphens
    return text.strip('-')

def generate_unique_handle(title, base_sku, fallback_index=0):
    """Generate unique handle by combining slugified title with base SKU"""
    # Slugify the title
    title_slug = slugify(title) if title else ""
    
    # Append the Base SKU (Product Code) at the end, lowercase
    if base_sku:
        base_sku_lower = base_sku.lower()
        if title_slug:
            handle = f"{title_slug}-{base_sku_lower}"
        else:
            handle = base_sku_lower
    else:
        handle = title_slug if title_slug else f"product-{fallback_index}"
    
    # Ensure handle is lowercase with hyphens only (no spaces or capital letters)
    handle = handle.lower()
    handle = re.sub(r'[^a-z0-9-]', '-', handle)  # Replace any non-alphanumeric/hyphen with hyphen
    handle = re.sub(r'-+', '-', handle)  # Remove multiple consecutive hyphens
    handle = handle.strip('-')  # Remove leading/trailing hyphens
    
    return handle

def sanitize_and_format_tags(breadcrumb_items):
    """Sanitize and format breadcrumb items into Shopify-compatible tags"""
    if not breadcrumb_items:
        return ''
    
    cleaned_tags = []
    
    for item in breadcrumb_items:
        # Step 1: Sanitize - Remove special characters except spaces and hyphens
        # Keep only alphanumeric, spaces, and hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9\s-]', '', item)
        
        # Step 2: Split & Clean - Remove leading/trailing spaces
        sanitized = sanitized.strip()
        
        # Step 3: Skip empty items or items that are just symbols
        if not sanitized or sanitized.strip() == '':
            continue
        
        # Check if item is just symbols (after removing allowed chars, nothing left)
        if not re.search(r'[a-zA-Z0-9]', sanitized):
            continue
        
        # Step 4: Length Check - Ensure no tag is longer than 255 characters (Shopify's limit)
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        cleaned_tags.append(sanitized)
    
    # Step 3: Comma Separation - Join with comma and single space
    tags = ', '.join(cleaned_tags)
    
    return tags

def convert_description_to_html(description):
    """Convert description text to HTML with <p> and <li> tags"""
    if not description:
        return ""
    
    # Split by newlines
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
        
        # Check if line looks like a list item (starts with bullet, dash, or number)
        is_list_item = re.match(r'^[\u2022\u2023\u25E6\u2043\u2219\-\*•]\s+|^\d+[\.\)]\s+', line)
        
        if is_list_item:
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            # Remove bullet/dash/number prefix
            list_text = re.sub(r'^[\u2022\u2023\u25E6\u2043\u2219\-\*•]\s+|^\d+[\.\)]\s+', '', line)
            html_parts.append(f'<li>{escape(list_text)}</li>')
        else:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<p>{escape(line)}</p>')
    
    if in_list:
        html_parts.append('</ul>')
    
    return ''.join(html_parts) if html_parts else f"<p>{escape(description)}</p>"

def create_shopify_row(product, variant_value="", image_url="", image_position="", is_variant_row=False, is_first_variant=False):
    """Create a Shopify CSV row with all required columns in exact order"""
    # Handle must be the same for all rows of the same product
    # Generate unique handle: slugified title + base SKU
    handle = generate_unique_handle(
        product.get('title', ''),
        product.get('base_sku', ''),
        fallback_index=len(st.session_state.products_list),
    )
    
    # Title, Body (HTML), and Price should only be in the first variant row
    title = product['title'] or "Untitled Product" if is_first_variant else ""
    body_html = convert_description_to_html(product['description']) if is_first_variant else ""
    
    # Pricing Engine Logic - apply to all variant rows
    try:
        original_price = float(product['price'])
        # Store original price in Cost per item (only in first variant row)
        cost_per_item = f"{original_price:.2f}" if is_first_variant else ""
        
        # Get price adjustments from product data (user input values)
        variant_price_adjustment = float(product.get('variant_price_adjustment', 0))
        compare_at_price_adjustment = float(product.get('compare_at_price_adjustment', 0))
        
        # Calculate Variant Price: Original Price + User Input Adjustment
        variant_price = original_price + variant_price_adjustment
        
        variant_price_formatted = f"{variant_price:.2f}"
        
        # Calculate Compare At Price: Original Price + User Input Adjustment
        compare_at_price = original_price + compare_at_price_adjustment
        compare_at_price_formatted = f"{compare_at_price:.2f}"
    except:
        cost_per_item = "0.00" if is_first_variant else ""
        variant_price_formatted = "0.00"
        compare_at_price_formatted = "0.00"
    
    # Generate Variant SKU: Base SKU + "-" + variant value
    base_sku = product.get('base_sku', '')
    if variant_value and base_sku and variant_value != 'Default Title':
        variant_sku = f"{base_sku}-{variant_value}"
    else:
        variant_sku = base_sku if is_variant_row else ""
    
    # Set Option1 Name and Value
    option1_name = product.get('option1_name', 'Title') if is_variant_row else ''
    option1_value = variant_value if is_variant_row else ''
    
    # Extract breadcrumb data for Type and Tags
    breadcrumb_items = product.get('breadcrumb_items', [])
    product_type_value = ''
    tags = ''
    
    if breadcrumb_items:
        # Final cleaning: Trim spaces and ensure all items are valid
        cleaned_breadcrumb = []
        for item in breadcrumb_items:
            item = item.strip()
            if item and re.search(r'[a-zA-Z]', item):  # Must contain letters
                cleaned_breadcrumb.append(item)
        
        breadcrumb_items = cleaned_breadcrumb
        
        # Final Mapping:
        # Tags: Join all items with a comma and space: Marketplace, Beauty&Fashion, Cosmetics, Personal Care
        if breadcrumb_items:
            tags = ", ".join(breadcrumb_items)
        else:
            tags = ''
        
        # Type: last breadcrumb item (Shopify CSV column is "Type")
        if breadcrumb_items:
            product_type = breadcrumb_items[-1].strip()
            product_type_value = re.sub(r'[^a-zA-Z0-9\s-]', '', product_type).strip()
        else:
            product_type_value = ''
    
    # Variant Image = Image Src at Position 1 (all variants share primary gallery image)
    image_urls = product.get('image_urls') or []
    primary_image_url = ''
    if image_urls:
        try:
            from markaz_scraper import normalize_markaz_image_url
            primary_image_url = normalize_markaz_image_url(image_urls[0]) or image_urls[0]
        except Exception:
            primary_image_url = image_urls[0]
    
    # Create row with all columns in exact order
    row = {
        'Handle': handle,
        'Title': title,
        'Body (HTML)': body_html,
        'Vendor': 'at One Spot' if is_first_variant else '',
        'Product Category': 'Apparel & Accessories' if is_first_variant else '',
        'Type': product_type_value if is_first_variant else '',
        'Tags': tags if is_first_variant else '',
        'Published': 'TRUE' if is_first_variant else '',
        'Option1 Name': option1_name,
        'Option1 Value': option1_value,
        'Option2 Name': '',
        'Option2 Value': '',
        'Option3 Name': '',
        'Option3 Value': '',
        'Variant SKU': variant_sku,
        'Variant Grams': '750' if is_variant_row else '',
        'Variant Inventory Tracker': 'shopify' if is_variant_row else '',
        'Variant Inventory Qty': '50' if is_variant_row else '',
        'Variant Inventory Policy': 'continue' if is_variant_row else '',
        'Variant Fulfillment Service': 'manual' if is_variant_row else '',
        'Variant Price': variant_price_formatted if is_variant_row else '',
        'Variant Compare At Price': compare_at_price_formatted if is_variant_row else '',
        'Variant Requires Shipping': 'TRUE' if is_variant_row else '',
        'Variant Taxable': 'TRUE' if is_variant_row else '',
        'Variant Barcode': '',
        'Image Src': image_url,
        'Image Position': image_position if image_position else '',
        'Image Alt Text': title if is_first_variant and image_url else '',
        'Variant Image': primary_image_url if is_variant_row else '',
        'Gift Card': 'FALSE' if is_first_variant else '',
        'SEO Title': title if is_first_variant else '',
        'SEO Description': product['description'][:160] if is_first_variant and product.get('description') else '',
        'Google Shopping / Google Product Category': '',
        'Google Shopping / Gender': 'unisex' if is_first_variant else '',
        'Google Shopping / Age Group': 'adult' if is_first_variant else '',
        'Google Shopping / MPN': '',
        'Google Shopping / Condition': 'new' if is_first_variant else '',
        'Google Shopping / Custom Product': 'FALSE' if is_first_variant else '',
        'Google Shopping / Custom Label 0': '',
        'Google Shopping / Custom Label 1': '',
        'Google Shopping / Custom Label 2': '',
        'Google Shopping / Custom Label 3': '',
        'Google Shopping / Custom Label 4': '',
        'Age group (product.metafields.shopify.age-group)': 'all-ages; adults' if is_first_variant else '',
        'Target gender (product.metafields.shopify.target-gender)': 'female; male; unisex' if is_first_variant else '',
        'Variant Weight Unit': 'kg' if is_variant_row else '',
        'Variant Tax Code': '',
        'Cost per item': cost_per_item,
        'Price / International': '',
        'Compare At Price / International': '',
        'Status': 'active' if is_first_variant else ''
    }
    
    return row

def format_for_shopify(product):
    """Format product data for Shopify CSV format with all required columns"""
    rows = []
    image_urls = product['image_urls'] if product['image_urls'] else []
    variants = product.get('variants', ['Default Title'])
    
    # Check if we have real variants (not just default)
    has_real_variants = variants and len(variants) > 0 and not (len(variants) == 1 and variants[0] == 'Default Title')
    
    if has_real_variants:
        # Create a row for EACH variant found
        for variant_idx, variant_value in enumerate(variants):
            is_first_variant = (variant_idx == 0)
            
            # First variant gets the first image and all product details
            if is_first_variant and image_urls:
                rows.append(create_shopify_row(
                    product, 
                    variant_value, 
                    image_urls[0], 
                    "1", 
                    is_variant_row=True, 
                    is_first_variant=True
                ))
            else:
                # Other variants get empty image (or no image) but all variant details
                rows.append(create_shopify_row(
                    product, 
                    variant_value, 
                    "", 
                    "", 
                    is_variant_row=True, 
                    is_first_variant=False
                ))
        
        # Additional rows for remaining images (after all variants)
        # These are image-only rows with same Handle but no variant info
        if image_urls and len(image_urls) > 1:
            for img_idx, img_url in enumerate(image_urls[1:], start=2):
                rows.append(create_shopify_row(
                    product, 
                    "", 
                    img_url, 
                    str(img_idx), 
                    is_variant_row=False, 
                    is_first_variant=False
                ))
    else:
        # No variants found, create a default row
        if image_urls:
            rows.append(create_shopify_row(
                product, 
                'Default Title', 
                image_urls[0], 
                "1", 
                is_variant_row=True, 
                is_first_variant=True
            ))
            # Additional image rows
            for img_idx, img_url in enumerate(image_urls[1:], start=2):
                rows.append(create_shopify_row(
                    product, 
                    "", 
                    img_url, 
                    str(img_idx), 
                    is_variant_row=False, 
                    is_first_variant=False
                ))
        else:
            rows.append(create_shopify_row(
                product, 
                'Default Title', 
                "", 
                "", 
                is_variant_row=True, 
                is_first_variant=True
            ))
    
    return rows

def save_product_to_supabase(product_data):
    """Save Markaz URL, stock status, and Shopify handle to Supabase after a successful fetch."""
    if not is_supabase_configured():
        return False, 'Supabase keys not configured in .streamlit/secrets.toml'

    markaz_url = canonicalize_markaz_product_url(
        (product_data or {}).get('url', '').strip()
    )
    if not markaz_url:
        return False, 'Product URL missing'

    shopify_handle = generate_unique_handle(
        product_data.get('title', ''),
        product_data.get('base_sku', ''),
    )

    try:
        saved = upsert_tracked_product(
            markaz_url=markaz_url,
            stock_status=product_data.get('stock_status', 'unknown'),
            title=product_data.get('title'),
            shopify_handle=shopify_handle,
        )
        patch_tracked_row_in_cache(saved or {
            'markaz_url': markaz_url,
            'stock_status': product_data.get('stock_status', 'unknown'),
            'title': product_data.get('title'),
            'shopify_handle': shopify_handle,
        })
        return True, None
    except Exception as exc:
        return False, str(exc)


def update_tracked_product_from_scrape(markaz_url, scraped_data):
    """Update Supabase row after a live Markaz refresh."""
    shopify_handle = generate_unique_handle(
        scraped_data.get('title', ''),
        scraped_data.get('base_sku', ''),
    )
    result = update_tracked_stock_status(
        markaz_url,
        scraped_data.get('stock_status', 'unknown'),
        title=scraped_data.get('title'),
        shopify_handle=shopify_handle,
    )
    if result:
        patch_tracked_row_in_cache(result)
    return result


def apply_default_pricing_rules(product_data):
    fetched_price = float(product_data.get('price', 0))
    variant_adjustment, compare_at_adjustment = get_default_price_adjustments(fetched_price)
    product_data['variant_price_adjustment'] = variant_adjustment
    product_data['compare_at_price_adjustment'] = compare_at_adjustment
    return product_data


def get_filtered_tracked_rows(tracked_rows, stock_filter):
    filter_values = {
        'All': None,
        'In Stock': 'in_stock',
        'Out of Stock': 'out_of_stock',
        'Unknown': 'unknown',
    }
    selected_status = filter_values.get(stock_filter)
    if not selected_status:
        return tracked_rows
    return [
        row for row in tracked_rows
        if row.get('stock_status', 'unknown') == selected_status
    ]


def get_filtered_tracked_rows_by_shopify(tracked_rows, shopify_filter, shopify_status_map):
    """Filter tracked rows by Shopify presence/status (Active / Draft / Not on Shopify)."""
    if not shopify_filter or shopify_filter == 'All':
        return tracked_rows

    shopify_status_map = shopify_status_map or {}
    filtered = []
    for row in tracked_rows:
        row_key = row.get('markaz_url') or row.get('id')
        snapshot = shopify_status_map.get(row_key, {}) or {}
        on_shopify = bool(snapshot.get('on_shopify'))
        status = (snapshot.get('status') or '').lower()

        if shopify_filter == 'Not on Shopify':
            if not on_shopify:
                filtered.append(row)
        elif shopify_filter == 'Active':
            if on_shopify and status == 'active':
                filtered.append(row)
        elif shopify_filter == 'Draft':
            if on_shopify and status == 'draft':
                filtered.append(row)
        elif shopify_filter == 'Archived':
            if on_shopify and status == 'archived':
                filtered.append(row)

    return filtered


def format_stock_status_label(stock_status):
    labels = {
        'in_stock': 'In Stock',
        'out_of_stock': 'Out of Stock',
        'unknown': 'Unknown',
    }
    return labels.get(stock_status, stock_status or 'Unknown')


def format_shopify_status_label(snapshot):
    if not snapshot:
        return 'Not on Shopify'
    if snapshot.get('status_unknown') or snapshot.get('rate_limited'):
        return 'Shopify: Linked'
    if not snapshot.get('on_shopify'):
        return 'Not on Shopify'

    status = (snapshot.get('status') or 'unknown').lower()
    labels = {
        'active': 'Shopify: Active',
        'draft': 'Shopify: Draft',
        'archived': 'Shopify: Archived',
    }
    return labels.get(status, f'Shopify: {status.title()}')


def format_shopify_status_detail(snapshot):
    if not snapshot:
        return 'Not on Shopify'

    if snapshot.get('status_unknown') or snapshot.get('rate_limited'):
        handle = snapshot.get('shopify_handle') or '—'
        err = snapshot.get('error') or 'Live status not loaded yet'
        if snapshot.get('rate_limited') or '429' in str(err):
            return (
                f"**Linked** · handle `{handle}` · live status pending "
                f"(Shopify rate limit — click **Refresh Shopify Status** and wait)."
            )
        return f"**Linked** · handle `{handle}` · {err}"

    if not snapshot.get('on_shopify'):
        if snapshot.get('error'):
            return f"Not on Shopify ({snapshot['error']})"
        return 'Not on Shopify'

    status = (snapshot.get('status') or 'unknown').title()
    images_count = snapshot.get('images_count', 0)
    inventory_qty = snapshot.get('inventory_quantity', 0)
    updated_at = snapshot.get('updated_at') or '—'
    return (
        f"**{status}** · {images_count} image(s) · inventory {inventory_qty} · "
        f"updated {updated_at}"
    )


SHOPIFY_FIELD_GREEN = "#22c55e"


def render_shopify_green_field(label, value):
    display_value = str(value).replace('**', '')
    st.markdown(
        f'<p style="color:{SHOPIFY_FIELD_GREEN}; margin:0.35rem 0;">'
        f'<strong>{label}:</strong> {display_value}</p>',
        unsafe_allow_html=True,
    )


def invalidate_shopify_status_cache():
    st.session_state.pop('shopify_status_map', None)


def invalidate_tracked_rows_cache():
    st.session_state.pop('tracked_rows_cache', None)


def _increment_supabase_fetch_count():
    st.session_state['supabase_fetch_count'] = (
        st.session_state.get('supabase_fetch_count', 0) + 1
    )


def patch_tracked_row_in_cache(row):
    """Update session cache in-place — avoids a full Supabase list refetch."""
    if not row or not row.get('markaz_url'):
        return
    cache = st.session_state.get('tracked_rows_cache')
    if cache is None:
        return
    markaz_url = canonicalize_markaz_product_url(row['markaz_url']) or row['markaz_url']
    product_id = extract_markaz_product_id(markaz_url)
    row = {**row, 'markaz_url': markaz_url}

    for index, existing in enumerate(cache):
        existing_url = existing.get('markaz_url')
        same_url = canonicalize_markaz_product_url(existing_url) == markaz_url
        same_id = (
            product_id
            and extract_markaz_product_id(existing_url) == product_id
        )
        if same_url or same_id:
            cache[index] = {**existing, **row}
            # Drop any other duplicates for same product id from cache.
            if product_id:
                st.session_state.tracked_rows_cache = [
                    r for i, r in enumerate(cache)
                    if i == index or extract_markaz_product_id(r.get('markaz_url')) != product_id
                ]
            return
    cache.insert(0, row)


def remove_tracked_rows_from_cache(markaz_urls):
    urls = {url for url in (markaz_urls or []) if url}
    if not urls:
        return
    cache = st.session_state.get('tracked_rows_cache')
    if cache is None:
        return
    st.session_state.tracked_rows_cache = [
        row for row in cache if row.get('markaz_url') not in urls
    ]


def set_tracked_rows_cache(rows):
    st.session_state.tracked_rows_cache = rows or []


def _merge_tracked_rows_cache(existing_rows, updated_rows):
    """Merge batch upsert results into cached list without refetching."""
    by_url = {row.get('markaz_url'): row for row in (existing_rows or []) if row.get('markaz_url')}
    for row in updated_rows or []:
        url = row.get('markaz_url')
        if url:
            by_url[url] = {**by_url.get(url, {}), **row}
    merged = list(by_url.values())
    merged.sort(key=lambda row: row.get('created_at') or '', reverse=True)
    return merged


def load_tracked_rows(force_refresh=False):
    """Load tracked products once per session until Reload or force_refresh."""
    if force_refresh or 'tracked_rows_cache' not in st.session_state:
        st.session_state.tracked_rows_cache = list_tracked_products()
        _increment_supabase_fetch_count()
    return st.session_state.tracked_rows_cache


def seed_shopify_status_map_from_rows(tracked_rows):
    """Provisional status from Supabase fields — no Shopify API calls."""
    status_map = {}
    for row in tracked_rows or []:
        row_key = row.get('markaz_url') or row.get('id')
        handle = (row.get('shopify_handle') or '').strip()
        product_id = (row.get('shopify_product_id') or '').strip()
        if handle or product_id:
            status_map[row_key] = {
                'on_shopify': True,
                'status_unknown': True,
                'status': None,
                'shopify_handle': handle or None,
                'shopify_product_id': product_id or None,
                'admin_url': '',
            }
        else:
            status_map[row_key] = {'on_shopify': False, 'status': None}
    return status_map


def load_shopify_status_map(tracked_rows, force_refresh=False):
    if not is_shopify_configured():
        return {}

    if force_refresh:
        with st.spinner(
            "Fetching Shopify status (rate-limited ~2 calls/sec; "
            "products with saved IDs load in bulk)..."
        ):
            previous = st.session_state.get('shopify_status_map') or {}
            st.session_state.shopify_status_map = fetch_shopify_status_map(
                tracked_rows,
                existing_map=previous,
            )
        return st.session_state.shopify_status_map

    if 'shopify_status_map' not in st.session_state:
        # First open this session: show linked/not-linked from DB only.
        # Live Active/Draft comes from "Refresh Shopify Status" (avoids 429 spam).
        st.session_state.shopify_status_map = seed_shopify_status_map_from_rows(tracked_rows)

    return st.session_state.shopify_status_map


def refresh_shopify_status_for_row(row):
    if not is_shopify_configured():
        return False

    row_key = row.get('markaz_url') or row.get('id')
    if 'shopify_status_map' not in st.session_state:
        st.session_state.shopify_status_map = {}

    previous = st.session_state.shopify_status_map
    st.session_state.shopify_status_map.update(
        fetch_shopify_status_map([row], existing_map=previous)
    )
    snapshot = st.session_state.shopify_status_map.get(row_key) or {}
    # Persist product_id when live lookup found it (speeds future bulk refresh).
    if (
        snapshot.get('on_shopify')
        and not snapshot.get('status_unknown')
        and snapshot.get('shopify_product_id')
        and row.get('markaz_url')
        and is_supabase_configured()
    ):
        update_tracked_shopify_metadata_batch([{
            'markaz_url': row.get('markaz_url'),
            'shopify_product_id': snapshot.get('shopify_product_id'),
            'shopify_handle': snapshot.get('shopify_handle') or row.get('shopify_handle'),
        }])
        patch_tracked_row_in_cache({
            'markaz_url': row.get('markaz_url'),
            'shopify_product_id': snapshot.get('shopify_product_id'),
            'shopify_handle': snapshot.get('shopify_handle') or row.get('shopify_handle'),
        })
    return row_key in st.session_state.shopify_status_map


def render_shopify_status_summary(tracked_rows, shopify_status_map):
    if not is_shopify_configured():
        return

    on_shopify = 0
    active_count = 0
    draft_count = 0
    for row in tracked_rows:
        row_key = row.get('markaz_url') or row.get('id')
        snapshot = shopify_status_map.get(row_key, {})
        if snapshot.get('on_shopify'):
            on_shopify += 1
            status = (snapshot.get('status') or '').lower()
            if status == 'active':
                active_count += 1
            elif status == 'draft':
                draft_count += 1

    st.caption(
        f"Shopify: **{on_shopify}** of **{len(tracked_rows)}** tracked product(s) found on store "
        f"({active_count} active, {draft_count} draft)."
    )
    if any(
        (shopify_status_map.get(row.get('markaz_url') or row.get('id')) or {}).get('status_unknown')
        for row in tracked_rows
    ):
        st.caption(
            "Some products show **Shopify: Linked** until you click **Refresh Shopify Status** "
            "(avoids Shopify 429 rate-limit errors on every page load)."
        )


SHOPIFY_ICON_PATH = Path(__file__).resolve().parent / 'assets' / 'shopify-icon.svg'


def render_tracked_products_heading():
    heading_col, icon_col, refresh_col = st.columns([0.82, 0.06, 0.12], vertical_alignment="center")
    with heading_col:
        st.subheader("Tracked Products")
    with icon_col:
        if is_shopify_configured():
            render_shopify_tab_icon()
    with refresh_col:
        if st.button(
            "Reload list",
            key="reload_tracked_list",
            help="Force refresh tracked products from Supabase (skips local cache).",
        ):
            invalidate_tracked_rows_cache()
            invalidate_shopify_status_cache()
            st.rerun()


def apply_shopify_sync_results(results):
    synced_count = 0
    failed_results = []
    metadata_batch = []

    for result in results:
        if result.get('success'):
            synced_count += 1
            markaz_url = result.get('markaz_url')
            if markaz_url:
                metadata_batch.append({
                    'markaz_url': markaz_url,
                    'shopify_product_id': result.get('shopify_product_id'),
                    'shopify_handle': result.get('shopify_handle'),
                })
                patch_tracked_row_in_cache({
                    'markaz_url': markaz_url,
                    'shopify_product_id': result.get('shopify_product_id'),
                    'shopify_handle': result.get('shopify_handle'),
                    'stock_status': result.get('stock_status'),
                })
        else:
            failed_results.append(result)

    if metadata_batch:
        update_tracked_shopify_metadata_batch(metadata_batch)

    return synced_count, failed_results


def show_shopify_sync_summary(synced_count, failed_results):
    if os.environ.get('MARKAZ_DEMO_MODE') == '1':
        from demo_mode.demo_guard import DEMO_SHOPIFY_ALERT

        st.warning(DEMO_SHOPIFY_ALERT)
    if synced_count:
        st.success(f"Synced **{synced_count}** product(s) to Shopify (simulated).")
    for result in failed_results:
        label = result.get('title') or result.get('shopify_handle') or result.get('markaz_url', 'Product')
        st.warning(f"Shopify sync skipped/failed for **{label}**: {result.get('error', 'Unknown error')}")


def apply_shopify_publish_results(results):
    created_count = 0
    updated_count = 0
    failed_results = []
    warning_results = []
    upsert_batch = []

    for result in results:
        if result.get('success'):
            if result.get('action') == 'created':
                created_count += 1
            else:
                updated_count += 1

            if result.get('stock_sync_warning'):
                warning_results.append(result)
            elif result.get('timeout_recovered') or result.get('image_sync_errors') or result.get('message'):
                # Soft notices (timeout recovery / partial image upload) — show as warnings.
                if result.get('timeout_recovered') or result.get('image_sync_errors'):
                    warning_results.append(result)

            markaz_url = result.get('markaz_url')
            if markaz_url and is_supabase_configured():
                upsert_batch.append({
                    'markaz_url': markaz_url,
                    'stock_status': result.get('stock_status', 'unknown'),
                    'title': result.get('title'),
                    'shopify_handle': result.get('shopify_handle'),
                    'shopify_product_id': result.get('shopify_product_id'),
                })
        else:
            failed_results.append(result)

    if upsert_batch:
        saved_rows = batch_upsert_tracked_products(upsert_batch)
        for row in saved_rows:
            patch_tracked_row_in_cache(row)

    return created_count, updated_count, failed_results, warning_results


def format_shopify_error_message(error_text):
    error_text = error_text or 'Unknown error'
    if 'merchant approval' in error_text.lower():
        scope_match = re.search(r'for ([\w_]+) scope', error_text)
        missing_scope = scope_match.group(1) if scope_match else None
        scope_hint = f" Missing scope: `{missing_scope}`." if missing_scope else ''
        return (
            f"{error_text}\n\n"
            f"**Fix:** Your Shopify app is connected but the store has not approved API permissions.{scope_hint}\n\n"
            "1. Open [Shopify Dev Dashboard](https://dev.shopify.com/dashboard) → your app → **Configuration**\n"
            "2. Under **Admin API access scopes**, enable all of:\n"
            "   `read_products`, `write_products`, `read_inventory`, `write_inventory`, `read_locations`\n"
            "3. **Save** and **Release** a new app version\n"
            "4. Reinstall the app on **at One Spot** (`5qxhsf-vs.myshopify.com`) and click **Install** / **Approve**\n"
            "5. Restart this app and publish again"
        )
    return error_text


def store_shopify_publish_feedback(created_count, updated_count, failed_results, warning_results=None):
    st.session_state.shopify_publish_feedback = {
        'created': created_count,
        'updated': updated_count,
        'failed': failed_results,
        'warnings': warning_results or [],
    }


def render_shopify_publish_feedback():
    feedback = st.session_state.get('shopify_publish_feedback')
    if not feedback:
        return

    show_shopify_publish_summary(
        feedback.get('created', 0),
        feedback.get('updated', 0),
        feedback.get('failed', []),
        feedback.get('warnings', []),
    )
    if st.button('Dismiss publish results', key='dismiss_shopify_publish_feedback'):
        st.session_state.shopify_publish_feedback = None
        st.rerun()


def show_shopify_publish_summary(created_count, updated_count, failed_results, warning_results=None):
    if os.environ.get('MARKAZ_DEMO_MODE') == '1':
        from demo_mode.demo_guard import DEMO_SHOPIFY_ALERT

        st.warning(DEMO_SHOPIFY_ALERT)

    if created_count or updated_count:
        success_label = 'simulated' if os.environ.get('MARKAZ_DEMO_MODE') == '1' else 'complete'
        st.success(
            f"Shopify publish {success_label}. **Created:** {created_count}, **Updated:** {updated_count}."
        )
    elif failed_results:
        st.error("No products were published to Shopify. See error details below.")

    for result in warning_results or []:
        label = result.get('title') or result.get('shopify_handle') or result.get('markaz_url', 'Product')
        images_added = result.get('images_added', 0)
        images_note = f" **Images added:** {images_added}." if images_added else ''
        if result.get('stock_sync_warning'):
            st.warning(
                f"**{label}** published, but stock/inventory was not synced.{images_note}\n\n"
                f"{format_shopify_error_message(result.get('stock_sync_warning'))}"
            )
        elif result.get('timeout_recovered'):
            st.warning(
                f"**{label}** is on Shopify (create/update response timed out, then recovered)."
                f"{images_note}\n\n{result.get('message', '')}"
            )
        elif result.get('image_sync_errors'):
            st.warning(
                f"**{label}** published, but some images failed.{images_note}\n\n"
                f"{result.get('message') or '; '.join(result.get('image_sync_errors') or [])}"
            )
        elif result.get('message'):
            st.info(f"**{label}:** {result.get('message')}")

    for result in failed_results:
        label = result.get('title') or result.get('shopify_handle') or result.get('markaz_url', 'Product')
        st.error(
            f"Shopify publish failed for **{label}**:\n\n{format_shopify_error_message(result.get('error'))}"
        )


def fetch_markaz_products_from_tracked_rows(tracked_rows):
    if os.environ.get('MARKAZ_DEMO_MODE') == '1':
        from demo_mode.demo_markaz import fetch_demo_products_from_tracked_rows

        return fetch_demo_products_from_tracked_rows(tracked_rows)

    products = []
    processed_urls = set()
    failed = []
    total = len(tracked_rows)

    with sync_playwright() as playwright:
        browser = launch_browser_for_serverless(playwright)
        for index, row in enumerate(tracked_rows):
            link = row.get('markaz_url', '').strip()
            if not link:
                continue

            context = None
            try:
                context = browser.new_context(
                    permissions=[],
                    ignore_https_errors=True,
                    viewport={'width': 1920, 'height': 1080},
                )
                page = context.new_page()
                product_data = scrape_product_from_page(page, link)
                if product_data.get('status') == 'success':
                    apply_default_pricing_rules(product_data)
                    products.append(product_data)
                    processed_urls.add(link)
                else:
                    failed.append((link, product_data.get('status', 'Unknown error')))
            except Exception as exc:
                failed.append((link, str(exc)))
            finally:
                if context:
                    try:
                        context.close()
                    except Exception:
                        pass
            if index < total - 1:
                time.sleep(0.5)

        try:
            browser.close()
        except Exception:
            pass

    return products, processed_urls, failed


def render_tracked_products_tab():
    render_tracked_products_heading()
    st.caption("Markaz URLs auto-save here when you successfully add a product in the Converter tab.")

    if not is_supabase_configured():
        st.warning("Supabase is not configured. Add your keys to `.streamlit/secrets.toml`.")
        return

    try:
        tracked_rows = load_tracked_rows()
    except Exception as exc:
        st.error(f"Could not load tracked products from Supabase: {exc}")
        return

    if not tracked_rows:
        st.info("No tracked products yet. Add a product in the Converter tab and it will appear here automatically.")
        return

    dup_groups, dup_extra = count_duplicate_tracked_products(tracked_rows)
    if dup_groups:
        st.warning(
            f"Found **{dup_groups}** duplicate Markaz product group(s) "
            f"(**{dup_extra}** extra row(s)). Same product id / Shopify handle is linked more than once."
        )
        if st.button(
            "Remove duplicate Markaz links",
            type="primary",
            key="dedupe_tracked_markaz_urls",
            help="Keep one row per Markaz product id (merge Shopify fields), delete the extras.",
        ):
            with st.spinner("Merging duplicate Markaz links..."):
                summary = dedupe_tracked_products(tracked_rows)
            invalidate_tracked_rows_cache()
            invalidate_shopify_status_cache()
            st.success(
                f"Removed **{summary.get('removed', 0)}** duplicate row(s) "
                f"across **{summary.get('groups', 0)}** product group(s)."
            )
            st.rerun()

    stock_filter = st.radio(
        "Filter by Markaz stock",
        options=["All", "In Stock", "Out of Stock", "Unknown"],
        horizontal=True,
        key="tracked_stock_filter",
    )
    shopify_filter = st.radio(
        "Filter by Shopify status",
        options=["All", "Not on Shopify", "Active", "Draft", "Archived"],
        horizontal=True,
        key="tracked_shopify_filter",
        help="Uses latest Shopify status snapshot. Click Refresh Shopify Status if list looks stale.",
    )

    shopify_status_map = load_shopify_status_map(tracked_rows)
    filtered_rows = get_filtered_tracked_rows(tracked_rows, stock_filter)
    filtered_rows = get_filtered_tracked_rows_by_shopify(
        filtered_rows,
        shopify_filter,
        shopify_status_map,
    )

    auto_sync_shopify = st.checkbox(
        "Auto-sync to Shopify after Refresh All Status",
        value=True,
        key="shopify_auto_sync_on_refresh",
        disabled=not is_shopify_configured(),
    )

    refresh_col, shopify_refresh_col, send_col, sync_col, publish_col, delete_col = st.columns(6)
    with refresh_col:
        refresh_all = st.button("Refresh All Status", type="secondary", key="refresh_all_tracked")
    with shopify_refresh_col:
        refresh_shopify_status = st.button(
            "Refresh Shopify Status",
            type="secondary",
            key="refresh_shopify_status_map",
            disabled=not is_shopify_configured(),
            help=(
                "Fetch live Active/Draft status from Shopify. "
                "Uses bulk ID lookup + rate limiting (~2 calls/sec) to avoid 429 errors."
            ),
        )
    with send_col:
        send_to_converter = st.button(
            "Send to Converter",
            type="primary",
            key="send_filtered_to_converter",
            help="Re-fetch filtered products and load them in Shopify Converter for CSV.",
        )
    with sync_col:
        sync_to_shopify = st.button(
            "Sync Stock",
            type="secondary",
            key="sync_filtered_to_shopify",
            disabled=not is_shopify_configured(),
            help="Update inventory/status on existing Shopify products.",
        )
    with publish_col:
        publish_to_shopify = st.button(
            "Publish to Shopify",
            type="primary",
            key="publish_filtered_to_shopify",
            disabled=not is_shopify_configured(),
            help="Fetch from Markaz and create products directly on Shopify.",
        )
    with delete_col:
        delete_filtered = st.button(
            "Delete Filtered",
            type="secondary",
            key="delete_filtered_tracked",
            help="Delete currently filtered products from Supabase and Shopify.",
        )

    if delete_filtered:
        if not filtered_rows:
            st.warning("No products match the current Markaz/Shopify filters to delete.")
            st.session_state.pop('bulk_delete_pending_rows', None)
        else:
            st.session_state.bulk_delete_pending_rows = [
                {
                    'id': row.get('id'),
                    'markaz_url': row.get('markaz_url'),
                    'title': row.get('title'),
                    'shopify_handle': row.get('shopify_handle'),
                    'shopify_product_id': row.get('shopify_product_id'),
                }
                for row in filtered_rows
            ]

    pending_delete_rows = st.session_state.get('bulk_delete_pending_rows') or []
    if pending_delete_rows:
        st.warning(
            f"⚠️ Confirm permanent delete of **{len(pending_delete_rows)}** filtered product(s) "
            "from **Supabase** and **Shopify** (if linked)."
        )
        confirm_col, cancel_col, _ = st.columns([1, 1, 4])
        with confirm_col:
            confirm_bulk_delete = st.button(
                "Confirm Delete",
                type="primary",
                key="confirm_bulk_delete_tracked",
            )
        with cancel_col:
            cancel_bulk_delete = st.button("Cancel", key="cancel_bulk_delete_tracked")

        if cancel_bulk_delete:
            st.session_state.pop('bulk_delete_pending_rows', None)
            st.rerun()

        if confirm_bulk_delete:
            progress = st.progress(0.0, text="Deleting filtered products...")
            status_container = st.empty()
            removed_count = 0
            shopify_deleted = 0
            shopify_failed = []
            urls_to_delete = []

            for index, row in enumerate(pending_delete_rows):
                title = row.get('title') or row.get('markaz_url') or 'Product'
                status_container.caption(
                    f"Deleting **{index + 1} of {len(pending_delete_rows)}**: {title[:60]}"
                )
                progress.progress(
                    (index + 1) / len(pending_delete_rows),
                    text=f"Delete {index + 1} of {len(pending_delete_rows)}",
                )

                if is_shopify_configured():
                    shopify_result = delete_tracked_row_from_shopify(row)
                    if shopify_result.get('success'):
                        if not (
                            shopify_result.get('skipped')
                            or shopify_result.get('not_found')
                        ):
                            shopify_deleted += 1
                    else:
                        shopify_failed.append({
                            'title': title,
                            'error': shopify_result.get('error', 'Unknown error'),
                        })

                markaz_url = row.get('markaz_url')
                if markaz_url:
                    urls_to_delete.append(markaz_url)

            if urls_to_delete:
                delete_tracked_products(urls_to_delete)
                removed_count = len(urls_to_delete)
                remove_tracked_rows_from_cache(urls_to_delete)

            progress.progress(1.0, text="Done.")
            status_container.caption("Finished.")
            st.session_state.pop('bulk_delete_pending_rows', None)
            invalidate_shopify_status_cache()

            st.success(
                f"Deleted **{removed_count}** product(s) from tracked list. "
                f"Shopify deleted: **{shopify_deleted}**."
            )
            for failed in shopify_failed:
                st.warning(
                    f"Removed from tracked list, but Shopify delete failed for "
                    f"**{failed['title']}**: {failed['error']}"
                )
            st.rerun()

    if refresh_shopify_status:
        tracked_for_status = load_tracked_rows()
        previous_map = st.session_state.get('shopify_status_map') or {}
        with st.spinner(
            "Fetching Shopify status (bulk by product ID; handles throttled "
            "to stay under 2 calls/sec)..."
        ):
            fresh_map = fetch_shopify_status_map(
                tracked_for_status,
                existing_map=previous_map,
            )
        st.session_state.shopify_status_map = fresh_map

        # Save newly discovered product IDs so next refresh is mostly 1 bulk call.
        metadata_batch = []
        for row in tracked_for_status:
            row_key = row.get('markaz_url') or row.get('id')
            snapshot = fresh_map.get(row_key) or {}
            if (
                snapshot.get('on_shopify')
                and not snapshot.get('status_unknown')
                and snapshot.get('shopify_product_id')
                and row.get('markaz_url')
            ):
                if str(row.get('shopify_product_id') or '') != str(snapshot.get('shopify_product_id')):
                    metadata_batch.append({
                        'markaz_url': row.get('markaz_url'),
                        'shopify_product_id': snapshot.get('shopify_product_id'),
                        'shopify_handle': snapshot.get('shopify_handle') or row.get('shopify_handle'),
                    })
                    patch_tracked_row_in_cache({
                        'markaz_url': row.get('markaz_url'),
                        'shopify_product_id': snapshot.get('shopify_product_id'),
                        'shopify_handle': snapshot.get('shopify_handle') or row.get('shopify_handle'),
                    })
        if metadata_batch and is_supabase_configured():
            update_tracked_shopify_metadata_batch(metadata_batch)

        rate_limited = sum(
            1 for snap in fresh_map.values()
            if snap.get('rate_limited') or snap.get('status_unknown')
        )
        if rate_limited:
            st.warning(
                f"Shopify status refreshed with **{rate_limited}** product(s) still pending "
                "(rate limit / not fully loaded). Click **Refresh Shopify Status** again after a few seconds."
            )
        else:
            st.success("Shopify status refreshed for tracked products.")
        st.rerun()

    if refresh_all:
        tracked_rows = load_tracked_rows()
        progress = st.progress(0.0, text="Refreshing stock status...")
        batch_items = []
        for index, row in enumerate(tracked_rows):
            progress.progress((index + 1) / len(tracked_rows), text=f"Checking {index + 1} of {len(tracked_rows)}")
            scraped = scrape_markaz_product(row['markaz_url'])
            if scraped.get('status') == 'success':
                shopify_handle = generate_unique_handle(
                    scraped.get('title', ''),
                    scraped.get('base_sku', ''),
                )
                batch_items.append({
                    'markaz_url': row['markaz_url'],
                    'stock_status': scraped.get('stock_status', 'unknown'),
                    'title': scraped.get('title'),
                    'shopify_handle': shopify_handle,
                })
        progress.progress(1.0, text="Saving to Supabase...")
        if batch_items:
            saved_rows = batch_upsert_tracked_products(batch_items)
            set_tracked_rows_cache(
                _merge_tracked_rows_cache(load_tracked_rows(), saved_rows)
            )
        st.success("Stock status refreshed for all tracked products.")

        refreshed_rows = load_tracked_rows()

        if auto_sync_shopify and is_shopify_configured():
            sync_results = sync_tracked_rows_to_shopify(refreshed_rows)
            synced_count, failed_results = apply_shopify_sync_results(sync_results)
            show_shopify_sync_summary(synced_count, failed_results)

        invalidate_shopify_status_cache()
        st.rerun()

    if sync_to_shopify:
        if not is_shopify_configured():
            st.warning("Shopify is not configured. Add credentials to `.streamlit/secrets.toml`.")
        elif not filtered_rows:
            st.warning("No products match the current Markaz/Shopify filters to sync.")
        else:
            with st.spinner(f"Syncing {len(filtered_rows)} product(s) to Shopify..."):
                sync_results = sync_tracked_rows_to_shopify(filtered_rows)
            synced_count, failed_results = apply_shopify_sync_results(sync_results)
            show_shopify_sync_summary(synced_count, failed_results)
            invalidate_shopify_status_cache()
            st.rerun()

    if publish_to_shopify:
        if not is_shopify_configured():
            st.warning("Shopify is not configured. Add credentials to `.streamlit/secrets.toml`.")
        elif not filtered_rows:
            st.warning("No products match the current Markaz/Shopify filters to publish.")
        else:
            progress = st.progress(0.0, text="Fetching from Markaz...")
            status_container = st.empty()
            status_container.caption(f"Fetching **{len(filtered_rows)}** product(s) from Markaz...")
            products, _, fetch_failed = fetch_markaz_products_from_tracked_rows(filtered_rows)
            progress.progress(0.5, text="Publishing to Shopify...")
            status_container.caption(f"Publishing **{len(products)}** product(s) to Shopify...")
            publish_results = publish_products_to_shopify(products)
            created_count, updated_count, publish_failed, publish_warnings = apply_shopify_publish_results(publish_results)
            progress.progress(1.0, text="Done.")
            status_container.caption("Finished.")
            store_shopify_publish_feedback(created_count, updated_count, publish_failed, publish_warnings)
            for link, error in fetch_failed:
                st.warning(f"Markaz fetch failed: {link[:70]}... — {error}")
            invalidate_shopify_status_cache()
            st.rerun()

    if send_to_converter:
        if not filtered_rows:
            st.warning("No products match the current Markaz/Shopify filters to send.")
        else:
            progress = st.progress(0.0, text="Fetching products from Markaz...")
            status_container = st.empty()
            status_container.caption(f"Fetching **{len(filtered_rows)}** product(s) from Markaz...")
            products, processed_urls, failed = fetch_markaz_products_from_tracked_rows(filtered_rows)
            progress.progress(1.0, text="Done.")
            status_container.caption("Finished.")

            if products:
                st.session_state.products_list = products
                st.session_state.processed_urls = processed_urls
                st.session_state.fetched_product_data = None
                filter_note_parts = []
                if stock_filter != "All":
                    filter_note_parts.append(f"Markaz: {stock_filter}")
                if shopify_filter != "All":
                    filter_note_parts.append(f"Shopify: {shopify_filter}")
                filter_note = " · ".join(filter_note_parts) if filter_note_parts else "All"
                st.session_state.converter_import_message = (
                    f"Loaded **{len(products)}** product(s) with filter **{filter_note}**. "
                    "Open the **Shopify Converter** tab to review and download CSV."
                )
                st.success(st.session_state.converter_import_message)
            else:
                st.error("No products could be fetched. Please try again.")

            for link, error in failed:
                st.warning(f"Skipped: {link[:70]}... — {error}")

            if products:
                st.rerun()

    filter_parts = []
    if stock_filter != "All":
        filter_parts.append(f"Markaz: {stock_filter}")
    if shopify_filter != "All":
        filter_parts.append(f"Shopify: {shopify_filter}")
    filter_label = " · ".join(filter_parts) if filter_parts else "All"

    if not filter_parts:
        st.markdown(f"**{len(tracked_rows)}** saved URL(s)")
    else:
        st.markdown(
            f"**{len(filtered_rows)}** matching of **{len(tracked_rows)}** "
            f"({filter_label})"
        )

    render_shopify_status_summary(tracked_rows, shopify_status_map)
    fetch_count = st.session_state.get('supabase_fetch_count', 0)
    if fetch_count:
        st.caption(
            f"Supabase list loaded from cache this session "
            f"(**{fetch_count}** full fetch{'es' if fetch_count != 1 else ''} to database). "
            "Use **Reload list** only when you need fresh data."
        )

    if not filtered_rows:
        st.info(f"No products match filter **{filter_label}**.")
        return

    # Pagination: 50 rows per page (list view only — bulk actions still use full filtered set)
    TRACKED_PAGE_SIZE = 50
    filter_signature = f"{stock_filter}|{shopify_filter}|{len(filtered_rows)}"
    if st.session_state.get('tracked_page_filter_sig') != filter_signature:
        st.session_state.tracked_page_filter_sig = filter_signature
        st.session_state.tracked_list_page = 1

    total_filtered = len(filtered_rows)
    total_pages = max(1, (total_filtered + TRACKED_PAGE_SIZE - 1) // TRACKED_PAGE_SIZE)
    current_page = int(st.session_state.get('tracked_list_page', 1) or 1)
    current_page = min(max(1, current_page), total_pages)
    st.session_state.tracked_list_page = current_page

    start_idx = (current_page - 1) * TRACKED_PAGE_SIZE
    end_idx = min(start_idx + TRACKED_PAGE_SIZE, total_filtered)
    page_rows = filtered_rows[start_idx:end_idx]

    nav_prev, nav_info, nav_next = st.columns([1, 3, 1])
    with nav_prev:
        if st.button(
            "← Prev",
            key="tracked_page_prev",
            disabled=current_page <= 1,
            width='stretch',
        ):
            st.session_state.tracked_list_page = current_page - 1
            st.rerun()
    with nav_info:
        st.markdown(
            f"<div style='text-align:center; padding-top:0.4rem;'>"
            f"Page <strong>{current_page}</strong> of <strong>{total_pages}</strong>"
            f" · showing <strong>{start_idx + 1}–{end_idx}</strong> of <strong>{total_filtered}</strong>"
            f" · {TRACKED_PAGE_SIZE}/page"
            f"</div>",
            unsafe_allow_html=True,
        )
    with nav_next:
        if st.button(
            "Next →",
            key="tracked_page_next",
            disabled=current_page >= total_pages,
            width='stretch',
        ):
            st.session_state.tracked_list_page = current_page + 1
            st.rerun()

    for row in page_rows:
        title = row.get('title') or 'Untitled product'
        stock_status = row.get('stock_status', 'unknown')
        row_key = row.get('markaz_url') or row.get('id')
        shopify_snapshot = shopify_status_map.get(row_key, {})
        expander_label = (
            f"{format_stock_status_label(stock_status)} | "
            f"{format_shopify_status_label(shopify_snapshot)} | {title}"
        )
        with st.expander(expander_label, expanded=False):
            st.write("**Markaz Stock Status:**", format_stock_status_label(stock_status))
            render_shopify_green_field("Shopify Status", format_shopify_status_detail(shopify_snapshot))

            if shopify_snapshot.get('on_shopify'):
                if shopify_snapshot.get('shopify_handle'):
                    st.write("**Shopify Handle:**", shopify_snapshot['shopify_handle'])
                elif row.get('shopify_handle'):
                    st.write("**Shopify Handle:**", row['shopify_handle'])
                if shopify_snapshot.get('shopify_product_id'):
                    render_shopify_green_field("Shopify Product ID", shopify_snapshot['shopify_product_id'])
                if shopify_snapshot.get('published_at'):
                    st.write("**Published on Shopify:**", shopify_snapshot['published_at'])
                if shopify_snapshot.get('updated_at'):
                    st.write("**Last Updated on Shopify:**", shopify_snapshot['updated_at'])
                admin_url = shopify_snapshot.get('admin_url')
                if admin_url:
                    st.markdown(f"**Open in Shopify:** [{admin_url}]({admin_url})")
            elif row.get('shopify_handle'):
                st.write("**Shopify Handle (saved):**", row['shopify_handle'])
                if shopify_snapshot.get('error') and '429' in str(shopify_snapshot.get('error')):
                    st.caption(
                        "Shopify rate limit hit while checking this product. "
                        "Wait a few seconds, then click **Shopify Status** again."
                    )
                else:
                    st.caption(
                        "Handle is saved, but Shopify did not return this product "
                        "(deleted on Shopify, or status not refreshed yet)."
                    )

            st.write("**Markaz URL:**", row.get('markaz_url'))
            if row.get('last_checked_at'):
                st.write("**Last Checked (Markaz):**", row['last_checked_at'])
            if row.get('created_at'):
                st.write("**Saved At:**", row['created_at'])

            action_col1, action_col2, action_col3, action_col4, action_col5 = st.columns(5)
            with action_col1:
                if st.button("Refresh Status", key=f"refresh_tracked_{row['id']}", width='stretch'):
                    with st.spinner("Checking Markaz..."):
                        scraped = scrape_markaz_product(row['markaz_url'])
                    if scraped.get('status') == 'success':
                        update_tracked_product_from_scrape(row['markaz_url'], scraped)
                        st.success("Markaz status updated.")
                        st.rerun()
                    else:
                        st.error(scraped.get('status', 'Failed to refresh status'))
            with action_col2:
                if st.button(
                    "Shopify Status",
                    key=f"shopify_status_{row['id']}",
                    width='stretch',
                    disabled=not is_shopify_configured(),
                    help="Fetch latest status from Shopify for this product.",
                ):
                    with st.spinner("Fetching Shopify status..."):
                        refresh_shopify_status_for_row(row)
                    st.success("Shopify status refreshed.")
                    st.rerun()
            with action_col3:
                if st.button(
                    "Sync Stock",
                    key=f"sync_stock_{row['id']}",
                    width='stretch',
                    disabled=not is_shopify_configured(),
                    help="Sync inventory and product status on Shopify.",
                ):
                    with st.spinner("Syncing stock to Shopify..."):
                        sync_results = sync_tracked_rows_to_shopify([row])
                    synced_count, failed_results = apply_shopify_sync_results(sync_results)
                    if synced_count:
                        st.success("Stock synced to Shopify.")
                    show_shopify_sync_summary(synced_count, failed_results)
                    invalidate_shopify_status_cache()
                    st.rerun()
            with action_col4:
                if st.button(
                    "Publish Shopify",
                    key=f"publish_shopify_{row['id']}",
                    width='stretch',
                    disabled=not is_shopify_configured(),
                    help="Fetch from Markaz and publish or update on Shopify.",
                ):
                    with st.spinner("Publishing to Shopify..."):
                        products, _, fetch_failed = fetch_markaz_products_from_tracked_rows([row])
                        if fetch_failed:
                            for link, error in fetch_failed:
                                st.warning(f"Markaz fetch failed: {link[:70]}... — {error}")
                        if products:
                            publish_results = publish_products_to_shopify(products)
                            created_count, updated_count, publish_failed, publish_warnings = (
                                apply_shopify_publish_results(publish_results)
                            )
                            store_shopify_publish_feedback(
                                created_count, updated_count, publish_failed, publish_warnings
                            )
                            invalidate_shopify_status_cache()
                            st.rerun()
                        elif not fetch_failed:
                            st.error("Could not fetch product data from Markaz.")
            with action_col5:
                if st.button("Delete", key=f"delete_tracked_{row['id']}", width='stretch'):
                    shopify_delete_result = None
                    if is_shopify_configured():
                        with st.spinner("Deleting from Shopify..."):
                            shopify_delete_result = delete_tracked_row_from_shopify(row)

                    delete_tracked_product(row['markaz_url'])
                    remove_tracked_rows_from_cache([row['markaz_url']])
                    invalidate_shopify_status_cache()

                    if shopify_delete_result and shopify_delete_result.get('success'):
                        if shopify_delete_result.get('skipped') or shopify_delete_result.get('not_found'):
                            st.success(
                                "Removed from tracked list. "
                                f"{shopify_delete_result.get('message', 'No Shopify product was linked.')}"
                            )
                        else:
                            st.success("Removed from tracked list and deleted from Shopify.")
                    elif shopify_delete_result and not shopify_delete_result.get('success'):
                        st.warning(
                            "Removed from tracked list, but Shopify delete failed: "
                            f"{shopify_delete_result.get('error', 'Unknown error')}"
                        )
                    else:
                        st.success("Removed from tracked list.")
                    st.rerun()

    if total_pages > 1:
        st.divider()
        bot_prev, bot_info, bot_next = st.columns([1, 3, 1])
        with bot_prev:
            if st.button(
                "← Prev",
                key="tracked_page_prev_bottom",
                disabled=current_page <= 1,
                width='stretch',
            ):
                st.session_state.tracked_list_page = current_page - 1
                st.rerun()
        with bot_info:
            st.markdown(
                f"<div style='text-align:center; padding-top:0.4rem;'>"
                f"Page <strong>{current_page}</strong> / <strong>{total_pages}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with bot_next:
            if st.button(
                "Next →",
                key="tracked_page_next_bottom",
                disabled=current_page >= total_pages,
                width='stretch',
            ):
                st.session_state.tracked_list_page = current_page + 1
                st.rerun()


def scrape_and_add_links_to_list(links, progress_bar=None, status_container=None):
    """Scrape product URLs and append successful results to products_list. Returns added count."""
    total = len(links)
    added_count = 0
    if total == 0:
        return 0

    def _update(i, label):
        if status_container is not None:
            status_container.caption(label)
        if progress_bar is not None:
            progress_bar.progress((i + 1) / total, text=f"Link {i + 1} of {total}")

    if _IS_DEMO:
        for i, link in enumerate(links):
            _update(i, f"**Link {i + 1} of {total}** — fetching (demo)...")
            if link in st.session_state.processed_urls:
                st.warning(f"⚠️ Skipped (already added): {link[:60]}...")
                continue
            try:
                new_product_data = scrape_markaz_product(link)
                if new_product_data.get("status") == "success":
                    apply_default_pricing_rules(new_product_data)
                    st.session_state.products_list.append(new_product_data)
                    st.session_state.processed_urls.add(link)
                    saved_ok, saved_error = save_product_to_supabase(new_product_data)
                    if not saved_ok:
                        st.warning(f"Supabase save failed for {link[:60]}... — {saved_error}")
                    added_count += 1
                else:
                    st.warning(
                        f"⚠️ Skipped (failed): {link[:60]}... — "
                        f"{new_product_data.get('status', 'Unknown error')}"
                    )
            except Exception as e:
                st.warning(f"⚠️ Skipped (error): {link[:60]}... — {str(e)}")
        return added_count

    with sync_playwright() as p:
        browser = launch_browser_for_serverless(p)
        for i, link in enumerate(links):
            _update(i, f"**Link {i + 1} of {total}** — fetching...")
            if link in st.session_state.processed_urls:
                st.warning(f"⚠️ Skipped (already added): {link[:60]}...")
                continue
            context = None
            try:
                context = browser.new_context(
                    permissions=[],
                    ignore_https_errors=True,
                    viewport={'width': 1920, 'height': 1080},
                )
                page = context.new_page()
                new_product_data = scrape_product_from_page(page, link)
                if new_product_data.get("status") == "success":
                    apply_default_pricing_rules(new_product_data)
                    st.session_state.products_list.append(new_product_data)
                    st.session_state.processed_urls.add(link)
                    saved_ok, saved_error = save_product_to_supabase(new_product_data)
                    if not saved_ok:
                        st.warning(f"Supabase save failed for {link[:60]}... — {saved_error}")
                    added_count += 1
                else:
                    st.warning(
                        f"⚠️ Skipped (failed): {link[:60]}... — "
                        f"{new_product_data.get('status', 'Unknown error')}"
                    )
            except Exception as e:
                st.warning(f"⚠️ Skipped (error): {link[:60]}... — {str(e)}")
            finally:
                if context:
                    try:
                        context.close()
                    except Exception:
                        pass
            if i < total - 1:
                time.sleep(1)
        try:
            browser.close()
        except Exception:
            pass

    return added_count


def render_converter_tab():
    if st.session_state.get('converter_import_message'):
        st.success(st.session_state.converter_import_message)
        if st.button("Dismiss", key="dismiss_converter_import_message"):
            st.session_state.converter_import_message = None
            st.rerun()

    # Custom CSS for button styling
    st.markdown("""
    <style>
    .stButton > button {
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Title + mode buttons: Single | Multiple | Category
    c_title, c_single, c_multi, c_category, c_empty = st.columns([2, 1, 1, 1, 5])
    with c_title:
        st.subheader("Add Products")
    with c_single:
        btn_single = st.button("Single", key="mode_single", help="Fetch one product at a time")
    with c_multi:
        btn_multi = st.button("Multiple", key="mode_multiple", help="Fetch multiple products (paste many URLs)")
    with c_category:
        btn_category = st.button(
            "Category",
            key="mode_category",
            help="Paste a Markaz category page and fetch product cards page-by-page",
        )
    with c_empty:
        pass
    if btn_single:
        st.session_state.add_mode = "single"
        st.rerun()
    if btn_multi:
        st.session_state.add_mode = "multiple"
        st.rerun()
    if btn_category:
        st.session_state.add_mode = "category"
        st.rerun()

    add_mode = st.session_state.add_mode
    if add_mode == "single":
        st.caption("Single product mode — enter one product URL below.")
    elif add_mode == "category":
        st.caption(
            "Category mode — paste a Markaz category/shop page URL. "
            "Product card URLs are collected page-by-page (`?page=1`, `?page=2`, …), then scraped."
        )
    else:
        st.caption("Multiple products mode — paste one product URL per line below.")

    # Initialize URL input counter for unique keys
    if 'url_input_counter' not in st.session_state:
        st.session_state.url_input_counter = 0

    category_start_page = 1
    category_end_page = 1
    if add_mode == "single":
        url_input = st.text_input(
            "Product URL",
            placeholder="https://www.markaz.app/shop/product/...",
            key=f"product_url_input_{st.session_state.url_input_counter}",
        )
    elif add_mode == "category":
        url_input = st.text_input(
            "Category / Shop Page URL",
            placeholder=(
                "https://www.markaz.app/shop/.../3%20Piece%20Suits"
                "  or  ...?page=2"
            ),
            key=f"product_url_input_{st.session_state.url_input_counter}",
        )
        page_col1, page_col2, _ = st.columns([1, 1, 3])
        with page_col1:
            category_start_page = st.number_input(
                "From page",
                min_value=1,
                value=1,
                step=1,
                key="category_start_page",
                help="Markaz uses ?page=N on category pages.",
            )
        with page_col2:
            category_end_page = st.number_input(
                "To page",
                min_value=1,
                value=1,
                step=1,
                key="category_end_page",
                help="Inclusive. Example: 1→2 fetches page=1 and page=2.",
            )
    else:
        url_input = st.text_area(
            "Paste Multiple Product URLs (One per line)",
            placeholder="https://www.markaz.app/shop/product/...\nhttps://www.markaz.app/shop/product/...",
            key=f"product_url_input_{st.session_state.url_input_counter}",
            height=120,
        )
    
    # Add Enter key listener to trigger Add to List button (for single-line paste)
    if not _IS_DEMO and add_mode == "single":
        st.markdown("""
    <script>
    (function() {
        function setupEnterKeyListener() {
            var inputs = document.querySelectorAll('input[type="text"]');
            for (var i = 0; i < inputs.length; i++) {
                var placeholder = (inputs[i].getAttribute('placeholder') || '').toLowerCase();
                if (placeholder.indexOf('markaz.app') !== -1 || placeholder.indexOf('product url') !== -1) {
                    // Remove existing listener if any
                    var newInput = inputs[i].cloneNode(true);
                    inputs[i].parentNode.replaceChild(newInput, inputs[i]);
                    
                    newInput.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter' || e.keyCode === 13) {
                            e.preventDefault();
                            // Find the "Add to List" button by data-testid or text
                            var buttons = document.querySelectorAll('button');
                            for (var j = 0; j < buttons.length; j++) {
                                var buttonText = (buttons[j].textContent || buttons[j].innerText || '').toLowerCase();
                                var buttonId = buttons[j].getAttribute('data-testid') || '';
                                if (buttonText.includes('add to list') || buttonText.includes('✅') || buttonId.includes('quick_add')) {
                                    buttons[j].click();
                                    return;
                                }
                            }
                        }
                    });
                    break;
                }
            }
        }
        
        // Setup listener with delays to ensure input is rendered
        setTimeout(setupEnterKeyListener, 100);
        setTimeout(setupEnterKeyListener, 300);
        setTimeout(setupEnterKeyListener, 600);
        setTimeout(setupEnterKeyListener, 1000);
        
        // Also use MutationObserver to catch dynamically added inputs
        var observer = new MutationObserver(function() {
            setupEnterKeyListener();
        });
        observer.observe(document.body, { childList: true, subtree: true });
        setTimeout(function() { observer.disconnect(); }, 5000);
    })();
    </script>
    """, unsafe_allow_html=True)
    
    # Buttons by mode
    if add_mode == "single":
        col1, col2 = st.columns(2)
        with col1:
            quick_add_button = st.button("✅ Add to List", type="primary", width='stretch', key="quick_add_button")
        with col2:
            fetch_button = st.button("📥 Fetch Product Data", type="secondary", width='stretch')
        category_fetch_button = False
    elif add_mode == "category":
        category_fetch_button = st.button(
            "📥 Fetch Category & Add to List",
            type="primary",
            width='stretch',
            key="category_fetch_button",
        )
        quick_add_button = False
        fetch_button = False
    else:
        quick_add_button = st.button("✅ Add to List", type="primary", width='stretch', key="quick_add_button")
        fetch_button = False
        category_fetch_button = False

    if fetch_button and url_input and add_mode == "single":
        # Single mode: fetch one URL and show preview (changes list me ja kr karein)
        with st.spinner("Fetching product data..."):
            product_data = scrape_markaz_product(url_input.strip())
        if product_data.get("status") == "success":
            if os.environ.get('MARKAZ_DEMO_MODE') == '1':
                st.info('**Demo Mode:** Product preview is simulated from your pasted URL (no live Markaz scrape).')
            st.session_state.fetched_product_data = product_data
            st.session_state.show_product_dialog = True
            st.rerun()
        else:
            st.error(f"Failed to fetch: {product_data.get('status', 'Unknown error')}")

    if category_fetch_button:
        category_url = (url_input or "").strip()
        if not category_url:
            st.warning("Please paste a Markaz category / shop page URL.")
        elif int(category_end_page) < int(category_start_page):
            st.warning("To page must be greater than or equal to From page.")
        else:
            progress_bar = st.progress(0.0, text="Collecting product URLs from category pages...")
            status_container = st.empty()
            status_container.caption(
                f"Scanning category pages **{int(category_start_page)}**–**{int(category_end_page)}**..."
            )
            with st.spinner("Reading product cards from Markaz category page(s)..."):
                discovery = scrape_category_product_urls(
                    category_url,
                    start_page=int(category_start_page),
                    end_page=int(category_end_page),
                )

            if discovery.get("status") != "success":
                progress_bar.progress(1.0, text="Done.")
                st.error(discovery.get("status", "Failed to read category page"))
                for err in discovery.get("errors") or []:
                    st.warning(err)
            else:
                links = discovery.get("urls") or []
                for page_info in discovery.get("pages") or []:
                    st.caption(
                        f"Page {page_info.get('page')}: "
                        f"{page_info.get('count', 0)} link(s) found "
                        f"({page_info.get('unique_new', 0)} new)"
                    )
                st.info(f"Found **{len(links)}** unique product URL(s). Scraping products now...")
                status_container.caption(f"Scraping **{len(links)}** product(s)...")
                added_count = scrape_and_add_links_to_list(
                    links,
                    progress_bar=progress_bar,
                    status_container=status_container,
                )
                progress_bar.progress(1.0, text="Done.")
                status_container.caption("Finished.")
                st.success(
                    f"✅ Category fetch complete. Added **{added_count}** product(s) "
                    f"(from **{len(links)}** URL(s) on pages "
                    f"{int(category_start_page)}–{int(category_end_page)})."
                )
                if added_count < len(links):
                    st.info(f"{len(links) - added_count} URL(s) were skipped (duplicates or errors).")
                st.session_state.url_input_counter += 1
                st.rerun()

    if quick_add_button:
        if add_mode == "multiple":
            # Multiple mode: sirf Add to List — bulk fetch aur sab list me add
            links = [l.strip() for l in (url_input or "").split('\n') if l.strip()]
            if not links:
                st.warning("Please enter at least one product URL")
            else:
                total = len(links)
                progress_bar = st.progress(0.0, text="Starting...")
                status_container = st.empty()
                added_count = scrape_and_add_links_to_list(
                    links,
                    progress_bar=progress_bar,
                    status_container=status_container,
                )
                progress_bar.progress(1.0, text="Done.")
                status_container.caption("Finished.")
                st.success(f"✅ **Bulk fetch complete.** Added **{added_count}** product(s) to the list (of {total} URL(s) processed).")
                if added_count < total:
                    st.info(f"{total - added_count} URL(s) were skipped (duplicates or errors).")
                st.rerun()
        elif add_mode == "single":
            # Single mode: first URL add to list
            first_url = (url_input or "").strip().split('\n')[0].strip() if url_input else ""
            if first_url:
                with st.spinner("Fetching and adding product to list... This may take a few seconds."):
                    product_data = scrape_markaz_product(first_url)
                    if product_data['status'] == 'success':
                        fetched_price = float(product_data.get('price', 0))
                        default_variant_adjustment, default_compare_at_adjustment = (
                            get_default_price_adjustments(fetched_price)
                        )
                        product_data['variant_price_adjustment'] = default_variant_adjustment
                        product_data['compare_at_price_adjustment'] = default_compare_at_adjustment
                        st.session_state.products_list.append(product_data)
                        st.session_state.processed_urls.add(first_url)
                        st.session_state.url_input_counter += 1
                        saved_ok, saved_error = save_product_to_supabase(product_data)
                        success_message = f"Product **{product_data['title']}** has been added to your list with default pricing rules."
                        if saved_ok:
                            success_message += " Saved to Supabase tracked products."
                        else:
                            success_message += f" Supabase save failed: {saved_error}"
                        st.success(success_message)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to scrape: {product_data['status']}")
            else:
                st.warning("Please enter at least one product URL")
    
    # STEP 2: Display product details in compact single-row 3-column layout
    if st.session_state.fetched_product_data:
        product_data = st.session_state.fetched_product_data
        
        st.divider()
        
        # Create 3 columns: [3, 4, 5] ratio for single row layout
        col1, col2, col3 = st.columns([3, 4, 5])
        
        # Column 1: Product Image
        with col1:
            if product_data.get('image_urls'):
                show_product_image(product_data['image_urls'][0], width='stretch', caption="Product Image")
        
        # Column 2: Product Details (compact format)
        with col2:
            st.markdown(f"**Title:** {product_data['title']}")
            if product_data.get('base_sku'):
                st.markdown(f"**SKU:** {product_data['base_sku']}")
            if product_data.get('variants') and len(product_data['variants']) > 0:
                variants_display = ', '.join(product_data['variants'])
                st.markdown(f"**{product_data.get('option1_name', 'Size')}:** {variants_display}")
            st.markdown(f"**Price:** Rs. {product_data['price']}")
        
        # Column 3: Set Pricing section (all pricing inputs)
        with col3:
            # Show fetched price
            fetched_price = float(product_data.get('price', 0))
            st.info(f"**Fetched Price:** Rs. {fetched_price:,.2f}")
            
            # Calculate default values based on pricing rules
            default_variant_adjustment, default_compare_at_adjustment = (
                get_default_price_adjustments(fetched_price)
            )
            
            # Variant Price Adjustment (with default value from pricing rules)
            variant_adjustment = st.number_input(
                "Variant Price Adjustment",
                value=default_variant_adjustment,
                step=100.0,
                help="Enter the amount to add to fetched price for Variant Price. Final Variant Price = Fetched Price + This Value",
                key="variant_price_adjustment"
            )
            final_variant_price = fetched_price + variant_adjustment
            st.markdown(f"**Final Variant:** Rs. {final_variant_price:,.2f}")
            
            # Compare At Price Adjustment (with default value from pricing rules)
            compare_at_adjustment = st.number_input(
                "Compare At Price Adjustment",
                value=default_compare_at_adjustment,
                step=100.0,
                help="Enter the amount to add to fetched price for Compare At Price. Final Compare At Price = Fetched Price + This Value",
                key="compare_at_price_adjustment"
            )
            final_compare_at_price = fetched_price + compare_at_adjustment
            st.markdown(f"**Final Compare At:** Rs. {final_compare_at_price:,.2f}")
        
        st.divider()
        
        # Action buttons in new row below (half-width each)
        col1, col2 = st.columns(2)
        with col1:
            add_to_list_button = st.button("✅ Add to List", type="primary", width='stretch', key="add_to_list")
        with col2:
            cancel_button = st.button("❌ Cancel", width='stretch', key="cancel_preview")
        
        # Handle "Add to List" button click
        if add_to_list_button:
            # Create a deep copy of product data to avoid modifying the original
            product_to_add = copy.deepcopy(product_data)
            
            # Store price adjustments in product data
            product_to_add['variant_price_adjustment'] = variant_adjustment
            product_to_add['compare_at_price_adjustment'] = compare_at_adjustment
            
            # Add product to the main conversion list (st.session_state.products_list)
            st.session_state.products_list.append(product_to_add)
            if product_to_add.get("url"):
                st.session_state.processed_urls.add(product_to_add["url"])

            saved_ok, saved_error = save_product_to_supabase(product_to_add)
            
            # Clear fetched data from session state (preview section clears)
            st.session_state.fetched_product_data = None
            st.session_state.show_product_dialog = False
            
            # Increment counter to create new widget key (this clears the input)
            st.session_state.url_input_counter += 1
            
            success_message = f"Product **{product_to_add['title']}** has been added to your conversion list."
            if saved_ok:
                success_message += " Saved to Supabase tracked products."
            else:
                success_message += f" Supabase save failed: {saved_error}"
            st.success(success_message)
            
            # Refresh to show updated main list and clear preview
            st.rerun()
        
        # Handle "Cancel" button click
        if cancel_button:
            # Clear fetched data from screen
            st.session_state.fetched_product_data = None
            st.session_state.show_product_dialog = False
            st.rerun()
    
    st.divider()
    
    # Product list display
    if st.session_state.products_list:
        st.header(f"Product List ({len(st.session_state.products_list)} products)")
        
        # Display products
        for idx, product in enumerate(st.session_state.products_list):
            # Initialize edit state for each product
            edit_key = f"edit_{idx}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False
            
            with st.expander(f"Product {idx + 1}: {product['title']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Title:**", product['title'])
                    if product.get('base_sku'):
                        st.write("**Base SKU:**", product['base_sku'])
                    if product.get('variants') and len(product['variants']) > 0:
                        variants_display = ', '.join(product['variants'])
                        st.write(f"**{product.get('option1_name', 'Variants')}:**", variants_display)
                    st.write("**Fetched Price:**", f"Rs. {product['price']}")
                    
                    # Calculate and display Variant Price and Compare At Price
                    fetched_price = float(product.get('price', 0))
                    variant_adjustment = product.get('variant_price_adjustment', 0)
                    compare_at_adjustment = product.get('compare_at_price_adjustment', 0)
                    
                    final_variant_price = fetched_price + variant_adjustment
                    final_compare_at_price = fetched_price + compare_at_adjustment
                    
                    st.write("**Variant Price:**", f"Rs. {final_variant_price:,.2f}")
                    st.write("**Compare At Price:**", f"Rs. {final_compare_at_price:,.2f}")
                    st.write("**URL:**", product['url'])
                
                with col2:
                    st.write("**Description:**", product['description'][:300] + "..." if len(product['description']) > 300 else product['description'])
                    st.write("**Images Found:**", len(product['image_urls']))
                    if product['image_urls']:
                        show_product_image(product['image_urls'][0], width=200, caption="First Image")
                
                st.divider()
                
                # Edit mode: Show input fields for price adjustments
                if st.session_state[edit_key]:
                    st.subheader("✏️ Edit Pricing")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_variant_adjustment = st.number_input(
                            "Variant Price Adjustment",
                            value=float(variant_adjustment),
                            step=100.0,
                            key=f"edit_variant_{idx}"
                        )
                        new_final_variant = fetched_price + new_variant_adjustment
                        st.write(f"**New Variant Price:** Rs. {new_final_variant:,.2f}")
                    
                    with col2:
                        new_compare_at_adjustment = st.number_input(
                            "Compare At Price Adjustment",
                            value=float(compare_at_adjustment),
                            step=100.0,
                            key=f"edit_compare_{idx}"
                        )
                        new_final_compare = fetched_price + new_compare_at_adjustment
                        st.write(f"**New Compare At Price:** Rs. {new_final_compare:,.2f}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Save Changes", key=f"save_{idx}", width='stretch'):
                            product['variant_price_adjustment'] = new_variant_adjustment
                            product['compare_at_price_adjustment'] = new_compare_at_adjustment
                            st.session_state[edit_key] = False
                            st.success("✅ Prices updated successfully!")
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_edit_{idx}", width='stretch'):
                            st.session_state[edit_key] = False
                            st.rerun()
                    
                    st.divider()
                
                # Action buttons: Edit and Remove
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✏️ Edit Prices", key=f"edit_btn_{idx}", width='stretch'):
                        st.session_state[edit_key] = True
                        st.rerun()
                with col2:
                    if st.button(f"🗑️ Remove Product {idx + 1}", key=f"remove_{idx}", width='stretch'):
                        st.session_state.products_list.pop(idx)
                        st.rerun()
        
        st.divider()
        
        st.header("Export to Shopify")
        
        export_col1, export_col2 = st.columns(2)
        with export_col1:
            publish_all = st.button(
                "Publish All to Shopify",
                type="primary",
                key="publish_all_to_shopify",
                disabled=not is_shopify_configured(),
                help="Create products directly on your Shopify store (no CSV needed).",
            )
        with export_col2:
            pass

        if publish_all:
            if not is_shopify_configured():
                st.warning("Shopify is not configured. Add credentials to `.streamlit/secrets.toml`.")
            else:
                with st.spinner(f"Publishing {len(st.session_state.products_list)} product(s) to Shopify..."):
                    publish_results = publish_products_to_shopify(st.session_state.products_list)
                created_count, updated_count, publish_failed, publish_warnings = apply_shopify_publish_results(publish_results)
                store_shopify_publish_feedback(created_count, updated_count, publish_failed, publish_warnings)
                st.rerun()

        st.subheader("Download Shopify CSV")
        
        # Define exact column order as required by Shopify
        column_order = [
            'Handle', 'Title', 'Body (HTML)', 'Vendor', 'Product Category', 'Type',
            'Tags', 'Published', 'Option1 Name', 'Option1 Value', 'Option2 Name', 'Option2 Value',
            'Option3 Name', 'Option3 Value', 'Variant SKU', 'Variant Grams', 'Variant Inventory Tracker',
            'Variant Inventory Qty', 'Variant Inventory Policy', 'Variant Fulfillment Service',
            'Variant Price', 'Variant Compare At Price', 'Variant Requires Shipping', 'Variant Taxable',
            'Variant Barcode', 'Image Src', 'Image Position', 'Image Alt Text', 'Variant Image', 'Gift Card',
            'SEO Title', 'SEO Description', 'Google Shopping / Google Product Category',
            'Google Shopping / Gender', 'Google Shopping / Age Group', 'Google Shopping / MPN',
            'Google Shopping / Condition', 'Google Shopping / Custom Product',
            'Google Shopping / Custom Label 0', 'Google Shopping / Custom Label 1',
            'Google Shopping / Custom Label 2', 'Google Shopping / Custom Label 3',
            'Google Shopping / Custom Label 4',
            'Age group (product.metafields.shopify.age-group)',
            'Target gender (product.metafields.shopify.target-gender)',
            'Variant Weight Unit', 'Variant Tax Code',
            'Cost per item', 'Price / International', 'Compare At Price / International', 'Status'
        ]
        
        # Convert all products to Shopify format
        all_rows = []
        for product in st.session_state.products_list:
            rows = format_for_shopify(product)
            all_rows.extend(rows)
        
        # Create DataFrame with exact column order
        df = pd.DataFrame(all_rows)
        
        # Ensure all columns exist (add missing columns with empty values)
        for col in column_order:
            if col not in df.columns:
                df[col] = ''
        
        # Reorder columns to match exact order
        df = df[column_order]
        
        # Convert to CSV
        csv = df.to_csv(index=False)
        
        # Download button
        st.download_button(
            label="📥 Download Shopify CSV",
            data=csv,
            file_name="shopify_products.csv",
            mime="text/csv",
            type="primary",
            width='stretch'
        )
        
        # Show preview
        st.subheader("CSV Preview")
        if _IS_DEMO:
            st.caption("Demo mode — showing first 5 rows only.")
            st.dataframe(df.head(5), width='stretch')
        else:
            st.dataframe(df, width='stretch')
        
        # Clear all button
        if st.button("Clear All Products", type="secondary"):
            st.session_state.products_list = []
            st.session_state.processed_urls = set()
            st.rerun()
    else:
        st.info("👈 Enter a product URL above and click 'Add to List' to get started!")
        st.markdown("""
        ### How to use:
        1. Paste a Markaz product URL in the input field above
        2. Click "Add to List" to scrape and add the product
        3. Repeat for multiple products
        4. Click "Download Shopify CSV" to export all products
        """)


def main():
    render_logout_control()
    st.title("Markaz to Shopify CSV Converter")
    st.markdown("Scrape Markaz product data and convert to Shopify-compatible CSV format.")

    render_shopify_publish_feedback()

    # Radio instead of st.tabs: Streamlit runs EVERY tab body on each rerun,
    # which was flooding Supabase list_tracked_products on Converter clicks.
    selected_section = st.radio(
        "Section",
        options=["Shopify Converter", "Tracked Products"],
        horizontal=True,
        key="main_section",
        label_visibility="collapsed",
    )

    if selected_section == "Shopify Converter":
        render_converter_tab()
    else:
        render_tracked_products_tab()


if __name__ == "__main__":
    if not is_authenticated():
        render_login_page()
        st.stop()
    main()
