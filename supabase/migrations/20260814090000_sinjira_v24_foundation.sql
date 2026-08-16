-- SINJIRA™ V24 — fondation cumulative sans IA active.
-- Objectifs: profil privé, relations, Monde parallèle manuel, Marché en brouillon,
-- jetons en grand livre, licences à usage unique, Codex/provenance et sécurité RLS.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- PROFIL PRIVÉ ET RELATIONS
-- ---------------------------------------------------------------------------
create table if not exists public.private_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  birth_date date,
  gender text,
  languages text[] not null default '{}',
  residence_city text,
  residence_region text,
  residence_country text,
  origin_city text,
  origin_region text,
  origin_country text,
  relationship_status text,
  relationship_since date,
  relationship_partner_label text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.family_relationships (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  related_user_id uuid references auth.users(id) on delete set null,
  relationship_type text not null,
  relative_name text not null,
  since_date date,
  until_date date,
  private_note text,
  status text not null default 'private_record' check (status in ('private_record','pending','accepted','rejected','ended')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists family_relationships_owner_idx on public.family_relationships(owner_user_id);

create table if not exists public.character_questionnaire_drafts (
  user_id uuid primary key references auth.users(id) on delete cascade,
  answers jsonb not null default '{}'::jsonb,
  status text not null default 'draft' check (status in ('draft','ready','submitted','archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.privacy_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  public_profile boolean not null default false,
  show_avatar_public boolean not null default true,
  show_city_to_contacts boolean not null default false,
  show_relationship_status boolean not null default false,
  show_online_status boolean not null default true,
  allow_messages_from text not null default 'contacts' check (allow_messages_from in ('nobody','contacts','community')),
  allow_ai_personal_data boolean not null default false,
  updated_at timestamptz not null default now()
);

create table if not exists public.notification_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  security_email boolean not null default true,
  direct_messages boolean not null default true,
  community_activity boolean not null default true,
  market_activity boolean not null default true,
  parallel_world boolean not null default true,
  digest_frequency text not null default 'daily' check (digest_frequency in ('never','daily','weekly')),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- MONDE PARALLÈLE — moteur manuel, prêt pour automatisation future
-- ---------------------------------------------------------------------------
create table if not exists public.parallel_cycles (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  summary text,
  starts_at timestamptz,
  ends_at timestamptz,
  status text not null default 'draft' check (status in ('draft','open','closed','archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.parallel_missions (
  id uuid primary key default gen_random_uuid(),
  cycle_id uuid not null references public.parallel_cycles(id) on delete cascade,
  title text not null,
  prompt text not null,
  mission_scope text not null default 'global' check (mission_scope in ('global','regional','group','individual')),
  status text not null default 'draft' check (status in ('draft','open','closed','archived')),
  opens_at timestamptz,
  closes_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists parallel_missions_cycle_idx on public.parallel_missions(cycle_id,status);

create table if not exists public.parallel_responses (
  id uuid primary key default gen_random_uuid(),
  mission_id uuid not null references public.parallel_missions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  character_id uuid not null references public.characters(id) on delete cascade,
  response_text text not null check (char_length(response_text) between 1 and 4000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(mission_id,user_id)
);

create table if not exists public.parallel_character_state (
  character_id uuid primary key references public.characters(id) on delete cascade,
  user_id uuid not null unique references auth.users(id) on delete cascade,
  current_region text,
  current_group text,
  public_summary text,
  private_summary text,
  state jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- MARCHÉ — brouillons fonctionnels, publication/paiement désactivables
-- ---------------------------------------------------------------------------
create table if not exists public.market_listings (
  id uuid primary key default gen_random_uuid(),
  seller_user_id uuid not null references auth.users(id) on delete cascade,
  seller_kind text not null default 'individual' check (seller_kind in ('individual','business')),
  title text not null check (char_length(title) between 1 and 140),
  description text not null check (char_length(description) between 1 and 4000),
  price_cad numeric(12,2) not null default 0 check (price_cad >= 0),
  listing_type text not null default 'sale' check (listing_type in ('sale','gift')),
  condition_label text,
  location_label text,
  status text not null default 'draft' check (status in ('draft','active','reserved','sold','archived')),
  token_cost integer not null default 0 check (token_cost between 0 and 1),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check ((price_cad = 0 and listing_type = 'gift') or price_cad > 0),
  check ((price_cad <= 20 and token_cost = 0) or (price_cad > 20 and token_cost in (0,1)))
);
create index if not exists market_listings_status_idx on public.market_listings(status,created_at desc);
create index if not exists market_listings_seller_idx on public.market_listings(seller_user_id,created_at desc);

create table if not exists public.market_favorites (
  user_id uuid not null references auth.users(id) on delete cascade,
  listing_id uuid not null references public.market_listings(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key(user_id,listing_id)
);

-- ---------------------------------------------------------------------------
-- JETONS — grand livre immuable côté client
-- ---------------------------------------------------------------------------
create table if not exists public.token_ledger (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  amount integer not null check (amount <> 0),
  entry_type text not null,
  description text,
  reference_type text,
  reference_id uuid,
  created_at timestamptz not null default now()
);
create index if not exists token_ledger_user_idx on public.token_ledger(user_id,created_at desc);

-- ---------------------------------------------------------------------------
-- LICENCES PHYSIQUES — les codes bruts ne sont jamais stockés ici
-- ---------------------------------------------------------------------------
create table if not exists public.license_batches (
  id uuid primary key default gen_random_uuid(),
  product_slug text not null,
  batch_code text not null unique,
  quantity integer not null check (quantity > 0),
  status text not null default 'active' check (status in ('active','revoked','exhausted')),
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.activation_codes (
  id uuid primary key default gen_random_uuid(),
  batch_id uuid not null references public.license_batches(id) on delete cascade,
  code_hash text not null unique,
  product_slug text not null,
  status text not null default 'unused' check (status in ('unused','redeemed','revoked')),
  redeemed_by uuid references auth.users(id) on delete set null,
  redeemed_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists activation_codes_batch_idx on public.activation_codes(batch_id,status);

create table if not exists public.license_redemptions (
  id uuid primary key default gen_random_uuid(),
  activation_code_id uuid not null unique references public.activation_codes(id) on delete restrict,
  user_id uuid not null references auth.users(id) on delete cascade,
  product_slug text not null,
  redeemed_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- CODEX / PROVENANCE
-- ---------------------------------------------------------------------------
create table if not exists public.codex_entities (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  entity_type text not null,
  title text not null,
  summary text,
  body jsonb not null default '{}'::jsonb,
  source_kind text not null default 'roman' check (source_kind in ('roman','bible','parallel','fan','admin','ai_draft')),
  canon_status text not null default 'PROVISOIRE',
  source_reference text,
  spoiler_book integer not null default 1,
  spoiler_chapter integer not null default 0,
  published boolean not null default false,
  version_no integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists codex_entities_type_idx on public.codex_entities(entity_type,published);

create table if not exists public.codex_relationships (
  id uuid primary key default gen_random_uuid(),
  source_entity_id uuid not null references public.codex_entities(id) on delete cascade,
  target_entity_id uuid not null references public.codex_entities(id) on delete cascade,
  relation_type text not null,
  source_reference text,
  spoiler_book integer not null default 1,
  spoiler_chapter integer not null default 0,
  published boolean not null default false,
  unique(source_entity_id,target_entity_id,relation_type)
);

create table if not exists public.content_versions (
  id uuid primary key default gen_random_uuid(),
  entity_kind text not null,
  entity_id uuid,
  version_label text not null,
  change_summary text,
  source_reference text,
  changed_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- MISE À JOUR AUTOMATIQUE DES updated_at
-- ---------------------------------------------------------------------------
do $$
declare t text;
begin
  foreach t in array array['private_profiles','family_relationships','character_questionnaire_drafts','privacy_settings','notification_preferences','parallel_cycles','parallel_missions','parallel_responses','parallel_character_state','market_listings','codex_entities']
  loop
    execute format('drop trigger if exists %I_updated_at on public.%I',t,t);
    execute format('create trigger %I_updated_at before update on public.%I for each row execute function public.set_updated_at()',t,t);
  end loop;
end $$;

-- ---------------------------------------------------------------------------
-- TRIGGER D'INSCRIPTION CUMULATIF
-- ---------------------------------------------------------------------------
create or replace function public.handle_new_sinjira_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  wants_contribution boolean := coalesce((new.raw_user_meta_data ->> 'initial_contributor_opt_in')::boolean, false);
  wants_free_text boolean := coalesce((new.raw_user_meta_data ->> 'initial_share_free_text')::boolean, false);
  langs text[] := '{}';
  q jsonb := coalesce(new.raw_user_meta_data -> 'quick_character_questionnaire','{}'::jsonb);
begin
  insert into public.profiles(user_id,pseudo,display_name)
  values(new.id,coalesce(nullif(new.raw_user_meta_data->>'pseudo',''),'Joueur SINJIRA'),nullif(new.raw_user_meta_data->>'display_name',''))
  on conflict (user_id) do update set pseudo=excluded.pseudo,display_name=excluded.display_name;

  insert into public.research_consents(user_id,participate,share_free_text,consent_version,consented_at)
  values(new.id,wants_contribution,wants_contribution and wants_free_text,'sinjira-gameplay-v1',case when wants_contribution then now() else null end)
  on conflict (user_id) do nothing;

  if jsonb_typeof(new.raw_user_meta_data->'languages')='array' then
    select coalesce(array_agg(value),'{}') into langs from jsonb_array_elements_text(new.raw_user_meta_data->'languages');
  end if;

  insert into public.private_profiles(user_id,birth_date,gender,languages,residence_city,residence_region,residence_country,origin_city,origin_region,origin_country,relationship_status,relationship_since,relationship_partner_label)
  values(
    new.id,
    case when coalesce(new.raw_user_meta_data->>'birth_date','') ~ '^\\d{4}-\\d{2}-\\d{2}$' then (new.raw_user_meta_data->>'birth_date')::date else null end,
    nullif(new.raw_user_meta_data->>'gender',''),langs,
    nullif(new.raw_user_meta_data->>'residence_city',''),nullif(new.raw_user_meta_data->>'residence_region',''),nullif(new.raw_user_meta_data->>'residence_country',''),
    nullif(new.raw_user_meta_data->>'origin_city',''),nullif(new.raw_user_meta_data->>'origin_region',''),nullif(new.raw_user_meta_data->>'origin_country',''),
    nullif(new.raw_user_meta_data->>'relationship_status',''),
    case when coalesce(new.raw_user_meta_data->>'relationship_since','') ~ '^\\d{4}-\\d{2}-\\d{2}$' then (new.raw_user_meta_data->>'relationship_since')::date else null end,
    nullif(new.raw_user_meta_data->>'relationship_partner_label','')
  ) on conflict (user_id) do nothing;

  insert into public.privacy_settings(user_id) values(new.id) on conflict (user_id) do nothing;
  insert into public.notification_preferences(user_id) values(new.id) on conflict (user_id) do nothing;

  if coalesce((new.raw_user_meta_data->>'fill_character_now')::boolean,false) and q <> '{}'::jsonb then
    insert into public.character_questionnaire_drafts(user_id,answers,status)
    values(new.id,q,'ready') on conflict (user_id) do update set answers=excluded.answers,status='ready',updated_at=now();
  end if;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created_sinjira on auth.users;
create trigger on_auth_user_created_sinjira after insert on auth.users for each row execute procedure public.handle_new_sinjira_user();

-- ---------------------------------------------------------------------------
-- RLS
-- ---------------------------------------------------------------------------
alter table public.private_profiles enable row level security;
alter table public.family_relationships enable row level security;
alter table public.character_questionnaire_drafts enable row level security;
alter table public.privacy_settings enable row level security;
alter table public.notification_preferences enable row level security;
alter table public.parallel_cycles enable row level security;
alter table public.parallel_missions enable row level security;
alter table public.parallel_responses enable row level security;
alter table public.parallel_character_state enable row level security;
alter table public.market_listings enable row level security;
alter table public.market_favorites enable row level security;
alter table public.token_ledger enable row level security;
alter table public.license_batches enable row level security;
alter table public.activation_codes enable row level security;
alter table public.license_redemptions enable row level security;
alter table public.codex_entities enable row level security;
alter table public.codex_relationships enable row level security;
alter table public.content_versions enable row level security;

-- Données privées: propriétaire seulement.
drop policy if exists private_profiles_own on public.private_profiles;
create policy private_profiles_own on public.private_profiles for all to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists family_relationships_own on public.family_relationships;
create policy family_relationships_own on public.family_relationships for all to authenticated using(auth.uid()=owner_user_id) with check(auth.uid()=owner_user_id);
drop policy if exists questionnaire_drafts_own on public.character_questionnaire_drafts;
create policy questionnaire_drafts_own on public.character_questionnaire_drafts for all to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists privacy_settings_own on public.privacy_settings;
create policy privacy_settings_own on public.privacy_settings for all to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists notification_preferences_own on public.notification_preferences;
create policy notification_preferences_own on public.notification_preferences for all to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);

-- Monde parallèle: cycles/missions ouverts lisibles, réponses et état privés au membre.
drop policy if exists parallel_cycles_read on public.parallel_cycles;
create policy parallel_cycles_read on public.parallel_cycles for select to authenticated using(status in ('open','closed'));
drop policy if exists parallel_missions_read on public.parallel_missions;
create policy parallel_missions_read on public.parallel_missions for select to authenticated using(status in ('open','closed'));
drop policy if exists parallel_responses_own on public.parallel_responses;
create policy parallel_responses_own on public.parallel_responses for all to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists parallel_state_own on public.parallel_character_state;
create policy parallel_state_own on public.parallel_character_state for select to authenticated using(auth.uid()=user_id);

-- Marché: le public ne voit que les annonces actives; le vendeur gère ses propres brouillons.
drop policy if exists market_listings_public_read on public.market_listings;
create policy market_listings_public_read on public.market_listings for select to anon,authenticated using(status='active');
drop policy if exists market_listings_own on public.market_listings;
create policy market_listings_own on public.market_listings for all to authenticated using(auth.uid()=seller_user_id) with check(auth.uid()=seller_user_id);
drop policy if exists market_favorites_own on public.market_favorites;
create policy market_favorites_own on public.market_favorites for all to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);

-- Jetons: lecture personnelle uniquement. Aucune écriture client.
drop policy if exists token_ledger_own_read on public.token_ledger;
create policy token_ledger_own_read on public.token_ledger for select to authenticated using(auth.uid()=user_id);
revoke insert,update,delete on public.token_ledger from anon,authenticated;

-- Licences: tables internes, aucune politique utilisateur.
revoke all on public.license_batches from anon,authenticated;
revoke all on public.activation_codes from anon,authenticated;
revoke all on public.license_redemptions from anon,authenticated;

-- Codex: seulement les entrées publiées sont visibles publiquement.
drop policy if exists codex_entities_public_read on public.codex_entities;
create policy codex_entities_public_read on public.codex_entities for select to anon,authenticated using(published=true);
drop policy if exists codex_relationships_public_read on public.codex_relationships;
create policy codex_relationships_public_read on public.codex_relationships for select to anon,authenticated using(published=true);
-- Historique de versions réservé à l'administration/service_role pour l'instant.
revoke all on public.content_versions from anon,authenticated;

-- Les écritures administratives des cycles/codex passent par service_role / Edge Functions.
revoke insert,update,delete on public.parallel_cycles from anon,authenticated;
revoke insert,update,delete on public.parallel_missions from anon,authenticated;
revoke insert,update,delete on public.parallel_character_state from anon,authenticated;
revoke insert,update,delete on public.codex_entities from anon,authenticated;
revoke insert,update,delete on public.codex_relationships from anon,authenticated;

-- Activation atomique d'un code : service_role uniquement.
create or replace function public.redeem_sinjira_activation(p_code_hash text,p_user_id uuid)
returns table(product_slug text, product_id uuid)
language plpgsql
security definer
set search_path=public
as $$
declare
  c public.activation_codes%rowtype;
  p public.products%rowtype;
begin
  select * into c from public.activation_codes where code_hash=p_code_hash for update;
  if c.id is null or c.status <> 'unused' then raise exception 'CODE_INVALID_OR_USED'; end if;
  select * into p from public.products where slug=c.product_slug and active=true;
  if p.id is null then raise exception 'PRODUCT_NOT_ACTIVE'; end if;
  update public.activation_codes set status='redeemed',redeemed_by=p_user_id,redeemed_at=now() where id=c.id;
  insert into public.license_redemptions(activation_code_id,user_id,product_slug) values(c.id,p_user_id,c.product_slug);
  insert into public.user_entitlements(user_id,product_id,source) values(p_user_id,p.id,'physical_activation') on conflict (user_id,product_id) do nothing;
  return query select c.product_slug,p.id;
end;
$$;
revoke all on function public.redeem_sinjira_activation(text,uuid) from public,anon,authenticated;
grant execute on function public.redeem_sinjira_activation(text,uuid) to service_role;

-- Catalogue minimal V24 pour les droits d'accès. L'activation de paiement reste séparée.
insert into public.products(slug,name,product_type,active)
values('fracture-du-reseau-mere','Fracture du Réseau-Mère — accès en ligne','game',true)
on conflict (slug) do update set name=excluded.name,product_type=excluded.product_type,active=excluded.active;
