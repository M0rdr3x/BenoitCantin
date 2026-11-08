#!/usr/bin/env python3
"""P56R : rapprocher toutes les huit classes de revenus du cadre public.

Résultat : classification et dépendances du budget actuel du Québec dans le
Canada, pas un taux ni une politique fiscale Nova. Aucune validation de type
NO_GO ne peut être requalifiée en GO par ce seul script.
"""
from __future__ import annotations
import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
import mesurer_pont_recettes_fiscales_nova_p56q as p56q

VERSION="P56R-1"
CATS={
"impot_particuliers":("IMPOT_REVENU_ACTUEL","PILIER_1_POTENTIEL"),
"impots_societes":("IMPOT_REVENU_ACTUEL","PILIER_1_POTENTIEL"),
"cotisations_services_sante":("COTISATION_EMPLOYEURS","REMPLACEMENT_EXPLICITE_A_DEMONTRER"),
"impot_foncier_scolaire":("PRELEVEMENT_SCOLAIRE","REMPLACEMENT_EXPLICITE_A_DEMONTRER"),
"taxes_consommation":("TAXES_PROVINCIALES_CONSOMMATION","REMPLACEMENT_EXPLICITE_A_DEMONTRER"),
"droits_permis_redevances":("RECETTES_HETEROGENES","AUDIT_JURIDIQUE_ET_VENTILATION"),
"revenus_divers":("RECETTES_HETEROGENES","AUDIT_COMPTABLE_ET_VENTILATION"),
"entreprises_gouvernement":("REVENUS_ENTREPRISES_PUBLIQUES","CONSERVATION_SOUS_REVUE")
}
INCOME=("impot_particuliers","impots_societes")
AT_RISK=("cotisations_services_sante","impot_foncier_scolaire","taxes_consommation")
OTHER=("droits_permis_redevances","revenus_divers","entreprises_gouvernement")
YEARS=("2025-2026","2026-2027","2027-2028","2028-2029","2029-2030","2030-2031")
SOURCES={
"p56p":"projets/projet-nova/etudes/P56P_BASE_BUDGET_PREELECTORALE_2026_2031_VGQ_ET_ECARTS.json",
"p56q":"projets/projet-nova/etudes/P56Q_PONT_CONTREFACTUEL_RECETTES_2027_2031_SIMULATEUR_AMENDE.json",
"p56o":"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json"}
URLS={
"budget_officiel":"https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf",
"fss":"https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/employeur-principaux-changements-2026/",
"taxe_scolaire":"https://www.quebec.ca/education/prescolaire-primaire-et-secondaire/administration-encadrements/financement/taxe-scolaire",
"entreprises_publics":"https://www.quebec.ca/gouvernement/finances-publiques/budget-comptes-publics/comptes-publics/perimetre-comptable-fiduciaires-gouvernement"
}
LIMITS={
"chiffres_actuels_sont_recettes_pas_assiettes",
"pourcentage_du_rendement_actuel_n_est_pas_taux_imposition",
"retrait_trois_categories_n_est_pas_decision_nova",
"cotisations_FSS_ne_sont_pas_base_benefices",
"taxe_scolaire_n_est_pas_une_economie_de_services",
"taxes_federales_non_retirables_par_regime_provincial",
"les_ressources_provenant_des_transferts_ne_sont_pas_une_economie",
"droits_permis_redevances_non_decomposes",
"revenus_divers_non_decomposes",
"simulations_continuation_gouvernementale_non_programme_nova",
"souverainete_ne_donne_pas_recettes_federales_gratuites",
"recommandation_taux_fiscaux_non_autorisee"
}
def require(ok,code):
    if not ok:
        raise ValueError(code)

def cad(x):
    return p56q.integer(x)

def percent(a,b):
    require(b>0,"IMPOT_REVENU_REFERENCE_NUL")
    return (a*Decimal(100)/b).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)

def controler(d,p,q,model,bar,closure):
    previous=p56q.audit(q,p,model,bar,closure)
    require(isinstance(d,dict) and d.get("schema_version")==VERSION and
        d.get("date_revision")=="2026-11-08" and
        d.get("objet")=="RECONCILIATION_DES_HUIT_CATEGORIES_REVENUS_GOUVERNEMENTAUX_POUR_NOVA" and
        d.get("statut")=="CLASSIFICATION_PRELIMINAIRE_RECETTES_OFFICIELLES_NON_DECISIONS_POLITIQUES" and
        d.get("decision")=="NO_GO_AUTOMATIQUE","ENTETE_P56R_INVALIDE")
    source=d.get("provenance")
    require(isinstance(source,dict) and
            all(source.get(k)==v for k,v in SOURCES.items()),
            "DEPENDANCES_SOURCES_INCOMPATIBLES")
    for key,url in URLS.items():
        require(isinstance(source.get(key),dict) and
                source[key].get("url")==url,"LIEN_SOURCE_NON_OFFICIEL_"+key)
    require(source["budget_officiel"].get("date")=="2026-08-17" and
            source["budget_officiel"].get("tableau")=="2" and
            source["budget_officiel"].get("page_imprimee")==17 and
            source["fss"].get("remplace_pas_un_calcul_de_cotisations_reelles") is True and
            source["taxe_scolaire"].get("valeur_reelle_affectee_non_calculee") is True and
            source["entreprises_publics"].get("flux_financier_nouveau_non_calcule") is True and
            source["transferts"].get("statut")==
            "RECETTE_DU_REGIME_QUEBEC_CANADA_NON_GARANTIE_EN_SOUVERAINETE",
            "SOURCES_ET_LIMITES_MAL_DECRITES")
    opts=d.get("deux_prelevements_et_limites")
    require(isinstance(opts,dict) and opts.get("orientation")==
            "IMPOT_UNIQUE_SUR_REVENUS_PARTICULIERS_ET_SOCIETES_PLUS_MESURE_CONTRE_ABUS_PARADIS_FISCAUX" and
            opts.get("pilier_revenu_potentiel_categories")==list(INCOME) and
            opts.get("pilier_anti_paradis_recettes_futures_mcad") is None and
            opts.get("taux_personnes_entreprises_proposes") is None and
            all(opts.get(k) is True for k in (
              "prelevements_non_fiscaux_et_redevances_non_classes_comme_impots_automatiquement",
              "cotisations_regimes_sociaux_federaux_non_abolies_unilateralement",
              "suppression_taxe_fonciere_scolaire_NON_adoptee",
              "suppression_FSS_NON_adoptee",
              "suppression_taxes_consommation_provinciales_NON_adoptee",
              "remplacement_et_compensation_obligatoires_avant_adoption",
              "offre_services_publics_maintenue_dans_contre_factuel",
              "aucun_effet_comportemental_ou_dynamique_inclus")),
            "PROGRAMME_DEUX_PRELEVEMENTS_NON_APPROUVE")
    categories=d.get("categories_officielles")
    require(isinstance(categories,list) and len(categories)==8 and
            {r.get("poste_p56p") for r in categories if isinstance(r,dict)}==set(CATS) and
            {r.get("id") for r in categories}==
            {f"R{i:02d}" for i in range(1,9)},
            "HUIT_CATEGORIES_INCOMPLETES")
    for r in categories:
        key=r["poste_p56p"]
        require((r.get("nature"),r.get("traitement_provisoire"))==CATS[key] and
                isinstance(r.get("assiette_ou_nature"),str) and
                len(r["assiette_ou_nature"])>=20 and
                isinstance(r.get("risque_et_justification"),str) and
                len(r["risque_et_justification"])>=65 and
                r.get("avis_juridique_independant") is None and
                r.get("circuit_de_continuite_documente") is False and
                r.get("effet_nova_2027_2036_mcad") is None and
                r.get("statut")=="A_EXAMINER",
                "CLASSIFICATION_PREMATUREMENT_CERTIFIEE")
        amounts=r.get("montants_annee_p56p_mcad")
        require(isinstance(amounts,dict) and set(amounts)==set(YEARS),
                "RECETTE_SOURCE_PAR_EXERCICE_MANQUANTE")
        for original in p["annees_historique_et_previsions"]:
            fy=original["exercice"]
            require(cad(amounts[fy])==cad(original["revenus"][key]),
                    "POSTE_NON_RECONCILIE_"+key+"_"+fy)
    transfers=d.get("transferts_federaux")
    require(isinstance(transfers,dict) and transfers.get("classe")=="TRANSFERT_INTERGOUVERNEMENTAL" and
            transfers.get("lien_avec_regime")=="QUEBEC_DANS_CANADA" and
            transfers.get("non_economie_budgetaire") is True and
            transfers.get("transfert_pas_maintenu_par_defaut_en_souverainete") is True and
            set(transfers.get("montants_par_exercice_mcad",{}))==set(YEARS),
            "TRANSFERTS_FEDERAUX_CONFONDUS")
    for r in p["annees_historique_et_previsions"]:
        require(cad(transfers["montants_par_exercice_mcad"][r["exercice"]])==
                cad(r["transferts_federaux_mcad"]),
                "TRANSFERT_FEDERAL_SOURCE_NON_RECONCILIE")
    results=d.get("rapprochement_annees")
    require(isinstance(results,list) and
            [x.get("exercice") for x in results]==list(YEARS),
            "SIX_EXERCICES_COMPTABLES_REQUIS")
    summaries={}
    qyears={x["exercice"]:x for x in q["annees_reconciliees"]}
    for current,record in zip(results,p["annees_historique_et_previsions"]):
        year=current["exercice"]
        rv=record["revenus"]
        income=sum((cad(rv[k]) for k in INCOME),Decimal(0))
        at_risk=sum((cad(rv[k]) for k in AT_RISK),Decimal(0))
        other=sum((cad(rv[k]) for k in OTHER),Decimal(0))
        fed=cad(record["transferts_federaux_mcad"])
        total=cad(record["total_revenus_mcad"])
        legal=cad(record["solde_budgetaire_selon_loi_mcad"])
        gap=cad(record["ecart_a_resorber_non_finance_par_mesures_identifiees_mcad"])
        require(income+at_risk+other+fed==total,
                "REVENUS_TOTAUX_NON_CONCILIES")
        vals={
          "impots_sur_revenu_actuels_mcad":income,
          "trois_categories_a_remplacer_si_supprimees_mcad":at_risk,
          "autres_revenus_autonomes_a_qualifier_mcad":other,
          "transferts_federaux_au_regime_actuel_mcad":fed,
          "revenus_consolides_regime_actuel_mcad":total,
          "reconciliation_somme_mcad":income+at_risk+other+fed,
          "montant_pour_maintenir_recettes_publiques_mcad":at_risk,
          "besoin_arithmetique_si_zero_solde_loi_mcad":max(0,at_risk-legal),
          "besoin_zero_solde_loi_sans_ecarts_a_resorber_mcad":max(0,at_risk-legal+gap)
        }
        for key,val in vals.items():
            require(cad(current.get(key))==val,"CALCUL_MAUVAIS_"+key+"_"+year)
        require(current.get("millesime")==(
            "COMPTES_PUBLICS_2025_2026" if year=="2025-2026"
            else "PREVISIONS_RAPPORT_PREELECTORAL_AOUT_2026") and
            current.get("recettes_remplacement_en_pourcentage_des_impots_revenu_actuels")==
            str(percent(at_risk,income)) and
            current.get("ressources_zero_solde_en_pourcentage_des_impots_revenu_actuels")==
            str(percent(max(0,at_risk-legal),income)) and
            current.get("taux_effectif_nova") is None and
            current.get("rendement_cible_anti_paradis_prevu_mcad") is None and
            current.get("economie_reelle_identifiee_mcad") is None and
            current.get("scenario_immuable_hypothese_statique") is True and
            current.get("n_est_pas_une_hausse_de_taux_recommandee") is True,
            "POURCENTAGE_RECETTES_CONFONDU_TAUX_NOVA")
        require(at_risk==cad(qyears[year]["trois_categories_risque_suppression_mcad"]) and
                cad(current["besoin_arithmetique_si_zero_solde_loi_mcad"])==
                cad(qyears[year]["ressources_theoriques_additionnelles_pour_solde_loi_zero_si_ecart_resorbe_mcad"]),
                "RISQUE_P56Q_NON_RECONCILIE")
        summaries[year]={
            "impots_revenu_actuels_mcad":str(income),
            "trois_categories_a_remplacer_mcad":str(at_risk),
            "autres_revenus_provinciaux_mcad":str(other),
            "transferts_federaux_mcad":str(fed),
            "revenus_publics_totaux_mcad":str(total),
            "ratio_recettes_a_remplacer_sur_impots_revenu_actuels_pourcent":str(percent(at_risk,income)),
            "besoin_statique_zero_solde_loi_mcad":str(max(0,at_risk-legal))
        }
    require(summaries["2027-2028"]=={
        "impots_revenu_actuels_mcad":"68093",
        "trois_categories_a_remplacer_mcad":"42875",
        "autres_revenus_provinciaux_mcad":"29246",
        "transferts_federaux_mcad":"34011",
        "revenus_publics_totaux_mcad":"174225",
        "ratio_recettes_a_remplacer_sur_impots_revenu_actuels_pourcent":"62.97",
        "besoin_statique_zero_solde_loi_mcad":"48570"
    },"PIVOT_2027_2028_INCORRECT")
    regimes=d.get("deux_regimes")
    require(isinstance(regimes,dict) and
            set(regimes)=={"QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN"},
            "REGIMES_FUSIONNES")
    canada=regimes["QUEBEC_DANS_CANADA"]
    sovereign=regimes["QUEBEC_SOUVERAIN"]
    require(canada.get("recettes_federales_dans_reference_publique") is True and
            canada.get("tps_et_impots_federaux_non_abolissables_unilateralement") is True and
            canada.get("simulation_nova_certifiee") is False,
            "COMPETENCES_FEDERALES_INVENTEES")
    require(sovereign.get("reference_provinciale_non_directement_transposable") is True and
            sovereign.get("transferts_federaux_maintenus_par_defaut") is False and
            all(sovereign.get(k) is None for k in (
              "assiettes_impots_federaux_devenu_souverains_mcad",
              "couts_fonctions_federales_mcad",
              "dette_et_pensions_de_transition_mcad")) and
            sovereign.get("simulation_nova_certifiee") is False,
            "SOUVERAINETE_IMAGINAIRE_CHIFFREE")
    limits=d.get("limites")
    require(isinstance(limits,dict) and set(limits)==LIMITS and
            all(v is True for v in limits.values()),
            "LIMITES_DE_PROVENANCE_SILENCIEUSES")
    gates=d.get("conditions_pour_prochaine_phase")
    require(isinstance(gates,list) and len(gates)==10 and
            {r.get("id") for r in gates if isinstance(r,dict)}==
            {f"R{i:02d}" for i in range(1,11)} and
            all(r.get("statut")=="NON_DEMONTRE" and
                r.get("preuve_id") is None and
                r.get("responsable_habilite") is None and
                r.get("validation_independante") is False and
                len(r.get("critere",""))>=60 for r in gates),
            "CONDITIONS_AUDIT_SANS_AVIS_INDEPENDANTS")
    ind=d.get("indicateurs_fins")
    require(isinstance(ind,dict) and
            ind.get("p55n_score_estime")==53 and
            ind.get("p55n_points_restants_estimes")==47 and
            ind.get("p56o_portes_closes")==0 and
            ind.get("p52b_montants_a_renseigner")==600 and
            ind.get("p52d_incidence_a_renseigner")==720 and
            ind.get("p52a_preuves_a_valider")==20 and
            ind.get("annees_du_modele_decennal_sans_prevision_officielle_aout_2026")==6 and
            ind.get("avis_independants_nova_signes")==0 and
            ind.get("politique_nova_adoptee") is False and
            ind.get("budget_nova_certifie") is False and
            ind.get("decision")=="NO_GO_AUTOMATIQUE" and
            previous["score_estime_p55n"]==53 and
            bar.get("score_estimatif")==53,
            "PRETENDU_100_POURCENT_OU_CERTIFICATION")
    return {
      "jalon":"P56R",
      "source":"RAPPORT_PREELECTORAL_AOUT_2026_RECONCILIE_P56P_P56Q",
      "nombre_categories_revenues":len(categories),
      "nombre_exercices_reference":len(results),
      "annee_pivot":"2027-2028",
      "tableau_annee_pivot":summaries["2027-2028"],
      "rapprochements_annuels":summaries,
      "revenus_non_classes_comme_impots_a_ventiler":True,
      "transferts_federaux_non_recettes_souveraines_acquises":True,
      "taux_fiscal_nova_calculable":False,
      "mesures_deux_prelevements_adoptees":False,
      "conditions_non_demontrees":len(gates),
      "score_estime_p55n":53,
      "points_restants_estimes":47,
      "p52b_montants_inconnus":600,
      "p52d_incidences_inconnues":720,
      "programme_termine":False,
      "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for s in ("inventaire","p56p","p56q","p52b","barometre","p56o"):
        parser.add_argument("--"+s,required=True,type=Path)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-budget-nova-certifie",action="store_true")
    a=parser.parse_args(argv)
    if a.exiger_budget_nova_certifie:
        print("REFUS: aucun taux ni bilan Nova vérifié",file=sys.stderr)
        return 3
    try:
        def load(f):
            return json.loads(f.read_text(encoding="utf-8"))
        result=controler(*[load(getattr(a,k)) for k in (
           "inventaire","p56p","p56q","p52b","barometre","p56o")])
        output=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as file:
                file.write(output)
        else:
            print(output,end="")
        return 0
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as err:
        print("REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
