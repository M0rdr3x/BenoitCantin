#!/usr/bin/env python3
"""P56J — analyser la perte mécanique de recettes avant un scénario fiscal à deux prélèvements.

Ne calcule AUCUN taux, ne simule pas de comportement et ne modifie pas P52B.
Les résultats sont des identités comptables historiques 2025-2026, et non des prévisions.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
import rapprocher_comptes_publics_p52b_nova_p56c as p56c
import rapprocher_versions_finances_nova_p56b as p56b
import evaluer_transition_fiscale_nova_p52b as p52b

VERSION = "P56J-1"
SOURCE_PATHS = {
    "P56C": "projets/projet-nova/etudes/P56C_TABLE_PASSAGE_COMPTES_PUBLICS_VERS_P52B_2025_2026.json",
    "P56B": "projets/projet-nova/etudes/P56B_SNAPSHOTS_FINANCES_2025_2026_SOURCES_OFFICIELLES.json",
    "P52A": "projets/projet-nova/etudes/P52A_FAISABILITE_FISCALE_DEUX_REGIMES.md"
}
GROUPS = {
    "IMPOTS_REVENU_EXISTANTS": (
        "impot_particuliers", "impots_societes"),
    "PRELEVEMENTS_EXISTANTS_A_REMPLACER_SI_ABOLIS": (
        "cotisations_services_sante", "impot_foncier_scolaire", "taxes_consommation"),
    "RECETTES_MIXTES_A_CLARIFIER": (
        "droits_permis_redevances", "revenus_divers", "revenus_entreprises_gouvernement"),
    "TRANSFERTS_FEDERAUX_DANS_CANADA": ("transferts_gouvernement_federal",)
}
EVIDENCE_IDS = {f"J{i:02d}" for i in range(1,18)}
AMOUNTS = {
    "IMPOTS_REVENU_EXISTANTS": "63568",
    "PRELEVEMENTS_EXISTANTS_A_REMPLACER_SI_ABOLIS": "40186",
    "RECETTES_MIXTES_A_CLARIFIER": "26871",
    "TRANSFERTS_FEDERAUX_DANS_CANADA": "29803",
}
EXPECTED_GATES = {
    "QUEBEC_DANS_CANADA": "TEST_DE_RETRAIT_COMPTABLE_HISTORIQUE_PROVINCIAL_SEULEMENT",
    "QUEBEC_SOUVERAIN": "NON_CHIFFRABLE_SANS_RECETTES_FEDERALES_ET_FONCTIONS_TRANSFEREES"
}

def check(ok, label):
    if not ok:
        raise ValueError(label)

def amount(raw):
    check(type(raw) is str and bool(re.fullmatch(r"(?:0|[1-9][0-9]{0,7})", raw)), "MONTANT_MCAD_INVALIDE")
    return Decimal(raw)

def audit(p56j, crosswalk, snapshots, model, evidence, barometer):
    check(isinstance(p56j,dict) and p56j.get("schema_version")==VERSION, "SCHEMA_INATTENDU")
    check(p56j.get("statut")=="ETUDE_CONTRAFACTUELLE_STATIQUE_NON_PREVISION" and
          p56j.get("objet")=="EXPOSITION_FISCALE_HISTORIQUE_AVANT_REFORME_A_DEUX_PRELEVEMENTS" and
          p56j.get("decision")=="NO_GO_AUTOMATIQUE" and
          p56j.get("territoire_reference")=="QUEBEC_DANS_CANADA" and
          p56j.get("exercice_historique")=="2025-2026" and
          p56j.get("unite")=="M_CAD","PERIMETRE_SOURCE_INVALIDE")
    references=p56j.get("sources_principales")
    check(isinstance(references,dict) and
          all(references.get(key)==path for key,path in SOURCE_PATHS.items()),
          "CHEMIN_SOURCE_CHANGE")
    source_officielle=references.get("COMPTES_OFFICIELS")
    check(isinstance(source_officielle,dict) and
          source_officielle.get("url")==p56b.SOURCES["COMPTES_PUBLICS_AUDITES_2025_2026"] and
          source_officielle.get("pages_pdf_indices_zero")==[11,18] and
          source_officielle.get("type")=="COMPTES_PUBLICS_ETATS_FINANCIERS_2025_2026",
          "SOURCE_OFFICIELLE_INCOHERENTE")
    fiscal=references.get("DEPENSES_FISCALES")
    check(isinstance(fiscal,dict) and
          fiscal.get("url")=="https://www.budget.finances.gouv.qc.ca/Budget/outils/depenses-fiscales/portrait-portrait.asp" and
          fiscal.get("type")=="ESTIMATION_DEPENSES_FISCALES_2025_PERIMETRE_DISTINCT" and
          fiscal.get("montant_ajoute_au_revenu_nova_mcad") is None,
          "DEPENSES_FISCALES_TRAITEES_A_TORT_COMME_GAIN")
    # Rentrer dans la chaîne des calculateurs antérieurs; pas de seconde base de vérité.
    earlier=p56c.verifier(crosswalk,snapshots,model,evidence)
    check(earlier["revenus_audites_mcad"]=="160428" and
          earlier["depenses_auditees_mcad"]=="165930" and
          earlier["solde_comptable_audite_mcad"]=="-5502" and
          earlier["montants_p52b_manquants"]==600,
          "REVENUS_OFFICIELS_OU_PROJECTIONS_MODIFIES")
    rows=crosswalk.get("poste_sources")
    check(isinstance(rows,list), "POSTES_SOURCES_MANQUANTS")
    values={r["id"]:amount(r["montant_audite_mcad"]) for r in rows}
    groups=p56j.get("groupes_de_repartition")
    check(isinstance(groups,list) and len(groups)==len(GROUPS), "GROUPES_FISCAUX_NON_EXHAUSTIFS")
    totals={}
    seen=set()
    allitems=set()
    for group in groups:
        check(isinstance(group,dict),"GROUPE_MAL_FORME")
        key=group.get("id")
        check(type(key) is str and key in GROUPS and key not in seen, "GROUPE_DUPLIQUE")
        seen.add(key)
        ids=group.get("postes_p56c")
        check(isinstance(ids,list) and tuple(ids)==GROUPS[key], "REPARTITION_INCORRECTE")
        check(not set(ids).intersection(allitems), "POSTE_DOUBLE_COMPTABILISE")
        allitems.update(ids)
        if key=="IMPOTS_REVENU_EXISTANTS":
            check(group.get("nature")=="RECETTES_HISTORIQUES_DU_SYSTEME_ACTUEL" and
                  group.get("reforme_adoptee") is False and
                  group.get("assiette_nouvelle_prouvee") is False,
                  "TAUX_OU_ASSIETTE_NOVA_NON_PROUVES")
        elif key=="PRELEVEMENTS_EXISTANTS_A_REMPLACER_SI_ABOLIS":
            check(group.get("nature")=="POSTES_SOUSTRAITS_DANS_TEST_MECANIQUE_SEULEMENT" and
                  group.get("reforme_adoptee") is False and
                  group.get("remplacement_valide") is False,
                  "ABOLITIONS_NON_AUTORISEES")
        elif key=="RECETTES_MIXTES_A_CLARIFIER":
            check(group.get("nature")=="RECETTES_MIXTES_ET_NON_FISCALES_SOUS_RESERVES" and
                  group.get("ventilation_complete") is False and
                  group.get("librement_disponible") is False,
                  "REVENUS_MIXTES_NON_PROUVES")
        else:
            check(group.get("nature")=="RECETTES_HISTORIQUES_SOUS_COMPETENCE_FEDERALE" and
                  group.get("maintien_en_souverainete_non_prouve") is True,
                  "TRANSFERTS_FEDERAUX_SOUVERAINS_INVENTES")
        totals[key]=sum((values[x] for x in ids), Decimal(0))
        check(str(totals[key])==AMOUNTS[key],"SOUS_TOTAL_SOURCE_NON_RECONCILIE")
    check(set(GROUPS)==seen and allitems=={x for x,v in values.items()
          if next(row for row in rows if row["id"]==x)["nature"]=="RECETTE"},
          "CLASSEMENT_PARTIEL_DES_RECETTES")
    revenues=sum(totals.values(),Decimal(0))
    expenses=Decimal(earlier["depenses_auditees_mcad"])
    check(revenues==Decimal("160428") and expenses==Decimal("165930"),
          "TOTAL_REVENUS_DEPENSES_FALSIFIE")
    base=revenues-expenses
    removed=totals["PRELEVEMENTS_EXISTANTS_A_REMPLACER_SI_ABOLIS"]
    counterfactual_revenues=revenues-removed
    counterfactual_balance=counterfactual_revenues-expenses
    check(base==Decimal("-5502") and counterfactual_balance==Decimal("-45688"),
          "SOLDE_ARITHMETIQUE_INVALIDE")
    counter=p56j.get("contre_factuel")
    check(isinstance(counter,dict) and
          counter.get("etat")=="ILLUSTRATION_STATIQUE_SANS_REACTIONS_COMPORTEMENTALES"
          and counter.get("annee_cible_p52b") is None and
          counter.get("supprime_effectivement_les_prelevements") is False and
          counter.get("pretend_que_ces_categories_sont_tous_prelevements_a_remplacer") is False
          and counter.get("services_et_depenses_constantes_dans_illustration") is True
          and counter.get("somme_des_postes_a_remplacer_prevision_validee") is False
          and counter.get("aucun_montant_depenses_supprime") is False
          and counter.get("recettes_nouveaux_prelevements_certifiees_mcad") is None
          and counter.get("revenus_anti_evasion_supposes_nets_mcad")=="0"
          and counter.get("base_de_calcul_taux_imposition_candidat") is None
          and counter.get("montant_reel_economie_certifiee_mcad") is None,
          "ILLUSTRATION_PAS_AUTORISATION")
    regimes=p56j.get("regimes")
    check(isinstance(regimes,dict) and set(regimes)==set(EXPECTED_GATES),
          "REGIMES_NON_COMPARABLES")
    a,b=regimes["QUEBEC_DANS_CANADA"],regimes["QUEBEC_SOUVERAIN"]
    check(a.get("scenario")==EXPECTED_GATES["QUEBEC_DANS_CANADA"] and
          a.get("federal_TPS_et_impot_demeurent") is True and
          a.get("libre_reforme_tous_prelevements") is False and
          a.get("deficit_2027_2036_prevu_mcad") is None and
          a.get("taux_propose") is None and a.get("decision")=="NO_GO",
          "COMPETENCES_PROVINCIALES_EXAGEREES")
    check(b.get("scenario")==EXPECTED_GATES["QUEBEC_SOUVERAIN"] and
          all(b.get(k) is None for k in (
              "montants_2025_2026_directement_transferables_mcad",
              "recettes_federales_reprises_mcad",
              "transferts_federaux_continues_mcad",
              "defense_frontieres_dette_pensions_couts_mcad",
              "solde_previsionnel_mcad","taux_propose")) and b.get("decision")=="NO_GO",
          "BUDGET_SOUVERAIN_INVENTE")
    prudent=p56j.get("conditions_prudence")
    check(isinstance(prudent,dict) and
          prudent.get("solde_budgetaire_annee_precedente_minimum_mcad")=="0" and
          prudent.get("ratio_dette_nette_pib_maximum_pourcent")=="45" and
          prudent.get("budget_precedent_nova_valide") is False and
          prudent.get("ratio_2027_2036_nova_valide") is False and
          prudent.get("autorisation_automatique") is False,
          "GARDE_FOUS_NON_RESPECTES")
    checklist=p56j.get("preuves_a_obtenir")
    check(isinstance(checklist,list) and len(checklist)==len(EVIDENCE_IDS) and
          p56j.get("nb_preuves_obligatoires")==len(EVIDENCE_IDS),
          "LISTE_ACCEPTATION_INCOMPLETE")
    check({x.get("id") for x in checklist if isinstance(x,dict)}==EVIDENCE_IDS and
          all(x.get("statut")=="NON_OBTENU" and x.get("preuve_url") is None and
              x.get("avis_independant") is None and x.get("montant_reconcilie_mcad") is None and
              len(x.get("preuve_attendue",""))>=60 for x in checklist),
          "PREUVES_FISCALES_NON_ATTESTEES")
    check(p56j.get("p52b_champs_monetaires_inconnus")==600 and
          p56j.get("p52d_incidences_inconnues")==720 and
          p56j.get("p52a_preuves_non_validees")==20 and
          p56j.get("p55n_score_estimatif")==53 and
          p56j.get("projections_p52b_alterees") is False and
          p56j.get("suppression_fiscale_adoptee") is False and
          p56j.get("economie_nova_certifiee_mcad") is None and
          p56j.get("avis_independant_nova") is False,
          "MATURITE_FICTIVE_OU_ECONOMIE_INVENTEE")
    check(isinstance(barometer,dict) and
          barometer.get("schema_version")=="P55N-1" and
          barometer.get("score_estimatif")==53 and
          barometer.get("score_evalue_sur")==100 and
          sum(x["points_estimes"] for x in barometer["axes"])==53 and
          sum(x["maximum"] for x in barometer["axes"])==100,
          "BAROMETRE_PRINCIPAL_NON_CONCORDE")
    return {
        "jalon":"P56J","schema_version":VERSION,
        "statut":"DIAGNOSTIC_MECANIQUE_HISTORIQUE_NON_PREVISION",
        "exercice_source":"2025-2026","regime_observe":"QUEBEC_DANS_CANADA",
        "groupes_historique_mcad":{k:str(totals[k]) for k in GROUPS},
        "revenus_consolides_constates_mcad":str(revenues),
        "depenses_consolidees_constatees_mcad":str(expenses),
        "deficit_comptable_constate_mcad":str(-base),
        "revenus_restants_si_trois_groupes_supprimes_mcad":str(counterfactual_revenues),
        "deficit_comptable_mecanique_sans_substitution_mcad":str(-counterfactual_balance),
        "recettes_a_remplacer_pour_revenir_au_niveau_historique_mcad":str(removed),
        "recettes_additionnelles_mecaniques_pour_equilibre_comptable_mcad":str(-counterfactual_balance),
        "deficit_comptable_initial_non_elimine_si_substitution_integrale_mcad":str(-base),
        "ces_sommes_ne_sont_pas_un_taux_fiscal":True,
        "ces_sommes_ne_sont_pas_un_budget_adopte":True,
        "ces_sommes_ne_sont_pas_un_budget_souverain":True,
        "compensation_federale_tps_impossible_unilateralement":True,
        "depenses_fiscales_estimees_non_ajoutees_comme_recettes":True,
        "anti_evasion_recouvrement_non_certifie_mcad":"0",
        "cellules_p52b_renseignees_2027_2036":0,
        "preuves_obligatoires_a_obtenir":len(checklist),
        "scenarios_souverains_financiers_chiffres":0,
        "incidence_sur_menages_et_entreprises_chiffree":False,
        "garantie_services_municipaux_sante_education_validee":False,
        "avis_independants_verifies":False,
        "p55n_score_estimatif_pourcent":53,
        "p55n_points_restants_estimes":47,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--diagnostic",required=True,type=Path)
    p.add_argument("--p56c",required=True,type=Path)
    p.add_argument("--p56b",required=True,type=Path)
    p.add_argument("--gabarit",required=True,type=Path)
    p.add_argument("--preuves",required=True,type=Path)
    p.add_argument("--barometre",required=True,type=Path)
    p.add_argument("--rapport",type=Path)
    p.add_argument("--exiger-taux-certifie",action="store_true")
    args=p.parse_args(argv)
    if args.exiger_taux_certifie:
        print("NO_GO_AUTOMATIQUE: assiette, charges et avis indépendants absents",file=sys.stderr)
        return 3
    try:
        def load(pth):
            return json.loads(pth.read_text(encoding="utf-8"))
        result=json.dumps(audit(
            load(args.diagnostic),load(args.p56c),load(args.p56b),
            load(args.gabarit),load(args.preuves),load(args.barometre)),
            ensure_ascii=False,indent=2)+"\n"
        if args.rapport:
            with args.rapport.open("x",encoding="utf-8") as out:
                out.write(result)
        else:
            print(result,end="")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,AssertionError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
