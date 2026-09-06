#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'mobile-native' / 'App.tsx'
SHARE_MODULE = ROOT / 'mobile-native' / 'safePublicShare.ts'
PACKAGE = ROOT / 'mobile-native' / 'package.json'
VAULT_GUARD = ROOT / 'mobile-native' / 'scripts' / 'validate-vault-mobile.mjs'
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
    for path in (APP, SHARE_MODULE, PACKAGE, VAULT_GUARD, CLIENT_BOUNDARY, WORKFLOW):
        require(path.is_file(), f'fichier manquant: {path.relative_to(ROOT)}')

    app = APP.read_text('utf-8')
    share_module = SHARE_MODULE.read_text('utf-8')
    package = PACKAGE.read_text('utf-8')
    vault_guard = VAULT_GUARD.read_text('utf-8')
    client_boundary = CLIENT_BOUNDARY.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')

    # Le shell privé garde la décision de partage, mais il ne possède aucune API d’export native.
    require("import { sharePublicSinjiraUrl } from './safePublicShare';" in app,
            'module de partage public non importé dans App.tsx')
    forbid(app, 'Share.share(', 'App.tsx doit rester incapable d’appeler directement le menu de partage')
    forbid(app, '  Share,', 'API Share ne doit pas être importée dans le shell privé')
    require("const PRIVATE_SHARE_PATH_PREFIXES = ['/app/', '/compte/', '/admin/', '/auth/', '/api/'] as const;" in app,
            'liste minimale des routes privées absente ou affaiblie dans App.tsx')

    share_guard = section(app, 'function shareableSinjiraUrl', 'function hasSensitiveExternalMaterial')
    require("parsed.protocol !== 'https:'" in share_guard,
            'le premier garde doit limiter le partage à HTTPS')
    require('!ALLOWED_WEB_HOSTS.has(parsed.hostname)' in share_guard,
            'le premier garde doit limiter aux domaines SINJIRA autorisés')
    require('PRIVATE_SHARE_PATH_PREFIXES.some' in share_guard,
            'les préfixes privés ne sont pas évalués dans App.tsx')
    require('normalizedPath === root || normalizedPath.startsWith(prefix)' in share_guard,
            'racines et descendants privés non bloqués dans App.tsx')
    require('if (privatePath) return null;' in share_guard,
            'une route privée doit être refusée avant sortie du shell')
    require('return `${ORIGIN}${pathname}`;' in share_guard,
            'App.tsx doit produire une URL chemin-seulement')
    forbid(share_guard, 'parsed.search', 'query string interdite dans l’URL de partage')
    forbid(share_guard, 'parsed.hash', 'fragment interdit dans l’URL de partage')

    share_action = section(app, 'const shareCurrentPage = async () => {', '  useEffect(() => {\n    Linking.getInitialURL()')
    require('const shareUrl = shareableSinjiraUrl(currentUrl);' in share_action,
            'currentUrl doit passer par le premier garde')
    require("if (!shareUrl)" in share_action and 'Cette page reste privée.' in share_action,
            'refus local explicite des pages privées absent')
    require('await sharePublicSinjiraUrl(shareUrl);' in share_action,
            'le shell doit transmettre uniquement shareUrl au module isolé')
    forbid(share_action, 'sharePublicSinjiraUrl(currentUrl)',
           'currentUrl brut ne doit jamais quitter le shell privé')
    require('onPress={() => void shareCurrentPage()}' in app,
            'bouton de partage natif non relié')
    require('Partager cette page SINJIRA si elle est publique' in app,
            'libellé accessibilité du partage absent')

    # Le module d’export est public-only et refait sa propre validation en défense en profondeur.
    require("import { Share } from 'react-native';" in share_module,
            'API Share absente du module public isolé')
    require("const PRIVATE_PATH_PREFIXES = ['/app/', '/compte/', '/admin/', '/auth/', '/api/'] as const;" in share_module,
            'module isolé sans liste minimale de routes privées')
    for host in ('www.benoitcantin.com', 'benoitcantin.com', 'sinjira.com', 'www.sinjira.com'):
        require(host in share_module, f'domaine public autorisé manquant: {host}')
    module_guard = section(share_module, 'function canonicalPublicSinjiraUrl', 'export async function sharePublicSinjiraUrl')
    require("parsed.protocol !== 'https:'" in module_guard,
            'module isolé non limité à HTTPS')
    require('!PUBLIC_SHARE_HOSTS.has(parsed.hostname)' in module_guard,
            'module isolé non limité aux domaines publics autorisés')
    require('PRIVATE_PATH_PREFIXES.some' in module_guard and 'if (privatePath) return null;' in module_guard,
            'module isolé ne bloque pas les routes privées')
    require('return `${parsed.origin}${pathname}`;' in module_guard,
            'module isolé doit reconstruire une URL sans query/hash')
    forbid(module_guard, 'parsed.search', 'query string interdite dans le module isolé')
    forbid(module_guard, 'parsed.hash', 'fragment interdit dans le module isolé')

    export_action = share_module[share_module.index('export async function sharePublicSinjiraUrl'):]
    require('const shareUrl = canonicalPublicSinjiraUrl(candidate);' in export_action,
            'seconde validation de l’URL absente')
    require("if (!shareUrl) throw new Error('PUBLIC_SHARE_URL_REQUIRED');" in export_action,
            'refus du module public absent')
    require('return Share.share({' in export_action,
            'menu natif non appelé depuis le module isolé')
    require('message: `SINJIRA™ — ${shareUrl}`' in export_action and 'url: shareUrl' in export_action,
            'le menu natif doit recevoir uniquement l’URL revalidée')
    forbid(export_action, 'url: candidate', 'candidate brute interdite dans le menu natif')

    # Le module public ne connaît aucune donnée, capacité ou mécanisme du shell privé.
    for marker in (
        'currentUrl', 'WebView', 'SecureStore', 'localStorage', 'VAULT_PATH', 'PERSONAL_AI_PATH',
        'conscience', 'vault_session_id', 'content_payload', 'service_conscience_', 'functions.invoke',
        'SUPABASE_SERVICE_ROLE_KEY', 'SERVICE_ROLE_KEY', 'SUPABASE_ACCESS_TOKEN', 'sb_secret_',
        '/auth/v1/admin/', 'gpvivleexywljowcqkru',
    ):
        forbid(share_module, marker, f'surface privée/privilégiée interdite dans safePublicShare.ts: {marker}')

    # Le garde historique du Coffre reste inchangé et doit continuer d’interdire Share.share dans App.tsx.
    require("'Share.share('," in vault_guard,
            'le garde historique du Coffre ne bloque plus Share.share dans App.tsx')
    for marker in ('security_resolve_connection_challenge_mfa', 'SecureStore', 'WEB_DEVICE_KEY_STORAGE'):
        require(marker in client_boundary, f'garde client sécurité #195 non chaînable: {marker}')

    for marker in (
        'SUPABASE_SERVICE_ROLE_KEY', 'SERVICE_ROLE_KEY', 'SUPABASE_ACCESS_TOKEN', 'sb_secret_',
        '/auth/v1/admin/', 'service_conscience_', 'private.conscience_', 'gpvivleexywljowcqkru',
    ):
        forbid(app, marker, f'surface privilégiée/production interdite dans App.tsx: {marker}')

    require('"typecheck": "tsc --noEmit"' in package,
            'script TypeScript typecheck mobile absent')
    require('"validate:vault": "node scripts/validate-vault-mobile.mjs"' in package,
            'garde mobile historique absent du package')

    required_paths = (
        'mobile-native/App.tsx',
        'mobile-native/safePublicShare.ts',
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
            'installation mobile sans scripts absente')
    require('npm run validate:vault' in workflow,
            'garde mobile historique du Coffre non exécuté')
    require('npm run typecheck' in workflow,
            'typecheck TypeScript mobile absent')
    forbid(workflow, 'environment: production', 'environnement production interdit')
    forbid(workflow, 'SUPABASE_ACCESS_TOKEN', 'PAT Supabase interdit')
    forbid(workflow, '${{ secrets.', 'aucun secret GitHub Actions ne doit être requis')

    print(
        'OK partage mobile V25: shell privé sans Share.share, export isolé public-only, '
        'double validation HTTPS/domaines/routes et query/hash supprimés avant partage.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
