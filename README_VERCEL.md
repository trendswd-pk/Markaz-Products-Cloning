# ⚠️ Important: Vercel Deployment

## Current Setup

**`requirements.txt`** ab minimal version hai (Playwright aur Streamlit removed) taake Vercel par deploy ho sake.

## ⚠️ Limitations

**Vercel par deploy hone ke baad:**
- ✅ Deploy ho jayega (250 MB limit ke andar)
- ❌ **Scraping nahi chalega** (Playwright nahi hai)
- ❌ **Streamlit app nahi chalegi** (Streamlit nahi hai)
- ✅ Sirf info page dikhega

## 🔄 Full Functionality Ke Liye

Agar aapko **full functionality** chahiye (scraping + Streamlit app):

### Option 1: Streamlit Cloud (Recommended) ⭐

1. **Original requirements restore karein:**
   ```bash
   cp requirements-full.txt requirements.txt
   ```

2. **GitHub par push karein:**
   ```bash
   git add .
   git commit -m "Restore full requirements for Streamlit Cloud"
   git push
   ```

3. **Streamlit Cloud par deploy karein:**
   - [streamlit.io/cloud](https://streamlit.io/cloud) par jayein
   - GitHub repository connect karein
   - Deploy karein

### Option 2: Vercel Par Keep Karein (Limited)

Agar aap Vercel par hi rakhna chahte hain:
- Current setup theek hai
- Lekin scraping nahi chalega
- Sirf info page dikhega

## 📝 Files

- **`requirements.txt`** - Minimal version (Vercel ke liye)
- **`requirements-full.txt`** - Full version (Streamlit Cloud ke liye)
- **`api/app.py`** - Vercel serverless function handler

## 🚀 Deploy

Vercel par deploy karne ke liye:
```bash
vercel --prod
```

Ya GitHub se automatically deploy ho jayega.

---

**Note:** Full functionality ke liye Streamlit Cloud use karein!
