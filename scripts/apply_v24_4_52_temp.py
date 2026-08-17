from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

# Ledger production
ledger=ROOT/'supabase/production-migration-ledger.txt'
text=ledger.read_text('utf-8')
line='20260817235509 sinjira_v24_4_52_admin_notification_triggers\n'
if line not in text:
    if not text.endswith('\n'): text+='\n'
    text+=line
ledger.write_text(text,'utf-8')

# Contrat ledger
p=ROOT/'scripts/validate_production_migration_ledger.py'
text=p.read_text('utf-8')
text=text.replace('EXPECTED_COUNT=83','EXPECTED_COUNT=84').replace("EXPECTED_LAST='20260817234217'","EXPECTED_LAST='20260817235509'")
p.write_text(text,'utf-8')

# Bouton Ouvrir : commentaire roman -> onglet commentaires
p=ROOT/'assets/js/sinjira-admin-v18.js'
text=p.read_text('utf-8')
needle="if(type.includes('social')||entity.includes('social'))return 'social-moderation';"
repl="if(type.includes('novel_comment')||entity.includes('novel_comment'))return 'reader-comments';\n if(type.includes('social')||entity.includes('social'))return 'social-moderation';"
if needle not in text: raise SystemExit('notificationTarget needle absent')
text=text.replace(needle,repl)
p.write_text(text,'utf-8')

# Cache-buster admin
p=ROOT/'admin/sinjira/index.html'
text=p.read_text('utf-8')
text=text.replace('sinjira-admin-v18.js?v=18.51','sinjira-admin-v18.js?v=18.52')
p.write_text(text,'utf-8')

# Nouveau validateur des triggers
p=ROOT/'scripts/validate_admin_notification_triggers.py'
p.write_text('''#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260817235509_sinjira_v24_4_52_admin_notification_triggers.sql'
JS=ROOT/'assets/js/sinjira-admin-v18.js'
errors=[]
def need(cond,msg):
    if not cond: errors.append(msg)
need(MIG.exists(),'migration V24.4.52 absente')
if MIG.exists():
    sql=MIG.read_text('utf-8')
    for marker in (
      'trg_admin_notify_access_request','trg_admin_notify_novel_comment','trg_admin_notify_social_report',
      'trg_admin_notify_fracture_report_insert','trg_admin_notify_fracture_report_submit',
      'sinjira_admin_notifications_health','24.4.52'):
        need(marker in sql,'élément notifications absent: '+marker)
    need("new.status <> 'pending'" in sql,'filtre demande/commentaire pending absent')
    need("new.status <> 'open'" in sql,'filtre signalement open absent')
    need("old.submitted_at is null and new.submitted_at is not null" in sql,'rapport Fracture non limité au moment de soumission')
    for fn in ('notify_sinjira_admin_access_request','notify_sinjira_admin_novel_comment','notify_sinjira_admin_social_report','notify_sinjira_admin_fracture_report'):
        need(f'revoke all on function public.{fn}() from public,anon,authenticated' in sql,'fonction trigger exposée: '+fn)
js=JS.read_text('utf-8')
need("return 'reader-comments'" in js,'notification commentaire roman ne cible pas l’onglet reader-comments')
if errors:
    print(f'ECHEC notifications V24.4.52: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK notifications V24.4.52: demandes, commentaires, signalements et rapports Fracture sont reliés au centre admin.')
''','utf-8')

# CI principale
p=ROOT/'.github/workflows/validate-site.yml'
text=p.read_text('utf-8')
needle='      - name: Vérifier la parité client/serveur de l’administration V24.4.50\n        run: python scripts/validate_admin_action_contract.py\n'
repl=needle+'      - name: Vérifier les déclencheurs de notifications administrateur V24.4.52\n        run: python scripts/validate_admin_notification_triggers.py\n'
if needle not in text: raise SystemExit('validate-site needle absent')
text=text.replace(needle,repl)
p.write_text(text,'utf-8')
print('V24.4.52 patch applied')
