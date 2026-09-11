#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
USERS = ROOT / 'supabase/functions/admin-users/index.ts'
ANALYTICS = ROOT / 'supabase/functions/admin-analytics/index.ts'
USERS_LIMIT_RE = re.compile(r'\bMAX_ADMIN_USERS\s*=\s*1000\s*;')
ANALYTICS_LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4_?096\s*;')

COMMON_PRIVATE = [
    "'Cache-Control': 'private, no-store, max-age=0'",
    "'Pragma': 'no-cache'",
    "'X-Content-Type-Options': 'nosniff'",
    "'Referrer-Policy': 'no-referrer'",
]


def validate_users(source: str) -> list[str]:
    errors: list[str] = []
    required = {
        'POST uniquement': "req.method!=='POST'",
        'admin explicite': 'requiredAdmin(req)',
        'pagination auth bornée': 'perPage:MAX_ADMIN_USERS',
        'erreur Auth vérifiée': 'if(authError) throw authError',
        'erreurs secondaires vérifiées': 'if(profileError||accessError||adminsError) throw profileError||accessError||adminsError',
        'allowlist logs': 'SAFE_LOG_CODES',
        'fallback log fixe': "'ADMIN_USERS_BACKEND_FAILED'",
        'log sanitizé': "console.error('[admin-users]',adminUsersLogCode(e))",
        'réponse backend fixe': "code:'ADMIN_USERS_FAILED'",
    }
    for label, marker in required.items():
        if marker not in source:
            errors.append(f'admin-users: garde absent: {label}.')
    if not USERS_LIMIT_RE.search(source):
        errors.append('admin-users: MAX_ADMIN_USERS doit rester exactement à 1000.')
    for marker in COMMON_PRIVATE:
        if marker not in source:
            errors.append(f'admin-users: en-tête privé absent: {marker}.')
    lowered = source.lower()
    for forbidden in [
        "console.error('[admin-users]',e)",
        "console.error('[admin-users]',e?.message",
        "console.error('[admin-users]',e.message",
    ]:
        if forbidden.lower() in lowered:
            errors.append('admin-users: erreur backend brute journalisée.')
    return errors


def validate_analytics(source: str) -> list[str]:
    errors: list[str] = []
    required = {
        'POST uniquement': "req.method !== 'POST'",
        'admin explicite': 'requiredAdmin(req)',
        'lecture JSON bornée': 'readLimitedJson(req)',
        'Content-Length fail-closed': '!Number.isFinite(declared) || declared < 0 || declared > MAX_REQUEST_BYTES',
        'taille UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength > MAX_REQUEST_BYTES',
        'JSON explicite si corps': "contentType !== 'application/json'",
        'slug borné': 'GAME_SLUG_RE',
        'requête contributions bornée': '.limit(10000)',
        'allowlist logs': 'SAFE_LOG_CODES',
        'fallback log fixe': "'ADMIN_ANALYTICS_BACKEND_FAILED'",
        'log sanitizé': "console.error('[admin-analytics]', adminAnalyticsLogCode(error))",
        'réponse backend fixe': "code: 'ANALYTICS_FAILED'",
    }
    for label, marker in required.items():
        if marker not in source:
            errors.append(f'admin-analytics: garde absent: {label}.')
    if not ANALYTICS_LIMIT_RE.search(source):
        errors.append('admin-analytics: MAX_REQUEST_BYTES doit rester exactement à 4096.')
    for marker in COMMON_PRIVATE:
        if marker not in source:
            errors.append(f'admin-analytics: en-tête privé absent: {marker}.')
    lowered = source.lower()
    for forbidden in [
        "console.error('[admin-analytics]', error)",
        "console.error('[admin-analytics]', error?.message",
        "console.error('[admin-analytics]', error.message",
        'await req.json()',
    ]:
        if forbidden.lower() in lowered:
            errors.append('admin-analytics: erreur brute ou lecture JSON non bornée détectée.')

    auth_pos = source.find('const { service } = await requiredAdmin(req)')
    body_pos = source.find('const body = await readLimitedJson(req)')
    if auth_pos < 0 or body_pos < 0:
        errors.append('admin-analytics: ordre admin/corps impossible à vérifier.')
    elif auth_pos > body_pos:
        errors.append('admin-analytics: admin/JWT/AAL2 doit être validé avant la lecture du corps.')
    return errors


def validate(users_path: Path, analytics_path: Path) -> list[str]:
    try:
        users = users_path.read_text('utf-8', errors='strict')
        analytics = analytics_path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'lecture admin privée impossible: {exc}']
    return validate_users(users) + validate_analytics(analytics)


def self_test() -> None:
    users = USERS.read_text('utf-8', errors='strict')
    analytics = ANALYTICS.read_text('utf-8', errors='strict')
    clean = validate(USERS, ANALYTICS)
    if clean:
        raise AssertionError('Les fichiers réels sains doivent passer: ' + ' | '.join(clean))

    user_cases = {
        'users log brut': users.replace("console.error('[admin-users]',adminUsersLogCode(e));", "console.error('[admin-users]',e?.message||'ADMIN_USERS_FAILED');", 1),
        'users fallback retiré': users.replace("return SAFE_LOG_CODES.has(code) ? code : 'ADMIN_USERS_BACKEND_FAILED';", 'return code;', 1),
        'users no-store retiré': users.replace("'Cache-Control': 'private, no-store, max-age=0',", '', 1),
        'users limite augmentée': users.replace('MAX_ADMIN_USERS = 1000;', 'MAX_ADMIN_USERS = 5000;', 1),
        'users erreurs secondaires ignorées': users.replace('if(profileError||accessError||adminsError) throw profileError||accessError||adminsError;', '', 1),
    }
    analytics_cases = {
        'analytics log brut': analytics.replace("console.error('[admin-analytics]', adminAnalyticsLogCode(error));", "console.error('[admin-analytics]', error?.message || 'ANALYTICS_FAILED');", 1),
        'analytics fallback retiré': analytics.replace("return SAFE_LOG_CODES.has(code) ? code : 'ADMIN_ANALYTICS_BACKEND_FAILED';", 'return code;', 1),
        'analytics no-store retiré': analytics.replace("'Cache-Control': 'private, no-store, max-age=0',", '', 1),
        'analytics limite corps augmentée': analytics.replace('MAX_REQUEST_BYTES = 4096;', 'MAX_REQUEST_BYTES = 65536;', 1),
        'analytics lecture directe': analytics.replace('const body = await readLimitedJson(req);', 'const body = await req.json();', 1),
        'analytics auth après corps': analytics.replace(
            'const { service } = await requiredAdmin(req);\n    const body = await readLimitedJson(req);',
            'const body = await readLimitedJson(req);\n    const { service } = await requiredAdmin(req);',
            1,
        ),
        'analytics contributions non bornées': analytics.replace('\n      .limit(10000);', ';', 1),
    }

    with TemporaryDirectory() as tmp:
        users_path = Path(tmp) / 'users.ts'
        analytics_path = Path(tmp) / 'analytics.ts'
        analytics_path.write_text(analytics, encoding='utf-8')
        for label, mutated in user_cases.items():
            if mutated == users:
                raise AssertionError(f'Auto-test invalide, mutation admin-users sans effet: {label}')
            users_path.write_text(mutated, encoding='utf-8')
            if not validate(users_path, analytics_path):
                raise AssertionError(f'Affaiblissement admin-users non détecté: {label}')
        users_path.write_text(users, encoding='utf-8')
        for label, mutated in analytics_cases.items():
            if mutated == analytics:
                raise AssertionError(f'Auto-test invalide, mutation admin-analytics sans effet: {label}')
            analytics_path.write_text(mutated, encoding='utf-8')
            if not validate(users_path, analytics_path):
                raise AssertionError(f'Affaiblissement admin-analytics non détecté: {label}')
    print(f'OK auto-test lectures admin privées: {len(user_cases)+len(analytics_cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la confidentialité des lectures admin-users et admin-analytics.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate(USERS, ANALYTICS)
    if errors:
        print(f'ÉCHEC lectures admin privées: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK lectures admin privées: AAL2/no-store préservés, bornes conservées et logs backend sanitizés pour admin-users/admin-analytics.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
