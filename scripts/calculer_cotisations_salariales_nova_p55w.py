#!/usr/bin/env python3
"""P55W : cotisations salariales 2026 au Québec, sous hypothèses strictes.

Calcul arithmétique de RRQ, RQAP et AE seulement. Les salariés ont 18-64 ans,
un emploi continu, un employeur et un salaire entièrement cotisable au Québec.
N'est pas une paie individuelle ni une proposition d'abolition des régimes.
"""
import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets/projet-nova/etudes/P55W_COTISATIONS_SALARIALES_2026_SOURCES_ET_HYPOTHESES.json"
NO_GO="NO_GO_AUTOMATIQUE"
RATE={
  "rrq":{"exemption_annuelle_cad":"3500.00",
    "max_gains_premier_palier_cad":"74600.00",
    "max_gains_supplementaires_cad":"85000.00",
    "taux_premier_palier_salarie_pct":"6.30",
    "taux_premier_palier_employeur_pct":"6.30",
    "taux_second_palier_salarie_pct":"4.00",
    "taux_second_palier_employeur_pct":"4.00",
    "maximum_salarie_cad":"4895.30","maximum_employeur_cad":"4895.30"},
  "rqap":{"max_salaire_assurable_cad":"103000.00",
    "taux_salarie_pct":"0.430","taux_employeur_pct":"0.602",
    "maximum_salarie_cad":"442.90","maximum_employeur_cad":"620.06"},
  "ae":{"max_salaire_assurable_cad":"68900.00",
    "taux_salarie_quebec_pct":"1.30",
    "taux_employeur_quebec_pct":"1.82",
    "maximum_salarie_cad":"895.70","maximum_employeur_cad":"1253.98"}
}
SRC={
  "rrq_rqap":"https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/employeur-principaux-changements-2026/",
  "ae_quebec":"https://www.canada.ca/fr/agence-revenu/services/impot/entreprises/sujets/retenues-paie/retenues-paie-cotisations/assurance-emploi-ae/taux-cotisation-a-ae-maximums.html",
  "exemption_rrq":"https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/calcul-des-retenues-et-des-cotisations/cotisations-au-rrq/exemption-generale/",
}
MONEY=re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$")
CENT=Decimal("0.01")

def need(ok,reason):
    if not ok:
        raise ValueError(reason)

def money(value):
    need(type(value) is str and MONEY.fullmatch(value) is not None,
         "P55W_SALAIRE_DECIMAL_EXPLICITE_EXIGE")
    amount=Decimal(value)
    need(Decimal("0")<=amount<=Decimal("10000000"),
         "P55W_SALAIRE_HORS_PÉRIMÈTRE")
    return amount

def cents(value):
    return value.quantize(CENT,rounding=ROUND_HALF_UP)

def show(value):
    return str(cents(value))

def payroll(wage):
    """Montants annuels conditionnels, arrondi de chaque cotisation séparé."""
    w=money(wage)
    first=max(Decimal(0),min(w,Decimal("74600"))-Decimal("3500"))
    second=max(Decimal(0),min(w,Decimal("85000"))-Decimal("74600"))
    rrq=cents(first*Decimal("0.063")+second*Decimal("0.04"))
    rqap_s=cents(min(w,Decimal("103000"))*Decimal("0.00430"))
    rqap_e=cents(min(w,Decimal("103000"))*Decimal("0.00602"))
    ae_s=cents(min(w,Decimal("68900"))*Decimal("0.013"))
    ae_e=cents(min(w,Decimal("68900"))*Decimal("0.0182"))
    s=rrq+rqap_s+ae_s
    e=rrq+rqap_e+ae_e
    return {
       "annee":2026,"regime":"QUEBEC_DANS_CANADA",
       "salaire_admissible_hypothese_cad":show(w),
       "rrq_salarie_cad":show(rrq),
       "rqap_salarie_cad":show(rqap_s),
       "ae_salarie_cad":show(ae_s),
       "total_salarie_trois_regimes_cad":show(s),
       "rrq_employeur_cad":show(rrq),
       "rqap_employeur_cad":show(rqap_e),
       "ae_employeur_cad":show(ae_e),
       "total_employeur_trois_regimes_cad":show(e),
       "montants_reels_garantis":False,
       "fss_et_autres_cotisations_employeur_inclus":False,
       "impot_revenu_et_prestations_inclus":False,
       "ressources_de_remplacement_identifiees":False,
       "economie_nova_certifiee_cad":None,
       "decision":NO_GO}

def check(cfg):
    need(type(cfg) is dict
         and cfg.get("schema_version")=="P55W-1"
         and cfg.get("date_reference")=="2026-11-07"
         and cfg.get("decision")==NO_GO
         and cfg.get("statut")==
              "MODELE_DE_BAREME_OFFICIEL_CONDITIONNEL_NON_DECLARATION_REELLE",
         "P55W_ENTETE")
    s=cfg.get("sources")
    need(type(s) is dict and
         all(s.get(k)==v for k,v in SRC.items()) and
         s.get("annee")==2026 and s.get("pays")=="CANADA"
         and s.get("province")=="QUEBEC",
         "P55W_SOURCES")
    need(cfg.get("parametres")==RATE,"P55W_PARAMETRES_OFFICIELS")
    required={
       "revenu_pris_comme_salaire_admissible_aux_trois_regimes",
       "emploi_continu_toute_annee_2026",
       "personne_salariee_18_a_64_ans",
       "sans_exemption_ou_renonciation_particuliere",
       "un_seul_employeur_pour_annee",
       "gains_cotises_entierement_au_quebec",
       "retenues_reelles_par_periode_ou_arrondi_peuvent_differer",
       "cotisations_rrq_ei_rqap_uniquement",
       "non_inclus_FSS_employeur_normes_travail_CNESST_et_autres_charges",
       "non_inclus_impots_sur_revenu_reels",
       "non_inclus_prestations_ou_credit_impot",
       "non_comparable_automatiquement_a_l_exemple_gouvernemental_50k_revenu_annuel",
    }
    hypothesis=cfg.get("hypotheses_obligatoires")
    need(type(hypothesis) is dict and set(hypothesis)==required
         and all(v is True for v in hypothesis.values()),
         "P55W_HYPOTHESES_PERDUES")
    safe=cfg.get("protections")
    need(type(safe) is dict and
         safe.get("p52d_montants_inconnus")==720
         and safe.get("p52b_montants_inconnus")==600
         and safe.get("p55n_score_estime_pourcent")==53
         and safe.get("avis_independants_signes")==0
         and len(safe)==22
         and all(v is True for k,v in safe.items() if type(v) is bool)
         and safe.get("no_go_automatique") is True
         and safe.get("main_non_fusionnee") is True,
         "P55W_PROTECTIONS")
    actions=cfg.get("actions")
    need(type(actions) is list and len(actions)==8
         and [a["id"] for a in actions]==[
            "W"+str(i).zfill(2) for i in range(1,9)]
         and all(type(a) is dict and set(a)=={"id","objet","statut"}
                 and a["statut"]=="OUVERT" for a in actions),
         "P55W_PREUVES_OUVERTES")
    case=cfg.get("temoin_analytique_50000_cad")
    calc=payroll("50000.00")
    fields=("salaire_presume_cad","rrq_salarie_cad",
         "rqap_salarie_cad","ae_salarie_cad",
         "total_salarie_trois_regimes_cad",
         "rrq_employeur_cad","rqap_employeur_cad",
         "ae_employeur_cad","total_employeur_trois_regimes_cad")
    mapping={"salaire_presume_cad":"salaire_admissible_hypothese_cad"}
    need(type(case) is dict and
         all(case.get(key)==calc[mapping.get(key,key)]
             for key in fields)
         and case.get("source_du_salaire")==
            "HYPOTHESE_EXPLICITE_FICTIVE_NON_PIECE_D_UN_SALARIE"
         and case.get("type_de_calcul")==
            "ARITHMETIQUE_DES_TAUX_2026_SOUS_HYPOTHESES_RESTRICTIVES"
         and case.get("comparaison_directe_avec_P55T_847_cad_autorisee")
             is False,
         "P55W_CAS_DE_SALAIRE_NON_CONFORME")
    return True

def load():
    with CONFIG.open(encoding="utf-8") as stream:
        d=json.load(stream)
    check(d)
    import mesurer_couverture_incidences_nova_p55s as p55s
    scope,coverage=p55s.load()
    need(scope["decision"]==NO_GO
         and coverage["total_montants_non_renseignes"]==720
         and p55s.read(p55s.P55N)["score_estimatif"]==53,
         "P55W_CHAINAGE_P52D_ET_P55N")
    return d

def public_report(cfg,wage):
    check(cfg)
    r=payroll(wage)
    return {
       "schema_version":"P55W-BILAN-PUBLIC-1",
       "nature":"EXEMPLE_PURE_HYPOTHESE_SALARIE_QUEBEC_2026",
       "cotisations_conditionnelles":r,
       "cotisations_employeur_toutes_charges_incluses":False,
       "comparaison_avec_847_P55T_autorisee":False,
       "taux_nova_propose_pct":None,
       "protection_et_financement_regimes_demontres":False,
       "p52d_montants_inconnus":720,
       "p52b_montants_inconnus":600,
       "score_completude_estime_pct":53,
       "avis_independants_signes":0,
       "decision":NO_GO}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--salaire",default="50000.00")
    p.add_argument("--bilan-public")
    p.add_argument("--exiger-faisabilite",action="store_true")
    options=p.parse_args(argv)
    try:
        cfg=load()
        report=public_report(cfg,options.salaire)
        if options.bilan_public:
            target=Path(options.bilan_public).expanduser().absolute()
            need(target.parent.is_dir() and not target.parent.is_symlink()
                 and not target.exists() and not target.is_symlink(),
                 "P55W_SORTIE_EXISTANTE")
            import evaluer_completude_programme_nova_p55n as p55n
            p55n.write_new(str(target),report)
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 3 if options.exiger_faisabilite else 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):
        print("P55W_REFUS: HYPOTHESE_OU_BAREME_INCOMPLET",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
