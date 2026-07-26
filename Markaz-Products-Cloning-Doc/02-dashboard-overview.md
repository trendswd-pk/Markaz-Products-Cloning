# Dashboard overview

**Version:** 0.1.0  
**Route:** `/` (authenticated home)  
**Who can access:** signed-in users

![Dashboard overview](./images/02-dashboard-overview.png)

![Logout control](./images/19-logout-control.png)

## What this page does

After login you see the main shell: who is signed in, the product title, and a switch between **Shopify Converter** and **Tracked Products**.

## Layout at a glance

| Area | Content |
|------|---------|
| Top | Demo banner (demo only); **Signed in as …**; **Logout** |
| Header | **Markaz to Shopify CSV Converter** + short caption |
| Nav | Production: horizontal radio — `Shopify Converter` \| `Tracked Products`. Demo: same labels as **tabs** |
| Main | Active section body |

## Steps

1. Confirm **Signed in as** shows your username.
2. Choose **Shopify Converter** to scrape / build a product list.
3. Choose **Tracked Products** to manage saved Markaz URLs.
4. Click **Logout** to clear the session and return to [Login](./01-login-page.md).

![Logout button](./images/23-button-logout.png)

## Permissions

| Action | Allowed |
|--------|---------|
| View both sections | Yes (all signed-in users) |
| Logout | Yes |

There are no separate View / Edit roles in production.

## Errors & edge cases

- If Shopify or Supabase secrets are missing, some buttons disable or show warnings inside each section (the shell still loads).

## Related links

- [Shopify Converter tab](./03-shopify-converter-tab.md)
- [Tracked Products tab](./09-tracked-products-tab.md)
- [Login](./01-login-page.md)
- [Demo mode](./15-demo-mode.md)
