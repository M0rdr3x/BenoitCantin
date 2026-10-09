#!/usr/bin/env python3
"""Auditer la réconciliation de #449 sans modifier ni exécuter la branche candidate.

Résultats : chemins concurrents réellement distincts, chemins déjà identiques
et conflits du moteur Git. Ce rapport est un diagnostic, PAS une autorisation
de fusion ou de déploiement.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MAIN_REF = "refs/remotes/origin/main"
RELEASE_REF = "refs/remotes/origin/a1/web-release-transparency"


def git(*args: str, accept: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode not in accept:
        raise RuntimeError(
            f"git {' '.join(args)}: retour {result.returncode}: {result.stderr[:1200]}"
        )
    return result


def tree_blobs(ref: str) -> dict[str, str]:
    # Mode et blob SHA sont lus sans exécuter le code du ref distant.
    result = git("ls-tree", "-r", "--full-tree", "-z", ref)
    items: dict[str, str] = {}
    for item in result.stdout.split("\0"):
        if not item:
            continue
        metadata, name = item.split("\t", 1)
        mode, kind, oid = metadata.split(" ")
        if kind == "blob":
            items[name] = mode + ":" + oid
    return items


def classify(main_paths: set[str], release_paths: set[str],
             main_blobs: dict[str, str], release_blobs: dict[str, str]
             ) -> tuple[list[str], list[str], list[str], list[str]]:
    common = main_paths & release_paths
    identical = sorted(x for x in common if main_blobs.get(x) == release_blobs.get(x))
    divergent = sorted(common - set(identical))
    return (
        identical,
        divergent,
        sorted(main_paths - release_paths),
        sorted(release_paths - main_paths),
    )


def self_test() -> None:
    identical, divergent, main_only, release_only = classify(
        {"shared", "different", "main-only"},
        {"shared", "different", "release-only"},
        {"shared": "100644:aaa", "different": "100644:bbb"},
        {"shared": "100644:aaa", "different": "100644:ccc"},
    )
    assert identical == ["shared"]
    assert divergent == ["different"]
    assert main_only == ["main-only"]
    assert release_only == ["release-only"]
    # Suppression d'un côté, modification de l'autre : divergence, jamais égalité.
    identical, divergent, _, _ = classify(
        {"delete"}, {"delete"}, {}, {"delete": "100644:abc"}
    )
    assert not identical and divergent == ["delete"]
    print("OK: auto-tests des quatre états de réconciliation Git.")


def emit(report: str) -> None:
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(report + "\n")


def scan() -> int:
    main_sha = git("rev-parse", MAIN_REF).stdout.strip()
    release_sha = git("rev-parse", RELEASE_REF).stdout.strip()
    base = git("merge-base", main_sha, release_sha).stdout.strip()

    def changed(sha: str) -> set[str]:
        raw = git("diff", "--name-only", "--no-renames", base, sha).stdout
        return set(filter(None, raw.splitlines()))

    main_paths = changed(main_sha)
    release_paths = changed(release_sha)
    identical, divergent, main_only, release_only = classify(
        main_paths, release_paths, tree_blobs(main_sha), tree_blobs(release_sha)
    )

    # --name-only : sortie diagnostique Git (sans conflit résolu ni tree écrit
    # dans les branches). Git retourne 1 lorsque des conflits subsistent.
    merge = git("merge-tree", "--write-tree", "--name-only",
                main_sha, release_sha, accept=(0, 1))
    if merge.returncode == 1:
        merge_state = "CONFLITS_GIT_PRESENTS"
    else:
        merge_state = "FUSION_GIT_TECHNIQUEMENT_POSSIBLE"
    # Limite affichage; le corps d'un fichier privé n'est jamais interrogé.
    merge_summary = merge.stdout.splitlines()
    excerpt = "\n".join(merge_summary[:85])
    if len(merge_summary) > 85:
        excerpt += "\n[sortie Git tronquée]"

    report = [
        "## SINJIRA — audit de divergence du candidat web-only #449",
        "",
        f"- Base commune : \`{base}\`",
        f"- main : \`{main_sha}\`",
        f"- Candidat #449 : \`{release_sha}\`",
        f"- Chemins touchés des deux côtés : **{len(identical) + len(divergent)}**",
        f"- Déjà identiques : **{len(identical)}**",
        f"- Différents et nécessitant une décision : **{len(divergent)}**",
        f"- Modifiés uniquement sur main : **{len(main_only)}**",
        f"- Modifiés uniquement sur la candidate : **{len(release_only)}**",
        f"- Résultat merge-tree : **{merge_state}**",
        "",
        "### Chemins concurrents divergents — ne pas remplacer main automatiquement",
        "",
    ]
    report.extend(f"- \`{path}\`" for path in divergent)
    report.extend(["", "### Déjà identiques sur les deux branches", ""])
    report.extend(f"- \`{path}\`" for path in identical)
    report.extend([
        "",
        "### Diagnostic natif Git (merge-tree --write-tree --name-only)",
        "",
        "\`\`\`text",
        excerpt,
        "\`\`\`",
        "",
        "**Sécurité :** audit en lecture seule. Aucune écriture sur la branche,",
        "aucun déploiement ni remplacement de contenu. Les fichiers en divergence",
        "nécessitent un arbitrage et les smokes de #450 restent indispensables.",
    ])
    emit("\n".join(report))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    flag = parser.add_mutually_exclusive_group(required=True)
    flag.add_argument("--self-test", action="store_true")
    flag.add_argument("--scan", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    return scan()


if __name__ == "__main__":
    raise SystemExit(main())
