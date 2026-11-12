#!/usr/bin/env python3
"""Projet Nova P50X: constate les règles serveur ACTIVES, sans les modifier.

Lit trois surfaces GitHub distinctes : /branches/main, /rulesets et
/rules/branches/main (règles EFFECTIVES). Un refus 403/404 sur la dernière
surface bloque toute certification au lieu de supposer la protection en place.
Les bypass_actors peuvent être masqués aux lecteurs non administrateurs.
Aucune fusion, création de PR ou modification de GitHub n'est effectuée.
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
MAIN_SHA="9ed5f70cbe7022f25a679346a1288701f3b09067"
REQUIRED_CHECKS={
    ("no-committed-secrets",15368),
    ("Contrat sécurité validation site",15368),
    ("Contrat sécurité CI navigateur",15368),
}

def get(path,token):
    if not path.startswith("/repos/"+REPO+"/"):
        raise ValueError("API_HORS_DEPOT")
    headers={
        "Accept":"application/vnd.github+json",
        "User-Agent":"nova-p50x-observer-read-only",
        "X-GitHub-Api-Version":"2022-11-28",
    }
    if token:
        headers["Authorization"]="Bearer "+token
    with urlopen(Request("https://api.github.com"+path,headers=headers),timeout=25) as resp:
        return json.load(resp)

def fetch_snapshot(token):
    base="/repos/"+REPO
    branch=get(base+"/branches/main",token)
    rulesets=get(base+"/rulesets?includes_parents=true&per_page=100",token)
    if not isinstance(rulesets,list) or len(rulesets)>=100:
        raise ValueError("PAGINATION_RULESETS_A_VERIFIER")
    details=[]
    for item in rulesets:
        if not isinstance(item,dict):
            raise ValueError("RULESET_NON_FIABLE")
        if item.get("enforcement")=="active":
            rid=item.get("id")
            if type(rid) is not int or rid<=0:
                raise ValueError("IDENTIFIANT_RULESET_INVALIDE")
            details.append(get(base+"/rulesets/"+str(rid),token))
    effective=None
    effective_access="CONSULTABLE"
    try:
        effective=get(base+"/rules/branches/main?per_page=100",token)
        if not isinstance(effective,list) or len(effective)>=100:
            effective=None
            effective_access="PAGINATION_OU_REPONSE_NON_FIABLE"
    except (HTTPError,URLError,TimeoutError,ValueError):
        effective_access="NON_ACCESSIBLE_A_CETTE_INTEGRATION"
    return {"branch":branch,"rulesets":rulesets,"details":details,
            "effective":effective,"effective_access":effective_access}

def evaluate(data,candidate):
    issues=[]
    if not isinstance(candidate,dict):
        issues.append("CANDIDAT_P50V_NON_LISIBLE")
        candidate={}
    if candidate.get("enforcement")!="disabled":
        issues.append("CANDIDAT_DOIT_RESTER_DESACTIVE")
    if not isinstance(data,dict):
        data={}
        issues.append("DONNEES_GITHUB_INACCESSIBLES")
    branch=data.get("branch")
    if not isinstance(branch,dict):
        branch={}
        issues.append("BRANCHE_NON_LISIBLE")
    sha=(branch.get("commit") or {}).get("sha")
    if sha!=MAIN_SHA:
        issues.append("MAIN_A_CHANGE_RELANCER_VALIDATIONS")
    if branch.get("protected") is not True:
        issues.append("MAIN_NON_PROTEGEE_OU_INCONNUE")
    summaries=data.get("rulesets")
    if not isinstance(summaries,list):
        summaries=[]
        issues.append("LISTE_RULESETS_NON_LISIBLE")
    active=[r for r in summaries if isinstance(r,dict) and r.get("enforcement")=="active"]
    if not active:
        issues.append("AUCUN_RULESET_ACTIF")
    details=data.get("details")
    if not isinstance(details,list):
        details=[]
        issues.append("DETAILS_RULESET_NON_LISIBLES")
    selected=[x for x in details if isinstance(x,dict) and
              x.get("name")==candidate.get("name") and
              x.get("enforcement")=="active" and x.get("target")=="branch"]
    if len(selected)!=1:
        issues.append("RULESET_CANDIDAT_ACTIF_NON_OBSERVE_UNIQUEMENT")
    active_config=False
    bypass_state="INCONNU"
    if len(selected)==1:
        obj=selected[0]
        cond=obj.get("conditions")
        if cond!={"ref_name":{"include":["refs/heads/main"],"exclude":[]}}:
            issues.append("CONDITIONS_MAIN_DIFFERENTES")
        rules=obj.get("rules")
        if not isinstance(rules,list):
            rules=[]
            issues.append("REGLES_INSTALLEES_NON_LISIBLES")
        bytype={r.get("type"):r for r in rules if isinstance(r,dict)}
        if not {"deletion","non_fast_forward","pull_request","required_status_checks"}.issubset(bytype):
            issues.append("REGLES_PREVENTIVES_MANQUANTES")
        pull=(bytype.get("pull_request") or {}).get("parameters") or {}
        if (type(pull.get("required_approving_review_count")) is not int or
            pull.get("required_approving_review_count")<1 or
            pull.get("require_last_push_approval") is not True or
            pull.get("dismiss_stale_reviews_on_push") is not True or
            pull.get("required_review_thread_resolution") is not True):
            issues.append("REVUES_OBLIGATOIRES_NON_CONFIRMEES")
        params=(bytype.get("required_status_checks") or {}).get("parameters") or {}
        raw=params.get("required_status_checks")
        check_set=set()
        if isinstance(raw,list):
            for entry in raw:
                if isinstance(entry,dict) and isinstance(entry.get("context"),str):
                    check_set.add((entry["context"],entry.get("integration_id")))
        if not REQUIRED_CHECKS.issubset(check_set):
            issues.append("CHECKS_REQUIS_OU_APPLICATION_INCORRECTS")
        if params.get("strict_required_status_checks_policy") is not True:
            issues.append("CHECKS_STRICTS_NON_CONFIRMEES")
        actors=obj.get("bypass_actors","INCONNU")
        if actors==[]:
            bypass_state="AUCUN_BYPASS_DECLARÉ_DANS_LA_REPONSE"
        elif actors=="INCONNU":
            bypass_state="NON_DIVULGUE_PAR_API"
            issues.append("EXCEPTIONS_DE_CONTOURNEMENT_NON_AUDITABLES")
        else:
            bypass_state="PRESENT_OU_FORMAT_INCONNU"
            issues.append("EXCEPTIONS_DE_CONTOURNEMENT_A_REVOIR")
        active_config=not any(x in issues for x in (
            "CONDITIONS_MAIN_DIFFERENTES","REGLES_PREVENTIVES_MANQUANTES",
            "REGLES_INSTALLEES_NON_LISIBLES",
            "REVUES_OBLIGATOIRES_NON_CONFIRMEES",
            "CHECKS_REQUIS_OU_APPLICATION_INCORRECTS",
            "CHECKS_STRICTS_NON_CONFIRMEES"
        ))
    effective=data.get("effective")
    eff_access=data.get("effective_access")
    rule_types=set()
    if eff_access!="CONSULTABLE" or not isinstance(effective,list):
        issues.append("REGLES_EFFECTIVES_MAIN_NON_ATTESTEES")
    else:
        rule_types={r.get("type") for r in effective if isinstance(r,dict)}
        if not {"deletion","non_fast_forward","pull_request","required_status_checks"}.issubset(rule_types):
            issues.append("REGLES_EFFECTIVES_MAIN_INCOMPLETES")
    # An actual blocking outcome (unapproved PR, stale review, missing check)
    # requires separate administrator-run non-merged canary experiments.
    issues.append("RECETTE_BLOCAGE_SERVEUR_NON_EFFECTUEE")
    issues.append("REVUES_HUMAINES_ET_MANDATS_NON_ATTESTES")
    return {
        "jalon":"P50X",
        "main_sha_observe":sha,
        "main_protected_observe":branch.get("protected"),
        "rulesets_actifs":len(active),
        "ruleset_candidat_actif_et_parametres_compatibles":active_config,
        "exceptions_bypass":bypass_state,
        "regles_effectives_lisibles":eff_access=="CONSULTABLE" and isinstance(effective,list),
        "nb_types_regles_effectives":len(rule_types),
        "activation_effective_certifiee":False,
        "recette_serveur_verifiee":False,
        "habilitation_admin_attestee":False,
        "revues_independantes_attestees":False,
        "fusion_autorisee":False,
        "publication_autorisee":False,
        "decision":"NO_GO_AUTOMATIQUE",
        "obstacles":sorted(set(issues)),
        "limite":"Même avec un ruleset actif, un test non fusionné des refus et une vérification admin des bypass restent nécessaires.",
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate",type=Path,required=True)
    parser.add_argument("--snapshot",type=Path,help="Cas simulés; aucune requête externe")
    parser.add_argument("--result",type=Path)
    parser.add_argument("--exiger-protection",action="store_true")
    a=parser.parse_args(argv)
    try:
        candidate=json.loads(a.candidate.read_text("utf-8"))
        data=json.loads(a.snapshot.read_text("utf-8")) if a.snapshot else fetch_snapshot(
            os.environ.get("GITHUB_TOKEN",""))
        report=evaluate(data,candidate)
    except (OSError,ValueError,TypeError,AttributeError,UnicodeError,HTTPError,URLError,
            TimeoutError) as err:
        report=evaluate(None,None)
        report["erreur_type"]=type(err).__name__
    report["instant_utc"]=datetime.now(timezone.utc).isoformat()
    result=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if a.result:
        a.result.parent.mkdir(parents=True,exist_ok=True)
        a.result.write_text(result,encoding="utf-8")
    else:
        print(result,end="")
    if report["main_sha_observe"] is None:
        return 2
    if a.exiger_protection and (not report["ruleset_candidat_actif_et_parametres_compatibles"]
                               or report["exceptions_bypass"]!="AUCUN_BYPASS_DECLARÉ_DANS_LA_REPONSE"
                               or not report["regles_effectives_lisibles"]):
        print("P50X_PROTECTION_ACTIVEE_NON_ATTESTEE",file=sys.stderr)
        return 3
    return 0

if __name__=="__main__":
    sys.exit(main())
