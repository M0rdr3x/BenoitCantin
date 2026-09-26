#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
FN = ROOT / 'supabase/functions/delete-player-account/index.ts'
CLIENT = ROOT / 'assets/js/v24-data-control.js'
DOC = ROOT / 'DELETE_ACCOUNT_HTTP_HARDENING_V24_5_51.md'
CONFIG = ROOT / 'supabase/config.toml'
MIGRATIONS = ROOT / 'supabase/migrations'


def edge_errors(source: str) -> list[str]:
    errors: list[str] = []
    markers = (
        "req.method !== 'POST'",
        'readBoundedJson',
        "contentType!=='application/json'",
        "const declaredRaw=req.headers.get('content-length');",
        "!/^\\d+$/.test(normalizedLength)",
        '!Number.isSafeInteger(declared)',
        'req.body.getReader()',
        "reader.cancel('REQUEST_TOO_LARGE')",
        'if(total>MAX_REQUEST_BYTES)',
        "new TextDecoder('utf-8',{fatal:true})",
        'JSON_REQUIRED',
        'REQUEST_TOO_LARGE',
        'INVALID_JSON',
        "CONFIRM_PHRASE='SUPPRIMER MON COMPTE'",
        'privacy_service_can_delete_user',
        'OWNER_OR_ADMIN_DELETE_BLOCKED',
        'MFA_REQUIRED',
        'Cache-Control',
        'private, no-store',
        'Pragma',
        'no-cache',
        'X-Content-Type-Options',
        'nosniff',
        'Referrer-Policy',
        'no-referrer',
        'SAFE_FAILURE_CODES',
        "SAFE_FAILURE_CODES.has(error.message)?error.message:'DELETE_FAILED'",
    )
    for marker in markers:
        if marker not in source:
            errors.append(f'Garde-fou V24.5.51 absent: {marker}')

    if not re.search(r'\bMAX_REQUEST_BYTES\s*=\s*1_?024\s*;', source):
        errors.append('La borne de suppression doit rester exactement à 1 024 octets.')

    for forbidden in ('await req.json()', 'await req.text()'):
        if forbidden in source:
            errors.append(f'Lecture applicative non bornée interdite: {forbidden}')

    auth_pos = source.find('const user = await requiredUser(req);')
    body_pos = source.find('const body=await readBoundedJson(req);')
    if auth_pos < 0 or body_pos < 0 or auth_pos > body_pos:
        errors.append('requiredUser/JWT doit précéder toute lecture applicative du corps.')

    mime_pos = source.find("contentType!=='application/json'")
    reader_pos = source.find('req.body.getReader()')
    bound_pos = source.find('if(total>MAX_REQUEST_BYTES)', reader_pos)
    decode_pos = source.find("new TextDecoder('utf-8',{fatal:true})", bound_pos)
    parse_pos = source.find('JSON.parse(raw)', decode_pos)
    if mime_pos < 0 or reader_pos < 0 or mime_pos > reader_pos:
        errors.append('Le MIME JSON exact doit être validé avant la lecture du flux.')
    if reader_pos < 0 or bound_pos < reader_pos or decode_pos < bound_pos or parse_pos < decode_pos:
        errors.append('Le corps doit être borné pendant le flux avant UTF-8 strict puis JSON.parse.')

    console_lines = [line.strip() for line in source.splitlines() if 'console.' in line]
    expected_console_lines = [
        "console.error('[delete-player-account]',{code:'AUTH_DELETE_FAILED'});",
        "console.error('[delete-player-account]',{code:failureCode(error)});",
    ]
    if console_lines != expected_console_lines:
        errors.append('Les logs de suppression doivent rester limités aux codes bornés approuvés, sans objet d’erreur brut.')

    raw_log_markers = (
        "console.error('[delete-player-account]',error)",
        'console.error(`[SINJIRA delete] storage ${bucket}`,error)',
        "console.error('[SINJIRA delete] auth delete',error)",
    )
    for marker in raw_log_markers:
        if marker in source:
            errors.append(f'Log d’erreur brut interdit dans delete-player-account: {marker}')
    return errors


def self_test() -> None:
    source = FN.read_text('utf-8', errors='ignore')
    clean = edge_errors(source)
    if clean:
        raise AssertionError('Le cas sain doit passer: ' + ' | '.join(clean))

    cases = {
        'lecture texte directe': source.replace(
            'const reader=req.body.getReader();',
            'const unsafe=await req.text();\n  const reader=req.body.getReader();',
            1,
        ),
        'MIME par préfixe': source.replace(
            "contentType!=='application/json'",
            "!contentType.startsWith('application/json')",
            1,
        ),
        'Content-Length non numérique accepté': source.replace(
            "if(!/^\\d+$/.test(normalizedLength))throw new Error('REQUEST_TOO_LARGE');\n",
            '',
            1,
        ),
        'entier sûr retiré': source.replace('!Number.isSafeInteger(declared)||', '', 1),
        'annulation retirée': source.replace("await reader.cancel('REQUEST_TOO_LARGE').catch(()=>undefined);", '', 1),
        'borne streaming retirée': source.replace('if(total>MAX_REQUEST_BYTES)', 'if(false)', 1),
        'UTF-8 permissif': source.replace("new TextDecoder('utf-8',{fatal:true})", "new TextDecoder('utf-8')", 1),
        'auth après corps': source.replace(
            'const user = await requiredUser(req);\n    const body=await readBoundedJson(req);',
            'const body=await readBoundedJson(req);\n    const user = await requiredUser(req);',
            1,
        ),
        'log brut': source.replace(
            "console.error('[delete-player-account]',{code:failureCode(error)});",
            "console.error('[delete-player-account]',error);",
            1,
        ),
        'limite augmentée': source.replace('MAX_REQUEST_BYTES=1024', 'MAX_REQUEST_BYTES=10240', 1),
    }
    for label, mutated in cases.items():
        if mutated == source:
            raise AssertionError(f'Mutation sans effet: {label}')
        if not edge_errors(mutated):
            raise AssertionError(f'Affaiblissement non détecté: {label}')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()

    errors: list[str] = []
    for path in (FN, CLIENT, DOC, CONFIG):
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors:
            print('- ' + error)
        return 1

    if args.self_test:
        self_test()
        print('OK auto-tests V24.5.51: affaiblissements critiques de la suppression de compte détectés.')
        return 0

    source = FN.read_text('utf-8', errors='ignore')
    client = CLIENT.read_text('utf-8', errors='ignore')
    doc = DOC.read_text('utf-8', errors='ignore').lower()
    config = tomllib.loads(CONFIG.read_text('utf-8'))
    errors.extend(edge_errors(source))

    for marker in (
        "prompt('Cette action est irréversible. Pour continuer, écrivez exactement : SUPPRIMER MON COMPTE')",
        "phrase!=='SUPPRIMER MON COMPTE'",
        "confirm('Dernière confirmation : supprimer définitivement ce compte SINJIRA™ et ses données personnelles associées?')",
        "functions.invoke('delete-player-account',{body:{confirm:'SUPPRIMER MON COMPTE'}})",
        "async function edgeErrorData(error)",
        "const responseData=error?(await edgeErrorData(error)):(data||null);",
        "if(error&&!responseData)throw error;",
        "if(!responseData?.ok)",
        "OWNER_OR_ADMIN_DELETE_BLOCKED",
        "MFA_REQUIRED",
        "LEGAL_HOLD_ACTIVE",
    ):
        if marker not in client:
            errors.append(f'Contrat client suppression absent: {marker}')
    if "body:{confirm:'SUPPRIMER'}" in client:
        errors.append('Le client ne doit plus envoyer l’ancienne confirmation SUPPRIMER.')

    function_cfg = config.get('functions', {}).get('delete-player-account', {})
    if function_cfg.get('verify_jwt') is not True:
        errors.append('delete-player-account doit conserver verify_jwt=true.')

    if any('24_5_51' in p.name.lower() for p in MIGRATIONS.glob('*.sql')):
        errors.append('V24.5.51 est Edge-only et ne doit pas ajouter de migration Supabase.')

    for marker in (
        'version **4**',
        'verify_jwt=true',
        'aucune migration supabase',
        '174 migrations',
        '1 024 octets',
        'private, no-store',
        'conservation légale',
        'aal2',
        'aucun paiement',
    ):
        if marker not in doc:
            errors.append(f'Document V24.5.51 incomplet: {marker}')

    forbidden = ('stripe', 'paypal', 'twilio', 'api.resend.com', 'shippo', 'easypost')
    for token in forbidden:
        if token in source.lower():
            errors.append(f'Intégration externe interdite dans V24.5.51: {token}')

    if errors:
        print(f'ECHEC V24.5.51 suppression de compte: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK V24.5.51: suppression de compte JWT avant corps, POST JSON 1 KiB borné en streaming, UTF-8 strict, réponses privées no-store, conservation légale/MFA/confirmation conservées, logs bornés, aucune migration ni service payant.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
