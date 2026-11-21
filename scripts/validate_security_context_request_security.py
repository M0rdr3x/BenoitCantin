#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/security-context/index.ts'

REQUIRED = {
    'POST uniquement': "req.method !== 'POST'",
    'authentification obligatoire': 'requiredUser(req)',
    'session issue du JWT validé': 'sessionIdFromVerifiedRequest(req)',
    'lecture JSON bornée': 'readLimitedJson(req)',
    'lecteur HTTP borné par échéance': 'readLimitedUtf8BodyWithDeadline(req, MAX_REQUEST_BYTES, MAX_REQUEST_READ_TIMEOUT_MS)',
    'délai absolu de 4 secondes': 'MAX_REQUEST_READ_TIMEOUT_MS = 4_000;',
    'lecteur partagé contrôlé': "from '../_shared/read-chunk-deadline.mjs';",
    'MIME JSON strict': "contentType !== 'application/json'",
    'dépassement de délai détecté': "limited.reason === 'REQUEST_TIMEOUT'",
    'dépassement réel en octets détecté': "limited.reason === 'REQUEST_TOO_LARGE'",
    'HTTP 408 pour transmission bloquée': "Délai de transmission dépassé.' }, 408)",
    'journal privé expurgé': "console.error('[security-context]', { code: 'SECURITY_CONTEXT_FAILED' });",
    'réponse privée': "'Cache-Control': 'private, no-store, max-age=0'",
    'protection MIME': "'X-Content-Type-Options': 'nosniff'",
    'référent masqué': "'Referrer-Policy': 'no-referrer'",
    'géolocalisation explicite opt-in infrastructure': "Deno.env.get('SINJIRA_TRUST_GEO_HEADERS') !== 'true'",
    'pays approximatif seulement': "req.headers.get('cf-ipcountry')",
    'région approximative seulement': "req.headers.get('x-sinjira-region')",
    'RPC contexte session canonique': "service.rpc('service_security_evaluate_context_session'",
    'session imposée au RPC': 'p_session_id: sessionId',
    'réponse succès privée': 'return privateJson({\n      ok: true,',
    'contrat confidentialité IP': 'raw_ip_stored: false',
    'contrat confidentialité GPS': 'gps_used: false',
}

REQUIRED_PATTERNS = {
    'requête bornée exactement à 4096 octets': re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4_?096\s*;'),
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'lecture JSON directe non bornée espacée': 'await req.json (',
    'lecture texte directe non bornée': 'await req.text()',
    'ancien lecteur sans échéance': 'readLimitedUtf8Body(req, MAX_REQUEST_BYTES)',
    'lecteur HTTP direct sans échéance': 'await reader.read()',
    'attente annulation bloquante': 'await reader.cancel(',
    'journal brut de fournisseur': "console.error('[security-context]', error)",
    'journal erreur brute': 'console.error(error)',
    'lecture IP brute Cloudflare': 'cf-connecting-ip',
    'lecture IP brute proxy': 'x-forwarded-for',
    'lecture IP brute générique': 'x-real-ip',
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        source = path.read_text('utf-8', errors='ignore')
    except OSError as exc:
        return [f'Fonction security-context illisible: {exc}']

    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde security-context absent: {label}.')
    for label, pattern in REQUIRED_PATTERNS.items():
        if not pattern.search(source):
            errors.append(f'Garde security-context absent ou affaibli: {label}.')
    for label, marker in FORBIDDEN.items():
        if marker in source.lower():
            errors.append(f'Garde security-context violé: {label}.')

    parsed_pos = source.find('const parsed = await readLimitedJson(req)')
    auth_pos = source.find('const user = await requiredUser(req)')
    if parsed_pos >= 0 and auth_pos >= 0 and auth_pos > parsed_pos:
        errors.append('Le corps ne doit pas être lu avant la validation de l’utilisateur JWT.')

    if source.count('privateJson(') < 6:
        errors.append('Les réponses sensibles doivent rester uniformément privées et non cachables.')

    return errors


def self_test() -> None:
    """Mutations sur le VRAI code Edge, sans secrets ni base externe."""
    original = EDGE.read_text('utf-8', errors='strict')
    assert not validate(EDGE), 'Le contrat courant doit réussir avant les mutations.'
    mutations = {
        'limite HTTP relâchée': ('MAX_REQUEST_BYTES = 4096;', 'MAX_REQUEST_BYTES = 40960;'),
        'échéance supprimée': ('MAX_REQUEST_READ_TIMEOUT_MS = 4_000;', ''),
        'ancien lecteur sans deadline': (
            'readLimitedUtf8BodyWithDeadline(req, MAX_REQUEST_BYTES, MAX_REQUEST_READ_TIMEOUT_MS)',
            'readLimitedUtf8Body(req, MAX_REQUEST_BYTES)'
        ),
        'requête sans MIME JSON': ("contentType !== 'application/json'", 'false'),
        'HTTP 408 supprimé': ("Délai de transmission dépassé.' }, 408)", "Délai de transmission dépassé.' }, 413)"),
        'dépassement HTTP non détecté': ("limited.reason === 'REQUEST_TOO_LARGE'", 'false'),
        'erreur brute écrite en logs': (
            "console.error('[security-context]', { code: 'SECURITY_CONTEXT_FAILED' });",
            "console.error('[security-context]', error);"
        ),
        'JSON directement non borné': (
            'const parsed = await readLimitedJson(req);',
            'const parsed = { body: await req.json() };'
        ),
        'texte directement non borné': (
            'const parsed = await readLimitedJson(req);',
            'const parsed = { body: await req.text() };'
        ),
        'réponse privée supprimée': ("'Cache-Control': 'private, no-store, max-age=0',", ''),
        'IP brute réintroduite': ("req.headers.get('cf-ipcountry')", "req.headers.get('cf-connecting-ip')"),
        'JWT validé après la lecture': (
            'const user = await requiredUser(req);\n    const sessionId = sessionIdFromVerifiedRequest(req);\n    const parsed = await readLimitedJson(req);',
            'const parsed = await readLimitedJson(req);\n    const user = await requiredUser(req);\n    const sessionId = sessionIdFromVerifiedRequest(req);'
        ),
    }
    with TemporaryDirectory(prefix='security-context-contract-') as temporary:
        p = Path(temporary) / 'index.ts'
        for name, (needle, replacement) in mutations.items():
            assert original.count(needle) >= 1, f'Mutation invalide {name}: ancre absente.'
            changed = original.replace(needle, replacement, 1)
            assert changed != original, f'Mutation invalide {name}: source identique.'
            p.write_text(changed, encoding='utf-8')
            detected = validate(p)
            assert detected, f'Mutation de sécurité indétectée : {name}.'
    print(f'OK {len(mutations)} mutations négatives sur le code réel security-context.')



def main() -> int:
    parser = argparse.ArgumentParser(description='Valide les bornes HTTP et la confidentialité de security-context.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print('OK auto-test security-context.')
        return 0

    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC security-context: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK security-context: JWT avant corps, JSON strict 4 KiB/4 s, logs expurgés, no-store et aucune IP brute/GPS.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
