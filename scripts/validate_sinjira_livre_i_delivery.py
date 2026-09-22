#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'projets/sinjira/codex/livre-i-delivery-contract.json'
DOWNLOAD = ROOT / 'supabase/functions/get-private-book-url/index.ts'
READER = ROOT / 'supabase/functions/get-private-book-reading-url/index.ts'
HELPER = ROOT / 'supabase/functions/_shared/privateBook.ts'
CONFIG = ROOT / 'supabase/config.toml'
GENERIC_EDGE = ROOT / 'supabase/functions/get-document-url/index.ts'

FULL_BASENAME = 'SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf'
FULL_SHA256 = '9862a11000fe46a2010e7fb902b9bba3dfea70724855a6fb682e0a6192df88e3'
DEMO_BASENAME = 'SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf'
DEMO_SHA256 = 'aad491ce8861928c561caa035fe5ee8cb16d42a8e307c93828758346cc93f26f'
PRODUCT_SLUG = 'sinjira-livre-01-la-cendre-du-jugement'
STATIC_EXTENSIONS = {'.html', '.js', '.mjs', '.css', '.json', '.xml', '.webmanifest', '.txt'}
SKIP_PARTS = {'codex', '.git', 'node_modules'}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def iter_static_text_files(root: Path):
    roots = (
        root / 'projets/sinjira',
        root / 'assets',
        root / 'sitemap.xml',
        root / 'robots.txt',
        root / 'manifest.webmanifest',
    )
    for candidate in roots:
        if not candidate.exists():
            continue
        paths = (candidate,) if candidate.is_file() else candidate.rglob('*')
        for path in paths:
            if not path.is_file():
                continue
            if candidate.is_dir() and path.suffix.lower() not in STATIC_EXTENSIONS:
                continue
            relative = path.relative_to(root)
            if any(part in SKIP_PARTS for part in relative.parts):
                continue
            yield path


def require_fragments(text: str, fragments: dict[str, str], prefix: str, errors: list[str]) -> None:
    for label, fragment in fragments.items():
        if fragment not in text:
            errors.append(f'{prefix}: {label} absent.')


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    contract_path = root / 'projets/sinjira/codex/livre-i-delivery-contract.json'
    try:
        contract = json.loads(contract_path.read_text('utf-8'))
    except Exception as exc:
        return [f'Contrat Livre I illisible: {exc}']

    expected = {
        ('schema',): 'sinjira.livre-i.delivery.v2',
        ('publication_state',): 'prepared_not_deployed',
        ('human_gate_required',): True,
        ('demo', 'pages'): 83,
        ('demo', 'sha256'): DEMO_SHA256,
        ('full_edition', 'pages'): 1066,
        ('full_edition', 'sha256'): FULL_SHA256,
        ('full_edition', 'public_repository_allowed'): False,
        ('full_edition', 'public_static_url_allowed'): False,
        ('full_edition', 'delivery'): 'authenticated_private_storage_only',
        ('full_edition', 'download_endpoint'): 'get-private-book-url',
        ('full_edition', 'reader_endpoint'): 'get-private-book-reading-url',
        ('full_edition', 'reader_page'): '/projets/sinjira/romans/lire-integral.html',
        ('full_edition', 'entitlement_table'): 'user_entitlements',
        ('full_edition', 'entitlement_client_mutation_allowed'): False,
        ('full_edition', 'entitlement_anonymous_read_allowed'): False,
        ('full_edition', 'product_slug'): PRODUCT_SLUG,
        ('full_edition', 'owner_role_creates_entitlement'): False,
        ('full_edition', 'family_access_creates_entitlement'): False,
        ('full_edition', 'child_full_edition_access_allowed'): False,
        ('full_edition', 'client_role_assertion_allowed'): False,
        ('full_edition', 'activation_env'): 'SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED',
        ('full_edition', 'signed_url_seconds'): 300,
        ('full_edition', 'signed_url_max_seconds'): 600,
        ('full_edition', 'reader_signed_url_refresh'): True,
        ('full_edition', 'reader_progress_storage'): 'local_device_only',
        ('full_edition', 'activation_requires_explicit_human_decision'): True,
        ('full_edition', 'production_deployment_authorized'): False,
    }
    for keys, expected_value in expected.items():
        current = contract
        try:
            for key in keys:
                current = current[key]
        except (KeyError, TypeError):
            errors.append('Contrat Livre I incomplet: ' + '.'.join(keys))
            continue
        if current != expected_value:
            errors.append(
                f"Contrat Livre I inattendu pour {'.'.join(keys)}: {current!r} != {expected_value!r}"
            )

    access_sources = contract.get('full_edition', {}).get('access_sources', [])
    if access_sources != ['canonical_product_right', 'server_verified_owner_role', 'server_verified_creator_family']:
        errors.append('Les sources d’accès doivent rester droit produit canonique + owner serveur + famille V25.')
    product_sources = contract.get('full_edition', {}).get('canonical_product_right_sources', [])
    if product_sources != ['active_product_entitlement', 'paid_order']:
        errors.append('Le droit produit canonique doit couvrir entitlement actif + commande paid uniquement.')

    demo_url = str(contract.get('demo', {}).get('public_url', ''))
    if not demo_url.endswith('/projets/sinjira/documents/' + DEMO_BASENAME):
        errors.append("L'URL publique stable de la démo n'est plus celle attendue.")

    signed_seconds = int(contract.get('full_edition', {}).get('signed_url_seconds', 999999))
    signed_max = int(contract.get('full_edition', {}).get('signed_url_max_seconds', 0))
    if signed_seconds > signed_max:
        errors.append('La durée de l’URL signée dépasse le maximum du contrat.')

    # L'intégrale ne doit jamais se retrouver dans le dépôt public, par nom ou par octets.
    for path in root.rglob(FULL_BASENAME):
        if path.is_file() and '.git' not in path.parts:
            errors.append(f'Édition intégrale interdite dans le dépôt public: {path.relative_to(root)}')
    for pdf in root.rglob('*.pdf'):
        if '.git' in pdf.parts or not pdf.is_file():
            continue
        try:
            digest = sha256_file(pdf)
        except OSError:
            continue
        if digest == FULL_SHA256:
            errors.append(f'Octets de l’édition intégrale détectés dans le dépôt public: {pdf.relative_to(root)}')

    for path in iter_static_text_files(root):
        try:
            text = path.read_text('utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        relative = path.relative_to(root)
        if FULL_BASENAME in text:
            errors.append(f'Lien/référence statique vers l’intégrale détecté: {relative}')
        if FULL_SHA256 in text:
            errors.append(f'Empreinte de l’intégrale injectée dans un actif public: {relative}')

    files = {
        'download': root / 'supabase/functions/get-private-book-url/index.ts',
        'reader': root / 'supabase/functions/get-private-book-reading-url/index.ts',
        'helper': root / 'supabase/functions/_shared/privateBook.ts',
        'config': root / 'supabase/config.toml',
        'generic': root / 'supabase/functions/get-document-url/index.ts',
    }
    try:
        texts = {name: path.read_text('utf-8') for name, path in files.items()}
    except OSError as exc:
        return errors + [f'Frontière privée illisible: {exc}']

    # Préserve les invariants historiques de la porte générique. La V2 Livre I
    # complète ces gardes; elle ne les remplace jamais.
    require_fragments(
        texts['generic'],
        {
            'authentification/résolution utilisateur': 'optionalUser(req)',
            'client serveur pour décision d’accès': 'serviceClient()',
            'contrôle du rang d’accès': 'userRank<(ranks[doc.access_level]||999)',
            'URL signée de courte durée': 'createSignedUrl(doc.storage_path,600)',
            'réponse privée non mise en cache': "'Cache-Control':'private, no-store, max-age=0'",
            'protection MIME': "'X-Content-Type-Options':'nosniff'",
        },
        'Frontière générique affaiblie',
        errors,
    )
    if 'getPublicUrl(' in texts['generic']:
        errors.append('get-document-url ne doit jamais produire une URL publique de Storage.')

    for name in ('download', 'reader'):
        source = texts[name]
        require_fragments(
            source,
            {
                'utilisateur authentifié': 'requiredUser(req)',
                'client serveur': 'serviceClient()',
                'bande âge serveur': "service.rpc('sinjira_age_band',{p_user_id:user.id})",
                'refus 11–12': "if(normalizedAgeBand==='child')",
                'bande standard bornée': "if(!['adult','youth'].includes(normalizedAgeBand))",
                'autorisation owner/famille/produit': 'requirePrivateBookAccess(service,user.id)',
                'stockage privé serveur': 'privateBookStorageConfig()',
                'réponse privée non mise en cache': "'Cache-Control':'private, no-store, max-age=0'",
                'URL signée privée': '.createSignedUrl(storage.storagePath,LIVRE_I_SIGNED_URL_SECONDS',
            },
            f'Porte privée {name} affaiblie',
            errors,
        )
        auth_pos = source.find('requiredUser(req)')
        service_pos = source.find('serviceClient()')
        age_pos = source.find("service.rpc('sinjira_age_band',{p_user_id:user.id})")
        child_pos = source.find("if(normalizedAgeBand==='child')")
        access_pos = source.find('requirePrivateBookAccess(service,user.id)')
        storage_pos = source.find('privateBookStorageConfig()')
        signed_pos = source.find('.createSignedUrl(storage.storagePath,LIVRE_I_SIGNED_URL_SECONDS')
        if not (0 <= auth_pos < service_pos < age_pos < child_pos < access_pos < storage_pos < signed_pos):
            errors.append(
                f'{name}: ordre attendu auth -> âge -> autorisation -> stockage -> URL signée non respecté.'
            )
        if 'getPublicUrl(' in source or 'external_url' in source:
            errors.append(f'{name}: repli public/externe interdit.')

    helper = texts['helper']
    require_fragments(
        helper,
        {
            'rôle auteur/propriétaire serveur': "service.rpc('is_sinjira_owner',{p_user_id:userId})",
            'rôle auteur reconnu uniquement côté serveur': "if(isOwner===true)return 'owner'",
            'catalogue famille serveur': "'sinjira_has_full_catalog_access'",
            'famille reconnue uniquement côté serveur': "if(fullCatalog===true)return 'family'",
            'droit produit canonique': "'has_sinjira_product'",
            'droit produit lié au Livre I et à la personne': "{p_product_slug:LIVRE_I_PRODUCT_SLUG,p_user_id:userId}",
            'droit produit booléen strict': "if(hasProduct===true)return 'product'",
            'TTL signé exact': 'LIVRE_I_SIGNED_URL_SECONDS=300',
        },
        'Helper d’autorisation affaibli',
        errors,
    )
    if 'getPublicUrl(' in helper:
        errors.append('helper: stockage public interdit.')
    if ".from('user_entitlements')" in helper:
        errors.append('helper: lecture directe user_entitlements interdite; utiliser has_sinjira_product.')
    if "{download:" in texts['reader']:
        errors.append('Le lecteur ne doit pas forcer le téléchargement du PDF.')
    if "{download:'SINJIRA_Livre_01_La_Cendre_du_Jugement.pdf'}" not in texts['download']:
        errors.append('Le téléchargement doit rester explicitement attaché.')

    for function_name in ('get-private-book-url', 'get-private-book-reading-url'):
        marker = f'[functions.{function_name}]\nverify_jwt = true'
        if marker not in texts['config']:
            errors.append(f'{function_name}: verify_jwt=true requis dans config.toml.')

    return errors


def self_test() -> None:
    clean = validate(ROOT)
    if clean:
        raise AssertionError('Le cas réel sain doit passer: ' + ' | '.join(clean))

    with TemporaryDirectory() as raw:
        root = Path(raw)
        rels = (
            'projets/sinjira/codex/livre-i-delivery-contract.json',
            'supabase/functions/get-private-book-url/index.ts',
            'supabase/functions/get-private-book-reading-url/index.ts',
            'supabase/functions/_shared/privateBook.ts',
            'supabase/functions/get-document-url/index.ts',
            'supabase/config.toml',
        )
        for rel in rels:
            src = ROOT / rel
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())

        (root / 'projets/sinjira/documents').mkdir(parents=True, exist_ok=True)
        leaked = root / 'projets/sinjira/documents' / FULL_BASENAME
        leaked.write_bytes(b'not-real-pdf')
        if not any('Édition intégrale interdite' in item for item in validate(root)):
            raise AssertionError('Nom intégral public non détecté.')
        leaked.unlink()

        public_page = root / 'projets/sinjira/index.html'
        public_page.parent.mkdir(parents=True, exist_ok=True)
        public_page.write_text(f'<a href="{FULL_BASENAME}">x</a>', encoding='utf-8')
        if not any('référence statique' in item for item in validate(root)):
            raise AssertionError('Lien statique intégral non détecté.')
        public_page.unlink()

        helper = root / 'supabase/functions/_shared/privateBook.ts'
        helper.write_text(helper.read_text('utf-8') + '\ngetPublicUrl("x");\n', encoding='utf-8')
        if not any('stockage public' in item for item in validate(root)):
            raise AssertionError('Repli public privé non détecté.')
        helper.write_bytes((ROOT / 'supabase/functions/_shared/privateBook.ts').read_bytes())

        generic = root / 'supabase/functions/get-document-url/index.ts'
        original_generic = generic.read_text('utf-8')
        generic.write_text(original_generic.replace('userRank<(ranks[doc.access_level]||999)', 'true', 1), encoding='utf-8')
        if not any('contrôle du rang d’accès' in item for item in validate(root)):
            raise AssertionError('Affaiblissement de la porte générique non détecté.')

        generic.write_text(original_generic, encoding='utf-8')
        reader = root / 'supabase/functions/get-private-book-reading-url/index.ts'
        source = reader.read_text('utf-8')
        source = source.replace(
            '    await requirePrivateBookAccess(service,user.id);\n\n    // L\'état de la livraison privée n\'est révélé qu\'à un compte déjà autorisé.\n    const storage=privateBookStorageConfig();',
            "    const storage=privateBookStorageConfig();\n    await requirePrivateBookAccess(service,user.id);",
            1,
        )
        reader.write_text(source, encoding='utf-8')
        if not any('ordre attendu auth -> âge -> autorisation -> stockage' in item for item in validate(root)):
            raise AssertionError('Révélation du stockage avant autorisation non détectée.')

    print('OK auto-test frontière Livre I V2: anciennes et nouvelles barrières conservées.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la frontière publique/privée du Livre I de SINJIRA.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    errors = validate()
    if errors:
        print('ÉCHEC frontière Livre I:')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK Livre I V2: démo publique, intégrale privée, âge puis owner/famille/droit produit canonique entitlement+paid, production non déployée.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
