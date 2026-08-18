#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260818002114_sinjira_v24_4_55_public_comment_security.sql'
errors=[]

def need(cond,msg):
    if not cond: errors.append(msg)

need(MIG.exists(),'migration V24.4.55 absente')
if MIG.exists():
    sql=MIG.read_text('utf-8')
    for marker in (
      'avatar_path_snapshot',
      'set_sinjira_comment_public_snapshot',
      'trg_sinjira_comment_public_snapshot',
      'list_sinjira_novel_comments',
      'sinjira_public_comments_security_health',
      "'version','24.4.55'"
    ):
        need(marker in sql,'élément sécurité commentaires absent: '+marker)

    need(
      'revoke all on function public.set_sinjira_comment_public_snapshot() from public,anon,authenticated' in sql,
      'fonction de snapshot publique/authentifiée'
    )
    need(
      'grant execute on function public.set_sinjira_comment_public_snapshot() to service_role' in sql,
      'fonction de snapshot non réservée au service serveur'
    )

    match=re.search(
      r'create or replace function public\.list_sinjira_novel_comments\(p_novel_slug text\)(.*?)revoke all on function public\.list_sinjira_novel_comments',
      sql,re.S|re.I
    )
    need(match is not None,'définition de list_sinjira_novel_comments introuvable')
    if match:
        fn=match.group(1).lower()
        need('returns table(id uuid, body text, spoiler boolean, created_at timestamptz, pseudo text, avatar_path text)' in fn,'signature publique historique des commentaires modifiée')
        need('security invoker' in fn,'list_sinjira_novel_comments n’est pas SECURITY INVOKER')
        need('join public.profiles' not in fn,'lecture publique rejoint encore la table profiles privée')
        need("c.status='approved'" in fn,'liste publique ne limite pas aux commentaires approuvés')
        need('limit 250' in fn,'limite publique 250 absente')
        need('display_name_snapshot' in fn and 'avatar_path_snapshot' in fn,'liste publique ne lit pas les snapshots')

    need(
      'grant execute on function public.list_sinjira_novel_comments(text) to anon,authenticated' in sql,
      'lecture publique des commentaires non accordée à anon/authenticated'
    )
    need(
      'security definer' in sql.split('create or replace function public.set_sinjira_comment_public_snapshot()',1)[1].split('$$;',1)[0].lower(),
      'trigger de snapshot doit rester SECURITY DEFINER côté serveur'
    )

if errors:
    print(f'ECHEC sécurité commentaires V24.4.55: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK sécurité commentaires V24.4.55: lecture publique SECURITY INVOKER, snapshots serveur et profils privés non exposés.')
