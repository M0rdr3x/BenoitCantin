#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'
LOBBY=ROOT/'assets'/'js'/'sinjira-fracture-lobby.js'
ENGINE_VERSION='24.4.6'


def latest_block(sql_files,name):
 rx=re.compile(rf'create\s+(?:or\s+replace\s+)?function\s+(?:public\.)?{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;',re.I|re.S)
 for p in reversed(sql_files):
  matches=list(rx.finditer(p.read_text('utf-8',errors='ignore')))
  if matches:return p,matches[-1].group(0)
 return None,''


def main()->int:
 errors=[]
 files=sorted(MIG.glob('*.sql'))
 sql='\n'.join(p.read_text('utf-8',errors='ignore') for p in files)
 lobby=LOBBY.read_text('utf-8',errors='ignore')

 # Frontend must refuse play until both engine and entitlement are verified.
 for marker in ["s.rpc('fracture_engine_health')","s.rpc('has_sinjira_product'","setFormsEnabled(false)","if(access!==true)"]:
  if marker not in lobby: errors.append(f'Lobby Fracture ne contient plus le garde-fou: {marker}')
 if "p_product_slug:'fracture-du-reseau-mere'" not in lobby:
  errors.append('Lobby Fracture ne vérifie plus le produit officiel fracture-du-reseau-mere.')

 # Secret engine tables must remain RLS-enabled and directly revoked from browser roles.
 secret_tables=['fracture_engine_games','fracture_engine_seats','fracture_engine_cards','fracture_engine_actions','fracture_engine_rounds','fracture_engine_votes','fracture_engine_events']
 normalized=re.sub(r'\s+',' ',sql.lower())
 for table in secret_tables:
  if f'alter table public.{table} enable row level security' not in normalized:
   errors.append(f'RLS moteur absente: {table}')
 if 'revoke all on public.fracture_engine_games' not in normalized:
  errors.append('Révocation directe des tables secrètes Fracture absente.')

 # Privacy wrapper: suspicion of another seat must be removed from returned state.
 p,block=latest_block(files,'fracture_engine_get_state')
 if not p:
  errors.append('fracture_engine_get_state introuvable.')
 else:
  compact=re.sub(r'\s+','',block.lower())
  if "elser-'suspect'end" not in compact:
   errors.append(f'Le dernier fracture_engine_get_state ({p.name}) ne masque plus les soupçons des autres joueurs.')

 # Final vote must be immutable after submission.
 p,vote=latest_block(files,'fracture_engine_submit_accusation')
 if not p:
  errors.append('fracture_engine_submit_accusation introuvable.')
 else:
  low=vote.lower()
  if 'already_submitted' not in low:
   errors.append('Le vote final Fracture peut perdre sa protection ALREADY_SUBMITTED.')
  if 'on conflict' in low:
   errors.append('Le vote final utilise encore un UPSERT/ON CONFLICT alors qu’il doit être immuable.')

 # Engine health must be the hardened 24.4.6 definition and test critical RPCs.
 p,health=latest_block(files,'fracture_engine_health')
 if not p:
  errors.append('fracture_engine_health introuvable.')
 else:
  compact=re.sub(r'\s+','',health.lower())
  if f"'engine_version','{ENGINE_VERSION}'" not in compact:
   errors.append(f'Le diagnostic moteur final ({p.name}) n’annonce pas {ENGINE_VERSION}.')
  for rpc in ['create_fracture_party','join_fracture_party','fracture_engine_get_state','fracture_engine_start','fracture_engine_submit_keep','fracture_engine_pick','fracture_engine_submit_report','fracture_engine_submit_accusation']:
   if rpc not in health: errors.append(f'Diagnostic moteur ne vérifie plus la RPC critique: {rpc}')

 if errors:
  print(f'ECHEC Fracture: {len(errors)} problème(s).')
  for e in errors: print('- '+e)
  return 1
 print(f'OK Fracture: moteur {ENGINE_VERSION}, RLS, confidentialité des soupçons, vote final immuable et contrôle de licence vérifiés.')
 return 0

if __name__=='__main__': raise SystemExit(main())
