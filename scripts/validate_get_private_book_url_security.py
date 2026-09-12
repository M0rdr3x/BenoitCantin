#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/get-private-book-url/index.ts'
CONFIG = ROOT / 'supabase/config.toml'

REQUIRED = {
    'POST uniquement': "req.method!=='POST'",
    'auth utilisateur': 'const user=await requiredUser(req);',
    'stockage après auth': 'const storage=privateStorageConfig();',
    'drapeau activation privé': "SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED",
    'bucket privé serveur': 'SINJIRA_LIVRE_I_PRIVATE_BUCKET',
    'chemin privé serveur': 'SINJIRA_LIVRE_I_PRIVATE_PATH',
    'slug Livre I exact': "const PRODUCT_SLUG='sinjira-livre-01-la-cendre-du-jugement';",
    'TTL signé exact': 'const SIGNED_URL_SECONDS=300;',
    'entitlement compte': ".eq('user_id',user.id)",
    'entitlement produit': ".eq('product_id',product.id)",
    'URL signée': '.createSignedUrl(storage.storagePath,SIGNED_URL_SECONDS',
    'cache privé': "'Cache-Control':'private, no-store, max-age=0'",
    'pragma no-cache': "'Pragma':'no-cache'",
    'nosniff': "'X-Content-Type-Options':'nosniff'",
    'no-referrer': "'Referrer-Policy':'no-referrer'",
    'log entitlement fixe': "console.error('[get-private-book-url]',{code:'BOOK_ENTITLEMENT_CHECK_FAILED'});",
    'log URL fixe': "console.error('[get-private-book-url]',{code:'BOOK_SIGNED_URL_FAILED'});",
    'log config fixe': "console.error('[get-private-book-url]',{code:'BOOK_PRIVATE_STORAGE_NOT_CONFIGURED'});",
    'log global fixe': "console.error('[get-private-book-url]',{code:'BOOK_PRIVATE_DELIVERY_FAILED'});",
}

FORBIDDEN = {
    'repli URL externe': 'external_url',
    'repli stockage public': 'getPublicUrl(',
    'log entitlement brut': "console.error('[SINJIRA Livre I] vérification du droit impossible',entitlementError)",
    'log storage brut': "console.error('[SINJIRA Livre I] création URL signée impossible',signedError)",
    'log catch brut': "console.error('[SINJIRA Livre I] erreur téléchargement privé',error)",
    'objet entitlement loggé': 'console.error(entitlementError)',
    'objet storage loggé': 'console.error(signedError)',
    'objet erreur loggé': 'console.error(error)',
}


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def config_stanza(config: str) -> str:
    marker = '[functions.get-private-book-url]'
    if marker not in config:
        return ''
    return config.split(marker, 1)[1].split('[functions.', 1)[0]


def validate_text(source: str, config: str) -> list[str]:
    errors: list[str] = []
    for label, marker in REQUIRED.items():
        require(errors, marker in source, f'Garde Livre I privé absent: {label}.')
    for label, marker in FORBIDDEN.items():
        require(errors, marker not in source, f'Garde Livre I privé violé: {label}.')

    auth_pos = source.find('const user=await requiredUser(req);')
    storage_pos = source.find('const storage=privateStorageConfig();')
    service_pos = source.find('const service=serviceClient();')
    require(errors, auth_pos >= 0 and storage_pos > auth_pos,
            'L’identité doit être validée avant de révéler l’état du stockage privé.')
    require(errors, service_pos > storage_pos,
            'Le client service ne doit être construit qu’après auth et validation du stockage privé.')

    entitlement_pos = source.find(".from('user_entitlements')")
    signed_pos = source.find('.createSignedUrl(storage.storagePath,SIGNED_URL_SECONDS')
    require(errors, entitlement_pos > service_pos and signed_pos > entitlement_pos,
            'L’URL signée doit être créée seulement après validation de l’entitlement du compte.')

    console_lines = [line.strip() for line in source.splitlines() if 'console.' in line]
    expected_console_lines = [
        "console.error('[get-private-book-url]',{code:'BOOK_ENTITLEMENT_CHECK_FAILED'});",
        "console.error('[get-private-book-url]',{code:'BOOK_SIGNED_URL_FAILED'});",
        "console.error('[get-private-book-url]',{code:'BOOK_PRIVATE_STORAGE_NOT_CONFIGURED'});",
        "console.error('[get-private-book-url]',{code:'BOOK_PRIVATE_DELIVERY_FAILED'});",
    ]
    require(errors, console_lines == expected_console_lines,
            'Les logs du Livre I privé doivent rester limités aux codes fixes approuvés.')

    stanza = config_stanza(config)
    require(errors, bool(stanza), 'Stanza [functions.get-private-book-url] absente de supabase/config.toml.')
    require(errors, 'verify_jwt = true' in stanza, 'get-private-book-url doit conserver verify_jwt=true.')
    require(errors, 'verify_jwt = false' not in stanza, 'verify_jwt=false interdit pour get-private-book-url.')
    return errors


def validate(edge_path: Path = EDGE, config_path: Path = CONFIG) -> list[str]:
    try:
        source = edge_path.read_text('utf-8', errors='strict')
    except OSError as exc:
        return [f'get-private-book-url illisible: {exc}']
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

    ordered = """    const user=await requiredUser(req);
    const storage=privateStorageConfig();
"""
    reversed_order = """    const storage=privateStorageConfig();
    const user=await requiredUser(req);
"""

    source_mutations = {
        'auth après stockage': source.replace(ordered, reversed_order, 1),
        'auth retirée': source.replace('const user=await requiredUser(req);', "const user={id:'bypass'};", 1),
        'POST retiré': source.replace("  if(req.method!=='POST')return privateJson({ok:false,error:'Méthode non autorisée.'},405);\n", '', 1),
        'no-store retiré': source.replace("  'Cache-Control':'private, no-store, max-age=0',\n", '', 1),
        'TTL élargi': source.replace('SIGNED_URL_SECONDS=300', 'SIGNED_URL_SECONDS=3600', 1),
        'filtre utilisateur retiré': source.replace("      .eq('user_id',user.id)\n", '', 1),
        'filtre produit retiré': source.replace("      .eq('product_id',product.id)\n", '', 1),
        'activation privée retirée': source.replace("  const enabled=Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED')==='true';\n", "  const enabled=true;\n", 1),
        'repli public ajouté': source.replace('    return privateJson({\n      ok:true,', "    service.storage.from(storage.bucket).getPublicUrl(storage.storagePath);\n    return privateJson({\n      ok:true,", 1),
        'log entitlement brut': source.replace("console.error('[get-private-book-url]',{code:'BOOK_ENTITLEMENT_CHECK_FAILED'});", "console.error(entitlementError);", 1),
        'log storage brut': source.replace("console.error('[get-private-book-url]',{code:'BOOK_SIGNED_URL_FAILED'});", "console.error(signedError);", 1),
        'log catch brut': source.replace("console.error('[get-private-book-url]',{code:'BOOK_PRIVATE_DELIVERY_FAILED'});", "console.error(error);", 1),
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
                '[functions.get-private-book-url]\nverify_jwt = true',
                '[functions.get-private-book-url]\nverify_jwt = false',
                1,
            ),
            'stanza retirée': config.replace(
                '[functions.get-private-book-url]\nverify_jwt = true\n\n',
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

    print(f'OK auto-tests Livre I privé: {len(source_mutations) + len(config_mutations)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la frontière privée de get-private-book-url.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate()
    if errors:
        print(f'ÉCHEC Livre I privé: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK Livre I privé: auth avant état du stockage, entitlement compte/produit, URL signée 300 s, aucun repli public et logs sanitizés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
