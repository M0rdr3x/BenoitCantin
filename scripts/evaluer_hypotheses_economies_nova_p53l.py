#!/usr/bin/env python3
"""P53L: analyser des hypotheses de dépenses publiques, jamais certifier des économies."""
import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys

import preparer_controles_probatoires_nova_p53k as p53k

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "projets" / "projet-nova" / "etudes"
REGLES = D / "P53L_CADRE_EVALUATION_ECONOMIES.json"
MONTANTS = (
    "cout_annuel_reference_cad", "cout_annuel_projection_cad",
    "cout_recurrent_additionnel_cad", "cout_initial_transition_cad",
    "cout_transfere_citoyens_cad", "cout_transfere_entreprises_cad",
    "cout_transfere_autres_organismes_cad",
)
PROTECTIONS = (
    "emplois_maintenus", "heures_contractuelles_maintenues",
    "salaires_et_conditions_maintenus", "qualite_service_maintenue",
    "delais_service_non_degrades", "acces_humain_maintenu",
    "services_essentiels_continus", "droits_et_recours_maintenus",
)
IDENTIFIANT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,80}\Z")
MONTANT = re.compile(r"(0|[1-9][0-9]*)(\.[0-9]{1,2})?\Z")
STATUTS = {"OUI", "NON", "INCONNU"}
NO_GO = "NO_GO_AUTOMATIQUE"

def exiger(ok, message):
    if not ok:
        raise ValueError(message)

def lire_json(path, limite=40000):
    p = Path(path)
    exiger(p.is_file() and not p.is_symlink() and 0 < p.stat().st_size <= limite,
           "FICHIER_SOURCE_INVALIDE")
    data = json.loads(p.read_text(encoding="utf-8"))
    exiger(type(data) is dict, "OBJET_JSON_ATTENDU")
    return data

def ouvrir_sources():
    # Relire les sources et verrous P53J/P53K avant toute analyse ultérieure.
    rows, p53h, k = p53k.sources()
    registre = p53k.file_dossiers(rows, p53h)
    exiger(len(registre) == 26 and k["premier_etat_de_preuves"]
           ["decision"] == NO_GO and
           k["premier_etat_de_preuves"]["revisions_independantes_signees"] == 0 and
           k["premier_etat_de_preuves"]["montants_Nova_inconnus"] == 1320,
           "PROVENANCE_P53K_INCOHERENTE")
    rules = lire_json(REGLES)
    exiger(rules["schema_version"] == "P53L-1" and
           rules["statut"] == "GRILLE_CANDIDATE_SANS_ECONOMIES_VALIDEES" and
           rules["reference_comptable"] == 2024 and
           rules["annee_projection_de_travail"] == 2027 and
           len(rules["categories"]) == 6 and
           len(set(rules["categories"])) == 6 and
           rules["montants_obligatoires"] == list(MONTANTS) and
           rules["protections_obligatoires"] == list(PROTECTIONS) and
           all(v is True for v in rules["verrous"].values()) and
           set(rules["verrous"]) == {
               "aucun_montant_suppose", "non_confusion_elimination_comptable",
               "aucune_suppression_emplois", "aucun_transfert_frais",
               "services_essentiels_proteges", "pas_de_certification_automatique",
               "controle_non_double_compte", "pas_de_publication_de_microdonnees",
               "aucun_taux_nova_adopte", "aucun_financement_budgetaire_presume",
           }, "REGLES_P53L_INCOHERENTES")
    return rules, len(rows), len(registre)

def argent_ou_inconnu(v):
    if v is None:
        return None
    exiger(type(v) is str and bool(MONTANT.fullmatch(v)),
           "MONTANT_CAD_NON_NEGATIF_OU_NULL_EXIGE")
    try:
        return Decimal(v)
    except InvalidOperation as exc:
        raise ValueError("MONTANT_INVALIDE") from exc

def ident(v):
    exiger(type(v) is str and bool(IDENTIFIANT.fullmatch(v)),
           "IDENTIFIANT_OU_PERIMETRE_INVALIDE")
    return v

def catalogue(rules):
    return {
        "schema_version": "P53L-CATALOGUE-1",
        "statut": "PISTES_NON_DOCUMENTEES_NON_FINANCEES",
        "pistes": [
            {"categorie": name, "montants_constates_cad": None,
             "effectif_a_proteger": True, "service_a_preserver": True,
             "economies_certifiees_cad": None}
            for name in rules["categories"]
        ],
    }

def evaluer(m, rules):
    """Calcul hypothétique interne; aucun résultat de cette fonction n'est une preuve."""
    exiger(type(m) is dict and m.get("schema_version") == "P53L-MESURE-1",
           "SCHEMA_MESURE_INVALIDE")
    ident(m.get("identifiant_mesure"))
    exiger(m.get("categorie") in rules["categories"], "CATEGORIE_HORS_CADRE")
    exiger(m.get("annee_reference") == 2024 and
           m.get("annee_projection") == 2027 and
           m.get("prix_constants") == "CAD_CONSTANTS_2024" and
           m.get("mois_comparables") == 12,
           "PERIODES_OU_UNITE_DE_PRIX_INCOMPARABLES")
    exiger(ident(m.get("perimetre_reference")) ==
           ident(m.get("perimetre_projection")), "PERIMETRE_NON_COMPARABLE")
    ident(m.get("poste_budgetaire"))
    exiger(m.get("origine") in ("HYPOTHESE", "DECLARATION_NON_AUTHENTIFIEE"),
           "SOURCE_REELLE_NON_AUTHENTIFIEE_INTERDITE")
    exiger(m.get("type_flux") in (
        "DEPENSE_FONCTIONNEMENT", "ELIMINATION_COMPTABLE",
        "TRANSFERT_INTERORGANISMES"), "TYPE_FLUX_INCONNU")
    montants = m.get("montants")
    exiger(type(montants) is dict and set(montants) == set(MONTANTS),
           "STRUCTURE_MONTANTS_INCOMPLETE")
    valeurs = {key: argent_ou_inconnu(montants[key]) for key in MONTANTS}
    protections = m.get("protections")
    exiger(type(protections) is dict and set(protections) == set(PROTECTIONS)
           and all(x in STATUTS for x in protections.values()),
           "PROTECTIONS_NON_DOCUMENTEES_OU_NON_VALIDES")
    # Le calcul ne doit pas masquer les échecs sociaux même si les coûts manquent.
    if any(v == "NON" for v in protections.values()):
        return "GARANTIE_SOCIALE_OU_SERVICE_VIOLEE", None
    if any(v == "INCONNU" for v in protections.values()):
        return "GARANTIE_SOCIALE_OU_SERVICE_INCONNUE", None
    if m["type_flux"] != "DEPENSE_FONCTIONNEMENT":
        return "SIMPLE_ECRITURE_OU_TRANSFERT_NON_ECONOMIE", None
    if any(v is None for v in valeurs.values()):
        return "COUT_COMPLET_INCONNU", None
    if any(valeurs[key] > 0 for key in (
        "cout_transfere_citoyens_cad", "cout_transfere_entreprises_cad",
        "cout_transfere_autres_organismes_cad")):
        return "TRANSFERT_DE_COUTS_INTERDIT", None
    # Première année : investissement initial imputé une fois, sans
    # l'amortir artificiellement sur une durée non vérifiée.
    diff = (valeurs["cout_annuel_reference_cad"] -
            valeurs["cout_annuel_projection_cad"])
    net_recurrent = (diff - valeurs["cout_recurrent_additionnel_cad"]
                     - valeurs["cout_transfere_citoyens_cad"]
                     - valeurs["cout_transfere_entreprises_cad"]
                     - valeurs["cout_transfere_autres_organismes_cad"])
    net_premier_exercice = net_recurrent - valeurs["cout_initial_transition_cad"]
    if net_recurrent <= 0:
        return "AUCUN_GAIN_RECURRENT_INDICATIF", (net_recurrent, net_premier_exercice)
    if net_premier_exercice <= 0:
        return "COUT_INITIAL_NON_COUVERT_PREMIER_EXERCICE", (net_recurrent, net_premier_exercice)
    return "HYPOTHESE_POSITIVE_NON_CERTIFIEE", (net_recurrent, net_premier_exercice)

def synthese(rules, source_count, register_count, etats):
    counts = dict(sorted(Counter(etats).items()))
    return {
        "schema_version": "P53L-RAPPORT-1", "exercice_source_mamh": 2024,
        "annee_projection_de_travail": 2027, "organismes_p53j": source_count,
        "dossiers_p53k": register_count, "pistes_non_documentees": len(rules["categories"]),
        "mesures_hypothetiques_controlees": len(etats),
        "statuts_declaratifs_agreges": counts,
        "economies_annuelles_certifiees_cad": None,
        "economies_premiere_annee_certifiees_cad": None,
        "couts_de_transfert_reels_certifies_cad": None,
        "postes_supprimes_autorises": 0,
        "qualite_services_degradee_autorisee": False,
        "suppression_recettes_publiques_autorisee": False,
        "champs_fiscaux_inconnus": 1320, "preuves_F01_F20_validees": 0,
        "taux_fiscaux_nova_adoptes": 0,
        "evaluation_independante_obtenue": False, "decision": NO_GO,
        "aucune_conclusion_financiere_derivee_de_scenarios": True,
    }

def ecrire_exclusif(path, texte):
    p = Path(path)
    exiger(not p.exists() and not p.is_symlink(),
           "REFUS_ECRASEMENT_D_UNE_SORTIE_EXISTANTE")
    with p.open("x", encoding="utf-8") as out:
        out.write(texte)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rapport")
    parser.add_argument("--catalogue")
    parser.add_argument("--mesure", action="append", default=[])
    parser.add_argument("--exiger-economies-certifiees", action="store_true")
    args = parser.parse_args(argv)
    try:
        exiger(len(args.mesure) <= 20, "TROP_DE_MESURES_NON_AUTHENTIFIEES")
        rules, orgs, dossiers = ouvrir_sources()
        etats = []
        ids = set()
        lignes = set()
        for path in args.mesure:
            mesure = lire_json(path)
            id_m = ident(mesure.get("identifiant_mesure"))
            exiger(id_m not in ids, "MESURE_EN_DOUBLE")
            ids.add(id_m)
            # Une seule mesure de la même ligne budgétaire et périmètre:
            # pas d'addition de scénarios qui se chevauchent.
            k = (ident(mesure.get("perimetre_reference")),
                 ident(mesure.get("poste_budgetaire")), mesure.get("annee_reference"))
            exiger(k not in lignes, "DOUBLON_POTENTIEL_DE_GAINS")
            lignes.add(k)
            etat, _ = evaluer(mesure, rules)
            etats.append(etat)
        report = synthese(rules, orgs, dossiers, etats)
        if args.rapport:
            ecrire_exclusif(args.rapport, json.dumps(report, ensure_ascii=False,
                        sort_keys=True, indent=2) + "\n")
        if args.catalogue:
            ecrire_exclusif(args.catalogue, json.dumps(catalogue(rules),
                        ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 3 if args.exiger_economies_certifiees else 0
    except (ValueError, OSError, KeyError, TypeError, UnicodeError,
            json.JSONDecodeError, InvalidOperation) as exc:
        print("P53L_REFUS: " + str(exc), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
