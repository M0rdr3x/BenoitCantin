#!/usr/bin/env python3
"""Inventaire exact du site public construit : aucun fichier ajouté ni perdu.

Ce contrôle protège AUSSI les nouveaux formats non couverts par les audits
PDF/JSON/CSV. La source autorisée est gelée dans pages_public_inventory.txt.
Pas de réseau, de clé, ni de publication.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

from audit_pages_jekyll import config_values
from pages_release_proof import MARKER, render

MANIFEST = Path(__file__).with_name("pages_public_inventory.txt")
GENERATED_MANIFEST = Path(__file__).with_name("pages_generated_inventory.txt")
EXPECTED_COUNT = 614
GENERATED_COUNT = 31


def inventory(text: str, count: int = EXPECTED_COUNT) -> tuple[set[str], list[str]]:
    lines = [line.strip() for line in text.splitlines()
             if line.strip() and not line.startswith("#")]
    errors: list[str] = []
    for path in lines:
        parts = path.split("/")
        if (path.startswith("/") or "\\" in path or
                any(not part or part in {".", ".."} for part in parts) or
                any(part.startswith("_") for part in parts) or
                any(part.startswith(".") and not (i == 0 and part == ".well-known")
                    for i, part in enumerate(parts))):
            errors.append(f"Chemin interdit dans le manifeste: {path}")
    if lines != sorted(lines):
        errors.append("Manifeste non trié")
    if len(lines) != len(set(lines)):
        errors.append("Doublon dans le manifeste")
    if len(lines) != count:
        errors.append(f"Inventaire modifié : {len(lines)} au lieu de {count} fichiers")
    return set(lines), errors


def scan(root: Path) -> set[str]:
    # Path.is_file() suit les liens symboliques par défaut : un tel lien ne
    # peut jamais compter comme ressource approuvée du manifeste.
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


def scan_symlinks(root: Path) -> list[str]:
    # rglob voit les entrées symlink de répertoires sans les parcourir.
    # Refus indépendamment des exclusions Jekyll : tar utilise --dereference.
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_symlink()
    )


def eligible(path: str, excluded: set[str]) -> bool:
    parts = path.split("/")
    if any(path == item or path.startswith(item.rstrip("/") + "/")
           for item in excluded):
        return False
    # Comportement de base de Jekyll pour les fichiers privés; seule
    # .well-known est explicitement incluse pour les preuves de sécurité.
    for i, part in enumerate(parts):
        if part.startswith("_"):
            return False
        if part.startswith(".") and not (i == 0 and part == ".well-known"):
            return False
    return True


def audit(root: Path, built: Path | None, manifest_text: str,
          release: tuple[str, str] | None = None) -> list[str]:
    expected, errors = inventory(manifest_text)
    try:
        generated, generated_errors = inventory(
            GENERATED_MANIFEST.read_text("utf-8"), GENERATED_COUNT
        )
    except OSError as exc:
        return errors + [f"Inventaire Jekyll généré introuvable: {type(exc).__name__}"]
    errors.extend(generated_errors)
    if expected & generated:
        errors.append("Chemins source et Jekyll générés en conflit")
    if not root.is_dir():
        return errors + ["Répertoire source introuvable"]
    cfg = root / "_config.yml"
    try:
        excluded = set(config_values(cfg.read_text("utf-8"), "exclude"))
    except (OSError, ValueError) as exc:
        return errors + [f"Configuration Jekyll non vérifiable: {type(exc).__name__}"]
    if not (root / "index.html").is_file():
        errors.append("Page d'accueil source disparue")
    for link in scan_symlinks(root):
        errors.append(f"Lien symbolique interdit dans la source: {link}")
    src_files = scan(root)
    eligible_files = {path for path in src_files if eligible(path, excluded)}
    for path in sorted(eligible_files - expected):
        errors.append(f"Fichier source supplémentaire destiné au web sans revue: {path}")
    for path in sorted(expected - eligible_files):
        errors.append(f"Fichier public approuvé absent ou exclu de la source: {path}")
    if built is None:
        return errors
    if not built.is_dir():
        return errors + ["Artefact Jekyll absent"]
    for link in scan_symlinks(built):
        errors.append(f"Lien symbolique interdit dans l'artefact: {link}")
    actual = scan(built)
    approved_output = expected | generated
    if release is not None:
        approved_output.add(MARKER)
    for path in sorted(actual - approved_output):
        errors.append(f"Fichier non autorisé dans l'artefact public: {path}")
    for path in sorted(approved_output - actual):
        errors.append(f"Fichier approuvé absent de l'artefact: {path}")
    if release is not None and MARKER in actual:
        try:
            proof = render(*release)
            if (built / MARKER).read_bytes() != proof:
                errors.append("Reçu Pages SHA/run incorrect ou altéré")
        except (OSError, ValueError):
            errors.append("Reçu Pages non vérifiable")
    for path in sorted(expected & src_files & actual):
        a = hashlib.sha256((root / path).read_bytes()).digest()
        b = hashlib.sha256((built / path).read_bytes()).digest()
        if a != b:
            errors.append(f"Fichier public modifié par la compilation: {path}")
    return errors


def self_test() -> None:
    source_manifest = MANIFEST.read_text("utf-8")
    expected, errors = inventory(source_manifest)
    assert not errors, errors
    generated, errors = inventory(GENERATED_MANIFEST.read_text("utf-8"), GENERATED_COUNT)
    assert not errors and not expected & generated, errors
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "repo"
        built = Path(temporary) / "site"
        root.mkdir()
        built.mkdir()
        (root / "_config.yml").write_text('exclude:\n  - "scripts"\n', "utf-8")
        for rel in expected:
            for base in (root, built):
                target = base / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(("public:" + rel).encode("utf-8"))
        for rel in generated:
            target = built / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(("generated:" + rel).encode("utf-8"))
        assert not audit(root, built, source_manifest), audit(root, built, source_manifest)
        receipt_id = ("a" * 40, "12345")
        assert any(MARKER in error for error in audit(
            root, built, source_manifest, receipt_id
        )), "Reçu absent non détecté"
        receipt = built / MARKER
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_bytes(render(*receipt_id))
        assert not audit(root, built, source_manifest, receipt_id), (
            audit(root, built, source_manifest, receipt_id)
        )
        assert any(MARKER in error for error in audit(root, built, source_manifest)), (
            "Reçu absent de l'inventaire de build normal non détecté"
        )
        receipt.write_bytes(b'{}')
        assert any("Reçu Pages" in error for error in audit(
            root, built, source_manifest, receipt_id
        )), "Reçu falsifié non détecté"
        receipt.unlink()
        assert not audit(root, built, source_manifest), audit(root, built, source_manifest)
        derived = sorted(generated)[0]
        (built / derived).unlink()
        assert any(derived in e and "absent de l'artefact" in e
                   for e in audit(root, built, source_manifest)), (
            "Page Jekyll générée disparue non détectée"
        )
        (built / derived).write_bytes(("generated:" + derived).encode("utf-8"))
        example = sorted(expected)[-1]
        (built / example).unlink()
        assert any(example in e and "absent de l'artefact" in e
                   for e in audit(root, built, source_manifest)), "Perte publique non détectée"
        (built / example).write_text("altéré", "utf-8")
        assert any(example in e and "modifié" in e
                   for e in audit(root, built, source_manifest)), "Mutation binaire non détectée"
        (built / example).write_bytes(("public:" + example).encode("utf-8"))
        for rel in ("assets/media/document-confidentiel.webp",
                    "projets/projet-nova/data/registre.export",
                    "projets/sinjira/extra.mjs"):
            path = built / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fichier inconnu", "utf-8")
            assert any(rel in e for e in audit(root, built, source_manifest)), (
                f"Fichier supplémentaire non détecté: {rel}"
            )
            path.unlink()
            path = root / rel
            path.write_text("nouvelle source", "utf-8")
            assert any(rel in e for e in audit(root, None, source_manifest)), (
                f"Nouvelle source non détectée: {rel}"
            )
            path.unlink()
        private = root / "scripts/internal.py"
        private.parent.mkdir(parents=True, exist_ok=True)
        private.write_text("interne", "utf-8")
        assert not audit(root, built, source_manifest), "Exclusions techniques non respectées"

        # Symlink de fichier : pourrait faire publier un secret avec --dereference,
        # y compris si la source cible est exclue de Jekyll.
        source_leak = root / "assets/public-secret.txt"
        source_leak.parent.mkdir(parents=True, exist_ok=True)
        source_leak.symlink_to(private)
        assert any("Lien symbolique interdit dans la source" in e and
                   "public-secret.txt" in e for e in audit(
                       root, built, source_manifest
                   )), "Symlink source vers un fichier privé accepté"
        source_leak.unlink()

        # Symlink de répertoire : Path.rglob ne doit pas le rendre invisible.
        source_directory = root / "assets/private-directory"
        source_directory.symlink_to(private.parent, target_is_directory=True)
        assert any("Lien symbolique interdit dans la source" in e and
                   "private-directory" in e for e in audit(
                       root, built, source_manifest
                   )), "Symlink source de dossier privé accepté"
        source_directory.unlink()

        for relative, target_path, directory in (
            ("assets/public-secret.txt", private, False),
            ("assets/private-directory", private.parent, True),
            ("assets/broken-secret.txt", root / "scripts/not-found.txt", False),
        ):
            leak = built / relative
            leak.symlink_to(target_path, target_is_directory=directory)
            assert any("Lien symbolique interdit dans l'artefact" in e and
                       relative in e for e in audit(
                           root, built, source_manifest
                       )), f"Lien symbolique artefact non détecté: {relative}"
            leak.unlink()
        assert not audit(root, built, source_manifest), (
            "L'audit sain échoue après les cas symlink"
        )
        bad_manifest = source_manifest + "assets/image-nouvelle.webp\n"
        assert any("Inventaire modifié" in e for e in audit(root, None, bad_manifest))
        assert not audit(root, built, source_manifest), audit(root, built, source_manifest)
    print("OK inventaire public global: 614 fichiers source + 31 pages générées, "
          "ajouts, pertes, altérations et liens symboliques refusés")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--source")
    parser.add_argument("--built")
    parser.add_argument("--release-sha", help="SHA attendu du marqueur Pages")
    parser.add_argument("--release-run-id", help="Run GitHub attendu du marqueur Pages")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.source:
        parser.error("--source requis sans --self-test")
    try:
        manifest = MANIFEST.read_text("utf-8")
    except OSError as exc:
        print(f"ERREUR manifeste: {type(exc).__name__}", file=sys.stderr)
        return 1
    if bool(args.release_sha) != bool(args.release_run_id):
        parser.error("--release-sha et --release-run-id doivent être fournis ensemble")
    if args.release_sha and not args.built:
        parser.error("--built requis pour la preuve d'identité Pages")
    identity = (args.release_sha, args.release_run_id) if args.release_sha else None
    issues = audit(Path(args.source).resolve(),
                   Path(args.built).resolve() if args.built else None,
                   manifest, identity)
    for issue in issues:
        print("ERREUR: " + issue, file=sys.stderr)
    if issues:
        return 1
    print(f"OK : {EXPECTED_COUNT} fichiers source + {GENERATED_COUNT} générés"
          + (" + 1 reçu Pages" if identity else "")
          + " présents et contrôlés, aucune addition ou perte non revue")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
