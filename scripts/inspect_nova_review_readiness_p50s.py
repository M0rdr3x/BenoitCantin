#!/usr/bin/env python3
"""P50S: constat GitHub en lecture seule; jamais de GO, merge ou deploiement."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO="M0rdr3x/BenoitCantin"
MAIN="9ed5f70cbe7022f25a679346a1288701f3b09067"
PRS={
 636:("main","6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb"),
 638:("main","e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e"),
 655:("review/p49q-coherence-participation-2026-10-11","8541f761be8dbabda0c3f024f8969562ab816bc7"),
 657:("review/p50o-durcissement-validateur-pr636-2026-10-14","f67abe43b7223d0f59ee1efb6cf883d558eddfb5"),
 659:("main","363bafc8f07cee1d72e785e51d48fbec121bb574"),
}
EXCLUDED="332afe7d9d73390feb41b0deb588692f3c73d48d"
RUNS={
 "P50Q":("da055a22ca7616743070dafa6a8befcad3a6c470",
         "Projet Nova P50Q - validation 40 tests et comparaison 14 cas"),
 "P50R":("363bafc8f07cee1d72e785e51d48fbec121bb574",
         "Projet Nova P50R - integration ephemere sans fusion publique"),
}
PERMANENT=[
 "MANDAT_JURIDIQUE_NON_ATTESTE",
 "REVUE_HUMAINE_INDEPENDANTE_NON_ATTESTEE",
 "TRAITEMENT_COURRIEL_NON_AUDITE",
 "PLAN_RESTAURATION_NON_ATTESTE",
 "AUTORISATION_ELECTORALE_NON_ATTESTEE",
 "DECISION_PUBLICATION_NON_ATTESTEE",
 "PR640_NE_PAS_FUSIONNER",
]

def get(path,token):
    if not path.startswith("/repos/"+REPO+"/"):
        raise ValueError("CHEMIN_API_NON_AUTORISE")
    req=Request("https://api.github.com"+path,headers={
        "Authorization":"Bearer "+token,
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
        "User-Agent":"nova-p50s-read-only"})
    with urlopen(req,timeout=25) as reply:
        return json.load(reply)

def collect(token):
    root="/repos/"+REPO
    main=get(root+"/git/ref/heads/main",token)
    prs={}
    for n in (*PRS.keys(),640):
        p=get(root+f"/pulls/{n}",token)
        reviews=get(root+f"/pulls/{n}/reviews?per_page=100",token)
        requested=get(root+f"/pulls/{n}/requested_reviewers",token)
        if not isinstance(reviews,list) or len(reviews)>=100:
            raise ValueError("REVUES_PAGINATION_INCONNUE")
        prs[str(n)]={
            "state":p.get("state"),"draft":p.get("draft"),"merged":p.get("merged"),
            "head":(p.get("head") or {}).get("sha"),
            "base":(p.get("base") or {}).get("ref"),
            "author":(p.get("user") or {}).get("login",""),
            "reviews":[{
                "state":r.get("state"),"commit":r.get("commit_id"),
                "user":(r.get("user") or {}).get("login",""),
                "type":(r.get("user") or {}).get("type",""),
                "date":r.get("submitted_at") or "",
            } for r in reviews],
            "requests":len(requested.get("users",[]))+len(requested.get("teams",[])),
        }
    runs={}
    for key,(sha,name) in RUNS.items():
        obj=get(root+"/actions/runs?head_sha="+sha+"&event=pull_request&per_page=100",token)
        if obj.get("total_count",0)>100:
            raise ValueError("RUNS_PAGINATION_INCONNUE")
        matches=[r for r in obj.get("workflow_runs",[])
                 if r.get("head_sha")==sha and r.get("name")==name]
        runs[key]={
            "sha":sha,"name":name,
            "success":any(r.get("conclusion")=="success" and r.get("status")=="completed"
                          for r in matches)}
    return {"main":(main.get("object") or {}).get("sha"),"prs":prs,"runs":runs}

def approvals(p):
    """Le dernier verdict substantiel par personne, sur le SHA actuel seulement."""
    latest={}
    for r in p.get("reviews",[]):
        if not isinstance(r,dict):
            continue
        login=r.get("user")
        if not login or r.get("type")=="Bot" or login.casefold()==str(p.get("author","")).casefold():
            continue
        if r.get("state") in ("APPROVED","CHANGES_REQUESTED","DISMISSED"):
            date=str(r.get("date") or "")
            if login not in latest or date>=latest[login][0]:
                latest[login]=(date,r.get("state"),r.get("commit"))
    return sum(state=="APPROVED" and sha==p.get("head")
               for _,state,sha in latest.values())

def analyze(s):
    if not isinstance(s,dict):
        return {"structure":"INCONNUE","obstacles":["RELEVE_GITHUB_NON_DISPONIBLE",*PERMANENT],
                "decision":"NO_GO_AUTOMATIQUE"}
    problems=[]
    if s.get("main")!=MAIN:
        problems.append("MAIN_MODIFIE_REPRISE_OBLIGATOIRE")
    rows={}
    prs=s.get("prs") if isinstance(s.get("prs"),dict) else {}
    for n,(base,sha) in PRS.items():
        p=prs.get(str(n))
        if not isinstance(p,dict):
            problems.append(f"PR{n}_INACCESSIBLE")
            continue
        if p.get("state")!="open" or p.get("merged") is not False:
            problems.append(f"PR{n}_ETAT_MODIFIE")
        if p.get("draft") is not True:
            problems.append(f"PR{n}_PAS_EN_BROUILLON")
        if p.get("base")!=base or p.get("head")!=sha:
            problems.append(f"PR{n}_SHA_OU_BASE_CHANGE")
        a=approvals(p)
        req=p.get("requests")
        rows[str(n)]={"approbations_git_head":a,"demandes_en_attente":req,
                       "habilitation_humaine_attestee":False,
                       "etat":"REVUE_GITHUB_NON_OBSERVEE" if a==0 else
                              "APPROBATION_GITHUB_A_QUALIFIER"}
        if a==0:
            problems.append(f"PR{n}_REVUE_FORMELLE_ABSENTE")
            if req==0:
                problems.append(f"PR{n}_AUCUNE_DEMANDE_REVISEUR")
        if type(req) is not int or req<0:
            problems.append(f"PR{n}_DEMANDES_INDETERMINEES")
    p640=prs.get("640")
    if not isinstance(p640,dict) or p640.get("merged") is not False or p640.get("head")!=EXCLUDED:
        problems.append("PR640_VERROU_A_REVERIFIER")
    run_status={}
    for key,(sha,name) in RUNS.items():
        entry=(s.get("runs") or {}).get(key)
        ok=(isinstance(entry,dict) and entry.get("sha")==sha and
            entry.get("name")==name and entry.get("success") is True)
        run_status[key]="REUSSITE_CI_VERIFIEE_AU_SHA" if ok else "A_REVERIFIER"
        if not ok:
            problems.append("PREUVE_CI_INSUFFISANTE_"+key)
    problems.extend(PERMANENT)
    return {
        "jalon":"P50S","structure":"RELEVE_EFFECTUE",
        "revues":rows,"ci":run_status,
        "nombre_pr_sans_approbation_github":sum(x["approbations_git_head"]==0 for x in rows.values()),
        "obstacles":sorted(set(problems)),
        "signature_juridique_attestee":False,
        "autorisation_publication":False,
        "decision":"NO_GO_AUTOMATIQUE",
        "limite":"GitHub APPROVED ne constitue pas un mandat ni un avis juridique.",
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot",type=Path)
    parser.add_argument("--rapport",type=Path)
    opts=parser.parse_args(argv)
    try:
        if opts.snapshot:
            src=json.loads(opts.snapshot.read_text(encoding="utf-8"))
        else:
            token=os.environ.get("GITHUB_TOKEN")
            if not token:
                raise ValueError("JETON_ABSENT")
            src=collect(token)
        result=analyze(src)
    except (OSError,ValueError,HTTPError,URLError,TimeoutError) as e:
        result=analyze(None)
        result["erreur_type"]=type(e).__name__
    result["horodatage_utc"]=datetime.now(timezone.utc).isoformat()
    body=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if opts.rapport:
        opts.rapport.parent.mkdir(parents=True,exist_ok=True)
        opts.rapport.write_text(body,encoding="utf-8")
    else:
        print(body,end="")
    return 0 if result["structure"]=="RELEVE_EFFECTUE" else 2

if __name__=="__main__":
    raise SystemExit(main())
