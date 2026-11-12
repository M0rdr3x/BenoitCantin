#!/usr/bin/env python3
"""P56B : comparer des millesimes publics sans creer de prevision fiscale Nova."""
from __future__ import annotations

import argparse
import copy
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

VERSION = "P56B-1"
SNAPSHOTS = {
    "BUDGET_INITIAL_REPRIS_DANS_COMPTES_PUBLICS": "PREVISION_BUDGET_INITIAL_RECLASSEE_DANS_ETATS_AUDITES",
    "PRELIMINAIRE_JUIN_2026": "RESULTAT_PRELIMINAIRE_NON_AUDITE",
    "COMPTES_AUDITES_JUILLET_2026": "RESULTAT_ANNUEL_COMPTES_PUBLICS_AUDITES",
}
SOURCES = {
    "COMPTES_PUBLICS_AUDITES_2025_2026": (
        "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/"
        "Comptes-publics/FR/CPTFR_vol1-2025-2026.pdf"
    ),
    "RAPPORT_PRELIMINAIRE_2025_2026": (
        "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/"
        "Rapports_situation_financiere/TRIMFR_SIFIN_4T_25-26.pdf"
    ),
}
FIELDS = (
    "revenus_totaux_mcad", "depenses_totales_mcad",
    "provision_eventualites_mcad", "solde_comptable_mcad",
    "versements_fonds_generations_mcad", "solde_leb_mcad",
    "ratio_dette_nette_pib_pct",
)
MONEY = re.compile(r"-?(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,3})?\Z")
RATIO = re.compile(r"(?:0|[1-9][0-9]{0,2})(?:\.[0-9]{1,2})?\Z")


def ensure(ok, reason):
    if not ok:
        raise ValueError(reason)


def decimal_value(raw, kind):
    ensure(type(raw) is str, "CHAINE_DECIMALE_REQUISE")
    ensure(bool((RATIO if kind == "ratio" else MONEY).fullmatch(raw)), "DECIMAL_INVALIDE")
    val = Decimal(raw)
    if kind == "ratio":
        ensure(val <= 100, "RATIO_PIB_HORS_BORNES")
    return val


def somme(d, k):
    v = d[k]
    return decimal_value(v, "ratio" if k.endswith("_pct") else "money") if v is not None else None


def compare(a, b, field):
    av, bv = somme(a, field), somme(b, field)
    ensure(av is not None and bv is not None, "COMPARAISON_AVEC_INCONNU")
    return str(bv - av)


def audit(d):
    ensure(isinstance(d, dict) and d.get("schema_version") == VERSION, "SCHEMA_INATTENDU")
    ensure(d.get("territoire") == "QUEBEC_DANS_CANADA", "REGIME_NON_COMPARABLE")
    ensure(d.get("exercice") == "2025-2026" and d.get("fin_exercice") == "2026-03-31", "EXERCICE_INATTENDU")
    ensure(d.get("unite_montants") == "M_CAD" and d.get("unite_ratio") == "POURCENT_PIB", "UNITE_INATTENDUE")
    ensure(d.get("decision") == "NO_GO_AUTOMATIQUE", "AUTORISATION_INATTENDUE")
    ensure(d.get("inconnues_p52b_conservees") == 600 and d.get("incidences_p52d_inconnues") == 720, "PREUVES_NOVA_NON_OBTENUES")
    ensure(d.get("score_p55n_estime") == 53, "REEVALUATION_NON_PROUVEE")
    for k in ("autorisation_publication_normative","validation_budget_nova","expertise_independante_nova"):
        ensure(d.get(k) is False, "CERTIFICATION_NOVA_NON_AUTORISEE")
    sources = d.get("sources")
    ensure(isinstance(sources, dict) and set(sources) == set(SOURCES), "SOURCES_INCOMPLETES")
    for k, url in SOURCES.items():
        source = sources[k]
        ensure(isinstance(source, dict) and source.get("url") == url, "SOURCE_NON_RECONNUE")
        ensure(source.get("pages_pdf_zero_index") and isinstance(source["pages_pdf_zero_index"], list),
               "PAGES_SOURCES_ABSENTES")
        ensure(all(type(p) is int and 0 <= p < 500 for p in source["pages_pdf_zero_index"]),
               "PAGE_SOURCE_INVALIDE")
    states = d.get("snapshots")
    ensure(isinstance(states, dict) and set(states) == set(SNAPSHOTS), "VERSIONS_INCOMPLETES")
    mapped = {}
    for name, etat in SNAPSHOTS.items():
        snapshot = states[name]
        ensure(isinstance(snapshot, dict) and snapshot.get("statut") == etat, "VERSION_NON_CONFORME")
        ensure(snapshot.get("exercice") == "2025-2026", "MILLÉSIME_NON_COMPARABLE")
        source_id = snapshot.get("source_id")
        expected_source = ("RAPPORT_PRELIMINAIRE_2025_2026" if name.startswith("PRELIMINAIRE")
                           else "COMPTES_PUBLICS_AUDITES_2025_2026")
        ensure(source_id == expected_source, "PROVENANCE_INATTENDUE")
        v = snapshot.get("donnees")
        pages = snapshot.get("pages_par_metrique")
        ensure(isinstance(v, dict) and set(v) == set(FIELDS), "POSTES_INCOMPLETS")
        ensure(isinstance(pages, dict) and set(pages) ==
               {k for k in FIELDS if v[k] is not None}, "TRACABILITE_PAGE_INCOMPLETE")
        for field in FIELDS:
            if v[field] is not None:
                somme(v, field)
                ensure(type(pages[field]) is int and
                       pages[field] in sources[source_id]["pages_pdf_zero_index"],
                       "PAGE_HORS_SOURCE")
        ensure(all(somme(v, k) is not None for k in (
            "revenus_totaux_mcad", "depenses_totales_mcad",
            "solde_comptable_mcad", "versements_fonds_generations_mcad",
            "solde_leb_mcad")), "COLONNES_ESSENTIELLES_MANQUANTES")
        # A provision is a budgetary forecast here, not a saving achieved.
        provision = somme(v, "provision_eventualites_mcad") or Decimal("0")
        ensure(somme(v, "revenus_totaux_mcad") - somme(v, "depenses_totales_mcad")
               - provision == somme(v, "solde_comptable_mcad"),
               "ECART_COMPTABLE_INTERNE")
        ensure(somme(v, "solde_comptable_mcad") +
               somme(v, "versements_fonds_generations_mcad") ==
               somme(v, "solde_leb_mcad"), "CONFUSION_SOLDE_LEB_ET_COMPTABLE")
        mapped[name] = v
    expected_provisions = {
        "BUDGET_INITIAL_REPRIS_DANS_COMPTES_PUBLICS": "2000",
        "PRELIMINAIRE_JUIN_2026": None,
        "COMPTES_AUDITES_JUILLET_2026": None,
    }
    for name, expected in expected_provisions.items():
        ensure(mapped[name]["provision_eventualites_mcad"] == expected,
               "PROVISION_TRANSPOSEE")
    budget = mapped["BUDGET_INITIAL_REPRIS_DANS_COMPTES_PUBLICS"]
    prelim = mapped["PRELIMINAIRE_JUIN_2026"]
    audited = mapped["COMPTES_AUDITES_JUILLET_2026"]
    return {
        "jalon": "P56B", "schema_version": VERSION,
        "exercice_compare": "2025-2026", "regime": "QUEBEC_DANS_CANADA",
        "statut": "CONTRÔLE_ARITHMETIQUE_PUBLIC_NON_AUDIT_NOVA",
        "nombre_snapshots": len(mapped), "sources_officielles_distinctes": len(sources),
        "rapprochement_preliminaire_vers_audite_mcad": {
            "variation_revenus": compare(prelim, audited, "revenus_totaux_mcad"),
            "variation_depenses": compare(prelim, audited, "depenses_totales_mcad"),
            "variation_solde_comptable": compare(prelim, audited, "solde_comptable_mcad"),
            "variation_solde_leb": compare(prelim, audited, "solde_leb_mcad"),
        },
        "rapprochement_budget_initial_vers_audite_mcad": {
            "variation_revenus": compare(budget, audited, "revenus_totaux_mcad"),
            "variation_depenses": compare(budget, audited, "depenses_totales_mcad"),
            "variation_solde_comptable": compare(budget, audited, "solde_comptable_mcad"),
            "variation_solde_leb": compare(budget, audited, "solde_leb_mcad"),
        },
        "variation_ratio_dette_nette_pib_points": compare(
            prelim, audited, "ratio_dette_nette_pib_pct"),
        "donnees_auditees_references_mcad": {
            "revenus_totaux": audited["revenus_totaux_mcad"],
            "depenses_totales": audited["depenses_totales_mcad"],
            "solde_comptable": audited["solde_comptable_mcad"],
            "versements_fonds_generations": audited["versements_fonds_generations_mcad"],
            "solde_budgetaire_leb": audited["solde_leb_mcad"],
        },
        "preliminaire_n_est_pas_audite": True,
        "revisions_comptables_ne_sont_pas_des_economies_nova": True,
        "transposition_automatique_aux_exercices_2027_2036": False,
        "budget_nova_certifie": False, "bilan_2027_2036_renseigne": False,
        "inconnues_p52b_conservees": 600, "incidences_p52d_inconnues": 720,
        "score_p55n_estime": 53,
        "certification_independante_nova": False,
        "decision": "NO_GO_AUTOMATIQUE",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--entree", type=Path, required=True)
    p.add_argument("--rapport", type=Path)
    p.add_argument("--exiger-budget-certifie", action="store_true")
    a = p.parse_args(argv)
    if a.exiger_budget_certifie:
        print("NO_GO_AUTOMATIQUE: aucun budget Nova certifié", file=sys.stderr)
        return 3
    try:
        data = json.loads(a.entree.read_text(encoding="utf-8"))
        result = json.dumps(audit(data), ensure_ascii=False, indent=2) + "\n"
        if a.rapport:
            with a.rapport.open("x", encoding="utf-8") as out:
                out.write(result)
        else:
            print(result, end="")
        return 0
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError) as e:
        print("REFUS: " + str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
