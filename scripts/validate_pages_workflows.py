#!/usr/bin/env python3
"""Empêche une publication Pages accidentelle par une régression du workflow manuel."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / ".github/workflows/deploy-pages-controlled.yml"
CHECKOUT_SHA = "d23441a48e516b6c34aea4fa41551a30e30af803"
JEKYLL_SHA = "44a6e6beabd48582f863aeeb6cb2151cc1716697"
UPLOAD_SHA = "56afc609e74202658d3ffba0e8f6dda462b719fa"
DEPLOY_SHA = "368f82528645a54fb793d4d04e342629a3f51346"


def validate(workflow: str) -> list[str]:
    errors: list[str] = []
    def need(ok: bool, name: str) -> None:
        if not ok:
            errors.append(name)
    need(workflow.startswith("name: Pages — déploiement isolé explicitement approuvé\n"),
         "Identité du workflow modifiée")
    need("on:\n  workflow_dispatch:\n" in workflow,
         "Déclenchement exclusivement manuel absent")
    need(not re.search(r"(?m)^  (?:push|pull_request|schedule|repository_dispatch|workflow_run):", workflow),
         "Publication automatique interdite")
    need("permissions:\n  contents: read\n" in workflow,
         "Permissions lecture seule globales manquantes")
    need("group: pages-production-controlled" in workflow,
         "Exclusion mutuelle des déploiements manquante")
    need("cancel-in-progress: false" in workflow,
         "Interruption d'un déploiement en cours interdite")
    need("test \"$EXPECTED_SHA\" = \"$GITHUB_SHA\"" in workflow,
         "Vérification SHA exact manquante")
    need("test \"$(git rev-parse HEAD)\" = \"$EXPECTED_SHA\"" in workflow,
         "Révision Git locale non vérifiée")
    need('test "$SOURCE" = "ACTIONS_ONLY"' in workflow,
         "Confirmation manuelle du mode Actions requise")
    need('test "$MODE" = "DRY_RUN" || test "$MODE" = "PUBLISH"' in workflow,
         "Choix des modes DRY_RUN/PUBLISH manquant")
    need("github.ref == 'refs/heads/main'" in workflow,
         "Publication limitée à main")
    need("inputs.mode == 'PUBLISH' && inputs.confirm_actions_source == 'ACTIONS_ONLY'" in workflow,
         "Publication non conditionnée au double consentement")
    need(workflow.count(f"uses: actions/checkout@{CHECKOUT_SHA}") == 2,
         "Checkout non épinglé ou nombre d'étapes modifié")
    need(workflow.count("persist-credentials: false") == 2,
         "Credentials checkout persistés")
    for tool, sha in {
        "actions/jekyll-build-pages": JEKYLL_SHA,
        "actions/upload-pages-artifact": UPLOAD_SHA,
        "actions/deploy-pages": DEPLOY_SHA,
    }.items():
        need(workflow.count(f"uses: {tool}@{sha}") == 1,
             f"Action non épinglée ou manquante: {tool}")
    uses = re.findall(r"(?m)^\s*uses:\s+(\S+)\s*$", workflow)
    need(len(uses) == 7, "Nombre d'actions externes inattendu")
    need(all(re.search(r"@[0-9a-f]{40}$", u) for u in uses),
         "Action non immuable détectée")
    need('      - name: Tracer l\'origine du publish' in workflow,
         "Etape de traçabilité du publish manquante")
    need("printf '%s\\n' '- Répertoire upload-pages-artifact : _site" in workflow,
         "Résumé de publication doit utiliser printf et non des backticks")
    need(workflow.count("path: _site") == 1,
         "L'artefact Pages doit être téléversé depuis _site exactement")
    need(re.search(r"(?m)^\s+path:\s*\.\s*$", workflow) is None,
         "Téléversement de la racine du dépôt interdit")
    need("python3 scripts/audit_pages_jekyll.py --source . --built _site" in workflow,
         "Audit réel de l'artefact absent")
    need("python3 scripts/verify_pages_live.py --check" in workflow,
         "Contrôle externe des chemins techniques absent")
    need("needs: deploy" in workflow,
         "Contrôle HTTP non dépendant du déploiement")
    need("pages: read" in workflow and "GH_PAGES_READ_TOKEN" in workflow,
         "Lecture de la configuration Pages manquante")
    need('settings.get("build_type") != "workflow"' in workflow,
         "Vérification API du mode GitHub Actions absente")
    need('settings.get("cname") != "www.benoitcantin.com"' in workflow,
         "Vérification API du domaine manquante")
    need('settings.get("https_enforced") is not True' in workflow,
         "Vérification API HTTPS forcé absente")
    need("pages: write" in workflow and "id-token: write" in workflow,
         "Identité Pages requise pour le seul job de publication")
    return errors


def smoke_summary_bash(workflow: str) -> None:
    """Exécuter le vrai résumé du workflow en local avec un SHA fictif, sans GitHub."""
    anchor = "      - name: Tracer l'origine du publish\n"
    if workflow.count(anchor) != 1:
        raise RuntimeError("Etape de résumé absente ou dupliquée")
    tail = workflow.split(anchor, 1)[1].split("\n  deploy:", 1)[0]
    start = "        run: |\n"
    if tail.count(start) != 1:
        raise RuntimeError("Bloc Bash de résumé invalide")
    raw_lines = tail.split(start, 1)[1].splitlines()
    if not raw_lines or any(not ln.startswith("          ") for ln in raw_lines if ln.strip()):
        raise RuntimeError("Indentation Bash incorrecte")
    script = "\n".join(ln[10:] if ln.startswith("          ") else "" for ln in raw_lines)
    if "`" in script:
        raise RuntimeError("Backticks interdits dans le résumé Bash")
    env = os.environ.copy()
    with tempfile.TemporaryDirectory() as directory:
        out = Path(directory) / "summary.md"
        env.update({
            "GITHUB_SHA": "a" * 40,
            "MODE": "DRY_RUN",
            "GITHUB_STEP_SUMMARY": str(out),
        })
        run = subprocess.run(
            ["bash"], input=script, text=True, capture_output=True,
            env=env, timeout=8, check=False,
        )
        if run.returncode != 0 or run.stderr:
            raise RuntimeError(
                "Résumé Bash invalide: " + (run.stderr.strip() or str(run.returncode))
            )
        rendered = out.read_text("utf-8")
        for expected in ("Source commit : " + "a" * 40,
                         "Mode : DRY_RUN",
                         "upload-pages-artifact : _site"):
            if expected not in rendered:
                raise RuntimeError("Résumé Bash incomplet: " + expected)


def self_test(workflow: str) -> None:
    errors = validate(workflow)
    if errors:
        raise SystemExit("Workflow sain rejeté: " + "; ".join(errors))
    smoke_summary_bash(workflow)
    mutations = {
        "Publication root": workflow.replace("path: _site", "path: .", 1),
        "Ouverture sur push": workflow.replace("  workflow_dispatch:\n", "  push:\n    branches: [main]\n  workflow_dispatch:\n", 1),
        "SHA non vérifié": workflow.replace('test "$EXPECTED_SHA" = "$GITHUB_SHA"', "true", 1),
        "Confirmation disparue": workflow.replace('test "$SOURCE" = "ACTIONS_ONLY"', "true", 1),
        "Autorisation deploy perdue": workflow.replace("inputs.mode == 'PUBLISH' && inputs.confirm_actions_source == 'ACTIONS_ONLY'", "inputs.mode == 'PUBLISH'", 1),
        "Vérification live supprimée": workflow.replace("python3 scripts/verify_pages_live.py --check", "echo SKIP", 1),
        "Identifiant non immuable": workflow.replace(f"actions/deploy-pages@{DEPLOY_SHA}", "actions/deploy-pages@v5", 1),
        "Résumé Bash avec substitution": workflow.replace(
            "printf '%s\\n' '- Répertoire upload-pages-artifact : _site (jamais la racine)'",
            'echo "- Répertoire upload-pages-artifact : `_site`"',
            1,
        ),
        "API mode Pages supprimée": workflow.replace('settings.get("build_type") != "workflow"', 'False', 1),
        "HTTPS forcé non vérifié": workflow.replace('settings.get("https_enforced") is not True', 'False', 1),
    }
    for name, candidate in mutations.items():
        if candidate == workflow or not validate(candidate):
            raise SystemExit(f"Mutation interdite non détectée: {name}")
    print(f"OK workflow Pages : {len(mutations)} régressions dangereuses détectées, résumé Bash exécuté")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    workflow = PATH.read_text("utf-8")
    if args.self_test:
        self_test(workflow)
        return 0
    errors = validate(workflow)
    for error in errors:
        print("ERREUR: " + error)
    if errors:
        return 1
    print("OK workflow Pages : manuel, SHA exact, artefact isolé, contrôle HTTPS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
