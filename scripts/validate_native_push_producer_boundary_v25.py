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
APPROVED_PRODUCER = EDGE_FUNCTIONS / "security-context" / "index.ts"
PUSH_POLICY = EDGE_FUNCTIONS / "_shared" / "security-push-policy.mjs"
PUSH_POLICY_TEST = ROOT / "scripts" / "test_security_push_policy_v25.mjs"
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-native-push-producer-boundary-v25.yml"

PRODUCER_SIGNATURES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Expo Push API", re.compile(r"exp\.host/--/api/v2/push/send", re.I)),
    ("expo-server-sdk", re.compile(r"\bexpo-server-sdk\b", re.I)),
    ("sendPushNotificationsAsync", re.compile(r"\bsendPushNotificationsAsync\b")),
    ("ExpoPushMessage", re.compile(r"\bExpoPushMessage\b")),
)
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


def validate_approved_native_push_emitter() -> None:
    if not EDGE_FUNCTIONS.is_dir():
        fail("répertoire supabase/functions absent")

    producers: list[tuple[Path, list[str]]] = []
    for path in sorted(EDGE_FUNCTIONS.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SERVER_SUFFIXES:
            continue
        hits = producer_hits(path.read_text(encoding="utf-8"))
        if hits:
            producers.append((path, hits))

    if not producers:
        fail("le producteur push de sécurité attendu a disparu sans remplacement explicite")

    unexpected = [
        f"{path.relative_to(ROOT)} ({', '.join(hits)})"
        for path, hits in producers
        if path != APPROVED_PRODUCER
    ]
    if unexpected:
        fail(
            "producteur Expo/native non approuvé détecté: "
            + "; ".join(unexpected)
            + ". Toute nouvelle surface d’émission exige un contrat de payload et des tests dédiés."
        )

    if len(producers) != 1 or producers[0][0] != APPROVED_PRODUCER:
        fail("un seul producteur Expo/native est autorisé: supabase/functions/security-context/index.ts")

    text = read(APPROVED_PRODUCER)
    required = (
        "from '../_shared/security-push-policy.mjs'",
        "buildSecurityPushMessage(endpoint.expo_push_token, outcome)",
        "offset += SECURITY_PUSH_MAX_BATCH",
        "endpoints.slice(offset, offset + SECURITY_PUSH_MAX_BATCH)",
        "endpointBatch[index]?.id",
        "fetch('https://exp.host/--/api/v2/push/send'",
        "console.warn('[security-context] Expo Push HTTP', response.status)",
    )
    for needle in required:
        assert_contains(text, needle, "producteur push approuvé")

    forbidden = (
        "data: { path:",
        "await response.text()",
        "console.warn('[security-context] envoi push impossible', error)",
        "console.warn('[security-context] endpoints push indisponibles', error.message)",
    )
    for needle in forbidden:
        if needle in text:
            fail(f"le producteur contourne la politique minimale ou journalise trop de détails: {needle}")


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


def validate_bridge() -> None:
    text = read(BRIDGE)
    assert_contains(text, "rpc('security_register_push_endpoint'", "enregistrement via RPC")
    assert_contains(text, "rpc('security_disable_push_for_device'", "désactivation via RPC")
    assert_contains(text, "p_expo_push_token:token", "token transmis uniquement au RPC")
    if re.search(r"\bfetch\s*\(", text):
        fail("le bridge push ne doit pas envoyer directement le token avec fetch()")
    hits = producer_hits(text)
    if hits:
        fail(f"le bridge navigateur ne doit pas devenir un émetteur Expo: {', '.join(hits)}")


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

    dangerous_grant = re.compile(
        r"grant\s+(?:all(?:\s+privileges)?|select|insert|update|delete)"
        r"(?:\s*,\s*(?:select|insert|update|delete))*"
        r"\s+on\s+table\s+public\.security_push_endpoints\s+to\s+[^;]*\b(?:public|anon|authenticated)\b",
        re.I,
    )
    disable_rls = re.compile(
        r"alter\s+table\s+public\.security_push_endpoints\s+disable\s+row\s+level\s+security",
        re.I,
    )
    for path in sorted(MIGRATIONS.glob("*.sql")):
        sql = path.read_text(encoding="utf-8")
        if dangerous_grant.search(sql):
            fail(f"ACL directe interdite sur security_push_endpoints: {path.relative_to(ROOT)}")
        if disable_rls.search(sql):
            fail(f"RLS désactivée sur security_push_endpoints: {path.relative_to(ROOT)}")
        if producer_hits(sql):
            fail(f"émission Expo/native interdite dans une migration SQL: {path.relative_to(ROOT)}")


def validate_mobile_registration_and_receiver() -> None:
    text = read(MOBILE_APP)
    required = (
        "Notifications.getExpoPushTokenAsync({ projectId: id })",
        "SecureStore.setItemAsync(PUSH_TOKEN_STORAGE, token)",
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
        "scripts/validate_native_push_producer_boundary_v25.py",
        "python3 scripts/validate_native_push_producer_boundary_v25.py",
        "node scripts/test_security_push_policy_v25.mjs",
    ):
        assert_contains(text, needle, "CI frontière push")


def main() -> None:
    run_self_tests()
    validate_approved_native_push_emitter()
    validate_payload_policy()
    validate_bridge()
    validate_storage_contract()
    validate_mobile_registration_and_receiver()
    validate_workflow()
    print(
        "OK native push V25: producteur unique approuvé, payload minimal testé, lots bornés à 100, "
        "logs Expo minimisés, token derrière service_role et réception interne seulement."
    )


if __name__ == "__main__":
    main()
