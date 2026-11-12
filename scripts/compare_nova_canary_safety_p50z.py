#!/usr/bin/env python3
"""Preuve P50Z de regression adversariale entre PR667 et PR668.

Charge deux validateurs a leurs SHA immuables sur le runner; sans reseau, sans
PR test creee, sans mutation. Prouve que 8 faux canaris acceptes auparavant
ne sont plus recevables, et qu'un canari correctement isole reste seulement
une declaration a controler par l'administrateur, JAMAIS un GO.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import sys

REPO="M0rdr3x/BenoitCantin"
OLD_SHA="0945b7c76941bbde35bab926b4bfdda0442ae62b"
FIX_SHA="9e8d08b2a4d097e9609320cef5e9167ab3fe64bf"
CASES=("sans_revue","approbation_perimee","check_non_satisfait")
TEST_PATH="projets/projet-nova/controles/canaris/"

def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise ValueError("MODULE_NON_LISIBLE")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def scenario():
    rows=[]
    observed={}
    for i,key in enumerate(CASES):
        n=900+i
        sha=str(i+1)*40
        rows.append({
            "id":key,"pr_number":n,"head_sha":sha,
            "pr_url":f"https://github.com/{REPO}/pull/{n}",
            "blocage_constate":True,"verification_humaine":True,
            "preuve_url":f"https://github.com/{REPO}/pull/{n}",
        })
        observed[str(n)]={
            "head_sha":sha,"open":True,"draft":False,"merged":False,
            "mergeable":True,"mergeable_state":"blocked",
            "base_ref":"main","base_repo":REPO,
            "head_repo":REPO,"head_ref":f"test/p50y-{key}-essai",
            "title":f"[P50Y-CANARI:{key}] Test fictif",
            "changed_paths":[TEST_PATH+key+".txt"],
        }
    doc={
        "schema_version":"P50Y-1",
        "main_sha_avant_essai":"9ed5f70cbe7022f25a679346a1288701f3b09067",
        "protection_serveur_confirmee_par_admin":True,
        "bypass_et_permissions_examines":True,
        "relecteur_independant_disponible":True,
        "cas":rows,"decision":"NO_GO",
    }
    return doc,observed

def execute(old,new):
    doc,valid_obs=scenario()
    normal=new.analyze(doc,valid_obs)
    if normal["statut_dossier"]!="DECLARATIONS_COMPLETEES_A_VALIDER_EXTERNEMENT":
        raise AssertionError("CONTROLE_NEGATIF_REJETE_PAR_ERREUR")
    if normal["decision"]!="NO_GO_AUTOMATIQUE":
        raise AssertionError("GO_INTERDIT")
    controls=[
        ("autre_branche_cible","base_ref","not-main"),
        ("autre_depot_cible","base_repo","foreign/repo"),
        ("fork_source","head_repo","foreign/repo"),
        ("branche_de_vraie_pr","head_ref","review/p50y-real-code"),
        ("titre_non_canari","title","[P50Y] Une vraie PR"),
        ("mauvais_identifiant_titre","title","[P50Y-CANARI:check_non_satisfait] autre"),
        ("fichier_site_public","changed_paths",["projets/projet-nova/participer.html"]),
        ("liste_fichiers_vide","changed_paths",[]),
        ("trop_de_fichiers","changed_paths",[TEST_PATH+str(i)+".txt" for i in range(4)]),
    ]
    probes=[]
    for label,field,value in controls:
        document,obs=scenario()
        obs["900"][field]=value
        baseline=old.analyze(document,obs)
        fixed=new.analyze(document,obs)
        if baseline["statut_dossier"]!="DECLARATIONS_COMPLETEES_A_VALIDER_EXTERNEMENT":
            raise AssertionError("LA_FAILLE_INITIALE_N_EST_PAS_REPRODUITE:"+label)
        if fixed["statut_dossier"]!="RECETTE_REQUISE":
            raise AssertionError("CORRECTION_NON_DETECTEE:"+label)
        if not any(issue.startswith("CANARI_") for issue in fixed["obstacles"]):
            raise AssertionError("CAUSE_REJET_ABSENTE:"+label)
        if baseline["decision"]!="NO_GO_AUTOMATIQUE" or fixed["decision"]!="NO_GO_AUTOMATIQUE":
            raise AssertionError("GO_NON_AUTORISE:"+label)
        probes.append({"scenario":label,"ancien":"DECLARATIONS_COMPLETEES_A_VALIDER_EXTERNEMENT",
                       "corrige":"RECETTE_REQUISE"})
    return {
        "jalon":"P50Z",
        "avant_commit":OLD_SHA,"apres_commit":FIX_SHA,
        "tests_adversariaux":len(probes),
        "faux_canaris_rejetes_avant":0,
        "faux_canaris_rejetes_apres":len(probes),
        "controle_negatif_valide":True,
        "resultats":probes,
        "recette_admin_executee":False,
        "protection_main_modifiee":False,
        "validation_institutionnelle":False,
        "decision":"NO_GO_AUTOMATIQUE",
        "limite":"Comparaison sur des fixtures fictives, pas demonstration d'une protection GitHub reelle.",
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--avant",type=Path,required=True)
    parser.add_argument("--apres",type=Path,required=True)
    parser.add_argument("--rapport",type=Path)
    args=parser.parse_args(argv)
    report=execute(load(args.avant,"p50y_old"),load(args.apres,"p50z_fixed"))
    output=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True,exist_ok=True)
        args.rapport.write_text(output,encoding="utf-8")
    else:
        print(output,end="")
    print("P50Z : faux canaris acceptes avant =",len(report["resultats"]),file=sys.stderr)
    print("P50Z : faux canaris acceptes apres = 0; NO_GO conserve",file=sys.stderr)
    return 0

if __name__=="__main__":
    sys.exit(main())
