#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'mobile-native' / 'App.tsx'
ROUTER = ROOT / 'mobile-native' / 'NativeModuleRouter.tsx'
SECURITY = ROOT / 'mobile-native' / 'NativeSecurityHub.tsx'
DOC = ROOT / 'mobile-native' / 'NATIVE_INTENT_ROUTING_V25.md'
CENTRAL_DOC = ROOT / 'mobile-native' / 'NATIVE_ROUTE_DISPATCH_V25.md'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-mobile-native-intent-routing-v25.yml'
CENTRAL_WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-mobile-native-route-dispatch-v25.yml'

errors: list[str] = []


def read(path: Path) -> str:
    if not path.exists():
        errors.append(f'fichier manquant: {path.relative_to(ROOT)}')
        return ''
    return path.read_text(encoding='utf-8')


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        errors.append(f'{label}: marqueur manquant: {needle}')


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        errors.append(f'{label}: marqueur interdit: {needle}')


app = read(APP)
router = read(ROUTER)
security = read(SECURITY)
doc = read(DOC)
central_doc = read(CENTRAL_DOC)
workflow = read(WORKFLOW)
central_workflow = read(CENTRAL_WORKFLOW)

# Le résolveur doit être situé dans navigateToUrl, avant le gate Registre.
start = app.find('  const navigateToUrl = async (url: string, tab?: TabKey) => {')
end = app.find('\n  const navigate = async', start + 1) if start >= 0 else -1
if start < 0 or end < 0:
    errors.append('App.tsx: section navigateToUrl introuvable')
    navigate_block = ''
else:
    navigate_block = app[start:end]

for needle in [
    "let internalIntent: URL | null = null;",
    "const parsed = new URL(url, ORIGIN);",
    "parsed.protocol === 'https:' && allowedHosts.has(parsed.hostname)",
    "!internalIntent.search && !internalIntent.hash && internalIntent.pathname === '/compte/securite.html'",
    "setNativeSecurityOpen(true);",
    "internalIntent.searchParams.get('surface') !== 'web'",
    "!internalIntent.hash",
    "isNativeModulePath(internalIntent.pathname)",
    "openNativeModule(internalIntent.pathname, tab);",
    "if (isVaultUrl(url) && Date.now() >= vaultLocalGateUntilRef.current)",
    "const approved = await requestVaultLocalGate();",
]:
    require(navigate_block, needle, 'navigateToUrl')

if navigate_block:
    native_pos = navigate_block.find('isNativeModulePath(internalIntent.pathname)')
    vault_pos = navigate_block.find('if (isVaultUrl(url)')
    if native_pos < 0 or vault_pos < 0 or native_pos > vault_pos:
        errors.append('navigateToUrl: le routage natif doit précéder le gate Registre sans le remplacer')

# Liens profonds et notifications doivent converger sur le même résolveur.
for needle in [
    "Linking.getInitialURL().then((url) => {",
    "if (normalized) void navigateToUrl(normalized);",
    "Linking.addEventListener('url', ({ url }) => {",
    "Notifications.addNotificationResponseReceivedListener((response) => {",
    "typeof path === 'string' && path.startsWith('/') && !path.startsWith('//')",
    "void navigate(path);",
]:
    require(app, needle, 'App.tsx')

# La WebView ne doit pas être convertie en routeur natif dans ce lot.
should_start = ''
ss_start = app.find('  const shouldStart = (request: { url: string }) => {')
ss_end = app.find('\n  if (!securityReady)', ss_start + 1) if ss_start >= 0 else -1
if ss_start < 0 or ss_end < 0:
    errors.append('App.tsx: section shouldStart introuvable')
else:
    should_start = app[ss_start:ss_end]
    forbid(should_start, 'openNativeModule(', 'shouldStart')
    forbid(should_start, 'isNativeModulePath(', 'shouldStart')
    require(should_start, 'if (isVaultUrl(url)', 'shouldStart')

# Les fragments Sécurité doivent rester des destinations Web précises.
for fragment in [
    '/compte/securite.html#devices-title',
    '/compte/securite.html#recent-title',
    '/compte/securite.html#travel-title',
    '/compte/securite.html#quick-title',
    '/compte/securite.html#preferences-title',
]:
    require(security, fragment, 'NativeSecurityHub.tsx')

# Le routeur reste une liste fermée et ne doit pas absorber Sécurité ou Registre.
require(router, 'export function isNativeModulePath', 'NativeModuleRouter.tsx')
for forbidden_route in [
    "'/compte/securite.html'",
    "'/compte/registre-personnel.html'",
    "'/compte/signaler-deces.html'",
    "'/compte/mfa.html'",
]:
    # Les chaînes peuvent exister dans des commentaires futurs; on vérifie surtout NATIVE_MODULE_PATHS.
    paths_start = router.find('export const NATIVE_MODULE_PATHS')
    paths_end = router.find('] as const', paths_start + 1) if paths_start >= 0 else -1
    paths_block = router[paths_start:paths_end] if paths_start >= 0 and paths_end >= 0 else ''
    forbid(paths_block, forbidden_route, 'NATIVE_MODULE_PATHS')

# Documentation: comportement, limites et principe humain.
for needle in [
    'L’HUMAIN AVANT TOUT',
    'PROTÉGER SANS SURVEILLER',
    '?surface=web',
    'Navigation interne de la WebView',
    'Registre personnel',
    'Liens profonds',
    'Notifications',
    'révision humaine',
]:
    require(doc, needle, 'NATIVE_INTENT_ROUTING_V25.md')

for needle in [
    'NATIVE_INTENT_ROUTING_V25.md',
    'validate_mobile_native_intent_routing_v25.py',
]:
    require(central_doc, needle, 'NATIVE_ROUTE_DISPATCH_V25.md')
    require(central_workflow, needle, 'workflow central')

# Workflow dédié: aucune écriture production, secrets ou commandes Supabase distantes.
for needle in [
    'python3 scripts/validate_mobile_native_intent_routing_v25.py',
    'python3 scripts/validate_mobile_native_account_route_classification_v25.py',
    'python3 scripts/validate_mobile_native_route_dispatch_v25.py',
    'python3 scripts/validate_mobile_native_security_hub_v25.py',
    'python3 scripts/validate_mobile_navigation_boundary_v25.py',
    'python3 scripts/validate_device_challenge_client_boundary.py',
    'python3 scripts/validate_no_committed_secrets.py',
    'npm run validate:vault',
    'npm run typecheck',
]:
    require(workflow, needle, 'workflow intentions natives')

for needle in [
    'SUPABASE_ACCESS_TOKEN',
    'SUPABASE_DB_PASSWORD',
    'service_role',
    'supabase db push',
    'supabase db reset',
    'apply_migration',
    'production',
]:
    forbid(workflow.lower(), needle.lower(), 'workflow intentions natives')

if errors:
    print('Validation routage intentions natives V25: ÉCHEC', file=sys.stderr)
    for error in errors:
        print(f'- {error}', file=sys.stderr)
    raise SystemExit(1)

print('Validation routage intentions natives V25: OK')
