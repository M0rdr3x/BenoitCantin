#!/usr/bin/env python3
"""P55V - comparateur executable de deux situations fiscales documentees.

Deux modes :
- SYNTHESE_FICTIVE_DEMONSTRATION : arithmetique sur exemples inventes ;
- CANDIDAT_DOCUMENTE_NON_AUDITE : chaque valeur declare une URL de provenance,
  mais le script NE VERIFIE PAS les documents ni les regles fiscales.
Dans les deux cas, les resultats sont conditionnels et NON CERTIFIES.
Le comparateur ne modifie jamais les 720 valeurs null de P52D.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

import mesurer_couverture_incidences_nova_p55s as p55s

BASE=p55s.BASE/"etudes"
DEMO=BASE/"P55V_EXEMPLE_COMPARAISON_FICTIVE_AVANT_APRES.json"
NO_GO="NO_GO_AUTOMATIQUE"
MODES={"SYNTHESE_FICTIVE_DEMONSTRATION","CANDIDAT_DOCUMENTE_NON_AUDITE"}
KEYS={"menage":p55s.HH,"entreprise":p55s.FIRMS}
CATEGORIES={"menage":p55s.CATEGORIES_HH,"entreprise":p55s.CATEGORIES_FIRMS}
CASE_ID=re.compile(r"^(?:demo|cas)-[a-z0-9]{1,8}$")
SRC_DEMO="FICTIF_EXPLICITE_NON_SOURCE"
LIMIT=32

def need(condition,message):
    if not condition:
        raise ValueError(message)

def decimal_amount(v):
    return p55s.money(v)

def subtractable_lines(kind,values):
    if kind=="menage":
        return (values["revenu_brut"]+values["prestations_federales"]+
            values["prestations_quebec_ou_etat"]-
            values["impot_revenu_federal"]-
            values["impot_revenu_quebec_ou_etat"]-
            values["cotisations_obligatoires"]-
            values["prelevements_municipaux_directs"])
    return (values["chiffre_affaires"]-
        values["couts_exploitation_hors_salaires"]-
        values["masse_salariale"]-values["impot_entreprise_federal"]-
        values["impot_entreprise_quebec_ou_etat"]-
        values["cotisations_employeur"]-
        values["prelevements_municipaux"]-
        values["taxes_consommation_non_recouvrables"]+
        values["subventions_recues"]-
        values["charge_additionnelle_anti_evasion"])

def arithmetic(case):
    """Compare des flux explicites, sans statuer sur leur realisme fiscal."""
    kind=case["type"]
    a={k:decimal_amount(v) for k,v in case["actuel"].items()}
    b={k:decimal_amount(v) for k,v in case["propose"].items()}
    f_a=subtractable_lines(kind,a)
    f_b=subtractable_lines(kind,b)
    s=lambda v:str(v.quantize(Decimal("0.01")))
    result={"id":case["id"],"type":kind,"categorie":case["categorie"],
        "regime":case["regime"],"scenario":case["scenario"],
        "annee":case["annee"],"calcul_conditionnel_non_certifiant":True,
        "flux_partiel_actuel_cad":s(f_a),
        "flux_partiel_propose_cad":s(f_b),
        "variation_flux_partiel_cad":s(f_b-f_a),
        "gain_de_pouvoir_achat_reel_demontre":False,
        "taux_nova_valides":False}
    if kind=="menage":
        a_after=f_a-a["taxes_consommation_supportees"]
        b_after=f_b-b["taxes_consommation_supportees"]
        result.update({
            "apres_taxes_supportees_illustratif_actuel_cad":s(a_after),
            "apres_taxes_supportees_illustratif_propose_cad":s(b_after),
            "variation_apres_taxes_supportees_illustrative_cad":
                s(b_after-a_after),
            "ne_reproduit_pas_revenu_disponible_officiel":True})
    else:
        result.update({
            "apres_taxes_supportees_illustratif_actuel_cad":None,
            "apres_taxes_supportees_illustratif_propose_cad":None,
            "variation_apres_taxes_supportees_illustrative_cad":None,
            "flux_entreprise_non_benefice_fiscal_certifie":True})
    return result

def validate_jeu(data):
    need(type(data) is dict and
         set(data)=={
             "schema_version","type_jeu","date_reference","statut",
             "unite","avis_independant_obtenu",
             "consequence_politique_reelle_autorisee",
             "version_programme_adoptee",
             "protection_des_donnees_nominatives",
             "sortie_requise","cas"},
         "P55V_JEU_SCHEMA")
    mode=data["type_jeu"]
    need(data["schema_version"]=="P55V-JEU-1"
         and mode in MODES
         and data["date_reference"]=="2026-11-07"
         and data["statut"]=="NON_REPRESENTATIF_NON_ADOPTE"
         and data["unite"]=="CAD_PAR_AN"
         and data["avis_independant_obtenu"] is False
         and data["consequence_politique_reelle_autorisee"] is False
         and data["version_programme_adoptee"] is False
         and data["protection_des_donnees_nominatives"] is True
         and data["sortie_requise"]==NO_GO,
         "P55V_AUCUNE_POLITIQUE_AUTORISEE")
    cases=data["cas"]
    need(type(cases) is list and 1<=len(cases)<=LIMIT,
         "P55V_NOMBRE_CAS_INVALIDE")
    ids=set()
    complete=partial=unknown=0
    reports=[]
    for item in cases:
        need(type(item) is dict and
             set(item)=={"id","type","categorie","regime","scenario",
                         "annee","actuel","propose","sources",
                         "avertissement"},
             "P55V_CAS_CHAMPS_INTERDITS")
        kind=item["type"];id=item["id"]
        need(type(id) is str and CASE_ID.fullmatch(id) is not None
             and id not in ids and kind in KEYS and
             item["categorie"] in CATEGORIES[kind] and
             item["regime"] in p55s.REGIMES
             and item["scenario"] in p55s.SCENARIOS
             and type(item["annee"]) is int and item["annee"]==2026
             and item["avertissement"]==
                "EXEMPLE_ARITHMETIQUE_INVENTE_SANS_VERIFICATION_FISCALE"
                if mode=="SYNTHESE_FICTIVE_DEMONSTRATION"
             else (type(id) is str and CASE_ID.fullmatch(id) is not None
                and id not in ids and kind in KEYS
                and item["categorie"] in CATEGORIES[kind]
                and item["regime"] in p55s.REGIMES
                and item["scenario"] in p55s.SCENARIOS
                and type(item["annee"]) is int and item["annee"]==2026
                and item["avertissement"]==
                    "SOURCES_DECLAREES_NON_CONTROLEES_EXTERNEMENT"),
             "P55V_IDENTITE_ET_ANNEE_INCOMPATIBLES")
        ids.add(id)
        need(type(item["sources"]) is dict and
             set(item["sources"])=={"actuel","propose"},
             "P55V_SOURCES_PAR_STATUT_EXIGEES")
        missing=0
        for status in ("actuel","propose"):
            row=item[status]
            src=item["sources"][status]
            need(type(row) is dict and type(src) is dict
                 and set(row)==set(KEYS[kind])
                 and set(src)==set(KEYS[kind]),
                 "P55V_COUVERTURE_CHAMPS_ET_SOURCES")
            for key in KEYS[kind]:
                value=row[key]
                source=src[key]
                if value is None:
                    need(source is None,
                         "P55V_SOURCE_POUR_MONTANT_ABSENT")
                    missing+=1
                else:
                    decimal_amount(value)
                    need(type(source) is str
                         and (source==SRC_DEMO if mode==
                              "SYNTHESE_FICTIVE_DEMONSTRATION"
                              else source.startswith("https://") and
                                   len(source)>16),
                         "P55V_PREUVE_DECLAREE_INCOMPATIBLE")
        if mode=="SYNTHESE_FICTIVE_DEMONSTRATION":
            need(missing==0,"P55V_DEMONSTRATION_INCOMPLETE")
        unknown+=missing
        if missing:
            partial+=1
        else:
            complete+=1
            result=arithmetic(item)
            result["type_source"]=mode
            result["sources_independamment_validees"]=False
            reports.append(result)
    return {"mode":mode,"nombre_cas":len(cases),
            "cas_arithmetiquement_complets":complete,
            "cas_incomplets":partial,
            "montants_manquants_du_jeu":unknown,
            "resultats_conditionnels":reports}

def check_parent():
    p55s_cfg,r=p55s.load()
    need(p55s_cfg["decision"]==NO_GO
         and r["total_montants_non_renseignes"]==720,
         "P55V_GABARIT_P52D_OU_SCORE_CHANGE")
    score=p55s.read(p55s.P55N)
    need(score["score_estimatif"]==53
         and score["decision"]==NO_GO,
         "P55V_SCORE_INCHANGE_EXIGE")
    return True

def public_report(diagnostic):
    return {"schema_version":"P55V-BILAN-PUBLIC-1",
        "date_reference":"2026-11-07",
        "jeu":"FICTIF" if diagnostic["mode"]==
            "SYNTHESE_FICTIVE_DEMONSTRATION"
            else "DECLARATION_CANDIDATE_NON_AUDITEE",
        "nombre_cas":diagnostic["nombre_cas"],
        "cas_calculables_arithmetiquement":
            diagnostic["cas_arithmetiquement_complets"],
        "cas_incomplets":diagnostic["cas_incomplets"],
        "montants_inconnus_du_jeu":diagnostic["montants_manquants_du_jeu"],
        "resultats_numeriques_de_cas_non_publies":True,
        "verification_sources_en_ligne_realisee":False,
        "taux_nova_propose_pct":None,
        "gain_general_pouvoir_achat_demontre":False,
        "effets_prix_et_services_publics_verifies":False,
        "financement_2027_2036_demontre":False,
        "p52d_valeurs_inconnues":720,
        "p52b_valeurs_inconnues":600,
        "score_programme_estime_pct":53,
        "avis_independants_signes":0,
        "decision":NO_GO}

def technical_report(diagnostic):
    return {"schema_version":"P55V-RESULTATS-CANDIDATS-1",
        "mode":diagnostic["mode"],
        "resultats":diagnostic["resultats_conditionnels"],
        "sources_non_auditees":True,
        "donnees_non_representatives_ou_hypotheses":True,
        "aucun_avis_independant":True,
        "decision":NO_GO}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jeu",default=str(DEMO))
    parser.add_argument("--bilan-public")
    parser.add_argument("--rapport-technique")
    parser.add_argument("--exiger-faisabilite",action="store_true")
    args=parser.parse_args(argv)
    try:
        check_parent()
        path=Path(args.jeu).expanduser().resolve()
        need(path.is_file() and not path.is_symlink()
             and path.stat().st_size<=100000,
             "P55V_JEU_INACCESSIBLE_OU_TROP_GRAND")
        data=p55s.read(path)
        diagnostic=validate_jeu(data)
        outputs=[Path(x).expanduser().absolute() for x in
                 (args.bilan_public,args.rapport_technique) if x]
        need(len({p.resolve() for p in outputs})==len(outputs),
             "P55V_DESTINATIONS_DUPLIQUEES")
        for dest in outputs:
            need(dest.parent.is_dir() and not dest.parent.is_symlink()
                 and not dest.exists() and not dest.is_symlink(),
                 "P55V_SORTIE_EXISTANTE_OU_INVALIDE")
        if args.bilan_public:
            import evaluer_completude_programme_nova_p55n as p55n
            p55n.write_new(args.bilan_public,
                           public_report(diagnostic))
        if args.rapport_technique:
            import evaluer_completude_programme_nova_p55n as p55n
            p55n.write_new(args.rapport_technique,
                           technical_report(diagnostic))
        print(json.dumps(public_report(diagnostic),
                         ensure_ascii=False,sort_keys=True))
        return 3 if args.exiger_faisabilite else 0
    except (OSError,ValueError,KeyError,TypeError,
            UnicodeError,json.JSONDecodeError):
        print("P55V_REFUS: DONNEES_OU_SOURCES_INSUFFISANTES",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
