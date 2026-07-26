# Pricing rules

**Version:** 0.1.0  
**Route:** applied in Converter preview / list (no standalone settings page)  
**Who can access:** signed-in users

![Pricing visible on preview](./images/04-product-preview-and-pricing.png)

## What this page does

Documents the default sale and compare-at markups applied when Markaz prices are converted for Shopify. You can override adjustments per product in the preview or list editors.

## Default adjustments

| Markaz price | Variant (sale) adjustment | Compare-at adjustment |
|--------------|---------------------------|------------------------|
| Less than 2000 | +500 | +2000 |
| 2000 or more | +1500 | +3000 |

- **Final variant price** = Markaz price + variant adjustment  
- **Final compare-at price** = Markaz price + compare-at adjustment  
- CSV **Vendor** = **at One Spot**  
- **Cost per item** = original Markaz price  

## Steps

1. Fetch or add a product so defaults apply.
2. (Optional) Open preview or **✏️ Edit Prices**.
3. Change **Variant Price Adjustment** and/or **Compare At Price Adjustment**.
4. Save / add to list.

## Stock behavior (API publish / sync)

| Markaz stock | Inventory qty | Shopify status |
|--------------|---------------|----------------|
| in_stock | 50 | active |
| out_of_stock | 0 | draft |

CSV export currently uses quantity `50` and status `active` on generated rows.

## Errors & edge cases

- Zero / missing Markaz price still receives the “low price” adjustment path.
- Bulk and category adds always start from these defaults.

## Related links

- [Product preview & pricing](./06-product-preview-and-pricing.md)
- [Product list management](./07-product-list-management.md)
- [Export CSV & publish](./08-export-csv-and-publish.md)
