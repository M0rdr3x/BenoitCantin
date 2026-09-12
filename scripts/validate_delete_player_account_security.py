#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/delete-player-account/index.ts'
CONFIG = ROOT / 'supabase/config.toml'

REQUIRED = {
    'POST uniquement': "req.method !== 'POST'",
    'auth commune': 'await requiredUser(req)',
    'confirmation humaine': "const CONFIRM_PHRASE='SUPPRIMER MON COMPTE';",
    'confirmation vérifiée': 'body.confirm !== CONFIRM_PHRASE',
    'JSON explicite': "contentType!=='application/json'",
    'lecture corps texte': 'const raw=await req.text();',
    'mesure UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES',
    'taille bornée': 'const MAX_REQUEST_BYTES=1024;',
    'legal hold': "service.rpc('privacy_service_can_delete_user'",
    'MFA': 'service.auth.mfa.getAuthenticatorAssuranceLevel(token)',
    'AAL2': "aal.nextLevel==='aal2'&&aal.currentLevel!=='aal2'",
    'suppression utilisateur': 'service.auth.admin.deleteUser(user.id)',
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma':'no-cache'",
    'protection MIME': "'X-Content-Type-Options':'nosniff'",
    'référent masqué': "'Referrer-Policy':'no-referrer'",
    'codes log bornés': 'const SAFE_FAILURE_CODES=new Set([',
    'normalisation log': "SAFE_FAILURE_CODES.has(error.message)?error.message:'DELETE_FAILED'",
}

FORBIDDEN = {
    'JSON direct non borné': 'await req.json()',
    'service role direct': 'SUPABASE_SERVICE_ROLE_KEY',
    'log objet erreur brut': "console.error('[delete-player-account]',error)",
    'log stockage brut': 'console.error(`[SINJIRA delete] storage ${bucket}`,error)',
    'log auth brut': "console.error('[SINJIRA delete] auth delete',error)",
    'console.log': 'console.log(',
    'console.warn': 'console.warn(',
}

EXPECTED_CONSOLE_LINES = [
    "console.error('[delete-player-account]',{code:'AUTH_DELETE_FAILED'});",
    "console.error('[delete-player-account]',{code:failureCode(error)});",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def config_stanza(config: str) -> str:
    marker = '[functions.delete-player-account]'
    if marker not in config:
        return ''
    return config.split(marker, 1)[1].split('[functions.', 1)[0]


def validate_text(source: str, config: str) -> list[str]:
    errors: list[str] = []

    for label, marker in REQUIRED.items():
        require(errors, marker in source, f'Garde delete-player-account absent: {label}.')
    for label, marker in FORBIDDEN.items():
        require(errors, marker not in source, f'Garde delete-player-account violé: {label}.')

    auth_pos = source.find('await requiredUser(req)')
    parse_pos = source.find('await readBoundedJson(req)')
    confirm_pos = source.find('body.confirm !== CONFIRM_PHRASE')
    service_pos = source.find('const service = serviceClient();')
    hold_pos = source.find("service.rpc('privacy_service_can_delete_user'")
    mfa_pos = source.find('service.auth.mfa.getAuthenticatorAssuranceLevel(token)')
    storage_lookup_pos = source.find("service.from('profiles')")
    storage_delete_pos = source.find("await removeStoragePaths(service,'sinjira-avatars'")
    revoke_pos = source.find("service.rpc('revoke_sinjira_contributions'")
    auth_delete_pos = source.find('service.auth.admin.deleteUser(user.id)')

    require(errors, 0 <= auth_pos < parse_pos < confirm_pos < service_pos,
            'Auth, parsing borné, confirmation humaine puis client service doivent rester dans cet ordre.')
    require(errors, service_pos < hold_pos < mfa_pos,
            'Le legal hold doit être vérifié avant le contrôle MFA et toute suppression.')
    require(errors, mfa_pos < storage_lookup_pos < storage_delete_pos < revoke_pos < auth_delete_pos,
            'Aucune lecture/suppression sensible ne doit précéder le contrôle MFA; la suppression Auth doit rester finale.')

    raw_pos = source.find('const raw=await req.text();')
    utf8_pos = source.find('new TextEncoder().encode(raw).byteLength>MAX_REQUEST_BYTES')
    parse_json_pos = source.find('JSON.parse(raw)')
    require(errors, 0 <= raw_pos < utf8_pos < parse_json_pos,
            'Le corps doit être mesuré en octets UTF-8 avant JSON.parse.')

    console_lines = [line.strip() for line in source.splitlines() if 'console.' in line]
    require(errors, console_lines == EXPECTED_CONSOLE_LINES,
            'Les logs delete-player-account doivent rester limités aux codes bornés approuvés.')

    for code in (
        "'ADMIN_CHECK_FAILED'",
        "'LEGAL_HOLD_CHECK_FAILED'",
        "'STORAGE_DELETE_FAILED'",
        "'STORAGE_PATH_LOOKUP_FAILED'",
        "'CONTRIBUTION_REVOKE_FAILED'",
    ):
        require(errors, code in source, f'Code d’échec interne manquant dans la liste bornée: {code}.')

    stanza = config_stanza(config)
    require(errors, bool(stanza), 'Stanza [functions.delete-player-account] absente de supabase/config.toml.')
    require(errors, 'verify_jwt = true' in stanza, 'delete-player-account doit conserver verify_jwt=true.')
    require(errors, 'verify_jwt = false' not in stanza, 'verify_jwt=false interdit pour delete-player-account.')

    return errors


def validate(edge_path: Path = EDGE, config_path: Path = CONFIG) -> list[str]:
    try:
        source = edge_path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'delete-player-account illisible: {exc}']
    try:
        config = config_path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'supabase/config.toml illisible: {exc}']
    return validate_text(source, config)


def self_test() -> None:
    source = EDGE.read_text('utf-8', errors='strict')
    config = CONFIG.read_text('utf-8', errors='strict')
    clean = validate_text(source, config)
    if clean:
        raise AssertionError('Le cas réel sain doit passer: ' + ' | '.join(clean))

    source_mutations = {
        'auth retirée': source.replace('await requiredUser(req)', 'Promise.resolve({id:"bypass"})', 1),
        'POST affaibli': source.replace("req.method !== 'POST'", "req.method !== 'GET'", 1),
        'confirmation retirée': source.replace('body.confirm !== CONFIRM_PHRASE', 'false', 1),
        'limite augmentée': source.replace('MAX_REQUEST_BYTES=1024', 'MAX_REQUEST_BYTES=1048576', 1),
        'JSON direct': source.replace('const raw=await req.text();', 'const raw=JSON.stringify(await req.json());', 1),
        'legal hold retiré': source.replace("service.rpc('privacy_service_can_delete_user'", "service.rpc('privacy_service_can_delete_user_DISABLED'", 1),
        'MFA retiré': source.replace('service.auth.mfa.getAuthenticatorAssuranceLevel(token)', 'Promise.resolve({data:null,error:null})', 1),
        'AAL2 retiré': source.replace("aal.nextLevel==='aal2'&&aal.currentLevel!=='aal2'", 'false', 1),
        'suppression auth avancée': source.replace(
            "    const [profileRes,submissionRes,applicationRes]=await Promise.all([",
            "    await service.auth.admin.deleteUser(user.id);\n    const [profileRes,submissionRes,applicationRes]=await Promise.all([",
            1,
        ),
        'log brut global': source.replace(
            "console.error('[delete-player-account]',{code:failureCode(error)});",
            "console.error('[delete-player-account]',error);",
            1,
        ),
        'log brut auth': source.replace(
            "console.error('[delete-player-account]',{code:'AUTH_DELETE_FAILED'});",
            "console.error('[SINJIRA delete] auth delete',error);",
            1,
        ),
    }
    for name, mutated in source_mutations.items():
        if mutated == source:
            raise AssertionError(f'Mutation sans effet: {name}')
        errors = validate_text(mutated, config)
        if not errors:
            raise AssertionError(f'Mutation non détectée: {name}')

    weak_config = config.replace(
        '[functions.delete-player-account]\nverify_jwt = true',
        '[functions.delete-player-account]\nverify_jwt = false',
        1,
    )
    if weak_config == config:
        raise AssertionError('Mutation config sans effet')
    if not validate_text(source, weak_config):
        raise AssertionError('verify_jwt=false non détecté')

    print(f'OK auto-tests delete-player-account: {len(source_mutations) + 1} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    errors = validate()
    if errors:
        for error in errors:
            print(f'ERREUR sécurité delete-player-account: {error}')
        return 1
    print('OK sécurité delete-player-account: auth, confirmation, legal hold, MFA, ordre destructif, logs bornés et JWT verrouillés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
