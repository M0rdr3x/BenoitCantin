#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'
REPAIR_VERSION='24.4.89'
SOCIAL_RUNTIME_VERSION='24.4.42'
PARALLEL_VERSION='24.4.88'
CURRENT_MIG=ROOT/'supabase/migrations/20260820224802_sinjira_v24_4_89_private_handle_runtime_decoupling.sql'


def compact(value:str)->str:return re.sub(r'\s+','',value.lower())

def version_tuple(value:str)->tuple[int,...]:
    parts=[]
    for token in str(value).split('.'):
        m=re.match(r'\d+',token)
        if not m:return ()
        parts.append(int(m.group(0)))
    return tuple(parts)

def version_at_least(value:str,minimum:str)->bool:
    current=version_tuple(value);floor=version_tuple(minimum)
    if not current or not floor:return False
    width=max(len(current),len(floor))
    return current+(0,)*(width-len(current))>=floor+(0,)*(width-len(floor))

def asset_version(html:str,asset_name:str)->str|None:
    m=re.search(rf'{re.escape(asset_name)}\?v=([0-9]+(?:\.[0-9]+)+)',html,re.I)
    return m.group(1) if m else None

def latest_function(files:list[Path],name:str)->tuple[Path|None,str]:
    rx=re.compile(rf'create\s+(?:or\s+replace\s+)?function\s+(?:public\.)?{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;',re.I|re.S)
    for path in reversed(files):
        matches=list(rx.finditer(path.read_text('utf-8',errors='ignore')))
        if matches:return path,matches[-1].group(0)
    return None,''


def main()->int:
    errors=[];files=sorted(MIG.glob('*.sql'))
    if not CURRENT_MIG.exists():errors.append('Migration V24.4.89 de cloisonnement absente.')
    else:
        low=compact(CURRENT_MIG.read_text('utf-8',errors='ignore'))
        for marker in [
          'createtableifnotexistsprivate.account_identities',
          'revokeallontableprivate.account_identitiesfromanon,authenticated',
          "values(v_user,'benoitcantin','benoitcantin')",
          "public_name='sethtremblay'",
          'novel_id=null','novel_note=null',
          "'identity_scope','parallel_world'",
          "'sin-'||upper(replace(v_user::text,'-',''))",
        ]:
            if marker not in low:errors.append(f'Pare-feu propriétaire incomplet: {marker}')

    repair_path,repair=latest_function(files,'ensure_sinjira_owner_character')
    if not repair_path:errors.append('ensure_sinjira_owner_character() introuvable.')
    else:
        block=compact(repair)
        for marker in [
          'frompublic.internal_admin_usersa',"a.role='owner'",
          'insertintoprivate.account_identities',
          "'benoitcantin'","'sethtremblay'",
          'novel_id=null','novel_note=null',
          'insertintopublic.character_social_profiles','insertintoprivate.parallel_identities',
          'insertintopublic.parallel_character_state','insertintopublic.parallel_world_memberships',
          'insertintopublic.user_entitlements','insertintopublic.reader_library','insertintopublic.project_access',
          f"'repair_version','{REPAIR_VERSION}'"
        ]:
            if compact(marker) not in block:errors.append(f'{repair_path.name}: réparation propriétaire incomplète: {marker}')

    health_path,health=latest_function(files,'sinjira_owner_character_health')
    if not health_path:errors.append('sinjira_owner_character_health() introuvable.')
    else:
        block=compact(health)
        for marker in [
          f"'repair_version','{REPAIR_VERSION}'",
          "'private_account_identity',v_account",
          "public_name='sethtremblay'",
          'fromprivate.account_identitieswhereuser_id=v_user'
        ]:
            if compact(marker) not in block:errors.append(f'{health_path.name}: diagnostic propriétaire incomplet: {marker}')

    for rel in ['assets/js/sinjira-mon-personnage.js','assets/js/sinjira-community-character.js','assets/js/sinjira-messages-character.js']:
        path=ROOT/rel
        if not path.exists():errors.append(f'Interface propriétaire absente: {rel}')
        elif 'ensure_sinjira_owner_character' not in path.read_text('utf-8',errors='ignore'):errors.append(f'{rel}: réparation propriétaire absente.')

    parallel=ROOT/'assets/js/v24-parallel.js'
    if not parallel.exists():errors.append('Client Monde parallèle absent.')
    else:
        text=parallel.read_text('utf-8',errors='ignore')
        if 'ensure_sinjira_owner_character' in text or ".from('characters')" in text:
            errors.append('Le client Monde parallèle reçoit encore une identité source du Registre.')
        if "s.rpc('parallel_my_context')" not in text:
            errors.append('Le client Monde parallèle ne passe pas par le contexte cloisonné.')

    critical_pages={
      ROOT/'compte/mon-personnage.html':('sinjira-mon-personnage.js','24.4.85'),
      ROOT/'compte/reseau-personnage.html':('sinjira-community-character.js',SOCIAL_RUNTIME_VERSION),
      ROOT/'compte/messages-personnage.html':('sinjira-messages-character.js','24.4.20'),
      ROOT/'compte/monde-parallele.html':('v24-parallel.js',PARALLEL_VERSION),
    }
    for path,(asset,minimum) in critical_pages.items():
        if not path.exists():errors.append(f'Page absente: {path.relative_to(ROOT)}');continue
        loaded=asset_version(path.read_text('utf-8',errors='ignore'),asset)
        if loaded is None:errors.append(f'{path.relative_to(ROOT)}: version de {asset} absente.')
        elif not version_at_least(loaded,minimum):errors.append(f'{path.relative_to(ROOT)}: {asset} v{loaded} antérieur au minimum {minimum}.')

    if errors:
        print(f'ECHEC propriétaire: {len(errors)} problème(s).')
        for e in errors:print('- '+e)
        return 1
    print('OK propriétaire: identifiant compte privé, profil affiché et personnage séparés; aucun identifiant privé spécifique n’est requis par le runtime versionné.')
    return 0

if __name__=='__main__':raise SystemExit(main())
