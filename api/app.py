"""
Vercel serverless function handler for Streamlit app
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def handler(request):
    """Vercel serverless function handler"""
    try:
        # Import the main app
        from app import main
        import streamlit.web.server as server
        import streamlit.runtime.scriptrunner.script_runner as script_runner
        
        # Create a simple response
        # Note: Full Streamlit functionality requires WebSocket support
        # This is a simplified approach for Vercel
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
            },
            'body': '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Markaz to Shopify CSV Converter</title>
                <meta http-equiv="refresh" content="0;url=https://streamlit.io/cloud">
            </head>
            <body>
                <h1>Streamlit App</h1>
                <p>For full functionality, please deploy to Streamlit Cloud.</p>
                <p>Redirecting...</p>
            </body>
            </html>
            '''
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/plain',
            },
            'body': f'Error: {str(e)}'
        }

# Vercel expects this function
def app(request):
    return handler(request)
