# Product preview and pricing

**Version:** 0.1.0  
**Route:** `/` → **Shopify Converter** → Single → **Fetch Product Data**  
**Who can access:** signed-in users

![Product preview](./images/04-product-preview-and-pricing.png)

## What this page does

Shows scraped (or demo-simulated) product details and lets you adjust **Sale Price Adjustment** and **Compare At Price Adjustment** before adding to the list. Defaults come from the global **Pricing Settings** (Delivery Charges + Margin %) at the top of the Converter tab.

## Layout at a glance

| Area | Content |
|------|---------|
| Pricing Settings | Delivery Charges + Margin % (applies to all fetch modes + list) |
| Preview | Title, price, SKU, image (or image URL caption in demo) |
| Pricing | Adjustment number inputs + live final prices (production) |
| Actions | **✅ Add to List** · **❌ Cancel** (production) / **Add preview to list** (demo) |

## Steps

1. (Optional) Set **Delivery Charges** and **Margin %** at the top.
2. In Single mode, paste a **Product URL**.
3. Click **📥 Fetch Product Data** (or **Fetch Product Data** in demo).
4. Review title, price, and SKU.
5. (Production) Change adjustments if needed; watch **Final Sale Price** / **Final Compare At**.
6. Click **✅ Add to List** / **Add preview to list**, or **❌ Cancel** to discard the preview.

## Form fields (production preview)

| Label | Type | Required | Notes |
|-------|------|----------|-------|
| Sale Price Adjustment | number | no | Default from [pricing rules](./13-pricing-rules.md) |
| Compare At Price Adjustment | number | no | Default = Markaz × 2 − Markaz |

## Errors & edge cases

- Cancel clears the preview without adding.
- Demo shows: “Demo preview simulated from your pasted URL.”

## Related links

- [Pricing rules](./13-pricing-rules.md)
- [Add products — Single](./04-add-products-single-mode.md)
- [Product list management](./07-product-list-management.md)
