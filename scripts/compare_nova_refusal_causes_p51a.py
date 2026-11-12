#!/usr/bin/env python3
"""P51A: compare preuves de motifs faux au SHA PR668 et au SHA PR670.

Un test offline prouve que les fausses explications de refus etaient considerees
recevables par P50Z et ne le sont plus par P51A. Ce n'est pas un test de merge
ou une attestation de protection serveur active.
"""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
from pathlib import Path

OLD="9e8d08b2a4d097e9609320cef5e9167ab3fe64bf"
NEW="a39056723f21d7b50416e57b616558ecc0f3f585"
REPO="M0rdr3x/BenoitCantin"
CASES=("sans_revue","approbation_perimee","check_non_satisfait")

def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise ValueError("SCRIPT_INDISPONIBLE")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def fixture():
    rows=[]
    observations={}
    for i,case in enumerate(CASES):
        n=920+i
        sha=str(i+1)*40
        rows.append({
            "id":case,"pr_number":n,"head_sha":sha,
            "pr_url":f"https://github.com/{REPO}/pull/{n}",
            "preuve_url":f"https://github.com/{REPO}/pull/{n}",
            "blocage_constate":True,"verification_humaine":True,
        })
        observations[str(n)]={
            "head_sha":sha,"open":True,"draft":False,"merged":False,
            "mergeable":True,"mergeable_state":"blocked",
            "base_ref":"main","base_repo":REPO,"head_repo":REPO,
            "head_ref":"test/p50y-"+case+"-essai",
            "title":"[P50Y-CANARI:"+case+"] Essai fictif",
            "changed_paths":["projets/projet-nova/controles/canaris/"+case+".txt"],
            "review_stats":{
                "submitted_substantive":0 if case=="sans_revue" else 1,
                "fresh_independent_approvals":1 if case=="check_non_satisfait" else 0,
                "prior_independent_approval_observed":case=="approbation_perimee",
            },
            "check_stats":{
                "checks_success":2 if case=="check_non_satisfait" else 3,
                "checks_non_satisfaits":1 if case=="check_non_satisfait" else 0,
            },
        }
    document={
        "schema_version":"P50Y-1",
        "main_sha_avant_essai":"9ed5f70cbe7022f25a679346a1288701f3b09067",
        "protection_serveur_confirmee_par_admin":True,
        "bypass_et_permissions_examines":True,
        "relecteur_independant_disponible":True,
        "cas":rows,"decision":"NO_GO"
    }
    return document,observations

def compare(old,new):
    doc,base=fixture()
    valid=new.analyze(doc,base)
    if valid["statut_dossier"]!="DECLARATIONS_COMPLETEES_A_VALIDER_EXTERNEMENT":
        raise AssertionError("UN_CANARI_LEGITIME_FICTIF_REJETE")
    if valid["decision"]!="NO_GO_AUTOMATIQUE":
        raise AssertionError("GO_ILLICITE")
    probes=[
        ("sans_revue_mais_check_rouge","920","check_stats","checks_success",2,
         "checks_non_satisfaits",1),
        ("approbation_perimee_sans_historique","921","review_stats",
         "prior_independent_approval_observed",False,None,None),
        ("approbation_perimee_encore_valide","921","review_stats",
         "fresh_independent_approvals",1,None,None),
        ("check_rouge_sans_approbation","922","review_stats",
         "fresh_independent_approvals",0,None,None),
        ("check_pretendu_non_satisfait_mais_vert","922","check_stats",
         "checks_success",3,"checks_non_satisfaits",0),
        ("absence_totale_preuve_API","920","review_stats",None,None,None,None),
    ]
    results=[]
    for label,number,section,k,v,k2,v2 in probes:
        doc,obs=fixture()
        if k is None:
            del obs[number][section]
        else:
            obs[number][section][k]=v
            if k2 is not None:
                obs[number][section][k2]=v2
        before=old.analyze(doc,obs)
        after=new.analyze(doc,obs)
        if before["statut_dossier"]!="DECLARATIONS_COMPLETEES_A_VALIDER_EXTERNEMENT":
            raise AssertionError("FAILLE_INITIALE_NON_REPRODUITE:"+label)
        if after["statut_dossier"]!="RECETTE_REQUISE":
            raise AssertionError("CONTROLE_CORRIGE_N_A_PAS_REJETE:"+label)
        if not any(t.startswith(("OBSERVATIONS_NE_SOUTIENNENT_","REVUES_OU_CHECKS_NON_"))
                   for t in after["obstacles"]):
            raise AssertionError("MOTIF_NON_DOCUMENTE:"+label)
        if before["decision"]!="NO_GO_AUTOMATIQUE" or after["decision"]!="NO_GO_AUTOMATIQUE":
            raise AssertionError("GO_ILLICITE:"+label)
        results.append(label)
    return {
        "jalon":"P51A",
        "ancien_sha":OLD,
        "corrige_sha":NEW,
        "nombre_sondes":len(results),
        "motifs_trompeurs_acceptes_avant":len(results),
        "motifs_trompeurs_acceptes_apres":0,
        "sondes":results,
        "scenario_valide_toujours_reconnu":True,
        "essai_GitHub_reel":False,
        "protection_serveur_attestee":False,
        "fusion_autorisee":False,
        "publication_autorisee":False,
        "decision":"NO_GO_AUTOMATIQUE",
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--avant",type=Path,required=True)
    ap.add_argument("--apres",type=Path,required=True)
    ap.add_argument("--rapport",type=Path)
    a=ap.parse_args()
    result=compare(load(a.avant,"p50z_previous"),load(a.apres,"p51a_fixed"))
    body=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if a.rapport:
        a.rapport.parent.mkdir(parents=True,exist_ok=True)
        a.rapport.write_text(body,encoding="utf-8")
    else:
        print(body,end="")
    print("P51A: motifs non corroborés correctement rejetés:",result["nombre_sondes"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
