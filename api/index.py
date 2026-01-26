"""
Vercel serverless function handler
Minimal version - Playwright functionality will be added after basic deployment works
"""

def app(request):
    """Vercel serverless function handler"""
    try:
        # Handle different request formats (Vercel can send different formats)
        if isinstance(request, dict):
            query = request.get('query', {}) or {}
            body = request.get('body', {}) or {}
            if isinstance(body, str):
                # Try to parse JSON body if it's a string
                try:
                    import json
                    body = json.loads(body)
                except:
                    body = {}
        else:
            query = {}
            body = {}
        
        # Get URL from query or body
        url = query.get('url') or body.get('url') or ''
        
        # Return HTML page
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Markaz to Shopify CSV Converter</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { 
            color: #1f77b4; 
            margin-top: 0;
        }
        .info { 
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #1f77b4;
        }
        .success {
            background: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #4caf50;
        }
        a {
            color: #1f77b4;
            text-decoration: none;
            font-weight: bold;
        }
        a:hover {
            text-decoration: underline;
        }
        code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛍️ Markaz to Shopify CSV Converter</h1>
        
        <div class="success">
            <strong>✅ Deployment Successful!</strong>
            <p>Your Vercel serverless function is working correctly.</p>
        </div>
        
        <div class="info">
            <p><strong>Current Status:</strong></p>
            <p>Basic serverless function is deployed and running.</p>
            <p>Playwright scraping functionality will be added in the next update.</p>
        </div>
        
        <div class="info">
            <p><strong>Next Steps:</strong></p>
            <ol>
                <li>Verify environment variables are set in Vercel Dashboard</li>
                <li>Check build logs for any warnings</li>
                <li>Playwright functionality will be enabled after browser installation</li>
            </ol>
        </div>
        
        <p><strong>Test URL:</strong> <code>?url=PRODUCT_URL</code></p>
        <p>Currently returns this page. Scraping will be enabled after Playwright setup.</p>
    </div>
</body>
</html>"""
        
        # Return proper Vercel response format
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html; charset=utf-8',
            },
            'body': html_content
        }
        
    except Exception as e:
        # Return error response with details
        import traceback
        error_details = traceback.format_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/html; charset=utf-8',
            },
            'body': f"""<!DOCTYPE html>
<html>
<head>
    <title>Error - Markaz CSV Converter</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }}
        .error {{ background: #ffebee; padding: 20px; border-radius: 5px; border-left: 4px solid #f44336; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="error">
        <h2>❌ Error Occurred</h2>
        <p><strong>Error:</strong> {str(e)}</p>
        <details>
            <summary>Technical Details</summary>
            <pre>{error_details}</pre>
        </details>
    </div>
</body>
</html>"""
        }
