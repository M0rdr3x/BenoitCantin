#!/usr/bin/env python3
"""Projet Nova P52B — scénarios fiscaux conditionnels, sans taux inventés.

Toutes les entrées monétaires sont des chaînes décimales en milliards CAD,
et chaque montant connu doit posséder une référence de provenance.
Un champ null n'est jamais remplacé par zéro. La réussite du calcul ou de
la validation technique ne crée aucune autorisation de politique publique.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys

VERSION = "P52B-1"
REGIMES = ("QUEBEC_DANS_CANADA", "QUEBEC_SOUVERAIN")
TRAJECTOIRES = ("central", "prudent", "stress")
EXERCICES = tuple(range(2027, 2037))
RECETTES = (
    "impot_revenu_net",
    "anti_evasion_additionnelle_nette",
    "revenus_non_fiscaux_nets",
    "transferts_federaux_nets",
    "autres_prelevements_provinciaux_nets",
)
DEPENSES = (
    "services_existants_hors_dette_et_municipal_nets",
    "service_dette_net",
    "transferts_municipaux_nets",
    "fonctions_souveraines_nouvelles_nettes",
    "couts_transition_nets",
    "provision_crises_nette",
)
ALL = RECETTES + DEPENSES
DECIMAL_PATTERN = re.compile(r"^(0|[1-9][0-9]{0,5})(?:\.[0-9]{1,6})?$")
SIGNED_PATTERN = re.compile(r"^-?(0|[1-9][0-9]{0,5})(?:\.[0-9]{1,6})?$")
ZERO_PROVENANCE = "HYPOTHESE_PRUDENTE_ZERO_NON_CERTIFIEE"
REFERENCE_SHA = "9ed5f70cbe7022f25a679346a1288701f3b09067"


def decimal_gcad(raw, *, signed=False):
    # Reject booleans, floats, exponents, nonfinite numbers and ambiguity.
    if not isinstance(raw, str):
        raise ValueError("MONTANT_DOIT_ETRE_CHAINE_DECIMALE_OU_NULL")
    if not (SIGNED_PATTERN if signed else DECIMAL_PATTERN).fullmatch(raw):
        raise ValueError("MONTANT_DECIMAL_INVALIDE")
    try:
        result = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError("MONTANT_DECIMAL_INVALIDE") from exc
    if not result.is_finite():
        raise ValueError("MONTANT_NON_FINI")
    return result


def enforce(test, message):
    if not test:
        raise ValueError(message)


def validate_evidence_register(registry):
    enforce(isinstance(registry, dict), "REGISTRE_ABSENT")
    enforce(registry.get("control_id") == "P52A", "REGISTRE_HORS_PERIMETRE")
    enforce(registry.get("status") == "PROPOSITION_NON_ADOPTEE", "REGISTRE_STATUT_INATTENDU")
    enforce(registry.get("automatic_go") is False and
            registry.get("publication_authorized") is False,
            "REGISTRE_AUTORISATION_INTERDITE")
    evidence = registry.get("required_evidence")
    enforce(isinstance(evidence, list) and len(evidence) == 20,
            "VINGT_PREUVES_REQUISES")
    ids = [row.get("id") for row in evidence if isinstance(row, dict)]
    enforce(len(ids) == len(evidence) and len(set(ids)) == 20,
            "PREUVES_NON_UNIQUES")
    # Registered validations must be backed by new, independent, documented
    # reviews; this model currently allows no implicit promotion whatsoever.
    unresolved = sum(1 for row in evidence if row.get("statut") != "VALIDE")
    return unresolved


def validate_header(template):
    enforce(isinstance(template, dict), "TEMPLATE_NON_LISIBLE")
    enforce(template.get("schema_version") == VERSION, "SCHEMA_INATTENDU")
    enforce(template.get("statut") == "ETUDE_NON_ADOPTEE", "ETUDE_STATUT_INATTENDU")
    enforce(template.get("reference_main_sha") == REFERENCE_SHA,
            "SHA_REFERENCE_A_RECONCILIER")
    enforce(template.get("authorization") == {
        "legal": False, "publication": False, "fusion": False
    }, "AUTORISATION_INATTENDUE")
    enforce(template.get("unite") == "G_CAD", "UNITE_MONETAIRE_INATTENDUE")
    base = template.get("reference_2026_2027")
    enforce(isinstance(base, dict) and base.get("statut") == "MODELE_NON_CERTIFIE",
            "REFERENCE_NON_FIABLE")
    enforce(set(base) == {"statut", "revenus_consolides", "depenses_consolidees",
                          "service_dette_indicatif", "dette_nette_initiale"},
            "REFERENCE_CHAMPS_INATTENDUS")
    # Model reference only, not an official budgetary balance.
    for key in ("revenus_consolides", "depenses_consolidees",
                "service_dette_indicatif", "dette_nette_initiale"):
        decimal_gcad(base[key])
    enforce(set(template.get("regimes", {})) == set(REGIMES),
            "REGIMES_INCOMPLETS")
    return base


def verify_row(row, year):
    enforce(isinstance(row, dict) and set(row) == {
        "exercice_debut", "recettes", "depenses", "sources",
        "solde_budgetaire_precedent", "ratio_dette_nette_pib_pct",
        "perimetre_reconcilie", "incidence_menages_validee",
        "emplois_et_services_valides", "inventaire_prelevements_valide"
    }, "CHAMPS_ANNUELS_INATTENDUS")
    enforce(type(row["exercice_debut"]) is int and row["exercice_debut"] == year,
            "EXERCICE_INATTENDU")
    for group, names in (("recettes", RECETTES), ("depenses", DEPENSES)):
        enforce(isinstance(row[group], dict) and set(row[group]) == set(names),
                "ASSIETTES_INCOMPLETES_" + group)
    sources = row["sources"]
    enforce(isinstance(sources, dict) and set(sources).issubset(ALL),
            "SOURCES_INATTENDUES")
    enforce(all(type(row[k]) is bool for k in (
        "perimetre_reconcilie", "incidence_menages_validee",
        "emplois_et_services_valides", "inventaire_prelevements_valide"
    )), "ATTESTATIONS_INVALIDES")
    known, missing, totals = 0, 0, {}
    for group, fields in (("recettes", RECETTES), ("depenses", DEPENSES)):
        acc = Decimal(0)
        for name in fields:
            raw = row[group][name]
            if raw is None:
                enforce(name not in sources, "SOURCE_SANS_MONTANT_" + name)
                missing += 1
                continue
            value = decimal_gcad(raw)
            source = sources.get(name)
            enforce(isinstance(source, str) and 1 <= len(source) <= 150 and
                    not any(c in source for c in "\r\n<>"),
                    "PREUVE_SOURCE_REQUISE_" + name)
            if name == "anti_evasion_additionnelle_nette":
                enforce(value == 0 and source == ZERO_PROVENANCE,
                        "RECETTE_ANTI_EVASION_NON_CERTIFIEE_INTERDITE")
            known += 1
            acc += value
        totals[group] = acc
    prev = row["solde_budgetaire_precedent"]
    debt = row["ratio_dette_nette_pib_pct"]
    if prev is not None:
        prev = decimal_gcad(prev, signed=True)
    if debt is not None:
        debt = decimal_gcad(debt)
        enforce(debt <= 1000, "RATIO_DETTE_ABERRANT")
    financial_gate = bool(prev is not None and debt is not None and
                          prev >= 0 and debt <= Decimal(45))
    complete = missing == 0
    # Technical calculation is allowed for FULL inputs only. Never imply a
    # fully financed or authorized political reform from financial gate alone.
    solde = (totals["recettes"] - totals["depenses"]) if complete else None
    return {
        "exercice_debut": year,
        "champs_connus": known,
        "champs_manquants": missing,
        "solde_simule_gcad": str(solde) if solde is not None else None,
        "conditions_financieres_preliminaires_remplies": financial_gate,
        "integrite_de_la_couverture_declaree": all(row[k] is True for k in (
            "perimetre_reconcilie", "incidence_menages_validee",
            "emplois_et_services_valides", "inventaire_prelevements_valide")),
        "validation_independante_obtenue": False,
        "autorisation_de_baisse": False,
    }


def evaluate(template, registry):
    base = validate_header(template)
    pending_evidence = validate_evidence_register(registry)
    regimes = template["regimes"]
    summaries, total_missing = [], 0
    for regime in REGIMES:
        raw_regime = regimes[regime]
        enforce(isinstance(raw_regime, dict) and
                set(raw_regime) == {"trajectoires", "objectif_deux_prelevements"},
                "REGIME_NON_CONFORME")
        enforce(raw_regime["objectif_deux_prelevements"] == (
            "PROVINCIAL_SEULEMENT_FEDERAL_DEMEURE" if regime == REGIMES[0]
            else "CONDITIONNE_A_SOUVERAINETE_LEGALE"),
            "COMPETENCES_FISCALES_CONFONDUES")
        trajectories = raw_regime["trajectoires"]
        enforce(isinstance(trajectories, dict) and
                set(trajectories) == set(TRAJECTOIRES),
                "TROIS_TRAJECTOIRES_REQUISES")
        for scenario in TRAJECTOIRES:
            rows = trajectories[scenario]
            enforce(isinstance(rows, list) and len(rows) == len(EXERCICES),
                    "HORIZON_DECENNAL_INCOMPLET")
            checked = [verify_row(row, year) for row, year in zip(rows, EXERCICES)]
            missing = sum(x["champs_manquants"] for x in checked)
            total_missing += missing
            valid = (missing == 0 and pending_evidence == 0 and
                     all(x["integrite_de_la_couverture_declaree"] for x in checked))
            summaries.append({
                "regime": regime,
                "trajectoire": scenario,
                "annees": len(checked),
                "annees_calculables": sum(x["solde_simule_gcad"] is not None for x in checked),
                "entrees_manquantes": missing,
                "etat": "CALCUL_CONDITIONNEL_A_AUDITER" if valid else "NON_VALIDABLE",
                "soldes_gcad": [x["solde_simule_gcad"] for x in checked],
                "taux_fiscal_propose": None,
                "deux_taxes_sur_toute_economie_realisees": False,
                "validation_juridique": False,
                "decision": "NO_GO",
            })
    baseline_gap = decimal_gcad(base["revenus_consolides"]) - decimal_gcad(
        base["depenses_consolidees"])
    return {
        "jalon": "P52B",
        "source": VERSION,
        "reference_ecart_arithmetique_gcad": str(baseline_gap),
        "reference_ecart_non_assimilable_solde_budgetaire_officiel": True,
        "nombre_regimes": len(REGIMES),
        "nombre_trajectoires": len(summaries),
        "nombre_exercices": len(EXERCICES),
        "entrees_financieres_manquantes": total_missing,
        "preuves_P52A_encore_non_valides": pending_evidence,
        "resultats": summaries,
        "changement_legislatif": False,
        "taux_fiscal_adopte": False,
        "publication_autorisee": False,
        "decision": "NO_GO_AUTOMATIQUE",
        "limite": "Les chiffres sont des simulations conditionnelles, jamais des prévisions certifiées; finances municipales et taxes fédérales sont distinctes.",
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gabarit", type=Path, required=True)
    ap.add_argument("--registre", type=Path, required=True)
    ap.add_argument("--rapport", type=Path)
    ap.add_argument("--exiger-completude", action="store_true")
    args = ap.parse_args(argv)
    try:
        template = json.loads(args.gabarit.read_text(encoding="utf-8"))
        register = json.loads(args.registre.read_text(encoding="utf-8"))
        report = evaluate(template, register)
        exit_code = 3 if (args.exiger_completude and (
            report["entrees_financieres_manquantes"] or
            report["preuves_P52A_encore_non_valides"])) else 0
    except (OSError, UnicodeError, ValueError, TypeError, KeyError,
            InvalidOperation) as exc:
        report = {"jalon": "P52B", "decision": "NO_GO_AUTOMATIQUE",
                  "statut": "INVALIDE", "erreur_type": type(exc).__name__,
                  "publication_autorisee": False, "taux_fiscal_adopte": False}
        exit_code = 2
    body = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True, exist_ok=True)
        args.rapport.write_text(body, encoding="utf-8")
    else:
        print(body, end="")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
