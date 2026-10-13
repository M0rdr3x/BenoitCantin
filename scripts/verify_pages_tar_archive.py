#!/usr/bin/env python3
"""Prouver hors ligne que l'archive Pages conserve chaque fichier et le reçu caché.

Reproduit sous Linux les options TAR de l'action GitHub officielle épinglée
98ef48e41587a300b82de4cf298aa98b57b2faae, avec include-hidden-files=true.
Ce test N'ENVOIE aucun artefact sur GitHub Pages.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from pages_release_proof import MARKER, render


def build_tar(built: Path, archive: Path, *, include_hidden: bool = True) -> None:
    command = [
        "tar", "--dereference", "--hard-dereference",
        "--directory", str(built),
        "-cf", str(archive), "--exclude=.git", "--exclude=.github",
    ]
    if not include_hidden:
        command.append("--exclude=.[^/]*")
    command.append(".")
    subprocess.run(command, check=True, capture_output=True, timeout=120)


def audit(built: Path, archive: Path, sha: str, run_id: str) -> list[str]:
    try:
        receipt = render(sha, run_id)
    except ValueError:
        return ["Identifiants de publication TAR invalides"]
    if not built.is_dir() or built.is_symlink():
        return ["Répertoire Jekyll introuvable ou symbolique"]
    errors: list[str] = []
    approved: dict[str, bytes] = {}
    for f in built.rglob("*"):
        relative = f.relative_to(built).as_posix()
        if f.is_symlink():
            errors.append(f"Lien symbolique non publiable: {relative}")
        elif f.is_file():
            # L'artefact approuvé ne doit contenir ni .git ni .github.
            if any(part in {".git", ".github"} for part in f.relative_to(built).parts):
                errors.append(f"Répertoire Git imprévu dans le build: {relative}")
                continue
            try:
                approved[relative] = hashlib.sha256(f.read_bytes()).digest()
            except OSError:
                errors.append(f"Source TAR illisible: {relative}")
    if MARKER not in approved:
        errors.append(f"Reçu caché absent du build: {MARKER}")
    elif approved[MARKER] != hashlib.sha256(receipt).digest():
        errors.append("Reçu caché incorrect avant empaquetage")
    if errors:
        return errors

    found: dict[str, bytes] = {}
    try:
        with tarfile.open(archive, mode="r:") as tar:
            for member in tar.getmembers():
                # GNU tar représente la racine du paquet par "." ou "./".
                if member.name in {".", "./"} and member.isdir():
                    continue
                name = member.name.removeprefix("./").removesuffix("/")
                if not name:
                    continue
                if (name.startswith("/") or
                        any(part in {"", ".", ".."} for part in name.split("/"))):
                    errors.append("Chemin TAR non canonique")
                    continue
                if member.isdir():
                    continue
                if not member.isfile():
                    errors.append(f"Entrée TAR non régulière: {name}")
                    continue
                if name in found:
                    errors.append(f"Entrée TAR dupliquée: {name}")
                    continue
                reader = tar.extractfile(member)
                if reader is None:
                    errors.append(f"Fichier TAR illisible: {name}")
                    continue
                with reader:
                    found[name] = hashlib.sha256(reader.read()).digest()
    except (OSError, tarfile.TarError):
        return errors + ["Archive TAR absente ou non analysable"]
    for name in sorted(approved.keys() - found.keys()):
        errors.append(f"Fichier absent de l'archive Pages: {name}")
    for name in sorted(found.keys() - approved.keys()):
        errors.append(f"Fichier supplémentaire dans l'archive Pages: {name}")
    for name in sorted(found.keys() & approved.keys()):
        if found[name] != approved[name]:
            errors.append(f"Fichier altéré pendant l'archivage Pages: {name}")
    return errors


def self_test() -> None:
    sha, run_id = "a" * 40, "1234567"
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        site = folder / "site"
        site.mkdir()
        (site / "index.html").write_text("<title>Public SINJIRA</title>", "utf-8")
        hidden = site / MARKER
        hidden.parent.mkdir(parents=True)
        hidden.write_bytes(render(sha, run_id))
        archive = folder / "artifact.tar"
        build_tar(site, archive)
        assert not audit(site, archive, sha, run_id), audit(site, archive, sha, run_id)
        assert audit(site, archive, "b" * 40, run_id), (
            "Le marqueur SHA incorrect a été accepté"
        )
        build_tar(site, archive, include_hidden=False)
        assert any(MARKER in error for error in audit(site, archive, sha, run_id)), (
            "Exclusion cachée de .well-known non détectée"
        )
        build_tar(site, archive)
        (site / "index.html").write_text("modifié après création archive", "utf-8")
        assert any("index.html" in error for error in audit(site, archive, sha, run_id)), (
            "Un TAR avec anciens octets a été accepté"
        )
        (site / "index.html").unlink()
        assert any("index.html" in error for error in audit(site, archive, sha, run_id)), (
            "Un TAR contenant un fichier supplémentaire a été accepté"
        )
        (site / "index.html").write_text("<title>Public SINJIRA</title>", "utf-8")
        hidden.unlink()
        assert any(MARKER in error for error in audit(site, archive, sha, run_id)), (
            "Reçu manquant dans le build non détecté"
        )
    print("OK archive Pages : TAR fidèle, .well-known préservé, perte et altération rejetées")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--built")
    parser.add_argument("--sha")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.built or not args.sha or not args.run_id:
        parser.error("--built, --sha et --run-id requis hors autotest")
    try:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "pages.tar"
            build_tar(Path(args.built).resolve(), archive)
            issues = audit(Path(args.built).resolve(), archive, args.sha, args.run_id)
    except (OSError, subprocess.SubprocessError) as exc:
        print("ERREUR TAR Pages : " + type(exc).__name__, file=sys.stderr)
        return 1
    for issue in issues:
        print("ERREUR TAR Pages : " + issue, file=sys.stderr)
    if issues:
        return 1
    print("OK TAR : tous les fichiers _site et le reçu .well-known sont archivés "
          "octet par octet, aucun artefact téléversé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
