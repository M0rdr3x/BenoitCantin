#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/admin-reports/index.ts'

REQUIRED = {
    'POST uniquement': "req.method !== 'POST'",
    'admin explicite': 'requiredAdmin(req)',
    'lecture JSON bornée': 'readLimitedJson(req)',
    'content-type JSON strict': "if (contentType !== 'application/json') throw new Error('JSON_REQUIRED');",
    'taille UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'réponse privée': "'Cache-Control': 'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma': 'no-cache'",
    'nosniff': "'X-Content-Type-Options': 'nosniff'",
    'no-referrer': "'Referrer-Policy': 'no-referrer'",
    'courriel admin existant préservé': 'email: emails.get(r.owner_user_id)',
    'limite historique rapports préservée': '.limit(2000)',
    'erreur MFA fermée': "error?.message === 'MFA_STATE_UNAVAILABLE'",
    'réponse privée rapports': 'return privateJson({\n        ok:true,\n        reports,',
    'dashboard fail-closed': "throw new Error('REPORT_DASHBOARD_QUERY_FAILED')",
    'profils fail-closed': "throw new Error('REPORT_PROFILES_LOOKUP_FAILED')",
    'comptes Auth fail-closed': "throw new Error('REPORT_OWNER_LOOKUP_FAILED')",
    'log sanitizé': "console.error('[admin-reports]', safeLogCode(error));",
    'fallback log fixe': "return SAFE_LOG_CODES.has(code) ? code : 'ADMIN_REPORTS_FAILED';",
    'JSON requis réponse explicite': "error?.message === 'JSON_REQUIRED'",
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'helper JSON générique cacheable': 'return json(',
    'import helper JSON générique': "import { corsHeaders, json }",
    'auth admin indirecte par requiredUser': 'requiredUser(req)',
    'log objet erreur brut': "console.error('[admin-reports]', error);",
}

LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4_?096\s*;')


def validate(path: Path) -> list[str]:
    try:
        source = path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'admin-reports illisible: {exc}']

    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde admin-reports absent: {label}.')
    if not LIMIT_RE.search(source):
        errors.append('Garde admin-reports absent ou affaibli: requête exactement bornée à 4096 octets.')
    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde admin-reports violé: {label}.')

    auth_pos = source.find('const { service } = await requiredAdmin(req)')
    body_pos = source.find('const body = await readLimitedJson(req)')
    if auth_pos < 0 or body_pos < 0:
        errors.append('Ordre admin/corps impossible à vérifier.')
    elif auth_pos > body_pos:
        errors.append('Le corps ne doit pas être lu avant la validation admin/JWT/AAL2.')

    dashboard_check = source.find("if (reports.error || active.error || finished.error) throw new Error('REPORT_DASHBOARD_QUERY_FAILED');")
    dashboard_return = source.find('dashboard:{')
    if dashboard_check < 0 or dashboard_return < 0 or dashboard_check > dashboard_return:
        errors.append('Les erreurs du tableau de bord doivent être vérifiées avant de fabriquer les compteurs.')

    profile_check = source.find("if (profileResult.error) throw new Error('REPORT_PROFILES_LOOKUP_FAILED');")
    profile_map = source.find('const profileMap = new Map')
    if profile_check < 0 or profile_map < 0 or profile_check > profile_map:
        errors.append('Les erreurs de profils doivent être vérifiées avant de construire les identités.')

    owner_check = source.find("if (ownerError) throw new Error('REPORT_OWNER_LOOKUP_FAILED');")
    email_set = source.find('if (data?.user?.email) emails.set(id, data.user.email);')
    if owner_check < 0 or email_set < 0 or owner_check > email_set:
        errors.append('Les erreurs Auth doivent être vérifiées avant d’exposer les courriels administrateur.')

    if source.count('privateJson(') < 14:
        errors.append('Les réponses administratives doivent rester uniformément privées et non cachables.')
    return errors


def self_test() -> None:
    real = EDGE.read_text('utf-8', errors='strict')
    clean = validate(EDGE)
    if clean:
        raise AssertionError('Le fichier réel sain doit passer: ' + ' | '.join(clean))

    cases = {
        'json direct': real.replace('const body = await readLimitedJson(req);', 'const body = await req.json();', 1),
        'content-type JSON retiré': real.replace("  if (contentType !== 'application/json') throw new Error('JSON_REQUIRED');\n", '', 1),
        'no-store retiré': real.replace("'Cache-Control': 'private, no-store, max-age=0',", '', 1),
        'limite affaiblie': real.replace('MAX_REQUEST_BYTES = 4096;', 'MAX_REQUEST_BYTES = 40960;', 1),
        'admin explicite retiré': real.replace('const { service } = await requiredAdmin(req);', 'const user = await requiredUser(req); const service = serviceClient();', 1),
        'ordre inversé': real.replace(
            'const { service } = await requiredAdmin(req);\n    const body = await readLimitedJson(req);',
            'const body = await readLimitedJson(req);\n    const { service } = await requiredAdmin(req);',
            1,
        ),
        'réponse cacheable': real.replace('return privateJson({\n        ok:true,\n        reports,', 'return json({\n        ok:true,\n        reports,', 1),
        'erreur dashboard ignorée': real.replace("      if (reports.error || active.error || finished.error) throw new Error('REPORT_DASHBOARD_QUERY_FAILED');\n", '', 1),
        'erreur profils ignorée': real.replace("      if (profileResult.error) throw new Error('REPORT_PROFILES_LOOKUP_FAILED');\n", '', 1),
        'erreur Auth ignorée': real.replace("        if (ownerError) throw new Error('REPORT_OWNER_LOOKUP_FAILED');\n", '', 1),
        'log brut réintroduit': real.replace("console.error('[admin-reports]', safeLogCode(error));", "console.error('[admin-reports]', error);", 1),
    }

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'index.ts'
        for label, mutated in cases.items():
            if mutated == real:
                raise AssertionError(f'Auto-test invalide, mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Affaiblissement non détecté: {label}')
    print(f'OK auto-test admin-reports: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la confidentialité, les bornes HTTP et la cohérence fail-closed de admin-reports.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC admin-reports: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK admin-reports: admin/JWT/AAL2 avant corps, JSON strict 4 KiB, lectures fail-closed et réponses privées no-store.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
