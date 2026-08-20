#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'/'20260816149000_sinjira_v24_4_12_parallel_character_convergence.sql'
IDENTITY_MIG=ROOT/'supabase'/'migrations'/'20260820223914_sinjira_v24_4_87_identity_firewall.sql'
CLEANUP_MIG=ROOT/'supabase'/'migrations'/'20260820224027_sinjira_v24_4_88_identity_leak_cleanup.sql'
JS=ROOT/'assets'/'js'/'v24-parallel.js'
HTML=ROOT/'compte'/'monde-parallele.html'
PUBLIC_HTML=ROOT/'projets'/'sinjira'/'monde-parallele'/'index.html'
UI_VERSION='24.4.88'

def compact(value:str)->str:return re.sub(r'\s+','',value.lower())

def main()->int:
    errors=[]
    for path,label in [(MIG,'convergence'),(IDENTITY_MIG,'pare-feu identité'),(CLEANUP_MIG,'nettoyage identité'),(JS,'client'),(HTML,'page compte'),(PUBLIC_HTML,'portail public')]:
        if not path.exists():errors.append(f'{label} Monde parallèle absent: {path.relative_to(ROOT)}')
    if errors:
        for e in errors:print('- '+e)
        return 1

    sql=MIG.read_text('utf-8',errors='ignore');low=compact(sql)
    identity=IDENTITY_MIG.read_text('utf-8',errors='ignore');identity_low=compact(identity)
    cleanup=CLEANUP_MIG.read_text('utf-8',errors='ignore');cleanup_low=compact(cleanup)
    js=JS.read_text('utf-8',errors='ignore');js_low=compact(js)
    html=HTML.read_text('utf-8',errors='ignore');public_html=PUBLIC_HTML.read_text('utf-8',errors='ignore')

    for table in ['fictional_relationships','memorial_records','parallel_character_state','parallel_cycle_responses','parallel_group_members','parallel_story_installments','parallel_world_memberships']:
        if f'altertablepublic.{table}' not in low or 'referencespublic.characters(id)' not in low:
            errors.append(f'{table}: FK canonique vers public.characters non garantie.')

    for marker in [
      'createtableifnotexistsprivate.account_identities',
      'revokeallontableprivate.account_identitiesfromanon,authenticated',
      "account_handle='abysstime'",
      "public_name='sethtremblay'",
      'createorreplacefunctionpublic.parallel_my_context()',
      'createorreplacefunctionpublic.parallel_save_cycle_response',
      "'character_id',v_identity.id",
      'source_character_id'
    ]:
        if marker not in identity_low:errors.append(f'Pare-feu identité absent: {marker}')

    for forbidden in ["'user_id',v_identity.user_id","'source_character_id',v_identity.source_character_id"]:
        if forbidden in identity_low:errors.append(f'RPC Monde parallèle expose un lien interne interdit: {forbidden}')

    if "-'compte_pseudo'" not in cleanup_low:errors.append('Le nettoyage V24.4.88 ne retire pas compte_pseudo de la source personnage.')
    if 'public_description' not in cleanup_low:errors.append('Le nettoyage V24.4.88 ne resynchronise pas la description publique du personnage.')

    for forbidden in [
      ".from('characters')", ".from(\"characters\")",
      ".from('parallel_world_memberships')", ".from('parallel_character_state')",
      ".from('parallel_cycle_responses')", ".from('parallel_story_installments')",
      'ensure_sinjira_owner_character','character.id','user.id'
    ]:
        if forbidden.lower() in js.lower():errors.append(f'Client Monde parallèle contourne le pare-feu serveur: {forbidden}')

    if "s.rpc('parallel_my_context')" not in js:errors.append('Le client ne charge pas son contexte par RPC cloisonné.')
    if "s.rpc('parallel_save_cycle_response'" not in js:errors.append('Le client n’enregistre pas ses réponses par RPC cloisonné.')
    if f"const ui_version='{UI_VERSION}'" not in js_low:errors.append(f'Version client {UI_VERSION} absente.')
    if f'v24-parallel.js?v={UI_VERSION}' not in html:errors.append(f'Cache-busting {UI_VERSION} absent.')
    if f'Univers persistant V{UI_VERSION}' not in html:errors.append(f'Version visible différente de V{UI_VERSION}.')
    if 'identifiant technique privé du compte' not in html.lower():errors.append('La séparation compte/personnage n’est pas expliquée dans l’espace compte.')
    if 'pare-feu d’identité' not in public_html.lower():errors.append('Le pare-feu d’identité n’est pas expliqué sur le portail public.')

    if errors:
        print(f'ECHEC Monde parallèle V{UI_VERSION}: {len(errors)} problème(s).')
        for e in errors:print('- '+e)
        return 1
    print(f'OK Monde parallèle V{UI_VERSION}: compte privé, profil et personnage cloisonnés; aucune clé source lue par le navigateur.')
    return 0

if __name__=='__main__':raise SystemExit(main())
