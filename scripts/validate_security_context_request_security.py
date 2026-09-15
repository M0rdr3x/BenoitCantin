#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/security-context/index.ts'
WORKFLOW = ROOT / '.github/workflows/sinjira-security-context-request-v25.yml'

REQUIRED = {
    'POST uniquement': "req.method !== 'POST'",
    'authentification obligatoire': 'requiredUser(req)',
    'session issue du JWT validé': 'sessionIdFromVerifiedRequest(req)',
    'lecture JSON bornée': 'readLimitedJson(req)',
    'normalisation MIME exacte': ".split(';', 1)[0].trim().toLowerCase()",
    'JSON exact': "contentType !== 'application/json'",
    'lecture bornée par flux': 'req.body?.getReader()',
    'annulation au dépassement': 'reader.cancel()',
    'décodage UTF-8 strict': "new TextDecoder('utf-8', { fatal: true })",
    'log global à code fixe': "console.error('[security-context]', { code: 'SECURITY_CONTEXT_FAILED' });",
    'réponse privée': "'Cache-Control': 'private, no-store, max-age=0'",
    'protection MIME': "'X-Content-Type-Options': 'nosniff'",
    'référent masqué': "'Referrer-Policy': 'no-referrer'",
    'géolocalisation explicitement opt-in infrastructure': "Deno.env.get('SINJIRA_TRUST_GEO_HEADERS') !== 'true'",
    'pays approximatif seulement': "req.headers.get('cf-ipcountry')",
    'région approximative seulement': "req.headers.get('x-sinjira-region')",
    'RPC contexte session canonique': "service.rpc('service_security_evaluate_context_session'",
    'session imposée au RPC': 'p_session_id: sessionId',
    'réponse succès privée': 'return privateJson({\n      ok: true,',
}

REQUIRED_PATTERNS = {
    'requête bornée exactement à 4096 octets': re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4_?096\s*;'),
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'lecture JSON directe non bornée espacée': 'await req.json (',
    'lecture texte intégrale avant borne': 'await req.text()',
    'MIME JSON par préfixe': "startswith('application/json')",
    'lecture IP brute Cloudflare': 'cf-connecting-ip',
    'lecture IP brute proxy': 'x-forwarded-for',
    'lecture IP brute générique': 'x-real-ip',
    'log objet erreur brut security-context': "console.error('[security-context]', error)",
    'log objet erreur brut générique': 'console.error(error)',
    'log stack erreur brute': 'error.stack',
    'géolocalisation GPS navigateur': 'navigator.geolocation',
    'géolocalisation GPS getCurrentPosition': 'getcurrentposition',
    'géolocalisation GPS watchPosition': 'watchposition',
    'latitude précise': 'latitude',
    'longitude précise': 'longitude',
}

WORKFLOW_REQUIRED = {
    'permissions lecture seule': 'contents: read',
    'runner épinglé': 'runs-on: ubuntu-24.04',
    'Python épinglé': "python-version: '3.12.14'",
}

WORKFLOW_COMMAND_PATTERNS = {
    'auto-test exécuté': re.compile(
        r'^\s*(?:-\s*)?run:\s+python3 scripts/validate_security_context_request_security\.py --self-test\s*$',
        re.MULTILINE,
    ),
    'validation exécutée': re.compile(
        r'^\s*(?:-\s*)?run:\s+python3 scripts/validate_security_context_request_security\.py\s*$',
        re.MULTILINE,
    ),
}

WATCHED_PATHS = (
    'supabase/functions/security-context/index.ts',
    'scripts/validate_security_context_request_security.py',
    '.github/workflows/sinjira-security-context-request-v25.yml',
)

CHECKOUT_SHA = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'


def validate(path: Path, workflow_path: Path = WORKFLOW) -> list[str]:
    errors: list[str] = []
    try:
        source = path.read_text('utf-8', errors='ignore')
    except OSError as exc:
        return [f'Fonction security-context illisible: {exc}']

    try:
        workflow = workflow_path.read_text('utf-8', errors='ignore')
    except OSError as exc:
        return [f'Workflow security-context illisible: {exc}']

    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde security-context absent: {label}.')
    for label, pattern in REQUIRED_PATTERNS.items():
        if not pattern.search(source):
            errors.append(f'Garde security-context absent ou affaibli: {label}.')

    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde security-context violé: {label}.')

    parsed_pos = source.find('const parsed = await readLimitedJson(req)')
    auth_pos = source.find('const user = await requiredUser(req)')
    session_pos = source.find('const sessionId = sessionIdFromVerifiedRequest(req)')
    if parsed_pos < 0 or auth_pos < 0 or session_pos < 0 or not (auth_pos < session_pos < parsed_pos):
        errors.append('Le JWT et la session issue du JWT doivent être validés avant toute lecture du corps.')

    if source.count('privateJson(') < 6:
        errors.append('Les réponses sensibles doivent rester uniformément privées et non cachables.')

    for label, marker in WORKFLOW_REQUIRED.items():
        if marker not in workflow:
            errors.append(f'Workflow security-context absent ou affaibli: {label}.')
    for label, pattern in WORKFLOW_COMMAND_PATTERNS.items():
        if not pattern.search(workflow):
            errors.append(f'Workflow security-context absent ou affaibli: {label}.')

    if 'permissions:\n  contents: write' in workflow:
        errors.append('Le workflow security-context ne doit pas obtenir contents: write.')

    for watched in WATCHED_PATHS:
        if workflow.count(watched) < 2:
            errors.append(f'Le workflow doit surveiller {watched} sur pull_request et push.')

    if CHECKOUT_SHA not in workflow:
        errors.append('actions/checkout doit rester épinglé au SHA revu.')
    if SETUP_PYTHON_SHA not in workflow:
        errors.append('actions/setup-python doit rester épinglé au SHA revu.')

    return errors


def self_test() -> None:
    with TemporaryDirectory() as raw:
        root = Path(raw)
        path = root / 'index.ts'
        workflow_path = root / 'workflow.yml'
        safe = """
const MAX_REQUEST_BYTES = 4096;
const PRIVATE_HEADERS = {
  'Cache-Control': 'private, no-store, max-age=0',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
};
function privateJson(data, status=200){return new Response(JSON.stringify(data),{status,headers:PRIVATE_HEADERS})}
async function readLimitedJson(req){
 const contentType = (req.headers.get('content-type') || '').split(';', 1)[0].trim().toLowerCase();
 if (contentType !== 'application/json') return {response:privateJson({},415)};
 const reader = req.body?.getReader();
 if(!reader)return {body:{}};
 const chunks=[]; let total=0;
 while(true){
  const {done,value}=await reader.read(); if(done)break; if(!value)continue;
  total+=value.byteLength;
  if(total>MAX_REQUEST_BYTES){try{await reader.cancel()}catch{} return {response:privateJson({},413)}}
  chunks.push(value);
 }
 const bytes=new Uint8Array(total); let offset=0;
 for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength}
 const raw=new TextDecoder('utf-8', { fatal: true }).decode(bytes);
 return {body:JSON.parse(raw||'{}')};
}
function sessionIdFromVerifiedRequest(req){return req}
function trustedGeo(req){
 if (Deno.env.get('SINJIRA_TRUST_GEO_HEADERS') !== 'true') return {country:null,region:null};
 const country=req.headers.get('cf-ipcountry');
 const region=req.headers.get('x-sinjira-region');
 return {country,region};
}
Deno.serve(async (req) => {
 if (req.method !== 'POST') return privateJson({},405);
 try {
  const user = await requiredUser(req);
  const sessionId = sessionIdFromVerifiedRequest(req);
  const parsed = await readLimitedJson(req);
  if (parsed.response) return parsed.response;
  if (!parsed.body) return privateJson({},400);
  const geo=trustedGeo(req);
  const service=serviceClient();
  const {data}=await service.rpc('service_security_evaluate_context_session',{p_session_id: sessionId});
  if(!data)return privateJson({},500);
  return privateJson({
      ok: true,
      geo
  });
 } catch (error) {
  const code = error instanceof Error ? error.message : '';
  if (code === 'AUTH_REQUIRED') return privateJson({},401);
  console.error('[security-context]', { code: 'SECURITY_CONTEXT_FAILED' });
  return privateJson({},500);
 }
});
"""
        safe_workflow = f"""name: test
on:
  pull_request:
    paths:
      - '{WATCHED_PATHS[0]}'
      - '{WATCHED_PATHS[1]}'
      - '{WATCHED_PATHS[2]}'
  push:
    paths:
      - '{WATCHED_PATHS[0]}'
      - '{WATCHED_PATHS[1]}'
      - '{WATCHED_PATHS[2]}'
permissions:
  contents: read
jobs:
  validate:
    runs-on: ubuntu-24.04
    steps:
      - uses: {CHECKOUT_SHA}
      - uses: {SETUP_PYTHON_SHA}
        with:
          python-version: '3.12.14'
      - run: python3 scripts/validate_security_context_request_security.py --self-test
      - run: python3 scripts/validate_security_context_request_security.py
"""
        path.write_text(safe, encoding='utf-8')
        workflow_path.write_text(safe_workflow, encoding='utf-8')
        clean = validate(path, workflow_path)
        if clean:
            raise AssertionError('Le cas sain doit passer: ' + ' | '.join(clean))

        source_mutations = {
            'lecture JSON directe': safe.replace(' const reader = req.body?.getReader();', ' const bodyDirect = await req.json();'),
            'lecture texte intégrale': safe.replace(' const reader = req.body?.getReader();', ' const rawDirect = await req.text();'),
            'MIME JSON par préfixe': safe.replace("if (contentType !== 'application/json')", "if (!contentType.startsWith('application/json'))"),
            'annulation retirée': safe.replace('try{await reader.cancel()}catch{} ', ''),
            'UTF-8 non strict': safe.replace("new TextDecoder('utf-8', { fatal: true })", "new TextDecoder('utf-8')"),
            'log erreur brut': safe.replace("console.error('[security-context]', { code: 'SECURITY_CONTEXT_FAILED' });", "console.error('[security-context]', error);"),
            'no-store retiré': safe.replace("'Cache-Control': 'private, no-store, max-age=0',", ''),
            'limite augmentée': safe.replace('MAX_REQUEST_BYTES = 4096;', 'MAX_REQUEST_BYTES = 40960;'),
            'IP brute': safe.replace("const country=req.headers.get('cf-ipcountry');", "const country=req.headers.get('cf-connecting-ip');"),
            'GPS précis': safe.replace("const region=req.headers.get('x-sinjira-region');", "const region=req.headers.get('x-sinjira-region');\n const latitude = 48.0;"),
            'corps avant auth': safe.replace('  const user = await requiredUser(req);\n  const sessionId = sessionIdFromVerifiedRequest(req);\n  const parsed = await readLimitedJson(req);', '  const parsed = await readLimitedJson(req);\n  const user = await requiredUser(req);\n  const sessionId = sessionIdFromVerifiedRequest(req);'),
            'corps avant session': safe.replace('  const sessionId = sessionIdFromVerifiedRequest(req);\n  const parsed = await readLimitedJson(req);', '  const parsed = await readLimitedJson(req);\n  const sessionId = sessionIdFromVerifiedRequest(req);'),
        }
        for label, mutated in source_mutations.items():
            if mutated == safe:
                raise AssertionError(f'Mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            workflow_path.write_text(safe_workflow, encoding='utf-8')
            if not validate(path, workflow_path):
                raise AssertionError(f'Régression non détectée: {label}')

        path.write_text(safe, encoding='utf-8')
        workflow_mutations = {
            'permissions écriture': safe_workflow.replace('contents: read', 'contents: write', 1),
            'checkout non épinglé': safe_workflow.replace(CHECKOUT_SHA, 'actions/checkout@main', 1),
            'setup-python non épinglé': safe_workflow.replace(SETUP_PYTHON_SHA, 'actions/setup-python@main', 1),
            'auto-test retiré': safe_workflow.replace(
                '      - run: python3 scripts/validate_security_context_request_security.py --self-test\n',
                '      - run: echo self-test-retiré\n',
                1,
            ),
            'validation retirée': safe_workflow.replace(
                '      - run: python3 scripts/validate_security_context_request_security.py\n',
                '      - run: echo validation-retirée\n',
                1,
            ),
            'trigger fonction retiré': safe_workflow.replace(f"      - '{WATCHED_PATHS[0]}'", "      - 'supabase/functions/security-context/index.disabled'", 1),
        }
        for label, mutated_workflow in workflow_mutations.items():
            if mutated_workflow == safe_workflow:
                raise AssertionError(f'Mutation workflow sans effet: {label}')
            workflow_path.write_text(mutated_workflow, encoding='utf-8')
            if not validate(path, workflow_path):
                raise AssertionError(f'Régression workflow non détectée: {label}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide les bornes HTTP, les logs, la confidentialité et le workflow CI de security-context.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print('OK auto-test security-context: code et workflow protégés.')
        return 0

    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC security-context: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK security-context: JWT/session avant corps, JSON exact borné à 4 KiB pendant la lecture, logs fixes, no-store, aucune IP brute/GPS et workflow CI verrouillé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
