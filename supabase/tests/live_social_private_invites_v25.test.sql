begin;

create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(30);

select has_table('private','social_live_room_invites','table privée invitations live présente');
select ok((select relrowsecurity from pg_class where oid='private.social_live_room_invites'::regclass),'RLS invitations active');
select ok(not has_table_privilege('authenticated','private.social_live_room_invites','SELECT'),'authenticated ne lit pas directement les invitations');
select ok(not has_table_privilege('authenticated','private.social_live_room_invites','INSERT'),'authenticated n insère pas directement les invitations');
select ok(not has_table_privilege('authenticated','private.social_live_room_invites','UPDATE'),'authenticated ne modifie pas directement les invitations');
select ok(not has_table_privilege('authenticated','private.social_live_room_invites','DELETE'),'authenticated ne supprime pas directement les invitations');
select ok(
  not has_table_privilege('service_role','private.social_live_room_invites','SELECT')
  and not has_table_privilege('service_role','private.social_live_room_invites','INSERT')
  and not has_table_privilege('service_role','private.social_live_room_invites','UPDATE')
  and not has_table_privilege('service_role','private.social_live_room_invites','DELETE'),
  'invitations restent strict_no_direct même pour service_role'
);

select ok(
  exists(
    select 1 from pg_constraint c
    where c.conrelid='private.social_live_room_invites'::regclass
      and pg_get_constraintdef(c.oid) ilike '%pending%'
      and pg_get_constraintdef(c.oid) ilike '%accepted%'
      and pg_get_constraintdef(c.oid) ilike '%declined%'
      and pg_get_constraintdef(c.oid) ilike '%revoked%'
      and pg_get_constraintdef(c.oid) ilike '%expired%'
  ),
  'états invitation bornés'
);
select ok(
  exists(
    select 1 from pg_indexes
    where schemaname='private' and tablename='social_live_room_invites'
      and indexname='social_live_room_invites_one_pending_idx'
      and indexdef ilike '%unique%'
      and indexdef ilike '%status%pending%'
  ),
  'une seule invitation pending par salon et invité'
);
select ok(
  exists(
    select 1 from information_schema.columns
    where table_schema='private' and table_name='social_live_room_invites' and column_name='expires_at'
      and column_default ilike '%7 days%'
  ),
  'expiration serveur à sept jours présente'
);

select ok(not (select prosecdef from pg_proc where oid='public.social_live_invite_create(uuid,uuid)'::regprocedure),'wrapper création invitation SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.social_live_my_invites(integer)'::regprocedure),'wrapper liste invitations SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.social_live_invite_respond(uuid,boolean)'::regprocedure),'wrapper réponse invitation SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.social_live_invite_revoke(uuid)'::regprocedure),'wrapper révocation invitation SECURITY INVOKER');
select is(
  (
    select count(*)::int from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='sinjira_social_user_internal'
      and p.proname in ('social_live_invite_create','social_live_my_invites','social_live_invite_respond','social_live_invite_revoke')
      and p.prosecdef
  ),
  4,
  'quatre implémentations privilégiées restent hors schéma public'
);
select ok(not has_function_privilege('anon','public.social_live_invite_create(uuid,uuid)','EXECUTE'),'anon ne crée pas invitation');

select ok(
  position('owner_user_id=v_user' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure))>0
  and position('visibility=' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure))>0,
  'création réservée au propriétaire d un salon privé'
);
select ok(position('sinjira_age_band' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure))>0,'création vérifie la cohorte');
select ok(
  position('sinjira_can_social_interact' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure))>0
  and position('social_is_blocked' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure))>0,
  'création réutilise interaction sociale et blocages'
);
select ok(position('pg_advisory_xact_lock' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure))>0,'invitations sérialisées par compte');
select ok(
  position('SOCIAL_LIVE_INVITE_RATE_LIMIT' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure))>0
  and position('SOCIAL_LIVE_INVITE_PENDING_LIMIT' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure))>0,
  'anti-raid invitations limite débit et volume pending'
);
select ok(position('SOCIAL_LIVE_INVITEE_UNAVAILABLE' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure))>0,'éligibilité cible utilise une erreur générique');

select ok(
  position('invitee_user_id=v_user' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_respond(uuid,boolean)'::regprocedure))>0,
  'seul l invité courant peut répondre'
);
select ok(
  position('public.social_live_room_members' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_respond(uuid,boolean)'::regprocedure))>0
  and position('insert into public.social_live_room_members' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_respond(uuid,boolean)'::regprocedure))>0,
  'acceptation crée l adhésion privée côté serveur'
);
select ok(
  position('has_accepted_community_rules' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_respond(uuid,boolean)'::regprocedure))>0
  and position('social_is_suspended' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_respond(uuid,boolean)'::regprocedure))>0,
  'acceptation revalide règles et suspension'
);
select ok(
  position('owner_user_id=v_user' in pg_get_functiondef('sinjira_social_user_internal.social_live_invite_revoke(uuid)'::regprocedure))>0,
  'révocation réservée au propriétaire du salon'
);
select ok(
  position('inviter_label' in pg_get_functiondef('sinjira_social_user_internal.social_live_my_invites(integer)'::regprocedure))>0,
  'liste retourne un libellé public minimal de l invitant'
);

select ok(
  position('inet_client_addr' in lower(pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure)))=0,
  'invitations ne collectent pas IP'
);
select ok(
  position('latitude' in lower(pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure)))=0
  and position('longitude' in lower(pg_get_functiondef('sinjira_social_user_internal.social_live_invite_create(uuid,uuid)'::regprocedure)))=0,
  'invitations ne collectent pas GPS'
);

select ok(
  exists(
    select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='private' and p.proname='sinjira_live_message_content_policy_guard' and p.prosecdef
  ),
  'garde contenu live existe hors schéma public'
);

select * from finish();
rollback;
