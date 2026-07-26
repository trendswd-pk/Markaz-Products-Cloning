# Changelog

## 2026-07-26

### Documentation

- Portfolio docs pack created under `Markaz-Products-Cloning-Doc/`
- Wired demo-mode screenshots into page guides ([Login](./01-login-page.md), [Tracked Products](./09-tracked-products-tab.md), and related pages)

### Product (current 0.1.0 snapshot)

- Tracked Products shows live Shopify status (Active / Draft / Not on Shopify)
- Category scrape adds products page-by-page into the Converter list
- CSV includes variant images, weights, and category fields
- Demo Mode runs without Supabase, Playwright, or real Shopify
- Login session survives browser refresh for 14 days

## 2026-07-18

### Tracked Products

- Shopify status draft / active indicators on the Tracked page
- Improved tracked-row Shopify metadata display

## Earlier

### Converter & publish

- Category URL discovery and bulk URL paste
- Direct Shopify publish and stock sync
- Vendor name set to **at One Spot**
- Pricing markups for sale and compare-at prices

### Platform

- Supabase-backed tracked product storage
- Demo Mode with per-user JSON storage
