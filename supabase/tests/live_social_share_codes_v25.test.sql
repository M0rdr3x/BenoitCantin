begin;

create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(37);

select has_table('private','social_live_room_share_codes','table privée codes de partage live présente');
select ok((select relrowsecurity from pg_class where oid='private.social_live_room_share_codes'::regclass),'RLS codes de partage active');
select ok(not has_table_privilege('authenticated','private.social_live_room_share_codes','SELECT'),'authenticated ne lit pas directement les codes');
select ok(not has_table_privilege('authenticated','private.social_live_room_share_codes','INSERT'),'authenticated n insère pas directement les codes');
select ok(not has_table_privilege('authenticated','private.social_live_room_share_codes','UPDATE'),'authenticated ne modifie pas directement les codes');
select ok(not has_table_privilege('authenticated','private.social_live_room_share_codes','DELETE'),'authenticated ne supprime pas directement les codes');
select ok(
  not has_table_privilege('service_role','private.social_live_room_share_codes','SELECT')
  and not has_table_privilege('service_role','private.social_live_room_share_codes','INSERT')
  and not has_table_privilege('service_role','private.social_live_room_share_codes','UPDATE')
  and not has_table_privilege('service_role','private.social_live_room_share_codes','DELETE'),
  'codes restent strict_no_direct même pour service_role'
);
select ok(
  exists(
    select 1 from pg_constraint c
    where c.conrelid='private.social_live_room_share_codes'::regclass
      and pg_get_constraintdef(c.oid) ilike '%code_hash%'
      and pg_get_constraintdef(c.oid) ilike '%a-f0-9%64%'
  ),
  'hash SHA-256 hex borné par contrainte'
);
select is(
  (
    select count(*)::int from information_schema.columns
    where table_schema='private' and table_name='social_live_room_share_codes'
      and column_name in ('code','raw_code','secret','token')
  ),
  0,
  'aucune colonne ne stocke le secret brut'
);
select ok(
  exists(
    select 1 from pg_constraint c
    where c.conrelid='private.social_live_room_share_codes'::regclass
      and pg_get_constraintdef(c.oid) ilike '%active%'
      and pg_get_constraintdef(c.oid) ilike '%used%'
      and pg_get_constraintdef(c.oid) ilike '%revoked%'
      and pg_get_constraintdef(c.oid) ilike '%expired%'
  ),
  'états des codes bornés'
);
select ok(
  exists(select 1 from information_schema.columns where table_schema='private' and table_name='social_live_room_share_codes' and column_name='expires_at')
  and exists(select 1 from information_schema.columns where table_schema='private' and table_name='social_live_room_share_codes' and column_name='closed_at')
  and not exists(select 1 from information_schema.columns where table_schema='private' and table_name='social_live_room_share_codes' and column_name='redeemed_by_user_id'),
  'expiration/fermeture explicites et identité du rédempteur non persistée'
);

select ok(not (select prosecdef from pg_proc where oid='public.social_live_share_code_create(uuid)'::regprocedure),'wrapper création code SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.social_live_share_code_list(uuid,integer)'::regprocedure),'wrapper liste codes SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.social_live_share_code_revoke(uuid)'::regprocedure),'wrapper révocation code SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.social_live_share_code_redeem(text)'::regprocedure),'wrapper rachat code SECURITY INVOKER');
select is(
  (
    select count(*)::int from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='sinjira_social_user_internal'
      and p.proname in ('social_live_share_code_create','social_live_share_code_list','social_live_share_code_revoke','social_live_share_code_redeem')
      and p.prosecdef
  ),
  4,
  'quatre implémentations privilégiées restent hors schéma public'
);
select ok(not has_function_privilege('anon','public.social_live_share_code_create(uuid)','EXECUTE'),'anon ne crée pas de code');
select ok(not has_function_privilege('anon','public.social_live_share_code_redeem(text)','EXECUTE'),'anon ne rachète pas de code');
select ok(has_function_privilege('authenticated','public.social_live_share_code_create(uuid)','EXECUTE'),'authenticated peut créer via wrapper');
select ok(has_function_privilege('authenticated','public.social_live_share_code_redeem(text)','EXECUTE'),'authenticated peut racheter via wrapper');

select ok(
  position('owner_user_id=v_user' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_create(uuid)'::regprocedure))>0
  and position("visibility='private'" in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_create(uuid)'::regprocedure))>0,
  'création réservée au propriétaire d un salon privé'
);
select ok(position('sinjira_age_band' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_create(uuid)'::regprocedure))>0,'création vérifie la cohorte du propriétaire');
select ok(
  position('has_accepted_community_rules' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_create(uuid)'::regprocedure))>0
  and position('social_is_suspended' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_create(uuid)'::regprocedure))>0,
  'création vérifie règles et suspension'
);
select ok(
  position('pg_advisory_xact_lock' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_create(uuid)'::regprocedure))>0
  and position('SOCIAL_LIVE_SHARE_CODE_RATE_LIMIT' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_create(uuid)'::regprocedure))>0
  and position('SOCIAL_LIVE_SHARE_CODE_ACTIVE_LIMIT' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_create(uuid)'::regprocedure))>0,
  'création sérialisée avec limites de débit et volume actif'
);
select ok(
  position('gen_random_bytes(32)' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_create(uuid)'::regprocedure))>0
  and position("digest(v_raw,'sha256')" in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_create(uuid)'::regprocedure))>0,
  'secret 256 bits et SHA-256 côté serveur'
);
select ok(
  position("'display_once',true" in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_create(uuid)'::regprocedure))>0,
  'secret annoncé comme affiché une seule fois'
);
select ok(
  position('creator_user_id=v_user' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_list(uuid,integer)'::regprocedure))>0
  and position('least(coalesce(p_limit,20),50)' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_list(uuid,integer)'::regprocedure))>0,
  'liste self-only et bornée à 50'
);
select ok(
  position('code_hash' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_list(uuid,integer)'::regprocedure))=0
  and position('redeemed_by_user_id' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_list(uuid,integer)'::regprocedure))=0,
  'liste ne retourne ni hash ni identité du rédempteur'
);
select ok(
  position('creator_user_id=v_user' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_revoke(uuid)'::regprocedure))>0
  and position("status='active'" in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_revoke(uuid)'::regprocedure))>0,
  'révocation self-only d un code actif'
);
select ok(
  position("^[a-f0-9]{64}$" in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0
  and position("digest(v_raw,'sha256')" in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0
  and position('SOCIAL_LIVE_SHARE_CODE_UNAVAILABLE' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0,
  'rachat valide un secret hex 256 bits et utilise une erreur générique'
);
select ok(
  position('pg_advisory_xact_lock' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0
  and position('for update' in lower(pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure)))>0,
  'rachat sérialise et verrouille le code'
);
select ok(
  position('owner_user_id=v_code.creator_user_id' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0
  and position("visibility='private'" in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0
  and position('v_code.creator_user_id=v_user' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0,
  'rachat reste lié au propriétaire, au salon privé et interdit l auto-rachat'
);
select ok(
  position('social_is_suspended(v_code.creator_user_id)' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0
  and position('sinjira_age_band(v_user)' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0
  and position('sinjira_can_social_interact(v_user,v_code.creator_user_id)' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0
  and position('social_is_blocked(v_user,v_code.creator_user_id)' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0,
  'rachat revalide suspension, cohorte, interaction et blocage'
);
select ok(
  position('insert into public.social_live_room_members' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0
  and position('insert into private.social_live_room_invites' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0
  and position("status='accepted'" in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0,
  'rachat crée adhésion et trace invitation acceptée côté serveur'
);
select ok(
  position("set status='used',closed_at=now()" in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))>0
  and position('redeemed_by_user_id' in pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure))=0,
  'code consommé sans persister l identité du rédempteur'
);
select ok(
  position('social_profiles' in lower(pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure)))=0
  and position('account_identities' in lower(pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure)))=0
  and position('inet_client_addr' in lower(pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure)))=0
  and position('latitude' in lower(pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure)))=0
  and position('longitude' in lower(pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure)))=0,
  'rachat sans annuaire, handle privé, IP ni GPS'
);
select ok(
  position('creator_user_id' in split_part(lower(pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure)),'return jsonb_build_object(',2))=0
  and position('redeemed_by_user_id' in split_part(lower(pg_get_functiondef('sinjira_social_user_internal.social_live_share_code_redeem(text)'::regprocedure)),'return jsonb_build_object(',2))=0,
  'réponse de rachat ne retourne aucun UUID utilisateur'
);

select * from finish();
rollback;
