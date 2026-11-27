#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
ADMIN=ROOT/'admin'/'sinjira'/'index.html'
V18=ROOT/'assets'/'js'/'sinjira-admin-v18.js'
HEALTH=ROOT/'assets'/'js'/'v24-admin-health.js'

REQUIRED_TABS=[
 'projects','documents','players','access','playtests','reports','reader-comments',
 'fan-characters','character-bible','canon-sinjira','analytics','extensions',
 'system-health','audit-log','social-moderation'
]


def main()->int:
 errors=[]
 if not ADMIN.exists(): errors.append('Route lowercase /admin/sinjira/ absente.')
 if not V18.exists(): errors.append('Module sinjira-admin-v18.js absent.')
 if not HEALTH.exists(): errors.append('Diagnostic v24-admin-health.js absent.')
 if errors:
  for e in errors: print('- '+e)
  return 1
 html=ADMIN.read_text('utf-8',errors='ignore')
 v18=V18.read_text('utf-8',errors='ignore')
 health=HEALTH.read_text('utf-8',errors='ignore')
 for tab in REQUIRED_TABS:
  if f'data-admin-tab="{tab}"' not in html: errors.append(f'Onglet admin absent: {tab}')
  if f'data-admin-panel="{tab}"' not in html: errors.append(f'Panneau admin absent: {tab}')
 if "import './v24-admin-health.js'" not in v18:
  errors.append('Le module admin principal ne charge pas le diagnostic V24 avancé.')
 for rpc in ['get_sinjira_server_version','get_sinjira_runtime_health','ensure_sinjira_owner_character','has_sinjira_product','fracture_engine_health']:
  if rpc not in health: errors.append(f'Diagnostic admin incomplet, RPC absente: {rpc}')
 if 'Identifiant du projet' not in health:
  errors.append("L'interface admin n'applique plus le libellé 'Identifiant du projet'.")
 if 'Fracture du Réseau-Mère' not in health:
  errors.append("L'identifiant visible officiel de Fracture n'est plus normalisé.")
 # Associations vérifiées sans ouvrir de session.
 ids=re.findall(r'\bid="([^"]+)"',html)
 if len(ids)!=len(set(ids)): errors.append('Identifiants HTML dupliqués.')
 labels=re.findall(r'<label for="([^"]+)"[^>]*>',html)
 if len(labels)<40 or any(ids.count(label)!=1 for label in labels):
  errors.append('Associations des libellés de formulaire incomplètes.')
 for tab in REQUIRED_TABS:
  if f'id="admin-tab-{tab}" aria-controls="admin-panel-{tab}"' not in html:
   errors.append(f'Commande non reliée à son panneau: {tab}')
  if f'id="admin-panel-{tab}" aria-labelledby="admin-tab-{tab}"' not in html:
   errors.append(f'Panneau non nommé: {tab}')
 for marker in ('href="#contenu"','id="contenu" tabindex="-1"','sinjira-admin-console-ux-v1.css?v=1.0.0'):
  if marker not in html: errors.append(f'Accessibilité admin: {marker}')
 css=(ROOT/'assets/css/sinjira-admin-console-ux-v1.css').read_text('utf-8')
 for marker in ('min-height:44px','overflow-wrap:anywhere','@media(max-width:480px)', 'font-size:max(1rem,16px)'):
  if marker not in css: errors.append(f'CSS admin: {marker}')
 if '/Admin/sinjira/' in html:
  errors.append('Ancien chemin /Admin/sinjira/ présent dans la console officielle.')
 if errors:
  print(f'ECHEC admin: {len(errors)} problème(s).')
  for e in errors: print('- '+e)
  return 1
 print(f'OK admin: route lowercase, {len(REQUIRED_TABS)} onglets/panneaux, diagnostic V24 et identifiants professionnels vérifiés.')
 return 0

if __name__=='__main__': raise SystemExit(main())
