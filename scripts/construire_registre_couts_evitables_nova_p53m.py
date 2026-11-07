#!/usr/bin/env python3
"""P53M: registre probatoire des coûts publics potentiellement évitables."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import evaluer_hypotheses_economies_nova_p53l as precedent

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
SOURCE=D/"P53M_CRITERES_COUTS_EVITABLES.json"
REGIMES=("QUEBEC_DANS_LE_CANADA","QUEBEC_SOUVERAIN_HYPOTHETIQUE")
PREUVES=(
    "competence_juridique","base_comptable","contrats_et_factures",
    "volumes_de_service","cout_transition","couts_recurrents",
    "couts_externes","comparabilite","qualite_avant_apres",
    "consultation_employes_usagers","anti_double_compte","avis_independant")
NO_GO="NO_GO_AUTOMATIQUE"

def must(ok,reason):
    if not ok: raise ValueError(reason)

def load(path):
    p=Path(path)
    must(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<40000,"SOURCE_INVALIDE")
    x=json.loads(p.read_text(encoding="utf-8"))
    must(type(x) is dict,"OBJET_JSON_ATTENDU")
    return x

def sources():
    p53l,nb,nd=precedent.ouvrir_sources()
    cfg=load(SOURCE)
    must(cfg["schema_version"]=="P53M-1" and
         cfg["statut"]=="ETUDE_NON_ADOPTEE" and
         cfg["regimes"]==list(REGIMES) and
         cfg["categories"]==p53l["categories"] and
         cfg["preuves_requises"]==list(PREUVES) and
         cfg["protections"]==list(precedent.PROTECTIONS) and
         set(cfg["indicateurs"])==set(cfg["categories"]) and
         all(type(v) is list and len(v)>=3 and len(v)==len(set(v))
             for v in cfg["indicateurs"].values()) and
         set(cfg["verrous"])=={
             "montants_inconnus_restent_inconnus","aucune_suppression_emplois",
             "aucun_transfert_couts","services_essentiels_intacts",
             "pas_de_double_compte","pas_de_melange_regimes",
             "aucune_certification_automatique","aucun_document_prive_dans_git",
             "aucune_fusion","pas_d_economie_par_consolidation"} and
         all(v is True for v in cfg["verrous"].values()),
         "CRITERES_NON_CONFORMES")
    must(nb==1344 and nd==26 and
         p53l["etat_initial"]["economies_certifiees_cad"] is None and
         p53l["etat_initial"]["decision"]==NO_GO,"P53L_NON_CONFORME")
    return p53l,cfg,nb,nd

def catalogue(cfg):
    rows=[]
    for regime in REGIMES:
        for cat in cfg["categories"]:
            rows.append({
                "regime":regime,"categorie":cat,
                "indicateurs_a_mesurer":cfg["indicateurs"][cat],
                "preuves":{name:"NON_OBTENUE" for name in PREUVES},
                "protections":{name:"INCONNU" for name in precedent.PROTECTIONS},
                "cout_reference_cad":None,"cout_projection_cad":None,
                "cout_transition_cad":None,"economie_certifiee_cad":None,
                "statut":"A_DOCUMENTER"
            })
    must(len(rows)==12 and len({(r["regime"],r["categorie"]) for r in rows})==12,
         "DOUZE_PISTES_NON_VERIFIEES")
    return rows

def examiner(f,p53l,cfg):
    """Revue déclarative et calcul indicatif; jamais contrôle de documents primaires."""
    must(f.get("schema_version")=="P53M-FICHE-1","SCHEMA_INCONNU")
    ident=precedent.ident(f.get("id_fiche"))
    regime=f.get("regime")
    cat=f.get("categorie")
    must(regime in REGIMES and cat in cfg["categories"],"CATEGORIE_OU_REGIME_INCONNU")
    scope=precedent.ident(f.get("perimetre_budgetaire"))
    poste=precedent.ident(f.get("poste_budgetaire"))
    must(f.get("exercice_reference")==2024 and f.get("projection")==2027,
         "ANNEES_HORS_CADRE")
    must(f.get("statut_source")=="DECLARATION_NON_AUTHENTIFIEE",
         "AUTHENTIFICATION_NON_AUTORISEE")
    preuves=f.get("preuves")
    guards=f.get("protections")
    must(type(preuves) is dict and set(preuves)==set(PREUVES)
         and all(v in ("NON_OBTENUE","DECLAREE_NON_AUTHENTIFIEE")
                 for v in preuves.values()),"PREUVES_INCOHERENTES")
    must(type(guards) is dict and set(guards)==set(precedent.PROTECTIONS)
         and all(v in ("OUI","NON","INCONNU") for v in guards.values()),
         "PROTECTIONS_INCOHERENTES")
    scenario=f.get("scenario_p53l")
    statut_scenario=None
    if scenario is not None:
        must(type(scenario) is dict and
             scenario.get("identifiant_mesure")==ident and
             scenario.get("categorie")==cat and
             scenario.get("perimetre_reference")==scope and
             scenario.get("perimetre_projection")==scope and
             scenario.get("poste_budgetaire")==poste and
             scenario.get("protections")==guards,
             "SCENARIO_NON_RATTACHE")
        statut_scenario,_=precedent.evaluer(scenario,p53l)
    if "NON" in guards.values():
        statut="PROTECTIONS_VIOLEES"
    elif "INCONNU" in guards.values():
        statut="PROTECTIONS_NON_DEMONTREES"
    elif "NON_OBTENUE" in preuves.values():
        statut="PREUVES_MANQUANTES"
    elif scenario is None:
        statut="SCENARIO_ABSENT"
    elif statut_scenario=="HYPOTHESE_POSITIVE_NON_CERTIFIEE":
        statut="HYPOTHESE_POSITIVE_NON_CERTIFIEE"
    else:
        statut="SCENARIO_NON_ADMISSIBLE"
    return {"id":ident,"dedoublonnage":(regime,scope,poste,2027),
            "etat":statut,"montant_certifie_cad":None}

def bilan(cfg,nb,nd,examens):
    return {
        "schema_version":"P53M-RAPPORT-1","organismes_2024":nb,
        "dossiers_probatoires_p53k":nd,"regimes":len(REGIMES),
        "categories":len(cfg["categories"]),"fiches_standards":12,
        "fiches_declares_examinees":len(examens),
        "statuts_sans_details":dict(sorted(Counter(x["etat"] for x in examens).items())),
        "economies_certifiees_par_regime_cad":{k:None for k in REGIMES},
        "economies_totales_certifiees_cad":None,"preuves_authentifiees":0,
        "avis_independants_signes":0,"couts_transfers_reels_cad":None,
        "recettes_fiscales_adoptees_cad":None,
        "emplois_supprimes_autorises":0,
        "services_essentiels_reduits_autorises":False,
        "preuves_fiscales_F01_F20_validees":0,"montants_Nova_inconnus":1320,
        "fusion_autorisee":False,"decision":NO_GO
    }

def ecrire(path,value):
    p=Path(path)
    must(not p.exists() and not p.is_symlink(),"ECRASEMENT_REFUSE")
    with p.open("x",encoding="utf-8") as h:
        h.write(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n")

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--bilan")
    a.add_argument("--registre")
    a.add_argument("--fiche",action="append",default=[])
    a.add_argument("--exiger-certification",action="store_true")
    opts=a.parse_args(argv)
    try:
        must(len(opts.fiche)<=20,"TROP_DE_FICHES")
        l,cfg,nb,nd=sources()
        examined=[]
        ids=set()
        dedupe=set()
        for path in opts.fiche:
            x=examiner(load(path),l,cfg)
            must(x["id"] not in ids,"ID_DOUBLE")
            must(x["dedoublonnage"] not in dedupe,"POSTE_DOUBLE")
            ids.add(x["id"])
            dedupe.add(x["dedoublonnage"])
            examined.append(x)
        if opts.bilan:
            ecrire(opts.bilan,bilan(cfg,nb,nd,examined))
        if opts.registre:
            ecrire(opts.registre,{
                "schema_version":"P53M-REGISTRE-1",
                "statut":"A_DOCUMENTER_SANS_DONNEES_CERTIFIEES",
                "fiches":catalogue(cfg)})
        print(json.dumps(bilan(cfg,nb,nd,examined),ensure_ascii=False,sort_keys=True))
        return 3 if opts.exiger_certification else 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P53M_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
