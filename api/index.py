def app(request):
    """Vercel serverless function handler"""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Markaz to Shopify CSV Converter</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #1f77b4; }
        .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
        a { color: #1f77b4; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛍️ Markaz to Shopify CSV Converter</h1>
        <div class="info">
            <p><strong>Note:</strong> Streamlit apps require WebSocket support which is not available in Vercel serverless functions.</p>
            <p>For full functionality, please deploy to:</p>
            <ul>
                <li><strong>Streamlit Cloud</strong> (Recommended - Free tier available)</li>
                <li><strong>Railway</strong> (Good for Python apps)</li>
                <li><strong>Render</strong> (Free tier available)</li>
            </ul>
        </div>
        <p>To deploy on Streamlit Cloud:</p>
        <ol>
            <li>Push your code to GitHub</li>
            <li>Go to <a href="https://streamlit.io/cloud">streamlit.io/cloud</a></li>
            <li>Connect your GitHub repository</li>
            <li>Deploy with one click!</li>
        </ol>
    </div>
</body>
</html>"""
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html; charset=utf-8'},
        'body': html
    }
