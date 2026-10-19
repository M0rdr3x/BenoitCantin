#!/usr/bin/env python3
"""Confirme le corpus exact Nova 40, âge, consentement et collecte fermée."""
import argparse
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NOVA=ROOT/"projets/projet-nova"
PATHS={
"manifest":NOVA/"data/consultation-40-v1.json",
"page":NOVA/"consultation-40.html",
"client":NOVA/"assets/consultation-40.js",
"sql":ROOT/"supabase/migrations/20261019190000_nova_foundations_40_survey_v1.sql",
"edge":ROOT/"supabase/functions/nova-consultation40-submit/index.ts",
"config":ROOT/"supabase/config.toml",
"index":NOVA/"index.html",
}

def validate(text):
    issues=[]
    required={
        "page":["sondage-age","sondage-consent","sondage-start","sondage-submit",
                'id="sondage-next"','id="sondage-back"','40 questions','non représentative'],
        "client":["const COLLECTION_OPEN = false","!eligible()","questions.length!==40",
                  "answers.size!==40","sondage-submit').disabled=true","age18Confirmed:true",
                  "explicitConsent:true","client.auth.getUser()",
                  "client.functions.invoke('nova-consultation40-submit'","textContent=item.text",
                  "cache:'no-store'"],
        "sql":["enable row level security","revoke all on public.nova_consultation40_participants",
               "revoke all on public.nova_consultation40_aggregate_counts",
               "primary key (survey_version, participant_hash)",
               "primary key (survey_version, question_id, response_value)",
               "security definer set search_path = ''","!= 40","jsonb_each_text(p_answers)",
               "raise exception 'ALREADY_SUBMITTED'","to service_role"],
        "edge":["const SURVEY_ID = 'nova-orientations-40-v1'",
                "NOVA40_COLLECTION_ENABLED","!== 'true'","NOVA40_SURVEY_PEPPER",
                "requiredUser(req)","age18Confirmed !== true","explicitConsent !== true",
                "crypto.subtle.sign('HMAC'","service.rpc('nova_consultation40_submit_v1'",
                "validAnswers(body.answers)","ORIGIN_NOT_ALLOWED","error?.code === '23505'"],
        "config":["[functions.nova-consultation40-submit]\nverify_jwt = true"],
        "index":['href="consultation-40.html"']
    }
    for key, markers in required.items():
        for marker in markers:
            if marker not in text[key]:
                issues.append(f"{key}: contrat manquant {marker}")
    if "localStorage.setItem" in text["client"] or "sessionStorage.setItem" in text["client"]:
        issues.append("Opinions politiques stockées localement")
    if "create policy" in text["sql"].lower():
        issues.append("Politique publique interdite pour les tables de votes")
    try:
        manifest=json.loads(text["manifest"])
        if (manifest["id"]!="nova-orientations-40-v1" or manifest["minimumAge"]!=18
                or manifest["collectionOpen"] is not False
                or manifest["choices"]!=["pour","contre","sans_opinion"]):
            issues.append("Version, âge, choix ou collecte non conforme")
        questions=manifest["questions"]
        if len(questions)!=40 or any(q["id"]!="q"+str(i+1).zfill(2)
          or len(q["text"])<35 for i,q in enumerate(questions)):
            issues.append("Banque de 40 questions non conforme")
        if not questions[0]["text"].startswith("Voulez-vous que le Québec cesse"):
            issues.append("Question de souveraineté manquante")
        if not questions[-1]["text"].startswith("Êtes-vous pour imposer une évaluation environnementale"):
            issues.append("Question environnementale manquante")
    except (ValueError,KeyError,TypeError):
        issues.append("JSON des 40 questions invalide")
    return issues

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    text={k:v.read_text("utf-8") for k,v in PATHS.items()}
    issues=validate(text)
    if issues:raise SystemExit("\n".join(issues))
    if args.self_test:
        muts=[
            ("client","const COLLECTION_OPEN = false","const COLLECTION_OPEN = true"),
            ("client","!eligible()","false"),
            ("client","answers.size!==40","false"),
            ("client","age18Confirmed:true","age18Confirmed:false"),
            ("client","explicitConsent:true","explicitConsent:false"),
            ("sql","enable row level security","disable row level security"),
            ("sql","!= 40","!= 39"),
            ("edge","NOVA40_COLLECTION_ENABLED","ENABLE_ALL"),
            ("edge","requiredUser(req)","null"),
            ("edge","validAnswers(body.answers)","true"),
            ("config","[functions.nova-consultation40-submit]\\nverify_jwt = true",
             "[functions.nova-consultation40-submit]\\nverify_jwt = false")
        ]
        for key,old,new in muts:
            altered=dict(text);altered[key]=altered[key].replace(old,new)
            assert validate(altered), "Régression non détectée: "+old
        for field,value in [("minimumAge",16),("collectionOpen",True)]:
            obj=json.loads(text["manifest"]);obj[field]=value
            altered=dict(text);altered["manifest"]=json.dumps(obj)
            assert validate(altered), "Régression de manifeste non détectée"
        print("OK consultation 40 : 13 mutations de sécurité et âge refusées")
    print("OK consultation Nova : 40 questions Pour/Contre, 18+, collecte désactivée, RLS")
if __name__=="__main__":main()
