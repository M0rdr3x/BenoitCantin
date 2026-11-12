#!/usr/bin/env python3
"""P50T — porte de revues GitHub distincte de l'autorisation de publication.

Lit un rapport P50S issu d'une vraie consultation read-only; n'interroge
aucun compte privé et n'effectue aucune mutation GitHub. Toute absence de revue
à l'empreinte courante est un blocage explicite pour la phase de revue.
Jamais de GO institutionnel, même si tous les avis GitHub sont favorables.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

PRIORITY=(657,638)
FOLLOWUP=(655,636,659)
ALL=PRIORITY+FOLLOWUP
SHA={
    657:"f67abe43b7223d0f59ee1efb6cf883d558eddfb5",
    638:"e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e",
    655:"8541f761be8dbabda0c3f024f8969562ab816bc7",
    636:"6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb",
    659:"363bafc8f07cee1d72e785e51d48fbec121bb574",
}
MAIN="9ed5f70cbe7022f25a679346a1288701f3b09067"
REQUIRED_TECH={"P50Q":"REUSSITE_CI_VERIFIEE_AU_SHA",
               "P50R":"REUSSITE_CI_VERIFIEE_AU_SHA"}
STAGES=("prioritaire","complete")


def inspect(report: object, stage: str="prioritaire") -> dict:
    if stage not in STAGES:
        raise ValueError("ETAPE_INCONNUE")
    subset=PRIORITY if stage=="prioritaire" else ALL
    blockers=[]
    statuses={}
    if not isinstance(report,dict) or report.get("structure")!="RELEVE_EFFECTUE":
        blockers.append("RAPPORT_P50S_ABSENT_OU_INVALIDE")
        report={}
    if report.get("decision")!="NO_GO_AUTOMATIQUE":
        blockers.append("NO_GO_P50S_ABSENT")
    if report.get("autorisation_publication") is not False:
        blockers.append("PRETENTION_AUTORISATION_PUBLIQUE")
    if report.get("signature_juridique_attestee") is not False:
        blockers.append("PRETENTION_SIGNATURE_JURIDIQUE")
    if report.get("main_sha",MAIN)!=MAIN:
        blockers.append("BASE_MAIN_INATTENDUE")
    found=report.get("revues")
    if not isinstance(found,dict):
        found={}
        blockers.append("REGISTRE_REVUES_INVALIDE")
    for n in ALL:
        row=found.get(str(n))
        if not isinstance(row,dict):
            statuses[str(n)]="INCONNU"
            if n in subset:
                blockers.append(f"PR{n}_REVUE_INCONNUE")
            continue
        a=row.get("approbations_git_head")
        required=row.get("habilitation_humaine_attestee")
        if type(a) is not int or a<0 or required is not False:
            statuses[str(n)]="NON_FIABLE"
            if n in subset:
                blockers.append(f"PR{n}_PREUVE_DE_REVUE_INVALIDE")
            continue
        if a==0:
            statuses[str(n)]="APPROBATION_ABSENTE"
            if n in subset:
                blockers.append(f"PR{n}_APPROBATION_ABSENTE")
        else:
            statuses[str(n)]="APPROBATION_GITHUB_OBSERVEE_NON_INSTITUTIONNELLE"
    checks=report.get("ci") if isinstance(report.get("ci"),dict) else {}
    for name,expected in REQUIRED_TECH.items():
        if checks.get(name)!=expected:
            blockers.append(f"PREUVE_TECHNIQUE_{name}_INSUFFISANTE")
    original=report.get("obstacles")
    if not isinstance(original,list) or any(not isinstance(x,str) for x in original):
        blockers.append("OBSTACLES_P50S_NON_FIABLES")
        original=[]
    # Source-of-truth guardrails: even an approved review cannot supersede a
    # SHA change, missing API evidence, or PR640 becoming mergeable.
    unsafe_terms=("SHA_OU_BASE_CHANGE","MAIN_MODIFIE","PR640_VERROU_",
                  "INACCESSIBLE","ETAT_MODIFIE","PAS_EN_BROUILLON",
                  "PREUVE_CI_INSUFFISANTE")
    for issue in original:
        if any(x in issue for x in unsafe_terms):
            blockers.append("DERIVE_P50S:"+issue)
    phase="REVUES_GITHUB_OBSERVEES_SEULEMENT" if not blockers else "REVUES_REQUISES"
    next_actions=[]
    for n in subset:
        if statuses.get(str(n))=="APPROBATION_ABSENTE":
            next_actions.append(f"Obtenir une revue GitHub indépendante de la PR {n}, sur son SHA exact.")
    if "PR657_APPROBATION_ABSENTE" not in blockers and stage=="complete":
        next_actions.append("Réexaminer les SHA après toute intégration : les approbations antérieures expirent.")
    return {
        "jalon":"P50T",
        "phase":stage,
        "etat_porte_revues":phase,
        "exigences_sha":{str(k):SHA[k] for k in subset},
        "revues":statuses,
        "preuves_techniques":checks,
        "obstacles_revues":sorted(set(blockers)),
        "actions":next_actions,
        "approbations_git_ne_prouvent_pas_mandat":True,
        "revue_juridique_et_confidentialite_requise":True,
        "autorisation_publication":False,
        "autorisation_fusion":False,
        "exclusion_pr640":True,
        "decision":"NO_GO_AUTOMATIQUE",
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rapport-p50s",type=Path,required=True)
    p.add_argument("--phase",choices=STAGES,default="prioritaire")
    p.add_argument("--resultat",type=Path)
    p.add_argument("--exiger-revues",action="store_true",
                   help="Retour 3 lorsque la porte de revue est bloquee.")
    args=p.parse_args(argv)
    try:
        result=inspect(json.loads(args.rapport_p50s.read_text(encoding="utf-8")),args.phase)
    except (OSError,UnicodeError,json.JSONDecodeError,ValueError) as e:
        result=inspect(None,args.phase)
        result["erreur_type"]=type(e).__name__
    raw=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.resultat:
        args.resultat.parent.mkdir(parents=True,exist_ok=True)
        args.resultat.write_text(raw,encoding="utf-8")
    else:
        print(raw,end="")
    if args.exiger_revues and result["etat_porte_revues"]!="REVUES_GITHUB_OBSERVEES_SEULEMENT":
        print("P50T_REVIEW_GATE_BLOCKED: les revues independantes sont absentes ou non probantes.",file=sys.stderr)
        return 3
    return 0 if "RAPPORT_P50S_ABSENT_OU_INVALIDE" not in result["obstacles_revues"] else 2

if __name__=="__main__":
    raise SystemExit(main())
