#!/usr/bin/env python3
"""Garde A1 : réponse security-context minimale et décision inconnue fail-closed."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/security-context/index.ts'
WORKFLOW = ROOT / '.github/workflows/sinjira-security-context-response-v25.yml'


def validate(source: str, workflow: str) -> list[str]:
    errors: list[str] = []

    required_source = {
        'authentification requiredUser': 'const user = await requiredUser(req);',
        'session JWT vérifiée': 'const sessionId = sessionIdFromVerifiedRequest(req);',
        'RPC de décision serveur': 'service_security_evaluate_context_session',
        'géolocalisation explicitement activée': 'SINJIRA_TRUST_GEO_HEADERS',
        'réponse privée sans cache': "'Cache-Control': 'private, no-store, max-age=0'",
        'issues canoniques explicites': "const SECURITY_OUTCOMES = new Set(['allow', 'challenge', 'block']);",
        'projection publique nullable': 'function publicSecurityResult(data: unknown): PublicSecurityResult | null',
        'aucun défaut allow': "const outcome = typeof source.outcome === 'string' ? source.outcome.trim() : '';",
        'issue inconnue refusée': 'if (!SECURITY_OUTCOMES.has(outcome)) return null;',
        'challenge UUID obligatoire': 'if (!challengeId || !UUID_RE.test(challengeId)) return null;',
        'projection exécutée': 'const publicSecurity = publicSecurityResult(data);',
        'décision invalide détectée': 'if (!publicSecurity) {',
        'décision invalide indisponible': "return privateJson({ ok: false, error: 'Le contexte de sécurité est temporairement indisponible.' }, 503);",
        'projection utilisée sur HTTP': 'security: publicSecurity,',
        'objet complet réservé au push': 'runSecurityPushBackground(service, user.id, data)',
        'code fixe décision invalide': "console.warn('[security-context]', { code: 'SECURITY_DECISION_INVALID' });",
    }
    for label, fragment in required_source.items():
        if fragment not in source:
            errors.append(f'Manquant: {label}.')

    forbidden_global = {
        'sérialisation brute du résultat RPC': 'security: data',
        'spread brut du résultat RPC': '...data',
        'lecture IP X-Forwarded-For': 'x-forwarded-for',
        'lecture IP Cloudflare': 'cf-connecting-ip',
        'lecture IP X-Real-IP': 'x-real-ip',
        'lecture IP True-Client-IP': 'true-client-ip',
        'repli implicite allow': ": 'allow';",
    }
    lowered = source.lower()
    for label, fragment in forbidden_global.items():
        if fragment.lower() in lowered:
            errors.append(f'Interdit: {label}.')

    helper_start = source.find('function publicSecurityResult(data: unknown)')
    helper_end = source.find('function sessionIdFromVerifiedRequest', helper_start)
    if helper_start < 0 or helper_end < 0:
        errors.append('Impossible d’isoler publicSecurityResult().')
    else:
        helper = source[helper_start:helper_end]
        for field in (
            'risk_score', 'risk_reasons', 'country', 'region', 'city', 'latitude', 'longitude',
            'delete_after', 'user_id', 'device_key', 'display_name', 'platform',
        ):
            if field in helper:
                errors.append(f'Champ interne interdit dans la projection publique: {field}.')

    projection_pos = source.find('const publicSecurity = publicSecurityResult(data);')
    invalid_pos = source.find('if (!publicSecurity) {', projection_pos)
    push_pos = source.find('EdgeRuntime.waitUntil(runSecurityPushBackground', projection_pos)
    response_pos = source.find('security: publicSecurity,', projection_pos)
    if min(projection_pos, invalid_pos, push_pos, response_pos) < 0 or not (projection_pos < invalid_pos < push_pos < response_pos):
        errors.append('La décision doit être validée fail-closed avant le push de fond et avant toute réponse succès.')

    invalid_end = source.find('\n    }', invalid_pos)
    if invalid_pos >= 0 and invalid_end >= 0:
        invalid_block = source[invalid_pos:invalid_end]
        if '503' not in invalid_block:
            errors.append('Une décision serveur invalide doit produire un non-2xx 503 générique.')
        if 'EdgeRuntime.waitUntil' in invalid_block:
            errors.append('Aucun push ne doit partir pour une décision serveur invalide.')

    response_start = source.find('return privateJson({\n      ok: true')
    response_end = source.find('\n    });', response_start)
    if response_start < 0 or response_end < 0:
        errors.append('Impossible d’isoler la réponse HTTP de succès.')
    else:
        response = source[response_start:response_end]
        for field in ('risk_score', 'risk_reasons', 'country', 'region', 'city', 'latitude', 'longitude'):
            if any(marker in response for marker in (f'{field}:', f"'{field}':", f'"{field}":')):
                errors.append(f'Champ interne exposé dans la réponse HTTP: {field}.')
        if 'privacy:' in response:
            errors.append('La réponse publique contient encore le bloc documentaire privacy inutile au flux.')

    for line in source.splitlines():
        compact = line.strip()
        if compact.startswith('console.error') and (', error' in compact or ' error)' in compact or 'error.stack' in compact):
            errors.append('Le journal serveur sérialise encore un objet d’erreur brut.')

    required_workflow = {
        'runner épinglé': 'runs-on: ubuntu-24.04',
        'permissions lecture seule': 'contents: read',
        'Python épinglé': "python-version: '3.12.14'",
        'auto-test requête': 'python3 scripts/validate_security_context_request_security.py --self-test',
        'validation requête': 'python3 scripts/validate_security_context_request_security.py',
        'auto-test réponse': 'python3 scripts/validate_security_context_response_v25.py --self-test',
        'validation réponse': 'python3 scripts/validate_security_context_response_v25.py',
    }
    for label, fragment in required_workflow.items():
        if fragment not in workflow:
            errors.append(f'Workflow manquant: {label}.')

    watched = (
        'supabase/functions/security-context/index.ts',
        'scripts/validate_security_context_request_security.py',
        'scripts/validate_security_context_response_v25.py',
        '.github/workflows/sinjira-security-context-response-v25.yml',
    )
    for path in watched:
        if workflow.count(path) < 2:
            errors.append(f'Le workflow doit surveiller {path} sur pull_request et push.')

    if 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803' not in workflow:
        errors.append('actions/checkout doit rester épinglé au SHA revu.')
    if 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1' not in workflow:
        errors.append('actions/setup-python doit rester épinglé au SHA revu.')

    return errors


def self_test(source: str, workflow: str) -> None:
    mutations: list[tuple[str, str, str]] = [
        ('réponse RPC brute', source.replace('security: publicSecurity,', 'security: data,', 1), workflow),
        ('score de risque public', source.replace("return { outcome: outcome as 'allow' | 'block' };", "return { outcome: outcome as 'allow' | 'block', risk_score: source.risk_score } as any;", 1), workflow),
        ('pays sérialisé', source.replace("geo_mode: geo.country ? 'trusted_coarse' : 'disabled'", "country: geo.country,\n      geo_mode: geo.country ? 'trusted_coarse' : 'disabled'", 1), workflow),
        ('IP brute', source.replace("const countryRaw = req.headers.get('cf-ipcountry') || '';", "const countryRaw = req.headers.get('cf-ipcountry') || '';\n  const ip = req.headers.get('x-forwarded-for');", 1), workflow),
        ('auth retirée', source.replace('const user = await requiredUser(req);', "const user = { id: 'unsafe' };", 1), workflow),
        ('session vérifiée retirée', source.replace('const sessionId = sessionIdFromVerifiedRequest(req);', "const sessionId = 'unsafe';", 1), workflow),
        ('RPC retirée', source.replace('service_security_evaluate_context_session', 'unsafe_context_rpc', 1), workflow),
        ('repli allow réintroduit', source.replace("const outcome = typeof source.outcome === 'string' ? source.outcome.trim() : '';", "const outcome = typeof source.outcome === 'string' ? source.outcome.trim() : 'allow';", 1), workflow),
        ('issue inconnue acceptée', source.replace('if (!SECURITY_OUTCOMES.has(outcome)) return null;', '// issue inconnue acceptée', 1), workflow),
        ('challenge sans UUID', source.replace('if (!challengeId || !UUID_RE.test(challengeId)) return null;', '// UUID non vérifié', 1), workflow),
        ('validation placée après push', source.replace('    EdgeRuntime.waitUntil(runSecurityPushBackground(service, user.id, data));', '    const latePushMarker = true;', 1).replace('    const publicSecurity = publicSecurityResult(data);', '    EdgeRuntime.waitUntil(runSecurityPushBackground(service, user.id, data));\n    const publicSecurity = publicSecurityResult(data);', 1), workflow),
        ('503 transformé en succès', source.replace("return privateJson({ ok: false, error: 'Le contexte de sécurité est temporairement indisponible.' }, 503);", "return privateJson({ ok: true, security: { outcome: 'allow' } }, 200);", 1), workflow),
        ('erreur brute journalisée', source.replace("console.error('[security-context]', { code: 'SECURITY_CONTEXT_FAILED' });", "console.error('[security-context]', error);", 1), workflow),
        ('auto-test réponse CI retiré', source, workflow.replace('python3 scripts/validate_security_context_response_v25.py --self-test', 'echo self-test-retire', 1)),
        ('garde requête CI retiré', source, workflow.replace('python3 scripts/validate_security_context_request_security.py', 'echo request-guard-retire', 1)),
        ('chemin Edge retiré du trigger', source, workflow.replace("      - 'supabase/functions/security-context/index.ts'", "      - 'supabase/functions/security-context/index.disabled'", 1)),
    ]

    undetected: list[str] = []
    for name, mutated_source, mutated_workflow in mutations:
        if mutated_source == source and mutated_workflow == workflow:
            undetected.append(name + ' (mutation sans effet)')
            continue
        if not validate(mutated_source, mutated_workflow):
            undetected.append(name)
    if undetected:
        raise SystemExit('ÉCHEC auto-test, régressions non détectées: ' + ', '.join(undetected))
    print(f'OK: {len(mutations)}/{len(mutations)} régressions security-context détectées')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()

    source = EDGE.read_text(encoding='utf-8')
    workflow = WORKFLOW.read_text(encoding='utf-8')
    if args.self_test:
        self_test(source, workflow)
        return

    errors = validate(source, workflow)
    if errors:
        for error in errors:
            print(f'ERREUR: {error}')
        raise SystemExit(1)

    print('OK: security-context est borné, minimal et fail-closed; seules allow/challenge(UUID)/block peuvent sortir en succès.')


if __name__ == '__main__':
    main()
