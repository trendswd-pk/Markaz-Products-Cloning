-- ============================================================
-- OPTION B: Table pehle se bani ho (update / migration)
-- Supabase -> SQL Editor -> New query -> paste -> Run
-- ============================================================

-- Missing columns add karo
alter table public.tracked_products
    add column if not exists user_id uuid references auth.users (id) on delete cascade;

alter table public.tracked_products
    add column if not exists shopify_product_id text;

alter table public.tracked_products
    add column if not exists shopify_handle text;

-- Purana single-url unique constraint hatao (agar ho)
alter table public.tracked_products
    drop constraint if exists tracked_products_markaz_url_key;

-- Per-user unique URL (agar pehle se na ho)
do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'tracked_products_user_id_markaz_url_key'
    ) then
        alter table public.tracked_products
            add constraint tracked_products_user_id_markaz_url_key
            unique (user_id, markaz_url);
    end if;
end $$;

-- Indexes
create index if not exists tracked_products_markaz_url_idx
    on public.tracked_products (markaz_url);

create index if not exists tracked_products_stock_status_idx
    on public.tracked_products (stock_status);

create index if not exists tracked_products_user_id_idx
    on public.tracked_products (user_id);

create index if not exists tracked_products_shopify_handle_idx
    on public.tracked_products (shopify_handle);

-- RLS secure karo
alter table public.tracked_products enable row level security;

drop policy if exists "tracked_products_select_own" on public.tracked_products;
drop policy if exists "tracked_products_insert_own" on public.tracked_products;
drop policy if exists "tracked_products_update_own" on public.tracked_products;
drop policy if exists "tracked_products_delete_own" on public.tracked_products;

create policy "tracked_products_select_own"
    on public.tracked_products
    for select
    to authenticated
    using (auth.uid() = user_id);

create policy "tracked_products_insert_own"
    on public.tracked_products
    for insert
    to authenticated
    with check (auth.uid() = user_id);

create policy "tracked_products_update_own"
    on public.tracked_products
    for update
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create policy "tracked_products_delete_own"
    on public.tracked_products
    for delete
    to authenticated
    using (auth.uid() = user_id);
