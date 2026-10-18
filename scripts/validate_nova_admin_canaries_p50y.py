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
CANARY_FILE_RE = re.compile(
    r"^projets/projet-nova/controles/canaris/[a-z0-9][a-z0-9_-]{0,63}\.txt$"
)
REQUIRED_CHECKS = (
    "no-committed-secrets",
    "Contrat sécurité validation site",
    "Contrat sécurité CI navigateur",
)
ACTIONS_APP_ID = 15368
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

def review_evidence(reviews, head_sha, author_id):
    """Count only, never disclose review authors. Refuse incomplete API pages."""
    if not isinstance(reviews,list) or len(reviews) >= 100:
        raise ValueError("REVUES_NON_EXHAUSTIVES")
    latest = {}
    previous = False
    substantive = 0
    for index, item in enumerate(reviews):
        if not isinstance(item,dict):
            raise ValueError("REVUE_NON_FIABLE")
        state = item.get("state")
        actor = item.get("user") or {}
        if not isinstance(actor,dict):
            raise ValueError("REVUE_ACTEUR_INCONNU")
        if state not in ("APPROVED","DISMISSED","CHANGES_REQUESTED"):
            continue
        substantive += 1
        identity = actor.get("id")
        if (type(identity) is not int or identity<=0 or
            identity == author_id or actor.get("type") == "Bot"):
            continue
        commit = item.get("commit_id")
        # DISMISSED ne prouve pas, à lui seul, qu'un avis antérieur
        # était APPROVED : un refus CHANGES_REQUESTED peut aussi être
        # dismiss. Exiger une vraie trace APPROVED au vieux commit.
        if state == "APPROVED" and commit != head_sha:
            previous = True
        stamp = str(item.get("submitted_at") or "")
        key = (stamp,index)
        if identity not in latest or key > latest[identity][0]:
            latest[identity] = (key,state,commit)
    current = sum(1 for _,state,commit in latest.values()
                  if state=="APPROVED" and commit==head_sha)
    return {
        "submitted_substantive":substantive,
        "fresh_independent_approvals":current,
        "prior_independent_approval_observed":previous,
    }


def checks_evidence(checks, head_sha):
    """Required global contexts: unique, successful only when at current SHA."""
    if (not isinstance(checks,dict) or type(checks.get("total_count")) is not int or
        checks["total_count"]>=100 or
        not isinstance(checks.get("check_runs"),list)):
        raise ValueError("CHECKS_NON_EXHAUSTIFS")
    rows=checks["check_runs"]
    if checks["total_count"] != len(rows):
        raise ValueError("CHECKS_PAGINATION_INCOMPLETE")
    successes=0
    unsatisfied=0
    for name in REQUIRED_CHECKS:
        candidates=[r for r in rows if isinstance(r,dict) and r.get("name")==name]
        if len(candidates)>1:
            raise ValueError("CHECKS_AMBIGUS_"+name)
        if candidates:
            r=candidates[0]
            if ((r.get("app") or {}).get("id")!=ACTIONS_APP_ID or
                r.get("head_sha")!=head_sha):
                raise ValueError("ORIGINE_CHECK_INVALIDE_"+name)
            success=(r.get("status")=="completed" and r.get("conclusion")=="success")
        else:
            success=False
        successes+=int(success)
        unsatisfied+=int(not success)
    return {"checks_success":successes,"checks_non_satisfaits":unsatisfied}




def observe_server(token: str):
    """Read branch, installed rulesets, their details and effective branch rules."""
    base = "/repos/" + REPO
    branch = github(base + "/branches/main",token)
    summaries = github(base + "/rulesets?includes_parents=true&per_page=100",token)
    if not isinstance(summaries,list) or len(summaries)>=100:
        raise ValueError("RULESETS_NON_EXHAUSTIFS")
    details = []
    for item in summaries:
        if not isinstance(item,dict):
            raise ValueError("RULESET_INVALIDE")
        if item.get("enforcement") == "active":
            rid = item.get("id")
            if type(rid) is not int or rid<=0:
                raise ValueError("RULESET_ID_INVALIDE")
            details.append(github(base + "/rulesets/" + str(rid),token))
    effective=github(base + "/rules/branches/main?per_page=100",token)
    if not isinstance(effective,list) or len(effective)>=100:
        raise ValueError("REGLES_EFFECTIVES_NON_EXHAUSTIVES")
    return {"branch":branch,"summaries":summaries,
            "details":details,"effective":effective}


def server_preflight(snapshot):
    """Fail closed when the *actual* main protections cannot be established.

    A positive result is only a configuration observation, not a tested merge
    refusal, independent human review, or authorization to publish.
    """
    issues=[]
    if not isinstance(snapshot,dict):
        return {"etat":"NON_ATTESTE","obstacles":["SERVEUR_GITHUB_NON_LISIBLE"],
                "sha_main_observe":None,"rulesets_actifs":0}
    branch=snapshot.get("branch")
    if not isinstance(branch,dict):
        branch={}
        issues.append("BRANCHE_MAIN_NON_LISIBLE")
    sha=(branch.get("commit") or {}).get("sha")
    if sha!=MAIN_SHA:
        issues.append("MAIN_SHA_CHANGE_DEPUIS_LE_DOSSIER")
    if branch.get("protected") is not True:
        issues.append("MAIN_NON_PROTEGEE")
    summaries=snapshot.get("summaries")
    if not isinstance(summaries,list) or len(summaries)>=100:
        summaries=[]
        issues.append("RULESETS_NON_LISIBLES")
    active=[item for item in summaries if isinstance(item,dict)
            and item.get("enforcement")=="active"]
    if not active:
        issues.append("RULESET_ACTIF_ABSENT")
    details=snapshot.get("details")
    if not isinstance(details,list) or len(details)!=len(active):
        details=[]
        issues.append("DETAILS_RULESET_MANQUANTS")
    effective=snapshot.get("effective")
    if not isinstance(effective,list) or len(effective)>=100:
        effective=[]
        issues.append("REGLES_EFFECTIVES_NON_LISIBLES")
    required_types={"deletion","non_fast_forward","pull_request","required_status_checks"}
    if not required_types.issubset({x.get("type") for x in effective if isinstance(x,dict)}):
        issues.append("REGLES_EFFECTIVES_INCOMPLETES")
    suitable=0
    bypass_unknown=False
    for item in details:
        if not isinstance(item,dict) or item.get("enforcement")!="active":
            continue
        if item.get("target")!="branch":
            continue
        condition=item.get("conditions")
        if condition!={"ref_name":{"include":["refs/heads/main"],"exclude":[]}}:
            continue
        if "bypass_actors" not in item:
            bypass_unknown=True
            continue
        if item["bypass_actors"]!=[]:
            issues.append("BYPASS_SERVEUR_DECLARE")
            continue
        rules=item.get("rules")
        if not isinstance(rules,list):
            continue
        bytype={v.get("type"):v for v in rules if isinstance(v,dict)}
        if not required_types.issubset(bytype):
            continue
        pr=(bytype["pull_request"].get("parameters") or {})
        checks=(bytype["required_status_checks"].get("parameters") or {})
        if (type(pr.get("required_approving_review_count")) is not int or
            pr["required_approving_review_count"]<1 or
            pr.get("dismiss_stale_reviews_on_push") is not True or
            pr.get("require_last_push_approval") is not True or
            pr.get("required_review_thread_resolution") is not True or
            checks.get("strict_required_status_checks_policy") is not True):
            continue
        rows=checks.get("required_status_checks")
        if not isinstance(rows,list):
            continue
        if not {(name,ACTIONS_APP_ID) for name in REQUIRED_CHECKS}.issubset({
                (v.get("context"),v.get("integration_id"))
                for v in rows if isinstance(v,dict)}):
            continue
        suitable+=1
    if suitable!=1:
        issues.append("RULESET_CONFORME_SANS_BYPASS_NON_DEMONTRE")
    if bypass_unknown:
        issues.append("EXCEPTIONS_BYPASS_NON_VISIBLES")
    return {"etat":"PRECONDITIONS_TECHNIQUES_VISIBLES" if not issues else "BLOQUANT",
            "obstacles":sorted(set(issues)),
            "sha_main_observe":sha,
            "rulesets_actifs":len(active)}


def attach_server_evidence(report,server):
    """Server status can only lower readiness; never manufacture a GO."""
    report=dict(report)
    report["etat_serveur_github"]=server["etat"]
    report["sha_main_live"]=server["sha_main_observe"]
    report["nombre_rulesets_actifs"]=server["rulesets_actifs"]
    report["obstacles"]=sorted(set(report["obstacles"]+server["obstacles"]))
    if server["etat"]!="PRECONDITIONS_TECHNIQUES_VISIBLES":
        report["statut_dossier"]="RECETTE_REQUISE"
        if "RECETTE_ADMIN_NON_CLOTUREE" not in report["obstacles"]:
            report["obstacles"].append("RECETTE_ADMIN_NON_CLOTUREE")
            report["obstacles"].sort()
    report["preuve_serveur_certifiee_automatiquement"]=False
    report["decision"]="NO_GO_AUTOMATIQUE"
    report["fusion_autorisee"]=False
    report["publication_autorisee"]=False
    return report

def actual_canary(number: int, token: str):
    base = "/repos/" + REPO
    pr = github(base + "/pulls/" + str(number), token)
    files = github(base + "/pulls/" + str(number) + "/files?per_page=100", token)
    # Refuse un résultat paginé ou incomplet : des changements hors du dossier
    # d'essai pourraient autrement passer inaperçus.
    if (not isinstance(files, list) or len(files) >= 100 or
            type(pr.get("changed_files")) is not int or
            pr["changed_files"] != len(files) or
            any(not isinstance(item, dict) for item in files)):
        raise ValueError("FICHIERS_CANARI_NON_EXHAUSTIFS")
    head = pr.get("head") or {}
    author=(pr.get("user") or {}).get("id")
    if type(author) is not int or author<=0:
        raise ValueError("AUTEUR_PR_INCONNU")
    reviews=github(base + "/pulls/" + str(number) + "/reviews?per_page=100",token)
    runs=github(base + "/commits/" + str(head.get("sha")) +
                "/check-runs?per_page=100",token)
    review_stats=review_evidence(reviews,head.get("sha"),author)
    check_stats=checks_evidence(runs,head.get("sha"))
    target = pr.get("base") or {}
    # True / False are not review decisions. A draft cannot demonstrate a
    # review or check gate because drafts are inherently not mergeable.
    result = {
        "head_sha": head.get("sha"),
        "head_ref": head.get("ref"),
        "head_repo": (head.get("repo") or {}).get("full_name"),
        "base_ref": target.get("ref"),
        "base_repo": (target.get("repo") or {}).get("full_name"),
        "title": pr.get("title"),
        "changed_paths": [item.get("filename") for item in files],
        "changed_statuses": [item.get("status") for item in files],
        "changed_previous_paths": [item.get("previous_filename") for item in files],
        "review_stats": review_stats,
        "check_stats": check_stats,
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
    if len(items) != len(CASES) or len(ids) != len(CASES) or any(
            not isinstance(x,str) for x in ids) or sorted(ids) != sorted(CASES):
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
        # Un lien vers une AUTRE PR ou vers un workflow non rattaché à ce
        # canari ne constitue pas une pièce probante de son refus de fusion.
        # Le journal Actions peut être ajouté au dossier interne, mais la
        # preuve_url publique doit désigner la PR témoin elle-même.
        elif evidence is not None and evidence != pr_url:
            problems.append("PREUVE_NON_RATTACHEE_AU_CANARI:" + caseid)
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
                elif (live.get("base_ref") != "main" or
                      live.get("base_repo") != REPO or
                      live.get("head_repo") != REPO or
                      not isinstance(live.get("head_ref"),str) or
                      not live["head_ref"].startswith("test/p50y-" + caseid + "-") or
                      not isinstance(live.get("title"),str) or
                      not live["title"].startswith("[P50Y-CANARI:" + caseid + "]")):
                    # Une PR réelle du Projet Nova ou une PR vers une autre
                    # branche ne peut JAMAIS servir de preuve de recette.
                    stages[caseid] = "CANARI_HORS_PERIMETRE"
                    problems.append("CANARI_IDENTITE_OU_CIBLE_INVALIDE:" + caseid)
                elif (not isinstance(live.get("changed_paths"),list) or
                      not isinstance(live.get("changed_statuses"),list) or
                      not isinstance(live.get("changed_previous_paths"),list) or
                      not 1 <= len(live["changed_paths"]) <= 3 or
                      len(live["changed_paths"]) != len(live["changed_statuses"]) or
                      len(live["changed_paths"]) != len(live["changed_previous_paths"]) or
                      any(not isinstance(path,str) or not CANARY_FILE_RE.fullmatch(path)
                          or status != "added" or previous is not None
                          for path,status,previous in zip(
                              live["changed_paths"],live["changed_statuses"],
                              live["changed_previous_paths"]))):
                    stages[caseid] = "CHANGEMENT_CANARI_DANGEREUX"
                    problems.append("CANARI_FICHIERS_HORS_REPERTOIRE:" + caseid)
                elif (not isinstance(live.get("review_stats"),dict) or
                      not isinstance(live.get("check_stats"),dict) or
                      type(live["review_stats"].get("submitted_substantive")) is not int or
                      type(live["review_stats"].get("fresh_independent_approvals")) is not int or
                      type(live["review_stats"].get("prior_independent_approval_observed")) is not bool or
                      type(live["check_stats"].get("checks_success")) is not int or
                      type(live["check_stats"].get("checks_non_satisfaits")) is not int or
                      live["check_stats"]["checks_success"] + live["check_stats"]["checks_non_satisfaits"] != len(REQUIRED_CHECKS)):
                    stages[caseid] = "PREUVES_API_INCOMPLETES"
                    problems.append("REVUES_OU_CHECKS_NON_ATTESTES:" + caseid)
                elif ((caseid=="sans_revue" and not (
                          live["review_stats"]["submitted_substantive"]==0 and
                          live["check_stats"]["checks_success"]==len(REQUIRED_CHECKS))) or
                      (caseid=="approbation_perimee" and not (
                          live["review_stats"]["prior_independent_approval_observed"] is True and
                          live["review_stats"]["fresh_independent_approvals"]==0 and
                          live["check_stats"]["checks_success"]==len(REQUIRED_CHECKS))) or
                      (caseid=="check_non_satisfait" and not (
                          live["review_stats"]["fresh_independent_approvals"]>=1 and
                          live["check_stats"]["checks_non_satisfaits"]>=1))):
                    stages[caseid] = "MOTIF_NON_CORROBORE"
                    problems.append("OBSERVATIONS_NE_SOUTIENNENT_PAS_LE_SCENARIO:" + caseid)
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
    p.add_argument("--observer-serveur", action="store_true",
                   help="Verifier main et les rulesets actifs via GET, sans PR temoin")
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
        if args.live or args.observer_serveur:
            # Si les API échouent, une preuve documentaire déclarée complète
            # ne peut PAS survivre à un serveur impossible à lire.
            try:
                server = server_preflight(observe_server(
                    os.environ.get("GITHUB_TOKEN","")))
            except (OSError,UnicodeError,ValueError,TypeError,AttributeError,
                    KeyError,HTTPError,URLError,TimeoutError):
                server = server_preflight(None)
            result = attach_server_evidence(result,server)
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
