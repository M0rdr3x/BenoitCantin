#!/usr/bin/env python3
"""Reçu d'identité vérifiable du déploiement Pages, sans secret.

Émis uniquement dans _site après compilation, avant upload. Le contrôle
HTTP compare les octets exacts du reçu à la révision et au run approuvés.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

MARKER = ".well-known/sinjira-pages-release.json"
SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
RUN_PATTERN = re.compile(r"[1-9][0-9]{0,19}\Z")


def render(sha: str, run_id: str) -> bytes:
    if not SHA_PATTERN.fullmatch(sha):
        raise ValueError("SHA GitHub malformé")
    if not RUN_PATTERN.fullmatch(run_id):
        raise ValueError("Numéro de run GitHub malformé")
    return (json.dumps({
        "deployment": "github-pages",
        "repository": "M0rdr3x/BenoitCantin",
        "revision": sha,
        "run_id": run_id,
        "version": 1,
    }, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n").encode("ascii")


def marker_path(built: Path) -> Path:
    return built / MARKER


def write(built: Path, sha: str, run_id: str) -> None:
    data = render(sha, run_id)
    if not built.is_dir() or built.is_symlink():
        raise ValueError("Dossier _site invalide")
    target = marker_path(built)
    if target.exists() or target.is_symlink():
        raise ValueError("Reçu existant inattendu : aucun écrasement autorisé")
    parent = target.parent
    if parent.is_symlink():
        raise ValueError("Répertoire de reçu symbolique interdit")
    parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def verify(built: Path, sha: str, run_id: str) -> list[str]:
    expected = render(sha, run_id)
    path = marker_path(built)
    if path.is_symlink() or not path.is_file():
        return ["Reçu de publication absent ou symbolique"]
    try:
        actual = path.read_bytes()
    except OSError:
        return ["Reçu de publication illisible"]
    if actual != expected:
        return ["Reçu de publication ne correspond pas au commit/run approuvés"]
    return []


def self_test() -> None:
    sha, run = "a" * 40, "38120000123"
    assert b'"revision":"' + sha.encode('ascii') + b'"' in render(sha, run)
    for bad_sha, bad_run in (("bad", run), (sha, "0"), (sha, "abc"), (sha, "1\n")):
        try:
            render(bad_sha, bad_run)
        except ValueError:
            continue
        raise AssertionError("Identifiant de publication invalide accepté")
    with tempfile.TemporaryDirectory() as folder:
        built = Path(folder)
        assert verify(built, sha, run)
        write(built, sha, run)
        assert not verify(built, sha, run)
        assert verify(built, "b" * 40, run)
        assert verify(built, sha, "38120000124")
        try:
            write(built, sha, run)
        except ValueError:
            pass
        else:
            raise AssertionError("Un second reçu a écrasé le premier")
        marker_path(built).write_text("{}", "utf-8")
        assert verify(built, sha, run)
        marker_path(built).unlink()
        assert verify(built, sha, run)
    print("OK reçu Pages : SHA et run exacts, publication obsolète ou absente refusée")


def main() -> int:
    parser = argparse.ArgumentParser()
    task = parser.add_mutually_exclusive_group(required=True)
    task.add_argument("--self-test", action="store_true")
    task.add_argument("--write", metavar="BUILT")
    task.add_argument("--verify", metavar="BUILT")
    parser.add_argument("--sha")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.sha or not args.run_id:
        parser.error("--sha et --run-id requis")
    try:
        if args.write:
            write(Path(args.write).resolve(), args.sha, args.run_id)
        else:
            errors = verify(Path(args.verify).resolve(), args.sha, args.run_id)
            if errors:
                for error in errors:
                    print("ERREUR : " + error, file=sys.stderr)
                return 1
    except (OSError, ValueError) as exc:
        print("ERREUR : preuve Pages invalide (" + type(exc).__name__ + ")", file=sys.stderr)
        return 1
    print("OK : reçu Pages exact vérifié, SHA " + args.sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
