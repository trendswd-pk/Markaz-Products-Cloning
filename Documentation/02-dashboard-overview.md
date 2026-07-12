# 02 — Dashboard Overview

**Location:** Main screen after successful login

## Layout

```
┌─────────────────────────────────────────────────────────┐
│  Signed in as admin                    [Logout]           │
│  Markaz to Shopify CSV Converter                        │
│  Scrape Markaz product data and convert to Shopify...   │
│                                                         │
│  [Shopify publish feedback banner — if any]             │
│                                                         │
│  ┌──────────────────┬──────────────────────┐           │
│  │ Shopify Converter│ Tracked Products     │           │
│  └──────────────────┴──────────────────────┘           │
│                                                         │
│  (Tab content here)                                     │
└─────────────────────────────────────────────────────────┘
```

## Step-by-step: First visit

### Step 1: Confirm you are logged in

Top-left shows **Signed in as {username}**.

### Step 2: Read the page title

**Markaz to Shopify CSV Converter** — main heading.

### Step 3: Check publish feedback (if visible)

After a Shopify publish action, a green/yellow/red feedback banner may appear at the top with:
- Created / Updated counts
- Warnings (e.g. stock sync skipped)
- Errors (e.g. missing Shopify scope)

Click **Dismiss publish results** to hide it.  
Details: [12-shopify-publish-feedback.md](./12-shopify-publish-feedback.md)

### Step 4: Choose a tab

| Tab | Use for |
|-----|---------|
| **Shopify Converter** | Scrape Markaz URLs, build product list, CSV export, publish |
| **Tracked Products** | View saved URLs, stock status, Shopify sync |

### Step 5: Start working

- New products → **Shopify Converter** tab  
  See [03-shopify-converter-tab.md](./03-shopify-converter-tab.md)
- Saved products → **Tracked Products** tab  
  See [09-tracked-products-tab.md](./09-tracked-products-tab.md)

## Two main workflows

### A) One-time bulk export
Converter → Add URLs → Download CSV → Import in Shopify Admin

### B) Ongoing product management
Converter → Add URL (auto-saves) → Tracked Products → Refresh / Sync / Publish

## Session data (in memory)

While the app is open, these persist in your browser session:

| Data | Purpose |
|------|---------|
| `products_list` | Products in Converter ready for CSV/publish |
| `processed_urls` | Prevents duplicate URL adds |
| `shopify_status_map` | Cached Shopify status for Tracked Products |
| `shopify_publish_feedback` | Last publish result message |

**Note:** Converter product list clears when you close the browser tab. Tracked Products persist in Supabase.
