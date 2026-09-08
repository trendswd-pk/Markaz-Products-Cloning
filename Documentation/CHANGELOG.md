# Changelog

All notable changes to Markaz to Shopify Converter are documented here.

## [1.0.0] — 2026-09-08

### Added
- Portfolio Demo Mode polish: Trends WD favicon, clickable demo account cards, and **Reset demo data**
- `demo_mode/demo.json` for portfolio Live Demo wiring (`type`: `web-app`)
- Canonical documentation pack under `Documentation/` with screenshot pipeline to `Documentation/images/`
- Cursor rules for changelog, version sync, and demo/production separation
- Professional root README with documentation screenshots
- Mobile documentation screenshots (login, dashboard, tracked products)

### Changed
- Demo login accounts aligned to Admin / Editor / Viewer cards (`admin@admin.com`, `demo`, `viewer@demo.com`)
- Screenshot capture output path moved to `Documentation/images/`

### Fixed
- Main Vercel deploy ignore list now excludes `demo_mode/` and `Documentation/` so the demo stays a separate host

## [0.1.0] — 2026-07-26

### Added
- Portfolio docs pack (originally under `Markaz-Products-Cloning-Doc/`)
- Demo Mode without Supabase, Playwright, or real Shopify
- Tracked Products with Shopify Active / Draft / Not on Shopify status
- Category scrape into the Converter list
- 14-day login session across refresh

### Changed
- CSV includes variant images, weights, and category fields

## 2026-08-11

### Added
- Supabase free-tier keep-alive (GitHub Action, in-app ping, CLI script)

## Earlier

### Added
- Category URL discovery and bulk URL paste
- Direct Shopify publish and stock sync
- Vendor name **at One Spot**
- Pricing markups for sale and compare-at prices
- Supabase-backed tracked product storage
