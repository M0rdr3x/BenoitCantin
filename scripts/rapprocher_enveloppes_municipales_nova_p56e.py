#!/usr/bin/env python3
"""P56E: rapprochement prudent des enveloppes municipales 2027; pas de transfert comptable."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

VERSION = "P56E-1"
OFFICIAL_URL = ("https://www.quebec.ca/gouvernement/gestion-municipale/"
                "finances-fiscalite-municipales/information-financiere/preparation-budget")
REPORT_URL = ("https://www.quebec.ca/gouvernement/gestion-municipale/"
              "finances-fiscalite-municipales/information-financiere/"
              "publications-financieres/rapport-financier")
SOMMAIRE_URL = ("https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/"
                "affaires-municipales/publications/finances_indicateurs_fiscalite/"
                "information_financiere/SOM_transferts_fiscaux.pdf")
PROGRAMS = {
    "CROISSANCE_PARTIE_TVQ": ("821.0", "MUNICIPALITES_ADMISSIBLES",
                             "PAYE_AU_PLUS_TARD_31_MAI"),
    "COMPENSATION_TERRES_PUBLIQUES": ("25.8", "MUNICIPALITES_AVEC_TERRES_PUBLIQUES",
                                    "PAYE_AU_PLUS_TARD_30_JUIN"),
    "PARTAGE_REDEVANCES_RESSOURCES": ("38.0", "MRC_ADMISSIBLES",
                                   "PAYE_AU_PLUS_TARD_30_JUIN"),
    "PEREQUATION_MUNICIPALE": ("67.0", "MUNICIPALITES_FAIBLE_POTENTIEL_FISCAL",
                             "PAYE_AU_PLUS_TARD_30_JUIN")
}
DECIMAL = re.compile(r"(?:0|[1-9][0-9]{0,6})(?:\.[0-9]{1,3})?\Z")
NULL_FIELDS = (
    "montants_versements_reels_mcad",
    "depense_provinciale_reconciliee_mcad",
    "recette_municipale_reconciliee_mcad",
    "identifiant_etat_provincial",
    "identifiant_beneficiaire_municipal",
    "preuve_de_contrepartie",
    "annee_debut_exercice_budget_p52b",
    "economie_nova_certifiee_mcad",
)


def check(ok, error):
    if not ok:
        raise ValueError(error)


def number(raw):
    check(type(raw) is str and DECIMAL.fullmatch(raw), "DECIMAL_MONETAIRE_ATTENDU")
    return Decimal(raw)


def auditer(data):
    check(isinstance(data, dict) and data.get("schema_version") == VERSION,
          "SCHEMA_INATTENDU")
    check(data.get("territoire") == "QUEBEC_DANS_CANADA" and
          data.get("unite") == "M_CAD", "TERRITOIRE_OU_UNITE_INVALIDE")
    check(data.get("decision") == "NO_GO_AUTOMATIQUE" and
          data.get("programme_fiscal_adopte") is False and
          data.get("expertise_independante_nova") is False, "CERTIFICATION_INVENTEE")
    check(data.get("p52b_inconnues_restantes") == 600 and
          data.get("p52d_incidences_inconnues") == 720 and
          data.get("score_p55n_estimatif") == 53, "SCORE_OU_PREUVE_INVENTE")
    check(data.get("recettes_projet_nova_certifiees_mcad") is None and
          data.get("economies_projet_nova_certifiees_mcad") is None, "GAIN_NOVA_INVENTE")
    s = data.get("source_previsions")
    check(isinstance(s, dict) and s.get("id") == "PREPARATION_BUDGET_MUNICIPAL_2027"
          and s.get("url") == OFFICIAL_URL and
          s.get("type") == "ENVELOPPES_BUDGETAIRES_ESTIMEES" and
          s.get("annee_civile") == 2027 and
          s.get("derniere_mise_a_jour") == "2026-10-26" and
          s.get("modification_versements_possible") is True, "SOURCE_PREVISIONS_NON_CONFORME")
    r = data.get("source_rapports_municipaux")
    check(isinstance(r, dict) and r.get("url") == REPORT_URL and
          r.get("rapports_individuels_authentifies_pour_contreparties") == 0 and
          r.get("mise_a_jour_quotidienne_donnees_ouvertes") is True,
          "RAPPORTS_MUNICIPAUX_NON_RAPPROCHES")
    som = data.get("source_sommaire_2025")
    check(isinstance(som, dict) and som.get("url") == SOMMAIRE_URL and
          som.get("annee_annoncée_site") == 2025 and
          som.get("controle_version") ==
          "DIVERGENCE_EXTRACTION_TEXTE_2025_ET_RENDU_IMAGE_2024_OBSERVEE" and
          som.get("montants_importables") is None and
          som.get("date_et_empreinte_binaire_originale_verifiees") is False and
          som.get("decision") == "BLOQUE_JUSQU_A_VERIFICATION_SOURCE_ORIGINALE",
          "SOMMAIRE_2025_VERSION_NON_CONTROLEE")
    rows = data.get("programmes")
    check(isinstance(rows, list) and len(rows) == len(PROGRAMS),
          "QUATRE_PROGRAMMES_OBLIGATOIRES")
    seen = set()
    total = Decimal("0")
    for x in rows:
        check(isinstance(x, dict), "PROGRAMME_MAL_FORME")
        ident = x.get("id")
        check(type(ident) is str and ident in PROGRAMS and ident not in seen,
              "PROGRAMME_DUPLIQUE_OU_INCONNU")
        seen.add(ident)
        amount, population, schedule = PROGRAMS[ident]
        check(x.get("enveloppe_prevue_mcad") == amount and
              number(x["enveloppe_prevue_mcad"]) == Decimal(amount),
              "MONTANT_OFFICIEL_PREVISIONNEL_MODIFIE")
        check(x.get("admissibilite") == population and
              x.get("modalite_versement") == schedule, "BENEFICIAIRE_OU_CALENDRIER_INVALIDE")
        check(x.get("source_id") == s["id"] and
              type(x.get("annee_civile")) is int and x["annee_civile"] == 2027 and
              x.get("statut") == "ENVELOPPE_PREVISIONNELLE_2027_NON_VERSEMENT_CONSTATE",
              "OBSERVATION_NON_COMPARABLE")
        check(all(field in x and x[field] is None for field in NULL_FIELDS),
              "UNE_PREVISION_N_EST_PAS_UN_VERSEMENT")
        check(x.get("imputation_p52b_autorisee") is False,
              "IMPORTATION_DECENNALE_NON_AUTORISEE")
        check(type(x.get("intitule")) is str and len(x["intitule"]) > 15,
              "INTITULE_SOURCE_OBLIGATOIRE")
        total += number(amount)
    check(seen == set(PROGRAMS), "COUVERTURE_PROGRAMME_INCOMPLETE")
    check(total == number(data.get("somme_quatre_enveloppes_mcad")) ==
          Decimal("951.8"), "SOMME_ENVELOPPES_INCOHERENTE")
    check(data.get("somme_est_sous_ensemble_et_non_total_tous_transferts") is True,
          "FAUX_TOTAL_TRANSFERTS")
    tvq = data.get("ventilation_tvq_2027")
    check(isinstance(tvq, dict) and tvq.get("enveloppe_cad_millions") == "821.0"
          and tvq.get("volet_i_pourcent") == "93.5"
          and tvq.get("volet_ii_pourcent") == "6.5"
          and tvq.get("montants_par_municipalite_verifies") is False and
          tvq.get("nature") == "PARTS_PREVISIONNELLES_PUBLIEES_2027",
          "PARTS_TVQ_INCOMPARABLES")
    first = number(tvq["enveloppe_cad_millions"]) * number(tvq["volet_i_pourcent"]) / Decimal("100")
    second = number(tvq["enveloppe_cad_millions"]) * number(tvq["volet_ii_pourcent"]) / Decimal("100")
    check(first + second == Decimal("821.0"), "VENTILATION_TVQ_NON_EXHAUSTIVE")
    para = data.get("compensations_immeubles_parapublics_2027")
    check(isinstance(para, dict) and
          para.get("statut") == "MONTANTS_INDIVIDUELS_PAS_ENCORE_CALCULABLES_SUR_PAGE"
          and para.get("enveloppe_mcad") is None and
          para.get("statut_reconcilie") is False,
          "COMPENSATIONS_PARAPUBLIQUES_INVENTEES")
    mapping = data.get("methode_raccord")
    check(isinstance(mapping, dict) and mapping.get("difference_calendrier") ==
          "ANNEE_CIVILE_2027_NE_VAUT_PAS_EXERCICE_PROVINCIAL_2027_2028"
          and mapping.get("elimination") ==
          "SEULEMENT_SI_DEUX_CONTREPARTIES_DANS_LE_MEME_PERIMETRE_CONSOLIDE"
          and mapping.get("caisse_vs_droits") ==
          "ENVELOPPE_BUDGETEE_NE_PROUVE_PAS_UN_VERSEMENT_OU_UN_DROIT_CONSTATE",
          "CONVENTION_DE_RAPPROCHEMENT_ABSENTE")
    return {
        "jalon": "P56E", "schema_version": VERSION,
        "statut": "RAPPROCHEMENT_DE_SOURCES_PREVISIONNELLES_SANS_CONTREPARTIES",
        "decision": "NO_GO_AUTOMATIQUE",
        "annee_civile_previsions": 2027,
        "nombre_programmes_budgetaires_identifies": len(rows),
        "sous_total_quatre_enveloppes_previsionnelles_mcad": str(total),
        "sous_total_represente_total_transferts_publics": False,
        "tvq_volet_i_calcul_illustratif_mcad": str(first),
        "tvq_volet_ii_calcul_illustratif_mcad": str(second),
        "subventions_reelles_2027_versees_mcad": None,
        "rapprochement_depense_province_recette_municipale": False,
        "sommaire_historique_2025_valide": False,
        "source_2025_version_a_reverifier": True,
        "fonds_municipaux_et_services_proteges": True,
        "economie_obtenue_nova_mcad": None,
        "projections_2027_2036_modifiees": False,
        "inconnues_budget_p52b": 600,
        "inconnues_incidence_p52d": 720,
        "score_p55n_estimatif": 53,
        "expertise_independante": False,
        "budget_nova_certifie": False
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registre", type=Path, required=True)
    p.add_argument("--rapport", type=Path)
    p.add_argument("--exiger-certification", action="store_true")
    a = p.parse_args(argv)
    if a.exiger_certification:
        print("NO_GO_AUTOMATIQUE: contreparties municipales non authentifiées", file=sys.stderr)
        return 3
    try:
        d = json.loads(a.registre.read_text(encoding="utf-8"))
        result = json.dumps(auditer(d), ensure_ascii=False, indent=2) + "\n"
        if a.rapport is None:
            print(result, end="")
        else:
            with a.rapport.open("x", encoding="utf-8") as f:
                f.write(result)
        return 0
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as e:
        print("REFUS: " + str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
