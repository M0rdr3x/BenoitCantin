#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/admin-social-v20/index.ts'
LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*8_?192\s*;')

REQUIRED = {
    'POST uniquement': "req.method!=='POST'",
    'admin explicite': 'requiredAdmin(req)',
    'Content-Type JSON explicite': "contentType.startsWith('application/json')",
    'erreur média explicite': "e?.message==='UNSUPPORTED_MEDIA_TYPE'",
    'lecture JSON bornée': 'readLimitedJson(req)',
    'taille UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma':'no-cache'",
    'nosniff': "'X-Content-Type-Options':'nosniff'",
    'no-referrer': "'Referrer-Policy':'no-referrer'",
    'journalisation allowlistée': 'SAFE_LOG_CODES',
    'fallback log backend fixe': "'MODERATION_BACKEND_FAILED'",
    'log notification fixe': "'NOTIFICATION_WRITE_FAILED'",
    'source humaine': "decision_source:'human_admin'",
    'appel humain': "a==='review_appeal'",
    'renversement d’appel': "outcome==='reversed'",
    'raison d’appel bornée': 'reason.length<20||reason.length>4000',
    'MFA fermé': "e?.message==='MFA_STATE_UNAVAILABLE'",
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'helper JSON générique cacheable': 'return json(',
    'import helper JSON générique': "import {corsHeaders,json}",
    'auth admin indirecte': 'requiredUser(req)',
    'service client recréé avant admin': 'serviceClient()',
    'erreur interne renvoyée au client': "error:e?.message",
    'objet erreur notification journalisé': "console.error('[SINJIRA moderation notification]',error)",
    'message erreur notification journalisé': "console.error('[SINJIRA moderation notification]',error.message)",
    'objet erreur global journalisé': "console.error('[admin-social-v20]',e)",
    'message erreur global journalisé': "console.error('[admin-social-v20]',e?.message)",
}


def validate(path: Path) -> list[str]:
    try:
        source = path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'admin-social-v20 illisible: {exc}']

    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde modération absent: {label}.')
    if not LIMIT_RE.search(source):
        errors.append('Garde modération absent ou affaibli: requête exactement bornée à 8192 octets.')
    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde modération violé: {label}.')

    auth_pos = source.find('const {user,service:s}=await requiredAdmin(req)')
    content_type_pos = source.find('requireJsonContentType(req)')
    body_pos = source.find('const b=await readLimitedJson(req)')
    if min(auth_pos, content_type_pos, body_pos) < 0:
        errors.append('Ordre admin/Content-Type/corps impossible à vérifier.')
    elif not (auth_pos < content_type_pos < body_pos):
        errors.append('L’admin/JWT/AAL2 doit être validé avant Content-Type puis lecture du corps.')

    safe_log_pos = source.find("console.error('[admin-social-v20]',moderationLogCode(e))")
    fallback_log_pos = source.find("return SAFE_LOG_CODES.has(code)?code:'MODERATION_BACKEND_FAILED'")
    if safe_log_pos < 0 or fallback_log_pos < 0:
        errors.append('La journalisation globale doit rester sanitizée par allowlist avec fallback fixe.')

    if source.count('reversible:true') != 2:
        errors.append('Les deux mesures de modération actives doivent rester explicitement réversibles.')
    if source.count('privateJson(') < 13:
        errors.append('Les réponses de modération doivent rester uniformément privées et non cachables.')
    return errors


def self_test() -> None:
    real = EDGE.read_text('utf-8', errors='strict')
    clean = validate(EDGE)
    if clean:
        raise AssertionError('Le fichier réel sain doit passer: ' + ' | '.join(clean))

    cases = {
        'json direct': real.replace('const b=await readLimitedJson(req);', 'const b=await req.json();', 1),
        'Content-Type retiré': real.replace('    requireJsonContentType(req);\n', '', 1),
        'Content-Type après corps': real.replace(
            '    requireJsonContentType(req);\n    const b=await readLimitedJson(req);',
            '    const b=await readLimitedJson(req);\n    requireJsonContentType(req);',
            1,
        ),
        'no-store retiré': real.replace("'Cache-Control':'private, no-store, max-age=0',", '', 1),
        'limite affaiblie': real.replace('MAX_REQUEST_BYTES=8192;', 'MAX_REQUEST_BYTES=81920;', 1),
        'admin explicite retiré': real.replace('const {user,service:s}=await requiredAdmin(req);', 'const user=await requiredUser(req),s=serviceClient();', 1),
        'ordre auth inversé': real.replace(
            'const {user,service:s}=await requiredAdmin(req);\n    requireJsonContentType(req);\n    const b=await readLimitedJson(req);',
            'const b=await readLimitedJson(req);\n    const {user,service:s}=await requiredAdmin(req);\n    requireJsonContentType(req);',
            1,
        ),
        'log global brut': real.replace("console.error('[admin-social-v20]',moderationLogCode(e));", "console.error('[admin-social-v20]',e);", 1),
        'log notification brut': real.replace("console.error('[SINJIRA moderation notification]','NOTIFICATION_WRITE_FAILED');", "console.error('[SINJIRA moderation notification]',error);", 1),
        'fallback backend retiré': real.replace("return SAFE_LOG_CODES.has(code)?code:'MODERATION_BACKEND_FAILED';", 'return code;', 1),
        'source humaine retirée': real.replace("decision_source:'human_admin'", "decision_source:'automated'", 1),
        'réversibilité retirée': real.replace('reversible:true', 'reversible:false', 1),
        'appel retiré': real.replace("if(a==='review_appeal')", "if(a==='review_appeal_disabled')", 1),
    }

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'index.ts'
        for label, mutated in cases.items():
            if mutated == real:
                raise AssertionError(f'Auto-test invalide, mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Affaiblissement non détecté: {label}')
    print(f'OK auto-test modération Edge: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide les bornes HTTP, la confidentialité et les logs de admin-social-v20.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC sécurité modération Edge: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK modération Edge: admin/JWT/AAL2 avant corps, JSON 8 KiB, Content-Type explicite, no-store, logs sanitizés et décisions humaines réversibles préservées.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
