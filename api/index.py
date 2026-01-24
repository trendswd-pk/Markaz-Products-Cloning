"""
Vercel serverless function with Playwright for scraping
Optimized for serverless environment with proper browser flags
"""

def app(request):
    """Vercel serverless function handler"""
    try:
        # Dynamic import - only import when needed
        from playwright.sync_api import sync_playwright
        
        # Get URL from request
        url = request.get('query', {}).get('url') or request.get('body', {}).get('url', '')
        
        if not url:
            # Return HTML page if no URL provided
            html = """<!DOCTYPE html>
<html>
<head>
    <title>Markaz to Shopify CSV Converter</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #1f77b4; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛍️ Markaz to Shopify CSV Converter</h1>
        <p>App is working on Vercel!</p>
        <p>Add ?url=PRODUCT_URL to scrape a product.</p>
    </div>
</body>
</html>"""
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'text/html; charset=utf-8'},
                'body': html
            }
        
        # Launch browser with memory-saving flags for serverless
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--single-process'
                ]
            )
            
            try:
                page = browser.new_page()
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Simple scraping - get title
                title = page.title() or "Product"
                
                # Close browser immediately to free memory
                browser.close()
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': f'{{"title": "{title}", "url": "{url}"}}'
                }
            except Exception as e:
                # Ensure browser is closed even on error
                try:
                    browser.close()
                except:
                    pass
                raise e
                
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/plain'},
            'body': f'Error: {str(e)}'
        }
