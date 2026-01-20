import streamlit as st
from playwright.sync_api import sync_playwright
import pandas as pd
import re
from urllib.parse import urljoin
from html import escape

# Page configuration
st.set_page_config(
    page_title="Markaz to Shopify CSV Converter",
    page_icon="🛍️",
    layout="wide"
)

# Initialize session state
if 'products' not in st.session_state:
    st.session_state.products = []

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

def generate_unique_handle(title, base_sku):
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
        handle = title_slug if title_slug else f"product-{len(st.session_state.products)}"
    
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

def scrape_markaz_product(url):
    """Scrape product data from Markaz product URL using Playwright"""
    try:
        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to the page
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for spans with class 'ant-typography' to load (these contain title and SKU)
            try:
                page.wait_for_selector('span.ant-typography', timeout=10000)
            except Exception as e:
                browser.close()
                return {
                    'title': None,
                    'description': None,
                    'price': None,
                    'image_urls': [],
                    'sku': None,
                    'url': url,
                    'status': f'Error: Could not find product spans - {str(e)}'
                }
            
            # Find the product div (parent of the spans with classes 'flex flex-col flex-wrap')
            product_div = None
            try:
                # Get the first span and find its parent div with the classes
                first_span = page.locator('span.ant-typography').first
                # Find ancestor div with the specific classes
                product_div = first_span.locator('xpath=ancestor::div[contains(@class, "flex") and contains(@class, "flex-col") and contains(@class, "flex-wrap")]').first
                # Verify it exists
                if product_div.count() == 0:
                    # Fallback: try CSS selector
                    product_div = page.locator("div.flex.flex-col.flex-wrap").first
            except:
                # Final fallback: use page locator
                product_div = page.locator("div").filter(has=page.locator("span.ant-typography")).first
            
            # Extract Title from the second span with class 'ant-typography'
            # First span is SKU, second span is Title
            title = "Product Title Not Found"
            sku = ""
            try:
                # Find all spans with class 'ant-typography' within the product div
                if product_div:
                    spans = product_div.locator('span.ant-typography').all()
                else:
                    spans = page.locator('span.ant-typography').all()
                
                if len(spans) >= 2:
                    # First span is the SKU
                    sku = spans[0].inner_text().strip()
                    # Second span is the Title
                    title = spans[1].inner_text().strip()
                elif len(spans) == 1:
                    # Only one span found, assume it's the title
                    title = spans[0].inner_text().strip()
            except Exception as e:
                st.warning(f"Could not extract title/SKU: {str(e)}")
            
            # Extract price - find text containing 'Rs.' and extract the number immediately following it
            price = "0.00"
            try:
                # Look for element containing 'Rs.'
                price_elements = page.locator('*:has-text("Rs.")').all()
                
                for price_elem in price_elements:
                    price_text = price_elem.inner_text()
                    if 'Rs.' in price_text:
                        # Use regex to find 'Rs.' followed by optional whitespace, then capture digits and commas
                        # This ensures we only get the number immediately following 'Rs.'
                        price_match = re.search(r'Rs\.\s*([\d,]+)', price_text, re.IGNORECASE)
                        if price_match:
                            # Remove commas from the extracted price string
                            price = price_match.group(1).replace(',', '')
                            break
                
                # Fallback: search in the product div
                if price == "0.00":
                    div_text = product_div.inner_text()
                    # Use regex to find 'Rs.' followed by optional whitespace, then capture digits and commas
                    price_match = re.search(r'Rs\.\s*([\d,]+)', div_text, re.IGNORECASE)
                    if price_match:
                        # Remove commas from the extracted price string
                        price = price_match.group(1).replace(',', '')
                
                # Final fallback: search entire page text
                if price == "0.00":
                    page_text = page.inner_text('body')
                    price_match = re.search(r'Rs\.\s*([\d,]+)', page_text, re.IGNORECASE)
                    if price_match:
                        # Remove commas from the extracted price string
                        price = price_match.group(1).replace(',', '')
            except Exception as e:
                st.warning(f"Could not extract price: {str(e)}")
            
            # Extract breadcrumb navigation from the very top of the page (after title is extracted)
            # Capture Method: Find the entire breadcrumb container and get full text string
            breadcrumb_items = []
            try:
                # Find the breadcrumb container (usually ant-breadcrumb or div with many / separators)
                breadcrumb_container = None
                breadcrumb_text = ""
                
                # Try to find ant-breadcrumb container first
                try:
                    ant_breadcrumb = page.locator('.ant-breadcrumb, [class*="breadcrumb"]').first
                    if ant_breadcrumb.count() > 0:
                        breadcrumb_container = ant_breadcrumb
                        breadcrumb_text = ant_breadcrumb.inner_text().strip()
                except:
                    pass
                
                # If not found, look for div with / separators in main
                if not breadcrumb_text or 'Marketplace' not in breadcrumb_text:
                    try:
                        # Look for divs in main that contain 'Marketplace' and '/'
                        main_divs = page.locator('main div').all()
                        for div in main_divs[:20]:  # Check first 20 divs
                            try:
                                div_text = div.inner_text().strip()
                                # Check if it looks like a breadcrumb (has Marketplace and / separators)
                                if 'Marketplace' in div_text and '/' in div_text:
                                    # Count / separators - breadcrumb should have multiple
                                    separator_count = div_text.count('/')
                                    if separator_count >= 2:  # At least 2 separators
                                        breadcrumb_text = div_text
                                        breadcrumb_container = div
                                        break
                            except:
                                continue
                    except:
                        pass
                
                # If still not found, try getting text from main element that contains Marketplace
                if not breadcrumb_text or 'Marketplace' not in breadcrumb_text:
                    try:
                        main_text = page.locator('main').first.inner_text()
                        # Look for breadcrumb pattern: Marketplace / ... / ...
                        breadcrumb_match = re.search(r'Marketplace\s*[/\\]\s*[^\n]+', main_text, re.IGNORECASE)
                        if breadcrumb_match:
                            breadcrumb_text = breadcrumb_match.group(0).strip()
                    except:
                        pass
                
                # Clean Split: Split the string by the / character to get a list
                if breadcrumb_text and 'Marketplace' in breadcrumb_text:
                    # Split by / or \
                    items = re.split(r'\s*[/\\]\s*', breadcrumb_text)
                    
                    # List Cleaning: Process each item
                    cleaned_list = []
                    for item in items:
                        # Trim spaces from each item
                        item = item.strip()
                        
                        # Skip empty items
                        if not item:
                            continue
                        
                        # Filter out unwanted items
                        item_lower = item.lower()
                        should_skip = False
                        
                        # Skip if it contains block list terms
                        block_terms = ['followers', 'products', 'rs.', 'add to cart', 'cart']
                        for term in block_terms:
                            if term in item_lower:
                                should_skip = True
                                break
                        
                        # Skip product counts, follower counts, prices
                        if re.search(r'\d+\s*Products?', item, re.IGNORECASE):
                            should_skip = True
                        if re.search(r'\d+[KkMm]?\s*Followers?', item, re.IGNORECASE):
                            should_skip = True
                        if re.search(r'Rs\.?\s*\d+', item, re.IGNORECASE):
                            should_skip = True
                        
                        # Only keep items with letters (valid category names)
                        if not re.search(r'[a-zA-Z]', item):
                            should_skip = True
                        
                        if not should_skip and item:
                            cleaned_list.append(item)
                    
                    # Remove the very last item (Product Title) from the list
                    if cleaned_list:
                        # Check if last item matches the product title
                        if title and cleaned_list[-1].lower() in title.lower():
                            cleaned_list = cleaned_list[:-1]
                        else:
                            # If title doesn't match, still remove last item as it's likely the product
                            cleaned_list = cleaned_list[:-1]
                    
                    breadcrumb_items = cleaned_list
                
            except Exception as e:
                st.warning(f"Could not extract breadcrumb: {str(e)}")
            
            # Extract description - text content under title/price, stop before 'Product Code:'
            description = ""
            product_code = ""
            try:
                # Get all text from the product div, excluding title, SKU, and price
                div_text = product_div.inner_text()
                lines = div_text.split('\n')
                
                description_parts = []
                found_title = False
                found_sku = False
                found_price = False
                found_product_code = False
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Skip SKU (first span)
                    if not found_sku and line == sku:
                        found_sku = True
                        continue
                    
                    # Skip title (second span)
                    if not found_title and line == title:
                        found_title = True
                        continue
                    
                    # Skip price
                    if not found_price and re.search(r'Rs\.\s*[\d,]+', line, re.IGNORECASE):
                        found_price = True
                        continue
                    
                    # Skip if it's just the price number
                    if re.match(r'^[\d,]+(?:\.\d+)?$', line):
                        continue
                    
                    # Check for 'Product Code:' - extract value and stop description collection
                    if 'Product Code:' in line or 'product code:' in line.lower():
                        found_product_code = True
                        # Extract the value after 'Product Code:'
                        code_match = re.search(r'Product Code:\s*(.+)', line, re.IGNORECASE)
                        if code_match:
                            product_code = code_match.group(1).strip()
                        # Stop collecting description at this point
                        break
                    
                    # Collect description text after we've found title and price, but before Product Code
                    if found_title and found_price and not found_product_code and len(line) > 5:
                        # Skip navigation, buttons, etc.
                        if line.lower() not in ['add to cart', 'buy now', 'description', 'details', 'sku']:
                            description_parts.append(line)
                
                description = '\n'.join(description_parts)
                
                # If no description found or Product Code not found in lines, try finding description containers
                if (not description or len(description) < 20) or not product_code:
                    desc_selectors = [
                        '[class*="description"]',
                        '[class*="Description"]',
                        '[class*="detail"]',
                        '[class*="Detail"]',
                        'p',
                    ]
                    
                    for selector in desc_selectors:
                        try:
                            desc_elements = page.locator(selector).all()
                            for elem in desc_elements[:10]:  # Check first 10
                                text = elem.inner_text().strip()
                                
                                # Check for Product Code in this text
                                if 'Product Code:' in text or 'product code:' in text.lower():
                                    # Split at Product Code
                                    parts = re.split(r'Product Code:', text, flags=re.IGNORECASE)
                                    if len(parts) > 1:
                                        # Everything before Product Code is description
                                        description = parts[0].strip()
                                        # Extract Product Code value
                                        code_match = re.search(r'Product Code:\s*(.+)', text, re.IGNORECASE)
                                        if code_match:
                                            product_code = code_match.group(1).strip()
                                        break
                                elif (text and len(text) > 20 and 
                                      text != title and 
                                      text != sku and
                                      not re.search(r'Rs\.\s*[\d,]+', text, re.IGNORECASE) and
                                      text.lower() not in ['add to cart', 'buy now']):
                                    if not description:
                                        description = text
                                    else:
                                        # Append if it's different content
                                        if text not in description:
                                            description += '\n' + text
                                    break
                            if description and len(description) > 50:
                                break
                        except:
                            continue
                
                # If still no Product Code found, try searching the entire page
                if not product_code:
                    page_text = page.inner_text('body')
                    code_match = re.search(r'Product Code:\s*([A-Z0-9]+)', page_text, re.IGNORECASE)
                    if code_match:
                        product_code = code_match.group(1).strip()
                
                if not description or len(description) < 10:
                    description = "No description available"
            except Exception as e:
                description = "No description available"
                st.warning(f"Could not extract description: {str(e)}")
            
            # Extract Base SKU: alphanumeric code immediately following 'Product Code:'
            base_sku = ""
            if product_code:
                # Extract only alphanumeric characters (e.g., MZ51500000049KSAA)
                base_sku_match = re.search(r'([A-Z0-9]+)', product_code, re.IGNORECASE)
                if base_sku_match:
                    base_sku = base_sku_match.group(1).strip()
            
            if not base_sku:
                base_sku = sku if sku else ""
            
            # Extract variants using exact HTML structure
            # Target Container: Look for the div that contains a span with the text 'Size :'
            option1_name = 'Title'
            variants = []  # List to store all variant values
            
            try:
                # Find the div that contains a span with text 'Size :'
                size_container = None
                try:
                    # Find span with text 'Size :'
                    size_span = page.locator('span:has-text("Size :")').first
                    if size_span.count() > 0:
                        # Find the parent div that contains this span
                        size_container = size_span.locator('xpath=ancestor::div[1]').first
                        if size_container.count() == 0:
                            # Try alternative: get parent of parent
                            size_container = size_span.locator('xpath=ancestor::div').first
                except:
                    pass
                
                # If Size container found, extract variants from buttons
                if size_container and size_container.count() > 0:
                    try:
                        # Inside that div, find all button elements
                        button_elements = size_container.locator('button').all()
                        
                        # From each button, extract the text inside the span with class 'ant-typography'
                        for button in button_elements:
                            try:
                                # Find span with class 'ant-typography' inside the button
                                typography_span = button.locator('span.ant-typography').first
                                if typography_span.count() > 0:
                                    variant_text = typography_span.inner_text().strip()
                                    if variant_text and variant_text not in variants:
                                        variants.append(variant_text)
                            except:
                                # Fallback: get button text directly if no ant-typography span found
                                try:
                                    button_text = button.inner_text().strip()
                                    if button_text and button_text not in variants:
                                        variants.append(button_text)
                                except:
                                    continue
                        
                        # If buttons found, set option name to 'Size'
                        if variants:
                            option1_name = 'Size'
                    except Exception as e:
                        st.warning(f"Error extracting variants from Size container: {str(e)}")
                
                # If no Size container found, check for Color
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
                
            except Exception as e:
                st.warning(f"Could not extract variants: {str(e)}")
            
            # Default Case: If no 'Size :' container is found, set Option1 Name to 'Title' and Option1 Value to 'Default Title'
            if not variants:
                variants = ['Default Title']
                option1_name = 'Title'
            
            # Extract images from thumbnail gallery
            image_urls = []
            try:
                # Look for images in gallery/thumbnail containers
                img_selectors = [
                    '[class*="gallery"] img',
                    '[class*="thumbnail"] img',
                    '[class*="image"] img',
                    '[class*="Image"] img',
                    '.product-image img',
                    '.product-images img',
                ]
                
                for selector in img_selectors:
                    try:
                        img_elements = page.locator(selector).all()
                        for img in img_elements:
                            # Get src attribute
                            src = img.get_attribute('src')
                            if not src:
                                src = img.get_attribute('data-src')
                            if not src:
                                src = img.get_attribute('data-lazy-src')
                            
                            if src:
                                # Convert relative URLs to absolute
                                if not src.startswith('http'):
                                    src = urljoin(url, src)
                                
                                # Filter out logos, icons, placeholders
                                if src not in image_urls and not any(skip in src.lower() for skip in ['logo', 'icon', 'avatar', 'placeholder', 'loading']):
                                    image_urls.append(src)
                        
                        if image_urls:
                            break
                    except:
                        continue
                
                # If no images found, try all img tags
                if not image_urls:
                    all_imgs = page.locator('img').all()
                    for img in all_imgs[:10]:  # Limit to first 10
                        src = img.get_attribute('src')
                        if src and not any(skip in src.lower() for skip in ['logo', 'icon', 'avatar', 'placeholder', 'loading']):
                            if not src.startswith('http'):
                                src = urljoin(url, src)
                            if src not in image_urls:
                                image_urls.append(src)
            except Exception as e:
                st.warning(f"Could not extract images: {str(e)}")
            
            browser.close()
            
            return {
                'title': title,
                'description': description,
                'price': price,
                'image_urls': image_urls,
                'base_sku': base_sku,
                'variants': variants,  # List of all variant values
                'option1_name': option1_name,
                'breadcrumb_items': breadcrumb_items,  # List of breadcrumb items
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

def create_shopify_row(product, variant_value="", image_url="", image_position="", is_variant_row=False, is_first_variant=False):
    """Create a Shopify CSV row with all required columns in exact order"""
    # Handle must be the same for all rows of the same product
    # Generate unique handle: slugified title + base SKU
    handle = generate_unique_handle(product.get('title', ''), product.get('base_sku', ''))
    
    # Title, Body (HTML), and Price should only be in the first variant row
    title = product['title'] or "Untitled Product" if is_first_variant else ""
    body_html = convert_description_to_html(product['description']) if is_first_variant else ""
    
    # Pricing Engine Logic - apply to all variant rows
    try:
        original_price = float(product['price'])
        # Store original price in Cost per item (only in first variant row)
        cost_per_item = f"{original_price:.2f}" if is_first_variant else ""
        
        # Calculate Variant Price based on original price (apply to all variants)
        if original_price < 2000:
            variant_price = original_price + 500
        else:
            variant_price = original_price + 1000
        
        variant_price_formatted = f"{variant_price:.2f}"
    except:
        cost_per_item = "0.00" if is_first_variant else ""
        variant_price_formatted = "0.00"
    
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
        'Variant Compare At Price': '',
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

def main():
    st.title("🛍️ Markaz to Shopify CSV Converter")
    st.markdown("Scrape Markaz product data and convert to Shopify-compatible CSV format.")
    
    # Product URL input
    st.header("Add Product")
    url_input = st.text_input(
        "Product URL",
        placeholder="https://www.shop.markaz.app/explore/product/...",
        key="product_url_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        add_button = st.button("Add to List", type="primary", use_container_width=True)
    
    if add_button:
        if url_input:
            with st.spinner("Scraping product data... This may take a few seconds."):
                product_data = scrape_markaz_product(url_input)
                
                if product_data['status'] == 'success':
                    st.session_state.products.append(product_data)
                    st.success(f"✅ Added: {product_data['title']}")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to scrape: {product_data['status']}")
        else:
            st.warning("Please enter a product URL")
    
    st.divider()
    
    # Product list display
    if st.session_state.products:
        st.header(f"Product List ({len(st.session_state.products)} products)")
        
        # Display products
        for idx, product in enumerate(st.session_state.products):
            with st.expander(f"Product {idx + 1}: {product['title']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Title:**", product['title'])
                    if product.get('base_sku'):
                        st.write("**Base SKU:**", product['base_sku'])
                    if product.get('variants') and len(product['variants']) > 0:
                        variants_display = ', '.join(product['variants'])
                        st.write(f"**{product.get('option1_name', 'Variants')}:**", variants_display)
                    st.write("**Price:**", f"Rs. {product['price']}")
                    st.write("**URL:**", product['url'])
                
                with col2:
                    st.write("**Description:**", product['description'][:300] + "..." if len(product['description']) > 300 else product['description'])
                    st.write("**Images Found:**", len(product['image_urls']))
                    if product['image_urls']:
                        st.image(product['image_urls'][0], width=200, caption="First Image")
                
                if st.button(f"Remove Product {idx + 1}", key=f"remove_{idx}"):
                    st.session_state.products.pop(idx)
                    st.rerun()
        
        st.divider()
        
        # Download CSV section
        st.header("Download Shopify CSV")
        
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
        for product in st.session_state.products:
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
            use_container_width=True
        )
        
        # Show preview
        st.subheader("CSV Preview")
        st.dataframe(df, use_container_width=True)
        
        # Clear all button
        if st.button("Clear All Products", type="secondary"):
            st.session_state.products = []
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

if __name__ == "__main__":
    main()
