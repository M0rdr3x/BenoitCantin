#!/usr/bin/env python3
"""P50U — Audit read-only de la protection preventive de main.

Le controle ne modifie ni branches, ni rulesets, ni revues. Les informations
d'administration NON accessibles ne sont jamais declarees comme configurees.
Une protection GitHub ne constitue pas une autorisation institutionnelle.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO="M0rdr3x/BenoitCantin"
EXPECTED_MAIN="9ed5f70cbe7022f25a679346a1288701f3b09067"

def owners_from_codeowners(content):
    """Compter les comptes explicitement annonces, sans identifier les personnes."""
    if not isinstance(content,str):
        return None
    result=set()
    for line in content.splitlines():
        line=line.split("#",1)[0].strip()
        parts=line.split()
        if len(parts)<2:
            continue
        if parts[0]=="*":
            result.update(x for x in parts[1:] if x.startswith("@"))
    return len(result)

def evaluate(branch, rulesets, codeowners):
    problems=[]
    if not isinstance(branch,dict):
        problems.append("BRANCHE_MAIN_NON_LISIBLE")
        branch={}
    sha=(branch.get("commit") or {}).get("sha") if isinstance(branch.get("commit"),dict) else None
    if sha!=EXPECTED_MAIN:
        problems.append("HEAD_MAIN_CHANGE_REEXAMEN")
    protected=branch.get("protected")
    protection=branch.get("protection")
    if protected is not True:
        problems.append("MAIN_NON_PROTEGEE_OU_ETAT_INCONNU")
    if not isinstance(protection,dict):
        problems.append("DETAIL_PROTECTION_NON_LISIBLE")
        protection={}
    requirements=protection.get("required_status_checks")
    if not isinstance(requirements,dict):
        requirements={}
        problems.append("CHECKS_REQUIS_INCONNUS")
    checks=requirements.get("checks")
    contexts=requirements.get("contexts")
    if not isinstance(checks,list) or not isinstance(contexts,list):
        problems.append("LISTE_CHECKS_NON_LISIBLE")
        checks=[]
        contexts=[]
    required_count=len({str(x.get("context")) for x in checks if isinstance(x,dict) and x.get("context")}) + len(set(contexts))
    if required_count==0:
        problems.append("AUCUN_CHECK_OBLIGATOIRE")
    enforcement=requirements.get("enforcement_level")
    if enforcement in ("off",None):
        problems.append("ENFORCEMENT_CHECKS_DESACTIVE_OU_INCONNU")
    if not isinstance(rulesets,list):
        problems.append("RULESETS_NON_LISIBLES")
        rulesets=[]
    active_rulesets=sum(1 for r in rulesets if isinstance(r,dict) and r.get("enforcement")=="active")
    if protected is False and active_rulesets==0:
        problems.append("AUCUNE_PROTECTION_PREVENTIVE_OBSERVEE")
    owner_count=owners_from_codeowners(codeowners)
    if owner_count is None:
        problems.append("CODEOWNERS_NON_LISIBLE")
    elif owner_count<=1:
        problems.append("CODEOWNERS_NE_GARANTIT_PAS_REVUE_INDEPENDANTE")
    return {
        "jalon":"P50U",
        "main_sha_observe":sha,
        "main_sha_reference":EXPECTED_MAIN,
        "main_protegee":protected if type(protected) is bool else "INCONNU",
        "checks_requis_observes":required_count,
        "regles_actives_observees":active_rulesets,
        "codeowners_noms_non_publies":True,
        "codeowners_comptes":owner_count if owner_count is not None else "INCONNU",
        "etat_porte_technique":"PROTECTION_CONFIRME_E_SUR_SURFACE_LUE" if not problems else "BLOQUANT",
        "obstacles":sorted(set(problems)),
        "revue_humaine_qualifiee_attestee":False,
        "mandat_institutionnel_atteste":False,
        "autorisation_fusion":False,
        "autorisation_publication":False,
        "decision":"NO_GO_AUTOMATIQUE",
        "limite":"Les champs GitHub accessibles ne prouvent pas l'independance ni l'habilitation d'un reviewer.",
    }

def read_api(path,token):
    if not path.startswith("/repos/"+REPO+"/"):
        raise ValueError("ENDPOINT_INTERDIT")
    headers={"Accept":"application/vnd.github+json",
             "User-Agent":"nova-p50u-main-protection-audit",
             "X-GitHub-Api-Version":"2022-11-28"}
    if token:
        headers["Authorization"]="Bearer "+token
    with urlopen(Request("https://api.github.com"+path,headers=headers),timeout=30) as reply:
        return json.load(reply)

def collect(token):
    root="/repos/"+REPO
    return {"branch":read_api(root+"/branches/main",token),
            "rulesets":read_api(root+"/rulesets?includes_parents=true",token)}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot",type=Path,help="Rejeu test hors reseau")
    p.add_argument("--codeowners",type=Path,required=True)
    p.add_argument("--rapport",type=Path)
    p.add_argument("--exiger-protection",action="store_true")
    args=p.parse_args(argv)
    try:
        info=json.loads(args.snapshot.read_text("utf-8")) if args.snapshot else collect(
            os.environ.get("GITHUB_TOKEN",""))
        ownership=args.codeowners.read_text("utf-8")
        report=evaluate(info.get("branch"),info.get("rulesets"),ownership)
    except (OSError,ValueError,UnicodeError,HTTPError,URLError,TimeoutError,
            json.JSONDecodeError,AttributeError) as error:
        report=evaluate(None,None,None)
        report["erreur_type"]=type(error).__name__
    report["releve_utc"]=datetime.now(timezone.utc).isoformat()
    result=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True,exist_ok=True)
        args.rapport.write_text(result,"utf-8")
    else:
        print(result,end="")
    if "BRANCHE_MAIN_NON_LISIBLE" in report["obstacles"]:
        return 2
    if args.exiger_protection and report["etat_porte_technique"]=="BLOQUANT":
        print("P50U_GARDE_SERVEUR_MANQUANTE",file=sys.stderr)
        return 3
    return 0

if __name__=="__main__":
    raise SystemExit(main())
