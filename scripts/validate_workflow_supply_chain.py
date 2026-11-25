#!/usr/bin/env python3
"""Contrat statique des actions CI : références immuables et droits minimaux.

Scanner local de fichiers YAML, sans exécuter de code GitHub, sans réseau
et sans secrets. Ce contrôle complète les protections serveur de main.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
ACTION_LINE = re.compile(r"^\s*(?:-\s*)?uses:\s*(\S+)")
IMMUTABLE_ACTION = re.compile(r"^[^@\s]+@[a-f0-9]{40}$")
IMMUTABLE_DOCKER = re.compile(r"^docker://[^@\s]+@sha256:[a-f0-9]{64}$")



def has_privileged_pr_trigger(source: str) -> bool:
    """Refuser pull_request_target dans les formes YAML bloc, liste et inline.

    On n'interprète que l'événement racine `on` : les exemples dans les
    commentaires et les commandes shell ne doivent pas produire de faux positifs.
    """
    lines = source.splitlines()
    event = re.compile(r"(?<![\w])['\"]?pull_request_target['\"]?(?![\w])")
    for index, line in enumerate(lines):
        root = re.match(r"^(?:on|['\"]on['\"])\s*:\s*(.*)$", line)
        if not root:
            continue
        if event.search(root.group(1).split("#", 1)[0]):
            return True
        for child in lines[index + 1:]:
            if child.strip() and not child[0].isspace() and not child.lstrip().startswith("#"):
                break
            candidate = child.strip().split("#", 1)[0].strip()
            if re.fullmatch(r"['\"]?pull_request_target['\"]?\s*:\s*.*", candidate):
                return True
            if re.fullmatch(r"-\s*['\"]?pull_request_target['\"]?", candidate):
                return True
    return False


def root_permissions_are_explicit(source: str) -> bool:
    """Reject only-job, embedded-run, missing and duplicate root permissions.

    A job-scoped permission does not establish a least-privilege default for
    OTHER jobs. Matching indented lines can also mistake `run: |` text for
    a GitHub Actions permission policy. Scan only column-zero YAML keys.
    """
    root_keys = re.findall(r'(?m)^(?:permissions|["\']permissions["\'])\s*:', source)
    return len(root_keys) == 1



def inspect_netlify_staging_secrets(source: str) -> list[str]:
    """Require credentials only in the two canonical deployment step envs."""
    errors: list[str] = []
    expected = {"preview_deploy", "production_deploy"}
    seen: set[str] = set()
    blocks = re.split(r"(?m)^      - name:", source)
    secret_pattern = r"(?i)\$\{\{[^}]*\bsecrets\b"
    if re.search(secret_pattern, blocks[0]):
        errors.append("Netlify staging: secret hors étape")
    required = {
        "          NETLIFY_AUTH_TOKEN: " + "$" + "{{ secrets.NETLIFY_AUTH_TOKEN }}",
        "          NETLIFY_SITE_ID: " + "$" + "{{ secrets.NETLIFY_SITE_ID }}",
    }
    for block in blocks[1:]:
        ids = re.findall(r"(?m)^        id: ([a-z_]+)\s*$", block)
        refs = [line for line in block.splitlines() if re.search(secret_pattern, line)]
        if len(ids) == 1 and ids[0] in expected:
            step = ids[0]
            if step in seen:
                errors.append(f"Netlify staging: étape dupliquée {step}")
            seen.add(step)
            env = re.search(r"(?m)^        env:\n((?:          [^\n]+\n)+)", block)
            if (len(refs) != 2 or set(refs) != required or env is None
                    or not required.issubset(set(env.group(1).splitlines()))):
                errors.append(f"Netlify staging: secrets non limités à env de {step}")
        elif refs:
            errors.append("Netlify staging: secret dans une étape non autorisée")
    if seen != expected:
        errors.append("Netlify staging: étapes de déploiement attendues absentes")
    return errors


def inspect_workflow(name: str, source: str) -> list[str]:
    errors: list[str] = []
    if name == "deploy-netlify-staging.yml":
        errors.extend(inspect_netlify_staging_secrets(source))
    if not root_permissions_are_explicit(source):
        errors.append(f"{name}: permissions racine explicites et uniques obligatoires")
    if has_privileged_pr_trigger(source):
        errors.append(f"{name}: déclencheur privilégié pull_request_target interdit")
    if re.search(r"^\s*permissions\s*:\s*write-all\b", source, flags=re.MULTILINE):
        errors.append(f"{name}: permissions write-all interdites")
    for lineno, raw in enumerate(source.splitlines(), 1):
        match = ACTION_LINE.match(raw)
        if not match:
            continue
        action = match.group(1)
        if action.startswith("./"):
            continue
        if action.startswith("docker://"):
            safe = bool(IMMUTABLE_DOCKER.fullmatch(action))
        else:
            safe = bool(IMMUTABLE_ACTION.fullmatch(action))
        if not safe:
            errors.append(f"{name}:{lineno}: action non épinglée à un commit : {action}")
    return errors


def self_test() -> None:
    good = (
        "name: Test\n"
        "on:\n  pull_request:\n"
        "permissions:\n  contents: read\n"
        "jobs:\n  verify:\n    steps:\n"
        "      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803\n"
        "      - uses: ./.github/actions/local-safe\n"
    )
    assert inspect_workflow("safe.yml", good) == []
    # A genuinely root-scoped quoted YAML key must remain acceptable.
    quoted = good.replace("permissions:", "'permissions':", 1)
    assert inspect_workflow("quoted-root.yml", quoted) == []
    mutants = {
        "étiquette mobile": good.replace("@d23441a48e516b6c34aea4fa41551a30e30af803", "@v6"),
        "branche mobile": good.replace("@d23441a48e516b6c34aea4fa41551a30e30af803", "@main"),
        "permission implicite": good.replace("permissions:\n  contents: read\n", ""),
        "permission au niveau job uniquement": good.replace(
            "permissions:\n  contents: read\n",
            "",
        ).replace(
            "  verify:\n    steps:",
            "  verify:\n    permissions:\n      contents: read\n    steps:",
        ),
        "permission fictive en script": good.replace(
            "permissions:\n  contents: read\n",
            "",
        ).replace(
            "      - uses: ./.github/actions/local-safe\n",
            "      - run: |\n          permissions:\n            contents: read\n"
            "      - uses: ./.github/actions/local-safe\n",
        ),
        "permission racine dupliquée": good.replace(
            "permissions:\n  contents: read\n",
            "permissions:\n  contents: read\npermissions:\n  actions: write\n",
        ),
        "droits larges": good.replace("permissions:\n  contents: read", "permissions: write-all"),
        "déclencheur privilégié": good.replace("  pull_request:", "  pull_request_target:"),
    }
    for label, altered in mutants.items():
        if not inspect_workflow(label, altered):
            raise SystemExit(f"Auto-test défectueux : {label}")
    for bad_event in (
        "on: pull_request_target\n",
        "on: [push, pull_request_target]\n",
        "on: {push: {}, pull_request_target: {}}\n",
        "on:\n  'pull_request_target':\n",
        "on:\n  - pull_request_target\n",
    ):
        mutant = good.replace("on:\n  pull_request:\n", bad_event)
        if not inspect_workflow("événement alternatif", mutant):
            raise SystemExit("Auto-test défectueux : variante pull_request_target")
    safe_comment = good.replace("  pull_request:", "  # pull_request_target interdit\n  pull_request:")
    if inspect_workflow("commentaire inoffensif", safe_comment):
        raise SystemExit("Auto-test défectueux : faux positif commentaire")
    staging_env = (
        "        env:\n"
        "          NETLIFY_AUTH_TOKEN: " + "$" + "{{ secrets.NETLIFY_AUTH_TOKEN }}\n"
        "          NETLIFY_SITE_ID: " + "$" + "{{ secrets.NETLIFY_SITE_ID }}\n"
    )
    staging = (
        "jobs:\n  staging:\n    steps:\n"
        "      - name: Preview\n        id: preview_deploy\n" + staging_env
        + "        run: echo preview\n"
        + "      - name: Production candidate\n        id: production_deploy\n" + staging_env
        + "        run: echo candidate\n"
    )
    assert inspect_netlify_staging_secrets(staging) == []
    for mutant in (
        staging.replace("    steps:\n", "    env:\n      TOKEN: " + "$" + "{{ secrets.NETLIFY_AUTH_TOKEN }}\n    steps:\n"),
        staging.replace(staging_env, "", 1),
        staging + "      - name: Build\n" + staging_env + "        run: echo build\n",
        staging.replace("        id: production_deploy", "        id: preview_deploy"),
        staging.replace("        env:\n", "        other:\n", 1),
    ):
        if not inspect_netlify_staging_secrets(mutant):
            raise SystemExit("Auto-test défectueux : isolation secrets Netlify")
    print("OK: les mutations de sécurité CI sont refusées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not WORKFLOWS.is_dir():
        print("ÉCHEC: répertoire workflows manquant")
        return 1
    paths = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    if len(paths) < 100:
        print("ÉCHEC: inventaire workflows anormalement incomplet")
        return 1
    findings = []
    for path in paths:
        try:
            source = path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeError, OSError):
            findings.append(f"{path.name}: fichier YAML illisible")
            continue
        findings.extend(inspect_workflow(path.name, source))
    if findings:
        print(f"ÉCHEC: {len(findings)} anomalie(s) dans {len(paths)} workflows :")
        for item in findings:
            print("- " + item)
        return 1
    print(f"OK: {len(paths)} workflows analysés; actions épinglées, déclencheurs et permissions contrôlés.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
