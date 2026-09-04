begin;

select plan(30);

select has_table('public', 'employment_profiles', 'employment_profiles existe');
select has_table('public', 'employment_applications', 'employment_applications existe');
select has_column('public', 'employment_profiles', 'user_id', 'profil lié à son utilisateur');
select has_column('public', 'employment_applications', 'user_id', 'candidature liée à son utilisateur');

select ok((select relrowsecurity from pg_class where oid='public.employment_profiles'::regclass), 'RLS activé sur les profils');
select ok((select relforcerowsecurity from pg_class where oid='public.employment_profiles'::regclass), 'RLS forcé sur les profils');
select ok((select relrowsecurity from pg_class where oid='public.employment_applications'::regclass), 'RLS activé sur les candidatures');
select ok((select relforcerowsecurity from pg_class where oid='public.employment_applications'::regclass), 'RLS forcé sur les candidatures');

select ok(not has_table_privilege('anon','public.employment_profiles','SELECT'), 'anon ne lit pas les profils Emploi');
select ok(not has_table_privilege('anon','public.employment_applications','SELECT'), 'anon ne lit pas les candidatures');
select ok(has_table_privilege('authenticated','public.employment_profiles','SELECT'), 'authenticated peut lire sous RLS');
select ok(has_table_privilege('authenticated','public.employment_profiles','INSERT'), 'authenticated peut insérer son profil sous RLS');
select ok(has_table_privilege('authenticated','public.employment_profiles','UPDATE'), 'authenticated peut modifier son profil sous RLS');
select ok(has_table_privilege('authenticated','public.employment_profiles','DELETE'), 'authenticated peut supprimer son profil sous RLS');
select ok(has_table_privilege('authenticated','public.employment_applications','SELECT'), 'authenticated peut lire ses candidatures sous RLS');
select ok(has_table_privilege('authenticated','public.employment_applications','INSERT'), 'authenticated peut ajouter ses candidatures sous RLS');
select ok(has_table_privilege('authenticated','public.employment_applications','UPDATE'), 'authenticated peut modifier ses candidatures sous RLS');
select ok(has_table_privilege('authenticated','public.employment_applications','DELETE'), 'authenticated peut supprimer ses candidatures sous RLS');

select is((select count(*)::int from pg_policies where schemaname='public' and tablename='employment_profiles'), 4, 'quatre politiques propriétaire sur les profils');
select is((select count(*)::int from pg_policies where schemaname='public' and tablename='employment_applications'), 4, 'quatre politiques propriétaire sur les candidatures');
select ok(not exists(select 1 from pg_policies where schemaname='public' and tablename='employment_profiles' and coalesce(qual,'') <> '' and qual not ilike '%auth.uid%'), 'les USING du profil restent liés à auth.uid');
select ok(not exists(select 1 from pg_policies where schemaname='public' and tablename='employment_applications' and coalesce(qual,'') <> '' and qual not ilike '%auth.uid%'), 'les USING des candidatures restent liés à auth.uid');

select ok(to_regclass('public.employment_job_listings') is null, 'aucune table de fausses offres n’est créée');
select ok(not exists(
  select 1 from pg_constraint c
  where c.contype='f'
    and c.conrelid in ('public.employment_profiles'::regclass,'public.employment_applications'::regclass)
    and c.confrelid <> 'auth.users'::regclass
), 'les données Emploi ne référencent aucun autre module SINJIRA');

select ok(coalesce(obj_description('public.employment_profiles'::regclass),'') ilike '%Registre personnel%', 'le profil documente la séparation du Registre personnel');
select ok(coalesce(obj_description('public.employment_applications'::regclass),'') ilike '%Registre personnel%', 'le suivi documente la séparation du Registre personnel');
select ok(exists(select 1 from pg_constraint where conrelid='public.employment_profiles'::regclass and contype='c' and pg_get_constraintdef(oid) ilike '%actively_looking%'), 'les états de recherche sont bornés');
select ok(exists(select 1 from pg_constraint where conrelid='public.employment_applications'::regclass and contype='c' and pg_get_constraintdef(oid) ilike '%accepted%'), 'les états de candidature sont bornés');
select ok(exists(select 1 from pg_constraint where conrelid='public.employment_profiles'::regclass and contype='c' and pg_get_constraintdef(oid) ilike '%cardinality%'), 'la liste de compétences est bornée');
select ok(exists(select 1 from pg_constraint where conrelid='public.employment_applications'::regclass and contype='c' and pg_get_constraintdef(oid) ilike '%https%'), 'les liens sources sont limités à HTTP/HTTPS');

select * from finish();
rollback;
