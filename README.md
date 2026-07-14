# Markaz to Shopify Converter

Scrape product data from [Markaz](https://www.markaz.app), export Shopify-ready CSV, track URLs in Supabase, and publish or sync stock directly to Shopify. Store vendor name: **at One Spot**.

Full step-by-step guides: **[Documentation/](./Documentation/README.md)**  
Recent changes: **[Documentation/CHANGELOG.md](./Documentation/CHANGELOG.md)**

---

## Features

- **Markaz scraping** (Playwright) — title, description, price, images, SKU, variants, breadcrumbs, stock status
- **Add modes** — Single product URL, Multiple URLs, or **Category** page + page range
- **Shopify CSV** — all 48 required columns; Vendor = `at One Spot`
- **Direct Shopify publish** — create/update products, images, inventory, status
- **Tracked Products** (Supabase) — auto-save on add; Markaz + Shopify filters; pagination (50/page); bulk refresh, sync, publish, delete
- **Login** — credentials in secrets; session token survives refresh for 14 days
- **Demo mode** — simulated scrape/Shopify with no secrets or Playwright
- **Pricing rules** — sale + compare-at markups (editable per product)

---

## Quick Start

### 1. Clone and install

```bash
git clone <repository-url>
cd Markaz-Products-Cloning
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure secrets

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` with `[app_login]`, `[supabase]`, and `[shopify]`.  
See [Documentation/14-configuration-setup.md](./Documentation/14-configuration-setup.md).

### 3. Run

**Production** (real Markaz + Shopify + Supabase):

```bash
streamlit run app.py
```

**Demo** (no secrets / no Playwright required):

```bash
streamlit run demo_mode/app.py
```

Open **http://localhost:8501**

---

## How to use (production)

1. **Sign in** with `[app_login]` credentials.
2. Choose a section:
   - **Shopify Converter** — scrape and build a product list, then CSV download or Publish All
   - **Tracked Products** — manage saved URLs, filter, sync, publish, or delete
3. **Add products** via Single, Multiple, or Category mode.
4. **Export** — Download Shopify CSV and import in Admin, or publish via API.
5. **Track** — products auto-save to Supabase; use filters and bulk actions as needed.

---

## Project structure

```
Markaz-Products-Cloning/
├── app.py                  # Production Streamlit UI
├── markaz_scraper.py       # Markaz scraping (product + category)
├── shopify_publish.py      # Create/update products on Shopify
├── shopify_sync.py         # Inventory & status sync
├── shopify_auth.py         # Shopify OAuth client credentials
├── supabase_store.py       # Tracked products persistence
├── pricing_rules.py        # Sale / compare-at markups
├── auth.py                 # Login + session token
├── demo_mode/              # Standalone demo (simulated)
├── api/index.py            # Optional Vercel scrape API
├── Documentation/          # English user guides + changelog
├── requirements.txt
└── packages.txt            # System deps (Streamlit Cloud)
```

---

## Pricing logic

| Markaz price | Sale adjustment | Compare-at adjustment |
|--------------|-----------------|------------------------|
| &lt; 2000 | +500 | +2000 |
| ≥ 2000 | +1500 | +3000 |

- Sale price = Markaz + sale adjustment  
- Compare at = Markaz + compare-at adjustment  
- Vendor on CSV and API publish: **at One Spot**

Details: [Documentation/13-pricing-rules.md](./Documentation/13-pricing-rules.md)

---

## CSV format (summary)

- Handle: `{slugified-title}-{base-sku}`
- Vendor: `at One Spot`
- Variants with unique SKUs; multiple image rows
- Inventory qty 50 (in stock) / 0 (out of stock); policy `continue`
- Status: `active` or `draft` from stock

---

## Deployment

### Streamlit Community Cloud

1. Push to GitHub  
2. Deploy at [streamlit.io/cloud](https://streamlit.io/cloud) — main file `app.py`  
3. Add secrets in the Cloud app settings (`app_login`, `supabase`, `shopify`)  
4. Ensure `requirements.txt` and `packages.txt` are present  

### Vercel (optional scrape API)

```
GET https://your-app.vercel.app?url=PRODUCT_URL
```

Uses `api/index.py` + `vercel.json`. Suitable for JSON scrape responses, not the full Streamlit dashboard.

---

## Documentation index

| Topic | Link |
|-------|------|
| Getting started | [00](./Documentation/00-getting-started.md) |
| Login | [01](./Documentation/01-login-page.md) |
| Converter / Category mode | [03](./Documentation/03-shopify-converter-tab.md), [16](./Documentation/16-add-products-category-mode.md) |
| Tracked Products | [09](./Documentation/09-tracked-products-tab.md), [10](./Documentation/10-tracked-products-bulk-actions.md) |
| Demo mode | [15](./Documentation/15-demo-mode.md) |
| Configuration | [14](./Documentation/14-configuration-setup.md) |
| Changelog | [CHANGELOG](./Documentation/CHANGELOG.md) |
| Full index | [Documentation/README.md](./Documentation/README.md) |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 8501 busy | `fuser -k 8501/tcp` then restart |
| Playwright missing | `playwright install chromium` (production only) |
| Login not configured | Add `[app_login]` to `.streamlit/secrets.toml` |
| Logged out on refresh | Use latest build; URL should keep `?auth=...` after login |
| Supabase / too many requests | Active section radio only; use **Reload list**; see changelog |
| Demo crashes | Run `streamlit run demo_mode/app.py` — not `app.py` for demo |
| Stale ImportError after code change | Fully stop the Streamlit process and restart |

---

## Notes

- Scraping uses a headless browser; allow a few seconds per product or category page.
- Do not commit `.streamlit/secrets.toml`.
- Demo mode never calls real Shopify when `MARKAZ_DEMO_MODE=1`.

## License

Provided as-is for educational and commercial use.

## Contributing

Pull requests are welcome. For questions or bugs, open a GitHub issue.
