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

BOOK_SLUG = 'sinjira-livre-01-la-cendre-du-jugement'
FULL_BASENAME = 'SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf'

FORBIDDEN_PROMISES = (
    'accès permanent à tous les romans',
    'accès universel côté serveur',
    'accès propriétaire universel',
    'accès total sinjira',
)


def read(path: Path) -> str:
    return path.read_text('utf-8', errors='ignore')


def validate(contract_path: Path, licenses_path: Path, library_path: Path, library_html_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        contract = json.loads(read(contract_path))
    except Exception as exc:
        return [f'Contrat Livre I illisible: {exc}']

    try:
        licenses = read(licenses_path)
        library = read(library_path)
        library_html = read(library_html_path)
    except OSError as exc:
        return [f'Interface entitlement illisible: {exc}']

    required = {
        'Licences: slug Livre I': (licenses, BOOK_SLUG),
        'Bibliothèque: slug Livre I': (library, BOOK_SLUG),
        'Licences: droit réellement reconnu': (licenses, 'Droit numérique reconnu'),
        'Bibliothèque: droit réellement reconnu': (library, 'Droit numérique reconnu'),
        'Licences: source user_entitlements': (licenses, "from('user_entitlements')"),
        'Bibliothèque: source user_entitlements': (library, "from('user_entitlements')"),
        'Licences: frontière de diffusion privée expliquée': (licenses, 'diffusion privée'),
        'Bibliothèque: frontière de diffusion privée expliquée': (library, 'diffusion privée'),
        'Bibliothèque: rôle propriétaire séparé des produits': (library_html, 'Le rôle propriétaire reste distinct des droits numériques attribués aux produits.'),
    }
    for label, (text, marker) in required.items():
        if marker not in text:
            errors.append(f'{label} absent.')

    combined = '\n'.join((licenses, library, library_html)).lower()
    for phrase in FORBIDDEN_PROMISES:
        if phrase in combined:
            errors.append(f'Promesse propriétaire trop large interdite: {phrase}.')

    if "from('products').select('slug,name,product_type,active')" in licenses:
        errors.append('La page Licences ne doit plus fabriquer la possession propriétaire depuis tout le catalogue actif.')

    state = str(contract.get('publication_state') or '')
    if state == 'not_activated':
        for label, text in (('Licences', licenses), ('Bibliothèque', library), ('Bibliothèque HTML', library_html)):
            if "functions.invoke('get-private-book-url'" in text or 'functions.invoke("get-private-book-url"' in text:
                errors.append(f'{label}: appel à la diffusion privée interdit tant que publication_state=not_activated.')
            if FULL_BASENAME in text:
                errors.append(f'{label}: nom du PDF intégral interdit dans l’interface tant que la diffusion n’est pas activée.')

    return errors


def self_test() -> None:
    with TemporaryDirectory() as raw:
        root = Path(raw)
        contract = root / 'contract.json'
        licenses = root / 'licenses.js'
        library = root / 'library.js'
        html = root / 'library.html'
        contract.write_text(json.dumps({'publication_state':'not_activated'}), encoding='utf-8')
        licenses.write_text(
            f"const BOOK='{BOOK_SLUG}'; s.from('user_entitlements'); 'Droit numérique reconnu'; 'diffusion privée';",
            encoding='utf-8',
        )
        library.write_text(
            f"const BOOK='{BOOK_SLUG}'; s.from('user_entitlements'); 'Droit numérique reconnu'; 'diffusion privée';",
            encoding='utf-8',
        )
        html.write_text('Le rôle propriétaire reste distinct des droits numériques attribués aux produits.', encoding='utf-8')

        clean = validate(contract, licenses, library, html)
        if clean:
            raise AssertionError('Le cas sain doit passer: ' + ' | '.join(clean))

        licenses.write_text(read(licenses) + "\ns.functions.invoke('get-private-book-url');", encoding='utf-8')
        premature = validate(contract, licenses, library, html)
        if not any('not_activated' in item for item in premature):
            raise AssertionError('Un appel prématuré à get-private-book-url doit être bloqué.')

        licenses.write_text(
            f"const BOOK='{BOOK_SLUG}'; s.from('user_entitlements'); 'Droit numérique reconnu'; 'diffusion privée'; 'Accès permanent à tous les romans';",
            encoding='utf-8',
        )
        promise = validate(contract, licenses, library, html)
        if not any('Promesse propriétaire' in item for item in promise):
            raise AssertionError('Une promesse propriétaire universelle doit être bloquée.')

        licenses.write_text(
            f"const BOOK='{BOOK_SLUG}'; s.from('user_entitlements'); 'Droit numérique reconnu'; 'diffusion privée'; s.from('products').select('slug,name,product_type,active');",
            encoding='utf-8',
        )
        catalog = validate(contract, licenses, library, html)
        if not any('tout le catalogue actif' in item for item in catalog):
            raise AssertionError('La possession ne doit pas être déduite du catalogue actif.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide la séparation rôle propriétaire / entitlement dans l’interface Livre I.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print('OK auto-test UI entitlement Livre I.')
        return 0

    errors = validate(CONTRACT, LICENSES, LIBRARY, LIBRARY_HTML)
    if errors:
        print(f'ÉCHEC UI entitlement Livre I: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK UI entitlement Livre I: rôle propriétaire distinct, droits réels affichés, aucune diffusion intégrale prématurée.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
