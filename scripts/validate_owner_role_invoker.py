#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260818002945_sinjira_v24_4_56_owner_role_invoker.sql'
errors=[]

def need(cond,msg):
    if not cond: errors.append(msg)

need(MIG.exists(),'migration V24.4.56 absente')
if MIG.exists():
    sql=MIG.read_text('utf-8').lower()
    for marker in (
      'internal_admin_users_role_check',
      "role in ('owner','admin')",
      'internal_admin_users_self_read',
      'is_sinjira_admin',
      'is_sinjira_owner',
      'sinjira_owner_role_health',
      "'version','24.4.56'"
    ):
        need(marker in sql,'élément rôle propriétaire absent: '+marker)
    need("lower(coalesce(u.email,''))='kingtyrano@gmail.com'" in sql,'le rôle owner n’est pas explicitement rattaché au compte propriétaire attendu')
    need(sql.count('security invoker') >= 3,'fonctions rôle/health non SECURITY INVOKER')
    need('set search_path=public,auth,pg_temp' in sql,'search_path sécurisé absent des fonctions rôle')
    need("where a.user_id=p_user_id and a.role='owner'" in sql,'is_sinjira_owner ne vérifie pas le rôle owner')
    need("p_user_id=(select auth.uid())" in sql,'vérification self auth.uid absente')
    need("coalesce(auth.jwt()->>'role','')='service_role'" in sql,'chemin service_role explicite absent')
    need('revoke all on public.internal_admin_users from anon' in sql,'table des admins lisible par anon')
    need('grant select on public.internal_admin_users to authenticated' in sql,'lecture self admin non accordée à authenticated')
    need('revoke insert,update,delete on public.internal_admin_users from authenticated' in sql,'écriture admin non révoquée pour authenticated')
    need('revoke all on function public.is_sinjira_admin(uuid) from public,anon' in sql,'is_sinjira_admin exposée à anon/public')
    need('revoke all on function public.is_sinjira_owner(uuid) from public,anon' in sql,'is_sinjira_owner exposée à anon/public')
    need('revoke all on function public.sinjira_owner_role_health() from public,anon,authenticated' in sql,'healthcheck propriétaire exposé à un rôle navigateur')
    need('grant execute on function public.sinjira_owner_role_health() to service_role' in sql,'healthcheck propriétaire non réservé au service_role')

if errors:
    print(f'ECHEC rôle propriétaire V24.4.56: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK rôle propriétaire V24.4.56: owner/admin explicites, lecture self RLS, fonctions SECURITY INVOKER et healthcheck service-only.')
