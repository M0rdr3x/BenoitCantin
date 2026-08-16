#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'
OWNER='kingtyrano@gmail.com'


def main()->int:
 errors=[]
 sql='\n'.join(p.read_text('utf-8',errors='ignore') for p in sorted(MIG.glob('*.sql')))
 low=re.sub(r'\s+',' ',sql.lower())
 required=[
  OWNER,
  "'abysstime'",
  "'benoit cantin'",
  "'sinjira — livre ii (titre à confirmer)'",
  "'unlimited_tokens',true",
  "'all_content',true",
  "'all_games',true",
  "'all_romans',true",
  "'all_licenses',true",
  "'admin',true",
  "insert into public.internal_admin_users",
  "insert into public.user_entitlements",
  "insert into public.reader_library",
 ]
 compact=re.sub(r'\s+','',sql.lower())
 for marker in required:
  target=re.sub(r'\s+','',marker.lower())
  if target not in compact: errors.append(f'Contrat propriétaire absent: {marker}')

 # Repair function must only allow owner caller (or migration/service context with auth.uid() null).
 m=re.search(r'create\s+or\s+replace\s+function\s+public\.ensure_sinjira_owner_character\(\).*?\$\$.*?\$\$\s*;',sql,re.I|re.S)
 if not m: errors.append('ensure_sinjira_owner_character() introuvable.')
 else:
  block=m.group(0).lower()
  if 'v_caller is not null and v_caller<>v_user' not in re.sub(r'\s+',' ',block):
   errors.append('La réparation AbyssTime ne vérifie plus que l’appelant est le propriétaire.')
  if "where lower(coalesce(u.email,''))='kingtyrano@gmail.com'" not in re.sub(r'\s+',' ',block):
   errors.append('La réparation propriétaire ne cible plus explicitement le compte officiel.')

 # Owner entitlement path must remain server-side and product-independent.
 if "public.is_sinjira_owner(p_user_id)" not in sql:
  errors.append('has_sinjira_product ne conserve plus le bypass propriétaire universel.')

 if errors:
  print(f'ECHEC propriétaire: {len(errors)} problème(s).')
  for e in errors: print('- '+e)
  return 1
 print('OK propriétaire: AbyssTime/Benoit Cantin, personnage Livre II, admin, contenus/jeux/romans/licences et jetons illimités protégés par contrat serveur.')
 return 0

if __name__=='__main__': raise SystemExit(main())
