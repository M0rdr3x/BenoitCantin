#!/usr/bin/env python3
"""Protéger les documents publics déjà approuvés, sans ouvrir le catalogue privé.

Les livres intégraux / archives / éditions à vendre ne sont pas hébergés
statiquement. L'inventaire est figé à partir des 20 PDF réellement présents
sur main le 10 octobre 2026. Aucun accès réseau ni clé privée n'est nécessaire.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

APPROVED_PUBLIC_PDFS = frozenset({
    "projets/projet-nova/documents/01_Resume_Officiel_1_Page_Projet_Nova.pdf",
    "projets/projet-nova/documents/02_Depliant_Public_4_Pages_Projet_Nova.pdf",
    "projets/projet-nova/documents/03_Livre_Nova_Version_Courte.pdf",
    "projets/projet-nova/documents/04_Livre_Nova_Complet.pdf",
    "projets/projet-nova/documents/04_Livre_Nova_Complet_V1_8.pdf",
    "projets/projet-nova/documents/05_Manifeste_Officiel_Projet_Nova.pdf",
    "projets/projet-nova/documents/06_FAQ_Citoyenne_Officielle_Projet_Nova.pdf",
    "projets/projet-nova/documents/07_Programme_Electoral_Complet_Projet_Nova.pdf",
    "projets/projet-nova/documents/08_Code_de_Conduite_Gouvernance_Nova.pdf",
    "projets/projet-nova/documents/09_Dossier_de_Presse_Projet_Nova.pdf",
    "projets/projet-nova/documents/11_Charte_Visuelle_Projet_Nova.pdf",
    "projets/projet-nova/documents/12_Resume_Executif_Officiel_Systeme_Nova.pdf",
    "projets/sinjira/documents/Questionnaire_Registre_des_Consciences_Fans.pdf",
    "projets/sinjira/documents/Questionnaire_SINJIRA_Registre_des_Consciences.pdf",
    "projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf",
    "projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Feuille_de_fin_de_partie_Interactive.pdf",
    "projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fiche_Joueur_1_Copie_Interactive.pdf",
    "projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fiche_Joueur_Interactive.pdf",
    "projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fracture_du_Reseau_Mere_Fiche_Joueur_Web.pdf",
    "projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Mode_Solo_3_Joueurs_Interactive.pdf",
})

# Ces archives / livres électroniques ne font pas partie de l'offre gratuite.
# Un nouveau format doit être revu et ajouté explicitement, jamais implicitement.
PROHIBITED_PUBLIC_SUFFIXES = frozenset({
    ".epub", ".mobi", ".azw", ".azw3", ".cbz", ".cbr",
    ".docx", ".odt", ".rtf", ".zip", ".7z", ".rar", ".tar", ".gz",
})


def paths_by_suffix(root: Path, suffixes: set[str] | frozenset[str]) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in suffixes
    }


def audit(root: Path, built: Path | None) -> list[str]:
    errors: list[str] = []
    if len(APPROVED_PUBLIC_PDFS) != 20:
        errors.append("Inventaire des 20 PDF publics altéré")
    if not root.is_dir():
        return ["Dossier source absent"]
    source_pdfs = paths_by_suffix(root, {".pdf"})
    extra_source = source_pdfs - APPROVED_PUBLIC_PDFS
    missing_source = APPROVED_PUBLIC_PDFS - source_pdfs
    for rel in sorted(extra_source):
        errors.append(f"PDF non autorisé dans le dépôt public: {rel}")
    for rel in sorted(missing_source):
        errors.append(f"PDF public approuvé disparu du dépôt: {rel}")
    for rel in sorted(paths_by_suffix(root, PROHIBITED_PUBLIC_SUFFIXES)):
        errors.append(f"Document/archive non autorisé dans le dépôt public: {rel}")
    if built is None:
        return errors
    if not built.is_dir():
        return errors + ["Artefact public inexistant"]
    built_pdfs = paths_by_suffix(built, {".pdf"})
    for rel in sorted(built_pdfs - APPROVED_PUBLIC_PDFS):
        errors.append(f"PDF non autorisé publié: {rel}")
    for rel in sorted(APPROVED_PUBLIC_PDFS - built_pdfs):
        errors.append(f"PDF public approuvé absent du build: {rel}")
    for rel in sorted(paths_by_suffix(built, PROHIBITED_PUBLIC_SUFFIXES)):
        errors.append(f"Document/archive non autorisé publié: {rel}")
    for rel in sorted(APPROVED_PUBLIC_PDFS & source_pdfs & built_pdfs):
        original = root / rel
        published = built / rel
        if (hashlib.sha256(original.read_bytes()).digest()
                != hashlib.sha256(published.read_bytes()).digest()):
            errors.append(f"PDF public modifié pendant la compilation: {rel}")
    return errors


def self_test() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "source"
        out = Path(d) / "built"
        root.mkdir()
        out.mkdir()
        for rel in APPROVED_PUBLIC_PDFS:
            for base in (root, out):
                file = base / rel
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(b"%PDF-fixture")
        assert audit(root, None) == [], audit(root, None)
        assert audit(root, out) == [], audit(root, out)
        approved = sorted(APPROVED_PUBLIC_PDFS)[0]
        target = out / approved
        target.unlink()
        assert any(approved in e and "absent du build" in e
                   for e in audit(root, out)), "PDF approuvé disparu non détecté"
        target.write_bytes(b"invalid")
        assert any(approved in e and "modifié" in e
                   for e in audit(root, out)), "PDF approuvé altéré non détecté"
        target.write_bytes(b"%PDF-fixture")
        source = root / approved
        source.unlink()
        assert any(approved in e and "disparu du dépôt" in e
                   for e in audit(root, None)), "PDF source disparu non détecté"
        source.write_bytes(b"%PDF-fixture")
        fake = "projets/sinjira/documents/SINJIRA_ROMAN_01_INTEGRAL.pdf"
        for base in (root, out):
            path = base / fake
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"%PDF-integral-non-public")
        assert any(fake in e for e in audit(root, None)), "Roman payant dans Git accepté"
        assert any(fake in e and "publié" in e for e in audit(root, out)), "Roman payant publié accepté"
        (root / fake).unlink()
        (out / fake).unlink()
        for ext in (".epub", ".docx", ".zip"):
            forbidden = root / ("projets/sinjira/documents/edition-integrale" + ext)
            forbidden.parent.mkdir(parents=True, exist_ok=True)
            forbidden.write_bytes(b"not-public")
            assert any(ext in e for e in audit(root, None)), f"Format {ext} accepté"
            forbidden.unlink()
        assert audit(root, out) == [], audit(root, out)
    print(f"OK PDF : {len(APPROVED_PUBLIC_PDFS)} documents publics exacts, "
          "aucune édition intégrale/archives non approuvée")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--source")
    parser.add_argument("--built")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    problems = audit(Path(args.source).resolve(),
                     Path(args.built).resolve() if args.built else None)
    if problems:
        for problem in problems:
            print("ERREUR : " + problem, file=sys.stderr)
        return 1
    print(f"OK : {len(APPROVED_PUBLIC_PDFS)} PDF publics approuvés, "
          "aucun document réservé et intégrité du build vérifiée")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
