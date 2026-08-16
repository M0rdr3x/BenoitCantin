#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'
LOBBY=ROOT/'assets'/'js'/'sinjira-fracture-lobby.js'
ENGINE=ROOT/'assets'/'js'/'sinjira-fracture-engine.js'
ENGINE_CSS=ROOT/'assets'/'css'/'fracture-engine.css'
PARTY_HTML=ROOT/'projets'/'sinjira'/'jeux'/'fracture-du-reseau-mere'/'partie.html'
CARD_BACK=ROOT/'assets'/'media'/'fracture-card-back.webp'
GATEWAY=ROOT/'supabase'/'functions'/'fracture-engine-gateway'/'index.ts'
REPORT_FUNCTION=ROOT/'supabase'/'functions'/'send-game-report'/'index.ts'
CONFIG=ROOT/'supabase'/'config.toml'
ENGINE_VERSION='24.4.6'
UI_VERSION='24.4.15'
PRIVACY_VERSION='24.4.15'


def latest_block(sql_files,name):
 rx=re.compile(rf'create\s+(?:or\s+replace\s+)?function\s+(?:public\.)?{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;',re.I|re.S)
 for p in reversed(sql_files):
  matches=list(rx.finditer(p.read_text('utf-8',errors='ignore')))
  if matches:return p,matches[-1].group(0)
 return None,''


def read(path):
 return path.read_text('utf-8',errors='ignore') if path.exists() else ''


def main()->int:
 errors=[]
 files=sorted(MIG.glob('*.sql'))
 sql='\n'.join(p.read_text('utf-8',errors='ignore') for p in files)
 lobby=read(LOBBY)
 engine=read(ENGINE)
 css=read(ENGINE_CSS)
 party=read(PARTY_HTML)
 gateway=read(GATEWAY)
 report_fn=read(REPORT_FUNCTION)
 config=read(CONFIG)

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

 # Original privacy wrapper: suspicion of another seat must be removed from returned state.
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

 # V24.4.15 visual / information contract.
 if not ENGINE.exists():
  errors.append('Interface moteur Fracture absente.')
 else:
  compact_engine=re.sub(r'\s+','',engine)
  for marker in ["label:'Résistance'","label:'Réseau-Mère'",'functionidentityHtml(','engine-card__faction','engine-card__points']:
   if marker not in compact_engine:
    errors.append(f'Interface Fracture V{UI_VERSION} incomplète: {marker}')
  if 'revealAll?seat.identity:null' not in compact_engine:
   errors.append('Défense visuelle: l’identité des autres sièges pourrait être affichée avant la fin.')
  if 'seatsHtml(state,{revealAll:true})' not in compact_engine:
   errors.append('La révélation finale des identités n’est plus explicite.')
  for marker in ['fracture_engine_get_state_safe','fracture_engine_privacy_health','fracture-engine-gateway']:
   if marker not in engine:
    errors.append(f'Frontend Fracture ne passe plus par la couche privée: {marker}')
  if "rpc('fracture_engine_get_state'" in engine or 'getSupabase().rpc(name,args)' in engine:
   errors.append('Le navigateur appelle encore directement une RPC d’état/action sensible Fracture.')

 if 'fracture-card-back.webp' not in css:
  errors.append('Le CSS Fracture n’utilise pas le dos de carte officiel.')
 if 'engine-identity--r' not in css or 'engine-identity--rm' not in css:
  errors.append('Les deux identités n’ont plus de présentation visuelle distincte.')
 if f'v={UI_VERSION}' not in party or f'V{UI_VERSION}' not in party:
  errors.append(f'partie.html n’annonce pas correctement l’interface V{UI_VERSION}.')

 if not CARD_BACK.exists():
  errors.append('Dos de carte officiel Fracture absent.')
 else:
  raw=CARD_BACK.read_bytes()
  if len(raw)<20000:
   errors.append('Dos de carte officiel anormalement petit / possiblement corrompu.')
  if len(raw)<12 or raw[:4]!=b'RIFF' or raw[8:12]!=b'WEBP':
   errors.append('Dos de carte officiel n’est pas un WebP valide.')

 # Server privacy boundary: safe state RPC + Edge gateway.
 for fn in ['fracture_engine_sanitize_state','fracture_engine_get_state_safe','fracture_engine_privacy_health']:
  p,_=latest_block(files,fn)
  if not p: errors.append(f'Couche de confidentialité Fracture absente: {fn}')
 if f"'privacy_version','{PRIVACY_VERSION}'" not in re.sub(r'\s+','',sql.lower()):
  errors.append(f'La migration de confidentialité n’annonce pas {PRIVACY_VERSION}.')
 if not gateway:
  errors.append('Edge Function fracture-engine-gateway absente.')
 else:
  for marker in ["GATEWAY_VERSION='24.4.15'",'fracture_engine_get_state_safe','ALLOWED_ACTIONS','client.auth.getUser(token)']:
   if marker not in gateway: errors.append(f'Gateway Fracture incomplet: {marker}')
 if '[functions.fracture-engine-gateway]' not in config:
  errors.append('supabase/config.toml ne déclare pas fracture-engine-gateway.')
 else:
  stanza=config.split('[functions.fracture-engine-gateway]',1)[1].split('[functions.',1)[0]
  if 'verify_jwt = true' not in stanza:
   errors.append('supabase/config.toml ne protège pas fracture-engine-gateway avec verify_jwt=true.')

 # Report delivery hardening: no caller-selected email relay.
 if not report_fn:
  errors.append('send-game-report Edge Function absente.')
 else:
  compact_report=re.sub(r'\s+','',report_fn)
  if "FUNCTION_VERSION='24.4.15'" not in report_fn:
   errors.append('send-game-report n’est pas la version durcie 24.4.15.')
  if 'body?.email' in report_fn or 'body.email' in report_fn:
   errors.append('send-game-report accepte encore une adresse courriel fournie par le navigateur.')
  if 'if(!user?.email)' not in compact_report or 'to:[user.email]' not in compact_report:
   errors.append('send-game-report ne verrouille pas le destinataire sur le compte authentifié.')

 if errors:
  print(f'ECHEC Fracture: {len(errors)} problème(s).')
  for e in errors: print('- '+e)
  return 1
 print(f'OK Fracture: moteur {ENGINE_VERSION}, interface {UI_VERSION}, dos officiel, factions lisibles, identité privée, passerelle d’action, état serveur assaini, RLS, confidentialité des soupçons, vote final immuable et contrôle de licence vérifiés.')
 return 0

if __name__=='__main__': raise SystemExit(main())
