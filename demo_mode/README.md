# Demo Mode

Self-contained demo environment for the Markaz to Shopify Converter.

- **Standalone UI** (`demo_main.py`) — does not import production `app.py`
- No **Supabase**
- No **real Shopify API** (simulated publish/sync/delete)
- No **live Markaz scraping** (simulated from pasted URL)
- No **Playwright** / Chromium required
- **Per-user JSON files** on server for storage
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

No secrets required. Login: `demo` / `demo123`

## Demo Login Accounts

| Username | Password | Role |
|----------|----------|------|
| `demo` | `demo123` | Demo Admin |
| `viewer` | `view123` | Demo Viewer |

Credentials are shown on the demo login page.

## Storage

Each user gets isolated server-side JSON:

- `demo_mode/data/users/{username}/local_storage.json`

Tracked products persist per username between sessions on the same machine.

## What works in demo

| Action | Behavior |
|--------|----------|
| Fetch Product Data | Simulated title/price from URL |
| Add to List | Saves to converter list + tracked JSON |
| Publish / Sync Shopify | Simulated + warning banner |
| Tracked Products | 3 dummy products seeded on first login |
| Delete tracked row | Removes from JSON only |

## Production App

Run the normal app (requires Supabase + Shopify secrets + Playwright):

```bash
streamlit run app.py
```

Full documentation: [Documentation/15-demo-mode.md](../Documentation/15-demo-mode.md)
