#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/admin-license-codes/index.ts'
REQUEST_LIMIT_RE = re.compile(r'\bMAX_REQUEST_BYTES\s*=\s*4_?096\s*;')
QUANTITY_LIMIT_RE = re.compile(r'\bMAX_QUANTITY\s*=\s*5_?000\s*;')
RAW_CODE_ROW_RE = re.compile(r'rows\.push\s*\(\s*\{[^}]*\bcode\s*:', re.S)

REQUIRED = {
    'version fonctionnelle stable': "const VERSION='24.4.49';",
    'POST uniquement': "req.method!=='POST'",
    'admin explicite': 'requiredAdmin(req)',
    'lecture JSON bornée': 'readLimitedJson(req)',
    'content-type JSON strict': "if(contentType!=='application/json')throw new Error('JSON_REQUIRED');",
    'taille UTF-8 réelle': 'new TextEncoder().encode(raw).byteLength',
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma':'no-cache'",
    'nosniff': "'X-Content-Type-Options':'nosniff'",
    'no-referrer': "'Referrer-Policy':'no-referrer'",
    'pepper serveur': "Deno.env.get('SINJIRA_LICENSE_PEPPER')",
    'hash SHA-256': "crypto.subtle.digest('SHA-256',raw)",
    'persistance hash seulement': 'rows.push({batch_id:batch.id,code_hash:await digest(code,pepper),product_slug:productSlug})',
    'insertion lignes hashées': "s.from('activation_codes').insert(rows)",
    'rollback lot si insertion codes échoue': "s.from('license_batches').delete().eq('id',batch.id)",
    'échec insertion codes explicite': "throw new Error('LICENSE_CODES_INSERT_FAILED')",
    'échec rollback explicite': "throw new Error('LICENSE_BATCH_ROLLBACK_FAILED')",
    'log sanitizé': "console.error('[admin-license-codes]',safeLogCode(e));",
    'fallback log fixe': "return SAFE_LOG_CODES.has(code)?code:'LICENSE_BATCH_FAILED';",
    'codes bruts réponse privée': 'return privateJson({ok:true,batch,codes,warning:',
    'avertissement usage unique': 'Les codes bruts sont retournés une seule fois.',
    'MFA fermé': "e?.message==='MFA_STATE_UNAVAILABLE'",
    'JSON requis réponse explicite': "e?.message==='JSON_REQUIRED'",
}

FORBIDDEN = {
    'lecture JSON directe non bornée': 'await req.json()',
    'helper JSON générique cacheable': 'return json(',
    'import helper JSON générique': 'json} from',
    'auth admin indirecte': 'requiredUser(req)',
    'service client recréé': 'serviceClient()',
    'log objet erreur brut': "console.error('[admin-license-codes]',e);",
}


def validate(path: Path) -> list[str]:
    try:
        source = path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'admin-license-codes illisible: {exc}']

    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append(f'Garde licences admin absent: {label}.')
    if not REQUEST_LIMIT_RE.search(source):
        errors.append('Garde licences admin absent ou affaibli: requête exactement bornée à 4096 octets.')
    if not QUANTITY_LIMIT_RE.search(source):
        errors.append('Garde licences admin absent ou affaibli: quantité maximale exactement 5000.')

    lowered = source.lower()
    for label, marker in FORBIDDEN.items():
        if marker.lower() in lowered:
            errors.append(f'Garde licences admin violé: {label}.')
    if RAW_CODE_ROW_RE.search(source):
        errors.append('Garde licences admin violé: un code brut ne doit jamais être persisté dans activation_codes.')

    auth_pos = source.find('const {user,service:s}=await requiredAdmin(req)')
    body_pos = source.find('const body=await readLimitedJson(req)')
    if auth_pos < 0 or body_pos < 0:
        errors.append('Ordre admin/corps impossible à vérifier.')
    elif auth_pos > body_pos:
        errors.append('Le corps ne doit pas être lu avant la validation admin/JWT/AAL2.')

    pepper_pos = source.find("Deno.env.get('SINJIRA_LICENSE_PEPPER')")
    insert_pos = source.find("s.from('activation_codes').insert(rows)")
    rollback_pos = source.find("s.from('license_batches').delete().eq('id',batch.id)")
    success_pos = source.find('return privateJson({ok:true,batch,codes,warning:')
    if pepper_pos < 0 or insert_pos < 0 or pepper_pos > insert_pos:
        errors.append('Le pepper serveur doit être disponible avant toute persistance des hash de codes.')
    if insert_pos < 0 or rollback_pos < 0 or rollback_pos < insert_pos:
        errors.append('Le rollback du lot doit suivre l’échec potentiel de l’insertion des codes.')
    if success_pos < 0 or rollback_pos < 0 or rollback_pos > success_pos:
        errors.append('Le rollback doit être défini avant toute réponse de génération réussie.')

    return errors


def self_test() -> None:
    real = EDGE.read_text('utf-8', errors='strict')
    clean = validate(EDGE)
    if clean:
        raise AssertionError('Le fichier réel sain doit passer: ' + ' | '.join(clean))

    cases = {
        'json direct': real.replace('const body=await readLimitedJson(req);', 'const body=await req.json();', 1),
        'content-type JSON retiré': real.replace("  if(contentType!=='application/json')throw new Error('JSON_REQUIRED');\n", '', 1),
        'no-store retiré': real.replace("'Cache-Control':'private, no-store, max-age=0',", '', 1),
        'limite requête affaiblie': real.replace('MAX_REQUEST_BYTES=4096;', 'MAX_REQUEST_BYTES=40960;', 1),
        'quantité augmentée': real.replace('MAX_QUANTITY=5000;', 'MAX_QUANTITY=50000;', 1),
        'admin explicite retiré': real.replace('const {user,service:s}=await requiredAdmin(req);', 'const user=await requiredUser(req),s=serviceClient();', 1),
        'ordre inversé': real.replace(
            'const {user,service:s}=await requiredAdmin(req);\n    const body=await readLimitedJson(req);',
            'const body=await readLimitedJson(req);\n    const {user,service:s}=await requiredAdmin(req);',
            1,
        ),
        'code brut persisté': real.replace('code_hash:await digest(code,pepper)', 'code:code', 1),
        'pepper renommé': real.replace("Deno.env.get('SINJIRA_LICENSE_PEPPER')", "Deno.env.get('OTHER_PEPPER')", 1),
        'version dérivée': real.replace("const VERSION='24.4.49';", "const VERSION='24.4.50';", 1),
        'réponse codes cacheable': real.replace('return privateJson({ok:true,batch,codes,warning:', 'return json({ok:true,batch,codes,warning:', 1),
        'rollback lot retiré': real.replace("      const {error:rollbackError}=await s.from('license_batches').delete().eq('id',batch.id);\n", '', 1),
        'échec rollback masqué': real.replace("      if(rollbackError)throw new Error('LICENSE_BATCH_ROLLBACK_FAILED');\n", '', 1),
        'log brut réintroduit': real.replace("console.error('[admin-license-codes]',safeLogCode(e));", "console.error('[admin-license-codes]',e);", 1),
    }

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'index.ts'
        for label, mutated in cases.items():
            if mutated == real:
                raise AssertionError(f'Auto-test invalide, mutation sans effet: {label}')
            path.write_text(mutated, encoding='utf-8')
            if not validate(path):
                raise AssertionError(f'Affaiblissement non détecté: {label}')
    print(f'OK auto-test licences admin: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la confidentialité et la cohérence des codes d’activation administrateur.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    errors = validate(EDGE)
    if errors:
        print(f'ÉCHEC sécurité licences admin: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK licences admin: admin/JWT/AAL2 avant corps, JSON strict 4 KiB, codes no-store, persistance hashée et rollback du lot obligatoires.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
