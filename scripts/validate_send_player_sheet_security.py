#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/send-player-sheet/index.ts'
CONFIG = ROOT / 'supabase/config.toml'

REQUIRED = {
    'auth commune': 'const user=await requiredUser(req);',
    'POST uniquement': "req.method!=='POST'",
    'mode gratuit compilé': 'const PAID_EXTERNAL_SERVICES_ENABLED=false;',
    'code mode gratuit': "code:'PAID_EXTERNAL_SERVICE_DISABLED'",
    'JSON explicite': "contentType.startsWith('application/json')",
    'lecture corps texte': 'const raw=await req.text();',
    'mesure UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma':'no-cache'",
    'protection MIME': "'X-Content-Type-Options':'nosniff'",
    'référent masqué': "'Referrer-Policy':'no-referrer'",
    'taille texte bornée': 'const MAX_TEXT=6000;',
    'origine modèle fixe': "const TEMPLATE_ORIGIN='https://www.benoitcantin.com';",
    'préfixe modèle fixe': "const TEMPLATE_PATH_PREFIX='/projets/sinjira/jeux/fracture-du-reseau-mere/documents/';",
    'redirections refusées': "redirect:'error'",
    'signature PDF vérifiée': "!=='%PDF-'",
    'destinataire compte': 'to:[user.email]',
    'log fournisseur fixe': "console.error('[send-player-sheet]',{code:'PLAYER_SHEET_EMAIL_PROVIDER_FAILED',status:sent.status});",
    'log global fixe': "console.error('[send-player-sheet]',{code:'SEND_PLAYER_SHEET_FAILED'});",
}

FORBIDDEN = {
    'client Supabase local': 'createClient(',
    'auth artisanale': 'function userFrom(',
    'JSON direct non borné': 'await req.json()',
    'lecture réponse fournisseur': 'await sent.text()',
    'log erreur brute court': 'console.error(e)',
    'log objet erreur brut': 'console.error(error)',
    'destination fournie par le client': 'body.email',
    'destination fields': 'fields.email',
    'service role direct': 'SUPABASE_SERVICE_ROLE_KEY',
}

REQUEST_LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*220_?000\s*;')
TEMPLATE_LIMIT_RE = re.compile(r'\bMAX_TEMPLATE_BYTES\s*=\s*15\s*\*\s*1024\s*\*\s*1024\s*;')


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def config_stanza(config: str) -> str:
    marker = '[functions.send-player-sheet]'
    if marker not in config:
        return ''
    return config.split(marker, 1)[1].split('[functions.', 1)[0]


def validate_text(source: str, config: str) -> list[str]:
    errors: list[str] = []

    for label, marker in REQUIRED.items():
        require(errors, marker in source, f'Garde send-player-sheet absent: {label}.')
    for label, marker in FORBIDDEN.items():
        require(errors, marker not in source, f'Garde send-player-sheet violé: {label}.')

    require(errors, REQUEST_LIMIT_RE.search(source) is not None,
            'MAX_REQUEST_BYTES doit rester exactement à 220000 octets.')
    require(errors, TEMPLATE_LIMIT_RE.search(source) is not None,
            'MAX_TEMPLATE_BYTES doit rester exactement à 15 Mio.')

    auth_pos = source.find('const user=await requiredUser(req);')
    paid_pos = source.find('if(!PAID_EXTERNAL_SERVICES_ENABLED)')
    parse_pos = source.find('const parsed=await readLimitedJson(req);')
    provider_pos = source.find("fetch('https://api.resend.com/emails'")
    require(errors, auth_pos >= 0 and paid_pos > auth_pos,
            'Le compte doit être authentifié avant le garde du service payant.')
    require(errors, parse_pos > paid_pos,
            'Le corps ne doit pas être lu tant que le service payant est désactivé.')
    require(errors, provider_pos > parse_pos,
            'Le fournisseur externe doit rester derrière auth, garde payant et validation du corps.')

    raw_pos = source.find('const raw=await req.text();')
    utf8_pos = source.find('new TextEncoder().encode(raw).byteLength')
    json_pos = source.find("JSON.parse(raw||'{}')")
    require(errors, raw_pos >= 0 and utf8_pos > raw_pos and json_pos > utf8_pos,
            'Le corps doit être mesuré en octets UTF-8 avant le parsing JSON.')

    fetch_template_pos = source.find("fetch(templateUrl(mode),{cache:'no-store',redirect:'error'})")
    declared_template_pos = source.find("response.headers.get('content-length')")
    actual_template_pos = source.find('bytes.byteLength===0||bytes.byteLength>MAX_TEMPLATE_BYTES')
    signature_pos = source.find("String.fromCharCode(...bytes.subarray(0,5))!=='%PDF-'")
    require(errors,
            fetch_template_pos >= 0 and declared_template_pos > fetch_template_pos and
            actual_template_pos > declared_template_pos and signature_pos > actual_template_pos,
            'Le modèle PDF doit refuser les redirections puis être borné et signé avant chargement.')

    origin_checks = [
        "url.protocol!=='https:'",
        'url.origin!==TEMPLATE_ORIGIN',
        '!url.pathname.startsWith(TEMPLATE_PATH_PREFIX)',
        "!url.pathname.toLowerCase().endsWith('.pdf')",
        'url.username||url.password||url.search||url.hash',
    ]
    for marker in origin_checks:
        require(errors, marker in source, f'Validation URL modèle incomplète: {marker}')

    require(errors, "['session_title','party_code','player_label'].includes(name)" in source,
            'Les champs internes de session doivent rester ignorés.')
    require(errors, '.slice(0,MAX_TEXT)' in source,
            'Les valeurs de champs PDF doivent rester bornées.')

    console_lines = [line.strip() for line in source.splitlines() if 'console.' in line]
    expected_console_lines = [
        "console.error('[send-player-sheet]',{code:'PLAYER_SHEET_EMAIL_PROVIDER_FAILED',status:sent.status});",
        "console.error('[send-player-sheet]',{code:'SEND_PLAYER_SHEET_FAILED'});",
    ]
    require(errors, console_lines == expected_console_lines,
            'Les logs send-player-sheet doivent rester limités aux codes fixes approuvés.')

    stanza = config_stanza(config)
    require(errors, bool(stanza), 'Stanza [functions.send-player-sheet] absente de supabase/config.toml.')
    require(errors, 'verify_jwt = true' in stanza, 'send-player-sheet doit conserver verify_jwt=true.')
    require(errors, 'verify_jwt = false' not in stanza, 'verify_jwt=false interdit pour send-player-sheet.')

    return errors


def validate(edge_path: Path = EDGE, config_path: Path = CONFIG) -> list[str]:
    try:
        source = edge_path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'send-player-sheet illisible: {exc}']
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
        'service payant activé': source.replace('PAID_EXTERNAL_SERVICES_ENABLED=false', 'PAID_EXTERNAL_SERVICES_ENABLED=true', 1),
        'garde payant après corps': source.replace(
            "    const parsed=await readLimitedJson(req);\n    if(parsed.response)return parsed.response;",
            "    const earlyParsed=await readLimitedJson(req);\n    if(earlyParsed.response)return earlyParsed.response;\n    const parsed=earlyParsed;",
            1,
        ).replace('    if(!PAID_EXTERNAL_SERVICES_ENABLED){', '    if(!PAID_EXTERNAL_SERVICES_ENABLED&&parsed){', 1),
        'requiredUser retiré': source.replace('const user=await requiredUser(req);', "const user={email:'bypass@example.test'};", 1),
        'req.json direct': source.replace('const raw=await req.text();', 'const raw=JSON.stringify(await req.json());', 1),
        'content-type affaibli': source.replace("contentType.startsWith('application/json')", "contentType.startsWith('text/plain')", 1),
        'limite requête augmentée': source.replace('MAX_REQUEST_BYTES=220_000;', 'MAX_REQUEST_BYTES=2_200_000;', 1),
        'mesure UTF-8 retirée': source.replace('new TextEncoder().encode(raw).byteLength', 'raw.length', 1),
        'no-store retiré': source.replace("  'Cache-Control':'private, no-store, max-age=0',\n", '', 1),
        'redirections autorisées': source.replace("redirect:'error'", "redirect:'follow'", 1),
        'limite modèle augmentée': source.replace('MAX_TEMPLATE_BYTES=15*1024*1024;', 'MAX_TEMPLATE_BYTES=150*1024*1024;', 1),
        'signature PDF retirée': source.replace("  if(bytes.length<5||String.fromCharCode(...bytes.subarray(0,5))!=='%PDF-')throw new Error('PLAYER_SHEET_TEMPLATE_NOT_PDF');\n", '', 1),
        'origine modèle relâchée': source.replace('url.origin!==TEMPLATE_ORIGIN', 'false', 1),
        'destination arbitraire': source.replace('to:[user.email]', 'to:[String(body.email||user.email)]', 1),
        'réponse fournisseur lue': source.replace(
            "console.error('[send-player-sheet]',{code:'PLAYER_SHEET_EMAIL_PROVIDER_FAILED',status:sent.status});",
            "console.error('[send-player-sheet]',await sent.text());",
            1,
        ),
        'catch brut': source.replace(
            "console.error('[send-player-sheet]',{code:'SEND_PLAYER_SHEET_FAILED'});",
            "console.error(error);",
            1,
        ),
        'champ PDF non borné': source.replace('.slice(0,MAX_TEXT)', '', 1),
    }

    with TemporaryDirectory() as raw:
        tmp = Path(raw)
        edge_path = tmp / 'index.ts'
        config_path = tmp / 'config.toml'
        config_path.write_text(config, encoding='utf-8')

        for label, mutated in source_mutations.items():
            if mutated == source:
                raise AssertionError(f'Mutation source sans effet: {label}')
            edge_path.write_text(mutated, encoding='utf-8')
            if not validate(edge_path, config_path):
                raise AssertionError(f'Régression source non détectée: {label}')

        edge_path.write_text(source, encoding='utf-8')
        config_mutations = {
            'verify_jwt désactivé': config.replace(
                '[functions.send-player-sheet]\nverify_jwt = true',
                '[functions.send-player-sheet]\nverify_jwt = false',
                1,
            ),
            'stanza send-player-sheet retirée': config.replace(
                '[functions.send-player-sheet]\nverify_jwt = true\n\n',
                '',
                1,
            ),
        }
        for label, mutated in config_mutations.items():
            if mutated == config:
                raise AssertionError(f'Mutation config sans effet: {label}')
            config_path.write_text(mutated, encoding='utf-8')
            if not validate(edge_path, config_path):
                raise AssertionError(f'Régression config non détectée: {label}')

    print(f'OK auto-tests send-player-sheet: {len(source_mutations) + len(config_mutations)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la frontière HTTP, PDF, courriel et mode gratuit de send-player-sheet.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate()
    if errors:
        print(f'ÉCHEC send-player-sheet: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK send-player-sheet: auth avant garde payant, transport désactivé, JSON borné, PDF validé, destinataire du compte et logs sanitizés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
