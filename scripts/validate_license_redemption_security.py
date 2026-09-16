#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/redeem-license-code/index.ts'

REQUIRED = {
    'POST uniquement': "req.method!=='POST'",
    'authentification obligatoire': 'requiredUser(req)',
    'lecture JSON bornée': 'readLimitedJson(req)',
    'MIME JSON normalisé': ".split(';',1)[0].trim().toLowerCase()",
    'MIME JSON exact': "contentType!=='application/json'",
    'Content-Length numérique strict': "!/^\\d+$/.test(normalizedLength)",
    'Content-Length entier sûr': '!Number.isSafeInteger(declaredLength)',
    'lecture par flux': 'req.body?.getReader()',
    'annulation au dépassement': 'reader.cancel()',
    'borne pendant le flux': 'if(total>MAX_REQUEST_BYTES)',
    'UTF-8 strict': "new TextDecoder('utf-8',{fatal:true})",
    'secret serveur du code': "Deno.env.get('SINJIRA_LICENSE_PEPPER')",
    'client serveur': 'serviceClient()',
    'RPC canonique': "s.rpc('redeem_sinjira_activation'",
    'identité imposée par le serveur': 'p_user_id:user.id',
    'log RPC borné': "console.error('[redeem-license-code]',{code:'LICENSE_REDEEM_FAILED'});",
    'log inattendu borné': "console.error('[redeem-license-code]',{code:'LICENSE_UNEXPECTED_ERROR'});",
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'protection MIME': "'X-Content-Type-Options':'nosniff'",
    'référent masqué': "'Referrer-Policy':'no-referrer'",
}

REQUIRED_PATTERNS = {
    'requête bornée exactement à 4096 octets': re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4_?096\s*;'),
    'longueur minimale du code exactement à 12': re.compile(r'\bMIN_CODE_LENGTH\s*=\s*12\s*;'),
    'longueur maximale du code exactement à 80': re.compile(r'\bMAX_CODE_LENGTH\s*=\s*80\s*;'),
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'lecture JSON directe non bornée espacée': 'await req.json (',
    'lecture texte intégrale non bornée': 'await req.text()',
    'MIME JSON par préfixe': "startsWith('application/json')",
    'log erreur RPC brut': "console.error('[redeem-license-code]',error)",
    'log exception brute': "console.error('[redeem-license-code]',e)",
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        source = path.read_text('utf-8', errors='ignore')
    except OSError as exc:
        return [f'Fonction redeem-license-code illisible: {exc}']

    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde licence absent: {label}.')
    for label, pattern in REQUIRED_PATTERNS.items():
        if not pattern.search(source):
            errors.append(f'Garde licence absent ou affaibli: {label}.')
    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde licence violé: {label}.')

    auth_pos = source.find('requiredUser(req)')
    body_pos = source.find('await readLimitedJson(req)')
    if auth_pos < 0 or body_pos < 0 or auth_pos > body_pos:
        errors.append('La licence doit authentifier le compte avant toute lecture du corps applicatif.')

    reader_pos = source.find('req.body?.getReader()')
    bound_pos = source.find('if(total>MAX_REQUEST_BYTES)', reader_pos)
    decode_pos = source.find("new TextDecoder('utf-8',{fatal:true})", bound_pos)
    parse_pos = source.find("JSON.parse(raw||'{}')", decode_pos)
    if reader_pos < 0 or bound_pos < reader_pos or decode_pos < bound_pos or parse_pos < decode_pos:
        errors.append('Le corps licence doit être borné pendant le flux avant décodage UTF-8 strict et parsing JSON.')

    if "body?.action==='health'" in source:
        health_pos = source.find("body?.action==='health'")
        if auth_pos < 0 or auth_pos > health_pos:
            errors.append("L'action health ne doit pas contourner l'authentification.")

    console_lines = [line.strip() for line in source.splitlines() if "console.error('[redeem-license-code]'" in line]
    expected_console_lines = [
        "console.error('[redeem-license-code]',{code:'LICENSE_REDEEM_FAILED'});",
        "console.error('[redeem-license-code]',{code:'LICENSE_UNEXPECTED_ERROR'});",
    ]
    if console_lines != expected_console_lines:
        errors.append('Les logs redeem-license-code doivent rester limités aux deux codes fixes approuvés.')

    return errors


def self_test() -> None:
    source = EDGE.read_text('utf-8', errors='strict')
    clean = validate(EDGE)
    if clean:
        raise AssertionError('Le cas réel sain doit passer: ' + ' | '.join(clean))

    mutations = {
        'req.json direct': source.replace('const reader=req.body?.getReader();', 'const unsafe=await req.json();\n  const reader=req.body?.getReader();', 1),
        'req.text intégral': source.replace('const reader=req.body?.getReader();', 'const unsafe=await req.text();\n  const reader=req.body?.getReader();', 1),
        'MIME JSON par préfixe': source.replace("contentType!=='application/json'", "!contentType.startsWith('application/json')", 1),
        'Content-Length permissif': source.replace("if(!/^\\d+$/.test(normalizedLength)){", 'if(false){', 1),
        'annulation retirée': source.replace('try{await reader.cancel()}catch{/* Le rejet 413 reste prioritaire. */}', '', 1),
        'UTF-8 permissif': source.replace("new TextDecoder('utf-8',{fatal:true})", "new TextDecoder('utf-8')", 1),
        'limite corps augmentée': source.replace('MAX_REQUEST_BYTES=4096;', 'MAX_REQUEST_BYTES=40960;', 1),
        'auth après corps': source.replace('    const user=await requiredUser(req);', '    const early=await readLimitedJson(req);\n    const user=await requiredUser(req);', 1),
        'no-store retiré': source.replace("  'Cache-Control':'private, no-store, max-age=0',\n", '', 1),
        'pepper retiré': source.replace("Deno.env.get('SINJIRA_LICENSE_PEPPER')", "Deno.env.get('UNSAFE_PEPPER')", 1),
        'RPC changée': source.replace("s.rpc('redeem_sinjira_activation'", "s.rpc('unsafe_activation'", 1),
        'log RPC brut': source.replace("console.error('[redeem-license-code]',{code:'LICENSE_REDEEM_FAILED'});", "console.error('[redeem-license-code]',error);", 1),
        'log catch brut': source.replace("console.error('[redeem-license-code]',{code:'LICENSE_UNEXPECTED_ERROR'});", "console.error('[redeem-license-code]',e);", 1),
        'longueur code augmentée': source.replace('MAX_CODE_LENGTH=80;', 'MAX_CODE_LENGTH=8000;', 1),
    }

    with TemporaryDirectory() as raw:
        path = Path(raw) / 'index.ts'
        for label, mutated in mutations.items():
            if mutated == source:
                raise AssertionError(f'Mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Régression non détectée: {label}')

    print(f'OK auto-test activation licence: {len(mutations)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la sécurité de redeem-license-code.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC activation licence: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK activation licence: JWT avant corps, JSON exact 4 KiB borné en streaming, UTF-8 strict, code 12–80, RPC service-only, réponses privées et logs sanitizés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
