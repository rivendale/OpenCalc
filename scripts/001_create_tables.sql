-- Profiles table for user metadata
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  username text,
  accesslevel integer default 0,
  statuscode integer default 0,
  invitedby text,
  totaltrades integer default 0,
  opentrades integer default 0,
  ranking integer default 0,
  registered_on timestamptz default now()
);

alter table public.profiles enable row level security;
create policy "profiles_select_own" on public.profiles for select using (auth.uid() = id);
create policy "profiles_insert_own" on public.profiles for insert with check (auth.uid() = id);
create policy "profiles_update_own" on public.profiles for update using (auth.uid() = id);
create policy "profiles_delete_own" on public.profiles for delete using (auth.uid() = id);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, username)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'username', split_part(new.email, '@', 1))
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row
  execute function public.handle_new_user();

-- Tickers table (user watchlist)
create table if not exists public.tickers (
  id bigint generated always as identity primary key,
  symbol text not null,
  notes text default 'None',
  category text default 'None',
  timestamp timestamptz default now(),
  nextearnings text default 'No Data',
  user_id uuid not null references auth.users(id) on delete cascade,
  priceobj float default 0,
  earnsurprise float default 0,
  tprice float default 0,
  tvol float default 0,
  tdesc text default '',
  ttype text default ''
);

alter table public.tickers enable row level security;
create policy "tickers_select_own" on public.tickers for select using (auth.uid() = user_id);
create policy "tickers_insert_own" on public.tickers for insert with check (auth.uid() = user_id);
create policy "tickers_update_own" on public.tickers for update using (auth.uid() = user_id);
create policy "tickers_delete_own" on public.tickers for delete using (auth.uid() = user_id);

create index if not exists idx_tickers_user_id on public.tickers(user_id);
create index if not exists idx_tickers_symbol on public.tickers(symbol);

-- Trades table
create table if not exists public.trades (
  id bigint generated always as identity primary key,
  symbol text not null,
  putorcall text default 'P',
  note text default 'initiated',
  strat integer default 1,
  expirationdate text,
  strike1 float default 0,
  strike2 float default 0,
  initprem float default 0,
  initnumdays integer default 0,
  daysleft integer default 0,
  currprem float default 0,
  premclosed float default 0,
  premcap float default 0,
  status integer default 1,
  initqty integer default 1,
  ror float default 0,
  otm float default 0,
  opti float default 0,
  user_id uuid not null references auth.users(id) on delete cascade
);

alter table public.trades enable row level security;
create policy "trades_select_own" on public.trades for select using (auth.uid() = user_id);
create policy "trades_insert_own" on public.trades for insert with check (auth.uid() = user_id);
create policy "trades_update_own" on public.trades for update using (auth.uid() = user_id);
create policy "trades_delete_own" on public.trades for delete using (auth.uid() = user_id);

create index if not exists idx_trades_user_id on public.trades(user_id);
create index if not exists idx_trades_status on public.trades(status);

-- Strikes table (cached option chain data)
create table if not exists public.strikes (
  id bigint generated always as identity primary key,
  idtext text,
  symbol text not null,
  putorcall text default 'P',
  expirationdate text,
  strike float default 0,
  premium float default 0,
  volume float default 0,
  numdays integer default 0,
  updatedon timestamptz default now(),
  oai text default 'O',
  oi float default 0,
  opti float default 0
);

alter table public.strikes enable row level security;
create policy "strikes_select_all" on public.strikes for select using (true);
create policy "strikes_insert_auth" on public.strikes for insert with check (auth.uid() is not null);
create policy "strikes_update_auth" on public.strikes for update using (auth.uid() is not null);
create policy "strikes_delete_auth" on public.strikes for delete using (auth.uid() is not null);

create index if not exists idx_strikes_symbol on public.strikes(symbol);
create index if not exists idx_strikes_putorcall on public.strikes(putorcall);
create index if not exists idx_strikes_expdate on public.strikes(expirationdate);
