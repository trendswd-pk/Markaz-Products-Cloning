# 01 — Login Page

**Location:** First screen when opening the app (before dashboard)

## Purpose

Protects the app so only authorized users can access the Markaz scraper and Shopify tools.

## Step-by-step

### Step 1: Open the app

```bash
streamlit run app.py
```

Browser opens at `http://localhost:8501`

### Step 2: See the login form

You will see:
- **Title:** Login
- **Caption:** Markaz to Shopify Converter — authorized access only
- **Username** field
- **Password** field
- **Sign in** button

### Step 3: Enter credentials

Credentials are stored in `.streamlit/secrets.toml`:

```toml
[app_login]
username = "your_username"
password = "your_strong_password"
```

> **Note:** Use `[app_login]` — not `[auth]`. Streamlit reserves `[auth]` for its own system.

### Step 4: Click **Sign in**

- Correct credentials → dashboard loads
- Wrong credentials → red error: *Invalid username or password*

### Step 5: After login

- Top of dashboard shows: **Signed in as {username}**
- **Logout** button appears top-right
- Browser URL may include `?auth=...` (signed session token)

## Session persistence (page refresh)

Login survives **browser refresh** for up to **14 days**.

| Mechanism | Detail |
|-----------|--------|
| Token | HMAC-signed string in URL query param `auth` |
| Contents | Username + expiry + signature (password is not stored in the URL) |
| Restore | On load, valid token restores `session_state` without re-typing credentials |
| Logout | Clears session and removes the token from the URL |

If you open a bookmark **without** the `auth` query param, or the token expires / password in secrets changes, you must sign in again.

## Error: Login not configured

If `[app_login]` is missing from secrets, a red error box explains how to add it.

## Logout

1. Click **Logout** (top-right on dashboard)
2. Session and auth token clear
3. Login page shows again

## Security notes

- Passwords are compared securely (`hmac.compare_digest`)
- `secrets.toml` is gitignored — never commit it
- Auth token signature uses credentials from secrets; do not share logged-in URLs publicly

## Demo Mode login

Demo Mode is a **separate app** with its own login page and built-in accounts (`demo` / `demo123`).  
It does not use `secrets.toml`.  
See [15-demo-mode.md](./15-demo-mode.md).
