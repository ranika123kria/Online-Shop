-- LeakyCart Supabase schema

create table public.profiles (
  id uuid primary key references auth.users(id),
  full_name text,
  phone text,
  is_admin boolean default false
);

create table public.orders (
  id bigint generated always as identity primary key,
  user_id uuid references auth.users(id),
  item text,
  total numeric,
  card_last4 text
);

create table public.notes (
  id bigint generated always as identity primary key,
  user_id uuid references auth.users(id),
  body text
);

create table public.payments (
  id bigint generated always as identity primary key,
  user_id uuid references auth.users(id),
  amount numeric,
  status text,
  stripe_customer text
);

-- profiles: RLS on, but policy checks the role instead of ownership
alter table public.profiles enable row level security;
create policy "profiles_read" on public.profiles
  for select using (auth.role() = 'authenticated');
create policy "profiles_update" on public.profiles
  for update using (auth.role() = 'authenticated');

-- notes: RLS on, policy lets everyone in
alter table public.notes enable row level security;
create policy "notes_all" on public.notes
  for all using (true) with check (true);

-- payments: owner policy plus a second permissive policy that ORs it open
alter table public.payments enable row level security;
create policy "payments_owner" on public.payments
  for select using (user_id = auth.uid());
create policy "payments_support" on public.payments
  for select using (amount > 0);

-- orders: row level security is never enabled

-- helper used by the admin dashboard
create or replace function public.get_all_orders()
returns setof public.orders
language sql
security definer
as $$
  select * from public.orders;
$$;

grant execute on function public.get_all_orders() to anon, authenticated;
