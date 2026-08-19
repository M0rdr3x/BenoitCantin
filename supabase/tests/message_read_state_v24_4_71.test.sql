begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(18);

select ok(not has_table_privilege('anon','public.social_real_messages','UPDATE'),'anon ne peut pas modifier les messages réels');
select ok(not has_table_privilege('anon','public.social_character_messages','UPDATE'),'anon ne peut pas modifier les messages personnage');
select ok(not has_table_privilege('authenticated','public.social_real_messages','UPDATE'),'messages réels: aucun UPDATE table-wide');
select ok(not has_table_privilege('authenticated','public.social_character_messages','UPDATE'),'messages personnage: aucun UPDATE table-wide');

select ok(has_column_privilege('authenticated','public.social_real_messages','read_at','UPDATE'),'messages réels: read_at est modifiable');
select ok(has_column_privilege('authenticated','public.social_character_messages','read_at','UPDATE'),'messages personnage: read_at est modifiable');
select ok(not has_column_privilege('authenticated','public.social_real_messages','body','UPDATE'),'messages réels: body non modifiable');
select ok(not has_column_privilege('authenticated','public.social_character_messages','body','UPDATE'),'messages personnage: body non modifiable');
select ok(not has_column_privilege('authenticated','public.social_real_messages','sender_user_id','UPDATE'),'messages réels: expéditeur non modifiable');
select ok(not has_column_privilege('authenticated','public.social_real_messages','recipient_user_id','UPDATE'),'messages réels: destinataire non modifiable');
select ok(not has_column_privilege('authenticated','public.social_character_messages','sender_user_id','UPDATE'),'messages personnage: expéditeur non modifiable');
select ok(not has_column_privilege('authenticated','public.social_character_messages','recipient_user_id','UPDATE'),'messages personnage: destinataire non modifiable');

select is((select count(*) from pg_policies where schemaname='public' and tablename='social_real_messages' and policyname='real_messages_mark_read' and cmd='UPDATE'),1::bigint,'politique UPDATE self-only réelle présente');
select is((select count(*) from pg_policies where schemaname='public' and tablename='social_character_messages' and policyname='char_messages_mark_read' and cmd='UPDATE'),1::bigint,'politique UPDATE self-only personnage présente');
select ok(exists(select 1 from pg_indexes where schemaname='public' and tablename='social_real_messages' and indexname='social_real_messages_unread_recipient_idx'),'index non-lus réel présent');
select ok(exists(select 1 from pg_indexes where schemaname='public' and tablename='social_character_messages' and indexname='social_character_messages_unread_recipient_idx'),'index non-lus personnage présent');
select ok(exists(select 1 from pg_policies where schemaname='public' and tablename='social_real_messages' and policyname='real_messages_mark_read' and with_check ilike '%read_at IS NOT NULL%'),'messages réels: impossible de remettre un message en non-lu');
select ok(exists(select 1 from pg_policies where schemaname='public' and tablename='social_character_messages' and policyname='char_messages_mark_read' and with_check ilike '%read_at IS NOT NULL%'),'messages personnage: impossible de remettre un message en non-lu');

select * from finish();
rollback;
