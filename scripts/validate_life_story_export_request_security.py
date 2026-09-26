#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/life-story-export/index.ts'

REQUIRED = {
    'POST uniquement': "req.method !== 'POST'",
    'administrateur authentifié': 'requiredAdmin(req)',
    'lecture JSON bornée': 'readLimitedJson(req)',
    'MIME JSON exact': "contentType !== 'application/json'",
    'Content-Length numérique strict': "!/^\\d+$/.test(normalizedLength)",
    'Content-Length entier sûr': '!Number.isSafeInteger(declared)',
    'lecture par flux': 'req.body.getReader()',
    'annulation au dépassement': "reader.cancel('REQUEST_TOO_LARGE')",
    'borne pendant le flux': 'if (total > MAX_REQUEST_BYTES)',
    'UTF-8 strict': "new TextDecoder('utf-8', { fatal: true })",
    'réponse privée': "'Cache-Control': 'private, no-store, max-age=0'",
    'désactivation cache historique': "'Pragma': 'no-cache'",
    'protection MIME': "'X-Content-Type-Options': 'nosniff'",
    'référent masqué': "'Referrer-Policy': 'no-referrer'",
    'frontière Histoire de vie': 'assertLifeStoryBoundary(record);',
    'interdiction Registre': 'registry_access_prohibited',
    'jeton de remise en fragment': '`${DELIVERY_PAGE}#${raw}`',
    'stockage du hash du jeton': 'token_hash: tokenHash',
    'transport humain/manual': "transport: 'manual_or_future_sender'",
    'réponse privée succès': 'return privateJson({ ok: true,',
    'réponse privée erreur': "return privateJson({ ok: false, error: 'Opération Histoire de vie refusée.'",
    'allowlist des erreurs métier': 'const SAFE_ERROR_CODES = new Set([',
    'classification des erreurs': 'const { code, status } = classifyExportError(error);',
    'fallback backend fixe': "'LIFE_STORY_EXPORT_FAILED'",
    'log erreur sanitizé': "console.error('[life-story-export]', { code });",
    'code auth sûr': "'AUTH_REQUIRED'",
    'code admin sûr': "'ADMIN_REQUIRED'",
    'code MFA sûr': "'MFA_REQUIRED'",
    'code frontière sûr': "'SOURCE_BOUNDARY_VIOLATION'",
    'code export générable sûr': "'EXPORT_NOT_GENERATABLE'",
    'code export généré sûr': "'EXPORT_NOT_GENERATED'",
    'code destinataires sûr': "'NO_RECIPIENTS'",
}

REQUIRED_PATTERNS = {
    'requête bornée exactement à 4096 octets': re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4_?096\s*;'),
    'erreur backend inconnue en HTTP 500': re.compile(r"code\s*===\s*['\"]LIFE_STORY_EXPORT_FAILED['\"]\s*\?\s*500"),
    'fallback imposé après allowlist': re.compile(r"SAFE_ERROR_CODES\.has\(candidate\)\s*\?\s*candidate\s*:\s*['\"]LIFE_STORY_EXPORT_FAILED['\"]"),
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'lecture JSON directe non bornée espacée': 'await req.json (',
    'lecture texte intégrale non bornée': 'await req.text()',
    'jeton dans la query string': '?token=',
    'lecture du Registre reader_characters': 'reader_characters',
    'lecture du Registre registry_account_links': 'registry_account_links',
    'message backend brut converti en code': 'String(error?.message',
    'message backend brut converti en code direct': 'String(error.message',
    'objet erreur brut journalisé': "console.error('[life-story-export]', error)",
    'objet erreur brut journalisé guillemets doubles': 'console.error("[life-story-export]", error)',
}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        source = path.read_text('utf-8', errors='ignore')
    except OSError as exc:
        return [f'Fonction life-story-export illisible: {exc}']

    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde life-story-export absent: {label}.')
    for label, pattern in REQUIRED_PATTERNS.items():
        if not pattern.search(source):
            errors.append(f'Garde life-story-export absent ou affaibli: {label}.')
    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde life-story-export violé: {label}.')

    parsed_pos = source.find('const parsed = await readLimitedJson(req)')
    admin_pos = source.find('const { service } = await requiredAdmin(req)')
    if parsed_pos < 0 or admin_pos < 0:
        errors.append('Ordre auth/corps impossible à vérifier.')
    elif admin_pos > parsed_pos:
        errors.append('Le corps ne doit pas être lu avant la validation administrateur/JWT.')

    content_type_pos = source.find("contentType !== 'application/json'")
    reader_pos = source.find('req.body.getReader()')
    bound_pos = source.find('if (total > MAX_REQUEST_BYTES)', reader_pos)
    decode_pos = source.find("new TextDecoder('utf-8', { fatal: true })", bound_pos)
    parse_pos = source.find('JSON.parse(', decode_pos)
    if content_type_pos < 0 or reader_pos < 0 or content_type_pos > reader_pos:
        errors.append('Le Content-Type JSON exact doit être vérifié avant la lecture du flux.')
    if reader_pos < 0 or bound_pos < reader_pos or decode_pos < bound_pos or parse_pos < decode_pos:
        errors.append('Le corps doit être borné pendant le flux avant décodage UTF-8 strict puis parsing JSON.')

    if source.count('privateJson(') < 10:
        errors.append('Les réponses sensibles doivent rester uniformément privées et non cachables.')

    return errors


def self_test() -> None:
    with TemporaryDirectory() as raw:
        path = Path(raw) / 'index.ts'
        safe = """
const MAX_REQUEST_BYTES = 4096;
const DELIVERY_PAGE = 'https://www.benoitcantin.com/histoire-de-vie/remise.html';
const PRIVATE_HEADERS = {
  'Cache-Control': 'private, no-store, max-age=0',
  'Pragma': 'no-cache',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
};
const SAFE_ERROR_CODES = new Set([
 'AUTH_REQUIRED', 'ADMIN_REQUIRED', 'MFA_REQUIRED', 'SOURCE_BOUNDARY_VIOLATION',
 'EXPORT_NOT_GENERATABLE', 'EXPORT_NOT_GENERATED', 'NO_RECIPIENTS',
]);
function privateJson(data, status=200){return new Response(JSON.stringify(data),{status,headers:PRIVATE_HEADERS})}
async function readLimitedJson(req){
 const contentType=(req.headers.get('content-type')||'').split(';',1)[0].trim().toLowerCase();
 if(contentType !== 'application/json') return {response:privateJson({},415)};
 const rawLength=req.headers.get('content-length');
 if(rawLength!==null){
  const normalizedLength=rawLength.trim();
  if(!/^\\d+$/.test(normalizedLength)) return {response:privateJson({},413)};
  const declared=Number(normalizedLength);
  if(!Number.isSafeInteger(declared)||declared>MAX_REQUEST_BYTES)return {response:privateJson({},413)};
 }
 if(!req.body)return {body:{}};
 const reader=req.body.getReader();
 const chunks=[]; let total=0;
 while(true){
  const {done,value}=await reader.read();
  if(done)break;
  if(!value)continue;
  total+=value.byteLength;
  if (total > MAX_REQUEST_BYTES) {await reader.cancel('REQUEST_TOO_LARGE');return {response:privateJson({},413)}}
  chunks.push(value);
 }
 const bytes=new Uint8Array(total);
 let offset=0; for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength}
 const text=new TextDecoder('utf-8', { fatal: true }).decode(bytes);
 return {body:JSON.parse(text||'{}')};
}
function classifyExportError(error) {
 const candidate = typeof error === 'object' && error !== null && 'message' in error && typeof error.message === 'string' ? error.message : '';
 const code = SAFE_ERROR_CODES.has(candidate) ? candidate : 'LIFE_STORY_EXPORT_FAILED';
 const status = code === 'AUTH_REQUIRED' ? 401 : code === 'ADMIN_REQUIRED' || code === 'MFA_REQUIRED' ? 403 : code === 'LIFE_STORY_EXPORT_FAILED' ? 500 : 400;
 return { code, status };
}
function assertLifeStoryBoundary(record){
 if(record.registry_access_prohibited !== true) throw new Error('SOURCE_BOUNDARY_VIOLATION');
}
Deno.serve(async (req) => {
 if (req.method !== 'POST') return privateJson({},405);
 try {
  const { service } = await requiredAdmin(req);
  const parsed = await readLimitedJson(req);
  if (parsed.response) return parsed.response;
  const body=parsed.body || {};
  const record={registry_access_prohibited:true};
  assertLifeStoryBoundary(record);
  const raw='a';
  const tokenHash='b';
  const rows=[{token_hash: tokenHash}];
  const responseLinks=[{download_url:`${DELIVERY_PAGE}#${raw}`}];
  const result={transport: 'manual_or_future_sender'};
  if(!body) return privateJson({},400);
  return privateJson({ ok: true, rows, responseLinks, result });
 } catch (error) {
  const { code, status } = classifyExportError(error);
  console.error('[life-story-export]', { code });
  return privateJson({ ok: false, error: 'Opération Histoire de vie refusée.', code }, status);
 }
});
privateJson({});
privateJson({});
privateJson({});
privateJson({});
privateJson({});
privateJson({});
privateJson({});
"""
        path.write_text(safe, encoding='utf-8')
        clean = validate(path)
        if clean:
            raise AssertionError('Le cas sain doit passer: ' + ' | '.join(clean))

        mutations = {
            'JSON direct': safe.replace('const parsed = await readLimitedJson(req);', 'const parsed = {body: await req.json()};', 1),
            'texte intégral': safe.replace('const reader=req.body.getReader();', 'const unsafe=await req.text();\n const reader=req.body.getReader();', 1),
            'MIME préfixe': safe.replace("contentType !== 'application/json'", "!contentType.startsWith('application/json')", 1),
            'Content-Length permissif': safe.replace("if(!/^\\d+$/.test(normalizedLength)) return {response:privateJson({},413)};\n", '', 1),
            'entier sûr retiré': safe.replace('!Number.isSafeInteger(declared)||', '', 1),
            'annulation retirée': safe.replace("await reader.cancel('REQUEST_TOO_LARGE');", '', 1),
            'borne streaming retirée': safe.replace('if (total > MAX_REQUEST_BYTES)', 'if (false)', 1),
            'UTF-8 permissif': safe.replace("new TextDecoder('utf-8', { fatal: true })", "new TextDecoder('utf-8')", 1),
            'no-store retiré': safe.replace("'Cache-Control': 'private, no-store, max-age=0',", '', 1),
            'limite HTTP augmentée': safe.replace('MAX_REQUEST_BYTES = 4096;', 'MAX_REQUEST_BYTES = 40960;', 1),
            'frontière retirée': safe.replace('assertLifeStoryBoundary(record);', '// boundary removed', 1),
            'jeton en query': safe.replace('`${DELIVERY_PAGE}#${raw}`', '`${DELIVERY_PAGE}?token=${raw}`', 1),
            'auth après corps': safe.replace(
                'const { service } = await requiredAdmin(req);\n  const parsed = await readLimitedJson(req);',
                'const parsed = await readLimitedJson(req);\n  const { service } = await requiredAdmin(req);',
                1,
            ),
            'allowlist contournée': safe.replace(
                "const code = SAFE_ERROR_CODES.has(candidate) ? candidate : 'LIFE_STORY_EXPORT_FAILED';",
                "const code = candidate || 'LIFE_STORY_EXPORT_FAILED';",
                1,
            ),
            'message brut en code': safe.replace(
                'const { code, status } = classifyExportError(error);',
                "const code = String(error?.message || 'EXPORT_ERROR'); const status = 400;",
                1,
            ),
            'log brut': safe.replace(
                "console.error('[life-story-export]', { code });",
                "console.error('[life-story-export]', error);",
                1,
            ),
            'fallback 400': safe.replace(
                "code === 'LIFE_STORY_EXPORT_FAILED' ? 500",
                "code === 'LIFE_STORY_EXPORT_FAILED' ? 400",
                1,
            ),
        }
        for label, mutated in mutations.items():
            if mutated == safe:
                raise AssertionError(f'Mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Affaiblissement non détecté: {label}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide les bornes HTTP, la confidentialité et la sanitisation des erreurs de life-story-export.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print('OK auto-test life-story-export streaming.')
        return 0

    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC life-story-export: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK life-story-export: admin/JWT avant corps, JSON 4 KiB borné en streaming, UTF-8 strict, réponses no-store, frontière Histoire de vie et erreurs backend sanitizées.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
