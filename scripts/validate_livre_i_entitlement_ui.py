#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'projets/sinjira/codex/livre-i-delivery-contract.json'
LICENSES = ROOT / 'assets/js/v24-licenses.js'
LIBRARY = ROOT / 'assets/js/sinjira-library-v24-4-61.js'
LIBRARY_HTML = ROOT / 'compte/bibliotheque.html'
READER_JS = ROOT / 'assets/js/sinjira-private-book-reader.js'
READER_HTML = ROOT / 'projets/sinjira/romans/lire-integral.html'
ROMAN_HTML = ROOT / 'projets/sinjira/romans/index.html'
DEMO_HTML = ROOT / 'projets/sinjira/romans/lire-demo.html'

BOOK_SLUG = 'sinjira-livre-01-la-cendre-du-jugement'
READER_PATH = '/projets/sinjira/romans/lire-integral.html'
FULL_BASENAME = 'SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf'

FORBIDDEN_PROMISES = (
    'accès permanent à tous les romans',
    'accès universel côté serveur',
    'accès propriétaire universel',
    'accès total sinjira',
)

BROKEN_COVER_REFS = (
    'sinjira-livre01-couverture-avant.png',
    'sinjira-livre01-couverture-arriere.png',
)


def read(path: Path) -> str:
    return path.read_text('utf-8', errors='ignore')


def validate(
    contract_path: Path = CONTRACT,
    licenses_path: Path = LICENSES,
    library_path: Path = LIBRARY,
    library_html_path: Path = LIBRARY_HTML,
    reader_js_path: Path = READER_JS,
    reader_html_path: Path = READER_HTML,
    roman_html_path: Path = ROMAN_HTML,
    demo_html_path: Path = DEMO_HTML,
) -> list[str]:
    errors: list[str] = []
    try:
        contract = json.loads(read(contract_path))
        licenses = read(licenses_path)
        library = read(library_path)
        library_html = read(library_html_path)
        reader_js = read(reader_js_path)
        reader_html = read(reader_html_path)
        roman_html = read(roman_html_path)
        demo_html = read(demo_html_path)
    except (OSError, ValueError) as exc:
        return [f'Interface Livre I illisible: {exc}']

    full = contract.get('full_edition') or {}
    if contract.get('publication_state') != 'prepared_not_deployed':
        errors.append('Le parcours A1 doit rester prepared_not_deployed avant autorisation de production.')
    if full.get('production_deployment_authorized') is not False:
        errors.append('Le contrat ne doit pas autoriser le déploiement production depuis cette tranche.')
    if full.get('reader_progress_storage') != 'local_device_only':
        errors.append('La progression intégrale doit rester locale à l’appareil par défaut.')
    if full.get('owner_role_creates_entitlement') is not False:
        errors.append('Le rôle auteur/propriétaire ne doit jamais fabriquer un entitlement produit.')
    if full.get('client_role_assertion_allowed') is not False:
        errors.append('Une affirmation de rôle côté client ne doit jamais autoriser le Livre I.')

    required = {
        'Licences: slug Livre I': (licenses, BOOK_SLUG),
        'Bibliothèque: slug Livre I': (library, BOOK_SLUG),
        'Licences: droit réellement reconnu': (licenses, 'Droit numérique reconnu'),
        'Bibliothèque: droit réellement reconnu': (library, 'Droit numérique reconnu'),
        'Licences: droits produit self-only': (licenses, "rpc('sinjira_my_product_rights')"),
        'Bibliothèque: droits produit self-only': (library, "rpc('sinjira_my_product_rights')"),
        'Licences: frontière de diffusion privée expliquée': (licenses, 'diffusion privée'),
        'Bibliothèque: disponibilité privée expliquée': (library, 'La disponibilité de l’intégrale privée est vérifiée séparément dans la section Romans'),
        'Bibliothèque HTML: rôle propriétaire séparé des produits': (
            library_html,
            'Le rôle propriétaire reste distinct des droits numériques attribués aux produits.',
        ),
        'Bibliothèque: chemin lecteur privé': (library, READER_PATH),
        'Bibliothèque: catalogue roman canonique': (library, 'sinjira_my_novel_catalog'),
        'Bibliothèque: full_access serveur': (library, 'const fullAccess=Boolean(novel.full_access);'),
        'Bibliothèque: action intégrale conditionnelle': (library, 'fullAccess?'),
        'Lecteur: session obligatoire avec retour': (reader_js, "requireUser(`/compte/connexion.html?next="),
        'Lecteur: fonction privée générique': (reader_js, "const DELIVERY_FUNCTION='get-private-novel-url'"),
        'Lecteur: slug roman transmis au serveur': (reader_js, 'body:{novel_slug:novelSlug,mode}'),
        'Lecteur: fonction URL lecture privée': (reader_js, "invokeDelivery('read')"),
        'Lecteur: fonction téléchargement privée': (reader_js, "invokeDelivery('download')"),
        'Lecteur: progression locale': (reader_js, 'localStorage.setItem(storageKey'),
        'Lecteur HTML: non indexable': (reader_html, 'content="noindex,nofollow,noarchive"'),
        'Lecteur HTML: politique no-referrer': (reader_html, 'content="no-referrer" name="referrer"'),
        'Lecteur HTML: total de pages contrôlé': (reader_html, 'data-reader-total-pages="1066"'),
        'Roman: lien lecteur intégral générique': (roman_html, 'href="lire-integral.html?novel='),
        'Démo: lien lecteur intégral': (demo_html, 'href="lire-integral.html"'),
    }
    for label, (text, marker) in required.items():
        if marker not in text:
            errors.append(f'{label} absent.')

    combined_account = '\n'.join((licenses, library, library_html)).lower()
    for phrase in FORBIDDEN_PROMISES:
        if phrase in combined_account:
            errors.append(f'Promesse propriétaire trop large interdite: {phrase}.')

    if "from('products').select('slug,name,product_type,active')" in licenses:
        errors.append('La page Licences ne doit pas fabriquer la possession propriétaire depuis tout le catalogue actif.')

    for label,text in (('Licences',licenses),('Bibliothèque',library)):
        for forbidden in ("from('orders')","from('order_items')","from('user_entitlements')"):
            if forbidden in text:
                errors.append(f'{label}: lecture commerciale directe interdite ({forbidden}); utiliser le RPC self-only des droits produit.')

    # La porte de lecture ne doit jamais décider avec un rôle/email client.
    # La Bibliothèque reste une vue de catalogue : aucun appel direct à la
    # livraison privée ne doit réapparaître hors du lecteur dédié.
    for forbidden in (
        'isSinjiraOwner',
        'kingtyrano@gmail.com',
        'clientRole',
        'is_owner_from_client',
        ".from('profiles')",
    ):
        if forbidden in reader_js:
            errors.append(f'Lecteur privé: autorisation client interdite ({forbidden}).')

    for forbidden in (
        'functions.invoke(PRIVATE_NOVEL_FUNCTION',
        'data-private-book-download',
        'function downloadPrivateBook',
        'function bookActions',
        'Accès auteur',
        'BOOK_ONE_NOVEL_SLUG',
    ):
        if forbidden in library:
            errors.append(f'Bibliothèque: action privée ou rôle propriétaire dupliqué interdit ({forbidden}).')

    # Protéger sans surveiller : aucune écriture serveur de progression dans le lecteur intégral.
    for forbidden in (
        "from('sinjira_reader_library')",
        "from('reader_library')",
        '.insert(',
        '.update(',
        '.upsert(',
    ):
        if forbidden in reader_js:
            errors.append(f'Lecteur privé: progression serveur/écriture interdite ({forbidden}).')

    # Les pages publiques peuvent pointer vers la porte privée, mais ne doivent jamais
    # appeler directement les fonctions privées ni embarquer une URL intégrale.
    for label, text in (('Roman', roman_html), ('Démo', demo_html)):
        if 'functions.invoke(' in text:
            errors.append(f'{label}: appel direct à une Edge Function privée interdit dans la page publique.')
        if FULL_BASENAME in text:
            errors.append(f'{label}: nom du PDF intégral interdit dans la page publique.')
        for broken in BROKEN_COVER_REFS:
            if broken in text:
                errors.append(f'{label}: référence de couverture inexistante interdite ({broken}).')

    for label, text in (('Lecteur HTML', reader_html), ('Lecteur JS', reader_js), ('Bibliothèque', library)):
        if FULL_BASENAME in text:
            errors.append(f'{label}: nom statique du fichier intégral interdit.')
        if 'getPublicUrl(' in text:
            errors.append(f'{label}: URL publique Storage interdite.')

    if 'location.assign(String(data.url))' in library:
        errors.append('Bibliothèque: téléchargement privé direct interdit; utiliser uniquement le lecteur dédié.')
    if 'location.assign(String(data.url))' not in reader_js:
        errors.append('Lecteur: le téléchargement doit utiliser uniquement l’URL temporaire renvoyée par le serveur.')

    return errors


def self_test() -> None:
    with TemporaryDirectory() as raw:
        root = Path(raw)
        paths = {
            'contract': root / 'contract.json',
            'licenses': root / 'licenses.js',
            'library': root / 'library.js',
            'library_html': root / 'library.html',
            'reader_js': root / 'reader.js',
            'reader_html': root / 'reader.html',
            'roman': root / 'roman.html',
            'demo': root / 'demo.html',
        }
        paths['contract'].write_text(json.dumps({
            'publication_state': 'prepared_not_deployed',
            'full_edition': {
                'production_deployment_authorized': False,
                'reader_progress_storage': 'local_device_only',
                'owner_role_creates_entitlement': False,
                'client_role_assertion_allowed': False,
            },
        }), encoding='utf-8')
        paths['licenses'].write_text(
            f"const BOOK='{BOOK_SLUG}'; s.rpc('sinjira_my_product_rights'); 'Droit numérique reconnu'; 'diffusion privée';",
            encoding='utf-8',
        )
        paths['library'].write_text(
            f"const BOOK='{BOOK_SLUG}'; const PRIVATE_READER_PATH='{READER_PATH}'; "
            "s.rpc('sinjira_my_product_rights'); s.rpc('sinjira_my_novel_catalog'); "
            "'Droit numérique reconnu'; "
            "'La disponibilité de l’intégrale privée est vérifiée séparément dans la section Romans'; "
            "const fullAccess=Boolean(novel.full_access); "
            "const action=fullAccess?'reader':'none';",
            encoding='utf-8',
        )
        paths['library_html'].write_text(
            'Le rôle propriétaire reste distinct des droits numériques attribués aux produits.',
            encoding='utf-8',
        )
        paths['reader_js'].write_text(
            "const DELIVERY_FUNCTION='get-private-novel-url'; const novelSlug='la-cendre-du-jugement'; "
            "requireUser(`/compte/connexion.html?next=${encodeURIComponent(location.pathname+location.search)}`); "
            "functions.invoke(DELIVERY_FUNCTION,{body:{novel_slug:novelSlug,mode}}); "
            "invokeDelivery('read'); invokeDelivery('download'); "
            "localStorage.setItem(storageKey,String(current)); location.assign(String(data.url));",
            encoding='utf-8',
        )
        paths['reader_html'].write_text(
            '<meta content="noindex,nofollow,noarchive" name="robots"><meta content="no-referrer" name="referrer">'
            '<body data-reader-total-pages="1066"></body>',
            encoding='utf-8',
        )
        paths['roman'].write_text('<a href="lire-integral.html?novel=la-cendre-du-jugement">Lire</a>', encoding='utf-8')
        paths['demo'].write_text('<a href="lire-integral.html">Lire</a>', encoding='utf-8')

        args = tuple(paths[key] for key in ('contract', 'licenses', 'library', 'library_html', 'reader_js', 'reader_html', 'roman', 'demo'))
        clean = validate(*args)
        if clean:
            raise AssertionError('Le cas sain doit passer: ' + ' | '.join(clean))

        paths['licenses'].write_text(
            read(paths['licenses']).replace("s.rpc('sinjira_my_product_rights')","s.from('orders')",1),
            encoding='utf-8',
        )
        direct_orders = validate(*args)
        if not any('lecture commerciale directe interdite' in item for item in direct_orders):
            raise AssertionError('Une lecture directe des commandes depuis Licences doit être bloquée.')

        paths['licenses'].write_text(
            f"const BOOK='{BOOK_SLUG}'; s.rpc('sinjira_my_product_rights'); 'Droit numérique reconnu'; 'diffusion privée';",
            encoding='utf-8',
        )

        healthy_library = read(paths['library'])
        paths['library'].write_text(
            healthy_library + "\nfunctions.invoke(PRIVATE_NOVEL_FUNCTION);",
            encoding='utf-8',
        )
        direct_library_delivery = validate(*args)
        if not any('action privée ou rôle propriétaire dupliqué interdit' in item for item in direct_library_delivery):
            raise AssertionError('Un appel de livraison privée direct depuis la Bibliothèque doit être bloqué.')

        paths['library'].write_text(
            healthy_library.replace(
                'const fullAccess=Boolean(novel.full_access);',
                'const fullAccess=true;',
                1,
            ),
            encoding='utf-8',
        )
        bypass = validate(*args)
        if not any('full_access serveur' in item for item in bypass):
            raise AssertionError('Un contournement du full_access canonique doit être bloqué.')

        paths['library'].write_text(healthy_library, encoding='utf-8')
        paths['reader_js'].write_text(read(paths['reader_js']) + '\nisSinjiraOwner(user);', encoding='utf-8')
        client_owner = validate(*args)
        if not any('autorisation client interdite' in item for item in client_owner):
            raise AssertionError('Une autorisation auteur côté client doit être bloquée.')

        paths['reader_js'].write_text(
            "const DELIVERY_FUNCTION='get-private-novel-url'; const novelSlug='la-cendre-du-jugement'; "
            "requireUser(`/compte/connexion.html?next=${encodeURIComponent(location.pathname+location.search)}`); "
            "functions.invoke(DELIVERY_FUNCTION,{body:{novel_slug:novelSlug,mode}}); "
            "invokeDelivery('read'); invokeDelivery('download'); "
            "localStorage.setItem(storageKey,String(current)); location.assign(String(data.url)); "
            "s.from('sinjira_reader_library').upsert({last_page:1});",
            encoding='utf-8',
        )
        tracking = validate(*args)
        if not any('progression serveur/écriture interdite' in item for item in tracking):
            raise AssertionError('Une synchronisation silencieuse de progression doit être bloquée.')

        paths['reader_js'].write_text(
            "const DELIVERY_FUNCTION='get-private-novel-url'; const novelSlug='la-cendre-du-jugement'; "
            "requireUser(`/compte/connexion.html?next=${encodeURIComponent(location.pathname+location.search)}`); "
            "functions.invoke(DELIVERY_FUNCTION,{body:{novel_slug:novelSlug,mode}}); "
            "invokeDelivery('read'); invokeDelivery('download'); "
            "localStorage.setItem(storageKey,String(current)); location.assign(String(data.url));",
            encoding='utf-8',
        )
        paths['roman'].write_text('<a href="lire-integral.html?novel=la-cendre-du-jugement">Lire</a> sinjira-livre01-couverture-avant.png', encoding='utf-8')
        broken = validate(*args)
        if not any('référence de couverture inexistante' in item for item in broken):
            raise AssertionError('Une couverture cassée doit être bloquée.')

        paths['roman'].write_text('<a href="lire-integral.html?novel=la-cendre-du-jugement">Lire</a>', encoding='utf-8')
        paths['licenses'].write_text(read(paths['licenses']) + " 'Accès permanent à tous les romans';", encoding='utf-8')
        promise = validate(*args)
        if not any('Promesse propriétaire' in item for item in promise):
            raise AssertionError('Une promesse propriétaire universelle doit être bloquée.')

    print('OK auto-test UI Livre I V4: full_access canonique, lecteur privé dédié, progression locale et actifs publics protégés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide l’interface du lecteur privé du Livre I.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    errors = validate()
    if errors:
        print(f'ÉCHEC UI Livre I: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK UI Livre I V4: intégrale liée au full_access serveur, lecteur privé dédié, progression locale et pages publiques sans intégrale.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
