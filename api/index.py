"""
Vercel Python Serverless Function
Optimized for Playwright scraping with memory-efficient browser flags
"""

import json
import os
import subprocess

from markaz_scraper import scrape_markaz_product

# Playwright Browser Fix: Install chromium browser on Vercel
try:
    if os.getenv('VERCEL') == '1' or os.getenv('VERCEL_ENV'):
        subprocess.run(
            ['playwright', 'install', 'chromium'],
            capture_output=True,
            timeout=300,
            check=False,
        )
except Exception:
    pass


def app(request):
    """Vercel Python function handler."""
    try:
        if isinstance(request, dict):
            query = request.get('query', {}) or {}
            body = request.get('body', {}) or {}
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except json.JSONDecodeError:
                    body = {}
        else:
            query = {}
            body = {}

        url = query.get('url') or body.get('url') or ''

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
            <p>Example: <code>?url=https://www.markaz.app/shop/product/...</code></p>
        </div>
    </div>
</body>
</html>"""
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'text/html; charset=utf-8'},
                'body': html,
            }

        result = scrape_markaz_product(url)

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result, indent=2),
        }

    except Exception as e:
        import traceback
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': str(e),
                'details': traceback.format_exc(),
            }),
        }
