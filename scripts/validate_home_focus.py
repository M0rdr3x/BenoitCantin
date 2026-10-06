#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / 'index.html'

REQUIRED = {
    '/projets/sinjira/': 'SINJIRA™',
    '/projets/sinjira/registre/': 'Registre des Consciences',
    '/projets/projet-nova/': 'Projet Nova',
    '/projets/projet-nova/boussole-electorale.html': 'Boussole électorale',
}
FORBIDDEN_MARKERS = [
    'Lumina',
    'Futurax',
    'Chroniques des Mondes Fracturés',
    'v20-six-portals',
    'node-community',
    'node-character-network',
]


def main() -> int:
    errors: list[str] = []
    if not HOME.exists():
        print('ECHEC: index.html absent.')
        return 1

    text = HOME.read_text('utf-8', errors='ignore')

    for href, label in REQUIRED.items():
        if href not in text:
            errors.append(f'Porte principale absente: {label} ({href})')

    home_cosmos = re.search(r'<div class="home-cosmos".*?</div>\s*</div>\s*</section>', text, re.S)
    if not home_cosmos:
        errors.append('Constellation native home-cosmos introuvable sur la page d’accueil.')
    else:
        block = home_cosmos.group(0)
        nodes = re.findall(r'class="orbit-node\s+([^\"]+)"', block)
        if len(nodes) != 4:
            errors.append(f'La constellation doit contenir exactement 4 portes; détecté: {len(nodes)}.')
        expected_classes = {'node-sinjira-home', 'node-registre-home', 'node-nova-home', 'node-boussole-home'}
        found = set()
        for entry in nodes:
            found.update(entry.split())
        missing = sorted(expected_classes - found)
        if missing:
            errors.append('Classes de portes manquantes: ' + ', '.join(missing))

    for marker in FORBIDDEN_MARKERS:
        if marker in text:
            errors.append(f'Ancien univers/composant encore présent sur l’accueil: {marker}')

    if 'data-core-preview' not in text:
        errors.append('Aperçu central interactif data-core-preview absent.')
    if 'data-default-src="/assets/icons/benoit-sigil.svg"' not in text:
        errors.append('Le sceau Benoit Cantin doit rester l’image centrale par défaut.')

    if text.count('/projets/projet-nova/boussole-electorale.html') < 4:
        errors.append('La Boussole électorale doit être accessible à au moins quatre endroits sur l’accueil principal.')

    for marker in (
        'node-boussole-home',
        '/assets/media/nova-boussole-electorale.svg',
        'Quatre portes · une même signature',
        '>Boussole</a>',
    ):
        if marker not in text:
            errors.append(f'Boussole électorale: placement visuel principal absent: {marker}')

    if errors:
        print(f'ECHEC accueil: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK: accueil à quatre portes — SINJIRA™, Registre, Projet Nova et Boussole électorale — avec sceau BC par défaut.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
