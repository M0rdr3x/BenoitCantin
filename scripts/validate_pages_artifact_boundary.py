#!/usr/bin/env python3
"""Fail-closed : les workflows ne publient jamais la racine technique sur Pages.

Inspection statique hors réseau, sans permission de déploiement. Elle ne peut
pas lire ou modifier la configuration GitHub Pages au niveau administrateur.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
APPROVED = "deploy-github-pages-isolated.yml"
UPLOAD = "actions/upload-pages-artifact@56afc609e74202658d3ffba0e8f6dda462b719fa"
DEPLOY = "actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346"
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.I)
PAGES_ACTION = re.compile(r"(?:^|/)(?:upload-pages-artifact|deploy-pages)$", re.I)
SHA40 = re.compile(r"^[a-f0-9]{40}$")
GATES = (
    "workflow_dispatch:",
    "confirm_containment",
    "acknowledge_header_gap",
    "expected_sha",
    "github.ref == 'refs/heads/main'",
    '"$EXPECTED_SHA" != "$GITHUB_SHA"',
    "python3 scripts/build_netlify_public.py --check --security-containment",
    "python3 scripts/build_netlify_public.py --output _site --security-containment",
)


def page_uses(source: str) -> list[tuple[int, str]]:
    return [
        (i, match.group(1))
        for i, line in enumerate(source.splitlines())
        if (match := USES.match(line))
        and PAGES_ACTION.search(match.group(1).split("@", 1)[0])
    ]


def path_of_action(source: str, index: int) -> str | None:
    lines = source.splitlines()
    raw = lines[index]
    depth = len(raw) - len(raw.lstrip())
    with_seen = False
    paths: list[str] = []
    for line in lines[index + 1 :]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent < depth or (indent <= depth and stripped.startswith("- ")):
            break
        if indent == depth:
            if re.fullmatch(r"with:\s*(?:#.*)?", stripped):
                if with_seen:
                    return None
                with_seen = True
            elif with_seen:
                break
            continue
        if not with_seen:
            # Ne jamais confondre un chemin placé dans env: ou dans une
            # autre clé de l'étape avec le paramètre réel de l'action.
            continue
        if re.match(r"^<<\s*:", stripped):
            return None
        # Le paramètre doit être un enfant DIRECT de with:, jamais un leurre
        # placé sous une clé imbriquée. Sinon GitHub Actions peut ignorer le
        # faux path et conserver le défaut dangereux de l'action (".").
        if indent != depth + 2:
            continue
        match = re.fullmatch(r"path:\s*([^\n#]*?)(?:\s+#.*)?", stripped)
        if match:
            paths.append(match.group(1).strip().strip("'\""))
    return paths[0] if with_seen and len(paths) == 1 else None

def inspect_workflows(files: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if APPROVED not in files:
        return ["Workflow Pages isolé obligatoire absent"]
    actions: list[tuple[str, str]] = []
    for name, source in files.items():
        for line, action in page_uses(source):
            actions.append((name, action))
            if name != APPROVED:
                errors.append(f"{name}:{line + 1}: action Pages hors workflow isolé")
                continue
            if action not in (UPLOAD, DEPLOY):
                errors.append(f"{name}:{line + 1}: action Pages non officielle ou SHA inattendu")
                continue
            if action == UPLOAD and path_of_action(source, line) != "_site":
                errors.append(f"{name}:{line + 1}: seule la sortie _site peut être publiée")
    if sorted(actions) != sorted(((APPROVED, UPLOAD), (APPROVED, DEPLOY))):
        errors.append("Inventaire Pages invalide : un upload et un déploiement officiels requis")

    body = files[APPROVED]
    for marker in GATES:
        if marker not in body:
            errors.append(f"Workflow Pages isolé sans verrou : {marker}")
    if re.search(r"(?m)^  (?:push|pull_request|schedule|repository_dispatch)\s*:", body):
        errors.append("Workflow Pages de publication doit rester strictement manuel")
    if re.search(r"(?im)^\s*permissions:\s*write-all\b", body):
        errors.append("Droits d'écriture généraux interdits")
    return errors


def self_test() -> None:
    # Fixture représentant les étapes pertinentes du vrai workflow.
    good = (
        "name: Pages isolé\n"
        "on:\n  workflow_dispatch:\n    inputs:\n"
        "      confirm_containment:\n      acknowledge_header_gap:\n      expected_sha:\n"
        "permissions:\n  contents: read\n"
        "jobs:\n  build:\n"
        "    if: github.ref == 'refs/heads/main'\n"
        "    steps:\n"
        "      - run: python3 scripts/build_netlify_public.py --check --security-containment\n"
        "      - run: python3 scripts/build_netlify_public.py --output _site --security-containment\n"
        "      - run: 'test \"$EXPECTED_SHA\" != \"$GITHUB_SHA\"'\n"
        "      - name: Publier _site\n"
        "        uses: " + UPLOAD + "\n"
        "        with:\n          path: _site\n"
        "      - uses: " + DEPLOY + "\n"
    )
    assert inspect_workflows({APPROVED: good}) == []
    assert path_of_action(good, next(i for i, _ in page_uses(good))) == "_site"
    mutants = (
        ("publish root", good.replace("path: _site", "path: .")),
        ("publish ancestor", good.replace("path: _site", "path: _site/..")),
        ("publish missing", good.replace("          path: _site\n", "")),
        ("path fictif sous env", good.replace("        with:\n          path: _site", "        env:\n          path: _site")),
        ("override après with", good.replace("        with:\n          path: _site", "        with:\n          path: _site\n        with:\n          path: .")),
        ("publish duplicate", good.replace("path: _site", "path: _site\n          path: .")),
        ("publish expression", good.replace("path: _site", "path: $WORKSPACE")),
        # Un path sous une clé intermédiaire ne serait pas transmis à
        # actions/upload-pages-artifact et peut laisser le défaut ".".
        ("nested fake path", good.replace(
            "        with:\n          path: _site\n",
            "        with:\n          nested:\n            path: _site\n",
        )),
        # L'indentation directe doit être celle de la clé path: de l'action.
        ("overindented path", good.replace(
            "        with:\n          path: _site\n",
            "        with:\n            path: _site\n",
        )),
        ("wrong SHA", good.replace(UPLOAD, UPLOAD.split("@")[0] + "@v3")),
        ("missing review", good.replace("confirm_containment:", "not_confirmed:")),
        ("missing main", good.replace("github.ref == 'refs/heads/main'", "true")),
        ("auto deploy", good.replace("  workflow_dispatch:", "  push:")),
        ("missing deploy", good.replace("      - uses: " + DEPLOY + "\n", "")),
        ("no SHA compare", good.replace('"$EXPECTED_SHA" != "$GITHUB_SHA"', "true")),
    )
    for label, altered in mutants:
        assert inspect_workflows({APPROVED: altered}), "Dangerous Pages fixture accepted: " + label
    assert inspect_workflows({APPROVED: good, "extra.yml": good})
    print("OK : 15 mutations Pages refusées; upload _site direct obligatoire.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not WORKFLOWS.is_dir() or WORKFLOWS.is_symlink():
        print("ECHEC : répertoire workflows absent ou symbolique")
        return 1
    paths = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    if len(paths) < 100:
        print("ECHEC : inventaire incomplet des workflows")
        return 1
    entries: dict[str, str] = {}
    for path in paths:
        if path.is_symlink() or path.stat().st_size > 200_000:
            print("ECHEC : workflow symbolique ou trop volumineux")
            return 1
        try:
            entries[path.name] = path.read_text("utf-8", errors="strict")
        except (OSError, UnicodeError):
            print("ECHEC : workflow illisible")
            return 1
    problems = inspect_workflows(entries)
    if problems:
        for problem in problems:
            print("ECHEC : " + problem)
        return 1
    print(f"OK : {len(entries)} workflows analysés ; un seul upload _site autorisé, publication manuelle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
