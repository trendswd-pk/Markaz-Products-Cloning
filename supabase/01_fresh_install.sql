-- ============================================================
-- OPTION A: Pehli dafa table banana ho (fresh install)
-- Supabase -> SQL Editor -> New query -> paste -> Run
-- ============================================================

create table if not exists public.tracked_products (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users (id) on delete cascade,
    markaz_url text not null,
    title text,
    stock_status text not null default 'unknown'
        check (stock_status in ('in_stock', 'out_of_stock', 'unknown')),
    last_checked_at timestamptz not null default now(),
    shopify_product_id text,
    shopify_handle text,
    created_at timestamptz not null default now(),
    unique (user_id, markaz_url)
);

create index if not exists tracked_products_markaz_url_idx
    on public.tracked_products (markaz_url);

create index if not exists tracked_products_stock_status_idx
    on public.tracked_products (stock_status);

create index if not exists tracked_products_user_id_idx
    on public.tracked_products (user_id);

create index if not exists tracked_products_shopify_handle_idx
    on public.tracked_products (shopify_handle);

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
