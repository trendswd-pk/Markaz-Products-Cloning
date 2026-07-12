# Demo Mode

Self-contained demo environment for the Markaz to Shopify Converter.

- No **Supabase**
- No **`api/` routes**
- **localStorage** + per-user JSON files for storage
- **Simulated Shopify** actions
- **Dummy reference data** on first login

## Run locally

From project root:

```bash
streamlit run demo_mode/app.py
```

## Deploy on Streamlit Cloud

**Wrong** (folder URL — causes error):
```
https://github.com/.../Markaz-Products-Cloning/tree/main/demo_mode
```

**Correct** — paste link to the `.py` file:
```
https://github.com/trendswd-pk/Markaz-Products-Cloning/blob/main/demo_mode/app.py
```

Or use **Switch to interactive picker**:
- Repository: `trendswd-pk/Markaz-Products-Cloning`
- Branch: `main`
- Main file path: `demo_mode/app.py`

No secrets required for demo. Login: `demo` / `demo123`

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
