-- SINJIRA™ V25 — catalogue compte/créateur cohérent et relisible.
-- Membres : produits actifs + produits réellement achetés/attribués.
-- Créateur : catalogue interne complet sans fabriquer de faux achat.
-- Littérature : convergence du Livre II vers la table canonique sinjira_novels.

drop policy if exists sinjira_novels_owner_read on public.sinjira_novels;
create policy sinjira_novels_owner_read
on public.sinjira_novels
for select
to authenticated
using (public.is_sinjira_owner((select auth.uid())));

drop policy if exists products_entitled_read on public.products;
create policy products_entitled_read
on public.products
for select
to authenticated
using (
  exists(
    select 1
    from public.user_entitlements ue
    where ue.product_id=products.id
      and ue.user_id=(select auth.uid())
  )
);

drop policy if exists products_ordered_read on public.products;
create policy products_ordered_read
on public.products
for select
to authenticated
using (
  exists(
    select 1
    from public.order_items oi
    join public.orders o on o.id=oi.order_id
    where oi.product_id=products.id
      and o.user_id=(select auth.uid())
      and o.status='paid'
  )
);

drop policy if exists products_owner_read on public.products;
create policy products_owner_read
on public.products
for select
to authenticated
using (public.is_sinjira_owner((select auth.uid())));

insert into public.sinjira_novels(
  slug,title,subtitle,description,status,public_path,demo_path,comments_enabled,sort_order
)
values(
  'le-sang-du-sauveur',
  'SINJIRA — Le Sang du Sauveur',
  'Livre II',
  'Deuxième roman officiellement confirmé de SINJIRA™, actuellement en production éditoriale.',
  'announced',
  '/projets/sinjira/romans/le-sang-du-sauveur/index.html',
  null,
  false,
  20
)
on conflict(slug) do update
set title=excluded.title,
    subtitle=excluded.subtitle,
    description=excluded.description,
    public_path=excluded.public_path,
    sort_order=excluded.sort_order,
    updated_at=now();



-- Convergence V25 du repair personnage propriétaire.
-- L'accès complet du créateur provient du rôle owner et des catalogues canoniques:
-- ce repair ne doit plus fabriquer d'entitlement commercial ni de statut tester.
create or replace function sinjira_owner_internal.ensure_sinjira_owner_character()
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, auth
as $
declare
  v_user uuid;
  v_submission uuid;
  v_character uuid;
  v_caller uuid := auth.uid();
  v_social_ok boolean := false;
  v_parallel_state_ok boolean := false;
  v_parallel_membership_ok boolean := false;
begin
  select a.user_id into v_user
  from public.internal_admin_users a
  where a.role='owner'
  order by a.user_id
  limit 1;

  if v_user is null then
    return jsonb_build_object('ok',false,'code','OWNER_ACCOUNT_NOT_FOUND');
  end if;

  if v_caller is not null
     and v_caller <> v_user
     and coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'OWNER_ONLY';
  end if;

  insert into public.profiles(user_id,pseudo,display_name)
  values(v_user,'AbyssTime','Benoit Cantin')
  on conflict(user_id) do update
  set pseudo='AbyssTime',
      display_name='Benoit Cantin',
      updated_at=now();

  select id into v_submission
  from public.character_submissions
  where user_id=v_user
  order by created_at desc
  limit 1;

  select id into v_character
  from public.characters
  where user_id=v_user
  order by case when lower(coalesce(public_name,''))='abysstime' then 0 else 1 end,
           updated_at desc
  limit 1;

  if v_character is null then
    insert into public.characters(
      submission_id,user_id,public_name,public_description,status,novel_id,
      novel_note,bible,ai_generated,visible_to_user,canon_status,canon_version,
      portrait_path
    )
    values(
      v_submission,v_user,'AbyssTime',
      'Personnage officiel associé au compte de Benoit Cantin.',
      'assigned',null,'SINJIRA — Livre II : Le Sang du Sauveur',
      jsonb_build_object(
        'owner','Benoit Cantin',
        'account','AbyssTime',
        'placement','SINJIRA — Livre II : Le Sang du Sauveur',
        'source','Synchronisation propriétaire V24.4.20'
      ),
      false,true,'PROVISOIRE','v1.0','/assets/media/characters/abysstime.webp'
    )
    returning id into v_character;
  else
    update public.characters
    set public_name='AbyssTime',
        public_description=coalesce(
          nullif(public_description,''),
          'Personnage officiel associé au compte de Benoit Cantin.'
        ),
        submission_id=coalesce(submission_id,v_submission),
        status='assigned',
        novel_id=null,
        novel_note='SINJIRA — Livre II : Le Sang du Sauveur',
        visible_to_user=true,
        portrait_path='/assets/media/characters/abysstime.webp',
        updated_at=now()
    where id=v_character;
  end if;

  update public.characters
  set status='archived',visible_to_user=false,updated_at=now()
  where user_id=v_user and id<>v_character;

  if v_submission is not null then
    update public.character_submissions
    set status=case when id=v_submission then 'assigned' else 'archived' end,
        updated_at=now()
    where user_id=v_user;
  end if;

  insert into public.character_social_profiles(
    character_id,user_id,public_name,public_description,portrait_path,status,updated_at
  )
  select c.id,c.user_id,c.public_name,c.public_description,c.portrait_path,c.status,now()
  from public.characters c
  where c.id=v_character
  on conflict(character_id) do update
  set user_id=excluded.user_id,
      public_name=excluded.public_name,
      public_description=excluded.public_description,
      portrait_path=excluded.portrait_path,
      status=excluded.status,
      updated_at=now();

  insert into public.parallel_character_state(character_id,user_id)
  values(v_character,v_user)
  on conflict(character_id) do update
  set user_id=excluded.user_id,
      updated_at=now();

  insert into public.parallel_world_memberships(
    character_id,user_id,main_canon_eligible,parallel_world_only,status
  )
  values(v_character,v_user,true,false,'active')
  on conflict(character_id) do update
  set user_id=excluded.user_id,
      main_canon_eligible=true,
      parallel_world_only=false,
      status='active';

  insert into public.reader_library(user_id,novel_id,last_opened_at)
  select v_user,n.id,now()
  from public.novels n
  on conflict(user_id,novel_id) do update
  set last_opened_at=greatest(
    public.reader_library.last_opened_at,
    excluded.last_opened_at
  );

  select exists(
    select 1 from public.character_social_profiles
    where user_id=v_user and character_id=v_character and status='assigned'
  ) into v_social_ok;

  select exists(
    select 1 from public.parallel_character_state
    where user_id=v_user and character_id=v_character
  ) into v_parallel_state_ok;

  select exists(
    select 1 from public.parallel_world_memberships
    where user_id=v_user and character_id=v_character
      and status='active' and main_canon_eligible=true and parallel_world_only=false
  ) into v_parallel_membership_ok;

  return jsonb_build_object(
    'ok',v_social_ok and v_parallel_state_ok and v_parallel_membership_ok,
    'repair_version','24.4.20',
    'character_id',v_character,
    'submission_id',v_submission,
    'public_name','AbyssTime',
    'visible_to_user',true,
    'status','assigned',
    'social_profile',v_social_ok,
    'parallel_state',v_parallel_state_ok,
    'parallel_membership',v_parallel_membership_ok,
    'unlimited_tokens',true,
    'all_content',true
  );
end;
$;


revoke all on function sinjira_owner_internal.ensure_sinjira_owner_character()
from public,anon;
grant execute on function sinjira_owner_internal.ensure_sinjira_owner_character()
to authenticated,service_role;

delete from public.user_entitlements ue
using public.internal_admin_users a
where a.user_id=ue.user_id
  and a.role='owner'
  and ue.source='owner';

delete from public.project_access pa
using public.internal_admin_users a
where a.user_id=pa.user_id
  and a.role='owner'
  and pa.access_level='tester'
  and pa.granted_by=pa.user_id
  and pa.source='migration';

comment on function sinjira_owner_internal.ensure_sinjira_owner_character() is
  'V25: repair personnage owner sans identité courriel, entitlement commercial synthétique ni project_access tester artificiel.';

comment on policy sinjira_novels_owner_read on public.sinjira_novels is
  'V25: le propriétaire SINJIRA voit tout le catalogue roman, y compris les brouillons, sans créer de droit acheté.';
comment on policy products_entitled_read on public.products is
  'V25: un membre peut relire un produit lié à son propre entitlement même si ce produit devient inactif.';
comment on policy products_ordered_read on public.products is
  'V25: un membre peut relire un produit présent dans sa propre commande uniquement après paiement confirmé status=paid, même si ce produit devient ensuite inactif.';
comment on policy products_owner_read on public.products is
  'V25: le propriétaire SINJIRA voit tout le catalogue produit pour gérer ses créations; ce droit n est pas un achat.';
