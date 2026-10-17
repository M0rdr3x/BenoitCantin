#!/usr/bin/env python3
"""P50W — Précontrôle read-only d'un ruleset GitHub AVANT activation.

Lit les contrôles sur des commits figés, l'état de main et des PR prioritaires.
Aucune API POST/PATCH/PUT/DELETE, aucun accès à la messagerie, aucun GO.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

REPO="M0rdr3x/BenoitCantin"
EXPECTED_MAIN="9ed5f70cbe7022f25a679346a1288701f3b09067"
SAMPLES={
    636:"6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb",
    638:"e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e",
    664:"d8acb58c2829cf990d7c77614b3f640369fdbdca",
}
PRIORITY={
    657:"f67abe43b7223d0f59ee1efb6cf883d558eddfb5",
    638:"e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e",
}
CHECKS=(
    "no-committed-secrets",
    "Contrat sécurité validation site",
    "Contrat sécurité CI navigateur",
)
APP_ID=15368

def api(path, token):
    if not path.startswith("/repos/"+REPO+"/"):
        raise ValueError("API_HORS_DEPOT")
    headers={"User-Agent":"nova-p50w-readonly",
             "Accept":"application/vnd.github+json",
             "X-GitHub-Api-Version":"2022-11-28"}
    if token:
        headers["Authorization"]="Bearer "+token
    with urlopen(Request("https://api.github.com"+path,headers=headers),timeout=25) as f:
        return json.load(f)

def collect(token):
    prefix="/repos/"+REPO
    branch=api(prefix+"/branches/main",token)
    repo=api(prefix,token) if False else None
    # The repository root endpoint is /repos/OWNER/REPO (no trailing slash)
    # and is queried separately as a special read-only resource below.
    rulesets=api(prefix+"/rulesets?includes_parents=true",token)
    pulls={}
    for number in sorted(set(SAMPLES)|set(PRIORITY)):
        p=api(prefix+f"/pulls/{number}",token)
        pulls[str(number)]={
            "head":(p.get("head") or {}).get("sha"),
            "state":p.get("state"),
            "draft":p.get("draft"),
            "merged":p.get("merged"),
        }
    for number in PRIORITY:
        reviews=api(prefix+f"/pulls/{number}/reviews?per_page=100",token)
        requested=api(prefix+f"/pulls/{number}/requested_reviewers",token)
        if not isinstance(reviews,list) or len(reviews)>=100 or not isinstance(requested,dict):
            raise ValueError("REVIEWS_PAGINATION_OR_FORMAT_UNKNOWN")
        pulls[str(number)]["submitted_review_count"]=len(reviews)
        pulls[str(number)]["review_requests"]=len(requested.get("users",[]))+len(requested.get("teams",[]))
    checkruns={}
    for number,sha in SAMPLES.items():
        payload=api(prefix+f"/commits/{sha}/check-runs?per_page=100",token)
        if payload.get("total_count",0)>100 or not isinstance(payload.get("check_runs"),list):
            raise ValueError("CHECK_RUNS_PAGINATION_OR_FORMAT_UNKNOWN")
        checkruns[str(number)]=[{
            "name":r.get("name"),
            "status":r.get("status"),
            "conclusion":r.get("conclusion"),
            "app_id":(r.get("app") or {}).get("id"),
            "head_sha":r.get("head_sha"),
        } for r in payload["check_runs"]]
    return {"main_branch":branch,"rulesets":rulesets,"prs":pulls,"check_runs":checkruns}

def ruleset_checks(candidate):
    issues=[]
    if not isinstance(candidate,dict):
        return ["CANDIDAT_INACCESSIBLE"]
    if candidate.get("enforcement")!="disabled":
        issues.append("CANDIDAT_DEVRAIT_RESTER_DESACTIVE")
    if candidate.get("target")!="branch":
        issues.append("CIBLE_CANDIDAT_NON_BRANCHE")
    if candidate.get("conditions")!={"ref_name":{"include":["refs/heads/main"],"exclude":[]}}:
        issues.append("CIBLE_MAIN_NOM_NON_UNIQUE")
    if candidate.get("bypass_actors")!=[]:
        issues.append("BYPASS_CANDIDAT_PRESENT")
    if not isinstance(candidate.get("rules"),list):
        return issues+["CANDIDAT_REGLES_ABSENTES"]
    rules={r.get("type"):r for r in candidate["rules"] if isinstance(r,dict)}
    required=(rules.get("required_status_checks") or {}).get("parameters") or {}
    items=required.get("required_status_checks")
    if (not isinstance(items,list) or len(items)!=3 or
        {x.get("context") for x in items if isinstance(x,dict)}!=set(CHECKS) or
        any(x.get("integration_id")!=APP_ID for x in items if isinstance(x,dict))):
        issues.append("CONTEXTES_CANDIDATS_NON_CONFORMES")
    if required.get("strict_required_status_checks_policy") is not True:
        issues.append("POLITIQUE_CHECKS_STRICT_ABSENTE")
    pr=(rules.get("pull_request") or {}).get("parameters") or {}
    if (pr.get("required_approving_review_count",0)<1 or
        pr.get("require_last_push_approval") is not True or
        pr.get("dismiss_stale_reviews_on_push") is not True):
        issues.append("REVUES_EXIGEES_NON_CONFORMES")
    if set(rules)!={"required_status_checks","pull_request","deletion","non_fast_forward"}:
        issues.append("QUATRE_REGLES_ATTENDUES")
    return issues

def analyze(snapshot,candidate):
    problems=ruleset_checks(candidate)
    if not isinstance(snapshot,dict):
        return report(["RELEVE_INCONNU",*problems],0,0,0,False,False)
    branch=snapshot.get("main_branch")
    if not isinstance(branch,dict):
        return report(["MAIN_NON_LISIBLE",*problems],0,0,0,False,False)
    sha=(branch.get("commit") or {}).get("sha")
    main_matches=sha==EXPECTED_MAIN
    if not main_matches:
        problems.append("MAIN_SHA_A_REVALIDER")
    main_unprotected=branch.get("protected") is False
    if main_unprotected:
        problems.append("MAIN_NON_PROTEGEE")
    if branch.get("protected") is not True and not main_unprotected:
        problems.append("MAIN_PROTECTION_INCONNUE")
    rulesets=snapshot.get("rulesets")
    if not isinstance(rulesets,list):
        problems.append("RULESETS_INCONNUS")
        rulesets=[]
    active=sum(isinstance(x,dict) and x.get("enforcement")=="active" for x in rulesets)
    if not active:
        problems.append("AUCUN_RULESET_ACTIF")
    pulls=snapshot.get("prs")
    if not isinstance(pulls,dict):
        pulls={}
        problems.append("ETAT_PR_INCONNU")
    exact=0
    for number,expected in {**SAMPLES,**PRIORITY}.items():
        p=pulls.get(str(number))
        if isinstance(p,dict) and p.get("head")==expected and p.get("state")=="open" and p.get("draft") is True and p.get("merged") is False:
            exact+=1
        else:
            problems.append(f"PR{number}_SHA_OU_ETAT_CHANGE")
    reviewer_requests=0
    for number in PRIORITY:
        p=pulls.get(str(number)) or {}
        count=p.get("review_requests")
        if type(count) is not int or count<0:
            problems.append(f"PR{number}_DEMANDES_REVUES_INCONNUES")
        elif count==0:
            problems.append(f"PR{number}_AUCUNE_REVUE_DEMANDEE")
        else:
            reviewer_requests+=count
        reviews=p.get("submitted_review_count")
        if type(reviews) is not int or reviews<0:
            problems.append(f"PR{number}_REVUES_FORMELLES_INCONNUES")
        elif reviews==0:
            problems.append(f"PR{number}_REVUE_FORMELLE_ABSENTE")
    all_checks=snapshot.get("check_runs")
    if not isinstance(all_checks,dict):
        all_checks={}
        problems.append("PREUVES_CHECKS_INCONNUES")
    check_success=0
    for n,expected in SAMPLES.items():
        rows=all_checks.get(str(n))
        if not isinstance(rows,list):
            problems.append(f"PR{n}_CHECKRUNS_INCONNUS")
            continue
        for label in CHECKS:
            matching=[r for r in rows if isinstance(r,dict) and r.get("name")==label and
                      r.get("head_sha")==expected and r.get("app_id")==APP_ID and
                      r.get("status")=="completed" and r.get("conclusion")=="success"]
            if len(matching)==1:
                check_success+=1
            else:
                problems.append(f"PR{n}_CHECK_MANQUANT_OU_AMBIGU:{label}")
    # 9 successes are a preflight evidence only, not a server protection.
    technical=check_success==9 and exact==len(set(SAMPLES)|set(PRIORITY)) and main_matches and not ruleset_checks(candidate)
    return report(problems,check_success,len(SAMPLES)*len(CHECKS),exact,technical,main_unprotected,reviewer_requests)

def report(problems,success,total,exact,technical,main_unprotected,requests=0):
    return {
        "jalon":"P50W",
        "controle":"PREFLIGHT_ADMIN_LECTURE_SEULE",
        "checks_attendus":total,
        "checks_reussis_sur_sha":success,
        "prs_au_sha_attendu":exact,
        "pr_cibles_distinctes":len(set(SAMPLES)|set(PRIORITY)),
        "requetes_revues_prioritaires":requests,
        "compatibilite_technique_echantillon":"CONFIRMEE" if technical else "INCONCLUSIVE",
        "main_non_protegee_observee":main_unprotected,
        "obstacles":sorted(set(problems)),
        "ruleset_installe_par_ce_controle":False,
        "protection_serveur_validée":False,
        "revue_independante_attestee":False,
        "habilitation_administrateur_attestee":False,
        "autorisation_fusion":False,
        "autorisation_publication":False,
        "decision":"NO_GO_AUTOMATIQUE",
        "limite":"L'echantillon 3 PR ne garantit pas les checks futurs. L'activation require un administrateur et un test serveur.",
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot",type=Path)
    parser.add_argument("--candidate",type=Path,required=True)
    parser.add_argument("--report",type=Path)
    args=parser.parse_args(argv)
    try:
        candidate=json.loads(args.candidate.read_text("utf-8"))
        data=json.loads(args.snapshot.read_text("utf-8")) if args.snapshot else collect(os.environ.get("GITHUB_TOKEN",""))
        r=analyze(data,candidate)
    except (OSError,ValueError,UnicodeError,TypeError,AttributeError,KeyError,
            HTTPError,URLError,TimeoutError) as err:
        r=analyze(None,None)
        r["erreur_type"]=type(err).__name__
    r["horodatage_utc"]=datetime.now(timezone.utc).isoformat()
    output=json.dumps(r,ensure_ascii=False,indent=2)+"\n"
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(output,encoding="utf-8")
    else:
        print(output,end="")
    return 0 if "RELEVE_INCONNU" not in r["obstacles"] and "CANDIDAT_INACCESSIBLE" not in r["obstacles"] else 2

if __name__=="__main__":
    sys.exit(main())
