#!/usr/bin/env python3
"""P50K - Vérifie la structure du modèle public de pré-EFVP; ne délivre JAMAIS de GO."""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path
import sys

RISK_IDS = tuple(f"R{i:02d}" for i in range(1, 15))
VENDOR_IDS = tuple(f"V{i:02d}" for i in range(1, 13))
FLOWS = ("F01", "F02", "F03", "F04")
LOCKS = frozenset((
    "NO_GO_NON_LEVE_PAR_CI", "NE_PAS_FUSIONNER_PR_640",
    "AUCUNE_COLLECTE_POLITIQUE_NOUVELLE", "AUCUN_COFFRE_DEPLOYE",
    "AUCUNE_PREUVE_PRIVEE_GITHUB",
    "NON_CONFORMITE_NON_PRESUMEE_ET_CONFORMITE_NON_ATTESTEE",
))
FLOW_STATES = {
    "F01": "A_AUDITER",
    "F02": "NON_DEPLOYE",
    "F03": "DOCUMENTATION_SEULEMENT",
    "F04": "A_CARTOGRAPHIER",
}
REQUIRED_EVIDENCE = {
    "habilitation": "NON_FOURNIE", "regime_applicable": "NON_ETABLI",
    "cartographie_flux": "NON_VERIFIEE", "transferts_hors_quebec": "INCONNUS",
    "politique_conservation": "NON_VALIDEE", "plan_incident": "NON_VALIDE",
    "audit_courriel": "NON_REALISE",
}
HEADER = {
    "schema_version": "P50K-1.0",
    "nature": "MODELE_PUBLIC_NON_EFVP",
    "identite": "Projet Nova",
    "parti_futur": "Parti Nova",
    "qualification_juridique": "INDETERMINEE",
    "evaluation_efvp": "NON_REALISEE",
    "revision_juridique": "NON_ATTESTEE",
    "revision_confidentialite": "NON_ATTESTEE",
    "responsable_habilite": "NON_DESIGNE",
    "coffre": "NON_DEPLOYE",
    "courriel_existant": "CANAL_PUBLIC_AUDIT_NON_ATTESTE",
}
EXPECTED_ROOT = frozenset((*HEADER.keys(), "date_observation", "flux", "risques",
                           "prestataires", "domaines_preuves", "blocs", "decision", "note"))
CLOSED_DECISION = {
    "statut": "NO_GO", "efvp_signee": False, "prestataire_approuve": False,
    "publication_autorisee": False, "collecte_autorisee": False,
}

def inspect(value: object) -> dict:
    issues = []
    if not isinstance(value, dict):
        return {"statut_structure": "INVALIDE", "anomalies": ["RACINE_INVALIDE"],
                "decision": "NO_GO_AUTOMATIQUE", "efvp_reellement_realisee": False}
    if set(value) != EXPECTED_ROOT:
        issues.append("CHAMPS_INATTENDUS_OU_MANQUANTS")
    for key, expected in HEADER.items():
        if value.get(key) != expected:
            issues.append("VALEUR_INTERDITE_" + key.upper())
    try:
        date.fromisoformat(value["date_observation"])
    except (KeyError, TypeError, ValueError):
        issues.append("DATE_INVALIDE")
    if value.get("decision") != CLOSED_DECISION:
        issues.append("FAUSSE_DECISION")
    locks = value.get("blocs")
    if not isinstance(locks, list) or len(locks) != len(LOCKS) or set(locks) != LOCKS:
        issues.append("VERROUS_MODIFIES")
    if value.get("domaines_preuves") != REQUIRED_EVIDENCE:
        issues.append("PREUVES_FAUSSEMENT_ATTESTEES")
    flows = value.get("flux")
    if not isinstance(flows, list) or len(flows) != 4:
        issues.append("FLUX_INCOMPLETS")
    else:
        seen = set()
        for flow in flows:
            if not isinstance(flow, dict):
                issues.append("FLUX_INVALIDE"); continue
            code = flow.get("id")
            if code not in FLOW_STATES or code in seen:
                issues.append("FLUX_DOUBLE_OU_INCONNU"); continue
            seen.add(code)
            if (set(flow) != {"id", "nom", "statut", "traitements_reels_verifies"} or
                not isinstance(flow.get("nom"), str) or not flow["nom"] or
                flow.get("statut") != FLOW_STATES[code] or
                flow.get("traitements_reels_verifies") is not False):
                issues.append("FLUX_FAUSSEMENT_CERTIFIE_" + code)
        if seen != set(FLOW_STATES):
            issues.append("FLUX_INCOMPLETS")
    risks = value.get("risques")
    if not isinstance(risks, list) or len(risks) != len(RISK_IDS):
        issues.append("RISQUES_INCOMPLETS")
    else:
        seen = set()
        for risk in risks:
            if not isinstance(risk, dict):
                issues.append("RISQUE_INVALIDE"); continue
            code = risk.get("id")
            if code not in RISK_IDS or code in seen:
                issues.append("RISQUE_DOUBLE_OU_INCONNU"); continue
            seen.add(code)
            if (set(risk) != {"id", "intitule", "flux", "probabilite", "gravite",
                              "risque_residuel", "controle_effectif_atteste",
                              "preuve_publique", "avis_externe_atteste"} or
                not isinstance(risk.get("intitule"), str) or not risk["intitule"] or
                risk.get("flux") not in FLOWS or
                any(risk.get(field) != "INCONNU" for field in
                    ("probabilite", "gravite", "risque_residuel")) or
                risk.get("controle_effectif_atteste") is not False or
                risk.get("preuve_publique") != "" or
                risk.get("avis_externe_atteste") is not False):
                issues.append("RISQUE_FAUSSEMENT_EVALUE_" + code)
        if seen != set(RISK_IDS):
            issues.append("RISQUES_INCOMPLETS")
    vendor = value.get("prestataires")
    if not isinstance(vendor, dict):
        issues.append("PRESTATAIRES_INEXISTANTS")
    else:
        if set(vendor) != {
            "selection_effectuee", "nom_prestataire", "contrat_signe",
            "comparaison_commerciale_autorisee", "criteres"
        } or (vendor.get("selection_effectuee") is not False or
              vendor.get("nom_prestataire") != "" or
              vendor.get("contrat_signe") is not False or
              vendor.get("comparaison_commerciale_autorisee") is not False):
            issues.append("PRESTATAIRE_FAUSSEMENT_VALIDE")
        criteria = vendor.get("criteres")
        if not isinstance(criteria, list) or len(criteria) != len(VENDOR_IDS):
            issues.append("CRITERES_INCOMPLETS")
        else:
            seen = set()
            for item in criteria:
                if not isinstance(item, dict):
                    issues.append("CRITERE_INVALIDE"); continue
                code = item.get("id")
                if code not in VENDOR_IDS or code in seen:
                    issues.append("CRITERE_DOUBLE_OU_INCONNU"); continue
                seen.add(code)
                if (set(item) != {"id", "objet", "etat", "justificatif_externe_atteste"} or
                    not isinstance(item.get("objet"), str) or not item["objet"] or
                    item.get("etat") != "NON_EVALUE" or
                    item.get("justificatif_externe_atteste") is not False):
                    issues.append("CRITERE_FAUSSEMENT_VALIDE_" + code)
            if seen != set(VENDOR_IDS):
                issues.append("CRITERES_INCOMPLETS")
    return {
        "statut_structure": "MODELE_VALIDE_SANS_PREUVE" if not issues else "INVALIDE",
        "anomalies": sorted(set(issues)),
        "risques_documentes_comme_hypotheses": len(RISK_IDS),
        "criteres_eliminatoires_proposes": len(VENDOR_IDS),
        "preuves_reelles_authentifiees": 0,
        "efvp_reellement_realisee": False,
        "prestataire_reel_selectionne": False,
        "decision": "NO_GO_AUTOMATIQUE",
        "limite": "Sans accès aux flux réels ni preuve indépendante, un contrôle de schéma ne peut produire un GO.",
    }

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registre", type=Path, default=Path(__file__).resolve().parents[1] /
                        "projets/projet-nova/controles/P50K_REGISTRE_PUBLIC_PRE_EFVP.json")
    parser.add_argument("--rapport", type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect(json.loads(args.registre.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError):
        result = {"statut_structure": "INVALIDE", "anomalies": ["REGISTRE_ILLISIBLE"],
                  "decision": "NO_GO_AUTOMATIQUE", "efvp_reellement_realisee": False}
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True, exist_ok=True)
        args.rapport.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0 if result["statut_structure"] == "MODELE_VALIDE_SANS_PREUVE" else 2

if __name__ == "__main__":
    sys.exit(main())
