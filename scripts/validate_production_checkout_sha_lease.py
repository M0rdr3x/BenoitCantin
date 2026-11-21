#!/usr/bin/env python3
"""Contrat production: checkout de main doit être identique au SHA déclencheur.

Les fichiers vérifiés ont accès au contexte environnement "production". Le
contrôle doit intervenir avant Python, les validateurs du dépôt, CLI et API.
Aucun jeton ni appel GitHub/Supabase n'est nécessaire pour ce contrat.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ".github/workflows/sinjira-v25-production-deploy.yml",
    ".github/workflows/sinjira-v25-auth-password-hardening.yml",
    ".github/workflows/sinjira-v25-employment-production.yml",
    ".github/workflows/sinjira-v25-personal-ai-production-readiness.yml",
)
CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
GUARD = """      - name: Vérifier le commit immuable avant code et secrets
        shell: bash
        run: |
          set -euo pipefail
          if [ "$GITHUB_REF" != "refs/heads/main" ] ||
             [[ ! "$GITHUB_SHA" =~ ^[0-9a-f]{40}$ ]] ||
             [ "$(git rev-parse --verify HEAD)" != "$GITHUB_SHA" ]; then
            echo "SECURITE : checkout différent du commit de déclenchement; arrêt sans exécuter le code récupéré." >&2
            exit 1
          fi

"""
CHECKOUT_STEP = "      - name: Checkout de main\n"
NEXT_STEP = "      - name: Configurer Python\n"


def validate(text: str) -> list[str]:
    errors: list[str] = []
    if text.count("    environment: production") != 1:
        errors.append("environment production unique requis")
    if text.count(CHECKOUT_STEP) != 1:
        errors.append("checkout main unique requis")
    if text.count(NEXT_STEP) != 1:
        errors.append("configuration Python unique requise")
    if text.count(GUARD) != 1:
        errors.append("contrôle du SHA et du refus fail-closed absent, déplacé ou modifié")
    if text.count("          ref: main") != 1:
        errors.append("checkout doit rester explicitement lié à main")
    if text.count(f"uses: {CHECKOUT}") != 1:
        errors.append("action checkout épinglée au SHA attendue")
    if text.count("persist-credentials: false") != 1:
        errors.append("checkout sans identifiants persistés requis")
    co = text.find(CHECKOUT_STEP)
    g = text.find(GUARD)
    py = text.find(NEXT_STEP)
    if min(co, g, py) >= 0:
        if not co < g < py:
            errors.append("contrôle du SHA doit suivre checkout et précéder toute exécution Python")
        else:
            # Refus des étapes cachées entre checkout et la barrière, ou entre
            # la barrière et Python qui pourraient exécuter du code non revu.
            before_guard = text[co:g]
            after_guard = text[g + len(GUARD):py]
            if before_guard.count("      - name: ") != 1 or "        run:" in before_guard:
                errors.append("aucun code exécuté entre checkout et contrôle SHA")
            if after_guard.strip():
                errors.append("étape intercalée ou contenu non autorisé avant Python")
            if "          ref: main" not in before_guard or CHECKOUT not in before_guard:
                errors.append("barrière ne suit pas le checkout attendu")
    return errors


def script_guard() -> str:
    body = GUARD.split("        run: |\n", 1)[1].rstrip("\n")
    return "\n".join(line[10:] for line in body.splitlines()) + "\n"


def runtime_self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="sinjira-workflow-sha-") as temp:
        root = Path(temp)
        def run_git(*args: str) -> str:
            proc = subprocess.run(["git", *args], cwd=root, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return proc.stdout.strip()
        run_git("init", "-q")
        run_git("config", "user.name", "Workflow contract")
        run_git("config", "user.email", "workflow-test@example.invalid")
        (root / "file.txt").write_text("one\n", encoding="utf-8")
        run_git("add", "file.txt")
        run_git("commit", "-qm", "first")
        sha = run_git("rev-parse", "HEAD")
        assert re.fullmatch(r"[0-9a-f]{40}", sha), "commit SHA-1 temporaire invalide"

        def check(expected: str, branch: str = "refs/heads/main") -> int:
            env = {**os.environ, "GITHUB_SHA": expected, "GITHUB_REF": branch}
            proc = subprocess.run(["bash", "-c", script_guard()], cwd=root, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
            return proc.returncode

        assert check(sha) == 0, "le SHA exact devrait être autorisé"
        assert check("0" * 40) != 0, "un SHA différent doit arrêter le job"
        assert check("truncated") != 0, "SHA non canonique interdit"
        assert check(sha, "refs/heads/evil") != 0, "hors main interdit"
        (root / "file.txt").write_text("two\n", encoding="utf-8")
        run_git("add", "file.txt")
        run_git("commit", "-qm", "second")
        assert check(sha) != 0, "changement de main entre trigger et checkout interdit"
        assert check(run_git("rev-parse", "HEAD")) == 0, "nouveau trigger valide"


def mutation_self_test() -> None:
    for name in WORKFLOWS:
        text = (ROOT / name).read_text(encoding="utf-8")
        assert not validate(text), f"version saine refusée: {name}: {validate(text)}"
        cases = {
            "garde supprimé": text.replace(GUARD, "", 1),
            "force branch plutôt que commit": text.replace(
                '$(git rev-parse --verify HEAD)', '$(git rev-parse --verify main)', 1),
            "SHA modifié": text.replace('"$GITHUB_SHA" ]; then', '"$GITHUB_REF" ]; then', 1),
            "pas de refus": text.replace("            exit 1\n          fi\n\n", "            exit 0\n          fi\n\n", 1),
            "garde après exécution Python": text.replace(GUARD + NEXT_STEP,
                NEXT_STEP + GUARD, 1),
            "garde dupliqué": text.replace(GUARD, GUARD + GUARD, 1),
            "checkout anonyme sans base": text.replace("          ref: main\n", "          ref: develop\n", 1),
        }
        for label, changed in cases.items():
            assert changed != text, f"mutation sans effet: {label} ({name})"
            assert validate(changed), f"mutation non détectée: {label} ({name})"


def main() -> int:
    all_errors = []
    for workflow in WORKFLOWS:
        path = ROOT / workflow
        if not path.is_file():
            all_errors.append(f"{workflow}: fichier absent")
            continue
        errors = validate(path.read_text(encoding="utf-8"))
        all_errors.extend(f"{workflow}: {msg}" for msg in errors)
    for error in all_errors:
        print("ECHEC:", error)
    if all_errors:
        return 1
    if "--self-test" in sys.argv[1:]:
        mutation_self_test()
        runtime_self_test()
        print("PASS: 28 mutations critiques détectées; bash testé avec 2 commits et SHA distincts.")
    else:
        print("PASS: 4 workflows production refusent tout checkout différent du SHA déclencheur.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
