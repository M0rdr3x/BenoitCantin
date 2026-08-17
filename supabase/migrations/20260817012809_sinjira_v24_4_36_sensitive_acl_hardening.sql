-- SINJIRA™ V24.4.36 — défense en profondeur des ACL sensibles.
-- RLS reste la barrière fonctionnelle; ces ACL retirent les droits SQL inutiles aux rôles navigateur.

revoke all privileges on table public.guardian_links from public, anon;
revoke insert, update, delete, truncate, references, trigger on table public.guardian_links from authenticated;
grant select on table public.guardian_links to authenticated;

revoke all privileges on table public.guardian_signup_invites from public, anon;
revoke insert, update, delete, truncate, references, trigger on table public.guardian_signup_invites from authenticated;
grant select on table public.guardian_signup_invites to authenticated;

revoke all privileges on table public.private_family_links from public, anon;
revoke truncate, references, trigger on table public.private_family_links from authenticated;
grant select, insert, update, delete on table public.private_family_links to authenticated;

revoke all privileges on table public.social_real_messages from public, anon;
revoke update, delete, truncate, references, trigger on table public.social_real_messages from authenticated;
grant select, insert on table public.social_real_messages to authenticated;

revoke all privileges on table public.social_character_messages from public, anon;
revoke update, delete, truncate, references, trigger on table public.social_character_messages from authenticated;
grant select, insert on table public.social_character_messages to authenticated;

create or replace function public.sinjira_sensitive_acl_health()
returns jsonb
language sql
stable
security definer
set search_path=public
as $$
  with checks as (
    select * from (values
      ('guardian_links_anon_sealed', not has_table_privilege('anon','public.guardian_links','select,insert,update,delete')),
      ('guardian_signup_invites_anon_sealed', not has_table_privilege('anon','public.guardian_signup_invites','select,insert,update,delete')),
      ('guardian_signup_invites_auth_read_only', has_table_privilege('authenticated','public.guardian_signup_invites','select') and not has_table_privilege('authenticated','public.guardian_signup_invites','insert,update,delete')),
      ('private_family_links_anon_sealed', not has_table_privilege('anon','public.private_family_links','select,insert,update,delete')),
      ('social_real_messages_anon_sealed', not has_table_privilege('anon','public.social_real_messages','select,insert,update,delete')),
      ('social_real_messages_auth_minimal', has_table_privilege('authenticated','public.social_real_messages','select,insert') and not has_table_privilege('authenticated','public.social_real_messages','update,delete')),
      ('social_character_messages_anon_sealed', not has_table_privilege('anon','public.social_character_messages','select,insert,update,delete')),
      ('social_character_messages_auth_minimal', has_table_privilege('authenticated','public.social_character_messages','select,insert') and not has_table_privilege('authenticated','public.social_character_messages','update,delete'))
    ) v(name, ok)
  )
  select jsonb_build_object(
    'ok', bool_and(ok),
    'version', '24.4.36',
    'checks', jsonb_object_agg(name,ok)
  ) from checks;
$$;
revoke all on function public.sinjira_sensitive_acl_health() from public, anon, authenticated;
grant execute on function public.sinjira_sensitive_acl_health() to service_role;
