#!/usr/bin/env python3
"""Provisionne les comptes famille créateur sans inscrire leurs courriels dans Git."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
ENV_EMAILS = "SINJIRA_CREATOR_FAMILY_EMAILS"
ENV_URL = "SUPABASE_URL"
ENV_KEY = "SUPABASE_SERVICE_ROLE_KEY"
ROOT = Path(__file__).resolve().parents[1]
SUPABASE_CONFIG = ROOT / "supabase/config.toml"
PROJECT_ID_RE = re.compile(r'^\\s*project_id\\s*=\\s*"([a-z0-9-]+)"\\s*

def parse_emails(raw: str) -> list[str]:
    normalized = raw.replace(";", ",").replace("\n", ",")
    values: list[str] = []
    seen: set[str] = set()
    for item in normalized.split(","):
        email = item.strip().lower()
        if not email:
            continue
        if len(email) > 320 or not EMAIL_RE.fullmatch(email):
            raise ValueError("Adresse de compte familial invalide.")
        if email not in seen:
            seen.add(email)
            values.append(email)
    if not values:
        raise ValueError(f"{ENV_EMAILS} ne contient aucun compte.")
    if len(values) > 10:
        raise ValueError("Maximum 10 comptes familiaux par exécution.")
    return values


def expected_supabase_host() -> str:
    try:
        config = SUPABASE_CONFIG.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError("Impossible de lire supabase/config.toml.") from exc
    match = PROJECT_ID_RE.search(config)
    if not match:
        raise ValueError("project_id Supabase canonique introuvable.")
    return f"{match.group(1)}.supabase.co"


def rpc_url(base_url: str) -> str:
    raw = base_url.strip()
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("SUPABASE_URL invalide.") from exc

    if parsed.scheme.lower() != "https":
        raise ValueError("SUPABASE_URL doit utiliser https://.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("SUPABASE_URL ne doit contenir ni identifiants, ni query, ni fragment.")
    if parsed.path not in ("", "/"):
        raise ValueError("SUPABASE_URL doit pointer vers la racine du projet.")
    if port not in (None, 443):
        raise ValueError("SUPABASE_URL doit utiliser le port HTTPS standard.")

    expected_host = expected_supabase_host()
    if (parsed.hostname or "").lower() != expected_host:
        raise ValueError("SUPABASE_URL ne correspond pas au projet Supabase canonique.")

    return f"https://{expected_host}/rest/v1/rpc/set_sinjira_catalog_family_access_by_email"


def provision(url: str, service_key: str, emails: list[str], enabled: bool) -> None:
    endpoint = rpc_url(url)
    if not service_key.strip():
        raise ValueError(f"{ENV_KEY} est requis.")

    for index, email in enumerate(emails, start=1):
        body = json.dumps({"p_email": email, "p_enabled": enabled}).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=body,
            method="POST",
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status < 200 or response.status >= 300:
                    raise RuntimeError(f"RPC refusé avec HTTP {response.status}.")
                response.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Provisionnement du compte familial {index}/{len(emails)} refusé (HTTP {exc.code})."
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Provisionnement du compte familial {index}/{len(emails)} impossible."
            ) from exc

        state = "activé" if enabled else "désactivé"
        print(f"Compte familial {index}/{len(emails)} : accès {state}.")


def self_test() -> None:
    assert parse_emails("A@example.test,b@example.test") == [
        "a@example.test",
        "b@example.test",
    ]
    assert parse_emails("A@example.test; a@example.test\nB@example.test") == [
        "a@example.test",
        "b@example.test",
    ]
    canonical = f"https://{expected_supabase_host()}/"
    assert rpc_url(canonical).endswith(
        "/rest/v1/rpc/set_sinjira_catalog_family_access_by_email"
    )

    rejected_hosts = 0
    for value in (
        "https://example.invalid",
        f"https://{expected_supabase_host()}.example.invalid",
        f"https://user:pass@{expected_supabase_host()}",
        f"https://{expected_supabase_host()}/unexpected-path",
        f"https://{expected_supabase_host()}:444",
    ):
        try:
            rpc_url(value)
        except ValueError:
            rejected_hosts += 1
    assert rejected_hosts == 5

    rejected = 0
    for value in ("", "not-an-email", "a@", "@example.test"):
        try:
            parse_emails(value)
        except ValueError:
            rejected += 1
    assert rejected == 4
    print("OK provisionnement famille créateur: parsing, déduplication et hôte Supabase canonique validés.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--disable", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    emails = parse_emails(os.getenv(ENV_EMAILS, ""))
    provision(
        os.getenv(ENV_URL, ""),
        os.getenv(ENV_KEY, ""),
        emails,
        enabled=not args.disable,
    )


if __name__ == "__main__":
    main()
, re.MULTILINE)


def parse_emails(raw: str) -> list[str]:
    normalized = raw.replace(";", ",").replace("\n", ",")
    values: list[str] = []
    seen: set[str] = set()
    for item in normalized.split(","):
        email = item.strip().lower()
        if not email:
            continue
        if len(email) > 320 or not EMAIL_RE.fullmatch(email):
            raise ValueError("Adresse de compte familial invalide.")
        if email not in seen:
            seen.add(email)
            values.append(email)
    if not values:
        raise ValueError(f"{ENV_EMAILS} ne contient aucun compte.")
    if len(values) > 10:
        raise ValueError("Maximum 10 comptes familiaux par exécution.")
    return values


def rpc_url(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base.startswith("https://"):
        raise ValueError("SUPABASE_URL doit utiliser https://.")
    return base + "/rest/v1/rpc/set_sinjira_catalog_family_access_by_email"


def provision(url: str, service_key: str, emails: list[str], enabled: bool) -> None:
    endpoint = rpc_url(url)
    if not service_key.strip():
        raise ValueError(f"{ENV_KEY} est requis.")

    for index, email in enumerate(emails, start=1):
        body = json.dumps({"p_email": email, "p_enabled": enabled}).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=body,
            method="POST",
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status < 200 or response.status >= 300:
                    raise RuntimeError(f"RPC refusé avec HTTP {response.status}.")
                response.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Provisionnement du compte familial {index}/{len(emails)} refusé (HTTP {exc.code})."
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Provisionnement du compte familial {index}/{len(emails)} impossible."
            ) from exc

        state = "activé" if enabled else "désactivé"
        print(f"Compte familial {index}/{len(emails)} : accès {state}.")


def self_test() -> None:
    assert parse_emails("A@example.test,b@example.test") == [
        "a@example.test",
        "b@example.test",
    ]
    assert parse_emails("A@example.test; a@example.test\nB@example.test") == [
        "a@example.test",
        "b@example.test",
    ]
    assert rpc_url("https://example.supabase.co/").endswith(
        "/rest/v1/rpc/set_sinjira_catalog_family_access_by_email"
    )

    rejected = 0
    for value in ("", "not-an-email", "a@", "@example.test"):
        try:
            parse_emails(value)
        except ValueError:
            rejected += 1
    assert rejected == 4
    print("OK provisionnement famille créateur: parsing, déduplication et garde URL validés.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--disable", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    emails = parse_emails(os.getenv(ENV_EMAILS, ""))
    provision(
        os.getenv(ENV_URL, ""),
        os.getenv(ENV_KEY, ""),
        emails,
        enabled=not args.disable,
    )


if __name__ == "__main__":
    main()
