-- Tests de cloisonnement effectif Storage, uniquement sur PostgreSQL local.
-- Les objets sont des métadonnées synthétiques, jamais des fichiers réels.
begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,extensions;
select plan(12);

select is((select count(*)::int from storage.buckets
  where id in ('sinjira-character-sources','sinjira-character-submissions') and public is false),
  2,'les deux compartiments de photos restent privés');
select ok((select relrowsecurity from pg_class where oid='storage.objects'::regclass),
  'RLS active sur les métadonnées Storage');

insert into storage.objects(bucket_id,name) values
 ('sinjira-character-sources','10000000-0000-4000-8000-000000000001/acl-contract-a.webp'),
 ('sinjira-character-sources','10000000-0000-4000-8000-000000000002/acl-contract-b.webp');

set local role authenticated;
set local request.jwt.claim.sub='10000000-0000-4000-8000-000000000001';
set local request.jwt.claims='{"sub":"10000000-0000-4000-8000-000000000001","role":"authenticated","aal":"aal2"}';

select is((select auth.uid()::text),'10000000-0000-4000-8000-000000000001'::text,
  'identité de test A effectivement active');
select is((select count(*)::int from storage.objects where bucket_id='sinjira-character-sources' and name='10000000-0000-4000-8000-000000000001/acl-contract-a.webp'),
  1,'A peut lire son propre objet');
select is((select count(*)::int from storage.objects where bucket_id='sinjira-character-sources' and name='10000000-0000-4000-8000-000000000002/acl-contract-b.webp'),
  0,'A ne peut lire l objet B');
select throws_ok($$insert into storage.objects(bucket_id,name) values ('sinjira-character-sources','10000000-0000-4000-8000-000000000002/acl-contract-cross.webp')$$,
  '42501',null,'A ne peut écrire dans le dossier B');
select lives_ok($$insert into storage.objects(bucket_id,name) values ('sinjira-character-sources','10000000-0000-4000-8000-000000000001/acl-contract-own.webp')$$,
  'A conserve son droit d écriture légitime');
with removed as (delete from storage.objects where bucket_id='sinjira-character-sources' and name='10000000-0000-4000-8000-000000000002/acl-contract-b.webp' returning 1) select is((select count(*)::int from removed),
  0,'A ne peut supprimer l objet B');

set local request.jwt.claim.sub='10000000-0000-4000-8000-000000000002';
set local request.jwt.claims='{"sub":"10000000-0000-4000-8000-000000000002","role":"authenticated","aal":"aal2"}';
select is((select auth.uid()::text),'10000000-0000-4000-8000-000000000002'::text,
  'identité de test B effectivement active');
select is((select count(*)::int from storage.objects where bucket_id='sinjira-character-sources' and name='10000000-0000-4000-8000-000000000001/acl-contract-a.webp'),
  0,'B ne peut lire l objet A');
select is((select count(*)::int from storage.objects where bucket_id='sinjira-character-sources' and name='10000000-0000-4000-8000-000000000002/acl-contract-b.webp'),
  1,'B peut encore lire son propre objet');
with removed as (delete from storage.objects where bucket_id='sinjira-character-sources' and name='10000000-0000-4000-8000-000000000002/acl-contract-b.webp' returning 1) select is((select count(*)::int from removed),
  1,'B peut supprimer son propre objet');

reset role;
select * from finish();
rollback;
