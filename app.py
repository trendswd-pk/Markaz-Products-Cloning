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
from supabase_config import is_supabase_configured
from supabase_store import (
    delete_tracked_product,
    list_tracked_products,
    update_tracked_shopify_metadata,
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
else:
    from playwright.sync_api import sync_playwright
    from markaz_scraper import launch_browser_for_serverless, scrape_product_from_page, scrape_markaz_product

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
    st.session_state.add_mode = 'multiple'  # default: multiple; 'single' = one URL, 'multiple' = bulk URLs
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
    
    # Extract breadcrumb data for Standard Product Type and Tags
    breadcrumb_items = product.get('breadcrumb_items', [])
    standard_product_type = ''
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
        
        # Standard Product Type: Set this to the last item of this cleaned list (e.g., 'Personal Care')
        if breadcrumb_items:
            # Last item of the cleaned list
            product_type = breadcrumb_items[-1].strip()
            # Remove special characters except spaces and hyphens
            standard_product_type = re.sub(r'[^a-zA-Z0-9\s-]', '', product_type).strip()
        else:
            standard_product_type = ''
    
    # Create row with all columns in exact order
    row = {
        'Handle': handle,
        'Title': title,
        'Body (HTML)': body_html,
        'Vendor': 'Markaz' if is_first_variant else '',
        'Standard Product Type': standard_product_type if is_first_variant else '',
        'Custom Product Type': '',
        'Tags': tags if is_first_variant else '',
        'Published': 'TRUE' if is_first_variant else '',
        'Option1 Name': option1_name,
        'Option1 Value': option1_value,
        'Option2 Name': '',
        'Option2 Value': '',
        'Option3 Name': '',
        'Option3 Value': '',
        'Variant SKU': variant_sku,
        'Variant Grams': '',
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
        'Gift Card': 'FALSE' if is_first_variant else '',
        'SEO Title': title if is_first_variant else '',
        'SEO Description': product['description'][:160] if is_first_variant and product.get('description') else '',
        'Google Shopping / Google Product Category': '',
        'Google Shopping / Gender': '',
        'Google Shopping / Age Group': '',
        'Google Shopping / MPN': '',
        'Google Shopping / Condition': 'new' if is_first_variant else '',
        'Google Shopping / Custom Product': 'FALSE' if is_first_variant else '',
        'Google Shopping / Custom Label 0': '',
        'Google Shopping / Custom Label 1': '',
        'Google Shopping / Custom Label 2': '',
        'Google Shopping / Custom Label 3': '',
        'Google Shopping / Custom Label 4': '',
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

    markaz_url = (product_data or {}).get('url', '').strip()
    if not markaz_url:
        return False, 'Product URL missing'

    shopify_handle = generate_unique_handle(
        product_data.get('title', ''),
        product_data.get('base_sku', ''),
    )

    try:
        upsert_tracked_product(
            markaz_url=markaz_url,
            stock_status=product_data.get('stock_status', 'unknown'),
            title=product_data.get('title'),
            shopify_handle=shopify_handle,
        )
        return True, None
    except Exception as exc:
        return False, str(exc)


def update_tracked_product_from_scrape(markaz_url, scraped_data):
    """Update Supabase row after a live Markaz refresh."""
    shopify_handle = generate_unique_handle(
        scraped_data.get('title', ''),
        scraped_data.get('base_sku', ''),
    )
    return update_tracked_stock_status(
        markaz_url,
        scraped_data.get('stock_status', 'unknown'),
        title=scraped_data.get('title'),
        shopify_handle=shopify_handle,
    )


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


def format_stock_status_label(stock_status):
    labels = {
        'in_stock': 'In Stock',
        'out_of_stock': 'Out of Stock',
        'unknown': 'Unknown',
    }
    return labels.get(stock_status, stock_status or 'Unknown')


def format_shopify_status_label(snapshot):
    if not snapshot or not snapshot.get('on_shopify'):
        return 'Not on Shopify'

    status = (snapshot.get('status') or 'unknown').lower()
    labels = {
        'active': 'Shopify: Active',
        'draft': 'Shopify: Draft',
        'archived': 'Shopify: Archived',
    }
    return labels.get(status, f'Shopify: {status.title()}')


def format_shopify_status_detail(snapshot):
    if not snapshot or not snapshot.get('on_shopify'):
        if snapshot and snapshot.get('error'):
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


def load_shopify_status_map(tracked_rows, force_refresh=False):
    if not is_shopify_configured():
        return {}

    if force_refresh or 'shopify_status_map' not in st.session_state:
        st.session_state.shopify_status_map = fetch_shopify_status_map(tracked_rows)

    return st.session_state.shopify_status_map


def refresh_shopify_status_for_row(row):
    if not is_shopify_configured():
        return False

    row_key = row.get('markaz_url') or row.get('id')
    if 'shopify_status_map' not in st.session_state:
        st.session_state.shopify_status_map = {}

    st.session_state.shopify_status_map.update(fetch_shopify_status_map([row]))
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


SHOPIFY_ICON_PATH = Path(__file__).resolve().parent / 'assets' / 'shopify-icon.svg'


def render_tracked_products_heading():
    heading_col, icon_col = st.columns([0.94, 0.06], vertical_alignment="center")
    with heading_col:
        st.subheader("Tracked Products")
    with icon_col:
        if is_shopify_configured():
            render_shopify_tab_icon()


def apply_shopify_sync_results(results):
    synced_count = 0
    failed_results = []

    for result in results:
        if result.get('success'):
            synced_count += 1
            markaz_url = result.get('markaz_url')
            if markaz_url:
                update_tracked_shopify_metadata(
                    markaz_url,
                    shopify_product_id=result.get('shopify_product_id'),
                    shopify_handle=result.get('shopify_handle'),
                )
        else:
            failed_results.append(result)

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

    for result in results:
        if result.get('success'):
            if result.get('action') == 'created':
                created_count += 1
            else:
                updated_count += 1

            if result.get('stock_sync_warning'):
                warning_results.append(result)

            markaz_url = result.get('markaz_url')
            if markaz_url and is_supabase_configured():
                upsert_tracked_product(
                    markaz_url=markaz_url,
                    stock_status=result.get('stock_status', 'unknown'),
                    title=result.get('title'),
                    shopify_handle=result.get('shopify_handle'),
                )
                update_tracked_shopify_metadata(
                    markaz_url,
                    shopify_product_id=result.get('shopify_product_id'),
                    shopify_handle=result.get('shopify_handle'),
                )
        else:
            failed_results.append(result)

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
        st.warning(
            f"**{label}** published, but stock/inventory was not synced.{images_note}\n\n"
            f"{format_shopify_error_message(result.get('stock_sync_warning'))}"
        )

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
        tracked_rows = list_tracked_products()
    except Exception as exc:
        st.error(f"Could not load tracked products from Supabase: {exc}")
        return

    if not tracked_rows:
        st.info("No tracked products yet. Add a product in the Converter tab and it will appear here automatically.")
        return

    stock_filter = st.radio(
        "Filter by stock status",
        options=["All", "In Stock", "Out of Stock", "Unknown"],
        horizontal=True,
        key="tracked_stock_filter",
    )
    filtered_rows = get_filtered_tracked_rows(tracked_rows, stock_filter)
    shopify_status_map = load_shopify_status_map(tracked_rows)

    auto_sync_shopify = st.checkbox(
        "Auto-sync to Shopify after Refresh All Status",
        value=True,
        key="shopify_auto_sync_on_refresh",
        disabled=not is_shopify_configured(),
    )

    refresh_col, shopify_refresh_col, send_col, sync_col, publish_col = st.columns(5)
    with refresh_col:
        refresh_all = st.button("Refresh All Status", type="secondary", key="refresh_all_tracked")
    with shopify_refresh_col:
        refresh_shopify_status = st.button(
            "Refresh Shopify Status",
            type="secondary",
            key="refresh_shopify_status_map",
            disabled=not is_shopify_configured(),
            help="Fetch latest product status from Shopify for all tracked products.",
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

    if refresh_shopify_status:
        load_shopify_status_map(tracked_rows, force_refresh=True)
        st.rerun()

    if refresh_all:
        progress = st.progress(0.0, text="Refreshing stock status...")
        for index, row in enumerate(tracked_rows):
            progress.progress((index + 1) / len(tracked_rows), text=f"Checking {index + 1} of {len(tracked_rows)}")
            scraped = scrape_markaz_product(row['markaz_url'])
            if scraped.get('status') == 'success':
                update_tracked_product_from_scrape(row['markaz_url'], scraped)
        progress.progress(1.0, text="Done.")
        st.success("Stock status refreshed for all tracked products.")

        if auto_sync_shopify and is_shopify_configured():
            refreshed_rows = list_tracked_products()
            sync_results = sync_tracked_rows_to_shopify(refreshed_rows)
            synced_count, failed_results = apply_shopify_sync_results(sync_results)
            show_shopify_sync_summary(synced_count, failed_results)

        invalidate_shopify_status_cache()
        st.rerun()

    if sync_to_shopify:
        if not is_shopify_configured():
            st.warning("Shopify is not configured. Add credentials to `.streamlit/secrets.toml`.")
        elif not filtered_rows:
            st.warning(f"No products with status **{stock_filter}** to sync.")
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
            st.warning(f"No products with status **{stock_filter}** to publish.")
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
            st.warning(f"No products with status **{stock_filter}** to send.")
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
                st.session_state.converter_import_message = (
                    f"Loaded **{len(products)}** product(s) with filter **{stock_filter}**. "
                    "Open the **Shopify Converter** tab to review and download CSV."
                )
                st.success(st.session_state.converter_import_message)
            else:
                st.error("No products could be fetched. Please try again.")

            for link, error in failed:
                st.warning(f"Skipped: {link[:70]}... — {error}")

            if products:
                st.rerun()

    if stock_filter == "All":
        st.markdown(f"**{len(tracked_rows)}** saved URL(s)")
    else:
        st.markdown(f"**{len(filtered_rows)}** shown of **{len(tracked_rows)}** saved URL(s)")

    render_shopify_status_summary(tracked_rows, shopify_status_map)

    if not filtered_rows:
        st.info(f"No products with status **{stock_filter}**.")
        return

    for row in filtered_rows:
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
                st.caption("Handle is saved locally but product was not found on Shopify.")

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
    
    # Pehle 2 col = title, 3rd col = Single, 4th col = Multiple, baaki merge/empty — sab left pe pass pass
    c_title, c_single, c_multi, c_empty = st.columns([2, 1, 1, 6])
    with c_title:
        st.subheader("Add Products")
    with c_single:
        btn_single = st.button("Single", key="mode_single", help="Fetch one product at a time")
    with c_multi:
        btn_multi = st.button("Multiple", key="mode_multiple", help="Fetch multiple products (paste many URLs)")
    with c_empty:
        pass  # baaki empty — text aur buttons left side pe hi
    if btn_single:
        st.session_state.add_mode = "single"
        st.rerun()
    if btn_multi:
        st.session_state.add_mode = "multiple"
        st.rerun()
    # Show current mode hint
    if st.session_state.add_mode == "single":
        st.caption("Single product mode — enter one URL below.")
    else:
        st.caption("Multiple products mode — paste one URL per line below.")
    # Initialize URL input counter for unique keys
    if 'url_input_counter' not in st.session_state:
        st.session_state.url_input_counter = 0
    # Input: single line (Single mode) or text area (Multiple mode)
    if st.session_state.add_mode == "single":
        url_input = st.text_input(
            "Product URL",
            placeholder="https://www.markaz.app/shop/product/...",
            key=f"product_url_input_{st.session_state.url_input_counter}"
        )
    else:
        url_input = st.text_area(
            "Paste Multiple Product URLs (One per line)",
            placeholder="https://www.markaz.app/shop/product/...\nhttps://www.markaz.app/shop/product/...",
            key=f"product_url_input_{st.session_state.url_input_counter}",
            height=120
        )
    
    # Add Enter key listener to trigger Add to List button (for single-line paste)
    if not _IS_DEMO:
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
    
    # Buttons: Single mode = Add to List + Fetch Product Data; Multiple mode = sirf Add to List
    if st.session_state.add_mode == "single":
        col1, col2 = st.columns(2)
        with col1:
            quick_add_button = st.button("✅ Add to List", type="primary", width='stretch', key="quick_add_button")
        with col2:
            fetch_button = st.button("📥 Fetch Product Data", type="secondary", width='stretch')
    else:
        quick_add_button = st.button("✅ Add to List", type="primary", width='stretch', key="quick_add_button")
        fetch_button = False

    if fetch_button and url_input and st.session_state.add_mode == "single":
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

    if quick_add_button:
        if st.session_state.add_mode == "multiple":
            # Multiple mode: sirf Add to List — bulk fetch aur sab list me add
            links = [l.strip() for l in (url_input or "").split('\n') if l.strip()]
            if not links:
                st.warning("Please enter at least one product URL")
            else:
                total = len(links)
                progress_bar = st.progress(0.0, text="Starting...")
                status_container = st.empty()
                added_count = 0
                if _IS_DEMO:
                    for i, link in enumerate(links):
                        status_container.caption(f"**Link {i + 1} of {total}** — fetching (demo)...")
                        progress_bar.progress((i + 1) / total, text=f"Link {i + 1} of {total}")
                        if link in st.session_state.processed_urls:
                            st.warning(f"⚠️ Skipped (already added): {link[:60]}...")
                            continue
                        try:
                            new_product_data = scrape_markaz_product(link)
                            if new_product_data.get("status") == "success":
                                fetched_price = float(new_product_data.get("price", 0))
                                default_variant_adjustment, default_compare_at_adjustment = (
                                    get_default_price_adjustments(fetched_price)
                                )
                                new_product_data["variant_price_adjustment"] = default_variant_adjustment
                                new_product_data["compare_at_price_adjustment"] = default_compare_at_adjustment
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
                else:
                    with sync_playwright() as p:
                        browser = launch_browser_for_serverless(p)
                        for i, link in enumerate(links):
                            status_container.caption(f"**Link {i + 1} of {total}** — fetching...")
                            progress_bar.progress((i + 1) / total, text=f"Link {i + 1} of {total}")
                            if link in st.session_state.processed_urls:
                                st.warning(f"⚠️ Skipped (already added): {link[:60]}...")
                                continue
                            context = None
                            try:
                                context = browser.new_context(
                                    permissions=[],
                                    ignore_https_errors=True,
                                    viewport={'width': 1920, 'height': 1080}
                                )
                                page = context.new_page()
                                new_product_data = scrape_product_from_page(page, link)
                                if new_product_data.get("status") == "success":
                                    fetched_price = float(new_product_data.get("price", 0))
                                    default_variant_adjustment, default_compare_at_adjustment = (
                                        get_default_price_adjustments(fetched_price)
                                    )
                                    new_product_data["variant_price_adjustment"] = default_variant_adjustment
                                    new_product_data["compare_at_price_adjustment"] = default_compare_at_adjustment
                                    st.session_state.products_list.append(new_product_data)
                                    st.session_state.processed_urls.add(link)
                                    saved_ok, saved_error = save_product_to_supabase(new_product_data)
                                    if not saved_ok:
                                        st.warning(f"Supabase save failed for {link[:60]}... — {saved_error}")
                                    added_count += 1
                                else:
                                    st.warning(f"⚠️ Skipped (failed): {link[:60]}... — {new_product_data.get('status', 'Unknown error')}")
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
                progress_bar.progress(1.0, text="Done.")
                status_container.caption("Finished.")
                st.success(f"✅ **Bulk fetch complete.** Added **{added_count}** product(s) to the list (of {total} URL(s) processed).")
                if added_count < total:
                    st.info(f"{total - added_count} URL(s) were skipped (duplicates or errors).")
                st.rerun()
        else:
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
            'Handle', 'Title', 'Body (HTML)', 'Vendor', 'Standard Product Type', 'Custom Product Type',
            'Tags', 'Published', 'Option1 Name', 'Option1 Value', 'Option2 Name', 'Option2 Value',
            'Option3 Name', 'Option3 Value', 'Variant SKU', 'Variant Grams', 'Variant Inventory Tracker',
            'Variant Inventory Qty', 'Variant Inventory Policy', 'Variant Fulfillment Service',
            'Variant Price', 'Variant Compare At Price', 'Variant Requires Shipping', 'Variant Taxable',
            'Variant Barcode', 'Image Src', 'Image Position', 'Image Alt Text', 'Gift Card',
            'SEO Title', 'SEO Description', 'Google Shopping / Google Product Category',
            'Google Shopping / Gender', 'Google Shopping / Age Group', 'Google Shopping / MPN',
            'Google Shopping / Condition', 'Google Shopping / Custom Product',
            'Google Shopping / Custom Label 0', 'Google Shopping / Custom Label 1',
            'Google Shopping / Custom Label 2', 'Google Shopping / Custom Label 3',
            'Google Shopping / Custom Label 4', 'Variant Weight Unit', 'Variant Tax Code',
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

    converter_tab, tracked_tab = st.tabs(["Shopify Converter", "Tracked Products"])

    with converter_tab:
        render_converter_tab()

    with tracked_tab:
        render_tracked_products_tab()


if __name__ == "__main__":
    if not is_authenticated():
        render_login_page()
        st.stop()
    main()
