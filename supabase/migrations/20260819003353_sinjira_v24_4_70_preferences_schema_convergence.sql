-- Convergence GitHub/production pour les préférences V24.4.70.
-- Cette migration est idempotente et ne réactive aucun canal externe.

alter table public.privacy_settings
  add column if not exists created_at timestamptz not null default now();
alter table public.notification_preferences
  add column if not exists created_at timestamptz not null default now();

alter table public.privacy_settings alter column public_profile set default false;
alter table public.privacy_settings alter column show_avatar_public set default false;
alter table public.privacy_settings alter column show_city_to_contacts set default false;
alter table public.privacy_settings alter column show_relationship_status set default false;
alter table public.privacy_settings alter column show_online_status set default false;
alter table public.privacy_settings alter column allow_messages_from set default 'nobody';
alter table public.privacy_settings alter column allow_ai_personal_data set default false;

alter table public.notification_preferences alter column security_email set default false;
alter table public.notification_preferences alter column direct_messages set default true;
alter table public.notification_preferences alter column community_activity set default true;
alter table public.notification_preferences alter column market_activity set default false;
alter table public.notification_preferences alter column parallel_world set default true;
alter table public.notification_preferences alter column digest_frequency set default 'never';

update public.privacy_settings
set allow_ai_personal_data=false
where allow_ai_personal_data is distinct from false;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid='public.privacy_settings'::regclass
      and conname='privacy_settings_allow_ai_personal_data_check'
  ) then
    alter table public.privacy_settings
      add constraint privacy_settings_allow_ai_personal_data_check
      check (allow_ai_personal_data = false);
  end if;
end $$;

-- Le runtime V24.4.70 gère explicitement updated_at : uniformiser avec la production.
drop trigger if exists privacy_settings_updated_at on public.privacy_settings;
drop trigger if exists notification_preferences_updated_at on public.notification_preferences;

alter table public.privacy_settings enable row level security;
alter table public.notification_preferences enable row level security;

revoke all on table public.privacy_settings from public, anon, authenticated;
revoke all on table public.notification_preferences from public, anon, authenticated;

grant select on table public.privacy_settings to authenticated;
grant insert (user_id, public_profile, show_avatar_public, show_city_to_contacts, show_relationship_status, show_online_status, allow_messages_from, allow_ai_personal_data) on public.privacy_settings to authenticated;
grant update (public_profile, show_avatar_public, show_city_to_contacts, show_relationship_status, show_online_status, allow_messages_from, allow_ai_personal_data, updated_at) on public.privacy_settings to authenticated;

grant select on table public.notification_preferences to authenticated;
grant insert (user_id, security_email, direct_messages, community_activity, market_activity, parallel_world, digest_frequency) on public.notification_preferences to authenticated;
grant update (security_email, direct_messages, community_activity, market_activity, parallel_world, digest_frequency, updated_at) on public.notification_preferences to authenticated;

drop policy if exists privacy_settings_own on public.privacy_settings;
drop policy if exists privacy_settings_self_select on public.privacy_settings;
drop policy if exists privacy_settings_self_insert on public.privacy_settings;
drop policy if exists privacy_settings_self_update on public.privacy_settings;
create policy privacy_settings_self_select on public.privacy_settings
for select to authenticated using ((select auth.uid()) = user_id);
create policy privacy_settings_self_insert on public.privacy_settings
for insert to authenticated with check ((select auth.uid()) = user_id and allow_ai_personal_data = false);
create policy privacy_settings_self_update on public.privacy_settings
for update to authenticated using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id and allow_ai_personal_data = false);

drop policy if exists notification_preferences_own on public.notification_preferences;
drop policy if exists notification_preferences_self_select on public.notification_preferences;
drop policy if exists notification_preferences_self_insert on public.notification_preferences;
drop policy if exists notification_preferences_self_update on public.notification_preferences;
create policy notification_preferences_self_select on public.notification_preferences
for select to authenticated using ((select auth.uid()) = user_id);
create policy notification_preferences_self_insert on public.notification_preferences
for insert to authenticated with check ((select auth.uid()) = user_id);
create policy notification_preferences_self_update on public.notification_preferences
for update to authenticated using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

comment on table public.privacy_settings is 'Préférences de confidentialité self-only du Compte SINJIRA. IA personnelle forcée à false en mode gratuit.';
comment on table public.notification_preferences is 'Préférences internes self-only. Ne déclenchent aucun courriel, SMS, push ou service payant.';
