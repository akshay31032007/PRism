-- PRism analysis history table
-- Run in Supabase SQL Editor or via supabase db push

create table if not exists public.analysis_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  analysis_id text not null,
  pr_url text not null,
  pr_title text not null,
  repo text not null,
  verdict text not null check (verdict in ('READY_TO_MERGE', 'CAUTION', 'BLOCKED')),
  confidence double precision not null,
  latency_seconds double precision not null,
  analysed_at timestamptz not null,
  agent_count integer not null,
  blocking_issues integer not null,
  created_at timestamptz not null default now(),
  unique (user_id, analysis_id)
);

create index if not exists analysis_history_user_id_created_at_idx
  on public.analysis_history (user_id, created_at desc);

alter table public.analysis_history enable row level security;

create policy "Users can view own analysis history"
  on public.analysis_history
  for select
  using (auth.uid() = user_id);

create policy "Users can insert own analysis history"
  on public.analysis_history
  for insert
  with check (auth.uid() = user_id);

create policy "Users can delete own analysis history"
  on public.analysis_history
  for delete
  using (auth.uid() = user_id);
