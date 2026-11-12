#!/usr/bin/env python3
"""P56S : trois options financières statiques, sans taux ou politique Nova adoptés.

Les fractions 0, 1/4, 1 sont des TESTS DE SENSIBILITÉ, pas un calendrier
de réforme. Pour le Québec souverain, les résultats restent indéterminés.
"""
from __future__ import annotations
import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys

YEARS=("2027-2028","2028-2029","2029-2030","2030-2031")
FUTURE=("2031-2032","2032-2033","2033-2034","2034-2035","2035-2036","2036-2037")
OPTIONS={
"S1_CONTINUITE":(0,"REFERENCE_OPERATIONNELLE_NON_ARCHITECTURE_FINALE"),
"S2_TRANSITION_CONDITIONNELLE":(1,"TEST_25_POURCENT_PUREMENT_ILLUSTRATIF_SANS_CALENDRIER_ADOPTE"),
"S3_CIBLE_DEUX_PRELEVEMENTS":(4,"TEST_100_POURCENT_PUREMENT_ILLUSTRATIF_NON_ADOPTE")
}
LINKS={
"p56r":"projets/projet-nova/etudes/P56R_INVENTAIRE_EXHAUSTIF_CATEGORIES_RECETTES_ET_PONT_FISCAL_2026_2031.json",
"p56q":"projets/projet-nova/etudes/P56Q_PONT_CONTREFACTUEL_RECETTES_2027_2031_SIMULATEUR_AMENDE.json",
"p56o":"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
"p55n":"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json",
"officiel":"https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf"
}
FIELDS_NULL=(
"recettes_nouvelles_impot_revenu_nova_reellement_demontrees_mcad",
"recettes_nouvelles_anti_paradis_reellement_demontrees_mcad",
"compensations_pertes_prestations_mcad",
"cout_transition_mcad",
"variation_revenu_disponible_menages_certifiee_mcad",
"cout_complet_services_et_protection_emplois_certifie_mcad")
CURRENCY=re.compile(r"-?(?:0|[1-9][0-9]{0,8})\.[0-9]{2}\Z")
INVARIANTS=(
"retrait_tout_ou_partie_des_trois_recettes_purement_theorique",
"budgets_services_inchanges_pour_mesure_risque",
"aucune_economie_administrative_presumee",
"aucune_recette_anti_paradis_presumee",
"assiette_impot_nova_inconnue",
"taux_nova_inconnu",
"revenus_et_depenses_hors_trois_postes_supposes_constants",
"effets_macroeconomiques_non_estimes",
"credits_et_prestations_des_menages_a_preserver",
"compensations_et_cout_transition_inconnus",
"revenus_federaux_inchanges_uniquement_dans_referentiel_provincial",
"gains_revenu_disponible_non_demontres",
"no_go_constitutionnel_et_financier",
"un_quart_pour_S2_est_sensibilite_pas_echeancier",
"autres_droits_et_redevances_non_supprimes_par_defaut")
def require(ok,error):
    if not ok:
        raise ValueError(error)
def read_decimal(value):
    require(type(value) is str and CURRENCY.fullmatch(value),
            "MONTANT_DEUX_DECIMALES_OBLIGATOIRE")
    try:
        return Decimal(value)
    except InvalidOperation as e:
        raise ValueError("MONTANT_NON_DECIMAL") from e
def money(n):
    return format(Decimal(n).quantize(Decimal("0.01")),".2f")

def valider(data,p56r,p56q,cloture,barometre):
    require(isinstance(data,dict) and data.get("schema_version")=="P56S-1" and
        data.get("date")=="2026-11-08" and
        data.get("statut")=="ARITHMETIQUE_EXPLORATOIRE_PAS_TAUX_NOVA_PAS_POLITIQUE_ADOPTEE" and
        data.get("decision")=="NO_GO_AUTOMATIQUE" and
        data.get("decision_finale")=="NO_GO_AUTOMATIQUE",
        "EN_TETE_P56S_NON_FIABLE")
    require(data.get("sources")==LINKS,
            "REFERENCES_SOURCES_MODIFIEES")
    p=data.get("perimetre")
    require(isinstance(p,dict) and
        p.get("annees_donnees")==list(YEARS) and
        p.get("annees_modeles_non_justifiees")==list(FUTURE) and
        p.get("regime_calcule")=="QUEBEC_DANS_CANADA_REFORME_PROVINCIALE" and
        p.get("regime_non_calcule")=="QUEBEC_SOUVERAIN_HYPOTHETIQUE" and
        p.get("unite")=="MILLIONS_CAD_ANNUELS" and
        p.get("assiette_retrait_exclusivement")==[
          "cotisations_services_sante","impot_foncier_scolaire","taxes_consommation"] and
        p.get("source_solde")=="SOLDE_BUDGETAIRE_AU_SENS_DE_LA_LOI_AVEC_FONDS_GENERATIONS",
        "FENETRE_OU_COMPETENCES_INCOMPATIBLES")
    assumptions=data.get("hypotheses_communes")
    require(isinstance(assumptions,dict) and
        set(assumptions)==set(INVARIANTS) and
        all(assumptions[k] is True for k in INVARIANTS),
        "HYPOTHESES_NON_DECLAREES")
    require(p56r.get("schema_version")=="P56R-1" and
        p56r.get("decision")=="NO_GO_AUTOMATIQUE" and
        p56q.get("schema_version")=="P56Q-1" and
        p56q.get("decision")=="NO_GO_AUTOMATIQUE" and
        cloture.get("schema_version")=="P56O-1" and
        cloture.get("definition_terminee",{}).get("etat_actuel_termine") is False and
        barometre.get("schema_version")=="P55N-1" and
        barometre.get("score_estimatif")==53,
        "P56Q_R_ET_BAROMETRE_NON_RECONCILIES")
    baseline={r["exercice"]:r for r in p56q["annees_reconciliees"]}
    byyear={r["exercice"]:r for r in p56r["rapprochement_annees"]}
    require(set(YEARS).issubset(baseline) and set(YEARS).issubset(byyear),
            "ANNEES_BUDGETAIRES_OFFICIELLES_MANQUANTES")
    records=data.get("options")
    require(isinstance(records,list) and len(records)==3 and
            {r.get("id") for r in records if isinstance(r,dict)}==set(OPTIONS),
            "TROIS_STRATEGIES_OBLIGATOIRES")
    out={}
    for opt in records:
        key=opt["id"]
        numerator,expectedstatus=OPTIONS[key]
        require(type(opt.get("numerateur")) is int and
                opt["numerateur"]==numerator and
                opt.get("denominateur")==4 and
                opt.get("statut")==expectedstatus and
                opt.get("unite_fraction")=="QUARTS_DES_TROIS_POSTES_SEULEMENT" and
                opt.get("nonAdoptee") is True and
                len(opt.get("criteres",""))>=90 and
                len(opt.get("title",""))>=35,
                "FRACTION_DE_STRATEGIE_NON_EXPLIQUEE")
        items=opt.get("resultats_par_exercice")
        require(isinstance(items,list) and
                [x.get("exercice") for x in items]==list(YEARS),
                "EXERCICES_OPTIONS_NON_COMPLETS")
        out[key]={}
        for item in items:
            fy=item["exercice"]
            q=baseline[fy]
            r=byyear[fy]
            at_risk=Decimal(q["trois_categories_risque_suppression_mcad"])
            require(at_risk==Decimal(r["trois_categories_a_remplacer_si_supprimees_mcad"]),
                    "MONTANT_A_REMPLACER_NON_RECONCILIE")
            original=Decimal(q["solde_budgetaire_initial_au_sens_de_la_loi_mcad"])
            mitigation=Decimal(q["ecart_gouvernemental_a_resorber_mcad"])
            loss=at_risk*Decimal(numerator)/Decimal(4)
            fields={
                "exposition_officielle_trois_postes_mcad":at_risk,
                "solde_loi_reference_avec_mesures_a_resorber_mcad":original,
                "ecart_a_resorber_non_garanti_mcad":mitigation,
                "recettes_retirees_uniquement_dans_le_test_mcad":loss,
                "besoins_remplacement_recettes_pour_solde_initial_inchange_mcad":loss,
                "solde_loi_sans_nouveau_financement_si_retrait_test_mcad":original-loss,
                "solde_loi_sans_nouveau_financement_et_sans_resorption_mcad":original-loss-mitigation,
                "ressources_additionnelles_pour_solde_loi_zero_avec_ecart_mcad":max(Decimal(0),loss-original),
                "ressources_additionnelles_pour_solde_loi_zero_sans_resorption_mcad":max(Decimal(0),loss-original+mitigation)}
            for name,expected in fields.items():
                require(read_decimal(item.get(name))==expected,
                        "CALCUL_ERRONE_"+key+"_"+fy+"_"+name)
            require(all(item.get(name) is None for name in FIELDS_NULL),
                    "FAUX_FINANCEMENT_OU_POUVOIR_ACHAT_CERTIFIE")
            out[key][fy]={
              "recettes_en_risque_mcad":money(at_risk),
              "perte_fictive_recettes_mcad":money(loss),
              "besoin_remplacement_meme_solde_mcad":money(loss),
              "besoin_total_equilibre_sans_resorption_mcad":
                money(max(Decimal(0),loss-original+mitigation)),
              "solde_sans_financement_mcad":money(original-loss),
              "solde_sans_financement_ni_resorption_mcad":money(original-loss-mitigation)}
    sov=data.get("souverainete")
    require(isinstance(sov,dict) and
            sov.get("modele_separe_requis") is True and
            sov.get("toutes_lignes_quantitatives") is None and
            all(sov.get(k) is False for k in (
              "transferts_federaux_automatiquement_retenus",
              "nouvelles_recettes_fiscales_federales_validees",
              "couts_nouvelles_competences_chiffres",
              "dette_repartie_et_pensions_chiffrees")) and
            sov.get("statut")=="AUCUNE_SIMULATION_SOUVERAINE_VALIDE",
            "SOUVERAINETE_NON_CHIFFREE_PAR_DEFAUT")
    tasks=data.get("priorite_et_preuves_a_obtenir")
    require(isinstance(tasks,list) and len(tasks)==10 and
            {t.get("id") for t in tasks}=={f"S{i:02d}" for i in range(1,11)} and
            all(t.get("statut")=="NON_OBTENUE" and
                len(t.get("tache",""))>=65 for t in tasks),
            "PREUVES_NOVA_FICTIVEMENT_OBTENUES")
    meter=data.get("barometre")
    require(isinstance(meter,dict) and
            meter.get("score_estime_sur_100")==53 and
            meter.get("points_estimes_manquants")==47 and
            meter.get("portes_p56o_encore_non_demontrees")==10 and
            meter.get("preuves_p52a_non_validees")==20 and
            meter.get("cellules_p52b_manquantes")==600 and
            meter.get("incidences_p52d_manquantes")==720 and
            meter.get("avis_independants_signes")==0 and
            meter.get("renumerotation_du_score_par_creation_fichiers") is False,
            "COMPLETUDE_P55N_FAUSSEMENT_MODIFIEE")
    refused=data.get("indicateurs_refus")
    require(isinstance(refused,dict) and
            all(refused.get(k)==0 for k in (
              "options_adoptees","taux_nova_certifies",
              "resultats_distributifs_nova_certifies")) and
            all(refused.get(k) is False for k in (
              "scenario_souverain_valide",
              "financement_remplacement_demontre",
              "taux_imposition_derive_de_ratio_recettes",
              "modele_publicable_comme_prevision_nova")),
            "FICTION_PRESENTEE_COMME_CERTIFICATION")
    return {
        "jalon":"P56S","score_estime_pourcent":53,
        "points_estimes_restants":47,
        "nombre_options":len(records),
        "exercices_comparables":list(YEARS),
        "options":out,
        "2027_2028":{key:value["2027-2028"] for key,value in out.items()},
        "aucun_taux_nova_publie":True,
        "aucune_transition_adoptee":True,
        "budget_souverain_certifie":False,
        "budget_nova_certifie":False,
        "conditions_au_100_pourcent_demontrees":0,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("options","p56r","p56q","cloture","barometre"):
        ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--exiger-option-adoptee",action="store_true")
    args=ap.parse_args(argv)
    if args.exiger_option_adoptee:
        print("REFUS: aucune option fiscale approuvée ni financée",file=sys.stderr)
        return 3
    try:
        def read(path):
            return json.loads(path.read_text(encoding="utf-8"))
        result=valider(read(args.options),read(args.p56r),read(args.p56q),
                       read(args.cloture),read(args.barometre))
        output=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if args.rapport:
            with args.rapport.open("x",encoding="utf-8") as f:
                f.write(output)
        else:
            print(output,end="")
        return 0
    except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
