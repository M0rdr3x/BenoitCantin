#!/usr/bin/env python3
"""P50J: validate an EMPTY public evidence template; simulate future lifecycle rules.
No file upload, outbound network request, signature verification, authorization or deployment.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys

CODES = tuple(f"Q{i:02d}" for i in range(1, 10))
DESCRIPTIONS = (
    "Porteur et forme juridique",
    "Régime électoral applicable",
    "Nom et éventuelle réservation",
    "Mandats et désignations",
    "Financement et dépenses",
    "Renseignements personnels",
    "Sous-traitants et transferts",
    "Sécurité, conservation et incidents",
    "Mandat d'autorisation de publication",
)
STATES = frozenset((
    "NON_RECU", "RECU_ISOLE", "EN_VERIFICATION", "VERIFIE_HORS_DEPOT",
    "REJETE", "SUSPENDU", "EXPIRE", "REVOQUE",
))
TERMINAL = frozenset(("REJETE", "EXPIRE", "REVOQUE"))
LOCKS = frozenset((
    "AUCUNE_DONNEE_PERSONNELLE_DANS_GIT",
    "PR_640_NE_PAS_FUSIONNER",
    "AUCUN_GO_AUTOMATIQUE",
    "AUCUN_CANAL_DEPOT_REEL",
    "AUCUNE_COLLECTE_POLITIQUE",
))
FALSE_FIELDS = (
    "porteur_juridique_atteste", "autorisation_electorale_attestee",
    "eipd_ou_efvp_realisee_attestee", "coffre_prive_deploye",
    "formulaires_externes_actifs", "collecte_de_signatures_active",
    "collecte_de_contributions_active", "publication_autorisee",
)
ROOT_FIELDS = frozenset((
    "schema_version", "type", "date_revision", "identite_active",
    "identite_future_conditionnelle", *FALSE_FIELDS, "pieces_recues",
    "pieces_verifiees", "identifiants_de_pieces_publiques", "preuves", "verrous",
    "processus", "decision", "observation",
))
REQUIRED_GUARDS = {
    ("NON_RECU", "RECU_ISOLE"): (
        "canal_reel_autorise", "qualification_juridique_confirmee",
        "mandat_reception_verifie",
    ),
    ("RECU_ISOLE", "EN_VERIFICATION"): (
        "quarantaine_terminee", "verificateur_habilite",
    ),
    ("EN_VERIFICATION", "VERIFIE_HORS_DEPOT"): (
        "source_primaire_confirmee", "mandat_valide", "deux_revues_independantes",
        "absence_conflit", "non_expiree", "non_revoquee",
    ),
    ("EN_VERIFICATION", "REJETE"): ("motif_refus_documente",),
    ("RECU_ISOLE", "SUSPENDU"): ("anomalie_signalee",),
    ("EN_VERIFICATION", "SUSPENDU"): ("anomalie_signalee",),
    ("VERIFIE_HORS_DEPOT", "SUSPENDU"): ("anomalie_signalee",),
    ("EN_VERIFICATION", "EXPIRE"): ("date_limite_depassee",),
    ("VERIFIE_HORS_DEPOT", "EXPIRE"): ("date_limite_depassee",),
    ("EN_VERIFICATION", "REVOQUE"): ("revocation_confirmee",),
    ("VERIFIE_HORS_DEPOT", "REVOQUE"): ("revocation_confirmee",),
    ("SUSPENDU", "EN_VERIFICATION"): (
        "incident_resolu", "mandat_valide", "verificateur_habilite",
    ),
}


def inspect_public_template(document: object) -> dict:
    issues = []
    if not isinstance(document, dict):
        return {"structure": "INVALIDE", "problemes": ["MODELE_NON_OBJET"],
                "decision": "NO_GO_AUTOMATIQUE", "preuves_authentifiees": 0}
    if set(document) != ROOT_FIELDS:
        issues.append("CHAMPS_RACINE_NON_CONFORMES")
    if document.get("schema_version") != "P50J-1.0":
        issues.append("VERSION_INVALIDE")
    if document.get("type") != "MODELE_PUBLIC_VIDE":
        issues.append("TYPE_NON_PUBLIC")
    try:
        date.fromisoformat(document.get("date_revision", ""))
    except (TypeError, ValueError):
        issues.append("DATE_REVISION_INVALIDE")
    if document.get("identite_active") != "Projet Nova":
        issues.append("IDENTITE_INVALIDE")
    if document.get("identite_future_conditionnelle") != "Parti Nova":
        issues.append("IDENTITE_FUTURE_INVALIDE")
    if any(document.get(k) is not False for k in FALSE_FIELDS):
        issues.append("ACTIVATION_OU_ATTESTATION_INTERDITE")
    if type(document.get("pieces_recues")) is not int or document["pieces_recues"] != 0:
        issues.append("PIECES_DECLAREES_RECUES")
    if type(document.get("pieces_verifiees")) is not int or document["pieces_verifiees"] != 0:
        issues.append("PIECES_DECLAREES_VERIFIEES")
    if document.get("identifiants_de_pieces_publiques") != []:
        issues.append("REFERENCE_REELLE_OU_EXPOSEE")
    if document.get("decision") != "NO_GO":
        issues.append("DECISION_PUBLIQUE_NON_AUTORISEE")
    locks = document.get("verrous")
    if not isinstance(locks, list) or len(locks) != len(LOCKS) or set(locks) != LOCKS:
        issues.append("VERROUS_INCOMPLETS")
    process = document.get("processus")
    if not isinstance(process, dict) or process != {
        "etats": ["NON_RECU", "RECU_ISOLE", "EN_VERIFICATION",
                   "VERIFIE_HORS_DEPOT", "REJETE", "SUSPENDU", "EXPIRE", "REVOQUE"],
        "attestations_reelles": "HORS_DEPOT",
        "verification_double": "OBLIGATOIRE_AVANT_VALIDATION",
        "revalidation_apres_expiration": "NOUVELLE_REFERENCE",
    }:
        issues.append("MACHINE_ETATS_NON_CONFORME")
    evidence = document.get("preuves")
    if not isinstance(evidence, list) or len(evidence) != len(CODES):
        issues.append("FAMILLES_MANQUANTES")
    else:
        seen = set()
        for item in evidence:
            if not isinstance(item, dict):
                issues.append("PREUVE_NON_OBJET")
                continue
            key = item.get("code")
            if key in seen or key not in CODES:
                issues.append("CODE_DUPLIQUE_OU_INCONNU")
                continue
            seen.add(key)
            expected = {
                "code": key, "objet": DESCRIPTIONS[CODES.index(key)],
                "statut": "NON_RECU", "reference_privee": "",
                "piece_presente": False, "validite_attestee": False,
            }
            if item != expected:
                issues.append("PREUVE_PUBLIQUE_NON_VIDE_" + key)
        if seen != set(CODES):
            issues.append("FAMILLES_MANQUANTES")
    return {
        "structure": "VALIDE_MODELE_SEULEMENT" if not issues else "INVALIDE",
        "problemes": sorted(set(issues)),
        "familles_attendues": len(CODES),
        "preuves_authentifiees": 0,
        "canal_depot_actif": False,
        "deploiement_autorise": False,
        "decision": "NO_GO_AUTOMATIQUE",
        "note": "Contrôle local documentaire, sans vérification d'une preuve réelle.",
    }


def simulate_transition(before: str, after: str, assertions: object) -> dict:
    """Tests de conception uniquement; les assertions fournies ne sont jamais authentifiées."""
    failure = []
    if before not in STATES or after not in STATES:
        failure.append("ETAT_INCONNU")
    if before in TERMINAL:
        failure.append("ETAT_TERMINAL_NOUVELLE_REFERENCE")
    if before == after:
        failure.append("PAS_DE_TRANSITION")
    requirements = REQUIRED_GUARDS.get((before, after))
    if requirements is None:
        failure.append("TRANSITION_NON_PREVUE")
    if not isinstance(assertions, dict):
        failure.append("ATTESTATIONS_MAL_FORMEES")
    elif requirements and any(assertions.get(key) is not True for key in requirements):
        failure.append("GARANTIES_INSUFFISANTES")
    return {
        "transition_theorique": "AUTORISEE_SUR_DONNEES_FICTIVES" if not failure else "REFUSEE",
        "problemes": sorted(set(failure)),
        "preuve_authentifiee": False,
        "decision": "NO_GO_AUTOMATIQUE",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registre", type=Path, default=Path(__file__).resolve().parents[1] /
        "projets/projet-nova/controles/P50J_MODELE_PUBLIC_PREUVES.json")
    parser.add_argument("--rapport", type=Path)
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.registre.read_text(encoding="utf-8"))
        result = inspect_public_template(document)
    except (OSError, UnicodeError, json.JSONDecodeError):
        result = {"structure": "INVALIDE", "problemes": ["FICHIER_ABSENT_OU_JSON_INVALIDE"],
                  "decision": "NO_GO_AUTOMATIQUE", "preuves_authentifiees": 0}
    content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True, exist_ok=True)
        args.rapport.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0 if result["structure"] == "VALIDE_MODELE_SEULEMENT" else 2


if __name__ == "__main__":
    sys.exit(main())
