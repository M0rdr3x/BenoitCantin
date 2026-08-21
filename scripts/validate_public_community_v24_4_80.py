#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'projets/sinjira/communaute/index.html'
CSS=ROOT/'assets/css/sinjira-community-public-v24-4-80.css'
MIN_VERSION=(24,4,91)


def require(text,markers,label):
    missing=[m for m in markers if m not in text]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m in text]
    if found: raise AssertionError(f'{label}: anciens marqueurs encore présents: {found}')


def version_at_least(value):
    try:return tuple(int(x) for x in value.split('.'))>=MIN_VERSION
    except Exception:return False


def main():
    page=PAGE.read_text('utf-8',errors='ignore')
    css=CSS.read_text('utf-8',errors='ignore')
    version=re.search(r'data-community-public-version="([0-9.]+)"',page)
    if not version or not version_at_least(version.group(1)):
        raise AssertionError('page publique Communauté: version antérieure à V24.4.91.')
    css_version=re.search(r'sinjira-community-public-v24-4-80\.css\?v=([0-9.]+)',page)
    site_version=re.search(r'site\.js\?v=([0-9.]+)',page)
    if not css_version or not version_at_least(css_version.group(1)):
        raise AssertionError('page publique Communauté: cache CSS non invalidé pour V24.4.91.')
    if not site_version or not version_at_least(site_version.group(1)):
        raise AssertionError('page publique Communauté: cache du shell public non invalidé pour V24.4.91.')

    require(page,[
        'sinjira-communaute.webp',
        'Entrer dans la Communauté',
        'Communauté — profil',
        'Réseau des personnages',
        'Rencontres SINJIRA™',
        '10 messages chacun',
        'Centre de sécurité',
        'Signalements structurés',
        'Blocage unifié',
        'Décisions et appels',
        'appel interne est gratuit',
        'révision humaine',
        'identifiant technique du compte',
        'Monde parallèle',
        'Pas encore activé',
        'Sans publicité comportementale'
    ],'page publique Communauté V24.4.91')
    forbid(page,[
        'Communauté — identité du compte',
        '<span class="community-kicker">Compte réel</span>',
        '<h3>Votre identité communautaire</h3><p>Pseudo,',
        'site.css?v=24.0','sinjira.css?v=24.0','v24-platform.css?v=24.1'
    ],'page publique Communauté V24.4.91')
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
    print('OK V24.4.91: portail Communauté actuel, identités cloisonnées, Rencontres, sécurité, modération réversible et appels humains visibles.')
    return 0

if __name__=='__main__': raise SystemExit(main())
