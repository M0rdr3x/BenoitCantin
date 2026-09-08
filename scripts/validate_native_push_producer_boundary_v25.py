#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGE_FUNCTIONS = ROOT / "supabase" / "functions"
MIGRATIONS = ROOT / "supabase" / "migrations"
BRIDGE = ROOT / "assets" / "js" / "sinjira-security-push-bridge-v24-4-98.js"
MOBILE_APP = ROOT / "mobile-native" / "App.tsx"
PUSH_MIGRATION = MIGRATIONS / "20260821222633_sinjira_v24_4_98_security_push.sql"
RECEIPT_MIGRATION = MIGRATIONS / "20260907145100_sinjira_v25_security_push_receipt_queue.sql"
APPROVED_ORCHESTRATOR = EDGE_FUNCTIONS / "security-context" / "index.ts"
APPROVED_TRANSPORT = EDGE_FUNCTIONS / "_shared" / "security-push-network.mjs"
PUSH_POLICY = EDGE_FUNCTIONS / "_shared" / "security-push-policy.mjs"
RECEIPT_POLICY = EDGE_FUNCTIONS / "_shared" / "security-push-receipts.mjs"
PUSH_POLICY_TEST = ROOT / "scripts" / "test_security_push_policy_v25.mjs"
RECEIPT_POLICY_TEST = ROOT / "scripts" / "test_security_push_receipts_v25.mjs"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-native-push-producer-boundary-v25.yml"

PRODUCER_SIGNATURES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Expo Push API", re.compile(r"exp\.host/--/api/v2/push/send", re.I)),
    ("expo-server-sdk", re.compile(r"\bexpo-server-sdk\b", re.I)),
    ("sendPushNotificationsAsync", re.compile(r"\bsendPushNotificationsAsync\b")),
    ("ExpoPushMessage", re.compile(r"\bExpoPushMessage\b")),
)
RECEIPT_SIGNATURE = re.compile(r"exp\.host/--/api/v2/push/getReceipts", re.I)
SERVER_SUFFIXES = {".ts", ".tsx", ".js", ".mjs", ".cjs"}


def fail(message: str) -> None:
    raise SystemExit(f"ERREUR native push V25: {message}")


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"fichier requis absent: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def producer_hits(text: str) -> list[str]:
    return [label for label, pattern in PRODUCER_SIGNATURES if pattern.search(text)]


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"contrat absent ({label}): {needle}")


def run_self_tests() -> None:
    allowed = (
        "Notifications.getExpoPushTokenAsync({ projectId: id })",
        "rpc('security_register_push_endpoint', { p_expo_push_token: token })",
        "create table public.security_push_endpoints (expo_push_token text not null);",
        "const request = { ids: ['receipt-00000001'] };",
    )
    blocked = (
        "fetch('https://exp.host/--/api/v2/push/send', { method: 'POST' })",
        "import { Expo } from 'expo-server-sdk';",
        "await expo.sendPushNotificationsAsync(messages);",
        "const message: ExpoPushMessage = payload;",
    )
    for sample in allowed:
        if producer_hits(sample):
            fail(f"auto-test faux positif: {sample}")
    for sample in blocked:
        if not producer_hits(sample):
            fail(f"auto-test faux négatif: {sample}")
    if not RECEIPT_SIGNATURE.search("fetch('https://exp.host/--/api/v2/push/getReceipts')"):
        fail("auto-test faux négatif sur l’API de reçus Expo")
    if RECEIPT_SIGNATURE.search("fetch('https://exp.host/--/api/v2/push/send')"):
        fail("auto-test faux positif sur l’API de reçus Expo")


def validate_approved_native_push_emitter() -> None:
    if not EDGE_FUNCTIONS.is_dir():
        fail("répertoire supabase/functions absent")

    transports: list[tuple[Path, list[str]]] = []
    receipt_transports: list[Path] = []
    for path in sorted(EDGE_FUNCTIONS.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SERVER_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        hits = producer_hits(text)
        if hits:
            transports.append((path, hits))
        if RECEIPT_SIGNATURE.search(text):
            receipt_transports.append(path)

    if not transports:
        fail("le transport Expo de sécurité attendu a disparu sans remplacement explicite")

    unexpected = [
        f"{path.relative_to(ROOT)} ({', '.join(hits)})"
        for path, hits in transports
        if path != APPROVED_TRANSPORT
    ]
    if unexpected:
        fail(
            "transport Expo/native non approuvé détecté: "
            + "; ".join(unexpected)
            + ". Toute nouvelle surface réseau exige un contrat de payload et des tests dédiés."
        )

    if len(transports) != 1 or transports[0][0] != APPROVED_TRANSPORT:
        fail("un seul transport Expo/native est autorisé: supabase/functions/_shared/security-push-network.mjs")
    if receipt_transports != [APPROVED_TRANSPORT]:
        names = ", ".join(str(path.relative_to(ROOT)) for path in receipt_transports) or "aucun"
        fail(f"l’API de reçus Expo doit rester bornée au transport partagé approuvé; lecteurs détectés: {names}")

    transport_text = read(APPROVED_TRANSPORT)
    for needle in (
        "export const SECURITY_PUSH_SEND_URL = 'https://exp.host/--/api/v2/push/send';",
        "export const SECURITY_PUSH_RECEIPT_URL = 'https://exp.host/--/api/v2/push/getReceipts';",
        "export async function postSecurityPushJson(url, payload, fetchImpl = globalThis.fetch)",
        "if (!SECURITY_PUSH_NETWORK_URLS.has(url))",
        "signal: createSecurityPushAbortSignal()",
    ):
        assert_contains(transport_text, needle, "transport Expo approuvé")

    text = read(APPROVED_ORCHESTRATOR)
    required = (
        "from '../_shared/security-push-policy.mjs'",
        "from '../_shared/security-push-receipts.mjs'",
        "from '../_shared/security-push-network.mjs'",
        "buildSecurityPushMessage(endpoint.expo_push_token, outcome)",
        "offset += SECURITY_PUSH_MAX_BATCH",
        "endpoints.slice(offset, offset + SECURITY_PUSH_MAX_BATCH)",
        "resolveSecurityPushTickets(tickets, endpointBatch)",
        ".from('security_push_receipt_queue')",
        ".upsert(resolved.receiptRows, { onConflict: 'expo_receipt_id', ignoreDuplicates: true })",
        "processSecurityPushReceipts(service)",
        ".limit(SECURITY_PUSH_RECEIPT_MAX_BATCH)",
        "buildSecurityPushReceiptRequest(pending.map((row: any) => row.expo_receipt_id))",
        "postSecurityPushJson(SECURITY_PUSH_RECEIPT_URL, request)",
        "resolveSecurityPushReceipts(pending, result?.data)",
        ".in('expo_receipt_id', resolved.handledReceiptIds)",
        "postSecurityPushJson(SECURITY_PUSH_SEND_URL, messages)",
        "console.warn('[security-context] Expo Push HTTP', response.status)",
        "console.warn('[security-context] Expo Receipt HTTP', response.status)",
    )
    for needle in required:
        assert_contains(text, needle, "orchestrateur push approuvé")

    forbidden = (
        "data: { path:",
        "await response.text()",
        "fetch('https://exp.host/--/api/v2/push/send'",
        "fetch('https://exp.host/--/api/v2/push/getReceipts'",
        "console.warn('[security-context] envoi push impossible', error)",
        "console.warn('[security-context] lecture reçus push impossible', error)",
        "console.warn('[security-context] endpoints push indisponibles', error.message)",
    )
    for needle in forbidden:
        if needle in text:
            fail(f"l’orchestrateur contourne la politique minimale, le transport approuvé ou journalise trop de détails: {needle}")


def validate_payload_policy() -> None:
    text = read(PUSH_POLICY)
    required = (
        "export const SECURITY_PUSH_PATH = '/compte/securite.html';",
        "export const SECURITY_PUSH_MAX_BATCH = 100;",
        "export function buildSecurityPushMessage(expoPushToken, outcome)",
        "if (token.length < 20 || token.length > 300)",
        "throw new TypeError('INVALID_EXPO_PUSH_TOKEN')",
        "throw new TypeError('INVALID_SECURITY_PUSH_OUTCOME')",
        "title: SECURITY_PUSH_TITLE",
        "body: SECURITY_PUSH_BODIES[outcome]",
        "data: { path: SECURITY_PUSH_PATH }",
        "channelId: 'security'",
        "priority: 'high'",
        "ttl: 600",
    )
    for needle in required:
        assert_contains(text, needle, "politique payload push")

    for forbidden in (
        "user_id",
        "device_id",
        "endpoint_id",
        "risk_score",
        "country_code",
        "region_code",
        "access_token",
        "refresh_token",
        "security.",
    ):
        if forbidden in text.lower():
            fail(f"la politique de payload ne doit pas connaître de matière sensible: {forbidden}")

    test = read(PUSH_POLICY_TEST)
    assert_contains(
        test,
        "from '../supabase/functions/_shared/security-push-policy.mjs'",
        "test runtime sur le vrai builder",
    )
    for needle in (
        "assert.equal(SECURITY_PUSH_MAX_BATCH, 100",
        "assert.deepEqual(challenge",
        "assert.deepEqual(Object.keys(blocked.data), ['path'])",
        "INVALID_SECURITY_PUSH_OUTCOME",
        "INVALID_EXPO_PUSH_TOKEN",
        "le builder ne doit pas accepter directement un objet de contexte de sécurité",
    ):
        assert_contains(test, needle, "test payload push")


def validate_receipt_policy() -> None:
    text = read(RECEIPT_POLICY)
    required = (
        "export const SECURITY_PUSH_RECEIPT_MAX_BATCH = 1000;",
        "export function buildSecurityPushReceiptRequest(receiptIds)",
        "throw new TypeError('INVALID_EXPO_RECEIPT_BATCH')",
        "throw new TypeError('DUPLICATE_EXPO_RECEIPT_ID')",
        "export function resolveSecurityPushTickets(tickets, endpointRows)",
        "expo_receipt_id: normalizeReceiptId(ticket?.id)",
        "export function classifySecurityPushReceipt(receipt)",
        "return 'provider_accepted'",
        "return 'device_not_registered'",
        "export function resolveSecurityPushReceipts(pendingRows, receiptData)",
        "if (!Object.hasOwn(data, receiptId)) continue;",
        "handledReceiptIds.push(receiptId)",
    )
    for needle in required:
        assert_contains(text, needle, "politique reçus push")

    for forbidden in (
        "title",
        "body",
        "risk_score",
        "country_code",
        "region_code",
        "access_token",
        "refresh_token",
        "expo_push_token",
        "user_id",
        "security.",
    ):
        if forbidden in text.lower():
            fail(f"la politique de reçus ne doit pas connaître de contenu utilisateur: {forbidden}")

    test = read(RECEIPT_POLICY_TEST)
    assert_contains(
        test,
        "from '../supabase/functions/_shared/security-push-receipts.mjs'",
        "test runtime sur la vraie politique de reçus",
    )
    for needle in (
        "assert.equal(SECURITY_PUSH_RECEIPT_MAX_BATCH, 1000)",
        "resolveSecurityPushTickets(",
        "resolveSecurityPushReceipts(pending",
        "un reçu absent de la réponse Expo doit rester en file",
        "DeviceNotRegistered",
        "INVALID_EXPO_RECEIPT_BATCH",
        "DUPLICATE_EXPO_RECEIPT_ID",
    ):
        assert_contains(test, needle, "test reçus push")


def validate_bridge() -> None:
    text = read(BRIDGE)
    assert_contains(text, "rpc('security_register_push_endpoint'", "enregistrement via RPC")
    assert_contains(text, "rpc('security_disable_push_for_device'", "désactivation via RPC")
    assert_contains(text, "p_expo_push_token:token", "token transmis uniquement au RPC")
    if re.search(r"\bfetch\s*\(", text):
        fail("le bridge push ne doit pas envoyer directement le token avec fetch()")
    hits = producer_hits(text)
    if hits or RECEIPT_SIGNATURE.search(text):
        fail("le bridge navigateur ne doit pas communiquer directement avec les API Expo serveur")


def validate_storage_contract() -> None:
    text = read(PUSH_MIGRATION)
    required = (
        "create table if not exists public.security_push_endpoints",
        "alter table public.security_push_endpoints enable row level security",
        "revoke all on table public.security_push_endpoints from public, anon, authenticated",
        "grant select, insert, update, delete on table public.security_push_endpoints to service_role",
        "create or replace function public.security_register_push_endpoint",
        "char_length(trim(p_expo_push_token)) not between 20 and 300",
        "where user_id=v_user and device_key=p_device_key and revoked_at is null",
        "revoke all on function public.security_register_push_endpoint(text,text,text) from public, anon",
        "grant execute on function public.security_register_push_endpoint(text,text,text) to authenticated",
    )
    for needle in required:
        assert_contains(text, needle, "stockage push privé")

    receipt_sql = read(RECEIPT_MIGRATION)
    receipt_required = (
        "create table if not exists public.security_push_receipt_queue",
        "expo_receipt_id text primary key",
        "endpoint_id uuid not null references public.security_push_endpoints(id) on delete cascade",
        "available_after timestamptz not null default (now() + interval '15 minutes')",
        "expires_at timestamptz not null default (now() + interval '24 hours')",
        "alter table public.security_push_receipt_queue enable row level security",
        "revoke all on table public.security_push_receipt_queue from public, anon, authenticated",
        "grant select, insert, delete on table public.security_push_receipt_queue to service_role",
    )
    for needle in receipt_required:
        assert_contains(receipt_sql, needle, "file reçus push privée")

    forbidden_receipt_columns = re.compile(
        r"\b(?:title|body|path|user_id|risk_score|country_code|region_code|expo_push_token|access_token|refresh_token)\s+"
        r"(?:text|uuid|jsonb?|integer|bigint|smallint|boolean|timestamptz)",
        re.I,
    )
    if forbidden_receipt_columns.search(receipt_sql):
        fail("la file de reçus ne doit pas persister de contenu de notification, identité utilisateur ou secret")

    protected_tables = r"(?:security_push_endpoints|security_push_receipt_queue)"
    dangerous_grant = re.compile(
        rf"grant\s+(?:all(?:\s+privileges)?|select|insert|update|delete)"
        rf"(?:\s*,\s*(?:select|insert|update|delete))*"
        rf"\s+on\s+table\s+public\.{protected_tables}\s+to\s+[^;]*\b(?:public|anon|authenticated)\b",
        re.I,
    )
    disable_rls = re.compile(
        rf"alter\s+table\s+public\.{protected_tables}\s+disable\s+row\s+level\s+security",
        re.I,
    )
    for path in sorted(MIGRATIONS.glob("*.sql")):
        sql = path.read_text(encoding="utf-8")
        if dangerous_grant.search(sql):
            fail(f"ACL directe interdite sur stockage push privé: {path.relative_to(ROOT)}")
        if disable_rls.search(sql):
            fail(f"RLS désactivée sur stockage push privé: {path.relative_to(ROOT)}")
        if producer_hits(sql) or RECEIPT_SIGNATURE.search(sql):
            fail(f"appel Expo interdit dans une migration SQL: {path.relative_to(ROOT)}")


def validate_mobile_registration_and_receiver() -> None:
    text = read(MOBILE_APP)
    required = (
        "Notifications.getExpoPushTokenAsync({ projectId: id })",
        "SecureStore.setItemAsync(PUSH_TOKEN_STORAGE, token, { keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY })",
        "SecureStore.setItemAsync(PUSH_DEVICE_KEY_STORAGE, deviceKey, { keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY })",
        "const token = reusablePushTokenForInstallation({",
        "if (!token && (storedToken || boundDeviceKey)) {",
        "if (push && !token) void enableSecurityPush(true, key);",
        "syncPushToWeb(true, token)",
        "Notifications.addNotificationResponseReceivedListener",
        "typeof path === 'string' && path.startsWith('/') && !path.startsWith('//')",
    )
    for needle in required:
        assert_contains(text, needle, "frontière mobile push")


def validate_workflow() -> None:
    text = read(WORKFLOW)
    for needle in (
        "supabase/functions/**",
        "supabase/migrations/**",
        "scripts/test_security_push_policy_v25.mjs",
        "scripts/test_security_push_receipts_v25.mjs",
        "scripts/test_security_push_network_v25.mjs",
        "scripts/validate_native_push_producer_boundary_v25.py",
        "scripts/validate_security_push_background_v25.py",
        "python3 scripts/validate_native_push_producer_boundary_v25.py",
        "python3 scripts/validate_security_push_background_v25.py",
        "node scripts/test_security_push_policy_v25.mjs",
        "node scripts/test_security_push_receipts_v25.mjs",
        "node scripts/test_security_push_network_v25.mjs",
    ):
        assert_contains(text, needle, "CI frontière push")


def main() -> None:
    run_self_tests()
    validate_approved_native_push_emitter()
    validate_payload_policy()
    validate_receipt_policy()
    validate_bridge()
    validate_storage_contract()
    validate_mobile_registration_and_receiver()
    validate_workflow()
    print(
        "OK native push V25: orchestrateur unique, transport Expo unique, payload minimal, receipts bornés à 1000, "
        "file privée 15min/24h sans contenu utilisateur, DeviceNotRegistered traité et réception interne seulement."
    )


if __name__ == "__main__":
    main()
