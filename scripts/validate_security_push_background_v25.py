#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECURITY_CONTEXT = ROOT / 'supabase' / 'functions' / 'security-context' / 'index.ts'
NETWORK = ROOT / 'supabase' / 'functions' / '_shared' / 'security-push-network.mjs'
CONFIG = ROOT / 'supabase' / 'config.toml'
TEST = ROOT / 'scripts' / 'test_security_push_network_v25.mjs'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-native-push-producer-boundary-v25.yml'


def read(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f'ERREUR push background V25: fichier absent: {path.relative_to(ROOT)}')
    return path.read_text(encoding='utf-8')


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SystemExit(f'ERREUR push background V25: contrat absent ({label}): {needle}')


context = read(SECURITY_CONTEXT)
network = read(NETWORK)
config = read(CONFIG)
test = read(TEST)
workflow = read(WORKFLOW)

for needle in (
    "import 'jsr:@supabase/functions-js/edge-runtime.d.ts';",
    "from '../_shared/security-push-network.mjs'",
    'postSecurityPushJson(SECURITY_PUSH_RECEIPT_URL, request)',
    'postSecurityPushJson(SECURITY_PUSH_SEND_URL, messages)',
    'async function runSecurityPushBackground(',
    'await processSecurityPushReceipts(service);',
    'await sendSecurityPush(service, userId, security);',
    'EdgeRuntime.waitUntil(runSecurityPushBackground(service, user.id, data));',
    "console.warn('[security-context] tâche push de fond impossible');",
):
    require(context, needle, 'security-context')

for forbidden in (
    "fetch('https://exp.host/--/api/v2/push/send'",
    "fetch('https://exp.host/--/api/v2/push/getReceipts'",
    'await processSecurityPushReceipts(service);\n    await sendSecurityPush(service, user.id, data);',
):
    if forbidden in context:
        raise SystemExit(f'ERREUR push background V25: ancien chemin bloquant encore présent: {forbidden}')

for needle in (
    'export const SECURITY_PUSH_NETWORK_TIMEOUT_MS = 4000;',
    "export const SECURITY_PUSH_SEND_URL = 'https://exp.host/--/api/v2/push/send';",
    "export const SECURITY_PUSH_RECEIPT_URL = 'https://exp.host/--/api/v2/push/getReceipts';",
    "throw new TypeError('INVALID_SECURITY_PUSH_TIMEOUT')",
    "throw new TypeError('INVALID_SECURITY_PUSH_URL')",
    "throw new TypeError('INVALID_SECURITY_PUSH_FETCH')",
    'return AbortSignal.timeout(timeoutMs);',
    "method: 'POST'",
    "'Content-Type': 'application/json'",
    'signal: createSecurityPushAbortSignal()',
):
    require(network, needle, 'réseau Expo borné')

require(config, '[edge_runtime]', 'runtime Edge local')
require(config, 'policy = "per_worker"', 'runtime Edge local')

for needle in (
    "from '../supabase/functions/_shared/security-push-network.mjs'",
    'assert.equal(SECURITY_PUSH_NETWORK_TIMEOUT_MS, 4000)',
    'createSecurityPushAbortSignal(15)',
    'const stalledFetch = async',
    "error?.name === 'TimeoutError'",
    'assert.equal(timedOutSignal.aborted, true)',
    "postSecurityPushJson('https://example.com/push'",
    'INVALID_SECURITY_PUSH_URL',
    'INVALID_SECURITY_PUSH_FETCH',
):
    require(test, needle, 'test réseau Expo')

for needle in (
    'scripts/test_security_push_network_v25.mjs',
    'scripts/validate_security_push_background_v25.py',
    'python3 scripts/validate_security_push_background_v25.py',
    'node scripts/test_security_push_network_v25.mjs',
):
    require(workflow, needle, 'workflow push')

print('OK push background V25: décision sécurité synchrone, Expo hors chemin de réponse, timeout 4s réellement testé, endpoints exacts et runtime local per_worker.')
