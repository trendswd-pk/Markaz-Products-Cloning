# Streamlit Cloud Deployment Guide

## 🚀 Streamlit Cloud Par Deploy Karne Ka Tarika

### Step 1: GitHub Repository
1. Apna code GitHub par push karein (agar nahi hai to):
   ```bash
   git add .
   git commit -m "Ready for Streamlit Cloud"
   git push origin main
   ```

### Step 2: Streamlit Cloud Account
1. [streamlit.io/cloud](https://streamlit.io/cloud) par jayein
2. "Sign up" ya "Sign in" karein
3. GitHub account se connect karein

### Step 3: Deploy App
1. Streamlit Cloud dashboard mein "New app" button click karein
2. Apni GitHub repository select karein
3. Branch select karein (usually `main`)
4. Main file path: `app.py`
5. "Deploy!" button click karein

### Step 4: Playwright Setup
Streamlit Cloud par Playwright browsers automatically install ho jayenge. Agar manually install karna ho to:

1. App settings mein jayein
2. "Advanced settings" mein:
   - Build command: `playwright install chromium`
   - Ya requirements.txt mein already hai

### ✅ Advantages
- ✅ Free tier available
- ✅ Streamlit apps ke liye optimized
- ✅ Playwright browsers install ho jate hain
- ✅ WebSocket support hai
- ✅ Persistent connections
- ✅ Auto-deploy on git push
- ✅ Custom domain support

### 📝 Important Files
- `requirements.txt` - Dependencies
- `app.py` - Main app file
- `.streamlit/config.toml` - Streamlit configuration (optional)

### 🔧 Troubleshooting
Agar koi issue aaye:
1. Build logs check karein
2. Requirements.txt verify karein
3. Playwright browsers install ho rahe hain ya nahi check karein

### 🎉 Done!
App deploy ho jayegi aur aapko URL milega jahan se aap app use kar sakte hain!
