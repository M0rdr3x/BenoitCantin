#!/usr/bin/env python3
"""P56K : tracer des assiettes et crédits FISCAUX, sans fabriquer les taux Nova.

Chiffres: particuliers 2023, sociétés 2021, dépenses fiscales 2025,
contrôle fiscal 2025-2026; quatre périodes et natures explicitement distinctes.
Les identités sur données arrondies acceptent les écarts publiés de 1 M$.
La vérification des URLs n'authentifie pas les octets ou les montants à distance.
"""
from __future__ import annotations
import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
import evaluer_transition_fiscale_nova_p52b as model

VERSION="P56K-1"
SOURCES={
    "PARTICULIERS_2023":("https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-comp-impot.asp",2023),
    "SOCIETES_2021":("https://www.quebec.ca/gouvernement/finances-publiques/revenus/donnees-fiscales/statistiques-fiscales-societes",2021),
    "DEPENSES_FISCALES_2025":("https://www.budget.finances.gouv.qc.ca/Budget/outils/depenses-fiscales/portrait-portrait.asp",2025),
    "CONTROLE_FISCAL_2025_2026":("https://www.revenuquebec.ca/fr/salle-de-presse/statistiques/les-resultats-des-activites-de-controle-fiscal/","2025-2026")
}
PERSONAL={
 "revenu_total_mcad":"427915",
 "deductions_revenu_net_mcad":"40892",
 "revenu_net_mcad":"387023",
 "deductions_revenu_imposable_mcad":"14761",
 "revenu_imposable_mcad":"372261",
 "impot_avant_credits_mcad":"62148",
 "credits_non_remboursables_effet_mcad":"21358",
 "impot_a_payer_mcad":"40790",
 "credits_remboursables_mcad":"9305",
 "impot_a_payer_net_credits_remboursables_mcad":"31485",
 "taux_moyen_publie_pourcent":"9.5"
}
COUNT={
 "nombre_declarations_milliers":"7220",
 "declarations_imposables_milliers":"4911",
 "declarations_non_imposables_milliers":"2309"
}
DISTRIBUTION={
 "REVENU_MOINS_10000":"2532",
 "REVENU_10000_19999":"12615",
 "REVENU_20000_29999":"26507",
 "REVENU_30000_49999":"59789",
 "REVENU_50000_99999":"159483",
 "REVENU_100000_PLUS":"166989"
}
CORPORATE={
 "revenu_imposable_quebec_mcad":"95784",
 "masse_salariale_assujettie_fss_mcad":"155850",
 "impot_revenu_societes_mcad":"10000",
 "cotisations_fss_societes_mcad":"5327",
 "prelevements_bruts_deux_categories_mcad":"15327",
 "credits_impot_societes_mcad":"2468",
 "impots_et_cotisations_nets_apres_credits_publies_mcad":"12860",
 "ecart_arrondi_attendu_sur_net_mcad":"1",
}
CORP_COUNT={
 "nb_declarations_societes":"564599",
 "nb_societes_non_imposees_revenu":"322020",
 "pct_societes_non_imposees_revenu":"57.0",
 "nombre_petites":"542249",
 "nombre_moyennes":"14858",
 "nombre_grandes":"7492"
}
FISCAL={
 "total_publie_mcad":"52864.9",
 "impot_particuliers_mcad":"34843.4",
 "impot_societes_mcad":"7196.8",
 "taxes_consommation_mcad":"10824.7",
 "beneficiaires_particuliers_mcad":"43046.9",
 "beneficiaires_societes_mcad":"9818.0"
}
FISCAL_COUNT={
 "nombre_mesures_total":273,
 "nombre_mesures_impot_particuliers":152,
 "nombre_mesures_impot_societes":77,
 "nombre_mesures_taxes_consommation":44
}
NO_EVIDENCE={f"K{i:02d}" for i in range(1,11)}
VALUE=re.compile(r"(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,3})?\Z")

def require(ok,why):
    if not ok:
        raise ValueError(why)

def dec(value):
    require(type(value) is str and bool(VALUE.fullmatch(value)),"NOMBRE_DECIMAL_INVALIDE")
    try:
        return Decimal(value)
    except InvalidOperation as err:
        raise ValueError("NOMBRE_DECIMAL_INVALIDE") from err

def check_fields(obj,expect,label):
    require(isinstance(obj,dict),f"{label}_MAL_FORME")
    for k,expected in expect.items():
        require(k in obj and obj[k]==expected,f"{label}_{k}_DIVERGE")
    return {k:dec(obj[k]) for k in expect}

def auditer(data,gabarit,preuves,barometre):
    require(isinstance(data,dict) and data.get("schema_version")==VERSION,"SCHEMA_INVALIDE")
    require(data.get("date_revue")=="2026-11-07" and
            data.get("statut")=="OBSERVATIONS_FISCALES_OFFICIELLES_HETEROGENES_NON_MODELE_NOVA"
            and data.get("decision")=="NO_GO_AUTOMATIQUE" and
            data.get("territoire")=="QUEBEC_DANS_CANADA","EN_TETE_INVALIDE")
    refs=data.get("sources")
    require(isinstance(refs,dict) and set(refs)==set(SOURCES),"QUATRE_SOURCES_REQUISES")
    for key,(url,year) in SOURCES.items():
        r=refs[key]
        require(isinstance(r,dict) and r.get("url")==url and r.get("millesime")==year
                and isinstance(r.get("organisme"),str)
                and len(r["organisme"])>=8,"SOURCE_METADONNEES_INVALIDE_"+key)
    require(refs["PARTICULIERS_2023"].get("url_nombre_contribuables")=="https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/resume.asp" and
            refs["PARTICULIERS_2023"].get("tableau")=="A.7 et A.9" and
            refs["SOCIETES_2021"].get("tableau")==
            "Sommaire des assiettes et déclarations des sociétés" and
            refs["DEPENSES_FISCALES_2025"].get("tableau")==
            "B.2 - Coût global des dépenses fiscales","SOURCE_TABLES_INCORRECTES")
    p=data.get("particuliers_2023")
    personal=check_fields(p,PERSONAL,"PARTICULIERS")
    pc=check_fields(p,COUNT,"PARTICULIERS_NOMBRE")
    require(p.get("source_id")=="PARTICULIERS_2023"
            and p.get("unite_montant")=="M_CAD"
            and p.get("taux_moyen_denominateur")=="REVENU_TOTAL_ET_NON_REVENU_IMPOSABLE"
            and p.get("distribution_type")=="REVENUS_TOTAUX_ET_NON_ASSIETTES_IMPOSABLES_PAR_DECILE"
            and p.get("pouvoir_achat_mesure_par_tranche") is False
            and p.get("credit_par_tranche_obtenu") is False,
            "ASSIETTE_PERSONNELLE_NON_CONFORME")
    require(personal["revenu_total_mcad"]-personal["deductions_revenu_net_mcad"]==
            personal["revenu_net_mcad"],"REVENUS_NET_NON_RECONCILIES")
    # Le tableau A.7 est arrondi : 387023 - 14761 = 372262 contre 372261 publiés.
    deductible_gap=personal["revenu_net_mcad"]-personal["deductions_revenu_imposable_mcad"]-personal["revenu_imposable_mcad"]
    require(abs(deductible_gap)<=1,"REVENUS_IMPOSABLES_HORS_ARRONDIS")
    require(personal["impot_avant_credits_mcad"]-
            personal["credits_non_remboursables_effet_mcad"]==personal["impot_a_payer_mcad"]
            and personal["impot_a_payer_mcad"]-personal["credits_remboursables_mcad"]==
            personal["impot_a_payer_net_credits_remboursables_mcad"],
            "CREDITS_PERSONNELS_NON_RECONCILIES")
    require(pc["declarations_imposables_milliers"]+
            pc["declarations_non_imposables_milliers"]==
            pc["nombre_declarations_milliers"],"NB_CONTRIBUABLES_INCOHERENT")
    require(abs(personal["impot_a_payer_mcad"] /
            personal["revenu_total_mcad"]*100 -
            personal["taux_moyen_publie_pourcent"])<=Decimal("0.05"),
            "TAUX_MOYEN_PUBLIE_N_EST_PAS_SUR_REVENU_IMPOSABLE")
    income_dist=p.get("distribution_revenu_total_2023_mcad")
    require(isinstance(income_dist,list) and len(income_dist)==len(DISTRIBUTION),
            "TRANCHES_REVENU_INCOMPLETES")
    found={}
    for row in income_dist:
        require(isinstance(row,dict),"LIGNE_TRANCHE_INVALIDE")
        k=row.get("id")
        require(type(k) is str and k in DISTRIBUTION and k not in found,
                "TRANCHE_INCONNUE_OU_DUPLIQUEE")
        require(row.get("montant")==DISTRIBUTION[k] and
                isinstance(row.get("tranche"),str) and len(row["tranche"])>=8,
                "TRANCHE_REVENU_NON_TRAÇABLE")
        found[k]=dec(row["montant"])
    require(set(found)==set(DISTRIBUTION) and
            sum(found.values(),Decimal(0))==personal["revenu_total_mcad"],
            "DISTRIBUTION_REVENU_TOTAL_NE_RECONCILIE_PAS")
    s=data.get("societes_2021")
    corporate=check_fields(s,CORPORATE,"SOCIETES")
    corp_n=check_fields(s,CORP_COUNT,"SOCIETES_NOMBRE")
    require(s.get("source_id")=="SOCIETES_2021" and
            s.get("unite_montant")=="M_CAD" and isinstance(s.get("limites"),list)
            and len(s["limites"])>=4,"CONTEXTE_SOCIETES_INCOMPLET")
    require(corporate["impot_revenu_societes_mcad"]+
            corporate["cotisations_fss_societes_mcad"]==
            corporate["prelevements_bruts_deux_categories_mcad"],
            "IMPOT_SOCIETES_FSS_NON_CONCILIES")
    net_gap=(corporate["prelevements_bruts_deux_categories_mcad"]-
             corporate["credits_impot_societes_mcad"]-
             corporate["impots_et_cotisations_nets_apres_credits_publies_mcad"])
    require(abs(net_gap)<=corporate["ecart_arrondi_attendu_sur_net_mcad"]==
            Decimal("1") and net_gap==Decimal("-1"),
            "ARRONDI_SOCIETES_NON_DECLARE")
    require(corp_n["nombre_petites"]+corp_n["nombre_moyennes"]+
            corp_n["nombre_grandes"]==corp_n["nb_declarations_societes"] and
            abs(corp_n["nb_societes_non_imposees_revenu"]/
                corp_n["nb_declarations_societes"]*100 -
                corp_n["pct_societes_non_imposees_revenu"])<=Decimal("0.05"),
            "DECLARATIONS_SOCIETES_INCOHERENTES")
    f=data.get("depenses_fiscales_2025")
    fiscal=check_fields(f,FISCAL,"DEPENSES_FISCALES")
    require(f.get("source_id")=="DEPENSES_FISCALES_2025"
            and f.get("unite")=="M_CAD" and
            f.get("annee_nature")==
            "ESTIMATION_ET_PROJECTION_DEPENSES_FISCALES_NON_RECETTES_RECOUVREES" and
            f.get("recettes_automatiquement_recuperables_mcad") is None
            and f.get("droits_sociaux_et_mesures_protegees_a_inventorier") is True,
            "DEPENSES_FISCALES_NON_RECUPERABLES_AUTOMATIQUEMENT")
    for k,v in FISCAL_COUNT.items():
        require(type(f.get(k)) is int and f[k]==v,"MESURES_FISCALES_INCOMPLETES")
    require(f["nombre_mesures_impot_particuliers"]+
            f["nombre_mesures_impot_societes"]+
            f["nombre_mesures_taxes_consommation"]==f["nombre_mesures_total"],
            "MESURES_FISCALES_NON_RECONCILIEES")
    require(fiscal["impot_particuliers_mcad"]+fiscal["impot_societes_mcad"]+
            fiscal["taxes_consommation_mcad"]==
            fiscal["total_publie_mcad"] and
            fiscal["beneficiaires_particuliers_mcad"]+
            fiscal["beneficiaires_societes_mcad"]==fiscal["total_publie_mcad"],
            "COUTS_FISCAUX_DU_PORTRAIT_NON_RECONCILIES")
    c=data.get("controle_fiscal_2025_2026")
    require(isinstance(c,dict) and c.get("source_id")=="CONTROLE_FISCAL_2025_2026"
            and c.get("unite")=="M_CAD" and
            c.get("resultats_activites_controle_fiscal_publies_mcad")=="4797"
            and c.get("nouveau_rendement_recouvrable_nova_mcad") is None
            and c.get("ajout_au_revenu_p52b_autorise") is False
            and c.get("repartition_entreprises_pct")=="69" and
            c.get("repartition_particuliers_pct")=="31" and
            c.get("statut")==
            "RESULTAT_ACTIVITES_CONTROLE_NON_NOUVELLE_ASSIETTE_NOVA",
            "RESULTATS_FISCAUX_NON_RECETTE_ADDITIONNELLE")
    comp=data.get("comparabilite")
    require(isinstance(comp,dict)
            and comp.get("annees_alignées") is False
            and comp.get("particuliers_annee")==2023
            and comp.get("societes_annee")==2021
            and comp.get("depenses_fiscales_annee")==2025
            and comp.get("etats_financiers_niveau")=="COMPTES_PUBLICS_2025_2026"
            and comp.get("total_assiettes_personnes_et_societes_measures_agrege_2023_mcad") is None
            and all(comp.get(k) is False for k in
                    ("taux_unique_nova_calculable","taux_societes_nova_calculable",
                     "taux_particuliers_nova_calculable"))
            and all(comp.get(k) is True for k in (
                "aucune_projection_decennale_issue_d_une_annee_historique",
                "revenus_de_sociétés_2021_non_extrapoles_2027_2036",
                "revenus_de_particuliers_2023_non_extrapoles_2027_2036",
                "non_deduction_automatique_credits_et_prestations")),
            "ASSIETTES_ET_ANNEES_INCOMPARABLES")
    regimes=data.get("deux_regimes")
    require(isinstance(regimes,dict) and set(regimes)=={
        "QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN"},"REGIMES_NON_DISTINCTS")
    prov=regimes["QUEBEC_DANS_CANADA"]
    sovereign=regimes["QUEBEC_SOUVERAIN"]
    require(prov.get("competence")=="QUEBEC_SEULEMENT_IMPOTS_PROVINCIAUX"
            and prov.get("impots_federaux_non_supprimables_unilateralement") is True
            and prov.get("societes_et_particuliers_pas_deux_assiettes_additionnables_sans_recoupements") is True
            and prov.get("assiettes_2027_2036_validees") is False
            and prov.get("incidence_menages_deciles_validee") is False
            and prov.get("revenu_nouveau_prelevement_anti_paradis_mcad") is None,
            "COMPETENCES_PROVINCIALES_INVENTEES")
    require(sovereign.get("competence")=="HYPOTHESE_CONDITIONNEE_STATUT_ET_NEGOCIATIONS"
            and all(sovereign.get(k) is None for k in (
                "assiettes_federales_net_recouvrables_mcad",
                "couteuses_fonctions_federales_dette_pensions_mcad","taux_adopte"))
            and sovereign.get("traites_accords_fiscalite_recours_verifies") is False
            and sovereign.get("assiettes_2027_2036_validees") is False,
            "BUDGET_SOUVERAIN_NON_PROUVE")
    evidence=data.get("preuves_suivantes")
    require(isinstance(evidence,list) and len(evidence)==len(NO_EVIDENCE)
            and {x.get("id") for x in evidence if isinstance(x,dict)}==NO_EVIDENCE
            and all(x.get("statut")=="NON_OBTENUE" and x.get("preuve") is None and
                    len(x.get("objet",""))>=35 for x in evidence)
            and data.get("nombre_preuves_restantes")==10,
            "JUSTIFICATIFS_ECONOMIQUES_INCOMPLETS")
    prev=model.evaluate(gabarit,preuves)
    require(prev["entrees_financieres_manquantes"]==600
            and prev["preuves_P52A_encore_non_valides"]==20
            and prev["decision"]=="NO_GO_AUTOMATIQUE",
            "MODELE_DECENNAL_P52B_MODIFIE")
    require(isinstance(barometre,dict) and
            barometre.get("schema_version")=="P55N-1" and
            barometre.get("score_estimatif")==53 and
            barometre.get("score_evalue_sur")==100 and
            sum(x["points_estimes"] for x in barometre["axes"])==53,
            "BAROMETRE_NON_RECONCILIE")
    require(data.get("p55n_score_estimatif")==53 and
            data.get("p52b_montants_inconnus")==600 and
            data.get("p52d_incidences_inconnues")==720 and
            data.get("p52a_preuves_non_validees")==20 and
            data.get("taux_fiscaux_nova_adoptes") is False and
            data.get("transposition_p52b") is False and
            data.get("economies_nova_certifiees_mcad") is None
            and data.get("validation_independante_nova") is False and
            data.get("decision_budget_decennal")=="NO_GO",
            "VALIDATION_NOVA_FICTIVE")
    return {
        "jalon":"P56K","schema_version":VERSION,
        "statut":"SERIES_D_ASSIETTES_HISTORIQUES_NON_HARMONISEES",
        "particuliers_annee":2023,
        "particuliers_revenu_total_mcad":p["revenu_total_mcad"],
        "particuliers_revenu_imposable_mcad":p["revenu_imposable_mcad"],
        "particuliers_impot_apres_credits_remboursables_mcad":
            p["impot_a_payer_net_credits_remboursables_mcad"],
        "particuliers_ecart_arrondi_imposable_mcad":str(deductible_gap),
        "particuliers_six_tranches_revenus_totaux_mcad":str(sum(found.values())),
        "societes_annee":2021,
        "societes_revenu_imposable_quebec_mcad":s["revenu_imposable_quebec_mcad"],
        "societes_fss_masse_salariale_assujettie_mcad":s["masse_salariale_assujettie_fss_mcad"],
        "societes_credits_mcad":s["credits_impot_societes_mcad"],
        "societes_ecart_arrondi_net_mcad":str(net_gap),
        "societes_non_imposees_nombre":s["nb_societes_non_imposees_revenu"],
        "depenses_fiscales_annee":2025,
        "depenses_fiscales_publiees_mcad":f["total_publie_mcad"],
        "recettes_certaines_du_retrait_credits_mcad":None,
        "controle_fiscal_2025_2026_resultats_publies_mcad":"4797",
        "recettes_nouvelles_nova_anti_paradis_mcad":None,
        "annees_harmonisees":False,
        "assiette_nova_2027_2036_mcad":None,
        "taux_nova_calculable":False,
        "personnes_a_faible_revenu_non_protegees_par_hypothese":False,
        "incidence_distributive_calculee":False,
        "budget_nova_valide":False,
        "montants_budget_p52b_inconnus":600,
        "incidences_p52d_inconnues":720,
        "preuves_p52a_non_validees":20,
        "score_estime_p55n":53,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assiettes",required=True,type=Path)
    parser.add_argument("--gabarit",required=True,type=Path)
    parser.add_argument("--preuves",required=True,type=Path)
    parser.add_argument("--barometre",required=True,type=Path)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-taux-certifie",action="store_true")
    a=parser.parse_args(argv)
    if a.exiger_taux_certifie:
        print("NO_GO_AUTOMATIQUE: années non harmonisées et incidences non vérifiées",file=sys.stderr)
        return 3
    try:
        def load(pth):
            return json.loads(pth.read_text(encoding="utf-8"))
        result=json.dumps(auditer(load(a.assiettes),load(a.gabarit),
                                  load(a.preuves),load(a.barometre)),
                          ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as f:
                f.write(result)
        else:
            print(result,end="")
        return 0
    except (ValueError,KeyError,TypeError,OSError,AssertionError,json.JSONDecodeError) as err:
        print("REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
