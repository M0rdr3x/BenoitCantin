#!/usr/bin/env python3
"""P50I — vérifie exclusivement la STRUCTURE d'un modèle public, sans autoriser quoi que ce soit."""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

IDS = tuple(f"Q{i:02d}" for i in range(1, 10))
ALLOWED_STATES = frozenset(("NON_DOCUMENTE", "A_REVOIR", "VERIFIE_HORS_DEPOT", "REJETE"))
REQUIRED_LOCKS = frozenset((
    "PR_640_NON_FUSIONNABLE",
    "AUCUN_FORMULAIRE_ACTIF_PAR_CE_JALON",
    "AUCUNE_COLLECTE_DE_SIGNATURES_PAR_CE_JALON",
    "AUCUNE_CONTRIBUTION_POLITIQUE_PAR_CE_JALON",
    "AUCUNE_AUTORISATION_JURIDIQUE_PAR_CE_JALON",
    "AUCUNE_DONNEE_PRIVEE_DANS_GIT",
))
SOURCES = frozenset(("EQ-AUTORISATION", "EQ-REPAQ", "LOI-E33", "CAI-PARTIS", "CAI-PRIVE", "CAI-HORS-QUEBEC"))
URL_HOSTS = frozenset(("www.electionsquebec.qc.ca", "www.legisquebec.gouv.qc.ca", "www.cai.gouv.qc.ca"))
EVIDENCE_REF = re.compile(r"^EV-[A-Z0-9-]{8,60}$")
SENSITIVE_KEYS = frozenset(("signature", "date_naissance", "adresse_domicile", "numero_carte_membre",
                            "numero_assurance_sociale", "courriel_personnel", "personne_nom_complet"))

def inspect(value: object) -> dict:
    issues = []
    if not isinstance(value, dict):
        return {"structure": "INVALIDE", "anomalies": ["RACINE_INVALIDE"], "decision": "NO_GO_AUTOMATIQUE",
                "preuves_authentifiees": 0}
    if value.get("schema_version") != "P50I-1.0":
        issues.append("VERSION_INVALIDE")
    if value.get("nature") != "MODELE_PUBLIC_SANS_PREUVE_PRIVEE":
        issues.append("NATURE_INVALIDE")
    for key, expect in (
        ("identite_courante", "Projet Nova"),
        ("future_identite_conditionnelle", "Parti Nova"),
        ("qualification_actuelle", "INDETERMINEE_NON_ATTESTEE"),
        ("autorisation_electorale", "NON_VERIFIEE"),
        ("reservation_nom", "NON_VERIFIEE"),
        ("collecte_formulaires", "SUSPENDUE"),
        ("financement_officiel", "NON_AUTORISE_PAR_CE_MODELE"),
    ):
        if value.get(key) != expect:
            issues.append("AFFIRMATION_INCOMPATIBLE_" + key.upper())
    if value.get("actes_autorises_par_ce_modele") != []:
        issues.append("ACTE_AUTORISE_INTERDIT")
    locks = value.get("verrous")
    if not isinstance(locks, list) or set(locks) != REQUIRED_LOCKS or len(locks) != len(REQUIRED_LOCKS):
        issues.append("VERROUS_INCOMPLETS")
    decision = value.get("decision")
    if (not isinstance(decision, dict) or decision.get("statut") != "NO_GO" or
        any(decision.get(k) is not False for k in
            ("habilitation_attestee", "avis_juridique_independant_atteste",
             "publication_autorisee", "collecte_sensible_autorisee"))):
        issues.append("DECISION_INCOMPATIBLE")
    scenarios = value.get("scenarios")
    if (not isinstance(scenarios, list) or len(scenarios) != 4 or
        {s.get("id") for s in scenarios if isinstance(s, dict)} !=
        {"PROJET", "ORGANISATION_PRIVEE", "PARTI_EN_PREPARATION", "PARTI_AUTORISE"} or
        any(not isinstance(s, dict) or s.get("fait_etabli") is not False for s in scenarios)):
        issues.append("SCENARIOS_NON_PROBANTS")
    sources = value.get("sources_officielles")
    if not isinstance(sources, list):
        issues.append("SOURCES_MANQUANTES")
    else:
        codes = []
        for item in sources:
            if not isinstance(item, dict):
                issues.append("SOURCE_INVALIDE")
                continue
            codes.append(item.get("id"))
            u = item.get("url")
            parsed = urlparse(u) if isinstance(u, str) else None
            if (not parsed or parsed.scheme != "https" or parsed.netloc not in URL_HOSTS
                or parsed.username or parsed.password):
                issues.append("URL_SOURCE_INVALIDE")
        if set(codes) != SOURCES or len(codes) != len(SOURCES):
            issues.append("SOURCES_NON_CONCORDANTES")
    preuves = value.get("preuves")
    seen = set()
    if not isinstance(preuves, list):
        issues.append("PREUVES_MANQUANTES")
        preuves = []
    for item in preuves:
        if not isinstance(item, dict):
            issues.append("ENTREE_INVALIDE")
            continue
        identifier = item.get("id")
        if identifier not in IDS or identifier in seen:
            issues.append("ID_INVALIDE_OU_DOUBLE")
            continue
        seen.add(identifier)
        state = item.get("statut")
        if state not in ALLOWED_STATES:
            issues.append("ETAT_INVALIDE_" + identifier)
        if item.get("pieces_sensibles_hors_depot") is not True:
            issues.append("CONFIDENTIALITE_INVALIDE_" + identifier)
        if not isinstance(item.get("responsabilite_cible"), str) or not item["responsabilite_cible"]:
            issues.append("RESPONSABLE_INVALIDE_" + identifier)
        if not isinstance(item.get("objet"), str) or not item["objet"]:
            issues.append("OBJET_MANQUANT_" + identifier)
        ref = item.get("reference_opaque")
        dat = item.get("date_verification")
        if state == "VERIFIE_HORS_DEPOT":
            if not isinstance(ref, str) or not EVIDENCE_REF.fullmatch(ref):
                issues.append("REFERENCE_NON_VALIDABLE_" + identifier)
            try:
                date.fromisoformat(dat)
            except (ValueError, TypeError):
                issues.append("DATE_INVALIDE_" + identifier)
        elif ref or dat:
            issues.append("PREUVE_SANS_STATUT_" + identifier)
    if seen != set(IDS):
        issues.append("NEUF_PREUVES_INCOMPLETES")
    # Reject personal-data-shaped keys ANYWHERE in the public template.
    def check_keys(obj):
        if isinstance(obj, dict):
            for k,v in obj.items():
                if k.lower() in SENSITIVE_KEYS:
                    issues.append("CHAMP_SENSIBLE_INTERDIT")
                check_keys(v)
        elif isinstance(obj, list):
            for element in obj:
                check_keys(element)
    check_keys(value)
    return {
        "structure": "VALIDE_MODELE_SEULEMENT" if not issues else "INVALIDE",
        "anomalies": sorted(set(issues)),
        "preuves_presentes": len(seen),
        "preuves_authentifiees": 0,
        "statut_legal_confirme": False,
        "habilitations_confirmees": False,
        "collecte_autorisee": False,
        "publication_autorisee": False,
        "decision": "NO_GO_AUTOMATIQUE",
        "limite": "Aucun controle des signatures, actes juridiques, REPAQ en temps reel, ni traitements de donnees."
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registre", type=Path, default=Path(__file__).resolve().parents[1] /
        "projets/projet-nova/controles/P50I_REGISTRE_PUBLIC_QUALIFICATION.json")
    parser.add_argument("--rapport", type=Path)
    args = parser.parse_args(argv)
    try:
        report = inspect(json.loads(args.registre.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError):
        report = {"structure": "INVALIDE", "anomalies": ["LECTURE_INVALIDE"],
                  "decision": "NO_GO_AUTOMATIQUE", "preuves_authentifiees": 0}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True, exist_ok=True)
        args.rapport.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if report["structure"] == "VALIDE_MODELE_SEULEMENT" else 2

if __name__ == "__main__":
    sys.exit(main())
