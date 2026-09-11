#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/admin-users/index.ts'
MAX_USERS_RE = re.compile(r'\bMAX_ADMIN_USERS\s*=\s*1_?000\s*;')

REQUIRED = {
    'POST uniquement': "req.method!=='POST'",
    'admin/JWT/AAL2 explicite': 'requiredAdmin(req)',
    'borne comptes admin': 'perPage:MAX_ADMIN_USERS',
    'réponse privée': "'Cache-Control': 'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma': 'no-cache'",
    'nosniff': "'X-Content-Type-Options': 'nosniff'",
    'no-referrer': "'Referrer-Policy': 'no-referrer'",
    'profil minimal': "select('user_id,pseudo,display_name,avatar_path')",
    'droits projet minimaux': "select('user_id,project_id,access_level,projects(name,slug)')",
    'admins minimaux': "select('user_id')",
    'identité admin requise': 'id:u.id,email:u.email',
    'pseudo nécessaire UI': "pseudo:pmap.get(u.id)?.pseudo||''",
    'nom affiché nécessaire UI': "display_name:pmap.get(u.id)?.display_name||''",
    'avatar nécessaire UI': 'avatar_path:pmap.get(u.id)?.avatar_path||null',
    'rôle admin nécessaire UI': 'is_admin:adminIds.has(u.id)',
    'droits nécessaires UI': 'access:(access||[]).filter((a:any)=>a.user_id===u.id)',
    'MFA explicite': "e?.message==='MFA_REQUIRED'",
    'état MFA fermé': "e?.message==='MFA_STATE_UNAVAILABLE'",
}

FORBIDDEN = {
    'helper JSON générique cacheable': 'return json(',
    'import helper JSON générique': 'corsHeaders, json',
    'auth utilisateur simple': 'requiredUser(req)',
    'service client recréé': 'serviceClient()',
    'accès projet wildcard': "from('project_access').select('*",
    'date de création auth exposée': 'created_at:u.created_at',
    'dernière connexion exposée': 'last_sign_in_at:u.last_sign_in_at',
    'objet auth brut exposé': 'authData.users}',
}


def validate(path: Path) -> list[str]:
    try:
        source = path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'admin-users illisible: {exc}']

    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde admin-users absent: {label}.')
    if not MAX_USERS_RE.search(source):
        errors.append('Garde admin-users absent ou affaibli: liste bornée exactement à 1000 comptes.')

    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde admin-users violé: {label}.')

    auth_pos = source.find('const {service}=await requiredAdmin(req);')
    list_pos = source.find('service.auth.admin.listUsers')
    if auth_pos < 0 or list_pos < 0:
        errors.append('Ordre admin/lecture utilisateurs impossible à vérifier.')
    elif auth_pos > list_pos:
        errors.append('Aucune donnée utilisateur ne doit être lue avant la validation admin/JWT/AAL2.')

    if source.count('return new Response(') != 2:
        errors.append('Une réponse métier contourne privateJson; seuls privateJson et OPTIONS peuvent utiliser directement new Response.')

    if 'return privateJson({ok:true,users});' not in source:
        errors.append('La liste des comptes doit rester explicitement renvoyée via privateJson/no-store.')

    return errors


def self_test() -> None:
    real = EDGE.read_text('utf-8', errors='strict')
    clean = validate(EDGE)
    if clean:
        raise AssertionError('Le fichier réel sain doit passer: ' + ' | '.join(clean))

    cases = {
        'no-store retiré': real.replace("'Cache-Control': 'private, no-store, max-age=0',", '', 1),
        'admin explicite retiré': real.replace('const {service}=await requiredAdmin(req);', 'const user=await requiredUser(req); const service=serviceClient();', 1),
        'POST retiré': real.replace("if(req.method!=='POST')", 'if(false)', 1),
        'borne utilisateurs augmentée': real.replace('MAX_ADMIN_USERS = 1000;', 'MAX_ADMIN_USERS = 5000;', 1),
        'wildcard droits projet': real.replace("select('user_id,project_id,access_level,projects(name,slug)')", "select('*,projects(name,slug)')", 1),
        'date création réintroduite': real.replace('id:u.id,email:u.email,', 'id:u.id,email:u.email,created_at:u.created_at,', 1),
        'dernière connexion réintroduite': real.replace('id:u.id,email:u.email,', 'id:u.id,email:u.email,last_sign_in_at:u.last_sign_in_at,', 1),
        'liste utilisateurs cacheable': real.replace('return privateJson({ok:true,users});', 'return new Response(JSON.stringify({ok:true,users}));', 1),
        'MFA retiré': real.replace("e?.message==='MFA_REQUIRED'", "e?.message==='MFA_BYPASSED'", 1),
    }

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'index.ts'
        for label, mutated in cases.items():
            if mutated == real:
                raise AssertionError(f'Auto-test invalide, mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Affaiblissement non détecté: {label}')
    print(f'OK auto-test admin-users: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la confidentialité et la minimisation des données de admin-users.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC sécurité admin-users: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK admin-users: AAL2 avant lecture, 1000 comptes max, réponses no-store et données minimisées aux besoins de gestion des accès.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
