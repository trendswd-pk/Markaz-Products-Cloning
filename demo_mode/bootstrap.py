"""Patch production modules so the main app runs in demo mode."""


def activate_demo_mode():
    import auth
    import auth_config
    import markaz_scraper
    import shopify_config
    import shopify_publish
    import shopify_sync
    import supabase_config
    import supabase_store

    from demo_mode import demo_auth, demo_scrape, demo_shopify, demo_store

    markaz_scraper.scrape_markaz_product = demo_scrape.scrape_markaz_product_demo
    markaz_scraper.scrape_product_from_page = demo_scrape.scrape_product_from_page_demo

    supabase_config.is_supabase_configured = lambda: True

    supabase_store.list_tracked_products = demo_store.list_tracked_products
    supabase_store.get_tracked_product_by_url = demo_store.get_tracked_product_by_url
    supabase_store.get_tracked_product_by_handle = demo_store.get_tracked_product_by_handle
    supabase_store.upsert_tracked_product = demo_store.upsert_tracked_product
    supabase_store.update_tracked_stock_status = demo_store.update_tracked_stock_status
    supabase_store.update_tracked_shopify_metadata = demo_store.update_tracked_shopify_metadata
    supabase_store.delete_tracked_product = demo_store.delete_tracked_product

    shopify_config.is_shopify_configured = lambda: True

    shopify_sync.get_shopify_client = demo_shopify.get_shopify_client
    shopify_sync.fetch_shopify_status_map = demo_shopify.fetch_shopify_status_map
    shopify_sync.sync_tracked_rows_to_shopify = demo_shopify.sync_tracked_rows_to_shopify
    shopify_sync.delete_tracked_row_from_shopify = demo_shopify.delete_tracked_row_from_shopify

    shopify_publish.get_shopify_client = demo_shopify.get_shopify_client
    shopify_publish.publish_product_to_shopify = demo_shopify.publish_product_to_shopify
    shopify_publish.publish_products_to_shopify = demo_shopify.publish_products_to_shopify

    auth_config.is_auth_configured = demo_auth.is_auth_configured
    auth_config.get_auth_credentials = demo_auth.get_auth_credentials
    auth.render_login_page = demo_auth.render_login_page
    auth.verify_login = demo_auth.verify_login


def rebind_app_module():
    """Re-bind names imported into app.py (guards against stale module references)."""
    import app as app_module
    from demo_mode import demo_scrape, demo_shopify, demo_store

    app_module.scrape_markaz_product = demo_scrape.scrape_markaz_product_demo
    app_module.scrape_product_from_page = demo_scrape.scrape_product_from_page_demo
    app_module.publish_products_to_shopify = demo_shopify.publish_products_to_shopify
    app_module.sync_tracked_rows_to_shopify = demo_shopify.sync_tracked_rows_to_shopify
    app_module.fetch_shopify_status_map = demo_shopify.fetch_shopify_status_map
    app_module.delete_tracked_row_from_shopify = demo_shopify.delete_tracked_row_from_shopify
    app_module.get_shopify_client = demo_shopify.get_shopify_client
    app_module.list_tracked_products = demo_store.list_tracked_products
    app_module.upsert_tracked_product = demo_store.upsert_tracked_product
    app_module.update_tracked_shopify_metadata = demo_store.update_tracked_shopify_metadata
    app_module.update_tracked_stock_status = demo_store.update_tracked_stock_status
    app_module.delete_tracked_product = demo_store.delete_tracked_product
