"""Standalone demo UI — does NOT import production app.py (avoids pandas/playwright crash)."""

import streamlit as st

from demo_mode.demo_guard import DEMO_SHOPIFY_ALERT
from demo_mode.demo_markaz import fetch_demo_products_from_tracked_rows
from demo_mode.demo_scrape import scrape_markaz_product_demo
from demo_mode.demo_shopify import (
    delete_tracked_row_from_shopify,
    fetch_shopify_status_map,
    publish_products_to_shopify,
    sync_tracked_rows_to_shopify,
)
from demo_mode.demo_store import (
    delete_tracked_product,
    list_tracked_products,
    update_tracked_shopify_metadata,
    update_tracked_stock_status,
    upsert_tracked_product,
)
from pricing_rules import get_default_price_adjustments
from shopify_publish import generate_shopify_handle


def _init_session():
    if 'products_list' not in st.session_state:
        st.session_state.products_list = []
    if 'processed_urls' not in st.session_state:
        st.session_state.processed_urls = set()
    if 'fetched_product_data' not in st.session_state:
        st.session_state.fetched_product_data = None
    if 'url_input_counter' not in st.session_state:
        st.session_state.url_input_counter = 0
    if 'add_mode' not in st.session_state:
        st.session_state.add_mode = 'single'
    if 'shopify_status_map' not in st.session_state:
        st.session_state.shopify_status_map = {}


def _save_to_tracked(product):
    markaz_url = (product or {}).get('url', '').strip()
    if not markaz_url:
        return False, 'Product URL missing'

    handle = generate_shopify_handle(
        product.get('title', ''),
        product.get('base_sku', ''),
    )
    if not handle.startswith('demo-'):
        handle = f'demo-{handle}'

    upsert_tracked_product(
        markaz_url=markaz_url,
        stock_status=product.get('stock_status', 'unknown'),
        title=product.get('title'),
        shopify_handle=handle,
    )
    return True, None


def _apply_pricing(product):
    price = float(product.get('price', 0))
    variant_adj, compare_adj = get_default_price_adjustments(price)
    product['variant_price_adjustment'] = variant_adj
    product['compare_at_price_adjustment'] = compare_adj
    return product


def _shopify_status_label(snapshot):
    if not snapshot or not snapshot.get('on_shopify'):
        return 'Not on Shopify'
    status = snapshot.get('status') or 'unknown'
    return status.title()


def render_converter_tab():
    st.subheader('Add Products (Demo)')
    st.caption('Paste a Markaz URL — preview is simulated from the link (no live scrape).')

    url_input = st.text_input(
        'Product URL',
        placeholder='https://www.markaz.app/shop/product/...',
        key=f'demo_url_{st.session_state.url_input_counter}',
    )

    col1, col2 = st.columns(2)
    with col1:
        fetch_btn = st.button('Fetch Product Data', type='secondary', key='demo_fetch')
    with col2:
        add_btn = st.button('Add to List', type='primary', key='demo_add')

    if fetch_btn and url_input:
        product = scrape_markaz_product_demo(url_input.strip())
        if product.get('status') == 'success':
            st.session_state.fetched_product_data = product
            st.info('Demo preview simulated from your pasted URL.')
            st.rerun()
        else:
            st.error(product.get('status', 'Fetch failed'))

    if add_btn and url_input:
        product = scrape_markaz_product_demo(url_input.strip())
        if product.get('status') == 'success':
            product = _apply_pricing(product)
            st.session_state.products_list.append(product)
            st.session_state.processed_urls.add(product['url'])
            saved_ok, err = _save_to_tracked(product)
            st.session_state.url_input_counter += 1
            st.session_state.fetched_product_data = None
            msg = f"Added **{product['title']}** (demo)."
            if not saved_ok:
                msg += f' Track save failed: {err}'
            st.success(msg)
            st.rerun()
        else:
            st.error(product.get('status', 'Add failed'))

    if st.session_state.fetched_product_data:
        product = st.session_state.fetched_product_data
        st.divider()
        st.markdown(f"**Title:** {product.get('title')}")
        st.markdown(f"**Price:** Rs. {float(product.get('price', 0)):,.2f}")
        st.markdown(f"**SKU:** {product.get('base_sku')}")
        st.caption(f"Image URL: {product.get('image_urls', [''])[0]}")

        if st.button('Add preview to list', key='demo_add_preview'):
            product = _apply_pricing(dict(product))
            st.session_state.products_list.append(product)
            st.session_state.processed_urls.add(product['url'])
            _save_to_tracked(product)
            st.session_state.fetched_product_data = None
            st.session_state.url_input_counter += 1
            st.rerun()

    st.divider()
    products = st.session_state.products_list
    if not products:
        st.info('No products in converter list yet.')
        return

    st.header(f'Product List ({len(products)})')
    for idx, product in enumerate(products):
        with st.expander(f"{idx + 1}. {product.get('title', 'Product')}", expanded=False):
            st.write('URL:', product.get('url'))
            st.write('Price:', f"Rs. {float(product.get('price', 0)):,.2f}")

    st.divider()
    if st.button('Publish All to Shopify (Demo)', type='primary', key='demo_publish_all'):
        results = publish_products_to_shopify(products)
        created = sum(1 for r in results if r.get('success') and r.get('action') == 'created')
        updated = sum(1 for r in results if r.get('success') and r.get('action') == 'updated')
        st.warning(DEMO_SHOPIFY_ALERT)
        st.success(f'Demo publish simulated. Created: {created}, Updated: {updated}.')


def render_tracked_tab():
    st.subheader('Tracked Products (Demo)')
    try:
        rows = list_tracked_products()
    except Exception as exc:
        st.error(f'Could not load demo tracked products: {exc}')
        return

    if not rows:
        st.info('No tracked products. Add one from the Converter tab.')
        return

    status_map = fetch_shopify_status_map(rows)
    st.session_state.shopify_status_map = status_map

    sync_col, pub_col, refresh_col = st.columns(3)
    with sync_col:
        sync_btn = st.button('Sync Stock (Demo)', key='demo_sync_all')
    with pub_col:
        pub_btn = st.button('Publish to Shopify (Demo)', key='demo_pub_all')
    with refresh_col:
        refresh_btn = st.button('Refresh Status (Demo)', key='demo_refresh_all')

    if refresh_btn:
        for row in rows:
            scraped = scrape_markaz_product_demo(row['markaz_url'])
            if scraped.get('status') == 'success':
                update_tracked_stock_status(
                    row['markaz_url'],
                    scraped.get('stock_status', 'unknown'),
                    title=scraped.get('title'),
                )
        st.success('Demo stock status refreshed (simulated).')
        st.rerun()

    if sync_btn:
        results = sync_tracked_rows_to_shopify(rows)
        ok = sum(1 for r in results if r.get('success'))
        st.warning(DEMO_SHOPIFY_ALERT)
        st.success(f'Demo sync simulated for {ok} product(s).')
        st.rerun()

    if pub_btn:
        products, _, _ = fetch_demo_products_from_tracked_rows(rows)
        results = publish_products_to_shopify(products)
        ok = sum(1 for r in results if r.get('success'))
        st.warning(DEMO_SHOPIFY_ALERT)
        st.success(f'Demo publish simulated for {ok} product(s).')
        st.rerun()

    for row in rows:
        key = row.get('markaz_url') or row.get('id')
        snapshot = status_map.get(key, {})
        title = row.get('title') or 'Untitled'
        with st.expander(f"{title} — {_shopify_status_label(snapshot)}", expanded=False):
            st.write('URL:', row.get('markaz_url'))
            st.write('Stock:', row.get('stock_status', 'unknown'))
            st.write('Shopify handle:', row.get('shopify_handle') or '—')
            st.write('Shopify ID:', row.get('shopify_product_id') or '—')

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button('Publish', key=f'demo_pub_{row["id"]}'):
                    products, _, _ = fetch_demo_products_from_tracked_rows([row])
                    publish_products_to_shopify(products)
                    st.warning(DEMO_SHOPIFY_ALERT)
                    st.rerun()
            with c2:
                if st.button('Sync Stock', key=f'demo_sync_{row["id"]}'):
                    sync_tracked_rows_to_shopify([row])
                    st.warning(DEMO_SHOPIFY_ALERT)
                    st.rerun()
            with c3:
                if st.button('Delete', key=f'demo_del_{row["id"]}'):
                    delete_tracked_row_from_shopify(row)
                    delete_tracked_product(row['markaz_url'])
                    st.success('Removed from demo tracked list.')
                    st.rerun()


def run():
    _init_session()
    st.title('Markaz to Shopify CSV Converter')
    st.caption('Demo environment — simulated data only.')

    converter_tab, tracked_tab = st.tabs(['Shopify Converter', 'Tracked Products'])
    with converter_tab:
        render_converter_tab()
    with tracked_tab:
        render_tracked_tab()
