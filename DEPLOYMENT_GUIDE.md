# 🚀 Deployment Guide: Markaz Scraper

## Current Setup Analysis

### ✅ What You Have:
1. **`app.py`** - Full Streamlit application with UI
2. **`api/index.py`** - Vercel serverless function (API endpoint)
3. **`vercel.json`** - Currently routes to `api/index.py`

### ⚠️ Important: Streamlit on Vercel

**Streamlit apps CANNOT run on Vercel serverless functions** because:
- ❌ Streamlit requires WebSocket support (not available in serverless)
- ❌ Streamlit needs persistent connections
- ❌ Vercel functions are stateless with timeout limits
- ❌ Streamlit's session state won't work

## 🎯 Recommended Deployment Strategy

### Option 1: Hybrid Approach (Recommended)

**Keep API on Vercel, Deploy Streamlit on Streamlit Cloud**

1. **Vercel** → `api/index.py` (API endpoint for scraping)
2. **Streamlit Cloud** → `app.py` (UI that calls Vercel API)

**Benefits:**
- ✅ Best of both worlds
- ✅ API is fast and serverless
- ✅ Streamlit UI works perfectly
- ✅ Free tiers available for both

### Option 2: API Only on Vercel

**Use only `api/index.py` on Vercel**

- ✅ Already working
- ✅ Returns JSON/CSV
- ✅ Can be called from any frontend
- ❌ No UI (need to build custom frontend)

### Option 3: Streamlit Cloud Only

**Deploy `app.py` on Streamlit Cloud**

- ✅ Full Streamlit experience
- ✅ Easy deployment
- ✅ Free tier available
- ❌ Playwright might have memory issues

---

## 📋 Current Configuration Status

### ✅ `vercel.json` - CORRECT
```json
{
  "functions": {
    "api/index.py": {
      "runtime": "python3.12",
      "memory": 1024,
      "maxDuration": 60
    }
  },
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```
**Status:** ✅ Correctly configured for API endpoint

### ✅ `api/index.py` - CORRECT
- ✅ Proper Vercel function handler (`app(request)`)
- ✅ Returns JSON/HTML responses
- ✅ Playwright scraping logic included
- ✅ Memory management with finally block

### ✅ `requirements.txt` - COMPLETE
```
streamlit>=1.30.0
playwright==1.40.0
pandas
beautifulsoup4
lxml
requests
```
**Status:** ✅ All dependencies included

---

## 🚀 Deployment Steps

### For Vercel (API Endpoint) - Already Done ✅

Your current setup is correct for the API:
- `vercel.json` routes to `api/index.py`
- Function handler is correct
- Dependencies are in `requirements.txt`

**Test API:**
```
https://your-app.vercel.app?url=PRODUCT_URL
```

### For Streamlit Cloud (UI) - New Deployment

1. **Push to GitHub** (if not already)
   ```bash
   git add .
   git commit -m "Add Streamlit app"
   git push origin main
   ```

2. **Go to Streamlit Cloud**
   - Visit: https://streamlit.io/cloud
   - Sign in with GitHub
   - Click "New app"

3. **Configure Deployment**
   - Repository: Your GitHub repo
   - Branch: `main`
   - Main file: `app.py`
   - Python version: 3.12

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Your Streamlit app will be live!

---

## 🔗 Hybrid Setup: Streamlit → Vercel API

If you want Streamlit to call your Vercel API, update `app.py`:

```python
# In app.py, replace scrape_markaz_product() call with:
import requests

VERCEL_API_URL = "https://your-app.vercel.app"

def scrape_via_api(url):
    """Call Vercel API for scraping"""
    try:
        response = requests.get(f"{VERCEL_API_URL}?url={url}")
        if response.status_code == 200:
            return response.json()
        else:
            return {'status': f'Error: {response.status_code}'}
    except Exception as e:
        return {'status': f'Error: {str(e)}'}

# Use in your Streamlit app:
# product_data = scrape_via_api(url_input)
```

---

## 📊 Comparison

| Platform | Best For | Pros | Cons |
|----------|----------|------|------|
| **Vercel** | API Endpoints | Fast, serverless, free tier | No Streamlit support |
| **Streamlit Cloud** | Streamlit Apps | Easy, free, WebSocket support | Playwright memory limits |
| **Hybrid** | Best UX | API fast, UI works | Two deployments |

---

## ✅ Recommendation

**Use Hybrid Approach:**
1. ✅ Keep `api/index.py` on Vercel (already working)
2. ✅ Deploy `app.py` on Streamlit Cloud
3. ✅ Optionally connect Streamlit to Vercel API

This gives you:
- Fast API scraping on Vercel
- Beautiful UI on Streamlit Cloud
- Best user experience

---

## 🆘 Troubleshooting

### Vercel API Issues:
- Check function logs in Vercel Dashboard
- Verify `requirements.txt` has all dependencies
- Ensure `vercel.json` routes correctly

### Streamlit Cloud Issues:
- Check build logs
- Verify Python version (3.12)
- Ensure Playwright browsers are installed

---

**Your current Vercel setup is correct for API deployment!** 🎉
