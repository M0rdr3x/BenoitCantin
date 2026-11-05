#!/usr/bin/env python3
"""P55O : inspecter les 600 montants inconnus de P52B sans valeurs inventées.

Baromètre P55N inchangé. Les prévisions officielles P52C ne sont JAMAIS
recopiées comme réalisations ou prévisions annuelles du Projet Nova.
"""
import argparse
import json
from pathlib import Path
import sys

import evaluer_transition_fiscale_nova_p52b as p52b
import evaluer_completude_programme_nova_p55n as p55n

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"projets"/"projet-nova"/"etudes"
CONFIG=BASE/"P55O_CARTOGRAPHIE_MANQUES_BUDGET_2027_2036.json"
P52B=BASE/"P52B_GABARIT_MODELE_DECENNAL.json"
P52A=BASE/"P52A_REGISTRE_PREUVES_FISCALES.json"
P52C=BASE/"P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json"
NO_GO="NO_GO_AUTOMATIQUE"
CODES=(
    "impot_revenu_net",
    "revenus_non_fiscaux_nets",
    "transferts_federaux_nets",
    "autres_prelevements_provinciaux_nets",
    "services_existants_hors_dette_et_municipal_nets",
    "service_dette_net",
    "transferts_municipaux_nets",
    "fonctions_souveraines_nouvelles_nettes",
    "couts_transition_nets",
    "provision_crises_nette",
)
TAX_SOURCE={
    "impot_particuliers":50800,
    "impot_societes":14527,
    "taxes_vente":26349,
    "cotisations_sante":9412,
    "foncier_scolaire":1311,
}
EXPECTED_MISSING=600
GUARDS={
    "pas_de_changement_p52b",
    "pas_de_changement_p52c",
    "pas_de_changement_p55n",
    "pas_d_ajout_de_recettes_anti_evasion",
    "pas_de_coupes_emploi_services",
    "pas_d_appauvrissement_population",
    "pas_de_taux_ni_economies_certifies",
    "pas_de_recettes_federales_reprises_sans_competence",
    "pas_de_double_compte_ville_rtc_somhac",
    "aucun_contact_humain",
    "aucun_engagement_financier",
    "aucune_modification_sinjira",
    "aucune_fusion_main",
    "no_go_automatique",
}
BLOCKS={
    "NE_PAS_SIMULER_UN_TAUX_SANS_ASSIETTE",
    "NE_PAS_ASSIMILER_2026_2027_A_2027_2036",
    "NE_PAS_REMPLACER_NULL_PAR_ZERO",
    "NE_PAS_COMPTER_ANTI_EVASION_COMME_RECETTE_CERTIFIEE",
    "NE_PAS_ABOLIR_LES_AUTRES_PRELEVEMENTS_PAR_UN_SOUHAIT",
    "NE_PAS_SUPPRIMER_LE_FINANCEMENT_MUNICIPAL",
    "NE_PAS_AJOUTER_DEUX_FOIS_SERVICE_DETTE",
    "NE_PAS_CONFONDRE_PENSION_DETTE_ET_CAISSE",
    "NE_PAS_CONFONDRE_SCENARIOS_CONSTITUTIONNELS",
    "NE_PAS_AFFIRMER_GAINS_POUVOIR_ACHAT_SANS_INCIDENTE",
    "NE_PAS_INVENTER_DES_RESULTATS_PROFESSIONNELS",
    "NE_PAS_PUBLIER_COMME_PROGRAMME_ADOPTE",
}

def require(cond,reason):
    if not cond:
        raise ValueError(reason)

def read_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def validate_catalogue(catalogue):
    require(type(catalogue) is dict
            and catalogue.get("schema_version")=="P55O-1"
            and catalogue.get("date_reference")=="2026-11-05"
            and catalogue.get("statut")==
                "ANALYSE_CANDIDATE_NON_VALIDEE_INDEPENDAMMENT"
            and catalogue.get("objet")==
                "TRIAGE_CHAMPS_FISCAUX_MANQUANTS_P52B_A_PARTIR_DES_ORIGINAUX_CANDIDATS"
            and catalogue.get("references")==["P52A","P52B","P52C","P55N"]
            and catalogue.get("decision")==NO_GO,
            "P55O_ENTETE_INCORRECT")
    p=catalogue.get("perimetre")
    require(type(p) is dict
            and p.get("regimes")==list(p52b.REGIMES)
            and p.get("scenarios")==list(p52b.TRAJECTOIRES)
            and p.get("exercices_debut")==list(p52b.EXERCICES)
            and p.get("unite")=="G_CAD"
            and p.get("nombre_exercices_scenarios")==60
            and p.get("postes_recettes_non_anti_evasion")==4
            and p.get("postes_depenses")==6
            and p.get("postes_inconnus_par_exercice_scenario")==10
            and p.get("recettes_inconnues")==240
            and p.get("depenses_inconnues")==360
            and p.get("champs_inconnus_total")==EXPECTED_MISSING
            and p.get("anti_evasion_zero_prudent_sans_certification")==60
            and p.get("exercices_scenarios_calculables")==0
            and p.get("justificatifs_p52a_ouverts")==20
            and all(type(p[k]) is int for k in (
                "nombre_exercices_scenarios","recettes_inconnues",
                "depenses_inconnues","champs_inconnus_total",
                "anti_evasion_zero_prudent_sans_certification",
                "exercices_scenarios_calculables",
                "justificatifs_p52a_ouverts")),
            "P55O_PERIMETRE_NON_CONFORME")
    plans=catalogue.get("plans_acquisition")
    require(type(plans) is list and len(plans)==len(CODES),
            "P55O_DIX_CHAMPS_EXIGES")
    for i,(field,entry) in enumerate(zip(CODES,plans),1):
        require(type(entry) is dict
                and set(entry)=={"id","champ","groupe","domaine",
                                 "preuve_requise","condition","interdiction",
                                 "etats_source","statut"}
                and entry["id"]=="O"+str(i).zfill(2)
                and entry["champ"]==field
                and entry["groupe"]==(
                    "recettes" if i<=4 else "depenses")
                and entry["etat"+"s_source"]==
                    "NON_RENSEIGNE_SUR_60_EXERCICES_SCENARIOS"
                and entry["statut"]=="A_INSTRUIRE"
                and all(type(entry[k]) is str and len(entry[k])>=8
                        for k in ("domaine","preuve_requise",
                                  "condition","interdiction")),
                "P55O_PREUVE_OU_CHAMP_NON_CONFORME")
    prior=catalogue.get("source_budget_historique")
    require(type(prior) is dict
            and prior.get("id")=="P52C-1"
            and prior.get("exercice")=="2026-2027"
            and prior.get("unite")=="M_CAD"
            and prior.get("nature")==
                "PREVISIONS_BUDGET_GOUVERNEMENT_QUEBEC_NON_PROJECTIONS_NOVA"
            and type(prior.get("postes_temoins")) is list
            and prior["postes_temoins"]==[
                {"id":k,"valeur_mcad":v} for k,v in TAX_SOURCE.items()]
            and type(prior.get("somme_impots_revenus_actuels_mcad")) is int
            and prior["somme_impots_revenus_actuels_mcad"]==65327
            and prior.get("ventes_sont_agregat_non_tvq_seule") is True
            and prior.get("impossible_de_deduire_taux_futur") is True,
            "P55O_BUDGET_REFERENCE_DEFORME")
    require(type(catalogue.get("conditions_bloquantes")) is list
            and len(catalogue["conditions_bloquantes"])==len(BLOCKS)
            and set(catalogue["conditions_bloquantes"])==BLOCKS
            and type(catalogue.get("protections")) is dict
            and set(catalogue["protections"])==GUARDS
            and all(x is True for x in catalogue["protections"].values()),
            "P55O_PROTECTIONS_MANQUANTES")
    return True

def inspect(catalogue, model, evidences, fiscal, maturity):
    validate_catalogue(catalogue)
    require(p55n.validate(maturity)["score"]==53
            and maturity["decision"]==NO_GO,
            "P55O_SCORE_P55N_DOIT_DEMEURER_INCHANGE")
    summary=p52b.evaluate(model,evidences)
    require(summary["entrees_financieres_manquantes"]==600
            and summary["preuves_P52A_encore_non_valides"]==20
            and summary["nombre_trajectoires"]==6
            and summary["decision"]==NO_GO,
            "P55O_AMONT_FINANCEMENT_ENCORE_NON_VALIDE")
    require(type(fiscal) is dict and fiscal.get("schema_version")=="P52C-1"
            and fiscal.get("periode")=="2026-2027"
            and fiscal.get("unite")=="M_CAD"
            and fiscal.get("hypotheses_nova_certifiees") is False
            and fiscal.get("taux_adoptes") is False,
            "P55O_REFERENCE_BUDGET_INVALIDE")
    expected={x["id"]:x["valeur_mcad"] for x in catalogue[
        "source_budget_historique"]["postes_temoins"]}
    observed={}
    for x in fiscal.get("lignes_revenus",[]):
        if x.get("id") in TAX_SOURCE:
            require(type(x.get("valeur_mcad")) is str
                    and x["valeur_mcad"]==str(TAX_SOURCE[x["id"]])
                    and x["id"] not in observed,
                    "P55O_LIGNE_BUDGET_INCOMPATIBLE")
            observed[x["id"]]=int(x["valeur_mcad"])
    require(observed==expected
            and observed["impot_particuliers"]+observed["impot_societes"]==
                65327,
            "P55O_IMPOTS_REVENUS_REF_NE_BOUCLENT_PAS")
    fields=dict.fromkeys(CODES,0)
    scenarios=[]
    year_missing={str(y):0 for y in p52b.EXERCICES}
    zero_hypotheses=0
    for regime in p52b.REGIMES:
        for trajectory in p52b.TRAJECTOIRES:
            rows=model["regimes"][regime]["trajectoires"][trajectory]
            missing_revenue=missing_expense=calculable=0
            for row in rows:
                year=row["exercice_debut"]
                valid=p52b.verify_row(row,year)
                require(valid["champs_manquants"]==10
                        and valid["solde_simule_gcad"] is None
                        and valid["validation_independante_obtenue"] is False,
                        "P55O_SCENARIO_MODIFIE_NOUVELLE_REEVALUATION_REQUISE")
                calculable+=int(valid["solde_simule_gcad"] is not None)
                for group,fields_tuple in (
                    ("recettes",p52b.RECETTES),
                    ("depenses",p52b.DEPENSES)):
                    for field in fields_tuple:
                        if field=="anti_evasion_additionnelle_nette":
                            require(row[group][field]=="0"
                                    and row["sources"].get(field)==
                                        p52b.ZERO_PROVENANCE,
                                    "P55O_ZERO_ANTI_EVASION_NON_PRUDENT")
                            zero_hypotheses+=1
                        elif row[group][field] is None:
                            fields[field]+=1
                            year_missing[str(year)]+=1
                            if group=="recettes":
                                missing_revenue+=1
                            else:
                                missing_expense+=1
                        else:
                            raise ValueError("P55O_SAISIE_NON_REEVALUEE")
            scenarios.append({
                "regime":regime,"trajectoire":trajectory,
                "exercices":len(rows),
                "recettes_inconnues":missing_revenue,
                "depenses_inconnues":missing_expense,
                "soldes_calculables":calculable,
                "politique_fiscale_autorisee":False,
            })
    require(len(scenarios)==6
            and all(x["exercices"]==10
                    and x["recettes_inconnues"]==40
                    and x["depenses_inconnues"]==60
                    and x["soldes_calculables"]==0 for x in scenarios)
            and all(v==60 for v in fields.values())
            and all(v==60 for v in year_missing.values())
            and zero_hypotheses==60,
            "P55O_REPARTITION_DES_LACUNES_NON_CONFORME")
    return {"scenarios":scenarios,
            "frequence_par_champ":fields,
            "lacunes_par_exercice":year_missing,
            "anti_evasion_zeros_non_certifies":zero_hypotheses}

def load():
    cfg=read_json(CONFIG)
    return cfg,inspect(
        cfg,read_json(P52B),read_json(P52A),
        read_json(P52C),p55n.load())

def public_report(cfg,results):
    validate_catalogue(cfg)
    require(sum(results["frequence_par_champ"].values())==600,
            "P55O_SOLDE_DE_LACUNES_INCOHERENT")
    return {
        "schema_version":"P55O-BILAN-PUBLIC-1",
        "date_reference":"2026-11-05",
        "maturite_programme_estimative_pourcent":53,
        "maturite_modifiee_par_ce_jalon":False,
        "regimes":2,"trajectoires":3,"annees":10,
        "exercices_scenarios":60,
        "recettes_inconnues":240,"depenses_inconnues":360,
        "total_montants_inconnus":600,
        "soldes_futurs_calculables":0,
        "hypotheses_anti_evasion_a_zero_non_certifiees":60,
        "preuves_fiscales_p52a_ouvertes":20,
        "impots_revenus_2026_2027_prevision_officielle_mcad":65327,
        "impots_revenus_2026_2027_non_projections_nova":True,
        "taux_de_deux_prelevements_determinables":False,
        "financement_projet_demontre":False,
        "gains_pouvoir_achat_demontres":False,
        "avis_independants_signes":0,
        "economies_certifiees_cad":None,
        "decision":NO_GO,
    }

def public_table(cfg,results):
    validate_catalogue(cfg)
    return {
        "schema_version":"P55O-TABLE-PUBLIQUE-1",
        "source_budget":cfg["source_budget_historique"],
        "scenarios":results["scenarios"],
        "frequence_par_champ":results["frequence_par_champ"],
        "lacunes_par_exercice":results["lacunes_par_exercice"],
        "plans_acquisition":cfg["plans_acquisition"],
        "anti_evasion_zero_est_hypothese_et_non_prevision":True,
        "date_reference":"2026-11-05","decision":NO_GO,
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bilan-public")
    p.add_argument("--table-public")
    p.add_argument("--exiger-financement-demontre",action="store_true")
    opt=p.parse_args(argv)
    try:
        cfg,r=load()
        destinations=[Path(value).expanduser().absolute()
                      for value in (opt.bilan_public,opt.table_public)
                      if value]
        require(len(set(x.resolve() for x in destinations))==len(destinations),
                "P55O_CHEMINS_IDENTIQUES")
        for x in destinations:
            require(x.parent.is_dir() and not x.parent.is_symlink()
                    and not x.exists() and not x.is_symlink(),
                    "P55O_SORTIE_EXISTANTE")
        summary=public_report(cfg,r)
        if opt.bilan_public:
            p55n.write_new(opt.bilan_public,summary)
        if opt.table_public:
            p55n.write_new(opt.table_public,public_table(cfg,r))
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        return 3 if opt.exiger_financement_demontre else 0
    except (OSError,ValueError,TypeError,KeyError,
            UnicodeError,json.JSONDecodeError):
        print("P55O_REFUS: INTEGRITE_MODELE_FISCAL_INSUFFISANTE",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
