#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/admin-console/index.ts'
LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*32_?768\s*;')

REQUIRED = {
    'POST uniquement': "req.method!=='POST'",
    'admin explicite': 'requiredAdmin(req)',
    'JSON strict': "contentType!=='application/json'",
    'lecture bornée': 'readBoundedJson(req)',
    'taille UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'Content-Length fini': '!Number.isFinite(declared)||declared<0||declared>MAX_REQUEST_BYTES',
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma':'no-cache'",
    'nosniff': "'X-Content-Type-Options':'nosniff'",
    'no-referrer': "'Referrer-Policy':'no-referrer'",
    'logs allowlistés': 'SAFE_LOG_CODES',
    'fallback log fixe': "'ADMIN_CONSOLE_BACKEND_FAILED'",
    'état playtest précédent': 'const previousReview={status:row.status,reviewed_by:row.reviewed_by??null,reviewed_at:row.reviewed_at??null}',
    'erreur octroi tester capturée': 'const {error:grantError}=await service.from(\'project_access\').upsert',
    'échec octroi contrôlé': 'if(grantError){',
    'rollback participant': "const {error:rollbackError}=await service.from('playtest_participants').update(previousReview)",
    'échec rollback contrôlé': "if(rollbackError)throw new Error('PLAYTEST_REVIEW_ROLLBACK_FAILED')",
    'échec octroi explicite': "throw new Error('PLAYTEST_ACCESS_GRANT_FAILED')",
    'réponse octroi fixe': "e?.message==='PLAYTEST_ACCESS_GRANT_FAILED'",
    'réponse rollback fixe': "e?.message==='PLAYTEST_REVIEW_ROLLBACK_FAILED'",
}

FORBIDDEN = {
    'JSON direct non borné': 'await req.json()',
    'auth admin indirecte': 'requiredUser(req)',
    'service client recréé': 'serviceClient()',
    'log backend brut': "console.error('[admin-console]',e)",
    'log message backend brut': "console.error('[admin-console]',e?.message)",
}


def validate(path: Path) -> list[str]:
    try:
        source = path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'admin-console illisible: {exc}']

    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde admin-console absent: {label}.')
    if not LIMIT_RE.search(source):
        errors.append('Garde admin-console absent ou affaibli: requête exactement bornée à 32768 octets.')

    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde admin-console violé: {label}.')

    auth_pos = source.find('const {user,service}=await requiredAdmin(req)')
    body_pos = source.find('const body=await readBoundedJson(req)')
    if auth_pos < 0 or body_pos < 0:
        errors.append('Ordre admin/corps impossible à vérifier.')
    elif auth_pos > body_pos:
        errors.append('Le corps admin-console ne doit pas être lu avant admin/JWT/AAL2.')

    review_start = source.find("if(action==='review_playtest_participant')")
    state_save = source.find('const previousReview=', review_start)
    status_update = source.find("service.from('playtest_participants').update({", review_start)
    grant = source.find("const {error:grantError}=await service.from('project_access').upsert", review_start)
    grant_check = source.find('if(grantError){', review_start)
    rollback = source.find("const {error:rollbackError}=await service.from('playtest_participants').update(previousReview)", review_start)
    rollback_check = source.find("if(rollbackError)throw new Error('PLAYTEST_REVIEW_ROLLBACK_FAILED')", review_start)
    grant_fail = source.find("throw new Error('PLAYTEST_ACCESS_GRANT_FAILED')", review_start)
    if min(review_start, state_save, status_update, grant, grant_check, rollback, rollback_check, grant_fail) < 0:
        errors.append('Séquence de cohérence Playtest impossible à vérifier.')
    elif not (review_start < state_save < status_update < grant < grant_check < rollback < rollback_check < grant_fail):
        errors.append('La révision Playtest doit mémoriser l’état, mettre à jour, tenter l’accès, puis restaurer avant de signaler l’échec.')

    log_pos = source.find("console.error('[admin-console]',adminConsoleLogCode(e))")
    fallback_pos = source.find("return SAFE_LOG_CODES.has(code)?code:'ADMIN_CONSOLE_BACKEND_FAILED'")
    if log_pos < 0 or fallback_pos < 0:
        errors.append('Les logs admin-console doivent rester sanitizés par allowlist avec fallback fixe.')
    return errors


def self_test() -> None:
    real = EDGE.read_text('utf-8', errors='strict')
    clean = validate(EDGE)
    if clean:
        raise AssertionError('Le fichier réel sain doit passer: ' + ' | '.join(clean))

    cases = {
        'limite augmentée': real.replace('MAX_REQUEST_BYTES=32768;', 'MAX_REQUEST_BYTES=131072;', 1),
        'Content-Length permissif': real.replace(
            'if(!Number.isFinite(declared)||declared<0||declared>MAX_REQUEST_BYTES)throw new Error(\'REQUEST_TOO_LARGE\');',
            'if(Number.isFinite(declared)&&declared>MAX_REQUEST_BYTES)throw new Error(\'REQUEST_TOO_LARGE\');',
            1,
        ),
        'admin après corps': real.replace(
            'const {user,service}=await requiredAdmin(req);\n    const body=await readBoundedJson(req)',
            'const body=await readBoundedJson(req)\n    const {user,service}=await requiredAdmin(req);',
            1,
        ),
        'no-store retiré': real.replace("'Cache-Control':'private, no-store, max-age=0',", '', 1),
        'log backend brut': real.replace("console.error('[admin-console]',adminConsoleLogCode(e));", "console.error('[admin-console]',e);", 1),
        'état précédent retiré': real.replace('const previousReview={status:row.status,reviewed_by:row.reviewed_by??null,reviewed_at:row.reviewed_at??null};', '', 1),
        'erreur octroi ignorée': real.replace("const {error:grantError}=await service.from('project_access').upsert", "await service.from('project_access').upsert", 1),
        'contrôle octroi retiré': real.replace('if(grantError){', 'if(false){', 1),
        'rollback retiré': real.replace("const {error:rollbackError}=await service.from('playtest_participants').update(previousReview)", "const rollbackError=null; await service.from('playtest_participants').update({})", 1),
        'contrôle rollback retiré': real.replace("if(rollbackError)throw new Error('PLAYTEST_REVIEW_ROLLBACK_FAILED');", '', 1),
        'erreur octroi masquée': real.replace("throw new Error('PLAYTEST_ACCESS_GRANT_FAILED');", 'return privateJson({ok:true});', 1),
        'fallback log retiré': real.replace("return SAFE_LOG_CODES.has(code)?code:'ADMIN_CONSOLE_BACKEND_FAILED';", 'return code;', 1),
    }

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'index.ts'
        for label, mutated in cases.items():
            if mutated == real:
                raise AssertionError(f'Auto-test invalide, mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Affaiblissement non détecté: {label}')
    print(f'OK auto-test admin-console: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la frontière HTTP, les logs et la cohérence des décisions Playtest de admin-console.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC sécurité admin-console: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK admin-console: AAL2 avant corps, JSON 32 KiB, logs sanitizés et approbation Playtest avec rollback de cohérence.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
