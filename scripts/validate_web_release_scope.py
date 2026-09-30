#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WEB_RELEASE_BRANCH_PREFIX = "a1/web-release-"

ALLOWED_EXACT = {
    ".github/workflows/validate-site.yml",
    ".gitignore",
    "netlify.toml",
    "robots.txt",
    "sitemap.xml",
    "scripts/build_netlify_public.py",
    "scripts/validate_site.py",
    "scripts/validate_site_workflow_security.py",
    "scripts/validate_web_release_http.py",
    "scripts/validate_web_release_scope.py",
}

ALLOWED_PREFIXES = (
    ".well-known/",
    "assets/",
    "histoire-de-vie/",
    "projets/",
)

FORBIDDEN_PREFIXES = (
    ".github/",
    "Admin/",
    "admin/",
    "app/",
    "compte/",
    "docs/",
    "mobile-native/",
    "supabase/",
    "tests/",
)


def normalize(path: str) -> str:
    return PurePosixPath(path.strip().replace("\\", "/")).as_posix()


def allowed(path: str) -> bool:
    rel = normalize(path)
    if not rel or rel == ".":
        return False
    if rel in ALLOWED_EXACT:
        return True
    if "/" not in rel and rel.endswith(".html"):
        return True
    return any(rel.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def validate_paths(paths: list[str]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for raw in paths:
        rel = normalize(raw)
        if not rel or rel in seen:
            continue
        seen.add(rel)

        if any(rel.startswith(prefix) for prefix in FORBIDDEN_PREFIXES) and rel not in ALLOWED_EXACT:
            errors.append(f"{rel}: surface interdite dans une release web-only")
            continue
        if not allowed(rel):
            errors.append(f"{rel}: fichier hors allowlist de la release web-only")
    return errors


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} a échoué")
    return proc.stdout.strip()


def event_refs() -> tuple[str, str]:
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH absent")
    data = json.loads(Path(event_path).read_text(encoding="utf-8"))
    pr = data.get("pull_request") or {}
    base = ((pr.get("base") or {}).get("sha") or "").strip()
    head = ((pr.get("head") or {}).get("sha") or "").strip()
    if not base or not head:
        raise RuntimeError("SHA base/head de pull_request absents")
    return base, head


def changed_paths(base: str | None = None, head: str | None = None) -> list[str]:
    if not base or not head:
        base, head = event_refs()

    for sha in (base, head):
        git("cat-file", "-e", f"{sha}^{{commit}}")

    output = git("diff", "--name-only", "--diff-filter=ACMR", f"{base}...{head}")
    return [line.strip() for line in output.splitlines() if line.strip()]


def self_test() -> None:
    valid = [
        ".github/workflows/validate-site.yml",
        ".gitignore",
        "index.html",
        "assistant.html",
        "transparence-ia.html",
        "assets/js/site.js",
        "assets/css/ai-transparency.css",
        "projets/projet-nova/script.js",
        "netlify.toml",
        "robots.txt",
        "sitemap.xml",
        "scripts/build_netlify_public.py",
        "scripts/validate_site_workflow_security.py",
        "scripts/validate_web_release_http.py",
        "scripts/validate_web_release_scope.py",
    ]
    if validate_paths(valid):
        raise SystemExit("ERREUR auto-test web-only: allowlist valide rejetée")

    forbidden = [
        "supabase/migrations/20260930000000_test.sql",
        "supabase/functions/example/index.ts",
        "compte/index.html",
        "admin/index.html",
        "Admin/index.html",
        "app/index.html",
        "docs/internal.md",
        "mobile-native/App.tsx",
        "tests/e2e/test_public_site.py",
        ".github/workflows/production.yml",
        "scripts/other_validator.py",
        "README.md",
    ]
    missed = [path for path in forbidden if not validate_paths([path])]
    if missed:
        raise SystemExit("ERREUR auto-test web-only: chemins interdits non détectés: " + ", ".join(missed))

    print(f"OK auto-tests web-only: {len(valid)} chemins autorisés et {len(forbidden)} interdits correctement classés.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--base")
    parser.add_argument("--head")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    head_ref = os.environ.get("GITHUB_HEAD_REF", "")
    if event_name == "pull_request" and not head_ref.startswith(WEB_RELEASE_BRANCH_PREFIX):
        print(f"OK portée web-only: contrôle non requis pour la branche {head_ref!r}.")
        return 0

    try:
        paths = changed_paths(args.base, args.head)
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERREUR portée web-only: impossible de déterminer le diff: {exc}", file=sys.stderr)
        return 1

    errors = validate_paths(paths)
    if errors:
        print(f"ECHEC portée web-only: {len(errors)} fichier(s) hors périmètre.", file=sys.stderr)
        for error in errors:
            print("- " + error, file=sys.stderr)
        return 1

    print(f"OK portée web-only: {len(paths)} fichier(s) modifié(s), tous dans l’allowlist de release publique.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
