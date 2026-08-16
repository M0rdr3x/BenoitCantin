-- SINJIRA™ V24.4.12 — convergence Monde parallèle vers public.characters
-- Le Registre V24 et AbyssTime utilisent public.characters. L'ancienne table
-- sinjira_characters est conservée uniquement comme archive de compatibilité, jamais comme source active.

-- 1) Import rétrocompatible d'éventuels personnages V22 en conservant leurs UUID.
insert into public.characters(
  id,submission_id,user_id,public_name,public_description,status,novel_id,novel_note,
  bible,ai_generated,visible_to_user,canon_status,canon_version,created_at,updated_at,portrait_path
)
select
  sc.id,
  null,
  sc.user_id,
  sc.canonical_name,
  sc.short_description,
  case when sc.status='review' then 'author_review' else sc.status end,
  n.id,
  sc.future_novel_note,
  coalesce(sc.bible,'{}'::jsonb),
  sc.status='ai_draft',
  sc.status<>'archived',
  'PROVISOIRE',
  'legacy-v22',
  sc.created_at,
  sc.updated_at,
  null
from public.sinjira_characters sc
left join public.sinjira_novels sn on sn.id=sc.target_novel_id
left join public.novels n on n.slug=sn.slug
where not exists(select 1 from public.characters c where c.id=sc.id)
on conflict(id) do nothing;

-- 2) Toutes les FK narratives/parallel pointent désormais vers la table canonique V24.
alter table public.fictional_relationships drop constraint if exists fictional_relationships_character_a_id_fkey;
alter table public.fictional_relationships add constraint fictional_relationships_character_a_id_fkey
  foreign key(character_a_id) references public.characters(id) on delete cascade;
alter table public.fictional_relationships drop constraint if exists fictional_relationships_character_b_id_fkey;
alter table public.fictional_relationships add constraint fictional_relationships_character_b_id_fkey
  foreign key(character_b_id) references public.characters(id) on delete set null;

alter table public.memorial_records drop constraint if exists memorial_records_character_id_fkey;
alter table public.memorial_records add constraint memorial_records_character_id_fkey
  foreign key(character_id) references public.characters(id) on delete set null;

alter table public.parallel_character_state drop constraint if exists parallel_character_state_character_id_fkey;
alter table public.parallel_character_state add constraint parallel_character_state_character_id_fkey
  foreign key(character_id) references public.characters(id) on delete cascade;

alter table public.parallel_cycle_responses drop constraint if exists parallel_cycle_responses_character_id_fkey;
alter table public.parallel_cycle_responses add constraint parallel_cycle_responses_character_id_fkey
  foreign key(character_id) references public.characters(id) on delete cascade;

alter table public.parallel_group_members drop constraint if exists parallel_group_members_character_id_fkey;
alter table public.parallel_group_members add constraint parallel_group_members_character_id_fkey
  foreign key(character_id) references public.characters(id) on delete cascade;

alter table public.parallel_story_installments drop constraint if exists parallel_story_installments_character_id_fkey;
alter table public.parallel_story_installments add constraint parallel_story_installments_character_id_fkey
  foreign key(character_id) references public.characters(id) on delete cascade;

alter table public.parallel_world_memberships drop constraint if exists parallel_world_memberships_character_id_fkey;
alter table public.parallel_world_memberships add constraint parallel_world_memberships_character_id_fkey
  foreign key(character_id) references public.characters(id) on delete cascade;

-- 3) Adhésion automatique. Les numéros pionniers sont attribués sous verrou transactionnel
-- uniquement quand un personnage devient approuvé/assigné/futur/publié, jamais au questionnaire.
create or replace function private.ensure_parallel_world_membership(p_character_id uuid)
returns void
language plpgsql
security definer
set search_path=public,private,auth
as $$
declare
  c public.characters%rowtype;
  v_owner boolean:=false;
  v_pioneer integer;
  v_existing public.parallel_world_memberships%rowtype;
begin
  select * into c from public.characters where id=p_character_id;
  if c.id is null then return; end if;
  if c.status not in ('approved','assigned','future','published') then return; end if;

  select exists(
    select 1 from auth.users u
    where u.id=c.user_id and lower(coalesce(u.email,''))='kingtyrano@gmail.com'
  ) into v_owner;

  perform pg_advisory_xact_lock(24412026);
  select * into v_existing from public.parallel_world_memberships where character_id=c.id for update;

  if v_existing.character_id is not null then
    update public.parallel_world_memberships
    set user_id=c.user_id,
        status=case when status='memorial' then 'memorial' else 'active' end
    where character_id=c.id;
  elsif v_owner then
    insert into public.parallel_world_memberships(
      character_id,user_id,pioneer_number,main_canon_eligible,parallel_world_only,status
    ) values(c.id,c.user_id,null,true,false,'active');
  else
    select gs into v_pioneer
    from generate_series(1,40) gs
    where not exists(
      select 1 from public.parallel_world_memberships m where m.pioneer_number=gs
    )
    order by gs
    limit 1;

    insert into public.parallel_world_memberships(
      character_id,user_id,pioneer_number,main_canon_eligible,parallel_world_only,status
    ) values(
      c.id,c.user_id,v_pioneer,
      v_pioneer is not null,
      v_pioneer is null,
      'active'
    );
  end if;

  -- Une Chronique technique vide peut être créée sans inventer de narration.
  insert into public.parallel_character_state(character_id,user_id,life_state,state_data)
  values(c.id,c.user_id,'active','{}'::jsonb)
  on conflict(character_id) do update
    set user_id=excluded.user_id,
        life_state=case when public.parallel_character_state.life_state='memorial' then 'memorial' else 'active' end,
        updated_at=now();
end;
$$;
revoke all on function private.ensure_parallel_world_membership(uuid) from public,anon,authenticated;

create or replace function private.sync_parallel_membership_from_character()
returns trigger
language plpgsql
security definer
set search_path=public,private,auth
as $$
begin
  if new.status in ('approved','assigned','future','published') then
    perform private.ensure_parallel_world_membership(new.id);
  elsif new.status='archived' then
    update public.parallel_world_memberships
    set status=case when status='memorial' then 'memorial' else 'paused' end
    where character_id=new.id;
  end if;
  return new;
end;
$$;
revoke all on function private.sync_parallel_membership_from_character() from public,anon,authenticated;

drop trigger if exists sync_parallel_membership_from_character_trigger on public.characters;
create trigger sync_parallel_membership_from_character_trigger
after insert or update of status,user_id on public.characters
for each row execute function private.sync_parallel_membership_from_character();

-- Backfill des personnages V24 déjà approuvés/assignés.
do $$
declare r record;
begin
  for r in select id from public.characters where status in ('approved','assigned','future','published') order by created_at,id loop
    perform private.ensure_parallel_world_membership(r.id);
  end loop;
end $$;

-- 4) Policies qui lisaient encore la table V22.
drop policy if exists fictional_relationships_participants_read on public.fictional_relationships;
create policy fictional_relationships_participants_read on public.fictional_relationships
for select to authenticated
using (
  exists(
    select 1 from public.characters c
    where c.id=any(array[fictional_relationships.character_a_id,fictional_relationships.character_b_id])
      and c.user_id=(select auth.uid())
  )
);

drop policy if exists parallel_stories_authenticated on public.parallel_story_installments;
create policy parallel_stories_authenticated on public.parallel_story_installments
for select to authenticated
using (
  published_at is not null and (
    (story_kind='collective' and audience='all')
    or (story_kind='collective' and audience=public.sinjira_my_age_band())
    or (
      story_kind='individual'
      and exists(
        select 1 from public.characters c
        where c.id=parallel_story_installments.character_id
          and c.user_id=(select auth.uid())
      )
    )
  )
);

comment on table public.sinjira_characters is
  'Archive de compatibilité V22. La source canonique active des personnages SINJIRA V24 est public.characters.';
