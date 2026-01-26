# 🔧 Vercel Build Fix - uv Package Manager

## Problem
Vercel is using `uv` package manager (not `pip`), causing build failures when using `pip install` commands.

## Error Message
```
error: externally-managed-environment
× This environment is externally managed
╰─> This Python installation is managed by uv and should not be modified.
```

## ✅ Solution

### Step 1: Vercel Dashboard Settings

1. Go to **Vercel Dashboard** → Your Project → **Settings**
2. Click **Build & Development Settings**
3. Update these fields:

   **Install Command:**
   ```
   (Leave EMPTY - Vercel automatically installs using uv)
   ```

   **Build Command:**
   ```
   python -m playwright install chromium && python -m playwright install-deps chromium
   ```

### Step 2: Why This Works

- ✅ Vercel automatically installs dependencies from `requirements.txt` using `uv`
- ✅ We only need to install Playwright browsers AFTER dependencies are installed
- ✅ Using `python -m playwright` ensures we use the correct Python environment

### Step 3: Alternative Build Command

If the above doesn't work, try:
```bash
playwright install chromium && playwright install-deps chromium
```

## 📋 Checklist

- [ ] Install Command is **EMPTY** (not `pip install`)
- [ ] Build Command contains: `python -m playwright install chromium && python -m playwright install-deps chromium`
- [ ] No `pip install` commands anywhere
- [ ] Redeploy on Vercel

## 🚀 After Fix

1. Save settings in Vercel Dashboard
2. Push to GitHub (or trigger redeploy)
3. Check build logs - should see:
   - ✅ Dependencies installed by `uv`
   - ✅ Playwright browsers installed
   - ✅ Build successful

---

**This fix resolves the "externally-managed-environment" error!** ✅
