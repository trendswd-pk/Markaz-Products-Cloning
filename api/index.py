"""
Vercel Python Serverless Function
Ultra-minimal version - guaranteed to work
"""

def app(request):
    """
    Vercel Python function handler
    Must be named 'app' and accept 'request' parameter
    """
    # Ultra-simple response - no complex logic
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Markaz CSV Converter</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #1f77b4; margin: 0 0 20px 0; }
        .success { background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #4caf50; }
        .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #1f77b4; }
    </style>
</head>
<body>
    <div class="box">
        <h1>🛍️ Markaz to Shopify CSV Converter</h1>
        <div class="success">
            <strong>✅ Serverless Function Working!</strong>
            <p>Vercel deployment successful. Function is responding correctly.</p>
        </div>
        <div class="info">
            <p><strong>Status:</strong> Basic function deployed and operational.</p>
            <p><strong>Next:</strong> Playwright scraping will be added after this basic version is confirmed working.</p>
        </div>
    </div>
</body>
</html>"""
    
    # Return Vercel-compatible response
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html; charset=utf-8'},
        'body': html
    }
