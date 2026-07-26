# Markaz-Products-Cloning-Doc

Portfolio-style English documentation for **Markaz to Shopify Converter**.

## Contents

- `index.md` — docs home
- `APP-VERSION.md` / `CHANGELOG.md` / `version.json` — version sync
- `_meta/navigation.json` — sidebar for the Trends WD docs viewer
- `00-…` / `01-…` guides — one file per screen or topic
- `images/` — PNG screenshots only

## How to refresh

1. Update guides when the UI changes.
2. Re-run screenshots (demo mode):

   ```bash
   source venv/bin/activate
   python scripts/capture_docs_screenshots.py --port 8501
   ```

3. Keep version fields equal in `version.json`, `APP-VERSION.md`, `index.md`, and `_meta/navigation.json`.

## Screenshots still needed

These production-only (or alternate) shots are not in `images/` yet — guides use placeholders or nearby demo shots where noted:

- `05-add-products-multiple-mode.png` — Multiple URL paste UI (production)
- `16-add-products-category-mode.png` — Category + From/To page UI (production)
- `08-download-shopify-csv.png` — CSV download button row (production; demo has no CSV)
- `09-tracked-filters.png` — Markaz / Shopify filter radios (production)
- `14-configuration-secrets.png` — optional; config is file-based, not an in-app screen

Existing captures are from **Demo Mode** (`demo` / `demo123`).
