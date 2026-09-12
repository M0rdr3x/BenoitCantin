#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/fracture-engine-gateway/index.ts'
CONFIG = ROOT / 'supabase/config.toml'

EXPECTED_ACTIONS = {
    'fracture_engine_start',
    'fracture_engine_submit_keep',
    'fracture_engine_pick',
    'fracture_engine_submit_report',
    'fracture_engine_submit_accusation',
}

REQUIRED = {
    'version gateway historique': "const GATEWAY_VERSION='24.4.15';",
    'POST uniquement': "req.method!=='POST'",
    'Bearer explicite': "authorization.startsWith('Bearer ')",
    'JWT revérifié côté fonction': 'client.auth.getUser(token)',
    'JSON explicite': "contentType.startsWith('application/json')",
    'lecture corps par texte': 'const raw=await req.text();',
    'mesure UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma':'no-cache'",
    'protection MIME': "'X-Content-Type-Options':'nosniff'",
    'référent masqué': "'Referrer-Policy':'no-referrer'",
    'code partie strict': 'const PARTY_RE=/^FRM-[A-Z0-9]{6}$/;',
    'relecture état assaini': "client.rpc('fracture_engine_get_state_safe',{p_party_code:partyCode})",
    'appel action sans données brutes': 'const {error:actionError}=await client.rpc(action,args);',
    'log configuration fixe': "console.error('[fracture-engine-gateway]',{code:'FRACTURE_GATEWAY_CONFIG_MISSING'});",
    'log action fixe': "console.warn('[fracture-engine-gateway]',{code:'FRACTURE_ACTION_REJECTED',action});",
    'log état fixe': "console.error('[fracture-engine-gateway]',{code:'FRACTURE_STATE_LOAD_FAILED'});",
    'log rejet fixe': "console.error('[fracture-engine-gateway]',{code:'FRACTURE_GATEWAY_REQUEST_REJECTED'});",
}

FORBIDDEN = {
    'JSON direct non borné': 'await req.json()',
    'helper JSON public partagé': "import { corsHeaders, json }",
    'retour helper JSON public': 'return json(',
    'log message action brut': 'console.warn(\'[Fracture gateway action]\'',
    'log message état brut': 'console.error(\'[Fracture gateway state]\'',
    'log erreur brute': "console.error('[Fracture gateway]',message)",
    'état brut historique': "client.rpc('fracture_engine_get_state',{",
}

MAX_BODY_RE = re.compile(r'\bMAX_BODY_BYTES\s*=\s*32_?000\s*;')
ACTIONS_RE = re.compile(r'const\s+ALLOWED_ACTIONS\s*=\s*new\s+Set\s*\(\s*\[(.*?)\]\s*\)', re.S)


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def config_stanza(config: str) -> str:
    marker = '[functions.fracture-engine-gateway]'
    if marker not in config:
        return ''
    return config.split(marker, 1)[1].split('[functions.', 1)[0]


def validate_text(source: str, config: str) -> list[str]:
    errors: list[str] = []

    for label, marker in REQUIRED.items():
        require(errors, marker in source, f'Garde fracture-engine-gateway absent: {label}.')
    for label, marker in FORBIDDEN.items():
        require(errors, marker not in source, f'Garde fracture-engine-gateway violé: {label}.')
    require(errors, MAX_BODY_RE.search(source) is not None, 'MAX_BODY_BYTES doit rester exactement à 32000 octets.')

    match = ACTIONS_RE.search(source)
    if not match:
        errors.append('Allowlist fracture-engine-gateway introuvable.')
    else:
        actions = set(re.findall(r"'([^']+)'", match.group(1)))
        if actions != EXPECTED_ACTIONS:
            errors.append(f'Allowlist fracture-engine-gateway modifiée: {sorted(actions)}')

    auth_pos = source.find('client.auth.getUser(token)')
    body_pos = source.find('await readLimitedJson(req)')
    require(errors, auth_pos >= 0 and body_pos >= 0 and auth_pos < body_pos,
            'Le JWT doit être vérifié avant toute lecture/parsing du corps.')

    text_pos = source.find('const raw=await req.text();')
    utf8_pos = source.find('new TextEncoder().encode(raw).byteLength')
    parse_pos = source.find("JSON.parse(raw||'{}')")
    require(errors, text_pos >= 0 and utf8_pos > text_pos and parse_pos > utf8_pos,
            'Le corps doit être lu comme texte, mesuré en octets UTF-8, puis seulement parsé en JSON.')

    action_pos = source.find('const {error:actionError}=await client.rpc(action,args);')
    safe_state_pos = source.find("client.rpc('fracture_engine_get_state_safe',{p_party_code:partyCode})")
    require(errors, action_pos >= 0 and safe_state_pos > action_pos,
            'Après une action, la réponse brute doit être ignorée et l’état assaini relu séparément.')

    console_lines = [line.strip() for line in source.splitlines() if 'console.' in line]
    expected_console_lines = [
        "console.error('[fracture-engine-gateway]',{code:'FRACTURE_GATEWAY_CONFIG_MISSING'});",
        "console.warn('[fracture-engine-gateway]',{code:'FRACTURE_ACTION_REJECTED',action});",
        "console.error('[fracture-engine-gateway]',{code:'FRACTURE_STATE_LOAD_FAILED'});",
        "console.error('[fracture-engine-gateway]',{code:'FRACTURE_GATEWAY_REQUEST_REJECTED'});",
    ]
    require(errors, console_lines == expected_console_lines,
            'Les logs fracture-engine-gateway doivent rester limités aux codes fixes approuvés.')

    stanza = config_stanza(config)
    require(errors, bool(stanza), 'Stanza [functions.fracture-engine-gateway] absente de supabase/config.toml.')
    require(errors, 'verify_jwt = true' in stanza, 'fracture-engine-gateway doit conserver verify_jwt=true.')
    require(errors, 'verify_jwt = false' not in stanza, 'verify_jwt=false interdit pour fracture-engine-gateway.')

    return errors


def validate(edge_path: Path = EDGE, config_path: Path = CONFIG) -> list[str]:
    try:
        source = edge_path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'fracture-engine-gateway illisible: {exc}']
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
        'content-type retiré': source.replace("    return {response:privateJson({ok:false,error:'Content-Type application/json requis.',gateway_version:GATEWAY_VERSION},415)};\n", '', 1),
        'req.json direct': source.replace('const raw=await req.text();', 'const raw=JSON.stringify(await req.json());', 1),
        'mesure UTF-8 retirée': source.replace('new TextEncoder().encode(raw).byteLength', 'raw.length', 1),
        'limite augmentée': source.replace('MAX_BODY_BYTES=32_000;', 'MAX_BODY_BYTES=320_000;', 1),
        'auth après corps': source.replace(
            '    const token=authorization.slice(7);',
            '    const earlyParsed=await readLimitedJson(req);\n    if(earlyParsed.response) return earlyParsed.response;\n    const token=authorization.slice(7);',
            1,
        ),
        'getUser retiré': source.replace('const {data:userData,error:userError}=await client.auth.getUser(token);', 'const userData={user:{id:\'bypass\'}}; const userError=null;', 1),
        'Bearer retiré': source.replace("  if(!authorization.startsWith('Bearer ')) return privateJson({ok:false,error:'Connexion requise.',gateway_version:GATEWAY_VERSION},401);\n", '', 1),
        'no-store retiré': source.replace("  'Cache-Control':'private, no-store, max-age=0',\n", '', 1),
        'action ajoutée': source.replace("  'fracture_engine_submit_accusation'\n", "  'fracture_engine_submit_accusation',\n  'fracture_engine_debug'\n", 1),
        'état brut restauré': source.replace('fracture_engine_get_state_safe', 'fracture_engine_get_state', 1),
        'réponse action brute récupérée': source.replace('const {error:actionError}=await client.rpc(action,args);', 'const {data:actionData,error:actionError}=await client.rpc(action,args);', 1),
        'log action brut': source.replace("console.warn('[fracture-engine-gateway]',{code:'FRACTURE_ACTION_REJECTED',action});", "console.warn('[fracture-engine-gateway]',actionError.message);", 1),
        'log état brut': source.replace("console.error('[fracture-engine-gateway]',{code:'FRACTURE_STATE_LOAD_FAILED'});", "console.error('[fracture-engine-gateway]',stateError.message);", 1),
        'log catch brut': source.replace("console.error('[fracture-engine-gateway]',{code:'FRACTURE_GATEWAY_REQUEST_REJECTED'});", "console.error('[fracture-engine-gateway]',error);", 1),
        'version changée': source.replace("GATEWAY_VERSION='24.4.15'", "GATEWAY_VERSION='99.0.0'", 1),
        'POST retiré': source.replace("  if(req.method!=='POST') return privateJson({ok:false,error:'Méthode non autorisée.',gateway_version:GATEWAY_VERSION},405);\n", '', 1),
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
                '[functions.fracture-engine-gateway]\nverify_jwt = true',
                '[functions.fracture-engine-gateway]\nverify_jwt = false',
                1,
            ),
            'stanza gateway retirée': config.replace(
                '[functions.fracture-engine-gateway]\nverify_jwt = true\n\n',
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

    print(f'OK auto-tests fracture-engine-gateway: {len(source_mutations) + len(config_mutations)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la frontière HTTP/JWT et la confidentialité de fracture-engine-gateway.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate()
    if errors:
        print(f'ÉCHEC fracture-engine-gateway: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK fracture-engine-gateway: JWT avant corps, POST JSON 32 Ko réel, allowlist fermée, état assaini, réponses no-store et logs sanitizés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
