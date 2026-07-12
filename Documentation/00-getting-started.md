# 00 — Getting Started

## What this app does

Markaz to Shopify Converter scrapes product data from **Markaz** (`markaz.app`) and prepares it for **Shopify** — either as a CSV file or via direct API publish.

## Requirements

- Python 3.12+
- Chromium (via Playwright) — **production only**; not needed for [Demo Mode](./15-demo-mode.md)
- Internet connection

## Step 1: Clone and install

```bash
git clone <repository-url>
cd Markaz-Products-Cloning
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Step 2: Configure secrets

Copy the example secrets file:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` with your credentials. See [14-configuration-setup.md](./14-configuration-setup.md).

## Step 3: Run the app

**Production (real scrape + Shopify + Supabase):**

```bash
streamlit run app.py
```

**Demo (simulated — no secrets, no Playwright):**

```bash
streamlit run demo_mode/app.py
```

See [15-demo-mode.md](./15-demo-mode.md) for demo login and limitations.

Open: **http://localhost:8501**

## Step 4: Login

Use the credentials from `[app_login]` in `secrets.toml`.  
See [01-login-page.md](./01-login-page.md).

## Step 5: Choose your workflow

| Goal | Go to |
|------|--------|
| Scrape & download CSV | [Shopify Converter](./03-shopify-converter-tab.md) |
| Save URLs for later | Add products → auto-saved to [Tracked Products](./09-tracked-products-tab.md) |
| Publish directly to Shopify | [Export & Publish](./08-export-csv-and-publish.md) |
| Try without real APIs | [Demo Mode](./15-demo-mode.md) |

## Project structure (main files)

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit UI |
| `markaz_scraper.py` | Markaz product scraping |
| `shopify_publish.py` | Direct Shopify product create/update |
| `shopify_sync.py` | Inventory & status sync |
| `supabase_store.py` | Tracked products database |
| `pricing_rules.py` | Sale & compare-at price markup |
| `auth.py` | Login page |
| `demo_mode/app.py` | Demo entry (simulated, no secrets) |
| `demo_mode/demo_main.py` | Standalone demo UI |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 8501 busy | `fuser -k 8501/tcp` then restart |
| Playwright error | `playwright install chromium` (production only) |
| Demo crashes / segfault | Use `streamlit run demo_mode/app.py` — do not use `app.py` for demo |
| Login not configured | Add `[app_login]` to secrets.toml |
| Supabase warning | Add `[supabase]` block to secrets.toml |
