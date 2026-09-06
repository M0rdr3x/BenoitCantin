#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'assets' / 'js' / 'sinjira-security-center-v24-4-98.js'
SECURITY_PAGE = ROOT / 'compte' / 'securite.html'
MOBILE = ROOT / 'mobile-native' / 'App.tsx'
SERVER_GUARD = ROOT / 'scripts' / 'validate_device_challenge_continuity_smoke.py'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-device-challenge-client-boundary-v25.yml'


def fail(message: str) -> None:
    print(f'ECHEC frontière client challenge V25: {message}', file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def forbid(text: str, marker: str, message: str) -> None:
    if marker in text:
        fail(message)


def main() -> int:
    for path in (WEB, SECURITY_PAGE, MOBILE, SERVER_GUARD, WORKFLOW):
        require(path.is_file(), f'fichier manquant: {path.relative_to(ROOT)}')

    web = WEB.read_text('utf-8')
    page = SECURITY_PAGE.read_text('utf-8')
    mobile = MOBILE.read_text('utf-8')
    server_guard = SERVER_GUARD.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')

    # La page de sécurité doit continuer à charger le Centre de sécurité contrôlé ici.
    require('sinjira-security-center-v24-4-98.js' in page,
            'la page Ma sécurité ne charge plus le Centre de sécurité attendu')

    # Web: une approbation ou un refus passe uniquement par le résolveur multi-appareils
    # et présente la clé de l’appareil courant, jamais une clé choisie ailleurs.
    approve = (
        "rpc('security_resolve_connection_challenge',{"
        "p_challenge_id:target.dataset.challengeApprove,"
        "p_device_key:meta.device_key,p_decision:'approved'})"
    )
    deny = (
        "rpc('security_resolve_connection_challenge',{"
        "p_challenge_id:target.dataset.challengeDeny,"
        "p_device_key:meta.device_key,p_decision:'denied'})"
    )
    require(approve in web, 'approbation Web non liée à meta.device_key de la session courante')
    require(deny in web, 'refus Web non lié à meta.device_key de la session courante')
    require("security_register_device" in web and 'p_device_key:meta.device_key' in web,
            'l’enregistrement Web doit utiliser la même clé d’appareil courante')
    forbid(web, 'security_resolve_connection_challenge_mfa',
           'le client Web ne doit jamais retomber sur l’ancien auto-MFA')

    # Mobile: une seule clé opaque propre à cette installation est conservée dans SecureStore.
    require("import * as SecureStore from 'expo-secure-store';" in mobile,
            'Expo SecureStore absent du client mobile')
    require("const DEVICE_KEY_STORAGE = 'sinjira_native_device_key_v1';" in mobile,
            'emplacement SecureStore de la clé native absent ou modifié sans revue')
    require("const WEB_DEVICE_KEY_STORAGE = 'sinjira.security.device_key.v1';" in mobile,
            'pont vers le stockage Web de la clé courante absent')
    require('SecureStore.getItemAsync(DEVICE_KEY_STORAGE)' in mobile,
            'lecture de la clé appareil depuis SecureStore absente')
    require('SecureStore.setItemAsync(DEVICE_KEY_STORAGE, key)' in mobile,
            'écriture de la clé appareil dans SecureStore absente')
    require('setNativeDeviceKey(key)' in mobile,
            'la clé SecureStore ne devient plus la clé native courante')
    require(
        'localStorage.setItem(${JSON.stringify(WEB_DEVICE_KEY_STORAGE)},${JSON.stringify(nativeDeviceKey)})' in mobile,
        'le WebView doit recevoir uniquement nativeDeviceKey pour cet appareil',
    )
    require("const [nativeDeviceKey, setNativeDeviceKey] = useState('');" in mobile,
            'état unique de la clé native absent')

    # Aucun client n’implémente directement la voie MFA, ne choisit une autre clé,
    # ni n’embarque une surface privilégiée serveur/production.
    for text, label in ((mobile, 'mobile'), (page, 'page sécurité')):
        forbid(text, 'security_resolve_connection_challenge_mfa',
               f'auto-MFA interdit dans le client {label}')

    privileged_markers = (
        'SUPABASE_SERVICE_ROLE_KEY',
        'SERVICE_ROLE_KEY',
        'SUPABASE_ACCESS_TOKEN',
        'sb_secret_',
        '/auth/v1/admin/',
        'service_conscience_',
        'private.conscience_',
    )
    for marker in privileged_markers:
        for text, label in ((web, 'Web'), (mobile, 'mobile'), (page, 'page sécurité')):
            forbid(text, marker, f'surface privilégiée interdite dans le client {label}: {marker}')

    # Le garde serveur #193 doit rester présent: le garde client complète, il ne remplace pas,
    # la preuve de session courante et d’autre appareil fiable.
    for marker in ('CURRENT_TRUSTED_DEVICE_REQUIRED', 'TRUSTED_OTHER_DEVICE_REQUIRED',
                   'security_resolve_connection_challenge_mfa'):
        require(marker in server_guard, f'contrat serveur multi-appareils manquant: {marker}')

    # Workflow sans secret et sans production, déclenché dès qu’un des clients concernés change.
    required_paths = (
        "assets/js/sinjira-security-center-v24-4-98.js",
        "compte/securite.html",
        "mobile-native/App.tsx",
        "scripts/validate_device_challenge_client_boundary.py",
        "scripts/validate_device_challenge_continuity_smoke.py",
    )
    for marker in required_paths:
        require(marker in workflow, f'chemin CI manquant: {marker}')
    require('pull_request:' in workflow and 'workflow_dispatch:' in workflow,
            'déclencheurs CI client incomplets')
    require('python3 scripts/validate_device_challenge_client_boundary.py' in workflow,
            'nouveau garde client non exécuté')
    require('python3 scripts/validate_device_challenge_continuity_smoke.py' in workflow,
            'garde serveur multi-appareils non chaîné')
    require('python3 scripts/validate_no_committed_secrets.py' in workflow,
            'garde secrets absent')
    forbid(workflow, 'environment: production', 'environnement production interdit dans ce workflow')
    forbid(workflow, 'SUPABASE_ACCESS_TOKEN', 'PAT Supabase interdit dans ce workflow')
    forbid(workflow, '${{ secrets.', 'aucune expression GitHub Actions secrets.* ne doit être requise')
    forbid(workflow, 'supabase start', 'ce garde statique ne doit pas démarrer Supabase')

    print(
        'OK frontière client challenge V25: Web autorise/refuse uniquement via l’appareil courant, '
        'mobile conserve une seule clé opaque dans SecureStore et aucun client ne retombe sur l’auto-MFA.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
