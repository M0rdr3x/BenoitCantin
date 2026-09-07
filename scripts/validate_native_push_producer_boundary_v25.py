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


def validate_no_native_push_emitter() -> None:
    if not EDGE_FUNCTIONS.is_dir():
        fail("répertoire supabase/functions absent")
    offenders: list[str] = []
    for path in sorted(EDGE_FUNCTIONS.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SERVER_SUFFIXES:
            continue
        hits = producer_hits(path.read_text(encoding="utf-8"))
        if hits:
            offenders.append(f"{path.relative_to(ROOT)} ({', '.join(hits)})")
    if offenders:
        fail(
            "un émetteur Expo/native apparaît côté serveur sans contrat de payload approuvé: "
            + "; ".join(offenders)
            + ". Ajouter d'abord un builder testé qui borne data.path à un chemin SINJIRA interne "
            "et interdit secrets/identifiants sensibles."
        )


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
        r"grant\s+(?:all|select|insert|update|delete)(?:\s*,\s*(?:select|insert|update|delete))*"
        r"\s+on\s+table\s+public\.security_push_endpoints\s+to\s+(?:public|anon|authenticated)\b",
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


def main() -> None:
    run_self_tests()
    validate_no_native_push_emitter()
    validate_bridge()
    validate_storage_contract()
    validate_mobile_registration_and_receiver()
    print(
        "OK native push V25: aucun émetteur Expo serveur implicite, token stocké derrière service_role, "
        "bridge limité aux RPC et réception bornée à un chemin SINJIRA interne."
    )


if __name__ == "__main__":
    main()
