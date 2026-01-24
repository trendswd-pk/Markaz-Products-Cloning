"""
Vercel serverless function handler for Streamlit app
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import the main app
from app import main
import streamlit as st

def handler(request):
    """Vercel serverless function handler"""
    # Run the Streamlit app
    # Note: Streamlit may have limitations in serverless environments
    return main()

# Vercel expects this function
def app(request):
    return handler(request)
