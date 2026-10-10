#!/usr/bin/env python3
"""Registre fermé des JSON réellement destinés au public SINJIRA/Nova.

Inventaire prouvé depuis le main Git 790b1424 (2026-10-10):
50 chemins JSON publics; 28 chemins de développement explicitement exclus.
Un JSON nouveau n'est pas publié silencieusement. Aucune donnée n'est envoyée.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

from audit_pages_jekyll import config_values

# Fichiers d'interface, données électorales, pièces publiques de Nova
# et manifeste public Livre I. Leur contenu est conservé au bit près.
PUBLIC_JSON = frozenset({
    "documents-word-only.json",
    "documents.json",
    "projets/projet-nova/data/actualites.json",
    "projets/projet-nova/data/boussole-electorale-v1.json",
    "projets/projet-nova/data/boussole-electorale-v2.json",
    "projets/projet-nova/data/boussole-partis-2026.json",
    "projets/projet-nova/data/boussole-preuves-2026.json",
    "projets/projet-nova/data/boussole-sources-partis-2026.json",
    "projets/projet-nova/data/comptabilite.json",
    "projets/projet-nova/data/documents-word-only.json",
    "projets/projet-nova/data/documents.json",
    "projets/projet-nova/data/rencontres.json",
    "projets/projet-nova/data/sources.json",
    "projets/projet-nova/documents-word-only.json",
    "projets/projet-nova/documents.json",
    "projets/projet-nova/official/CURRENT_VERSION.json",
    "projets/projet-nova/official/versions/V316/V316_FINAL_INDEPENDENT_VERIFICATION.json",
    "projets/projet-nova/official/versions/V316/V316_GITHUB_PUBLICATION_RECEIPT.json",
    "projets/projet-nova/official/versions/V316/V316_IDENTITE_NUMERIQUE_VIE_PRIVEE_ACCES_AUDIT_STATE.json",
    "projets/projet-nova/official/versions/V316/V316_LOCAL_CHECKPOINT_HISTORY_COMMITMENT.json",
    "projets/projet-nova/official/versions/V316/V317_HANDOFF_CONTRACT_V316.json",
    "projets/projet-nova/official/versions/V317/V317_CYBERSECURITE_RESILIENCE_CONTINUITE_STATE.json",
    "projets/projet-nova/official/versions/V317/V317_FINAL_INDEPENDENT_VERIFICATION.json",
    "projets/projet-nova/official/versions/V317/V317_GITHUB_PUBLICATION_RECEIPT.json",
    "projets/projet-nova/official/versions/V317/V318_HANDOFF_CONTRACT_V317.json",
    "projets/projet-nova/official/versions/V318/V318_ARCHITECTURE_NUMERIQUE_INTEROPERABILITE_REVERSIBILITE_STATE.json",
    "projets/projet-nova/official/versions/V318/V318_FINAL_INDEPENDENT_VERIFICATION.json",
    "projets/projet-nova/official/versions/V318/V318_GITHUB_PUBLICATION_RECEIPT.json",
    "projets/projet-nova/official/versions/V318/V318_LOCAL_CHECKPOINT_HISTORY_COMMITMENT.json",
    "projets/projet-nova/official/versions/V318/V319_HANDOFF_CONTRACT_V318.json",
    "projets/projet-nova/official/versions/V319/V319_CURRENT_STATE.json",
    "projets/projet-nova/official/versions/V319/V319_FINAL_INDEPENDENT_VERIFICATION.json",
    "projets/projet-nova/official/versions/V319/V319_GITHUB_PUBLICATION_RECEIPT.json",
    "projets/projet-nova/official/versions/V319/V319_SOUVERAINETE_DONNEES_ARCHIVES_REPRODUCTIBILITE_STATE.json",
    "projets/projet-nova/official/versions/V319/V320_HANDOFF_CONTRACT_V319.json",
    "projets/projet-nova/official/versions/V320/V320_CURRENT_STATE.json",
    "projets/projet-nova/official/versions/V320/V320_FINAL_INDEPENDENT_VERIFICATION.json",
    "projets/projet-nova/official/versions/V320/V320_GITHUB_PUBLICATION_RECEIPT.json",
    "projets/projet-nova/official/versions/V320/V320_OFFICIAL_POINTER_UPDATE_RECEIPT.json",
    "projets/projet-nova/official/versions/V320/V320_SEPARATION_DEPENSES_PUBLIQUES_SECTEUR_PRIVE_STATE.json",
    "projets/projet-nova/official/versions/V320/V321_HANDOFF_CONTRACT_V320.json",
    "projets/projet-nova/official/versions/V321/V321_AUTONOMIE_OPERATIONNELLE_PUBLIQUE_CAPACITES_CRITIQUES_CONTINUITE_STATE.json",
    "projets/projet-nova/official/versions/V321/V321_CURRENT_STATE.json",
    "projets/projet-nova/official/versions/V321/V321_FINAL_INDEPENDENT_VERIFICATION.json",
    "projets/projet-nova/official/versions/V321/V321_GITHUB_PUBLICATION_RECEIPT.json",
    "projets/projet-nova/official/versions/V321/V322_HANDOFF_CONTRACT_V321.json",
    "projets/projet-nova/official/versions/V322/V322_CURRENT_STATE.json",
    "projets/projet-nova/official/versions/V322/V322_FINAL_INDEPENDENT_VERIFICATION.json",
    "projets/projet-nova/official/versions/V322/V322_GESTION_CYCLE_VIE_ACTIFS_PUBLICS_LOGISTIQUE_STATE.json",
    "projets/sinjira/romans/livre-1-release.json",
})

# Documents techniques présents dans Git qui doivent rester ABSENTS du web.
INTERNAL_JSON = frozenset({
    "MANIFEST_PACK_CUMULATIF_V8_A_V13.json",
    "VERIFICATION_ADMIN_PRO_V16.json",
    "VERIFICATION_ADMIN_PRO_V17.json",
    "VERIFICATION_COMPTE_UNIVERSEL.json",
    "VERIFICATION_FRACTURE_ONLINE_V9.json",
    "VERIFICATION_FRACTURE_V8.json",
    "VERIFICATION_MISE_A_JOUR_V11.json",
    "VERIFICATION_MISE_A_JOUR_V12.json",
    "VERIFICATION_MISE_A_JOUR_V13.json",
    "VERIFICATION_PACK_CUMULATIF_V8_A_V13.json",
    "VERIFICATION_PRO_V15.json",
    "VERIFICATION_SINJIRA.json",
    "VERIFICATION_SITE_COMPLET_V14.json",
    "VERIFICATION_SYSTEME.json",
    "VERIFICATION_V10.json",
    "VERIFICATION_V18_ACCUEIL.json",
    "VERIFICATION_V18_FINAL.json",
    "VERIFICATION_V18_FINAL_CANON.json",
    "VERIFICATION_V18_FINAL_REV2.json",
    "VERIFICATION_V19_PRO.json",
    "VERIFICATION_V20_1.json",
    "VERIFICATION_V20_PATCH.json",
    "VERIFICATION_VISUELS_SINJIRA_V2.json",
    "mobile-native/app.json",
    "mobile-native/eas.json",
    "mobile-native/package.json",
    "mobile-native/tsconfig.json",
    "projets/sinjira/codex/livre-i-delivery-contract.json",
})

REQUIRED_PUBLIC_COUNT = 50
REQUIRED_INTERNAL_COUNT = 28


def json_paths(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*.json")
        if path.is_file() and not path.is_symlink()
        and not any(part in {".git", "_site"} for part in path.relative_to(root).parts[:-1])
    }


def covered(path: str, exclusions: set[str]) -> bool:
    return any(path == exclusion or path.startswith(exclusion.rstrip("/") + "/")
               for exclusion in exclusions)


def audit(source: Path, built: Path | None) -> list[str]:
    errors: list[str] = []
    if len(PUBLIC_JSON) != REQUIRED_PUBLIC_COUNT or len(INTERNAL_JSON) != REQUIRED_INTERNAL_COUNT:
        errors.append("Inventaire JSON approuvé modifié sans migration documentée")
    if PUBLIC_JSON & INTERNAL_JSON:
        errors.append("Ambiguïté : un JSON est simultanément public et interne")
    if not source.is_dir():
        return errors + ["Répertoire source manquant"]
    config = source / "_config.yml"
    if not config.is_file():
        return errors + ["_config.yml manquant pour l'allowlist JSON"]
    try:
        excluded = set(config_values(config.read_text("utf-8"), "exclude"))
    except (OSError, ValueError) as exc:
        return errors + [f"Configuration d'exclusion invalide: {type(exc).__name__}"]
    source_all = json_paths(source)
    source_public = {p for p in source_all if not covered(p, excluded)}
    for path in sorted(source_public - PUBLIC_JSON):
        errors.append(f"JSON nouveau non approuvé pour le public: {path}")
    for path in sorted(PUBLIC_JSON - source_all):
        errors.append(f"JSON public attendu disparu du dépôt: {path}")
    for path in sorted(PUBLIC_JSON):
        if covered(path, excluded):
            errors.append(f"JSON public exclu de la publication: {path}")
    for path in sorted(INTERNAL_JSON):
        if path not in source_all:
            errors.append(f"JSON interne attendu disparu du dépôt: {path}")
        if not covered(path, excluded):
            errors.append(f"JSON technique non exclu du build: {path}")
    if built is None:
        return errors
    if not built.is_dir():
        return errors + ["Artefact Jekyll inexistant"]
    published = json_paths(built)
    for path in sorted(published - PUBLIC_JSON):
        errors.append(f"JSON technique ou inconnu publié: {path}")
    for path in sorted(PUBLIC_JSON - published):
        errors.append(f"JSON public absent de l'artefact: {path}")
    for path in sorted(PUBLIC_JSON & source_all & published):
        a = hashlib.sha256((source / path).read_bytes()).digest()
        b = hashlib.sha256((built / path).read_bytes()).digest()
        if a != b:
            errors.append(f"JSON public transformé pendant la compilation: {path}")
    return errors


def self_test() -> None:
    with tempfile.TemporaryDirectory() as directory:
        source, built = Path(directory) / "source", Path(directory) / "built"
        source.mkdir()
        built.mkdir()
        excluded = sorted(INTERNAL_JSON)
        (source / "_config.yml").write_text(
            "exclude:\n" + "".join(f'  - "{path}"\n' for path in excluded)
            + 'include:\n  - ".well-known"\n', "utf-8"
        )
        for path in PUBLIC_JSON:
            for root in (source, built):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('{"public":true}', "utf-8")
        for path in INTERNAL_JSON:
            target = source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('{"internal":true}', "utf-8")
        assert not audit(source, built), audit(source, built)

        path = sorted(PUBLIC_JSON)[0]
        (built / path).unlink()
        assert any(path in msg and "absent" in msg for msg in audit(source, built))
        (built / path).write_text('{"tampered":true}', "utf-8")
        assert any(path in msg and "transformé" in msg for msg in audit(source, built))
        (built / path).write_text('{"public":true}', "utf-8")

        unknown = "projets/projet-nova/data/new-private-report.json"
        target = source / unknown
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{"not-approved":true}', "utf-8")
        assert any(unknown in msg for msg in audit(source, None))
        target.unlink()
        target = built / unknown
        target.write_text('{"not-approved":true}', "utf-8")
        assert any(unknown in msg for msg in audit(source, built))
        target.unlink()

        private = sorted(INTERNAL_JSON)[-1]
        target = built / private
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{"internal":true}', "utf-8")
        assert any(private in msg for msg in audit(source, built))
        target.unlink()

        settings = source / "_config.yml"
        original = settings.read_text("utf-8")
        settings.write_text(original.replace(f'  - "{private}"\n', ""), "utf-8")
        assert any(private in msg and "non exclu" in msg for msg in audit(source, None))
        settings.write_text(original, "utf-8")
        assert not audit(source, built), audit(source, built)
    print("OK JSON: 50 publications connues, 28 données techniques exclues, "
          "pertes et transformations rejetées")


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
    errors = audit(Path(args.source).resolve(),
                   Path(args.built).resolve() if args.built else None)
    if errors:
        for error in errors:
            print("ERREUR: " + error, file=sys.stderr)
        return 1
    print("OK JSON: 50 fichiers publics vérifiés, 28 techniques exclus")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
