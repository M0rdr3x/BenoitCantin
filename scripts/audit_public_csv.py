#!/usr/bin/env python3
"""Contrat de publication des modèles CSV publics de Projet Nova.

57 modèles/documentations répertoriés depuis main (10 octobre 2026).
Refuse la publication non revue de véritables CSV opérationnels.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path
from audit_pages_jekyll import config_values

APPROVED_PUBLIC_CSV = frozenset({
    "projets/projet-nova/data/modele_comptabilite.csv",
    "projets/projet-nova/data/modele_rencontres.csv",
    "projets/projet-nova/official/versions/V316/V316_REGISTRE_ACCES_CITOYEN_CORRECTIONS_MODELE.csv",
    "projets/projet-nova/official/versions/V316/V316_REGISTRE_BASES_LEGALES_FINALITES_PARTAGES_MODELE.csv",
    "projets/projet-nova/official/versions/V316/V316_REGISTRE_CYCLE_VIE_DOSSIERS_MODELE.csv",
    "projets/projet-nova/official/versions/V316/V316_REGISTRE_IDENTITES_JUSTIFICATIFS_MODELE.csv",
    "projets/projet-nova/official/versions/V316/V316_REGISTRE_INCIDENTS_REVOCATIONS_MODELE.csv",
    "projets/projet-nova/official/versions/V316/V316_REGISTRE_INTEROPERABILITE_ECHANGES_MODELE.csv",
    "projets/projet-nova/official/versions/V316/V316_REGISTRE_JOURNAUX_AUDIT_ACCES_MODELE.csv",
    "projets/projet-nova/official/versions/V316/V316_REGISTRE_PERMISSIONS_ACCES_MODELE.csv",
    "projets/projet-nova/official/versions/V317/V317_REGISTRE_CHANGEMENTS_SECURITE_CONFIGURATIONS_MODELE.csv",
    "projets/projet-nova/official/versions/V317/V317_REGISTRE_CONTINUITE_REPRISE_MODELE.csv",
    "projets/projet-nova/official/versions/V317/V317_REGISTRE_EXERCICES_TESTS_CORRECTIFS_MODELE.csv",
    "projets/projet-nova/official/versions/V317/V317_REGISTRE_FOURNISSEURS_DEPENDANCES_NUMERIQUES_MODELE.csv",
    "projets/projet-nova/official/versions/V317/V317_REGISTRE_INCIDENTS_CYBER_REPONSES_MODELE.csv",
    "projets/projet-nova/official/versions/V317/V317_REGISTRE_SAUVEGARDES_RESTAURATIONS_MODELE.csv",
    "projets/projet-nova/official/versions/V317/V317_REGISTRE_SYSTEMES_CRITIQUES_DEPENDANCES_MODELE.csv",
    "projets/projet-nova/official/versions/V317/V317_REGISTRE_VULNERABILITES_CORRECTIFS_MODELE.csv",
    "projets/projet-nova/official/versions/V318/V318_REGISTRE_CONTRATS_INTERFACE_VERSIONS_MODELE.csv",
    "projets/projet-nova/official/versions/V318/V318_REGISTRE_CYCLE_VIE_FIN_SUPPORT_MODELE.csv",
    "projets/projet-nova/official/versions/V318/V318_REGISTRE_DEPENDANCES_LICENCES_ENFERMEMENT_MODELE.csv",
    "projets/projet-nova/official/versions/V318/V318_REGISTRE_EXCEPTIONS_ARCHITECTURALES_MODELE.csv",
    "projets/projet-nova/official/versions/V318/V318_REGISTRE_FORMATS_SCHEMAS_PORTABILITE_MODELE.csv",
    "projets/projet-nova/official/versions/V318/V318_REGISTRE_MIGRATIONS_DECOMMISSIONNEMENTS_MODELE.csv",
    "projets/projet-nova/official/versions/V318/V318_REGISTRE_PLANS_SORTIE_REVERSIBILITE_MODELE.csv",
    "projets/projet-nova/official/versions/V318/V318_REGISTRE_PORTEFEUILLE_SYSTEMES_STANDARDS_MODELE.csv",
    "projets/projet-nova/official/versions/V319/V319_REGISTRE_ARCHIVES_FORMATS_PRESERVATION_MODELE.csv",
    "projets/projet-nova/official/versions/V319/V319_REGISTRE_BUILDS_REPRODUCTIBLES_MODELE.csv",
    "projets/projet-nova/official/versions/V319/V319_REGISTRE_CLASSIFICATION_GARDE_DONNEES_MODELE.csv",
    "projets/projet-nova/official/versions/V319/V319_REGISTRE_CONTINUITE_SAVOIR_DOCUMENTATION_MODELE.csv",
    "projets/projet-nova/official/versions/V319/V319_REGISTRE_ENTIERCEMENTS_DROITS_CONTINUITE_MODELE.csv",
    "projets/projet-nova/official/versions/V319/V319_REGISTRE_EXCEPTIONS_RISQUES_COMPENSATIONS_MODELE.csv",
    "projets/projet-nova/official/versions/V319/V319_REGISTRE_MATERIAUX_RECONSTRUCTION_MODELE.csv",
    "projets/projet-nova/official/versions/V319/V319_REGISTRE_MIGRATIONS_INTERGENERATIONNELLES_MODELE.csv",
    "projets/projet-nova/official/versions/V320/V320_REGISTRE_ANTI_CONTOURNEMENT_MODELE.csv",
    "projets/projet-nova/official/versions/V320/V320_REGISTRE_CLASSIFICATION_ENTITES_MIXTES_PUBLIQUES_MODELE.csv",
    "projets/projet-nova/official/versions/V320/V320_REGISTRE_CONTINUITE_SERVICES_ESSENTIELS_MODELE.csv",
    "projets/projet-nova/official/versions/V320/V320_REGISTRE_CONTRATS_PRIVES_TRANSITION_MODELE.csv",
    "projets/projet-nova/official/versions/V320/V320_REGISTRE_FERMETURE_AIDES_PRIVEES_MODELE.csv",
    "projets/projet-nova/official/versions/V320/V320_REGISTRE_FLUX_PUBLIC_PRIVE_MODELE.csv",
    "projets/projet-nova/official/versions/V320/V320_REGISTRE_INTERNALISATION_CAPACITES_PUBLIQUES_MODELE.csv",
    "projets/projet-nova/official/versions/V320/V320_REGISTRE_OBLIGATIONS_NON_COMMERCIALES_MODELE.csv",
    "projets/projet-nova/official/versions/V321/V321_REGISTRE_CAPACITES_PUBLIQUES_CRITIQUES_MODELE.csv",
    "projets/projet-nova/official/versions/V321/V321_REGISTRE_CHAINES_APPROVISIONNEMENT_INTERPUBLIQUES_MODELE.csv",
    "projets/projet-nova/official/versions/V321/V321_REGISTRE_COMPETENCES_CRITIQUES_RELEVE_MODELE.csv",
    "projets/projet-nova/official/versions/V321/V321_REGISTRE_DECISIONS_PREPARATION_BASCULE_MODELE.csv",
    "projets/projet-nova/official/versions/V321/V321_REGISTRE_DEPENDANCES_INFRASTRUCTURES_CONTINUITE_MODELE.csv",
    "projets/projet-nova/official/versions/V321/V321_REGISTRE_EXERCICES_DEFAILLANCES_CORRECTIFS_MODELE.csv",
    "projets/projet-nova/official/versions/V321/V321_REGISTRE_PRODUCTION_MAINTENANCE_REPARATION_MODELE.csv",
    "projets/projet-nova/official/versions/V321/V321_REGISTRE_STOCKS_INTRANTS_CRITIQUES_MODELE.csv",
    "projets/projet-nova/official/versions/V322/V322_REGISTRE_ALLOCATION_CAPACITES_PENURIE_MODELE.csv",
    "projets/projet-nova/official/versions/V322/V322_REGISTRE_CYCLE_VIE_ACTIFS_PUBLICS_MODELE.csv",
    "projets/projet-nova/official/versions/V322/V322_REGISTRE_DECOMMISSIONNEMENT_FERMETURE_MODELE.csv",
    "projets/projet-nova/official/versions/V322/V322_REGISTRE_DEPENDANCES_CRITIQUES_MODELE.csv",
    "projets/projet-nova/official/versions/V322/V322_REGISTRE_MAINTENANCE_DEFAILLANCES_MODELE.csv",
    "projets/projet-nova/official/versions/V322/V322_REGISTRE_OBSOLESCENCE_RENOUVELLEMENT_MODELE.csv",
    "projets/projet-nova/official/versions/V322/V322_REGISTRE_RESEAU_LOGISTIQUE_PUBLIC_MODELE.csv",
})


def files(root: Path) -> set[str]:
    return {
        p.relative_to(root).as_posix()
        for p in root.rglob("*.csv")
        if p.is_file() and not p.is_symlink()
        and not any(part in {".git", "_site"} for part in p.relative_to(root).parts[:-1])
    }


def covered(path: str, excluded: set[str]) -> bool:
    return any(path == entry or path.startswith(entry.rstrip("/") + "/")
               for entry in excluded)


def audit(source: Path, built: Path | None) -> list[str]:
    errors: list[str] = []
    if len(APPROVED_PUBLIC_CSV) != 57:
        errors.append("L'inventaire CSV connu doit compter 57 fichiers")
    if not source.is_dir():
        return errors + ["Dossier source inexistant"]
    try:
        excluded = set(config_values((source / "_config.yml").read_text("utf-8"), "exclude"))
    except (OSError, ValueError) as exc:
        return errors + [f"Exclusions Jekyll non vérifiables: {type(exc).__name__}"]
    existing = files(source)
    publicly_included = {p for p in existing if not covered(p, excluded)}
    for p in sorted(publicly_included - APPROVED_PUBLIC_CSV):
        errors.append(f"CSV nouveau non approuvé pour le web: {p}")
    for p in sorted(APPROVED_PUBLIC_CSV - existing):
        errors.append(f"CSV approuvé disparu du dépôt: {p}")
    for p in sorted(APPROVED_PUBLIC_CSV):
        if covered(p, excluded):
            errors.append(f"CSV approuvé exclu de la compilation: {p}")
    if built is None:
        return errors
    if not built.is_dir():
        return errors + ["Artefact Jekyll absent"]
    published = files(built)
    for p in sorted(published - APPROVED_PUBLIC_CSV):
        errors.append(f"CSV non approuvé publié: {p}")
    for p in sorted(APPROVED_PUBLIC_CSV - published):
        errors.append(f"CSV public disparu du build: {p}")
    for p in sorted(APPROVED_PUBLIC_CSV & existing & published):
        if (hashlib.sha256((source / p).read_bytes()).digest()
                != hashlib.sha256((built / p).read_bytes()).digest()):
            errors.append(f"CSV public modifié par Jekyll: {p}")
    return errors


def self_test() -> None:
    with tempfile.TemporaryDirectory() as d:
        source, built = Path(d) / "source", Path(d) / "built"
        source.mkdir()
        built.mkdir()
        (source / "_config.yml").write_text('exclude:\n  - "scripts"\n', "utf-8")
        for p in APPROVED_PUBLIC_CSV:
            for base in (source, built):
                file = base / p
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("colonne,modele\n", "utf-8")
        assert audit(source, built) == [], audit(source, built)
        sample = sorted(APPROVED_PUBLIC_CSV)[0]
        (built / sample).unlink()
        assert any(sample in e and "disparu du build" in e for e in audit(source, built))
        (built / sample).write_text("valeur,reelle\n", "utf-8")
        assert any(sample in e and "modifié" in e for e in audit(source, built))
        (built / sample).write_text("colonne,modele\n", "utf-8")
        new_path = "projets/projet-nova/data/registre-citoyens-export.csv"
        original = source / new_path
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_text("identifiant,nom\n1,EXEMPLE\n", "utf-8")
        assert any(new_path in e for e in audit(source, None)), "CSV inédit source non détecté"
        original.unlink()
        leaked = built / new_path
        leaked.write_text("identifiant,nom\n1,EXEMPLE\n", "utf-8")
        assert any(new_path in e for e in audit(source, built)), "CSV inédit publié non détecté"
        leaked.unlink()
        settings = source / "_config.yml"
        settings.write_text('exclude:\n  - "projets/projet-nova/official"\n', "utf-8")
        assert any("approuvé exclu" in e for e in audit(source, None)), (
            "Exclusion des modèles CSV non détectée"
        )
        settings.write_text('exclude:\n  - "scripts"\n', "utf-8")
        assert audit(source, built) == [], audit(source, built)
    print("OK CSV : 57 modèles publics intègres, nouveaux registres privés refusés")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--source")
    p.add_argument("--built")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.source:
        p.error("--source requis")
    issues = audit(Path(args.source).resolve(),
                   Path(args.built).resolve() if args.built else None)
    if issues:
        for issue in issues:
            print("ERREUR: " + issue, file=sys.stderr)
        return 1
    print("OK CSV : 57 fichiers approuvés et intacts dans l'artefact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
