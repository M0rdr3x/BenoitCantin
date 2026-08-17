#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260817235509_sinjira_v24_4_52_admin_notification_triggers.sql'
errors=[]

def need(cond,msg):
    if not cond: errors.append(msg)

need(MIG.exists(),'migration V24.4.52 absente')
if MIG.exists():
    sql=MIG.read_text('utf-8')
    for marker in (
      'trg_admin_notify_access_request',
      'trg_admin_notify_novel_comment',
      'trg_admin_notify_social_report',
      'trg_admin_notify_fracture_report_insert',
      'trg_admin_notify_fracture_report_submit',
      'sinjira_admin_notifications_health',
      "'version','24.4.52'"
    ):
        need(marker in sql,'élément notifications absent: '+marker)
    need("new.status <> 'pending'" in sql,'filtre pending absent pour les flux modérés')
    need("new.status <> 'open'" in sql,'filtre open absent pour les signalements sociaux')
    need("old.submitted_at is null and new.submitted_at is not null" in sql,'rapport Fracture non limité au moment de soumission')
    for fn in (
      'notify_sinjira_admin_access_request',
      'notify_sinjira_admin_novel_comment',
      'notify_sinjira_admin_social_report',
      'notify_sinjira_admin_fracture_report'
    ):
        need(
          f'revoke all on function public.{fn}() from public,anon,authenticated' in sql,
          'fonction trigger exposée au navigateur: '+fn
        )

if errors:
    print(f'ECHEC notifications V24.4.52: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK notifications V24.4.52: demandes, commentaires, signalements et rapports Fracture créent des avis administrateur ciblés.')
