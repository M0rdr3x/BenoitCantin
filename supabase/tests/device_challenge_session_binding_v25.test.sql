begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, private, auth, extensions;

select plan(12);

select has_column(
  'public','security_connection_challenges','request_session_id',
  'les challenges conservent la session demandeuse'
);

select col_type_is(
  'public','security_connection_challenges','request_session_id','uuid',
  'request_session_id reste un UUID'
);

select has_trigger(
  'public','security_connection_challenges','security_connection_challenge_session_guard',
  'la table de challenges possède une garde de session centrale'
);

select ok(
  has_function_privilege(
    'service_role',
    'public.service_security_evaluate_context_session(uuid,text,text,text,text,text,text,text,uuid)',
    'EXECUTE'
  ),
  'le service serveur peut appeler le moteur de risque lié à la session'
);

select ok(
  not has_function_privilege(
    'authenticated',
    'public.service_security_evaluate_context_session(uuid,text,text,text,text,text,text,text,uuid)',
    'EXECUTE'
  ),
  'le navigateur ne peut pas appeler le moteur service-only lié à la session'
);

select ok(
  has_function_privilege(
    'service_role',
    'public.service_conscience_evaluate_access_session(uuid,text,text,text,text,text,text,uuid)',
    'EXECUTE'
  ),
  'le service serveur peut évaluer le Registre avec une session explicite'
);

select ok(
  not has_function_privilege(
    'authenticated',
    'public.service_conscience_evaluate_access_session(uuid,text,text,text,text,text,text,uuid)',
    'EXECUTE'
  ),
  'le navigateur ne peut pas appeler l’évaluation Registre session-aware'
);

select ok(
  not has_function_privilege(
    'service_role',
    'public.service_conscience_evaluate_access(uuid,text,text,text,text,text,text)',
    'EXECUTE'
  ),
  'l’ancien service Registre sans identité de session est fermé'
);

select ok(
  pg_get_functiondef(
    'private.security_rebind_service_session(uuid,text,uuid)'::regprocedure
  ) like '%from auth.sessions s%'
  and pg_get_functiondef(
    'private.security_rebind_service_session(uuid,text,uuid)'::regprocedure
  ) like '%is_trusted=false%'
  and pg_get_functiondef(
    'private.security_rebind_service_session(uuid,text,uuid)'::regprocedure
  ) like '%is_primary=false%',
  'le rebind valide auth.sessions et retire toute confiance héritée'
);

select ok(
  pg_get_functiondef(
    'private.security_challenge_request_session_guard()'::regprocedure
  ) like '%CHALLENGE_SESSION_REQUIRED%'
  and pg_get_functiondef(
    'private.security_challenge_request_session_guard()'::regprocedure
  ) like '%CHALLENGE_SESSION_MISMATCH%',
  'la résolution d’un challenge ancien ou réassocié échoue fermée'
);

select ok(
  pg_get_functiondef(
    'sinjira_security_internal.security_set_device_trust(uuid,boolean,boolean)'::regprocedure
  ) like '%c.request_session_id=v_session%',
  'une approbation fraîche ne peut augmenter la confiance que dans sa session demandeuse'
);

select ok(
  pg_get_functiondef(
    'public.service_conscience_evaluate_access_session(uuid,text,text,text,text,text,text,uuid)'::regprocedure
  ) like '%c.request_session_id=p_session_id%'
  and pg_get_functiondef(
    'public.service_conscience_evaluate_access_session(uuid,text,text,text,text,text,text,uuid)'::regprocedure
  ) like '%last_session_id = p_session_id%',
  'le Registre refuse de réutiliser un challenge d’une autre session'
);

select * from finish();
rollback;
