# Vercel Deployment Setup Guide

## 🔧 Environment Variables

Vercel Dashboard mein yeh environment variables add karein:

### Required Environment Variables:

1. **PLAYWRIGHT_BROWSERS_PATH**
   - Value: `0`
   - Description: System browsers use karne ke liye

2. **PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD** (Optional)
   - Value: `0` (browsers download karne ke liye)
   - Ya `1` (agar already installed hain)

### Vercel Dashboard mein Add Karne Ka Tarika:

1. Vercel Dashboard mein apne project mein jayein
2. **Settings** tab click karein
3. **Environment Variables** section mein jayein
4. Add karein:
   - Key: `PLAYWRIGHT_BROWSERS_PATH`
   - Value: `0`
   - Environment: Production, Preview, Development (sab mein)

---

## 🏗️ Build Command

Vercel Dashboard mein **Build & Development Settings** section mein:

### ⚠️ IMPORTANT: Vercel uses `uv` (not `pip`)

Vercel automatically installs dependencies using `uv`. **DO NOT** use `pip install` in build command.

### Install Command:
**Leave empty** - Vercel automatically installs from `requirements.txt` using `uv`

### Build Command:
```bash
python -m playwright install chromium && python -m playwright install-deps chromium
```

**Alternative (if above doesn't work):**
```bash
playwright install chromium && playwright install-deps chromium
```

**Important Notes:**
- Vercel automatically installs Python packages from `requirements.txt` using `uv`
- We only need to install Playwright browsers AFTER dependencies are installed
- Use `python -m playwright` to ensure we're using the correct Python environment

---

## 📝 vercel.json Configuration

Current `vercel.json` clean hai aur properly configured hai:
- No conflicting builds
- Proper routes
- Memory settings (1024 MB)
- Max duration (60 seconds)

---

## ✅ Deployment Steps

1. **Environment Variables Add Karein (Optional):**
   - Vercel Dashboard → Settings → Environment Variables
   - `PLAYWRIGHT_BROWSERS_PATH` = `0` (optional, system browsers use karne ke liye)

2. **Build Command Set Karein:**
   - Vercel Dashboard → Settings → Build & Development Settings
   - **Install Command:** (Leave empty - Vercel automatically installs using `uv`)
   - **Build Command:** `python -m playwright install chromium && python -m playwright install-deps chromium`
   
   **⚠️ Important:** Vercel uses `uv` package manager, NOT `pip`. Do NOT use `pip install` in build commands.

3. **vercel.json Configuration:**
   - Already configured with:
     - Memory: 1024 MB
     - Max Duration: 60 seconds
     - Browser flags: `--no-sandbox`, `--disable-setuid-sandbox`, `--disable-dev-shm-usage`, `--single-process`, `--disable-gpu`
     - Headless mode: `true` (hardcoded)

4. **Deploy:**
   - GitHub se automatically deploy hoga
   - Ya manually: `vercel --prod`

5. **Test:**
   - Visit: `https://your-app.vercel.app`
   - Test scraping: `https://your-app.vercel.app?url=PRODUCT_URL`

---

## ⚠️ Important Notes

1. **Size Limit:** Playwright + Chromium ~165 MB hai. Agar 250 MB limit exceed ho to:
   - Pro plan upgrade karein (512 MB unzipped limit)
   - Ya Playwright remove karein (but scraping nahi hoga)

2. **Memory:** 1024 MB set kiya hai (vercel.json mein). Agar zyada chahiye to:
   - Pro plan upgrade karein (max 3008 MB)
   - Ya memory optimize karein (browser flags already added)

3. **Timeout:** 60 seconds set kiya hai (vercel.json mein). Agar zyada chahiye to:
   - `maxDuration` increase karein (max 300 seconds for Pro)
   - Ya scraping logic optimize karein

4. **Browser Optimization:**
   - All memory-saving flags already added:
     - `--no-sandbox`
     - `--disable-setuid-sandbox`
     - `--disable-dev-shm-usage`
     - `--single-process`
     - `--disable-gpu`
   - Headless mode: `true` (hardcoded)

5. **Breadcrumb Extraction:**
   - Fixed to only use `main a[href*="/explore"]` selector
   - Prevents picking up 'Followers' and 'Products' text

---

## 🔍 Troubleshooting

### gitSource missing repoId Error:
- ✅ `vercel.json` se `builds` property remove kar di hai
- ✅ Routes properly configured hain
- ✅ No conflicting configurations

### Playwright Not Found / Build Failed:
- ✅ **DO NOT** use `pip install` in build command (Vercel uses `uv`)
- ✅ Install Command: Leave empty (Vercel auto-installs)
- ✅ Build Command: `python -m playwright install chromium && python -m playwright install-deps chromium`
- ✅ Environment variable `PLAYWRIGHT_BROWSERS_PATH=0` set karein (optional)

### "externally-managed-environment" Error:
- ✅ This happens when trying to use `pip` in a `uv`-managed environment
- ✅ Solution: Remove `pip install -r requirements.txt` from build command
- ✅ Vercel automatically installs dependencies using `uv`
- ✅ Only run `playwright install` commands in Build Command

### Memory Issues:
- ✅ Browser flags add kiye hain (--no-sandbox, --single-process)
- ✅ Browser immediately close ho raha hai
- ✅ Memory 1024 MB set kiya hai

---

## 📋 Checklist

- [ ] Environment variables add kiye
- [ ] Build command set kiya
- [ ] vercel.json clean hai
- [ ] GitHub repository connected hai
- [ ] Deploy successful hai

---

**Ab Vercel Dashboard mein settings update karein aur deploy karein!** 🚀
