-- ============================================================
-- Dedupe tracked Markaz products (same product id = one row)
-- Supabase -> SQL Editor -> paste -> Run
-- Safe to re-run.
-- ============================================================

-- 1) Add markaz_product_id column (numeric id from URL tail)
alter table public.tracked_products
    add column if not exists markaz_product_id text;

-- 2) Backfill from markaz_url (.../shop/product/slug/123456 or .../123456)
update public.tracked_products
set markaz_product_id = substring(markaz_url from '/shop/product/(?:[^/]+/)?([0-9]+)(?:\?|$|/)?')
where markaz_product_id is null
  and markaz_url ~ '/shop/product/';

-- 3) Merge duplicates: keep best row per markaz_product_id, delete extras
with ranked as (
    select
        id,
        markaz_product_id,
        row_number() over (
            partition by markaz_product_id
            order by
                (shopify_product_id is not null and shopify_product_id <> '') desc,
                (shopify_handle is not null and shopify_handle <> '') desc,
                last_checked_at desc nulls last,
                created_at desc nulls last
        ) as rn
    from public.tracked_products
    where markaz_product_id is not null
      and markaz_product_id <> ''
)
delete from public.tracked_products t
using ranked r
where t.id = r.id
  and r.rn > 1;

-- 4) Unique index so new duplicates cannot be inserted for same product id
create unique index if not exists tracked_products_markaz_product_id_unique_idx
    on public.tracked_products (markaz_product_id)
    where markaz_product_id is not null and markaz_product_id <> '';

-- 5) Also unique on exact markaz_url (service_role / single-tenant)
do $$
begin
    if not exists (
        select 1
        from public.tracked_products
        group by markaz_url
        having count(*) > 1
        limit 1
    ) then
        create unique index if not exists tracked_products_markaz_url_unique_idx
            on public.tracked_products (markaz_url);
    end if;
end $$;
