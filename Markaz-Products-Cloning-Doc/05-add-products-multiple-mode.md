# Add products — Multiple mode

**Version:** 0.1.0  
**Route:** `/` → **Shopify Converter** → **Multiple**  
**Who can access:** signed-in users (production UI)

> Screenshot placeholder: `./images/05-add-products-multiple-mode.png` (not captured yet — Multiple mode is production-only). Demo Mode has no Multiple mode.

## What this page does

Paste many Markaz product URLs (one per line) and add them in one bulk run with default pricing.

## Layout at a glance

| Area | Content |
|------|---------|
| Mode | **Multiple** |
| Input | **Paste Multiple Product URLs (One per line)** (textarea) |
| Action | **✅ Add to List** |

## Steps

1. Click **Multiple**.
2. Paste one product URL per line.
3. Click **✅ Add to List**.
4. Watch progress (`Link i of n`).
5. When finished, confirm success: bulk fetch complete with a count of added products.

## Form fields

| Label | Type | Required | Notes |
|-------|------|----------|-------|
| Paste Multiple Product URLs (One per line) | textarea | yes | Blank lines ignored |

## Errors & edge cases

- URLs already in the session list are skipped.
- Failed scrapes are skipped; others still add.
- Empty textarea → no products added.

## Related links

- [Add products — Single](./04-add-products-single-mode.md)
- [Add products — Category](./16-add-products-category-mode.md)
- [Product list management](./07-product-list-management.md)
