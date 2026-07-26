# Configuration setup

**Version:** 0.1.0  
**Route:** `.streamlit/secrets.toml` (not an in-app screen)  
**Who can access:** deployers / maintainers

## What this page does

Explains the secrets required for production login, Tracked Products (Supabase), and Shopify publish/sync.

## Steps

1. Copy the example file:

   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. Fill each block below.
3. Restart Streamlit (`streamlit run app.py`).
4. Sign in with the `[app_login]` credentials.

### Streamlit Cloud

Paste the same TOML blocks under **App settings → Secrets**. Do not commit `secrets.toml`.

## Secrets reference

### `[app_login]` (required)

| Key | Purpose |
|-----|---------|
| `username` | Dashboard login |
| `password` | Dashboard password |

> Use `[app_login]`, not `[auth]` — Streamlit reserves `[auth]`.

### `[supabase]` (Tracked Products)

| Key | Purpose |
|-----|---------|
| `url` | Project URL `https://….supabase.co` |
| `key` | Service role key |

### `[shopify]`

| Key | Purpose |
|-----|---------|
| `store_url` | `your-store.myshopify.com` |
| `client_id` | Dev Dashboard client ID |
| `client_secret` | Dev Dashboard client secret |
| `api_version` | Optional, default `2024-10` |
| `access_token` | Optional legacy Admin API token |

**Required Admin API scopes:** `read_products`, `write_products`, `read_inventory`, `write_inventory`, `read_locations`.

## Environment fallbacks

`APP_USERNAME`, `APP_PASSWORD`, `SUPABASE_URL`, `SUPABASE_KEY`, `SHOPIFY_STORE_URL`, `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`, `SHOPIFY_ACCESS_TOKEN`, `SHOPIFY_API_VERSION`.

## Errors & edge cases

- Missing login block → login page configuration error.
- Missing Supabase → Tracked Products warns and stops loading.
- Missing Shopify → publish/sync buttons disabled or inactive.
- Demo Mode needs **no** secrets — see [Demo mode](./15-demo-mode.md).

## Related links

- [Getting started](./00-getting-started.md)
- [Login](./01-login-page.md)
- [Export CSV & publish](./08-export-csv-and-publish.md)
