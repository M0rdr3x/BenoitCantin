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


def active_lines(source: str) -> str:
    """Ignore les commentaires YAML avant toute vérification de verrou."""
    return "\n".join(line.split(" #", 1)[0] for line in source.splitlines()
                     if line.strip() and not line.lstrip().startswith("#"))


def manual_events(source: str) -> list[str] | None:
    """N'accepter que le déclencheur manuel explicite au niveau racine."""
    lines = source.splitlines()
    starts = [i for i, line in enumerate(lines)
              if re.fullmatch(r"on:\s*(?:#.*)?", line)]
    if len(starts) != 1:
        return None
    events: list[str] = []
    for line in lines[starts[0] + 1:]:
        if line.strip() and not line[0].isspace() and not line.lstrip().startswith("#"):
            break
        match = re.fullmatch(r"  ([a-z][a-z0-9_]*):\s*(?:#.*)?", line)
        if match:
            events.append(match.group(1))
    return events


def manual_job_gate(source: str, name: str) -> bool:
    """Chaque job de publication doit être verrouillé, pas seulement un autre job."""
    marker = f"  {name}:"
    index = source.find("\n" + marker + "\n")
    if index == -1:
        return False
    rest = source[index + len(marker) + 2:]
    next_job = re.search(r"(?m)^  [a-zA-Z][a-zA-Z0-9_-]*:\s*$", rest)
    if next_job:
        rest = rest[:next_job.start()]
    match = re.search(r"(?m)^    if:\s*(.+)$", rest)
    if not match:
        return False
    expression = match.group(1).split(" #", 1)[0]
    return all(token in expression for token in (
        "github.ref == 'refs/heads/main'",
        "inputs.confirm_containment == 'CONTAIN'",
        "inputs.acknowledge_header_gap == 'ACK_HEADER_GAP'",
    ))


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
    active = active_lines(body)
    for marker in GATES:
        if marker not in active:
            errors.append(f"Workflow Pages isolé sans verrou : {marker}")
    if manual_events(body) != ["workflow_dispatch"]:
        errors.append("Pages doit avoir workflow_dispatch comme seul événement")
    # Un nom mentionné dans un if/commentaire ne prouve pas que l'input
    # obligatoire de workflow_dispatch est réellement déclaré.
    for key in ("confirm_containment", "acknowledge_header_gap", "expected_sha"):
        if len(re.findall(rf"(?m)^      {key}:\s*(?:#.*)?$", body)) != 1:
            errors.append(f"Input Pages absent, non direct ou ambigu : {key}")
    for job in ("build", "deploy"):
        if not manual_job_gate(body, job):
            errors.append(f"Job Pages {job} sans triple contrôle main + confirmation + avertissement")
    if re.search(r"(?im)^\s*permissions:\s*write-all\b", active):
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
        "    if: github.ref == 'refs/heads/main' && inputs.confirm_containment == 'CONTAIN' && inputs.acknowledge_header_gap == 'ACK_HEADER_GAP'\n"
        "    steps:\n"
        "      - run: python3 scripts/build_netlify_public.py --check --security-containment\n"
        "      - run: python3 scripts/build_netlify_public.py --output _site --security-containment\n"
        "      - run: 'test \"$EXPECTED_SHA\" != \"$GITHUB_SHA\"'\n"
        "      - name: Publier _site\n"
        "        uses: " + UPLOAD + "\n"
        "        with:\n          path: _site\n"
        "  deploy:\n"
        "    if: github.ref == 'refs/heads/main' && inputs.confirm_containment == 'CONTAIN' && inputs.acknowledge_header_gap == 'ACK_HEADER_GAP'\n"
        "    steps:\n"
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
        ("unknown automatic event", good.replace("  workflow_dispatch:\n", "  workflow_dispatch:\n  workflow_run:\n")),
        ("manual event merely commented", good.replace("  workflow_dispatch:\n", "  push:\n  # workflow_dispatch:\n")),
        ("missing build confirmation", good.replace(
            "if: github.ref == 'refs/heads/main' && inputs.confirm_containment == 'CONTAIN' &&",
            "if: github.ref == 'refs/heads/main' && true &&", 1,
        )),
        ("fake gate in comments", good.replace(
            "github.ref == 'refs/heads/main'",
            "true # github.ref == 'refs/heads/main'",
        )),
        ("path variant", good.replace("path: _site", "path: ./_site")),
        ("input in comment", good.replace(
            "      expected_sha:\n",
            "      # expected_sha:\n",
        )),
    )
    for label, altered in mutants:
        assert inspect_workflows({APPROVED: altered}), "Dangerous Pages fixture accepted: " + label
    assert inspect_workflows({APPROVED: good, "extra.yml": good})
    print("OK : 21 mutations Pages refusées; upload _site direct et double garde obligatoire.")


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
