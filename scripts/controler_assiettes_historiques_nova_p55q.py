#!/usr/bin/env python3
"""P55Q - historique fiscal: particuliers 2023 vs societes 2021, sans taux propose."""
import argparse
import json
from pathlib import Path
import sys
import calculer_exposition_prelevements_nova_p55p as p55p

BASE=Path(__file__).resolve().parents[1]/"projets/projet-nova/etudes"
SOURCE=BASE/"P55Q_ASSIETTES_HISTORIQUES_REVENUS_2021_2023.json"
NO_GO="NO_GO_AUTOMATIQUE"

def require(ok, message):
    if not ok:
        raise ValueError(message)

def validate(doc):
    require(type(doc) is dict and doc.get("schema_version")=="P55Q-1"
            and doc.get("statut")=="ETUDE_HISTORIQUE_CANDIDATE_NON_ADOPTEE"
            and doc.get("date_reference")=="2026-11-05"
            and doc.get("decision")==NO_GO,"P55Q_ENTETE")
    s=doc["sources"]
    p=doc["personnes_2023"]
    c=doc["societes_2021"]
    limits=doc["comparaison_sans_addition"]
    require(s["personnes"]["annee_imposition"]==2023
            and s["societes"]["annee_imposition"]==2021
            and s["personnes"]["table"]=="A.7"
            and s["personnes"]["page_resume"]==
              "https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-comp-impot.asp"
            and s["societes"]["page_resume"]==
              "https://www.quebec.ca/gouvernement/finances-publiques/revenus/donnees-fiscales/statistiques-fiscales-societes"
            and s["budget_2026_2027"]["source_interne"]==
              "P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json","P55Q_ORIGINES")
    expected_p={"contribuables_declares":7220140,"revenu_total_mcad":427915,
      "deductions_revenu_net_mcad":40892,"revenu_net_mcad":387023,
      "deductions_revenu_imposable_mcad":14761,"revenu_imposable_mcad":372261,
      "impot_sur_revenu_imposable_mcad":62148,
      "credits_non_remboursables_mcad":21358,"impot_a_payer_mcad":40790,
      "credits_remboursables_mcad":9305,
      "impot_moins_credits_remboursables_mcad":31485}
    expected_c={"declarations_revenues":564599,
      "revenu_imposable_au_quebec_mcad":95784,
      "revenu_imposable_mondial_mcad":231518,
      "impot_revenu_quebec_mcad":10000,
      "cotisations_fonds_services_sante_mcad":5327,
      "total_impots_cotisations_mcad":15327,
      "credits_impot_mcad":2468,
      "impot_cotisations_nets_credits_impot_mcad":12860,
      "societe_non_imposees_nombre":322020}
    require(all(type(p.get(k)) is int and p[k]==v for k,v in expected_p.items())
            and all(type(c.get(k)) is int and c[k]==v for k,v in expected_c.items())
            and "note" in p and "note" in c,"P55Q_MONTANTS_ORIGINAUX")
    # Allow +/-1 M$ caused by independently rounded official published values.
    require(abs((p["revenu_net_mcad"]-p["deductions_revenu_imposable_mcad"])
                -p["revenu_imposable_mcad"])<=1
            and p["revenu_total_mcad"]-p["deductions_revenu_net_mcad"]==
                p["revenu_net_mcad"]
            and p["impot_sur_revenu_imposable_mcad"]
                -p["credits_non_remboursables_mcad"]==p["impot_a_payer_mcad"]
            and p["impot_a_payer_mcad"]-p["credits_remboursables_mcad"]==
                p["impot_moins_credits_remboursables_mcad"]
            and c["impot_revenu_quebec_mcad"]+
                c["cotisations_fonds_services_sante_mcad"]==
                c["total_impots_cotisations_mcad"]
            and abs(c["total_impots_cotisations_mcad"]
                    -c["credits_impot_mcad"]
                    -c["impot_cotisations_nets_credits_impot_mcad"])<=1,
            "P55Q_BOUCLAGE_HISTORIQUE")
    require(limits["annee_commune_disponible_pour_base_personnes_et_socs"] is False
            and limits["somme_assiettes_utilisable_pour_taux"] is False
            and limits["assiette_combinee_harmonisee_mcad"] is None
            and limits["taux_pour_financer_les_deux_prelevements_pct"] is None
            and limits["revenu_additionnel_anti_paradis_fiscaux_certifie_mcad"] is None
            and limits["budget_2026_personnes_impot_mcad"]==50800
            and limits["budget_2026_societes_impot_mcad"]==14527
            and limits["p55n_score_global_estime_pct"]==53
            and limits["p52b_champs_financiers_inconnus"]==600
            and limits["decision"]==NO_GO,"P55Q_AUCUN_TAUX_INFERABLE")
    guards=doc["protections"]
    tasks=doc["pistes_de_travail"]
    require(type(guards) is dict and len(guards)==30
            and all(v is True for v in guards.values())
            and "NE_JAMAIS_ADDITIONNER_ASSIETTES_ANNEES_DIFFERENTES" in guards
            and type(tasks) is list and len(tasks)==10
            and [x["code"] for x in tasks]==[
                "Q"+str(i).zfill(2) for i in range(1,11)]
            and all(x["statut"]=="OUVERT" for x in tasks),
            "P55Q_VERROUS_QUESTIONS")
    return True

def load():
    cfg=p55p.p55o.read_json(SOURCE)
    validate(cfg)
    parent=p55p.load()
    report=p55p.public_report(parent)
    require(report["score_maturite_estimatif_inchange_pct"]==53
            and report["montants_financiers_nova_2027_2036_inconnus"]==600
            and report["recettes_actuelles_imputs_revenus_mcad"]==65327
            and report["decision"]==NO_GO,"P55Q_PARENT_P55P")
    return cfg

def public_report(cfg):
    validate(cfg)
    return {"schema_version":"P55Q-BILAN-PUBLIC-1",
        "annee_particuliers":2023,"annee_societes":2021,
        "particuliers_revenu_imposable_historique_mcad":372261,
        "particuliers_impot_a_payer_historique_mcad":40790,
        "societes_revenu_imposable_quebec_historique_mcad":95784,
        "societes_impot_revenu_historique_mcad":10000,
        "assiette_commune_certifiee_mcad":None,
        "taux_fiscal_unifie_propose_pct":None,
        "revenus_anti_paradis_certifies_mcad":None,
        "annees_fiscales_differentes":True,
        "score_estime_inchange_pct":53,
        "inconnues_financieres_decennales":600,
        "preuves_a_obtenir":10,"economie_certifiee_mcad":None,
        "decision":NO_GO}

def public_table(cfg):
    validate(cfg)
    return {"schema_version":"P55Q-TABLE-PUBLIQUE-1",
        "sources":cfg["sources"],"particuliers_2023":cfg["personnes_2023"],
        "societes_2021":cfg["societes_2021"],
        "limites":cfg["comparaison_sans_addition"],
        "preuves_a_obtenir":cfg["pistes_de_travail"],
        "warning":"ASSIETTES_ANNEES_NON_COMPARABLES_SANS_HARMONISATION",
        "decision":NO_GO}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan-public")
    ap.add_argument("--table-public")
    ap.add_argument("--exiger-taux-demontre",action="store_true")
    args=ap.parse_args(argv)
    try:
        cfg=load()
        paths=[Path(x).expanduser().absolute() for x in
               (args.bilan_public,args.table_public) if x]
        require(len(set(p.resolve() for p in paths))==len(paths),
                "P55Q_CHEMINS_IDENTIQUES")
        for p in paths:
            require(p.parent.is_dir() and not p.parent.is_symlink()
                    and not p.exists() and not p.is_symlink(),"P55Q_SORTIE_EXISTANTE")
        result=public_report(cfg)
        if args.bilan_public:
            p55p.p55o.p55n.write_new(args.bilan_public,result)
        if args.table_public:
            p55p.p55o.p55n.write_new(args.table_public,public_table(cfg))
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if args.exiger_taux_demontre else 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,json.JSONDecodeError):
        print("P55Q_REFUS: SOURCES_FISCALES_NON_HARMONISEES",file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
