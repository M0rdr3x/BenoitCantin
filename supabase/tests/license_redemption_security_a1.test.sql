begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(10);

select ok(
  to_regprocedure('public.redeem_sinjira_activation(text,uuid)') is not null,
  'RPC redeem_sinjira_activation existe'
);
select ok(
  (select prosecdef from pg_proc where oid='public.redeem_sinjira_activation(text,uuid)'::regprocedure),
  'RPC activation reste SECURITY DEFINER'
);
select ok(
  has_function_privilege('service_role','public.redeem_sinjira_activation(text,uuid)','execute'),
  'service_role peut exécuter la RPC activation'
);
select ok(
  not has_function_privilege('authenticated','public.redeem_sinjira_activation(text,uuid)','execute'),
  'authenticated ne peut pas exécuter directement la RPC activation'
);
select ok(
  not has_function_privilege('anon','public.redeem_sinjira_activation(text,uuid)','execute'),
  'anon ne peut pas exécuter directement la RPC activation'
);
select like(
  pg_get_functiondef('public.redeem_sinjira_activation(text,uuid)'::regprocedure),
  '%for update%',
  'le code activation est verrouillé transactionnellement'
);
select like(
  pg_get_functiondef('public.redeem_sinjira_activation(text,uuid)'::regprocedure),
  '%status=''unused''%',
  'seul un code inutilisé peut être activé'
);
select like(
  pg_get_functiondef('public.redeem_sinjira_activation(text,uuid)'::regprocedure),
  '%insert into public.user_entitlements%',
  'la RPC attribue le droit numérique côté serveur'
);
select like(
  pg_get_functiondef('public.redeem_sinjira_activation(text,uuid)'::regprocedure),
  '%on conflict (user_id,product_id) do nothing%',
  'l attribution est idempotente par utilisateur et produit'
);
select like(
  pg_get_functiondef('public.redeem_sinjira_activation(text,uuid)'::regprocedure),
  '%redeemed_by=p_user_id%',
  'le code consommé est lié à l utilisateur fourni par le serveur'
);

select * from finish();
rollback;
