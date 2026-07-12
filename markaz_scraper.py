import json
import os
import re
from urllib.parse import urljoin

SIZE_PATTERN = re.compile(
    r'^(X-?Small|Small|Medium|Large|X-?Large|XX-?Large|XXX-?Large|\d+XL?|One Size|Free Size)$',
    re.IGNORECASE,
)
VARIANT_BUTTON_BLOCKLIST = {
    'copy', 'save', 'product details', 'add to bag', 'buy now', 'compare', 'share',
    'link', 'zoom', 'view', 'show more', 'download media', 'return policy',
}


def launch_browser_for_serverless(playwright):
    """Launch Chromium with flags tuned for serverless environments."""
    is_vercel = os.getenv('VERCEL') == '1' or os.getenv('VERCEL_ENV') is not None

    launch_args = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-software-rasterizer',
        '--disable-extensions',
        '--disable-background-networking',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--disable-features=TranslateUI',
        '--disable-ipc-flooding-protection',
        '--disable-logging',
        '--log-level=3',
        '--disable-permissions-api',
        '--disable-notifications',
    ]

    if is_vercel:
        launch_args.append('--single-process')

    return playwright.chromium.launch(
        headless=True,
        args=launch_args,
        ignore_default_args=['--enable-automation'],
    )


def _empty_result(url, status):
    return {
        'title': None,
        'description': None,
        'price': None,
        'image_urls': [],
        'base_sku': None,
        'variants': ['Default Title'],
        'option1_name': 'Title',
        'breadcrumb_items': [],
        'stock_status': None,
        'url': url,
        'status': status,
    }


def parse_json_ld_product(page):
    """Return the Product schema object from JSON-LD, if present."""
    for script in page.locator('script[type="application/ld+json"]').all():
        try:
            data = json.loads(script.inner_text())
        except (json.JSONDecodeError, TypeError):
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get('@type') == 'Product':
                return item
    return None


def _normalize_price(value):
    if value is None:
        return '0.00'
    if isinstance(value, (int, float)):
        return f'{float(value):.2f}'
    text = str(value).strip().replace(',', '')
    match = re.search(r'([\d]+(?:\.\d+)?)', text)
    return match.group(1) if match else '0.00'


def extract_price(page, product_ld=None):
    if product_ld:
        offers = product_ld.get('offers', {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if isinstance(offers, dict) and offers.get('price') is not None:
            return _normalize_price(offers['price'])

    for scope in [page.locator('h1').first.locator('xpath=ancestor::div[3]').first, page.locator('main').first]:
        if scope.count() == 0:
            continue
        text = scope.inner_text()
        for pattern in [r'PKR\s*([\d,]+(?:\.\d+)?)', r'Rs\.?\s*([\d,]+(?:\.\d+)?)']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return _normalize_price(match.group(1))

    body_text = page.inner_text('body')
    for pattern in [r'PKR\s*([\d,]+(?:\.\d+)?)', r'Rs\.?\s*([\d,]+(?:\.\d+)?)']:
        match = re.search(pattern, body_text, re.IGNORECASE)
        if match:
            return _normalize_price(match.group(1))

    return '0.00'


def extract_breadcrumbs(page, title='', product_ld=None):
    breadcrumb_items = []

    category = (product_ld or {}).get('category', '')
    if category:
        breadcrumb_items.extend(part.strip() for part in re.split(r'\s*>\s*', category) if part.strip())

    try:
        nav_links = page.locator('nav a').all()
        nav_items = []
        for link in nav_links:
            text = link.inner_text().strip()
            href = link.get_attribute('href') or ''
            if not text or '/shop' not in href:
                continue
            if title and text.lower() == title.lower():
                continue
            if text not in nav_items:
                nav_items.append(text)
        if nav_items:
            breadcrumb_items = nav_items
    except Exception:
        pass

    if not breadcrumb_items:
        try:
            for link in page.locator('main a[href*="/shop"]').all():
                text = link.inner_text().strip()
                href = link.get_attribute('href') or ''
                if not text or '/product/' in href:
                    continue
                if title and (title.lower() in text.lower() or text.lower() in title.lower()):
                    continue
                block_terms = ['followers', 'products', 'pkr', 'rs.', 'add to bag', 'cart', 'visit shop']
                if any(term in text.lower() for term in block_terms):
                    continue
                if text not in breadcrumb_items:
                    breadcrumb_items.append(text)
        except Exception:
            pass

    cleaned_items = []
    for item in breadcrumb_items:
        for part in re.split(r'\s*/\s*', item):
            part = part.strip()
            if part and part not in cleaned_items:
                cleaned_items.append(part)
    return cleaned_items


def extract_description(page, product_ld=None):
    try:
        overview = page.locator(
            'xpath=//h2[contains(translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"),"product overview")]/parent::*'
        ).first
        if overview.count() > 0:
            text = overview.inner_text().strip()
            text = re.sub(r'^Product [Oo]verview\s*', '', text)
            text = re.sub(r'\nShow more\s*$', '', text, flags=re.IGNORECASE)
            if len(text) > 20:
                return text
    except Exception:
        pass

    if product_ld and product_ld.get('description'):
        return product_ld['description'].strip()

    return 'No description available'


def _is_size_value(text):
    text = text.strip()
    if not text or len(text) > 30:
        return False
    lowered = text.lower()
    if lowered in VARIANT_BUTTON_BLOCKLIST:
        return False
    if re.fullmatch(r'[\d.]+', text):
        return False
    return bool(SIZE_PATTERN.match(text))


def extract_variants(page, product_ld=None):
    variants = []
    option1_name = 'Title'

    try:
        overview = page.locator(
            'xpath=//h2[contains(translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"),"product overview")]/parent::*'
        ).first
        if overview.count() > 0:
            overview_text = overview.inner_text()
            sizes_match = re.search(
                r'AVAILABLE SIZES\s*\n?\s*(.+?)(?:\n[A-Z][A-Z\s/&-]*\n|\nPRODUCT CODE|\nShow more|$)',
                overview_text,
                re.IGNORECASE | re.DOTALL,
            )
            if sizes_match:
                sizes = [part.strip() for part in re.split(r',\s*', sizes_match.group(1).strip()) if part.strip()]
                if sizes:
                    return 'Size', sizes
    except Exception:
        pass

    try:
        size_label = page.locator('text=/Size\\s*:?/').first
        if size_label.count() > 0:
            container = size_label.locator('xpath=ancestor::div[2]').first
            if container.count() > 0:
                for button in container.locator('button').all():
                    text = button.inner_text().strip()
                    if _is_size_value(text) and text not in variants:
                        variants.append(text)
                if variants:
                    return 'Size', variants
    except Exception:
        pass

    try:
        color_label = page.locator('text=/Color\\s*:?/').first
        if color_label.count() > 0:
            container = color_label.locator('xpath=ancestor::div[2]').first
            if container.count() > 0:
                color_variants = []
                for button in container.locator('button').all():
                    text = button.inner_text().strip()
                    if text and text.lower() not in VARIANT_BUTTON_BLOCKLIST and text not in color_variants:
                        color_variants.append(text)
                if color_variants:
                    return 'Color', color_variants
    except Exception:
        pass

    return option1_name, ['Default Title']


def normalize_markaz_image_url(url):
    """Use content.public CDN URLs — Shopify rejects static.markaz.app (wrong content-type)."""
    if not url:
        return ''
    url = url.strip()
    static_match = re.match(
        r'https?://static\.markaz\.app/pakistan/products/([^?#]+)',
        url,
        re.IGNORECASE,
    )
    if static_match:
        filename = static_match.group(1)
        return f'https://content.public.markaz.app/markazimagevideo/public/products/{filename}'
    return url


def _is_valid_product_image(src):
    if not src or '/thumbnails/' in src.lower():
        return False
    lowered = src.lower()
    skip_tokens = ('logo', 'icon', 'avatar', 'placeholder', 'loading', 'markaz_logo')
    return not any(token in lowered for token in skip_tokens)


def _append_product_image(image_urls, src):
    normalized = normalize_markaz_image_url(src)
    if normalized and normalized not in image_urls:
        image_urls.append(normalized)


def extract_images(page, product_ld=None, url=''):
    image_urls = []

    if product_ld:
        images = product_ld.get('image', [])
        if isinstance(images, str):
            images = [images]
        for src in images:
            if _is_valid_product_image(src):
                _append_product_image(image_urls, src)

    img_selectors = [
        'img[src*="content.public.markaz.app/markazimagevideo/public/products/"]',
        'img[src*="static.markaz.app/pakistan/products/"]',
        '[class*="gallery"] img',
        '[class*="thumbnail"] img',
        '[class*="image"] img',
        '.product-image img',
    ]

    for selector in img_selectors:
        try:
            for img in page.locator(selector).all():
                src = img.get_attribute('src') or img.get_attribute('data-src') or img.get_attribute('data-lazy-src')
                if not src:
                    continue
                if not src.startswith('http'):
                    src = urljoin(url, src)
                if _is_valid_product_image(src):
                    _append_product_image(image_urls, src)
        except Exception:
            continue

    return image_urls


def extract_stock_status(page, product_ld=None):
    if product_ld:
        offers = product_ld.get('offers', {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        availability = str((offers or {}).get('availability', ''))
        if 'InStock' in availability:
            return 'in_stock'
        if 'OutOfStock' in availability:
            return 'out_of_stock'

    try:
        body_text = page.inner_text('body')
        if re.search(r'out of stock|sold out|currently unavailable', body_text, re.IGNORECASE):
            return 'out_of_stock'
        if re.search(r'\d+\s+in stock', body_text, re.IGNORECASE):
            return 'in_stock'
    except Exception:
        pass

    return 'unknown'


def scrape_product_from_page(page, url):
    """Scrape product data from an already-open Playwright page."""

    def suppress_warnings(msg):
        msg_text = msg.text if hasattr(msg, 'text') else str(msg)
        if any(k in msg_text for k in ['Unrecognized feature', 'ambient-light-sensor', 'Permissions Policy', 'Feature Policy']):
            return

    page.on('console', suppress_warnings)
    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(3000)

    try:
        page.wait_for_selector('h1', timeout=15000)
    except Exception:
        try:
            page.wait_for_selector('script[type="application/ld+json"]', state='attached', timeout=5000)
        except Exception as exc:
            return _empty_result(url, f'Error: Could not load product page - {exc}')

    product_ld = parse_json_ld_product(page)

    title = 'Product Title Not Found'
    if product_ld and product_ld.get('name'):
        title = product_ld['name'].strip()
    else:
        try:
            if page.locator('h1').count() > 0:
                title = page.locator('h1').first.inner_text().strip()
        except Exception:
            pass

    if title == 'Product Title Not Found':
        return _empty_result(url, 'Error: Could not find product title')

    base_sku = ''
    if product_ld and product_ld.get('sku'):
        base_sku = str(product_ld['sku']).strip()
    if not base_sku:
        page_text = page.inner_text('body')
        code_match = re.search(r'Product Code[:\s]*([A-Z0-9]+)', page_text, re.IGNORECASE)
        if code_match:
            base_sku = code_match.group(1).strip()

    price = extract_price(page, product_ld)
    description = extract_description(page, product_ld)
    breadcrumb_items = extract_breadcrumbs(page, title, product_ld)
    option1_name, variants = extract_variants(page, product_ld)
    image_urls = extract_images(page, product_ld, url)
    stock_status = extract_stock_status(page, product_ld)

    return {
        'title': title,
        'description': description,
        'price': price,
        'image_urls': image_urls,
        'base_sku': base_sku,
        'variants': variants,
        'option1_name': option1_name,
        'breadcrumb_items': breadcrumb_items,
        'stock_status': stock_status,
        'url': url,
        'status': 'success',
    }


def scrape_markaz_product(url):
    """Scrape product data from Markaz product URL."""
    from playwright.sync_api import sync_playwright

    browser = None
    context = None
    try:
        with sync_playwright() as playwright:
            browser = launch_browser_for_serverless(playwright)
            context = browser.new_context(
                permissions=[],
                ignore_https_errors=True,
                viewport={'width': 1920, 'height': 1080},
            )
            page = context.new_page()
            return scrape_product_from_page(page, url)
    except Exception as exc:
        return _empty_result(url, f'Error: {exc}')
    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass
        if browser:
            try:
                browser.close()
            except Exception:
                pass
