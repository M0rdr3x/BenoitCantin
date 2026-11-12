#!/usr/bin/env python3
"""P55S: mesurer la couverture de l'incidence, sans rendre fictive une economie.

Deux calculatrices de contrôle n'acceptent que des cas explicitement SYNTHETIQUES.
Elles ne reproduisent pas les lois fiscales ni les transferts sociaux réels.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

BASE=Path(__file__).resolve().parents[1]/"projets"/"projet-nova"
CONFIG=BASE/"etudes"/"P55S_CADRE_INCIDENCE_REVENU_DISPONIBLE.json"
P52D=BASE/"etudes"/"P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json"
P55N=BASE/"etudes"/"P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
NO_GO="NO_GO_AUTOMATIQUE"
HH=("revenu_brut","prestations_federales","prestations_quebec_ou_etat",
    "impot_revenu_federal","impot_revenu_quebec_ou_etat",
    "cotisations_obligatoires","prelevements_municipaux_directs",
    "taxes_consommation_supportees")
FIRMS=("chiffre_affaires","couts_exploitation_hors_salaires","masse_salariale",
       "impot_entreprise_federal","impot_entreprise_quebec_ou_etat",
       "cotisations_employeur","prelevements_municipaux",
       "taxes_consommation_non_recouvrables","subventions_recues",
       "charge_additionnelle_anti_evasion")
CATEGORIES_HH=("personne_seule_revenu_modeste","famille_avec_enfants",
               "famille_monoparentale","personne_retraitee",
               "personne_seule_revenu_moyen")
CATEGORIES_FIRMS=("PME","GRANDE_ENTREPRISE")
REGIMES=("QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN")
SCENARIOS=("central","prudent","stress")
SAFE={
    "NE_PAS_REMPLACER_NULL_PAR_ZERO",
    "NE_PAS_CALCULER_INCIDENTE_REELLE_SANS_PIECES",
    "CALCULS_SYNTHETIQUES_SEULEMENT_PAR_ENTREES_EXPLICITES",
    "AUCUNE_PONDERATION_POPULATION_PAR_CAS_FICTIFS",
    "REVENU_DISPONIBLE_DIRECT_DISTINCT_TAXES_CONSOMMATION",
    "DEPENSES_SERVICES_PUBLICS_EN_NATURE_HORS_REVENU_DISPONIBLE",
    "PRIX_ET_REPERCUSSIONS_NON_ESTIMES_AUTOMATIQUEMENT",
    "TRAITEMENT_FRAIS_GARDE_ET_LOGEMENT_A_DOCUMENTer",
    "FEDERAL_NON_SUPPRIME_DANS_CANADA",
    "TRANSITION_SOUVERAINE_HYPOTHETIQUE",
    "SERVICE_DETTE_ET_PRESTATIONS_NON_SUPPRIMES",
    "PROTECTION_MENAGES_MODESTES_ET_RETRAITES",
    "PROTECTION_PME_ET_EMPLOIS",
    "FONDS_MUNICIPAUX_CONSERVES",
    "PRELEVEMENT_ANTI_PARADIS_NON_CERTIFIE",
    "IMPOT_REVENU_NON_VALIDE",
    "CRITERES_GO_REQUIERENT_CAS_COMPLETS",
    "AUCUN_TAUX_CANDIDAT_IMPLICITE",
    "DEFICIT_BUDGETAIRE_NE_SE_DEDUIT_PAS_DES_CAS",
    "MAINTENIR_P52D_720_MONTANTS_INCONNUS",
    "MAINTENIR_P52B_600_MONTANTS_INCONNUS",
    "MAINTENIR_P55N_53_POURCENT",
    "AUCUNE_ECONOMIE_CERTIFIEE",
    "AUCUN_AVIS_PROFESSIONNEL_SIGNE",
    "SINJIRA_INCHANGE",
    "PAS_DE_CONTACT_EXTERNE",
    "PAS_DE_DEPENSE",
    "PAS_DE_FUSION_MAIN",
    "NO_GO_AUTOMATIQUE",
}
SYNTHETIC_LIMIT=Decimal("100000000.00")
MONEY=re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$")

def need(ok,why):
    if not ok:
        raise ValueError(why)

def read(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)

def money(value):
    need(type(value) is str and bool(MONEY.fullmatch(value)),
         "P55S_MONTANT_EXPLICITE_DEUX_DECIMALES_EXIGE")
    d=Decimal(value)
    need(d<=SYNTHETIC_LIMIT,"P55S_MONTANT_SYNTHETIQUE_TROP_ELEVE")
    return d

def fixture_synthetic(category,actual,proposed,kind="menage"):
    """Contrôle arithmétique sur exemples fictifs, jamais estimation réelle."""
    cols=HH if kind=="menage" else FIRMS if kind=="entreprise" else None
    need(cols is not None and category in
         (CATEGORIES_HH if kind=="menage" else CATEGORIES_FIRMS),
         "P55S_CATEGORIE_INVALIDE")
    need(type(actual) is dict and type(proposed) is dict and
         set(actual)==set(cols) and set(proposed)==set(cols),
         "P55S_CHAMPS_COMPLETS_EXIGES")
    a={k:money(actual[k]) for k in cols}
    b={k:money(proposed[k]) for k in cols}
    if kind=="menage":
        def totals(v):
            direct=(v["revenu_brut"]+v["prestations_federales"]+
                v["prestations_quebec_ou_etat"]-v["impot_revenu_federal"]-
                v["impot_revenu_quebec_ou_etat"]-
                v["cotisations_obligatoires"]-
                v["prelevements_municipaux_directs"])
            after=direct-v["taxes_consommation_supportees"]
            return direct,after
        label="FLUX_DIRECT_PARTIEL_ET_APRES_TAXES_ILLUSTRATIVES"
    else:
        def totals(v):
            cash=(v["chiffre_affaires"]-v["couts_exploitation_hors_salaires"]-
                v["masse_salariale"]-v["impot_entreprise_federal"]-
                v["impot_entreprise_quebec_ou_etat"]-
                v["cotisations_employeur"]-v["prelevements_municipaux"]-
                v["taxes_consommation_non_recouvrables"]+
                v["subventions_recues"]-v["charge_additionnelle_anti_evasion"])
            return cash,None
        label="FLUX_SOCIETE_ILLUSTRATIF_NON_BENEFICE_COMPTABLE"
    a_direct,a_other=totals(a)
    b_direct,b_other=totals(b)
    fmt=lambda value:None if value is None else str(value.quantize(Decimal("0.01")))
    return {"categorie":category,"type":kind,"donnees":"ENTIEREMENT_FICTIVES",
            "statut_non_representatif":True,
            "direct_actuel_cad":fmt(a_direct),
            "direct_propose_cad":fmt(b_direct),
            "variation_directe_cad":fmt(b_direct-a_direct),
            "apres_taxes_consommation_actuel_cad":fmt(a_other),
            "apres_taxes_consommation_propose_cad":fmt(b_other),
            "variation_apres_taxes_consommation_cad":
                fmt(b_other-a_other) if kind=="menage" else None,
            "limite":label,"taux_nova_propose":None,
            "validation_legale_ou_economique":False}

def check_config(cfg):
    need(type(cfg) is dict and cfg.get("schema_version")=="P55S-1"
         and cfg.get("date_reference")=="2026-11-06"
         and cfg.get("decision")==NO_GO
         and cfg.get("statut")==
             "PROTOCOLE_DE_CALCUL_DOCUMENTAIRE_ET_SYNTHETIQUE_NON_ADOPTE",
         "P55S_REFERENTIEL_INVALIDE")
    p=cfg.get("perimetre")
    need(type(p) is dict and
         p.get("regimes")==list(REGIMES)
         and p.get("scenarios")==list(SCENARIOS)
         and p.get("menages_categories")==list(CATEGORIES_HH)
         and p.get("entreprises_categories")==list(CATEGORIES_FIRMS)
         and p.get("champs_menages")==list(HH)
         and p.get("champs_entreprises")==list(FIRMS)
         and p.get("situations_fiscales")==["actuel","propose"]
         and p.get("combinaisons_regime_scenario")==6
         and p.get("nombre_cas_menages")==30
         and p.get("nombre_cas_entreprises")==12
         and p.get("montants_menages_inconnus")==480
         and p.get("montants_entreprises_inconnus")==240
         and p.get("montants_inconnus_total")==720
         and p.get("cas_reels_suffisamment_documentes")==0
         and p.get("cas_artificiels_representatifs_de_la_population") is False
         and p.get("comparaison_validable_avec_donnees_actuelles") is False,
         "P55S_COUVERTURE_INCONFORME")
    need(type(cfg.get("protections")) is dict
         and set(cfg["protections"])==SAFE
         and all(v is True for v in cfg["protections"].values()),
         "P55S_PROTECTIONS_MANQUANTES")
    tasks=cfg.get("actions_justificatifs")
    need(type(tasks) is list and len(tasks)==12
         and [x["id"] for x in tasks]==[
             "S"+str(i).zfill(2) for i in range(1,13)]
         and all(type(x) is dict
                 and set(x)=={"id","objet","preuve","statut"}
                 and x["statut"]=="OUVERT" and x["preuve"]
                 for x in tasks),"P55S_PREUVES_NON_DOCUMENTEES")
    methods=cfg.get("methodes")
    need(type(methods) is dict
         and methods.get("calcul_reel_autorise") is False
         and methods.get("calcul_synthetique_avec_jeu_fictif_explicitement_declare")
             is True
         and methods.get("extrapolation_fiscale_autorisee") is False
         and methods.get("comparaison_reelle_par_decile_disponible") is False,
         "P55S_PAS_DE_PREVISION_FISCALE")
    sources=cfg.get("sources")
    need(type(sources) is list
         and len(sources)==5
         and {x["id"] for x in sources}==
             {"P52D","P55N","ISQ_DISPONIBLE",
              "QUEBEC_SIMULATION","CFFP_SIMULATEUR"},
         "P55S_SOURCES_NON_CONFORMES")
    return True

def inspect(cfg,p52d,p55n):
    check_config(cfg)
    need(type(p52d) is dict and
         p52d.get("schema_version")=="P52D-1"
         and p52d.get("aucune_ponderation_population") is True
         and p52d.get("autorisations")=={
             "fiscalite":False,"publication":False,"fusion":False},
         "P55S_GABARIT_SOURCE_NON_AUTORISE")
    need(p55n.get("schema_version")=="P55N-1"
         and p55n.get("score_estimatif")==53
         and p55n.get("decision")==NO_GO,
         "P55S_SCORE_P55N_MODIFIE")
    cases_hh=cases_firm=missing_hh=missing_firm=0
    for regime in REGIMES:
        r=p52d["regimes"][regime]
        need(r["competence"]==(
            "PROVINCE_SANS_MODIFIER_FEDERAL" if regime=="QUEBEC_DANS_CANADA"
            else "ETAT_SOUVERAIN_HYPOTHETIQUE_NON_RECONNU"),
            "P55S_COMPETENCE_MODIFIEE")
        for scenario in SCENARIOS:
            rows=r["scenarios"][scenario]
            need([x["categorie"] for x in rows["menages"]]==list(CATEGORIES_HH)
                 and [x["categorie"] for x in rows["entreprises"]]==
                     list(CATEGORIES_FIRMS),
                 "P55S_CAS_MODIFIES")
            for category,kind,fields in (
                ("menages","menage",HH),("entreprises","entreprise",FIRMS)):
                for case in rows[category]:
                    need(case["regime"]==regime and
                         case["scenario"]==scenario and
                         case["sources"]=={} and
                         case["classification_validee"] is False,
                         "P55S_PIECES_PROFESSIONNELLES_NON_REUES")
                    for status in ("actuel","propose"):
                        fields_data=case[status]
                        need(type(fields_data) is dict and
                             set(fields_data)==set(fields) and
                             all(fields_data[k] is None for k in fields),
                             "P55S_NOUVELLES_DONNEES_A_REEXAMINER")
                        if kind=="menage":missing_hh+=len(fields)
                        else:missing_firm+=len(fields)
                    if kind=="menage":cases_hh+=1
                    else:cases_firm+=1
    need((cases_hh,cases_firm,missing_hh,missing_firm)==
         (30,12,480,240),"P55S_MATRICE_NON_CONFORME")
    return {"menages":cases_hh,"entreprises":cases_firm,
            "montants_menages_non_renseignes":missing_hh,
            "montants_entreprises_non_renseignes":missing_firm,
            "total_montants_non_renseignes":missing_hh+missing_firm}

def load():
    cfg=read(CONFIG)
    result=inspect(cfg,read(P52D),read(P55N))
    return cfg,result

def public_report(cfg,result):
    check_config(cfg)
    need(result["total_montants_non_renseignes"]==720,
         "P55S_RAPPORT_INCONFORME")
    return {
        "schema_version":"P55S-BILAN-PUBLIC-1",
        "date_reference":"2026-11-06",
        "score_programme_estimatif_pourcent":53,
        "progression_score_demontree":False,
        "scenarios_regime":6,
        "profils_menages":5,
        "profils_entreprises":2,
        "cas_menages_total":result["menages"],
        "cas_entreprises_total":result["entreprises"],
        "montants_menages_non_renseignes":480,
        "montants_entreprises_non_renseignes":240,
        "montants_inconnus_total":720,
        "simulations_reelles_completes":0,
        "simulations_synthetiques_representatives":False,
        "gain_pouvoir_achat_certifie":False,
        "recettes_fiscales_deux_prelevements_demontrees":False,
        "taux_fiscal_propose_pct":None,
        "avis_independants_signes":0,
        "decision":NO_GO}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan-public")
    ap.add_argument("--exiger-incidence-validee",action="store_true")
    args=ap.parse_args(argv)
    try:
        cfg,res=load()
        report=public_report(cfg,res)
        if args.bilan_public:
            import evaluer_completude_programme_nova_p55n as p55n
            p55n.write_new(args.bilan_public,report)
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 3 if args.exiger_incidence_validee else 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError):
        print("P55S_REFUS: INCIDENCE_NON_DEMONTREE",file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
