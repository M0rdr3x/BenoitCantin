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
UPLOAD = "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
ARCHIVE_PATH = "${{ runner.temp }}/artifact.tar"
DEPLOY = "actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346"
USES = re.compile(r"""^\s*(?:-\s*)?(?:uses|"uses"|'uses')\s*:\s*(?:"([^"\n]+)"|'([^'\n]+)'|([^\s#]+))\s*(?:#.*)?$""", re.I)
MULTILINE_USES = re.compile(r"""(?m)^\s*(?:-\s*)?(?:uses|"uses"|'uses')\s*:\s*[>|]""", re.I)
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
    'python3 scripts/pages_archive_integrity.py create _site "$RUNNER_TEMP/artifact.tar"',
    "needs: [build, verify]",
    "gh api \"repos/$GITHUB_REPOSITORY/actions/artifacts/$ARTIFACT_ID/zip\"",
    "actions/runs/$GITHUB_RUN_ID/artifacts?name=github-pages&per_page=100",
    ".total_count==1 and (.artifacts|length)==1 and (.artifacts[0].id|tostring)==$id",
    "ARTIFACT_ZIP_SHA256: ${{ needs.build.outputs.artifact_zip_sha256 }}",
    "artifact_zip_sha256: ${{ steps.upload.outputs.artifact-digest }}",
    ".workflow_run.head_branch==\"main\" and .digest==$digest",
    "overwrite: false",
    "archive: true",
    "python3 scripts/verify_pages_artifact_zip.py \"$dest/artifact.zip\" \"$ARTIFACT_ZIP_SHA256\" \"$ARCHIVE_SHA256\"",
    "name: github-pages",
    "ARTIFACT_ID: ${{ needs.build.outputs.artifact_id }}",
    "ARCHIVE_SHA256: ${{ needs.build.outputs.archive_sha256 }}",
    '(.workflow_run.id|tostring)==$run and .workflow_run.head_sha==$sha',
    "sha256sum --check --status",
)


def page_uses(source: str, approved: bool = True) -> list[tuple[int, str]]:
    actions: list[tuple[int, str]] = []
    for index, line in enumerate(source.splitlines()):
        match = USES.match(line)
        if not match:
            continue
        action = next((value for value in match.groups() if value is not None), "")
        if PAGES_ACTION.search(action.split("@", 1)[0]) or (approved and action.split("@", 1)[0].lower() == "actions/upload-artifact"):
            actions.append((index, action))
    return actions


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
        # A folded YAML scalar can hide the action identifier on a following
        # line. Refuse it rather than silently accepting unrecognized uses.
        if MULTILINE_USES.search(source):
            errors.append(f"{name}: valeur uses: multiligne interdite")
        if name != APPROVED and re.search(r"(?m)^\s*name\s*:\s*['\"]?github-pages['\"]?\s*(?:#.*)?$", source):
            errors.append(f"{name}: nom réservé github-pages hors workflow approuvé")
        for line, action in page_uses(source, name == APPROVED):
            actions.append((name, action))
            if name != APPROVED:
                errors.append(f"{name}:{line + 1}: action Pages hors workflow isolé")
                continue
            if action not in (UPLOAD, DEPLOY):
                errors.append(f"{name}:{line + 1}: action Pages non officielle ou SHA inattendu")
                continue
            if action == UPLOAD and path_of_action(source, line) != ARCHIVE_PATH:
                errors.append(f"{name}:{line + 1}: seule l’archive TAR contrôlée peut être publiée")
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
        "      - run: python3 scripts/pages_archive_integrity.py create _site \"$RUNNER_TEMP/artifact.tar\"\n"
        "          gh api \"repos/$GITHUB_REPOSITORY/actions/artifacts/$ARTIFACT_ID/zip\"\n"
        "          actions/runs/$GITHUB_RUN_ID/artifacts?name=github-pages&per_page=100\n"
        "          .total_count==1 and (.artifacts|length)==1 and (.artifacts[0].id|tostring)==$id\n"
        "          ARTIFACT_ZIP_SHA256: ${{ needs.build.outputs.artifact_zip_sha256 }}\n"
        "          artifact_zip_sha256: ${{ steps.upload.outputs.artifact-digest }}\n"
        "          .workflow_run.head_branch==\"main\" and .digest==$digest\n"
        "          python3 scripts/verify_pages_artifact_zip.py \"$dest/artifact.zip\" \"$ARTIFACT_ZIP_SHA256\" \"$ARCHIVE_SHA256\"\n"
        "          ARTIFACT_ID: ${{ needs.build.outputs.artifact_id }}\n"
        "          ARCHIVE_SHA256: ${{ needs.build.outputs.archive_sha256 }}\n"
        "          (.workflow_run.id|tostring)==$run and .workflow_run.head_sha==$sha\n"
        "      - run: sha256sum --check --status\n"
        "    needs: [build, verify]\n"
        "      - name: Publier _site\n"
        "        uses: " + UPLOAD + "\n"
        "        with:\n          name: github-pages\n          path: ${{ runner.temp }}/artifact.tar\n"
        "          overwrite: false\n          archive: true\n"
        "      - uses: " + DEPLOY + "\n"
    )
    assert inspect_workflows({APPROVED: good}) == []
    # GitHub Actions accepts quoted scalars and optional whitespace before ':'.
    # All these variants must remain visible to the inventory.
    quoted = good.replace("uses: " + UPLOAD, "uses: '" + UPLOAD + "'")
    quoted = quoted.replace("uses: " + DEPLOY, 'uses: "' + DEPLOY + '"')
    assert inspect_workflows({APPROVED: quoted}) == []
    quoted_spaced = good.replace("uses: " + UPLOAD, "uses : " + UPLOAD)
    assert inspect_workflows({APPROVED: quoted_spaced}) == []
    quoted_key = good.replace("uses: " + UPLOAD, "'uses': " + UPLOAD)
    quoted_key = quoted_key.replace("uses: " + DEPLOY, '"uses": ' + DEPLOY)
    assert inspect_workflows({APPROVED: quoted_key}) == []
    for label, rogue in (
        ("quoted rogue upload", '      - uses: "' + UPLOAD + '"\n'),
        ("quoted rogue deploy", "      - uses: '" + DEPLOY + "'\n"),
        ("spaced rogue upload", "      - uses : " + UPLOAD + "\n"),
        ("quoted key rogue upload", "      - 'uses': " + UPLOAD + "\n"),
        ("quoted key rogue deploy", '      - "uses": ' + DEPLOY + "\n"),
        ("folded rogue upload", "      - uses: >-\n        " + UPLOAD + "\n"),
        ("literal rogue deploy", "      - 'uses': |\n        " + DEPLOY + "\n"),
    ):
        assert inspect_workflows({APPROVED: good, label + ".yml": rogue.replace(UPLOAD, "actions/upload-pages-artifact@56afc609e74202658d3ffba0e8f6dda462b719fa")}), label
    assert path_of_action(good, next(i for i, _ in page_uses(good))) == ARCHIVE_PATH
    mutants = (
        ("publish root", good.replace("path: ${{ runner.temp }}/artifact.tar", "path: .")),
        ("publish ancestor", good.replace("path: ${{ runner.temp }}/artifact.tar", "path: ${{ runner.temp }}/artifact.tar/..")),
        ("publish missing", good.replace("          path: ${{ runner.temp }}/artifact.tar\n", "")),
        ("path fictif sous env", good.replace("        with:\n          name: github-pages\n          path: ${{ runner.temp }}/artifact.tar", "        env:\n          path: ${{ runner.temp }}/artifact.tar")),
        ("override après with", good.replace("        with:\n          name: github-pages\n          path: ${{ runner.temp }}/artifact.tar", "        with:\n          name: github-pages\n          path: ${{ runner.temp }}/artifact.tar\n        with:\n          path: .")),
        ("publish duplicate", good.replace("path: ${{ runner.temp }}/artifact.tar", "path: ${{ runner.temp }}/artifact.tar\n          path: .")),
        ("publish expression", good.replace("path: ${{ runner.temp }}/artifact.tar", "path: $WORKSPACE")),
        # Un path sous une clé intermédiaire ne serait pas transmis à
        # actions/upload-pages-artifact et peut laisser le défaut ".".
        ("nested fake path", good.replace(
            "        with:\n          name: github-pages\n          path: ${{ runner.temp }}/artifact.tar\n",
            "        with:\n          nested:\n            path: ${{ runner.temp }}/artifact.tar\n",
        )),
        # L'indentation directe doit être celle de la clé path: de l'action.
        ("overindented path", good.replace(
            "        with:\n          name: github-pages\n          path: ${{ runner.temp }}/artifact.tar\n",
            "        with:\n            path: ${{ runner.temp }}/artifact.tar\n",
        )),
        ("wrong SHA", good.replace(UPLOAD, UPLOAD.split("@")[0] + "@v3")),
        ("missing review", good.replace("confirm_containment:", "not_confirmed:")),
        ("missing main", good.replace("github.ref == 'refs/heads/main'", "true")),
        ("auto deploy", good.replace("  workflow_dispatch:", "  push:")),
        ("wrong archive name", good.replace("name: github-pages", "name: other")),
        ("missing artifact identity", good.replace("(.workflow_run.id|tostring)==$run and .workflow_run.head_sha==$sha", "true")),
        ("missing archive verification", good.replace("sha256sum --check --status", "true")),
        ("missing ZIP identity gate 0", good.replace("gh api \"repos/$GITHUB_REPOSITORY/actions/artifacts/$ARTIFACT_ID/zip\"", "removed")),
        ("missing ZIP identity gate 1", good.replace("actions/runs/$GITHUB_RUN_ID/artifacts?name=github-pages&per_page=100", "removed")),
        ("missing ZIP identity gate 2", good.replace(".total_count==1 and (.artifacts|length)==1 and (.artifacts[0].id|tostring)==$id", "removed")),
        ("missing ZIP identity gate 3", good.replace("ARTIFACT_ZIP_SHA256: ${{ needs.build.outputs.artifact_zip_sha256 }}", "removed")),
        ("missing ZIP identity gate 4", good.replace("artifact_zip_sha256: ${{ steps.upload.outputs.artifact-digest }}", "removed")),
        ("missing ZIP identity gate 5", good.replace(".workflow_run.head_branch==\"main\" and .digest==$digest", "removed")),
        ("missing ZIP identity gate 6", good.replace("overwrite: false", "removed")),
        ("missing ZIP identity gate 7", good.replace("archive: true", "removed")),
        ("missing ZIP identity gate 8", good.replace("python3 scripts/verify_pages_artifact_zip.py \"$dest/artifact.zip\" \"$ARTIFACT_ZIP_SHA256\" \"$ARCHIVE_SHA256\"", "removed")),
        ("missing verification dependency", good.replace("needs: [build, verify]", "needs: build")),
        ("missing deploy", good.replace("      - uses: " + DEPLOY + "\n", "")),
        ("no SHA compare", good.replace('"$EXPECTED_SHA" != "$GITHUB_SHA"', "true")),
    )
    for label, altered in mutants:
        assert inspect_workflows({APPROVED: altered}), "Dangerous Pages fixture accepted: " + label
    assert inspect_workflows({APPROVED: good, "extra.yml": good})
    print("OK : scénarios Pages hostiles refusés; archive contrôlée obligatoire.")


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
    print(f"OK : {len(entries)} workflows analysés ; une seule archive Pages autorisée, publication manuelle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
