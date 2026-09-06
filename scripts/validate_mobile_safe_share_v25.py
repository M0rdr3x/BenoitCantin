#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'mobile-native' / 'App.tsx'
PACKAGE = ROOT / 'mobile-native' / 'package.json'
CLIENT_BOUNDARY = ROOT / 'scripts' / 'validate_device_challenge_client_boundary.py'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-mobile-safe-share-v25.yml'


def fail(message: str) -> None:
    print(f'ECHEC partage mobile V25: {message}', file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def section(text: str, start: str, end: str) -> str:
    require(start in text and end in text, f'section introuvable: {start}')
    return text[text.index(start):text.index(end, text.index(start))]


def main() -> int:
    for path in (APP, PACKAGE, CLIENT_BOUNDARY, WORKFLOW):
        require(path.is_file(), f'fichier manquant: {path.relative_to(ROOT)}')

    app = APP.read_text('utf-8')
    package = PACKAGE.read_text('utf-8')
    client_boundary = CLIENT_BOUNDARY.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')

    require(re.search(r'\bShare,\s*\n\s*StyleSheet,', app) is not None,
            'API Share de React Native non importée')
    require("const PRIVATE_SHARE_PATH_PREFIXES = ['/app/', '/compte/', '/admin/', '/auth/', '/api/'] as const;" in app,
            'liste minimale des routes privées partageables absente ou affaiblie')

    share_guard = section(app, 'function shareableSinjiraUrl', 'function isVaultUrl')
    require("parsed.protocol !== 'https:'" in share_guard,
            'le partage doit être limité à HTTPS')
    require('!ALLOWED_WEB_HOSTS.has(parsed.hostname)' in share_guard,
            'le partage doit être limité aux domaines SINJIRA autorisés')
    require('PRIVATE_SHARE_PATH_PREFIXES.some' in share_guard,
            'les préfixes privés ne sont pas évalués')
    require('normalizedPath === root || normalizedPath.startsWith(prefix)' in share_guard,
            'les racines et descendants privés doivent être bloqués')
    require('if (privatePath) return null;' in share_guard,
            'une route privée doit être refusée avant partage')
    require('return `${ORIGIN}${pathname}`;' in share_guard,
            'le partage doit reconstruire une URL canonique chemin-seulement')
    forbid(share_guard, 'parsed.search', 'les paramètres de requête ne doivent jamais être partagés')
    forbid(share_guard, 'parsed.hash', 'les fragments ne doivent jamais être partagés')

    share_action = section(app, 'const shareCurrentPage = async () => {', '  useEffect(() => {\n    Linking.getInitialURL()')
    require('const shareUrl = shareableSinjiraUrl(currentUrl);' in share_action,
            'la page courante doit passer par le garde de partage')
    require("if (!shareUrl)" in share_action and 'Cette page reste privée.' in share_action,
            'refus explicite des pages privées absent')
    require('await Share.share({' in share_action,
            'menu de partage natif non appelé')
    require('message: `SINJIRA™ — ${shareUrl}`' in share_action and 'url: shareUrl' in share_action,
            'seule l’URL validée doit être transmise au menu natif')
    forbid(share_action, 'url: currentUrl', 'currentUrl brut ne doit jamais être partagé')
    require('onPress={() => void shareCurrentPage()}' in app,
            'bouton de partage natif non relié')
    require('Partager cette page SINJIRA si elle est publique' in app,
            'libellé accessibilité du partage absent')

    # Le partage ne doit pas contourner les protections appareil déjà figées en #195.
    for marker in ('security_resolve_connection_challenge_mfa', 'SecureStore', 'WEB_DEVICE_KEY_STORAGE'):
        require(marker in client_boundary, f'garde client sécurité #195 non chaînable: {marker}')

    # Aucun secret ni surface serveur dans cette fonctionnalité client.
    for marker in (
        'SUPABASE_SERVICE_ROLE_KEY', 'SERVICE_ROLE_KEY', 'SUPABASE_ACCESS_TOKEN', 'sb_secret_',
        '/auth/v1/admin/', 'service_conscience_', 'private.conscience_', 'gpvivleexywljowcqkru',
    ):
        forbid(app, marker, f'surface privilégiée/production interdite dans App.tsx: {marker}')

    require('"typecheck": "tsc --noEmit"' in package,
            'script TypeScript typecheck mobile absent')

    required_paths = (
        'mobile-native/App.tsx',
        'mobile-native/package.json',
        'scripts/validate_mobile_safe_share_v25.py',
        'scripts/validate_device_challenge_client_boundary.py',
    )
    for marker in required_paths:
        require(marker in workflow, f'chemin CI manquant: {marker}')
    require('pull_request:' in workflow and 'workflow_dispatch:' in workflow,
            'déclencheurs CI incomplets')
    require('python3 scripts/validate_mobile_safe_share_v25.py' in workflow,
            'validateur partage mobile non exécuté')
    require('python3 scripts/validate_device_challenge_client_boundary.py' in workflow,
            'garde client sécurité #195 non exécuté')
    require('python3 scripts/validate_no_committed_secrets.py' in workflow,
            'garde secrets non exécuté')
    require('npm install --ignore-scripts --no-audit --no-fund' in workflow,
            'installation mobile déterministe au package.json absente')
    require('npm run typecheck' in workflow,
            'typecheck TypeScript mobile absent')
    forbid(workflow, 'environment: production', 'environnement production interdit')
    forbid(workflow, 'SUPABASE_ACCESS_TOKEN', 'PAT Supabase interdit')
    forbid(workflow, '${{ secrets.', 'aucun secret GitHub Actions ne doit être requis')

    print(
        'OK partage mobile V25: Share natif limité aux URL SINJIRA publiques HTTPS, '
        'routes privées bloquées et query/hash supprimés avant tout partage.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
