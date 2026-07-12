# Demo Mode

Self-contained demo environment for the Markaz to Shopify Converter.

- No **Supabase**
- No **`api/` routes**
- **localStorage** + per-user JSON files for storage
- **Simulated Shopify** actions
- **Dummy reference data** on first login

## Run Demo Mode

From project root:

```bash
streamlit run demo_mode/app.py
```

## Demo Login Accounts

| Username | Password | Role |
|----------|----------|------|
| `demo` | `demo123` | Demo Admin |
| `viewer` | `view123` | Demo Viewer |

Credentials are shown on the demo login page.

## Storage

Each user gets isolated storage:

- Browser: `localStorage` key `markaz_demo_{username}`
- Server: `demo_mode/data/users/{username}/local_storage.json`

Tracked products and other demo data persist per user between sessions.

## Dummy Data

On first login, sample tracked products are seeded automatically (see `dummy_data.py`).

## Production App

Run the normal app (requires Supabase + Shopify secrets):

```bash
streamlit run app.py
```
