"""
Vercel serverless function handler for Streamlit app
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def handler(request):
    """Vercel serverless function handler"""
    try:
        # Import streamlit runtime
        import streamlit.runtime.scriptrunner.script_runner as script_runner
        from streamlit.web.server import Server
        from streamlit.runtime.state import SessionState
        
        # Return a simple HTML response
        # Note: Full Streamlit requires persistent WebSocket connections
        # which are not available in Vercel serverless functions
        html_content = """
        <!DOCTYPE html>
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
                h1 { color: #1f77b4; }
                .info { 
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
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
        </html>
        """
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html; charset=utf-8',
            },
            'body': html_content
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/plain; charset=utf-8',
            },
            'body': f'Error: {str(e)}'
        }

# Vercel expects this function
def app(request):
    return handler(request)
