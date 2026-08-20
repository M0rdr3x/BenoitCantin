#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'projets/sinjira/communaute/index.html'
CSS=ROOT/'assets/css/sinjira-community-public-v24-4-80.css'


def require(text,markers,label):
    missing=[m for m in markers if m not in text]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m in text]
    if found: raise AssertionError(f'{label}: anciens marqueurs encore présents: {found}')


def main():
    page=PAGE.read_text('utf-8',errors='ignore')
    css=CSS.read_text('utf-8',errors='ignore')
    require(page,[
        'data-community-public-version="24.4.80"',
        'sinjira-community-public-v24-4-80.css?v=24.4.80',
        'sinjira-communaute.webp',
        'Entrer dans la Communauté',
        'Communauté — identité du compte',
        'Réseau des personnages',
        'Rencontres SINJIRA™',
        '10 messages chacun',
        'Centre de sécurité',
        'Signalements structurés',
        'Blocage unifié',
        'Historique self-only',
        'Monde parallèle',
        'Pas encore activé',
        'Sans publicité comportementale',
        'site.js?v=24.4.80'
    ],'page publique Communauté V24.4.80')
    forbid(page,['site.css?v=24.0','sinjira.css?v=24.0','v24-platform.css?v=24.1'],'page publique Communauté V24.4.80')
    require(css,[
        '.community-public .community-hero-shell',
        '.community-public .community-live-grid',
        '.community-public .community-dual',
        '.community-public .community-safety',
        '.community-public .community-roadmap',
        '@media(max-width:920px)',
        '@media(max-width:640px)',
        '@media(prefers-reduced-motion:reduce)'
    ],'CSS public Communauté V24.4.80')
    print('OK V24.4.80: la page publique Communauté présente le portail actuel, le visuel officiel, Rencontres, sécurité et les états de fonctionnalités avec responsive dédié.')
    return 0

if __name__=='__main__': raise SystemExit(main())
