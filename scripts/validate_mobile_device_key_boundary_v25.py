#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'mobile-native' / 'App.tsx'
HELPER = ROOT / 'assets' / 'js' / 'sinjira-device-key-v25.js'
SECURITY = ROOT / 'assets' / 'js' / 'sinjira-security-center-v24-4-98.js'
VAULT = ROOT / 'assets' / 'js' / 'sinjira-consciousness-vault-v25.js'
PERSONAL_AI = ROOT / 'assets' / 'js' / 'sinjira-personal-ai-v25.js'
MOBILE_VALIDATOR = ROOT / 'mobile-native' / 'scripts' / 'validate-vault-mobile.mjs'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-mobile-device-key-boundary-v25.yml'


def fail(message: str) -> None:
    print(f'ECHEC frontière clé appareil mobile V25: {message}', file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> int:
    for path in (APP, HELPER, SECURITY, VAULT, PERSONAL_AI, MOBILE_VALIDATOR, WORKFLOW):
        require(path.is_file(), f'fichier manquant: {path.relative_to(ROOT)}')

    app = APP.read_text('utf-8')
    helper = HELPER.read_text('utf-8')
    security = SECURITY.read_text('utf-8')
    vault = VAULT.read_text('utf-8')
    personal_ai = PERSONAL_AI.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')

    # Le natif possède durablement sa seule clé dans SecureStore.
    for marker in (
        "const DEVICE_KEY_STORAGE = 'sinjira_native_device_key_v1';",
        'SecureStore.getItemAsync(DEVICE_KEY_STORAGE)',
        'SecureStore.setItemAsync(DEVICE_KEY_STORAGE, key)',
        "const DEVICE_KEY_REQUEST_TYPE = 'sinjira.device-key.request';",
        "const DEVICE_KEY_RESPONSE_EVENT = 'sinjira:native-device-key-response';",
        'const handleWebMessage = async (event: WebViewMessageEvent) => {',
        'if (!isAllowedWebUrl(currentUrl)) return;',
        'if (event.nativeEvent.url && !isAllowedWebUrl(event.nativeEvent.url)) return;',
        "if (payload.type !== DEVICE_KEY_REQUEST_TYPE) return;",
        "if (!/^[A-Za-z0-9-]{16,80}$/.test(requestId)) return;",
        'onMessage={(event) => { void handleWebMessage(event); }}',
    ):
        require(marker in app, f'garde natif manquant: {marker}')

    require(app.count('SecureStore.getItemAsync(DEVICE_KEY_STORAGE)') >= 2,
            'la clé doit être relue depuis SecureStore au bootstrap et au moment de la demande WebView')
    require('setNativeDeviceKey' not in app and '[nativeDeviceKey' not in app,
            'la clé ne doit plus vivre dans un state React longue durée')
    require('localStorage.removeItem(${JSON.stringify(LEGACY_WEB_DEVICE_KEY_STORAGE)})' in app,
            'ancienne copie localStorage WebView non purgée')
    require('sessionStorage.removeItem(${JSON.stringify(LEGACY_WEB_DEVICE_KEY_STORAGE)})' in app,
            'ancienne copie sessionStorage WebView non purgée')
    require('localStorage.setItem(${JSON.stringify(LEGACY_WEB_DEVICE_KEY_STORAGE)}' not in app,
            'la clé appareil ne doit jamais être réécrite dans localStorage par le natif')
    require('sessionStorage.setItem(${JSON.stringify(LEGACY_WEB_DEVICE_KEY_STORAGE)}' not in app,
            'la clé appareil ne doit jamais être réécrite dans sessionStorage par le natif')

    # Le helper est one-shot en WebView et échoue fermé; le navigateur classique garde son identifiant local.
    for marker in (
        "const NATIVE_REQUEST_TYPE='sinjira.device-key.request';",
        "const NATIVE_RESPONSE_EVENT='sinjira:native-device-key-response';",
        'const NATIVE_TIMEOUT_MS=3000;',
        "bridge.postMessage(JSON.stringify({type:NATIVE_REQUEST_TYPE,request_id:id}))",
        "code:'NATIVE_DEVICE_KEY_TIMEOUT'",
        "code:'NATIVE_DEVICE_KEY_UNAVAILABLE'",
        'if(bridge)return requestNativeDeviceKey(bridge);',
        'return browserDeviceKey();',
        'localStorage.getItem(DEVICE_KEY_STORAGE)',
        'sessionStorage.getItem(DEVICE_KEY_STORAGE)',
    ):
        require(marker in helper, f'contrat helper manquant: {marker}')
    require(helper.index('if(bridge)return requestNativeDeviceKey(bridge);') < helper.index('return browserDeviceKey();'),
            'le chemin WebView doit échouer fermé avant tout fallback navigateur')
    for forbidden in ('console.log(', 'console.warn(', 'console.error('):
        require(forbidden not in helper, 'le helper ne doit jamais journaliser une clé ou une réponse native')

    # Les trois surfaces sensibles passent toutes par le helper partagé.
    for name, text in (('Centre de sécurité', security), ('Coffre', vault), ('Mon IA', personal_ai)):
        require("./sinjira-device-key-v25.js" in text, f'{name}: helper partagé absent')
        require("'sinjira.security.device_key.v1'" not in text, f'{name}: stockage direct de clé encore présent')
        require('randomDeviceKey' not in text, f'{name}: génération locale dupliquée encore présente')
        require('localStorage.getItem(' not in text and 'sessionStorage.getItem(' not in text,
                f'{name}: lecture directe du stockage navigateur interdite')

    require('const meta=await getDeviceMetadata();' in vault,
            'Coffre: métadonnées appareil one-shot absentes')
    require('const meta=await getDeviceMetadata();' in personal_ai,
            'Mon IA: métadonnées appareil one-shot absentes')
    require('const currentDeviceKey=await getDeviceKey();' in security,
            'Centre de sécurité: clé courante one-shot absente du chargement')
    require(security.count('const deviceKey=await getDeviceKey();') >= 3,
            'Centre de sécurité: compromission + approbation + refus doivent relire la clé one-shot')
    require('security_resolve_connection_challenge_mfa' not in security,
            'l’ancienne auto-approbation MFA ne doit jamais revenir dans le client interactif')
    require('security_resolve_connection_challenge' in security,
            'résolveur multi-appareils standard absent du Centre de sécurité')
    require('CURRENT_TRUSTED_DEVICE_REQUIRED' in security and 'TRUSTED_OTHER_DEVICE_REQUIRED' in security,
            'messages des nouveaux refus multi-appareils absents')

    # Le natif ne reçoit toujours ni contenu Coffre ni état Mon IA.
    require('conscience-vault' not in app and 'vault_session_id' not in app and 'content_payload' not in app,
            'le natif ne doit jamais manipuler le contenu ou la capacité du Coffre')
    require("functions.invoke('personal-ai'" not in app and 'personal_ai_settings' not in app,
            'le natif ne doit jamais contourner l’Edge Mon IA')

    # Workflow sans production/secrets, avec validation statique et TypeScript réel.
    for marker in (
        'pull_request:',
        'workflow_dispatch:',
        'python3 scripts/validate_mobile_device_key_boundary_v25.py',
        'npm run validate:vault',
        'npm run typecheck',
        'npm install --ignore-scripts --no-audit --no-fund',
    ):
        require(marker in workflow, f'workflow incomplet: {marker}')
    for forbidden in ('SUPABASE_ACCESS_TOKEN', 'environment: production', 'supabase db push', '--no-verify-jwt', 'secrets.'):
        require(forbidden not in workflow, f'workflow mobile ne doit pas accéder à production/secrets: {forbidden}')

    print('OK frontière clé appareil mobile V25: clé durable uniquement dans SecureStore, pont WebView one-shot borné, aucun fallback natif vers localStorage et clients sensibles centralisés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
