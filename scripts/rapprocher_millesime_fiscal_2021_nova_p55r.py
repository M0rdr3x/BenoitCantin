#!/usr/bin/env python3
"""P55R - 2021 pour particuliers et societes: comparaison, jamais taux Nova."""
import argparse
import json
from pathlib import Path
import sys
import controler_assiettes_historiques_nova_p55q as p55q

DATA=p55q.BASE/"P55R_PAIRE_FISCALE_2021_PARTICULIERS_SOCIETES.json"
NO_GO="NO_GO_AUTOMATIQUE"
P={"revenu_total_mcad":383335,"deductions_agregees_mcad":49437,
"revenu_imposable_mcad":333898,"impot_a_payer_mcad":38503,
"credits_remboursables_mcad":14118,"impot_apres_credits_remboursables_mcad":24384,
"declarations_milliers":6975,"non_imposables_milliers":2052}
C={"revenu_imposable_quebec_mcad":95784,"revenu_imposable_mondial_mcad":231518,
"impot_revenu_quebec_mcad":10000,"cotisations_fss_mcad":5327,
"impots_cotisations_totaux_mcad":15327,"declarations":564599,
"societes_non_imposees_revenu":322020,"societes_sans_impot_ni_cotisation_fss":239628,
"petites_declarations":542249,"moyennes_declarations":14858,
"grandes_declarations":7492,"petites_impots_cotisations_mcad":4095,
"moyennes_impots_cotisations_mcad":2560,"grandes_impots_cotisations_mcad":8672}

def require(ok,msg):
    if not ok: raise ValueError(msg)

def check(d):
    require(d["schema_version"]=="P55R-1"
        and d["date_reference"]=="2026-11-05"
        and d["decision"]==NO_GO,"P55R_ENTETE")
    p=d["particuliers_2021"];c=d["societes_2021"]
    require(all(type(p.get(k)) is int and p[k]==v for k,v in P.items())
        and all(type(c.get(k)) is int and c[k]==v for k,v in C.items()),
        "P55R_MONTANTS_OFFICIELS")
    require(p["revenu_total_mcad"]-p["deductions_agregees_mcad"]==333898
        and abs(p["impot_a_payer_mcad"]-
            p["credits_remboursables_mcad"]-
            p["impot_apres_credits_remboursables_mcad"])<=1
        and c["impot_revenu_quebec_mcad"]+c["cotisations_fss_mcad"]==15327
        and c["petites_declarations"]+c["moyennes_declarations"]+
            c["grandes_declarations"]==564599
        and c["petites_impots_cotisations_mcad"]+
            c["moyennes_impots_cotisations_mcad"]+
            c["grandes_impots_cotisations_mcad"]==15327,
        "P55R_BOUCLAGE")
    src=d["sources"];m=d["rapprochements_autorises"]["comparaison_2021_meme_annee"]
    require(src["particuliers_2021"]["annee_imposition"]==2021
        and src["societes_2021"]["annee_imposition"]==2021
        and "finances.gouv.qc.ca" in src["particuliers_2021"]["url_table_historique"]
        and "quebec.ca" in src["societes_2021"]["url"]
        and m["annee_commune_observee"]==2021
        and m["particuliers_revenu_imposable_2023_mcad"]==372261
        and m["particuliers_delta_2021_a_2023_mcad"]==38363
        and m["particuliers_variation_deux_ans_pct_une_decimale"]=="11.5"
        and m["assiette_combinee_validee_mcad"] is None
        and m["taux_nova_propose_pct"] is None
        and m["recettes_anti_paradis_certifiees_mcad"] is None
        and m["annee_commune_est_base_fiscale_harmonisee"] is False
        and m["credits_exceptionnels_2021_recurrents_presumes"] is False
        and m["p52b_inconnues_restantes"]==600
        and m["p55n_completude_estimee_pct"]==53,
        "P55R_PAS_D_ASSIETTE_UNIQUE")
    guards=d["protections"]
    require(len(guards)==31 and all(value is True for value in guards.values())
        and "ASSIETTES_PERSONNES_ET_SOCIETES_NON_FUSIONNEES" in guards
        and "SINJIRA_INCHANGE" in guards
        and len(d["actions_preuves_humaines"])==8
        and [x["id"] for x in d["actions_preuves_humaines"]]==
            ["R"+str(i).zfill(2) for i in range(1,9)]
        and all(x["statut"]=="OUVERT" for x in d["actions_preuves_humaines"]),
        "P55R_GARDES")
    return True

def load():
    with DATA.open(encoding="utf8") as f: d=json.load(f)
    check(d)
    q=p55q.load()
    require(q["societes_2021"]["revenu_imposable_au_quebec_mcad"]==95784
        and q["personnes_2023"]["revenu_imposable_mcad"]==372261,
        "P55R_CHAINAGE_P55Q")
    return d

def report(d):
    check(d)
    return {"schema_version":"P55R-BILAN-PUBLIC-1",
      "annee_fiscale_commune":2021,
      "revenu_imposable_personnes_2021_mcad":333898,
      "revenu_imposable_societes_quebec_2021_mcad":95784,
      "non_imposes_personnes_pct":"29.4","non_imposees_societes_pct":"57.0",
      "credits_exceptionnels_2021_environ_mcad":7100,
      "credits_exceptionnels_2021_non_recurrents":True,
      "assiette_nova_harmonisee_mcad":None,"taux_nova_pct":None,
      "recettes_anti_paradis_certifiees_mcad":None,
      "maturite_estimee_pct":53,"financement_p52b_montants_inconnus":600,
      "preuves_ouvertes":8,"economies_certifiees_mcad":None,
      "decision":NO_GO}

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--rapport-public")
    parser.add_argument("--exiger-taux-certifie",action="store_true")
    a=parser.parse_args(argv)
    try:
        d=load();result=report(d)
        if a.rapport_public:
            p55q.p55p.p55o.p55n.write_new(a.rapport_public,result)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if a.exiger_taux_certifie else 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):
        print("P55R_REFUS: ASSIETTES_NON_CERTIFIEES",file=sys.stderr)
        return 2

if __name__=="__main__": raise SystemExit(main())
