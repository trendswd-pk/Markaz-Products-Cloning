"""
Vercel Python Serverless Function
Optimized for Playwright scraping with memory-efficient browser flags
"""

import json
import re
from urllib.parse import urljoin, parse_qs
from html import escape

def app(request):
    """
    Vercel Python function handler
    Handles scraping requests and returns JSON/CSV
    """
    try:
        # Handle different request formats
        if isinstance(request, dict):
            query = request.get('query', {}) or {}
            body = request.get('body', {}) or {}
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except:
                    body = {}
        else:
            query = {}
            body = {}
        
        # Get URL from query or body
        url = query.get('url') or body.get('url') or ''
        
        # If no URL, return info page
        if not url:
            html = """<!DOCTYPE html>
<html>
<head>
    <title>Markaz to Shopify CSV Converter</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #1f77b4; margin: 0 0 20px 0; }
        .success { background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #4caf50; }
        .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #1f77b4; }
        code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>🛍️ Markaz to Shopify CSV Converter</h1>
        <div class="success">
            <strong>✅ Serverless Function Working!</strong>
            <p>Vercel deployment successful with Playwright optimization.</p>
        </div>
        <div class="info">
            <p><strong>Usage:</strong></p>
            <p>Add <code>?url=PRODUCT_URL</code> to scrape a product.</p>
            <p>Example: <code>?url=https://www.shop.markaz.app/explore/product/...</code></p>
        </div>
    </div>
</body>
</html>"""
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'text/html; charset=utf-8'},
                'body': html
            }
        
        # Scrape the product
        result = scrape_markaz_product(url)
        
        # Return JSON response
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result, indent=2)
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': str(e),
                'details': error_details
            })
        }


def slugify(text):
    """Convert text to URL-friendly handle"""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def scrape_markaz_product(url):
    """Scrape product data from Markaz product URL using Playwright - Optimized for Vercel"""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Launch browser with Vercel-optimized flags to reduce memory footprint
            browser = p.chromium.launch(
                headless=True,  # Hardcoded headless mode
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--single-process',
                    '--disable-gpu'
                ]
            )
            page = browser.new_page()
            
            # Navigate to the page
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for spans with class 'ant-typography' to load
            try:
                page.wait_for_selector('span.ant-typography', timeout=10000)
            except Exception as e:
                browser.close()
                return {
                    'title': None,
                    'description': None,
                    'price': None,
                    'image_urls': [],
                    'base_sku': None,
                    'variants': [],
                    'option1_name': 'Title',
                    'breadcrumb_items': [],
                    'url': url,
                    'status': f'Error: Could not find product spans - {str(e)}'
                }
            
            # Find the product div
            product_div = None
            try:
                first_span = page.locator('span.ant-typography').first
                product_div = first_span.locator('xpath=ancestor::div[contains(@class, "flex") and contains(@class, "flex-col") and contains(@class, "flex-wrap")]').first
                if product_div.count() == 0:
                    product_div = page.locator("div.flex.flex-col.flex-wrap").first
            except:
                product_div = page.locator("div").filter(has=page.locator("span.ant-typography")).first
            
            # Extract Title and SKU
            title = "Product Title Not Found"
            sku = ""
            try:
                if product_div:
                    spans = product_div.locator('span.ant-typography').all()
                else:
                    spans = page.locator('span.ant-typography').all()
                
                if len(spans) >= 2:
                    sku = spans[0].inner_text().strip()
                    title = spans[1].inner_text().strip()
                elif len(spans) == 1:
                    title = spans[0].inner_text().strip()
            except Exception as e:
                pass
            
            # Extract price
            price = "0.00"
            try:
                price_elements = page.locator('*:has-text("Rs.")').all()
                for price_elem in price_elements:
                    price_text = price_elem.inner_text()
                    if 'Rs.' in price_text:
                        price_match = re.search(r'Rs\.\s*([\d,]+)', price_text, re.IGNORECASE)
                        if price_match:
                            price = price_match.group(1).replace(',', '')
                            break
                
                if price == "0.00":
                    div_text = product_div.inner_text()
                    price_match = re.search(r'Rs\.\s*([\d,]+)', div_text, re.IGNORECASE)
                    if price_match:
                        price = price_match.group(1).replace(',', '')
            except Exception as e:
                pass
            
            # Extract breadcrumb navigation - STRICT: ONLY <a> tags with href starting with "/explore"
            # Target: 'Marketplace', 'Beauty&Fashion', 'Cosmetics', 'Personal Care'
            # Ignore: Anything that is not an <a> tag to avoid 'Followers' or 'Product counts'
            breadcrumb_items = []
            try:
                # STRICT SELECTOR: Only get <a> tags from main that have href starting with "/explore"
                # This ensures we ONLY capture breadcrumb links, not any other text
                breadcrumb_links = page.locator('main a[href^="/explore"]').all()
                
                if breadcrumb_links:
                    # Extract text from each link (ONLY from <a> tags)
                    for link in breadcrumb_links:
                        try:
                            # Get href to verify it starts with "/explore"
                            href = link.get_attribute('href') or ''
                            
                            # STRICT: Only process if href starts with "/explore"
                            if not href.startswith('/explore'):
                                continue
                            
                            # Get text content from the <a> tag ONLY
                            link_text = link.inner_text().strip()
                            
                            # Skip if empty
                            if not link_text:
                                continue
                            
                            # Stop at product title - if this link text matches title, stop collecting
                            if title:
                                title_lower = title.lower()
                                link_lower = link_text.lower()
                                # If link text is part of title or title is part of link, stop
                                if title_lower in link_lower or link_lower in title_lower:
                                    break
                                # Also check if link text is very similar to title (product page link)
                                if len(link_text) > 10 and title_lower[:20] in link_lower:
                                    break
                            
                            # Basic validation: Must contain letters (valid category names)
                            if not re.search(r'[a-zA-Z]', link_text):
                                continue
                            
                            # Block list: Skip if contains unwanted terms (extra safety)
                            link_lower = link_text.lower()
                            block_terms = ['followers', 'products', 'rs.', 'add to cart', 'cart', 'view all']
                            
                            should_skip = False
                            for term in block_terms:
                                if term in link_lower:
                                    should_skip = True
                                    break
                            
                            # Skip product/follower counts and prices (extra safety)
                            if re.search(r'\d+\s*Products?', link_text, re.IGNORECASE):
                                should_skip = True
                            if re.search(r'\d+[KkMm]?\s*Followers?', link_text, re.IGNORECASE):
                                should_skip = True
                            if re.search(r'Rs\.\s*\d+', link_text, re.IGNORECASE):
                                should_skip = True
                            
                            # Add to breadcrumb if not skipped and not already in list
                            if not should_skip and link_text not in breadcrumb_items:
                                breadcrumb_items.append(link_text)
                        except Exception as e:
                            # Skip this link if any error occurs
                            continue
            except Exception as e:
                pass
            
            # Extract description and product code
            description = ""
            product_code = ""
            try:
                div_text = product_div.inner_text()
                lines = div_text.split('\n')
                
                description_parts = []
                found_title = False
                found_sku = False
                found_price = False
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if not found_sku and line == sku:
                        found_sku = True
                        continue
                    
                    if not found_title and line == title:
                        found_title = True
                        continue
                    
                    if not found_price and re.search(r'Rs\.\s*[\d,]+', line, re.IGNORECASE):
                        found_price = True
                        continue
                    
                    if re.match(r'^[\d,]+(?:\.\d+)?$', line):
                        continue
                    
                    if 'Product Code:' in line or 'product code:' in line.lower():
                        code_match = re.search(r'Product Code:\s*(.+)', line, re.IGNORECASE)
                        if code_match:
                            product_code = code_match.group(1).strip()
                        break
                    
                    if found_title and found_price and len(line) > 5:
                        if line.lower() not in ['add to cart', 'buy now', 'description', 'details', 'sku']:
                            description_parts.append(line)
                
                description = '\n'.join(description_parts)
                
                if not product_code:
                    page_text = page.inner_text('body')
                    code_match = re.search(r'Product Code:\s*([A-Z0-9]+)', page_text, re.IGNORECASE)
                    if code_match:
                        product_code = code_match.group(1).strip()
                
                if not description or len(description) < 10:
                    description = "No description available"
            except Exception as e:
                description = "No description available"
            
            # Extract Base SKU
            base_sku = ""
            if product_code:
                base_sku_match = re.search(r'([A-Z0-9]+)', product_code, re.IGNORECASE)
                if base_sku_match:
                    base_sku = base_sku_match.group(1).strip()
            
            if not base_sku:
                base_sku = sku if sku else ""
            
            # Extract variants
            option1_name = 'Title'
            variants = []
            
            try:
                size_span = page.locator('span:has-text("Size :")').first
                if size_span.count() > 0:
                    size_container = size_span.locator('xpath=ancestor::div[1]').first
                    if size_container.count() > 0:
                        button_elements = size_container.locator('button').all()
                        
                        for button in button_elements:
                            try:
                                typography_span = button.locator('span.ant-typography').first
                                if typography_span.count() > 0:
                                    variant_text = typography_span.inner_text().strip()
                                    if variant_text and variant_text not in variants:
                                        variants.append(variant_text)
                            except:
                                try:
                                    button_text = button.inner_text().strip()
                                    if button_text and button_text not in variants:
                                        variants.append(button_text)
                                except:
                                    continue
                        
                        if variants:
                            option1_name = 'Size'
            except:
                pass
            
            if not variants:
                try:
                    color_span = page.locator('span:has-text("Color :")').first
                    if color_span.count() > 0:
                        color_container = color_span.locator('xpath=ancestor::div[1]').first
                        if color_container.count() > 0:
                            button_elements = color_container.locator('button').all()
                            
                            for button in button_elements:
                                try:
                                    typography_span = button.locator('span.ant-typography').first
                                    if typography_span.count() > 0:
                                        variant_text = typography_span.inner_text().strip()
                                        if variant_text and variant_text not in variants:
                                            variants.append(variant_text)
                                except:
                                    try:
                                        button_text = button.inner_text().strip()
                                        if button_text and button_text not in variants:
                                            variants.append(button_text)
                                    except:
                                        continue
                            
                            if variants:
                                option1_name = 'Color'
                except:
                    pass
            
            if not variants:
                variants = ['Default Title']
                option1_name = 'Title'
            
            # Extract images
            image_urls = []
            try:
                img_selectors = [
                    '[class*="gallery"] img',
                    '[class*="thumbnail"] img',
                    '[class*="image"] img',
                    '.product-image img',
                ]
                
                for selector in img_selectors:
                    try:
                        img_elements = page.locator(selector).all()
                        for img in img_elements:
                            src = img.get_attribute('src') or img.get_attribute('data-src') or img.get_attribute('data-lazy-src')
                            if src:
                                if not src.startswith('http'):
                                    src = urljoin(url, src)
                                if src not in image_urls and not any(skip in src.lower() for skip in ['logo', 'icon', 'avatar', 'placeholder', 'loading']):
                                    image_urls.append(src)
                        if image_urls:
                            break
                    except:
                        continue
            except:
                pass
            
            browser.close()
            
            return {
                'title': title,
                'description': description,
                'price': price,
                'image_urls': image_urls,
                'base_sku': base_sku,
                'variants': variants,
                'option1_name': option1_name,
                'breadcrumb_items': breadcrumb_items,
                'url': url,
                'status': 'success'
            }
            
    except Exception as e:
        return {
            'title': None,
            'description': None,
            'price': None,
            'image_urls': [],
            'base_sku': None,
            'variants': ['Default Title'],
            'option1_name': 'Title',
            'breadcrumb_items': [],
            'url': url,
            'status': f'Error: {str(e)}'
        }
