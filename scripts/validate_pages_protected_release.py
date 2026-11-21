#!/usr/bin/env python3
"""Fail-closed contract for the isolated GitHub Pages publication workflow.

Static checks and mutation tests only: never deploy, access secrets, or call GitHub.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/deploy-github-pages-isolated.yml"
JOB_GUARD = (
    "    if: github.ref == 'refs/heads/main' && "
    "inputs.confirm_containment == 'CONTAIN' && "
    "inputs.acknowledge_header_gap == 'ACK_HEADER_GAP' && "
    "github.ref_protected == true"
)
PINNED_SCRIPT = "uses: actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd"
PINNED_DEPLOY = "uses: actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346"
SERVER_CHECK = "branch.protected !== true"
SHA_CHECK = "branch.commit?.sha !== context.sha"
EVENT_CHECK = "process.env.GITHUB_REF_PROTECTED !== 'true'"


def validate_text(source: str) -> list[str]:
    problems: list[str] = []
    _front, has_build, remaining = source.partition("\n  build:\n")
    build, has_deploy, deploy = remaining.partition("\n  deploy:\n")
    if not has_build or not has_deploy:
        return ["Jobs build/deploy isolés obligatoires."]

    for name, block in (("build", build), ("deploy", deploy)):
        if "\n" + JOB_GUARD + "\n" not in "\n" + block:
            problems.append(f"{name}: condition exacte main protégé / confirmations absente.")
    if "    needs: build\n" not in deploy:
        problems.append("Publication sans dépendance du build validé.")
    if (
        "      contents: read\n" not in deploy
        or "      pages: write\n" not in deploy
        or "      id-token: write\n" not in deploy
    ):
        problems.append("Permissions minimales de lecture/Pages/OIDC du déploiement absentes.")
    for name, required in (
        ("Contrôle serveur GitHub", "github.rest.repos.getBranch({ owner, repo, branch: 'main' })"),
        ("Contrôle protection au déclenchement", EVENT_CHECK),
        ("Refus de main non protégée", SERVER_CHECK),
        ("Refus de SHA dérivé", SHA_CHECK),
        ("Action de vérification épinglée", PINNED_SCRIPT),
        ("Action de publication épinglée", PINNED_DEPLOY),
    ):
        if required not in deploy:
            problems.append(f"{name} absent du job de déploiement.")

    check_pos = deploy.find(PINNED_SCRIPT)
    publish_pos = deploy.find(PINNED_DEPLOY)
    if check_pos < 0 or publish_pos < 0 or check_pos >= publish_pos:
        problems.append("Contrôle serveur absent ou placé après la publication.")
    if deploy.count(PINNED_DEPLOY) != 1:
        problems.append("La publication ne doit appeler deploy-pages qu'une fois.")
    if 'if [ "$EXPECTED_SHA" != "$GITHUB_SHA" ]; then' not in build:
        problems.append("Contrôle du SHA initial explicite absent.")
    if "continue-on-error: true" in source:
        problems.append("Le contournement des échecs de sécurité est interdit.")
    if "secrets." in source:
        problems.append("Aucun secret applicatif n'est nécessaire pour Pages.")
    return problems


def self_test(source: str) -> int:
    if validate_text(source):
        raise AssertionError("Le workflow de référence échoue : " + "; ".join(validate_text(source)))

    weakened_guard = JOB_GUARD.replace(" && github.ref_protected == true", "")
    scenarios = {
        "build sans protection": source.replace(
            "\n  build:\n" + JOB_GUARD, "\n  build:\n" + weakened_guard, 1
        ),
        "deploy sans protection": source.replace(
            "\n  deploy:\n", "\n  deploy:\n", 1
        ).replace("\n" + JOB_GUARD + "\n    permissions:\n      contents: read\n      pages: write",
                  "\n" + weakened_guard + "\n    permissions:\n      contents: read\n      pages: write", 1),
        "protection live supprimée": source.replace(SERVER_CHECK, "false", 1),
        "SHA live supprimé": source.replace(SHA_CHECK, "false", 1),
        "protection événement supprimée": source.replace(EVENT_CHECK, "false", 1),
        "action contrôle non épinglée": source.replace(PINNED_SCRIPT, "uses: actions/github-script@v7", 1),
        "permissions lecture retirées": source.replace(
            "      contents: read\n      pages: write", "      pages: write", 1
        ),
        "bypass des erreurs": source.replace(
            "\n  deploy:\n", "\n  deploy:\n    continue-on-error: true\n", 1
        ),
        "SHA initial ignoré": source.replace(
            'if [ "$EXPECTED_SHA" != "$GITHUB_SHA" ]; then', 'if false; then', 1
        ),
    }
    for title, changed in scenarios.items():
        if source == changed:
            raise AssertionError("Mutation non appliquée: " + title)
        if not validate_text(changed):
            raise AssertionError("Régression non détectée: " + title)
    return len(scenarios)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    workflow = WORKFLOW.read_text("utf-8")
    if args.self_test:
        count = self_test(workflow)
        print(f"PASS : {count} mutations de contrôle Pages dangereuses rejetées.")
    else:
        problems = validate_text(workflow)
        if problems:
            raise SystemExit("FAIL : " + " | ".join(problems))
        print("PASS : Pages exige main protégée et SHA revalidé côté serveur, avant publication.")


if __name__ == "__main__":
    main()
