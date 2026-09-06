begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, private, auth, extensions;

select plan(12);

select ok(has_function_privilege('authenticated',
  'public.security_resolve_connection_challenge(uuid,text,text)','EXECUTE'),
  'authenticated conserve le wrapper public de résolution par appareil fiable');
select ok(has_function_privilege('authenticated',
  'public.security_resolve_connection_challenge_mfa(uuid,text)','EXECUTE'),
  'authenticated conserve le wrapper public de résolution MFA');

select ok(
  (select not p.prosecdef and array_to_string(p.proconfig,',') like '%search_path=%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='security_resolve_connection_challenge'
   and oidvectortypes(p.proargtypes)='uuid, text, text'),
  'le wrapper public standard reste SECURITY INVOKER avec search_path fixe'
);
select ok(
  (select not p.prosecdef and array_to_string(p.proconfig,',') like '%search_path=%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='security_resolve_connection_challenge_mfa'
   and oidvectortypes(p.proargtypes)='uuid, text'),
  'le wrapper public MFA reste SECURITY INVOKER avec search_path fixe'
);

select ok(
  (select p.prosecdef and array_to_string(p.proconfig,',') like '%search_path=%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='sinjira_security_internal' and p.proname='security_resolve_connection_challenge'
   and oidvectortypes(p.proargtypes)='uuid, text, text'),
  'implémentation standard interne reste SECURITY DEFINER avec search_path fixe'
);
select ok(
  (select p.prosecdef and array_to_string(p.proconfig,',') like '%search_path=%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='sinjira_security_internal' and p.proname='security_resolve_connection_challenge_mfa'
   and oidvectortypes(p.proargtypes)='uuid, text'),
  'implémentation MFA interne reste SECURITY DEFINER avec search_path fixe'
);

select ok(
  pg_get_functiondef('sinjira_security_internal.security_resolve_connection_challenge(uuid,text,text)'::regprocedure)
    like '%last_session_id=v_session%',
  'la résolution standard lie la clé de l’approbateur à la session courante'
);
select ok(
  pg_get_functiondef('sinjira_security_internal.security_resolve_connection_challenge(uuid,text,text)'::regprocedure)
    like '%CURRENT_TRUSTED_DEVICE_REQUIRED%',
  'la résolution standard refuse une clé fiable qui ne correspond pas à la session courante'
);
select ok(
  pg_get_functiondef('sinjira_security_internal.security_resolve_connection_challenge_mfa(uuid,text)'::regprocedure)
    like '%v_action=''conscience_vault''%',
  'la résolution MFA distingue explicitement les challenges du Coffre'
);
select ok(
  pg_get_functiondef('sinjira_security_internal.security_resolve_connection_challenge_mfa(uuid,text)'::regprocedure)
    like '%TRUSTED_OTHER_DEVICE_REQUIRED%',
  'la résolution MFA interdit l’auto-approbation du Coffre si un autre appareil fiable existe'
);
select ok(
  pg_get_functiondef('sinjira_security_internal.security_set_device_trust(uuid,boolean,boolean)'::regprocedure)
    like '%resolver.id<>v_row.id%',
  'une approbation fraîche de confiance doit provenir explicitement d’un autre appareil'
);
select ok(
  pg_get_functiondef('sinjira_security_internal.security_resolve_connection_challenge_mfa(uuid,text)'::regprocedure)
    like '%last_session_id=v_session%',
  'la résolution MFA lie aussi la clé fournie à la session courante'
);

select * from finish();
rollback;
