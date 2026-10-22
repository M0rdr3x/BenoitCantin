#!/usr/bin/env python3
"""Contrat transversal minimal de sécurité (hors réseau et sans secrets CI).

Les validations locales garantissent la configuration du dépôt, pas l'état
réel de l'hébergeur, de Supabase Auth ou des règles GitHub.
"""
from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ORIGIN = "https://gpvivleexywljowcqkru.supabase.co"
PROJECT_WSS = "wss://gpvivleexywljowcqkru.supabase.co"
DENIED_PATHS = {
    "/.github/*", "/supabase/*", "/scripts/*", "/mobile-native/*",
    "/docs/*", "/tests/*", "/.git/*",
    "/.env*", "/.gitignore", "/netlify.toml",
}
PUBLIC_EDGE_FUNCTIONS = {
    "get-document-url",  # autorisation par document et niveau d'accès
    "send-game-report",  # téléchargement anonyme : surveiller l'abus de ressources
    "life-story-delivery",  # jeton opaque à usage borné et vérifié côté serveur
}
PINNED_ACTION = re.compile(r"^actions/(?:checkout|setup-python)@[0-9a-f]{40}$")


def inspect_netlify(raw: str, label: str, root_site: bool) -> list[str]:
    errors: list[str] = []
    try:
        cfg = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        return [f"{label}: TOML invalide : {exc}"]
    headers = {item.get("for"): item.get("values", {}) for item in cfg.get("headers", [])}
    global_headers = headers.get("/*", {})
    for name in ("X-Content-Type-Options", "Strict-Transport-Security",
                 "Referrer-Policy", "Permissions-Policy", "Cross-Origin-Opener-Policy",
                 "X-Permitted-Cross-Domain-Policies"):
        if not global_headers.get(name):
            errors.append(f"{label}: en-tête global absent: {name}")
    if global_headers.get("X-Content-Type-Options") != "nosniff":
        errors.append(f"{label}: X-Content-Type-Options doit être nosniff")
    hsts = global_headers.get("Strict-Transport-Security", "")
    if not re.search(r"(?:^|;)\s*max-age=(?:[3-9][0-9]{7,}|[1-9][0-9]{8,})\b", hsts):
        errors.append(f"{label}: HSTS insuffisant")
    csp = global_headers.get("Content-Security-Policy", "")
    for directive in ("default-src 'self'", "base-uri 'self'", "object-src 'self'",
                      "frame-ancestors 'self'", "form-action 'self'",
                      PROJECT_ORIGIN, PROJECT_WSS):
        if directive not in csp:
            errors.append(f"{label}: CSP incomplète : {directive}")
    if not re.search(r"(?:^|;)\s*connect-src\s+[^;]*" + re.escape(PROJECT_ORIGIN), csp):
        errors.append(f"{label}: connect-src ne permet pas l'API SINJIRA")
    if "connect-src *" in csp or "default-src *" in csp or "script-src *" in csp:
        errors.append(f"{label}: source CSP non bornée")
    redirects = {item.get("from"): item for item in cfg.get("redirects", [])}
    for path in sorted(DENIED_PATHS):
        rule = redirects.get(path, {})
        if (rule.get("status") != 404 or rule.get("to") != "/404.html"
                or rule.get("force") is not True):
            errors.append(f"{label}: source interne non bloquée sur Netlify: {path}")
    if root_site:
        for protected in ("/compte/*", "/app/*", "/admin/*", "/Admin/*",
                          "/administration.html", "/supabase/*", "/histoire-de-vie/*"):
            policy = headers.get(protected, {})
            if "no-store" not in policy.get("Cache-Control", ""):
                errors.append(f"{label}: cache privé non interdit: {protected}")
            if "noindex" not in policy.get("X-Robots-Tag", ""):
                errors.append(f"{label}: indexation espace privé non interdite: {protected}")
    return errors


def inspect_supabase_config(raw: str) -> list[str]:
    try:
        cfg = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        return [f"supabase/config.toml: TOML invalide : {exc}"]
    functions = cfg.get("functions", {})
    errors: list[str] = []
    for name, data in functions.items():
        actual = data.get("verify_jwt")
        expected = name not in PUBLIC_EDGE_FUNCTIONS
        if actual is not expected:
            errors.append(f"supabase/config.toml: JWT inattendu pour {name}: {actual!r}")
    if set(name for name, data in functions.items() if data.get("verify_jwt") is False) != PUBLIC_EDGE_FUNCTIONS:
        errors.append("supabase/config.toml: inventaire public JWT désaligné")
    if cfg.get("auth", {}).get("minimum_password_length", 0) < 12:
        errors.append("supabase/config.toml: longueur minimale < 12")
    return errors


def inspect_nova_workflow(raw: str) -> list[str]:
    label = ".github/workflows/validate-nova-participation.yml"
    errors: list[str] = []
    targets = re.findall(r"^\s*uses:\s*(\S+)", raw, flags=re.M)
    if len(targets) != 2 or any(not PINNED_ACTION.fullmatch(item) for item in targets):
        errors.append(f"{label}: actions non épinglées à des SHA 40 caractères")
    if raw.count("persist-credentials: false") != 1 or "persist-credentials: true" in raw:
        errors.append(f"{label}: credentials persistés ou contrôle absent")
    if "permissions:\n  contents: read" not in raw or "contents: write" in raw:
        errors.append(f"{label}: permissions non minimales")
    if "runs-on: ubuntu-24.04" not in raw or "ubuntu-latest" in raw:
        errors.append(f"{label}: runner non figé")
    if "python-version: '3.12.14'" not in raw:
        errors.append(f"{label}: Python non figé")
    if "${{ secrets." in raw or "pull_request_target:" in raw:
        errors.append(f"{label}: secret ou contexte PR dangereux")
    return errors


def inspect_sources() -> list[str]:
    return (
        inspect_netlify((ROOT / "netlify.toml").read_text("utf-8"), "netlify.toml", True)
        + inspect_netlify((ROOT / "projets/projet-nova/netlify.toml").read_text("utf-8"),
                          "projets/projet-nova/netlify.toml", False)
        + inspect_supabase_config((ROOT / "supabase/config.toml").read_text("utf-8"))
        + inspect_nova_workflow((ROOT / ".github/workflows/validate-nova-participation.yml").read_text("utf-8"))
    )


def self_test() -> None:
    root = (ROOT / "netlify.toml").read_text("utf-8")
    edge = (ROOT / "supabase/config.toml").read_text("utf-8")
    workflow = (ROOT / ".github/workflows/validate-nova-participation.yml").read_text("utf-8")
    failures = (
        inspect_netlify(root.replace("Strict-Transport-Security", "Disabled-HSTS", 1), "test", True),
        inspect_netlify(root.replace(PROJECT_ORIGIN, "https://other.invalid", 1), "test", True),
        inspect_netlify(root.replace('force = true', 'force = false', 1), "test", True),
        inspect_supabase_config(edge.replace("[functions.admin-console]\nverify_jwt = true",
                                             "[functions.admin-console]\nverify_jwt = false", 1)),
        inspect_nova_workflow(workflow.replace("actions/checkout@", "actions/checkout@v6 # ", 1)),
        inspect_nova_workflow(workflow.replace("persist-credentials: false", "persist-credentials: true", 1)),
    )
    for i, issues in enumerate(failures, start=1):
        if not issues:
            raise AssertionError(f"Mutation de sécurité #{i} non détectée")
    print(f"OK auto-tests sécurité : {len(failures)} mutations détectées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = inspect_sources()
    for error in errors:
        print("ÉCHEC:", error)
    if errors:
        return 1
    print("OK contrat de sécurité : en-têtes, chemins internes, cache privé, CSP Supabase, JWT Edge et CI Nova.")
    print("L'hôte public, les réglages Supabase Auth et la protection GitHub doivent être vérifiés séparément.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
