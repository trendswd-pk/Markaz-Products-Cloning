# Getting started

**Version:** 0.1.0  
**Route:** local install / first run  
**Who can access:** anyone with the repo (production needs secrets; demo does not)

## What this guide covers

How to install dependencies, choose production vs Demo Mode, and open the dashboard for the first time.

## Layout at a glance

| Area | Purpose |
|------|---------|
| Terminal | Install and run Streamlit |
| Browser | `http://localhost:8501` |
| Secrets file | Production login + Supabase + Shopify |

## Steps

### 1. Clone and create a virtualenv

```bash
git clone <repository-url>
cd Markaz-Products-Cloning
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Choose how to run

**Demo Mode** (no secrets, simulated Markaz / Shopify):

```bash
streamlit run demo_mode/app.py
```

Open **http://localhost:8501** and sign in with `demo` / `demo123`. See [Demo mode](./15-demo-mode.md).

**Production** (live scrape + Supabase + Shopify):

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit secrets.toml — see Configuration
streamlit run app.py
```

See [Configuration setup](./14-configuration-setup.md).

### 3. First login

1. Enter **Username** and **Password**.
2. Click **Sign in** (production) or **Sign in to Demo**.
3. You land on the dashboard with sections **Shopify Converter** and **Tracked Products**.

## Errors & edge cases

- Missing Chromium in production → install with `playwright install chromium`.
- Production without `[app_login]` → login page shows a configuration error.
- Port in use → Streamlit offers another port, or pass `--server.port 8502`.

## Related links

- [Login](./01-login-page.md)
- [Configuration setup](./14-configuration-setup.md)
- [Demo mode](./15-demo-mode.md)
- [Dashboard overview](./02-dashboard-overview.md)
