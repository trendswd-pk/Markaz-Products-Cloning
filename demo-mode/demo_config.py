DEMO_USERS = [
    {
        'username': 'admin@admin.com',
        'password': 'admin123',
        'label': 'Admin',
        'description': 'Full demo access — converter, tracked products, and simulated Shopify actions.',
    },
    {
        'username': 'demo',
        'password': 'demo123',
        'label': 'Editor / Staff',
        'description': 'Standard demo workspace with the same simulated tools.',
    },
    {
        'username': 'viewer@demo.com',
        'password': 'view123',
        'label': 'Viewer',
        'description': 'Read-oriented demo account with an isolated sandbox.',
    },
]

# Alias kept for older docs / capture scripts that still use `viewer`
DEMO_USER_ALIASES = {
    'viewer': 'viewer@demo.com',
}

STORAGE_NAMESPACE = 'markaz_demo'
TRACKED_PRODUCTS_KEY = 'tracked_products'
SHOPIFY_STATUS_KEY = 'shopify_status_map'
APP_SLUG = 'markaz-products-cloning'
