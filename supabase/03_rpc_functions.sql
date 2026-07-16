-- ============================================================
-- RPC functions — fewer round-trips from Streamlit backend
-- Supabase -> SQL Editor -> New query -> paste -> Run
-- Run after 01_fresh_install.sql or 02_update_existing_table.sql
-- ============================================================

-- Optional: one row per Markaz URL for service_role / single-tenant app.
-- Skipped automatically if duplicate markaz_url rows already exist (dedupe first).
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

-- -----------------------------------------------------------------
-- List all tracked products (1 HTTP call from Python)
-- -----------------------------------------------------------------
create or replace function public.list_tracked_products_rpc()
returns json
language sql
stable
security definer
set search_path = public
as $$
    select coalesce(
        json_agg(row_to_json(t) order by t.created_at desc),
        '[]'::json
    )
    from public.tracked_products t;
$$;

-- -----------------------------------------------------------------
-- Upsert one product (1 HTTP call — update or insert in DB)
-- -----------------------------------------------------------------
create or replace function public.upsert_tracked_product_rpc(
    p_markaz_url text,
    p_stock_status text default 'unknown',
    p_title text default null,
    p_shopify_handle text default null,
    p_shopify_product_id text default null,
    p_user_id uuid default null
)
returns json
language plpgsql
security definer
set search_path = public
as $$
declare
    v_row public.tracked_products;
    v_status text;
begin
    if p_markaz_url is null or btrim(p_markaz_url) = '' then
        raise exception 'markaz_url is required';
    end if;

    v_status := case
        when p_stock_status in ('in_stock', 'out_of_stock', 'unknown') then p_stock_status
        else 'unknown'
    end;

    update public.tracked_products
    set
        stock_status = v_status,
        title = coalesce(nullif(btrim(p_title), ''), title),
        shopify_handle = coalesce(nullif(btrim(p_shopify_handle), ''), shopify_handle),
        shopify_product_id = coalesce(nullif(btrim(p_shopify_product_id), ''), shopify_product_id),
        last_checked_at = now()
    where markaz_url = p_markaz_url
    returning * into v_row;

    if not found then
        insert into public.tracked_products (
            markaz_url,
            stock_status,
            title,
            shopify_handle,
            shopify_product_id,
            user_id,
            last_checked_at
        )
        values (
            p_markaz_url,
            v_status,
            nullif(btrim(p_title), ''),
            nullif(btrim(p_shopify_handle), ''),
            nullif(btrim(p_shopify_product_id), ''),
            p_user_id,
            now()
        )
        returning * into v_row;
    end if;

    return row_to_json(v_row);
end;
$$;

-- -----------------------------------------------------------------
-- Batch upsert after "Refresh All" (1 HTTP call for many rows)
-- p_items: [{"markaz_url":"...","stock_status":"in_stock","title":"...","shopify_handle":"..."}]
-- -----------------------------------------------------------------
create or replace function public.batch_upsert_tracked_products_rpc(p_items jsonb)
returns json
language plpgsql
security definer
set search_path = public
as $$
declare
    item jsonb;
    v_row public.tracked_products;
    v_status text;
    v_results jsonb := '[]'::jsonb;
begin
    if p_items is null or jsonb_typeof(p_items) <> 'array' then
        return '[]'::json;
    end if;

    for item in select value from jsonb_array_elements(p_items) as t(value)
    loop
        if coalesce(item->>'markaz_url', '') = '' then
            continue;
        end if;

        v_status := case
            when item->>'stock_status' in ('in_stock', 'out_of_stock', 'unknown')
                then item->>'stock_status'
            else 'unknown'
        end;

        update public.tracked_products
        set
            stock_status = v_status,
            title = coalesce(nullif(btrim(item->>'title'), ''), title),
            shopify_handle = coalesce(nullif(btrim(item->>'shopify_handle'), ''), shopify_handle),
            shopify_product_id = coalesce(
                nullif(btrim(item->>'shopify_product_id'), ''),
                shopify_product_id
            ),
            last_checked_at = now()
        where markaz_url = item->>'markaz_url'
        returning * into v_row;

        if not found then
            insert into public.tracked_products (
                markaz_url,
                stock_status,
                title,
                shopify_handle,
                shopify_product_id,
                last_checked_at
            )
            values (
                item->>'markaz_url',
                v_status,
                nullif(btrim(item->>'title'), ''),
                nullif(btrim(item->>'shopify_handle'), ''),
                nullif(btrim(item->>'shopify_product_id'), ''),
                now()
            )
            returning * into v_row;
        end if;

        v_results := v_results || jsonb_build_array(to_jsonb(v_row));
    end loop;

    return v_results::json;
end;
$$;

-- -----------------------------------------------------------------
-- Batch Shopify metadata update (1 HTTP call)
-- -----------------------------------------------------------------
create or replace function public.batch_update_shopify_metadata_rpc(p_items jsonb)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
    item jsonb;
    v_updated integer := 0;
begin
    if p_items is null or jsonb_typeof(p_items) <> 'array' then
        return 0;
    end if;

    for item in select value from jsonb_array_elements(p_items) as t(value)
    loop
        if coalesce(item->>'markaz_url', '') = '' then
            continue;
        end if;

        update public.tracked_products
        set
            shopify_product_id = coalesce(
                nullif(btrim(item->>'shopify_product_id'), ''),
                shopify_product_id
            ),
            shopify_handle = coalesce(
                nullif(btrim(item->>'shopify_handle'), ''),
                shopify_handle
            )
        where markaz_url = item->>'markaz_url';

        if found then
            v_updated := v_updated + 1;
        end if;
    end loop;

    return v_updated;
end;
$$;

-- -----------------------------------------------------------------
-- Delete many URLs (1 HTTP call)
-- -----------------------------------------------------------------
create or replace function public.delete_tracked_products_rpc(p_markaz_urls text[])
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
    v_deleted integer;
begin
    if p_markaz_urls is null or array_length(p_markaz_urls, 1) is null then
        return 0;
    end if;

    delete from public.tracked_products
    where markaz_url = any (p_markaz_urls);

    get diagnostics v_deleted = row_count;
    return v_deleted;
end;
$$;

-- Allow service_role (Streamlit secrets) to call RPCs
grant execute on function public.list_tracked_products_rpc() to service_role;
grant execute on function public.upsert_tracked_product_rpc(text, text, text, text, text, uuid) to service_role;
grant execute on function public.batch_upsert_tracked_products_rpc(jsonb) to service_role;
grant execute on function public.batch_update_shopify_metadata_rpc(jsonb) to service_role;
grant execute on function public.delete_tracked_products_rpc(text[]) to service_role;
