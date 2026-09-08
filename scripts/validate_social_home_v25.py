#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'compte' / 'communaute.html'
CSS = ROOT / 'assets' / 'css' / 'v25-social-home.css'
RUNTIME = ROOT / 'assets' / 'js' / 'sinjira-community-real.js'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f'ERREUR social V25: {message}')


def main() -> int:
    html = HTML.read_text(encoding='utf-8')
    css = CSS.read_text(encoding='utf-8')
    runtime = RUNTIME.read_text(encoding='utf-8')

    for marker in (
        '../assets/css/v25-social-home.css?v=25.0.1',
        'class="account-shell v25-social-layout"',
        'class="v25-social-rail"',
        'class="v25-social-main"',
        'class="v25-social-discovery"',
        'data-real-post-form=""',
        'data-real-feed=""',
        'data-real-identity=""',
        'Ordre chronologique',
        'Prochaine étape · Realtime sécurisé',
        'Cette carte n’affiche pas de faux statut en direct',
        '../assets/js/sinjira-community-real.js?v=24.4.94',
    ):
        require(marker in html, f'marqueur HTML absent: {marker}')

    require(html.count('data-real-post-form=""') == 1, 'le compositeur réel doit rester unique')
    require(html.count('data-real-feed=""') == 1, 'le fil réel doit rester unique')
    require(html.count('data-real-identity=""') == 1, 'l’identité réelle doit rester unique')

    for copied_brand in ('facebook', 'instagram', 'twitter', 'x.com'):
        require(copied_brand not in html.lower(), f'la surface SINJIRA ne doit pas copier une marque externe: {copied_brand}')

    for marker in (
        '.v25-social-layout{display:grid;grid-template-columns:220px minmax(0,680px) 300px',
        '@media(max-width:920px)',
        '@media(max-width:720px)',
        '.v25-social-main .v20-social-card',
        '.v25-live-preview',
    ):
        require(marker in css, f'contrat CSS absent: {marker}')

    for marker in (
        ".from('social_real_posts')",
        ".from('social_real_comments')",
        ".from('social_real_likes')",
        'openSocialReport',
        'editOwnContent',
        'deleteOwnContent',
    ):
        require(marker in runtime, f'le backend social réel existant doit rester branché: {marker}')

    require('setInterval(' not in html, 'la page ne doit pas simuler du temps réel par polling inline')
    require('WebSocket(' not in html, 'la page ne doit pas simuler un socket avant le contrat Realtime/RLS')

    print('OK social V25: nouveau fil responsive en trois zones, backend social réel conservé et En direct annoncé sans faux temps réel.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
