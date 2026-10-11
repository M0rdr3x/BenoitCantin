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

MANIFEST = Path(__file__).with_name("pages_public_inventory.txt")
EXPECTED_COUNT = 614


def inventory(text: str) -> tuple[set[str], list[str]]:
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
    if len(lines) != EXPECTED_COUNT:
        errors.append(f"Inventaire modifié : {len(lines)} au lieu de {EXPECTED_COUNT} fichiers")
    return set(lines), errors


def scan(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


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


def audit(root: Path, built: Path | None, manifest_text: str) -> list[str]:
    expected, errors = inventory(manifest_text)
    if not root.is_dir():
        return errors + ["Répertoire source introuvable"]
    cfg = root / "_config.yml"
    try:
        excluded = set(config_values(cfg.read_text("utf-8"), "exclude"))
    except (OSError, ValueError) as exc:
        return errors + [f"Configuration Jekyll non vérifiable: {type(exc).__name__}"]
    if not (root / "index.html").is_file():
        errors.append("Page d'accueil source disparue")
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
    actual = scan(built)
    for path in sorted(actual - expected):
        errors.append(f"Fichier non autorisé dans l'artefact public: {path}")
    for path in sorted(expected - actual):
        errors.append(f"Fichier approuvé absent de l'artefact: {path}")
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
        assert not audit(root, built, source_manifest), audit(root, built, source_manifest)
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
        bad_manifest = source_manifest + "assets/image-nouvelle.webp\n"
        assert any("Inventaire modifié" in e for e in audit(root, None, bad_manifest))
        assert not audit(root, built, source_manifest), audit(root, built, source_manifest)
    print("OK inventaire public global: 614 ressources exactes, nouvelles sources, "
          "pertes et altérations refusées")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--source")
    parser.add_argument("--built")
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
    issues = audit(Path(args.source).resolve(),
                   Path(args.built).resolve() if args.built else None, manifest)
    for issue in issues:
        print("ERREUR: " + issue, file=sys.stderr)
    if issues:
        return 1
    print(f"OK : {EXPECTED_COUNT} ressources publiques exactes, "
          "aucune addition ou perte non revue")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
