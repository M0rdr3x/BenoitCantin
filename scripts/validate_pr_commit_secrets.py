#!/usr/bin/env python3
"""Fail-closed scan of every changed source snapshot in a pull request history.

A secret added and removed in separate commits is still visible in Git. The
regular working-tree secrets guard does not see such intermediate snapshots.
This scanner uses local git objects only; no network, secrets or credentials.
Never print a blob, a token, Git stderr, or any matched credential.
"""
from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import re
import subprocess

if __package__:
    from scripts import validate_no_committed_secrets as secrets
else:
    import validate_no_committed_secrets as secrets

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_COMMITS = 200
MAX_CHANGED_BLOBS = 5000


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        # A Git error may include an untrusted filename; never echo stderr.
        raise ValueError("Impossible de lire l'historique Git demandé")
    return result.stdout


def verified_commit(repo: Path, sha: str) -> None:
    if not SHA.fullmatch(sha):
        raise ValueError("SHA de commit invalide")
    git(repo, "cat-file", "-e", sha + "^{commit}")


def changed_paths(repo: Path, sha: str) -> list[str]:
    # -m checks merge commits against each parent; --no-renames gives A/D pairs.
    raw = git(repo, "diff-tree", "--root", "-m", "-r", "--no-commit-id",
              "--no-renames", "--name-status", "-z", sha)
    if not raw:
        return []
    parts = raw.split(b"\0")
    if parts[-1] != b"" or len(parts) % 2 != 1:
        raise ValueError("Liste des chemins Git ambiguë")
    selected: set[str] = set()
    for i in range(0, len(parts) - 1, 2):
        status = parts[i].decode("ascii", "strict")
        if status == "D":
            continue
        if status not in {"A", "M", "T"}:
            raise ValueError("Statut de fichier Git inattendu")
        try:
            path = parts[i + 1].decode("utf-8", "strict")
        except UnicodeDecodeError:
            raise ValueError("Nom de fichier Git non UTF-8") from None
        if not path or path.startswith("/") or "\n" in path or "\r" in path:
            raise ValueError("Chemin de fichier Git ambigu")
        selected.add(path)
    return sorted(selected)


def snapshot_findings(repo: Path, commit: str, path: str) -> list[str]:
    name = PurePosixPath(path)
    mandatory = (name.suffix.lower() in secrets.MANDATORY_TEXT_EXTENSIONS
                 or name.name in secrets.MANDATORY_TEXT_NAMES)
    place = f"{commit[:12]}:{path}"
    if secrets.is_forbidden_env_file(Path(path)):
        return [place + ": fichier .env réel présent dans un commit"]

    item = git(repo, "ls-tree", "-z", commit, "--", path)
    if not item or not item.endswith(b"\0") or item.count(b"\0") != 1:
        raise ValueError("Objet Git absent ou ambigu")
    fields = item[:-1].split(b"\t", 1)
    if len(fields) != 2 or fields[1].decode("utf-8", "strict") != path:
        raise ValueError("Entrée Git inattendue")
    mode = fields[0].split(b" ", 1)[0]
    if mode == b"120000":
        return [place + ": lien symbolique introduit dans l'historique"]
    if mode not in {b"100644", b"100755"}:
        return [place + ": type d'objet Git non autorisé"]

    blob = commit + ":" + path
    size = int(git(repo, "cat-file", "-s", blob).strip())
    if size > secrets.MAX_TEXT_BYTES:
        return ([place + ": source trop volumineuse pour contrôle"]
                if mandatory else [])
    data = git(repo, "cat-file", "blob", blob)
    if len(data) != size:
        raise ValueError("Taille d'objet Git incohérente")
    if b"\0" in data:
        return [place + ": source binaire non inspectable"] if mandatory else []
    try:
        source = data.decode("utf-8", "strict")
    except UnicodeDecodeError:
        return [place + ": source UTF-8 non inspectable"] if mandatory else []

    found: list[str] = []
    for label, pattern in secrets.SECRET_PATTERNS:
        for hit in pattern.finditer(source):
            line = source.count("\n", 0, hit.start()) + 1
            found.append(f"{place}:{line}: {label}")
    for pos in secrets.leaked_privileged_jwt_positions(source):
        line = source.count("\n", 0, pos) + 1
        found.append(f"{place}:{line}: Supabase privileged JWT credential")
    return found


def inspect_range(repo: Path, base: str, head: str,
                  max_commits: int = MAX_COMMITS) -> tuple[int, int, list[str]]:
    verified_commit(repo, base)
    verified_commit(repo, head)
    ancestor = git(repo, "merge-base", base, head).decode("ascii").strip()
    commits = git(repo, "rev-list", "--reverse", ancestor + ".." + head)
    hashes = [line for line in commits.decode("ascii").splitlines() if line]
    if not hashes:
        raise ValueError("Aucun commit de PR à analyser")
    if len(hashes) > max_commits:
        raise ValueError("Historique de PR trop long pour analyse complète")

    scanned = 0
    issues: list[str] = []
    for commit in hashes:
        for path in changed_paths(repo, commit):
            scanned += 1
            if scanned > MAX_CHANGED_BLOBS:
                raise ValueError("Trop de versions de fichiers à analyser")
            issues.extend(snapshot_findings(repo, commit, path))
    return len(hashes), scanned, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    try:
        commits, files, issues = inspect_range(ROOT, args.base, args.head)
    except (ValueError, OSError, UnicodeError) as error:
        print("FAIL: historique non entièrement inspecté:", str(error))
        return 1
    if issues:
        # A filename itself may contain a credential or terminal-control text.
        # Never emit tainted findings to the public CI log, even if the
        # underlying matcher only records paths and categories.
        print(f"FAIL: {len(issues)} risque(s) dans {commits} commits de PR. "
              "Détails masqués pour protéger les identifiants.")
        return 1
    print(f"PASS: {commits} commits, {files} versions de fichiers; "
          "aucun secret reconnu dans l'historique de cette PR.")
    print("NOTE: l'historique plus ancien, les secrets inconnus et les forks "
          "nécessitent toujours un audit et une rotation distincts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
