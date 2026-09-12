#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/admin-sinjira-v18/index.ts'
LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*262_?144\s*;')
SIGNED_URL_RE = re.compile(r'createSignedUrl\([^\n]*?,\s*(\d+)\s*\)')

REQUIRED = {
    'POST uniquement': "req.method!=='POST'",
    'admin/JWT/AAL2 explicite': 'requiredAdmin(req)',
    'lecture JSON bornée': 'readBoundedJson(req)',
    'contrôle Content-Length': "req.headers.get('content-length')",
    'Content-Length fail-closed': '!Number.isFinite(declared)||declared<0||declared>MAX_REQUEST_BYTES',
    'lecture bornée par flux': 'req.body?.getReader()',
    'annulation au dépassement': 'reader.cancel()',
    'décodage UTF-8 strict': "new TextDecoder('utf-8',{fatal:true})",
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma':'no-cache'",
    'nosniff': "'X-Content-Type-Options':'nosniff'",
    'no-referrer': "'Referrer-Policy':'no-referrer'",
    'sources privées listées uniquement côté admin': "account_email,status,source_payload,photo_path,source_purged_at",
    'bucket source privé': "s.storage.from('sinjira-character-sources')",
    'purge source explicite': "if(a==='purge_submission_source')",
    'suppression photo source': "remove([sub.photo_path])",
    'effacement payload source': 'source_payload:null,photo_path:null,source_purged_at:new Date().toISOString()',
    'confirmation humaine CANON': "canonStatus==='CANON'&&c.author_confirmed_canon!==true",
    'erreur confirmation CANON': 'CANON_CONFIRMATION_REQUIRED',
    'Livre I verrouillé': "novel?.slug==='la-cendre-du-jugement'",
    'confirmation humaine retcon': 'c.author_confirmed_retcon!==true',
    'erreur retcon Livre I': 'ROMAN1_LOCKED',
    'IA distante désactivée': 'REMOTE_AI_DISABLED_FREE_ONLY',
    'santé confirme IA distante inactive': 'remote_ai:false,free_only:true',
    'MFA explicite': "e?.message==='MFA_REQUIRED'",
    'état MFA fermé': "e?.message==='MFA_STATE_UNAVAILABLE'",
    'requête trop grande': "e?.message==='REQUEST_TOO_LARGE'",
    'type JSON requis': "e?.message==='JSON_REQUIRED'",
    'JSON invalide': "e?.message==='INVALID_JSON'",
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'lecture texte intégrale avant borne': 'await req.text()',
    'helper JSON générique cacheable': 'return json(',
    'import helper JSON générique': 'corsHeaders,json',
    'auth utilisateur simple': 'requiredUser(req)',
    'service client recréé': 'serviceClient()',
}

PRIVATE_RESPONSE_MARKERS = [
    'return privateJson({ok:true,submissions:rows});',
    'return privateJson({ok:true,rows:data||[]});',
    'return privateJson({ok:true,characters:(chars||[]).map((x:any)=>({...x,novel_title:x.novels?.title||\'\'})),novels:novels||[]});',
    'return privateJson({ok:true,contexts});',
    'return privateJson({ok:true,character:data});',
]


def validate(path: Path) -> list[str]:
    try:
        source = path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'admin-sinjira-v18 illisible: {exc}']

    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde admin-sinjira-v18 absent: {label}.')
    if not LIMIT_RE.search(source):
        errors.append('Garde admin-sinjira-v18 absent ou affaibli: requête exactement bornée à 262144 octets.')

    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde admin-sinjira-v18 violé: {label}.')

    auth_pos = source.find('const {user,service:s}=await requiredAdmin(req);')
    body_pos = source.find('const b=await readBoundedJson(req)')
    if auth_pos < 0 or body_pos < 0:
        errors.append('Ordre admin/corps impossible à vérifier.')
    elif auth_pos > body_pos:
        errors.append('Le corps ne doit pas être lu avant la validation admin/JWT/AAL2.')

    signed_ttls = [int(value) for value in SIGNED_URL_RE.findall(source)]
    if not signed_ttls:
        errors.append('Aucune durée de lien signé photo détectée.')
    elif any(ttl > 600 for ttl in signed_ttls):
        errors.append('Les liens signés des sources personnages ne doivent pas dépasser 600 secondes.')

    if source.count('return new Response(') != 2:
        errors.append('Une réponse métier contourne privateJson; seuls le helper privateJson et OPTIONS peuvent utiliser directement new Response.')

    for marker in PRIVATE_RESPONSE_MARKERS:
        if marker not in source:
            errors.append('Une réponse sensible V18 ne passe plus explicitement par privateJson/no-store.')

    purge_pos = source.find("if(a==='purge_submission_source')")
    remove_pos = source.find("remove([sub.photo_path])", purge_pos)
    clear_pos = source.find('source_payload:null,photo_path:null,source_purged_at:new Date().toISOString()', purge_pos)
    if purge_pos < 0 or remove_pos < 0 or clear_pos < 0 or remove_pos > clear_pos:
        errors.append('La purge doit supprimer le fichier privé avant d’effacer les références et le payload source.')

    if "if(a==='generate_character')" not in source or 'REMOTE_AI_DISABLED_FREE_ONLY' not in source:
        errors.append('La génération distante de personnage doit rester explicitement désactivée.')

    return errors


def self_test() -> None:
    real = EDGE.read_text('utf-8', errors='strict')
    clean = validate(EDGE)
    if clean:
        raise AssertionError('Le fichier réel sain doit passer: ' + ' | '.join(clean))

    cases = {
        'json direct': real.replace('const b=await readBoundedJson(req)', 'const b=await req.json()', 1),
        'texte intégral réintroduit': real.replace('const reader=req.body?.getReader();', 'const rawDirect=await req.text();', 1),
        'annulation retirée': real.replace('try{await reader.cancel()}catch{/* Le rejet de taille reste prioritaire. */}', '', 1),
        'décodage non strict': real.replace("new TextDecoder('utf-8',{fatal:true})", "new TextDecoder('utf-8')", 1),
        'Content-Length permissif': real.replace(
            "if(!Number.isFinite(declared)||declared<0||declared>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');",
            "if(Number.isFinite(declared)&&declared>MAX_REQUEST_BYTES)throw new Error('REQUEST_TOO_LARGE');",
            1,
        ),
        'no-store retiré': real.replace("'Cache-Control':'private, no-store, max-age=0',", '', 1),
        'limite augmentée': real.replace('MAX_REQUEST_BYTES=262144;', 'MAX_REQUEST_BYTES=1048576;', 1),
        'admin explicite retiré': real.replace("const {user,service:s}=await requiredAdmin(req);", "const user=await requiredUser(req),s=serviceClient();", 1),
        'ordre inversé': real.replace(
            "const {user,service:s}=await requiredAdmin(req);\n    const b=await readBoundedJson(req)",
            "const b=await readBoundedJson(req);\n    const {user,service:s}=await requiredAdmin(req)\n    const a=String(b.action||'')",
            1,
        ),
        'lien photo prolongé': real.replace('createSignedUrl(sub.photo_path,600)', 'createSignedUrl(sub.photo_path,3600)', 1),
        'sources rendues cacheables': real.replace(
            'return privateJson({ok:true,submissions:rows});',
            'return new Response(JSON.stringify({ok:true,submissions:rows}));',
            1,
        ),
        'purge payload retirée': real.replace('source_payload:null,photo_path:null,source_purged_at:new Date().toISOString()', 'source_purged_at:new Date().toISOString()', 1),
        'suppression photo retirée': real.replace("remove([sub.photo_path])", "list(sub.photo_path)", 1),
        'confirmation CANON retirée': real.replace("if(canonStatus==='CANON'&&c.author_confirmed_canon!==true)throw new Error('CANON_CONFIRMATION_REQUIRED');", '', 1),
        'confirmation retcon retirée': real.replace("&&c.author_confirmed_retcon!==true", '', 1),
        'IA distante réactivée': real.replace('REMOTE_AI_DISABLED_FREE_ONLY', 'REMOTE_AI_ENABLED', 1),
    }

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'index.ts'
        for label, mutated in cases.items():
            if mutated == real:
                raise AssertionError(f'Auto-test invalide, mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Affaiblissement non détecté: {label}')
    print(f'OK auto-test admin-sinjira-v18: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide les bornes HTTP, la confidentialité et les décisions humaines de admin-sinjira-v18.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC sécurité admin-sinjira-v18: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK admin-sinjira-v18: admin/JWT/AAL2 avant corps, JSON 256 KiB borné pendant la lecture, réponses no-store, sources privées et décisions CANON/retcon humaines conservées.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
