#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'
OWNER='kingtyrano@gmail.com'
REPAIR_VERSION='24.4.20'


def compact(value:str)->str:
 return re.sub(r'\s+','',value.lower())


def latest_function(files:list[Path],name:str)->tuple[Path|None,str]:
 rx=re.compile(
  rf'create\s+(?:or\s+replace\s+)?function\s+(?:public\.)?{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;',
  re.I|re.S,
 )
 for path in reversed(files):
  matches=list(rx.finditer(path.read_text('utf-8',errors='ignore')))
  if matches:return path,matches[-1].group(0)
 return None,''


def main()->int:
 errors=[]
 files=sorted(MIG.glob('*.sql'))
 sql='\n'.join(p.read_text('utf-8',errors='ignore') for p in files)
 all_compact=compact(sql)

 # Contrat propriétaire global : l'accès illimité et les privilèges ne doivent
 # pas dépendre d'une licence individuelle ou d'un produit particulier.
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
 for marker in required:
  if compact(marker) not in all_compact:
   errors.append(f'Contrat propriétaire absent: {marker}')

 # On valide la DERNIÈRE définition de la réparation, pas une ancienne version
 # encore présente dans l'historique des migrations.
 repair_path,repair=latest_function(files,'ensure_sinjira_owner_character')
 if not repair_path:
  errors.append('ensure_sinjira_owner_character() introuvable.')
 else:
  block=compact(repair)
  repair_markers=[
   OWNER,
   'v_callerisnotnull',
   'v_caller<>v_user',
   "coalesce(auth.jwt()->>'role','')<>'service_role'",
   'insertintopublic.character_social_profiles',
   'insertintopublic.parallel_character_state',
   'insertintopublic.parallel_world_memberships',
   'main_canon_eligible=true',
   'parallel_world_only=false',
   'insertintopublic.user_entitlements',
   'insertintopublic.reader_library',
   'insertintopublic.project_access',
   f"'repair_version','{REPAIR_VERSION}'",
   "'social_profile',v_social_ok",
   "'parallel_state',v_parallel_state_ok",
   "'parallel_membership',v_parallel_membership_ok",
  ]
  for marker in repair_markers:
   if compact(marker) not in block:
    errors.append(f'{repair_path.name}: réparation propriétaire incomplète: {marker}')

 health_path,health=latest_function(files,'sinjira_owner_character_health')
 if not health_path:
  errors.append('sinjira_owner_character_health() introuvable.')
 else:
  health_block=compact(health)
  for marker in (
   f"'repair_version','{REPAIR_VERSION}'",
   "'visible_active_rows',v_visible",
   "'social_profile',v_social",
   "'parallel_state',v_state",
   "'parallel_membership',v_membership",
  ):
   if compact(marker) not in health_block:
    errors.append(f'{health_path.name}: diagnostic personnage propriétaire incomplet: {marker}')

 # Le chemin d'accès universel propriétaire doit rester côté serveur.
 if 'public.is_sinjira_owner(p_user_id)' not in sql:
  errors.append('has_sinjira_product ne conserve plus le bypass propriétaire universel.')

 # Les trois interfaces qui dépendent directement du personnage doivent appeler
 # la réparation actuelle et utiliser un cache-buster récent.
 frontend_checks={
  ROOT/'assets/js/sinjira-mon-personnage.js':('ensure_sinjira_owner_character',REPAIR_VERSION),
  ROOT/'assets/js/sinjira-community-character.js':('ensure_sinjira_owner_character',REPAIR_VERSION),
  ROOT/'assets/js/sinjira-messages-character.js':('ensure_sinjira_owner_character',REPAIR_VERSION),
 }
 for path,markers in frontend_checks.items():
  if not path.exists():
   errors.append(f'Interface propriétaire absente: {path.relative_to(ROOT)}')
   continue
  text=path.read_text('utf-8',errors='ignore')
  for marker in markers:
   if marker not in text:
    errors.append(f'{path.relative_to(ROOT)}: marqueur propriétaire absent: {marker}')

 critical_pages=(
  ROOT/'compte/mon-personnage.html',
  ROOT/'compte/reseau-personnage.html',
  ROOT/'compte/messages-personnage.html',
  ROOT/'compte/monde-parallele.html',
 )
 for path in critical_pages:
  if not path.exists():
   errors.append(f'Page personnage absente: {path.relative_to(ROOT)}')
   continue
  if f'v={REPAIR_VERSION}' not in path.read_text('utf-8',errors='ignore'):
   errors.append(f'{path.relative_to(ROOT)}: cache-buster antérieur à {REPAIR_VERSION}.')

 community=(ROOT/'assets/js/sinjira-community-character.js')
 if community.exists() and 'V24.3.1' in community.read_text('utf-8',errors='ignore'):
  errors.append('Le Réseau personnage affiche encore une consigne de migration V24.3.1 obsolète.')

 if errors:
  print(f'ECHEC propriétaire: {len(errors)} problème(s).')
  for error in errors:print('- '+error)
  return 1

 print(
  'OK propriétaire: AbyssTime est protégé par le contrat serveur, visible, '
  'auto-réparable dans Mon personnage/Réseau/Messages/Monde parallèle, avec '
  f'accès universel et diagnostic {REPAIR_VERSION}.'
 )
 return 0


if __name__=='__main__':raise SystemExit(main())
