begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(36);

-- Anon n'a aucun accès direct aux quatre tables.
select ok(not has_table_privilege('anon','public.social_real_posts','SELECT'),'anon: pas SELECT publications réelles');
select ok(not has_table_privilege('anon','public.social_real_posts','INSERT'),'anon: pas INSERT publications réelles');
select ok(not has_table_privilege('anon','public.social_real_posts','UPDATE'),'anon: pas UPDATE publications réelles');
select ok(not has_table_privilege('anon','public.social_real_posts','DELETE'),'anon: pas DELETE publications réelles');
select ok(not has_table_privilege('anon','public.social_real_comments','SELECT'),'anon: pas SELECT commentaires réels');
select ok(not has_table_privilege('anon','public.social_real_comments','INSERT'),'anon: pas INSERT commentaires réels');
select ok(not has_table_privilege('anon','public.social_real_comments','UPDATE'),'anon: pas UPDATE commentaires réels');
select ok(not has_table_privilege('anon','public.social_real_comments','DELETE'),'anon: pas DELETE commentaires réels');
select ok(not has_table_privilege('anon','public.social_character_posts','SELECT'),'anon: pas SELECT publications personnage');
select ok(not has_table_privilege('anon','public.social_character_posts','INSERT'),'anon: pas INSERT publications personnage');
select ok(not has_table_privilege('anon','public.social_character_posts','UPDATE'),'anon: pas UPDATE publications personnage');
select ok(not has_table_privilege('anon','public.social_character_posts','DELETE'),'anon: pas DELETE publications personnage');
select ok(not has_table_privilege('anon','public.social_character_comments','SELECT'),'anon: pas SELECT commentaires personnage');
select ok(not has_table_privilege('anon','public.social_character_comments','INSERT'),'anon: pas INSERT commentaires personnage');
select ok(not has_table_privilege('anon','public.social_character_comments','UPDATE'),'anon: pas UPDATE commentaires personnage');
select ok(not has_table_privilege('anon','public.social_character_comments','DELETE'),'anon: pas DELETE commentaires personnage');

-- Authenticated lit et peut demander une suppression, mais INSERT/UPDATE restent colonne-par-colonne.
select ok(has_table_privilege('authenticated','public.social_real_posts','SELECT'),'auth: SELECT publications réelles');
select ok(has_table_privilege('authenticated','public.social_real_posts','DELETE'),'auth: DELETE publications réelles soumis RLS');
select ok(not has_table_privilege('authenticated','public.social_real_posts','INSERT'),'auth: pas INSERT table-wide publications réelles');
select ok(not has_table_privilege('authenticated','public.social_real_posts','UPDATE'),'auth: pas UPDATE table-wide publications réelles');
select ok(has_table_privilege('authenticated','public.social_real_comments','SELECT'),'auth: SELECT commentaires réels');
select ok(has_table_privilege('authenticated','public.social_real_comments','DELETE'),'auth: DELETE commentaires réels soumis RLS');
select ok(has_table_privilege('authenticated','public.social_character_posts','SELECT'),'auth: SELECT publications personnage');
select ok(has_table_privilege('authenticated','public.social_character_posts','DELETE'),'auth: DELETE publications personnage soumis RLS');
select ok(has_table_privilege('authenticated','public.social_character_comments','SELECT'),'auth: SELECT commentaires personnage');
select ok(has_table_privilege('authenticated','public.social_character_comments','DELETE'),'auth: DELETE commentaires personnage soumis RLS');

-- Seul body est éditable côté navigateur.
select ok(has_column_privilege('authenticated','public.social_real_posts','body','UPDATE'),'auth: body publication réelle éditable');
select ok(not has_column_privilege('authenticated','public.social_real_posts','user_id','UPDATE'),'auth: user_id publication réelle immuable');
select ok(has_column_privilege('authenticated','public.social_real_comments','body','UPDATE'),'auth: body commentaire réel éditable');
select ok(not has_column_privilege('authenticated','public.social_real_comments','post_id','UPDATE'),'auth: post_id commentaire réel immuable');
select ok(has_column_privilege('authenticated','public.social_character_posts','body','UPDATE'),'auth: body publication personnage éditable');
select ok(not has_column_privilege('authenticated','public.social_character_posts','character_id','UPDATE'),'auth: character_id publication personnage immuable');
select ok(has_column_privilege('authenticated','public.social_character_comments','body','UPDATE'),'auth: body commentaire personnage éditable');
select ok(not has_column_privilege('authenticated','public.social_character_comments','character_id','UPDATE'),'auth: character_id commentaire personnage immuable');

-- Les politiques UPDATE self-only finales existent.
select is((select count(*) from pg_policies where schemaname='public' and policyname in ('real_posts_update','real_comments_update') and cmd='UPDATE'),2::bigint,'deux politiques UPDATE réelles présentes');
select is((select count(*) from pg_policies where schemaname='public' and policyname in ('char_posts_update','char_comments_update') and cmd='UPDATE'),2::bigint,'deux politiques UPDATE personnage présentes');

select * from finish();
rollback;
