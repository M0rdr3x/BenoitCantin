#!/usr/bin/env python3
"""P50V — Verifie une PROPOSITION DE RULESET, jamais son activation.

Tout le travail est local et read-only. Le ruleset source est disabled.
Les checks globaux doivent etre emis par des workflows non filtres par paths.
La validation n'accorde pas le pouvoir d'administrer, fusionner ou publier.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SPEC=Path("projets/projet-nova/controles/P50V_CANDIDAT_RULESET_MAIN_DESACTIVE.json")
SOURCES={
 "no-committed-secrets":(
     ".github/workflows/sinjira-secret-guard.yml",
     "98eb5c9c0a06d76bc244434a278fe77532e24a32",
     "no-committed-secrets:"),
 "Contrat sécurité validation site":(
     ".github/workflows/validate-site.yml",
     "0104ce84b8b62d8ec1a03d59c9fe03422ca0c89c",
     "name: Contrat sécurité validation site"),
 "Contrat sécurité CI navigateur":(
     ".github/workflows/e2e-site.yml",
     "fd7792b0f5157e7bba89f39c86155fff606bab8b",
     "name: Contrat sécurité CI navigateur"),
}
EXPECTED_SHA="9ed5f70cbe7022f25a679346a1288701f3b09067"

def git_blob_sha(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()

def check_workflow(source:str,label:str)->list[str]:
    faults=[]
    if not isinstance(source,str):
        return ["WORKFLOW_ABSENT:"+label]
    header=source.split("\njobs:",1)[0]
    if "\njobs:" not in source:
        faults.append("JOBS_NON_TROUVES:"+label)
    if not re.search(r"(?m)^on:\s*$",header):
        faults.append("DECLENCHEUR_ON_ABSENT:"+label)
    if not re.search(r"(?m)^\s{2}pull_request:\s*$",header):
        faults.append("PR_GLOBALE_ABSENTE:"+label)
    # Explicit path filters would leave some PRs without this check.
    if re.search(r"(?m)^\s+(?:paths|paths-ignore):",header):
        faults.append("FILTRE_CHEMIN_INTERDIT:"+label)
    if re.search(r"(?m)^\s{4}branches:\s*(?:\[[^\]]*\]|.*)",header):
        lines=re.findall(r"(?m)^\s{4}branches:\s*([^\n]*)",header)
        if lines and not any("main" in line for line in lines):
            faults.append("BRANCHE_MAIN_NON_DECLENCHEE:"+label)
    if "pull_request_target:" in header:
        faults.append("PR_TARGET_SENSIBLE:"+label)
    expected=SOURCES.get(label)
    if expected and expected[2] not in source:
        faults.append("NOM_JOB_EXACT_ABSENT:"+label)
    return faults

def validate(spec:object,workflows:dict)->dict:
    problems=[]
    if not isinstance(spec,dict):
        return report(["REGLE_NON_LISIBLE"])
    if spec.get("target")!="branch":
        problems.append("CIBLE_NON_BRANCHE")
    if spec.get("enforcement")!="disabled":
        problems.append("ENFORCEMENT_DOIT_RESTER_DISABLED_DANS_DEPOT")
    if spec.get("bypass_actors")!=[]:
        problems.append("BYPASS_NON_AUTORISE_DANS_CANDIDAT")
    if spec.get("conditions")!={"ref_name":{"include":["refs/heads/main"],"exclude":[]}}:
        problems.append("CIBLE_MAIN_NON_EXCLUSIVE")
    rules=spec.get("rules")
    if not isinstance(rules,list) or len(rules)!=4:
        problems.append("QUATRE_REGLES_ATTENDUES")
        rules=[]
    names=[v.get("type") for v in rules if isinstance(v,dict)]
    if len(set(names))!=len(names) or set(names)!={"deletion","non_fast_forward",
                                                    "pull_request","required_status_checks"}:
        problems.append("REGLES_SECURITE_MANQUANTES_OU_INATTENDUES")
    byname={r.get("type"):r for r in rules if isinstance(r,dict)}
    for name in ("deletion","non_fast_forward"):
        if byname.get(name)!={"type":name}:
            problems.append("REGLE_INVALIDE:"+name)
    review=(byname.get("pull_request") or {}).get("parameters") or {}
    if not isinstance(review,dict):
        review={}
    expected={
        "dismiss_stale_reviews_on_push":True,
        "require_code_owner_review":False,
        "require_last_push_approval":True,
        "required_approving_review_count":1,
        "required_review_thread_resolution":True,
        "allowed_merge_methods":["merge","squash"],
    }
    for k,v in expected.items():
        if review.get(k)!=v:
            problems.append("PARAMETRE_REVUE_INCORRECT:"+k)
    checks=(byname.get("required_status_checks") or {}).get("parameters") or {}
    if not isinstance(checks,dict):
        checks={}
    if checks.get("strict_required_status_checks_policy") is not True:
        problems.append("CHECKS_STRICT_NON_ACTIFS")
    items=checks.get("required_status_checks")
    expected_names=set(SOURCES)
    if (not isinstance(items,list) or len(items)!=len(expected_names) or
        {x.get("context") for x in items if isinstance(x,dict)}!=expected_names):
        problems.append("TROIS_CHECKS_UNIVERSELS_EXACTS_MANQUANTS")
    elif any(set(x)!={"context","integration_id"} or
             x.get("integration_id")!=15368 for x in items if isinstance(x,dict)):
        problems.append("APP_GITHUB_ACTIONS_REQUISE")
    for label,(path,sha,job_name) in SOURCES.items():
        data=workflows.get(path)
        if data is None:
            problems.append("WORKFLOW_SOURCE_INDISPONIBLE:"+label)
            continue
        if not isinstance(data,bytes):
            problems.append("WORKFLOW_SOURCE_NON_OCTETS:"+label)
            continue
        if git_blob_sha(data)!=sha:
            problems.append("WORKFLOW_SOURCE_SHA_MODIFIE:"+label)
        try:
            problems.extend(check_workflow(data.decode("utf-8"),label))
        except UnicodeError:
            problems.append("WORKFLOW_SOURCE_UTF8_INVALIDE:"+label)
    return report(problems)

def report(problems):
    return {
        "jalon":"P50V",
        "validation_du_candidat":"CANDIDAT_CONFORME_EN_LECTURE_SEULE" if not problems else
                                "CANDIDAT_BLOQUE",
        "anomalies":sorted(set(problems)),
        "commit_main_reference":EXPECTED_SHA,
        "checks_candidate_count":len(SOURCES),
        "activateur_obligatoire":"ADMINISTRATEUR_HABILITE",
        "tests_preventifs_de_blocage_non_effectues":True,
        "ruleset_installe":False,
        "revue_independante_juridiquement_attestee":False,
        "publication_autorisee":False,
        "fusion_autorisee":False,
        "decision":"NO_GO_AUTOMATIQUE",
        "limite":"Le JSON du depot est un modele DESACTIVE, pas une regle serveur en vigueur."
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--output",type=Path)
    args=p.parse_args(argv)
    specfile=args.root/SPEC
    try:
        obj=json.loads(specfile.read_text("utf-8"))
    except (OSError,UnicodeError,ValueError):
        obj=None
    sources={}
    for path,_,_ in SOURCES.values():
        try:sources[path]=(args.root/path).read_bytes()
        except OSError:sources[path]=None
    result=validate(obj,sources)
    body=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(body,"utf-8")
    else:
        print(body,end="")
    return 0 if result["validation_du_candidat"]=="CANDIDAT_CONFORME_EN_LECTURE_SEULE" else 2

if __name__=="__main__":
    sys.exit(main())
