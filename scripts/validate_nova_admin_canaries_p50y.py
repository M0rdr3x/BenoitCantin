#!/usr/bin/env python3
"""P50Y - Qualité du dossier de recette serveur, jamais une autorisation.

AUCUN write GitHub; le mode --live ne fait que des GET de PR et de reviews.
Les trois essais sont des PR temoins non fusionnees, faites par un mainteneur.
Un mergeable_state 'blocked' ne prouve pas A LUI SEUL la cause du blocage:
la decision reste necessairement NO_GO_AUTOMATIQUE.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO = "M0rdr3x/BenoitCantin"
MAIN_SHA = "9ed5f70cbe7022f25a679346a1288701f3b09067"
CASES = ("sans_revue", "approbation_perimee", "check_non_satisfait")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_URL = re.compile(
    r"^https://github\.com/M0rdr3x/BenoitCantin/"
    r"(?:pull/[1-9][0-9]*|actions/runs/[1-9][0-9]*)$"
)
def github(path: str, token: str):
    if not path.startswith("/repos/" + REPO + "/"):
        raise ValueError("CHEMIN_GITHUB_INTERDIT")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "projet-nova-p50y-lecture-seule",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    with urlopen(Request("https://api.github.com" + path, headers=headers),
                 timeout=25) as response:
        return json.load(response)

def actual_canary(number: int, token: str):
    base = "/repos/" + REPO
    pr = github(base + "/pulls/" + str(number), token)
    # True / False are not review decisions. A draft cannot demonstrate a
    # review or check gate because drafts are inherently not mergeable.
    result = {
        "head_sha": (pr.get("head") or {}).get("sha"),
        "open": pr.get("state") == "open",
        "draft": pr.get("draft"),
        "merged": pr.get("merged"),
        "mergeable": pr.get("mergeable"),
        "mergeable_state": pr.get("mergeable_state"),
    }
    return result

def analyze(document, observations=None):
    problems = []
    stages = {}
    if not isinstance(document, dict):
        document = {}
        problems.append("DOSSIER_NON_LISIBLE")
    if document.get("schema_version") != "P50Y-1":
        problems.append("SCHEMA_INATTENDU")
    if document.get("main_sha_avant_essai") != MAIN_SHA:
        problems.append("SHA_MAIN_REFERENCE_A_ACTUALISER")
    if document.get("decision") != "NO_GO":
        problems.append("DOCUMENT_NE_DOIT_PAS_DECLARER_GO")
    for k in ("protection_serveur_confirmee_par_admin",
              "bypass_et_permissions_examines",
              "relecteur_independant_disponible"):
        if type(document.get(k)) is not bool:
            problems.append("ATTESTATION_NON_BOOLEENNE:" + k)
    items = document.get("cas")
    if not isinstance(items, list):
        items = []
        problems.append("CAS_NON_LISIBLES")
    ids = [i.get("id") for i in items if isinstance(i, dict)]
    if len(items) != len(CASES) or sorted(ids) != sorted(CASES):
        problems.append("TROIS_CAS_UNIQUES_REQUIS")
    for caseid in CASES:
        matches = [v for v in items if isinstance(v, dict) and v.get("id") == caseid]
        if len(matches) != 1:
            stages[caseid] = "NON_EVALUABLE"
            problems.append("CAS_MANQUANT_OU_DUPLIQUE:" + caseid)
            continue
        row = matches[0]
        n, sha = row.get("pr_number"), row.get("head_sha")
        block, review = row.get("blocage_constate"), row.get("verification_humaine")
        pr_url, evidence = row.get("pr_url"), row.get("preuve_url")
        if type(n) is not int or n <= 0 or not isinstance(sha,str) or not SHA40.fullmatch(sha):
            stages[caseid] = "A_EXECUTER"
            problems.append("IDENTIFIANT_CANARI_ABSENT:" + caseid)
            continue
        if pr_url != f"https://github.com/{REPO}/pull/{n}":
            problems.append("URL_PR_NON_CONFORME:" + caseid)
        if type(block) is not bool or type(review) is not bool:
            problems.append("CONSTAT_NON_BOOLEEN:" + caseid)
        if evidence is not None and (not isinstance(evidence,str) or
                                      not EVIDENCE_URL.fullmatch(evidence)):
            problems.append("PREUVE_URL_NON_CONFORME:" + caseid)
        if not block or not review or not evidence:
            stages[caseid] = "PREUVE_A_COMPLETER"
            problems.append("PREUVE_HUMAINE_INCOMPLETE:" + caseid)
        else:
            stages[caseid] = "DECLARATION_A_CONTROLER"
        if observations is not None:
            live = observations.get(str(n)) if isinstance(observations,dict) else None
            if not isinstance(live,dict):
                stages[caseid] = "GITHUB_NON_VERIFIE"
                problems.append("ETAT_GITHUB_NON_LISIBLE:" + caseid)
            else:
                if (live.get("head_sha") != sha or live.get("open") is not True or
                    live.get("draft") is not False or live.get("merged") is not False):
                    stages[caseid] = "PR_TEMOIN_NON_VALIDE"
                    problems.append("CANARI_PAS_OUVERT_PRET_OU_SHA_DIVERGENT:" + caseid)
                elif live.get("mergeable_state") != "blocked" or live.get("mergeable") is not True:
                    stages[caseid] = "REFUS_FUSION_NON_PROUVE"
                    problems.append("GITHUB_N_ATTESTE_PAS_LE_BLOCAGE:" + caseid)
                # Even blocked can be caused by issues OTHER than the desired
                # branch policy. Admin must independently inspect rejection reason.
    if len(set(v.get("pr_number") for v in items if isinstance(v,dict) and
               type(v.get("pr_number")) is int)) not in (0, len(CASES)):
        problems.append("TROIS_PR_TEMOINS_DISTINCTES_REQUISES")
    complete = (
        not problems and len(stages)==len(CASES) and
        all(x == "DECLARATION_A_CONTROLER" for x in stages.values()) and
        all(document.get(k) is True for k in (
            "protection_serveur_confirmee_par_admin",
            "bypass_et_permissions_examines",
            "relecteur_independant_disponible"))
    )
    if not complete:
        problems.append("RECETTE_ADMIN_NON_CLOTUREE")
    return {
        "jalon": "P50Y",
        "statut_dossier": "DECLARATIONS_COMPLETEES_A_VALIDER_EXTERNEMENT"
                         if complete else "RECETTE_REQUISE",
        "cases": stages,
        "obstacles": sorted(set(problems)),
        "preuve_serveur_certifiee_automatiquement": False,
        "expertise_juridique_et_electorale_verifiee": False,
        "protection_main_installee_par_ce_programme": False,
        "fusion_autorisee": False,
        "publication_autorisee": False,
        "decision": "NO_GO_AUTOMATIQUE",
        "limite": "Les GET de PR, les URLs et les attestations déclaratives ne prouvent pas seuls les raisons du blocage; validation d'administrateur requise.",
    }

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dossier", type=Path, required=True)
    p.add_argument("--rapport", type=Path)
    p.add_argument("--live", action="store_true",
                   help="Lire les trois PR temoins via API GitHub, sans mutation")
    args = p.parse_args(argv)
    try:
        source = json.loads(args.dossier.read_text(encoding="utf-8"))
        obs = None
        if args.live:
            obs = {}
            items = source.get("cas", [])
            if not isinstance(items,list):
                raise ValueError("CAS_NON_LISTE")
            for row in items:
                n = row.get("pr_number") if isinstance(row,dict) else None
                if type(n) is int and n > 0:
                    obs[str(n)] = actual_canary(n, os.environ.get("GITHUB_TOKEN",""))
        result = analyze(source,obs)
    except (OSError,UnicodeError,ValueError,TypeError,AttributeError,
            HTTPError,URLError,TimeoutError) as e:
        result = analyze(None)
        result["erreur_type"] = type(e).__name__
    raw = json.dumps(result,ensure_ascii=False,indent=2) + "\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True,exist_ok=True)
        args.rapport.write_text(raw,encoding="utf-8")
    else:
        print(raw,end="")
    return 0 if "DOSSIER_NON_LISIBLE" not in result["obstacles"] else 2

if __name__ == "__main__":
    sys.exit(main())
