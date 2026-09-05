begin;

select plan(32);

select has_table('private','personal_ai_settings','réglages Mon IA privés');
select has_table('private','personal_ai_source_permissions','permissions de sources privées');
select has_table('private','personal_ai_audit','audit Mon IA privé');

select ok(not has_table_privilege('anon','private.personal_ai_settings','SELECT'), 'anon ne lit pas les réglages');
select ok(not has_table_privilege('authenticated','private.personal_ai_settings','SELECT'), 'authenticated ne lit pas directement les réglages');
select ok(not has_table_privilege('service_role','private.personal_ai_settings','SELECT'), 'service_role ne lit pas directement les réglages');
select ok(not has_table_privilege('anon','private.personal_ai_source_permissions','SELECT'), 'anon ne lit pas les permissions');
select ok(not has_table_privilege('authenticated','private.personal_ai_source_permissions','SELECT'), 'authenticated ne lit pas directement les permissions');
select ok(not has_table_privilege('service_role','private.personal_ai_source_permissions','SELECT'), 'service_role ne lit pas directement les permissions');
select ok(not has_table_privilege('authenticated','private.personal_ai_audit','SELECT'), 'authenticated ne lit pas l audit');
select ok(not has_table_privilege('service_role','private.personal_ai_audit','SELECT'), 'service_role ne lit pas directement l audit');

select has_function('public','service_personal_ai_evaluate_access',array['uuid','text','text','text','text','text','text'],'wrapper risque ai_private présent');
select has_function('public','service_personal_ai_get_state',array['uuid','text','integer','text','text'],'lecture serveur présente');
select has_function('public','service_personal_ai_update_settings',array['uuid','boolean','text','text','text','integer','text','text'],'écriture réglages serveur présente');
select has_function('public','service_personal_ai_set_source_permission',array['uuid','text','boolean','text','integer','text','text'],'gestion consentement serveur présente');
select has_function('public','service_personal_ai_delete_data',array['uuid','text','integer','text','text'],'suppression serveur présente');

select ok(not has_function_privilege('anon','public.service_personal_ai_get_state(uuid,text,integer,text,text)','EXECUTE'), 'anon ne peut appeler get_state');
select ok(not has_function_privilege('authenticated','public.service_personal_ai_get_state(uuid,text,integer,text,text)','EXECUTE'), 'authenticated ne peut appeler get_state directement');
select ok(has_function_privilege('service_role','public.service_personal_ai_get_state(uuid,text,integer,text,text)','EXECUTE'), 'service_role peut appeler get_state');
select ok(not has_function_privilege('authenticated','public.service_personal_ai_update_settings(uuid,boolean,text,text,text,integer,text,text)','EXECUTE'), 'authenticated ne peut modifier directement');
select ok(has_function_privilege('service_role','public.service_personal_ai_update_settings(uuid,boolean,text,text,text,integer,text,text)','EXECUTE'), 'service_role peut modifier via Edge');
select ok(not has_function_privilege('authenticated','public.service_personal_ai_set_source_permission(uuid,text,boolean,text,integer,text,text)','EXECUTE'), 'authenticated ne peut accorder une source directement');
select ok(has_function_privilege('service_role','public.service_personal_ai_set_source_permission(uuid,text,boolean,text,integer,text,text)','EXECUTE'), 'service_role peut gérer les consentements via Edge');
select ok(not has_function_privilege('authenticated','public.service_personal_ai_delete_data(uuid,text,integer,text,text)','EXECUTE'), 'authenticated ne peut contourner la suppression protégée');
select ok(has_function_privilege('service_role','public.service_personal_ai_delete_data(uuid,text,integer,text,text)','EXECUTE'), 'service_role peut supprimer via Edge');

select ok(exists(
  select 1 from pg_constraint
  where conrelid='private.personal_ai_source_permissions'::regclass
    and contype='c'
    and pg_get_constraintdef(oid) ilike '%life_story%'
    and pg_get_constraintdef(oid) ilike '%employment%'
), 'sources initiales explicitement bornées');
select ok(not exists(
  select 1 from pg_constraint
  where conrelid='private.personal_ai_source_permissions'::regclass
    and contype='c'
    and pg_get_constraintdef(oid) ilike '%conscience%'
), 'le Registre personnel n est jamais une source autorisable');
select ok(exists(
  select 1 from pg_constraint
  where conrelid='private.personal_ai_settings'::regclass
    and contype='c'
    and pg_get_constraintdef(oid) ilike '%not_configured%'
), 'le runtime reste non configuré en fondation V25');
select ok(coalesce(obj_description('private.personal_ai_settings'::regclass),'') ilike '%aucune conversation%', 'absence de mémoire conversationnelle documentée');
select ok(coalesce(obj_description('private.personal_ai_source_permissions'::regclass),'') ilike '%aucun RPC V25 ne lit%', 'permissions sans récupération de source documentées');

select ok(exists(
  select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.proname='service_personal_ai_evaluate_access'
    and p.prosecdef
    and array_to_string(p.proconfig,',') ilike '%search_path%'
), 'wrapper ai_private SECURITY DEFINER à search_path fixé');
select ok(exists(
  select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.proname='service_personal_ai_get_state'
    and p.prosecdef
    and array_to_string(p.proconfig,',') ilike '%search_path%'
), 'RPC de lecture SECURITY DEFINER à search_path fixé');

select * from finish();
rollback;
