-- Profiles table: Stores user game stats
create table profiles (
  id uuid references auth.users not null primary key,
  xp integer default 0,
  level integer default 1,
  current_theme text default 'default',
  streak integer default 0,
  last_seen timestamp with time zone default now()
);

-- Habits table: Stores the user's habits to track
create table habits (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  title text not null,
  description text,
  frequency text default 'daily', -- 'daily', 'weekly'
  target_count integer default 1,
  unit text, -- e.g., 'steps', 'minutes', 'pages'
  active boolean default true,
  created_at timestamp with time zone default now()
);

-- Habit Logs: Stores the history of habit completions (Heatmap data)
create table habit_logs (
  id uuid default gen_random_uuid() primary key,
  habit_id uuid references habits not null,
  user_id uuid references auth.users not null,
  completed_at timestamp with time zone default now(),
  count integer default 1, -- For quantitative habits (e.g. 500 steps)
  notes text
);

-- Rewards: Stores items available in the shop or created by the user
create table rewards (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  title text not null,
  cost integer not null,
  is_redeemed boolean default false,
  type text not null -- 'real_world', 'theme_unlock'
);

-- User Themes: Stores which themes the user has unlocked
create table user_themes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  theme_key text not null, -- e.g., 'cyberpunk', 'matrix'
  unlocked_at timestamp with time zone default now()
);

-- Enable Row Level Security (RLS) on all tables
alter table profiles enable row level security;
alter table habits enable row level security;
alter table habit_logs enable row level security;
alter table rewards enable row level security;
alter table user_themes enable row level security;

-- RLS Policies
-- Profiles
create policy "Users can view their own profile" on profiles for select using (auth.uid() = id);
create policy "Users can update their own profile" on profiles for update using (auth.uid() = id);
create policy "Users can insert their own profile" on profiles for insert with check (auth.uid() = id);

-- Habits
create policy "Users can view their own habits" on habits for select using (auth.uid() = user_id);
create policy "Users can insert their own habits" on habits for insert with check (auth.uid() = user_id);
create policy "Users can update their own habits" on habits for update using (auth.uid() = user_id);
create policy "Users can delete their own habits" on habits for delete using (auth.uid() = user_id);

-- Habit Logs
create policy "Users can view their own logs" on habit_logs for select using (auth.uid() = user_id);
create policy "Users can insert their own logs" on habit_logs for insert with check (auth.uid() = user_id);
create policy "Users can update their own logs" on habit_logs for update using (auth.uid() = user_id);

-- Rewards
create policy "Users can view their own rewards" on rewards for select using (auth.uid() = user_id);
create policy "Users can insert their own rewards" on rewards for insert with check (auth.uid() = user_id);
create policy "Users can update their own rewards" on rewards for update using (auth.uid() = user_id);
create policy "Users can delete their own rewards" on rewards for delete using (auth.uid() = user_id);

-- User Themes
create policy "Users can view their own themes" on user_themes for select using (auth.uid() = user_id);
create policy "Users can insert their own themes" on user_themes for insert with check (auth.uid() = user_id);
