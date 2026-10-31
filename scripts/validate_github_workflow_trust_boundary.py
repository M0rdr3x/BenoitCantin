#!/usr/bin/env python3
"""Règles de confiance transversales pour les GitHub Actions du site.

Tout workflow est vérifié, pas seulement les fichiers modifiés par une PR.
Aucun token, secret, output de pipeline ou contenu utilisateur n'est analysé.
L'exécution est purement statique et ne nécessite aucune dépendance réseau.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
# La seule écriture GitHub attendue dans les workflows actuels est le
# commit HTML limité de la normalisation SEO (voir validateur dédié).
APPROVED_WRITE_JOBS = {
    ("nova-seo-normalize.yml", "commit"),
}

APPROVED_PAGES_OIDC_JOB = ("deploy-github-pages-isolated.yml", "deploy")


def validate_pages_deploy_contract(source: str) -> list[str]:
    """Exception OIDC strictement limitée à l'action native Pages.
    
    La publication technique doit rester un workflow manuel avec artefact
    isolé, double consentement, SHA exact et job deploy sans code externe.
    """
    errors = []
    if "on:\n  workflow_dispatch:" not in source:
        errors.append("Pages: déclenchement manuel seul obligatoire")
    for trigger in ("push", "pull_request", "schedule", "workflow_run", "pull_request_target"):
        if re.search(rf"(?m)^  {trigger}:", source):
            errors.append("Pages: déclencheur automatique/privilégié interdit")
    start = source.find("  deploy:\n")
    if start < 0:
        return errors + ["Pages: job deploy absent"]
    tail = source[start:]
    next_job = re.search(r"(?m)^  [a-zA-Z][a-zA-Z0-9_-]*:\s*$", tail[10:])
    deploy = tail if not next_job else tail[:next_job.start()+10]
    mandatory = (
        "    needs: build",
        "    permissions:\n      pages: write\n      id-token: write",
        "      name: github-pages",
        "inputs.confirm_containment == 'CONTAIN'",
        "inputs.acknowledge_header_gap == 'ACK_HEADER_GAP'",
        "uses: actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346",
    )
    if not all(marker in deploy for marker in mandatory):
        errors.append("Pages: contrat déploiement manuel/permissions/artefact non conforme")
    if source.count("      id-token: write") != 1 or source.count("      pages: write") != 1:
        errors.append("Pages: privilèges de déploiement répétés")
    if any(marker in deploy for marker in (
        "run:", "actions/checkout@", "${{ secrets.", "continue-on-error:", "uses: ./",
    )):
        errors.append("Pages: exécution de code ou secret dans le job privilégié interdite")
    if deploy.count("uses: ") != 1:
        errors.append("Pages: seule l'action immuable de déploiement est autorisée")
    if "python3 scripts/build_netlify_public.py --output _site --security-containment" not in source:
        errors.append("Pages: générateur public isolé obligatoire")
    if "path: _site" not in source:
        errors.append("Pages: seul l'artefact isolé _site peut être téléversé")
    return errors
PRIVILEGED_EVENTS = frozenset({"pull_request_target", "workflow_run"})
SHA_ACTION = re.compile(r"^[0-9a-f]{40}$")
ACTION_LINE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.I)
EVENT_LINE = re.compile(r"^  ([A-Za-z_][A-Za-z_0-9-]*):(?:\s*(?:\[\s*.*|.*))?$")
JOB_LINE = re.compile(r"^  ([A-Za-z_][A-Za-z_0-9-]*):\s*$")
WRITE_SCOPE = re.compile(r"^\s+([a-z-]+):\s*write\s*$", re.I)


def active_lines(source: str) -> list[tuple[int, str]]:
    return [(i, line) for i, line in enumerate(source.splitlines(), 1)
            if line.strip() and not line.lstrip().startswith("#")]


def violations(filename: str, source: str) -> list[str]:
    issues: list[str] = []
    lines = active_lines(source)
    if re.search(r"(?mi)^\s*permissions:\s*(?:write-all|read-all)\s*$", source):
        issues.append("Permissions globales implicites interdites")
    root_permissions = [line for _, line in lines if line.startswith("permissions:")]
    if root_permissions != ["permissions:"]:
        issues.append("Une seule déclaration globale permissions en bloc est exigée")
    # La notation YAML en flux et les permissions de job en ligne ne doivent
    # pas contourner les règles d'indention conservatrices de cet auditeur.
    if any(re.match(r"^on:\s*\S", line) for _, line in lines):
        issues.append("Déclencheurs YAML en ligne non audités et interdits")
    if any(re.match(r"^    permissions:\s*\S", line) for _, line in lines):
        issues.append("Permissions de job en ligne non auditées et interdites")

    for number, line in lines:
        if re.match(r"^\s{2}(?:pull_request_target|workflow_run):", line):
            issues.append(f"Déclencheur privilégié non approuvé (ligne {number})")
        match = ACTION_LINE.match(line)
        if match:
            target = match.group(1)
            if target.startswith("./"):
                continue
            if target.startswith("docker://"):
                if "@sha256:" not in target:
                    issues.append(f"Action Docker sans digest immuable (ligne {number})")
                continue
            parts = target.rsplit("@", 1)
            if len(parts) != 2 or not SHA_ACTION.fullmatch(parts[1]):
                issues.append(f"Action tierce non épinglée SHA 40 (ligne {number})")
    # Scinder strictement au niveau YAML des jobs pour ne pas faire dépendre
    # la classification des permissions d'une simple occurrence ailleurs.
    in_jobs = False
    current_job = None
    current_permissions = False
    for number, line in lines:
        if line == "jobs:":
            in_jobs = True
            current_job = None
            continue
        if not in_jobs:
            if re.match(r"^  contents:\s*write\s*$", line):
                issues.append(f"Écriture globale sur le dépôt interdite (ligne {number})")
            if re.match(r"^  id-token:\s*write\s*$", line):
                issues.append(f"OIDC global non justifié (ligne {number})")
            continue
        if re.match(r"^[^ ]", line):
            in_jobs = False
            current_job = None
            continue
        job = JOB_LINE.match(line)
        if job and job.group(1) != "permissions":
            current_job = job.group(1)
            current_permissions = False
            continue
        if line == "    permissions:":
            current_permissions = True
            continue
        if line.startswith("    ") and not line.startswith("      "):
            current_permissions = False
        if current_permissions and re.match(r"^      contents:\s*write\s*$", line):
            if (filename, current_job) not in APPROVED_WRITE_JOBS:
                issues.append(f"Écriture GitHub non approuvée job {current_job} (ligne {number})")
        if re.match(r"^      pages:\s*write\s*$", line):
            if (filename, current_job) != APPROVED_PAGES_OIDC_JOB:
                issues.append(f"Publication Pages privilégiée non approuvée (ligne {number})")
        if re.match(r"^      id-token:\s*write\s*$", line):
            if (filename, current_job) != APPROVED_PAGES_OIDC_JOB:
                issues.append(f"Écriture OIDC non approuvée job {current_job} (ligne {number})")

    if filename == APPROVED_PAGES_OIDC_JOB[0]:
        issues.extend(validate_pages_deploy_contract(source))
    return issues


def check_repository(root: Path = WORKFLOWS) -> list[str]:
    if not root.is_dir() or root.is_symlink():
        return ["Répertoire Actions absent ou symbolique"]
    files = sorted([*root.glob("*.yml"), *root.glob("*.yaml")])
    if len(files) < 90:
        return [f"Inventaire GitHub Actions incomplet : {len(files)} workflows seulement"]
    errors: list[str] = []
    for file in files:
        if file.is_symlink() or not file.is_file():
            errors.append(f"{file.name}: workflow symbolique ou illisible")
            continue
        try:
            content = file.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            errors.append(f"{file.name}: lecture impossible")
            continue
        errors.extend(f"{file.name}: {violation}" for violation in violations(file.name, content))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("Utiliser --check")
    errors = check_repository()
    if errors:
        print(f"NO_GO : {len(errors)} anomalie(s) sur les workflows GitHub.")
        for item in errors[:35]:
            print("- " + item)
        if len(errors) > 35:
            print(f"- {len(errors)-35} autres anomalies.")
        return 1
    total = len(list(WORKFLOWS.glob("*.yml"))) + len(list(WORKFLOWS.glob("*.yaml")))
    print(f"PASS: {total} workflows GitHub, frontières de privilèges et actions épinglées.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
