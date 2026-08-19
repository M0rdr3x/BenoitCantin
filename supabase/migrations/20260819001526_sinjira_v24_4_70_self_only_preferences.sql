create table if not exists public.privacy_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  public_profile boolean not null default false,
  show_avatar_public boolean not null default false,
  show_city_to_contacts boolean not null default false,
  show_relationship_status boolean not null default false,
  show_online_status boolean not null default false,
  allow_messages_from text not null default 'nobody' check (allow_messages_from in ('nobody','contacts','community')),
  allow_ai_personal_data boolean not null default false check (allow_ai_personal_data = false),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.privacy_settings enable row level security;
revoke all on table public.privacy_settings from public, anon, authenticated;
grant select on table public.privacy_settings to authenticated;
grant insert (user_id, public_profile, show_avatar_public, show_city_to_contacts, show_relationship_status, show_online_status, allow_messages_from, allow_ai_personal_data) on public.privacy_settings to authenticated;
grant update (public_profile, show_avatar_public, show_city_to_contacts, show_relationship_status, show_online_status, allow_messages_from, allow_ai_personal_data, updated_at) on public.privacy_settings to authenticated;

create policy privacy_settings_self_select on public.privacy_settings
for select to authenticated
using ((select auth.uid()) = user_id);

create policy privacy_settings_self_insert on public.privacy_settings
for insert to authenticated
with check ((select auth.uid()) = user_id and allow_ai_personal_data = false);

create policy privacy_settings_self_update on public.privacy_settings
for update to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id and allow_ai_personal_data = false);

create table if not exists public.notification_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  security_email boolean not null default false,
  direct_messages boolean not null default true,
  community_activity boolean not null default true,
  market_activity boolean not null default false,
  parallel_world boolean not null default true,
  digest_frequency text not null default 'never' check (digest_frequency in ('never','daily','weekly')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.notification_preferences enable row level security;
revoke all on table public.notification_preferences from public, anon, authenticated;
grant select on table public.notification_preferences to authenticated;
grant insert (user_id, security_email, direct_messages, community_activity, market_activity, parallel_world, digest_frequency) on public.notification_preferences to authenticated;
grant update (security_email, direct_messages, community_activity, market_activity, parallel_world, digest_frequency, updated_at) on public.notification_preferences to authenticated;

create policy notification_preferences_self_select on public.notification_preferences
for select to authenticated
using ((select auth.uid()) = user_id);

create policy notification_preferences_self_insert on public.notification_preferences
for insert to authenticated
with check ((select auth.uid()) = user_id);

create policy notification_preferences_self_update on public.notification_preferences
for update to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

comment on table public.privacy_settings is 'Préférences de confidentialité self-only du Compte SINJIRA. IA personnelle forcée à false en mode gratuit.';
comment on table public.notification_preferences is 'Préférences internes self-only. Ne déclenchent aucun courriel, SMS, push ou service payant.';
