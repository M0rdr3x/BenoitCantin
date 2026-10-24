#!/usr/bin/env python3
"""Confirme le corpus exact Nova 40, âge, consentement et collecte fermée."""
import argparse
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NOVA=ROOT/"projets/projet-nova"
# SHA du blob Git approuvé : toute modification du corpus exige une revue et une nouvelle version.
# Ceci détecte une dérive accidentelle, sans prétendre valoir signature cryptographique indépendante.
APPROVED_MANIFEST_GIT_SHA = "97f0d3ad2b13be728356bba7a1831b91fd047070"
APPROVED_MANIFEST_SHA256 = "5eece3aacaff678fd6f514d2ca5c4a158da9afb2dd3c5d6fb3c7849ac2cecfac"

def manifest_git_sha(text):
    data = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
ICON=NOVA/"assets/nova-sondage-icone.webp"
ICON_SHA256="40adc5363eb4b1a76236e2755b6c73c30119dc4477d41801e720d4e6583cfeb2"
PATHS={
"manifest":NOVA/"data/consultation-40-v1.json",
"page":NOVA/"consultation-40.html",
"client":NOVA/"assets/consultation-40.js",
"sql":ROOT/"supabase/candidate-migrations/20261019190000_nova_foundations_40_survey_v1.sql",
"edge":ROOT/"supabase/functions/nova-consultation40-submit/index.ts",
"body":ROOT/"supabase/functions/_shared/nova_survey_body.mjs",
"config":ROOT/"supabase/config.toml",
"index":NOVA/"index.html",
"portal":ROOT/"index.html",
}

def validate(text):
    issues=[]
    if manifest_git_sha(text["manifest"]) != APPROVED_MANIFEST_GIT_SHA:
        issues.append("Corpus Nova 40 modifié sans revue de version")
    if hashlib.sha256(text["manifest"].encode("utf-8")).hexdigest() != APPROVED_MANIFEST_SHA256:
        issues.append("Empreinte SHA-256 du corpus Nova 40 divergente")
    if text["client"].count("const APPROVED_MANIFEST_SHA256 = '"+APPROVED_MANIFEST_SHA256+"';")!=1:
        issues.append("Empreinte navigateur du questionnaire 40 absente ou incohérente")
    required={
        "page":["sondage-age","sondage-consent","sondage-start","sondage-submit",
                'id="sondage-privacy-warning"', "Une fois une contribution agrégée",
                'id="sondage-next"','id="sondage-back"','40 questions','non représentative',
                'id="sondage-consent" type="checkbox" autocomplete="off"',
                'id="sondage-form" novalidate autocomplete="off"',
                'Cette case ne constitue pas un consentement à une future collecte.',
                'Toute collecte future exigera un consentement distinct'],
        "client":["const COLLECTION_OPEN = false","const LIVE_OPINION_CONSENT_GRANTED = false","!eligible()","questions.length!==40",
                  "answers.size!==40","sondage-submit').disabled=true","age18Confirmed:true",
                  "explicitConsent:LIVE_OPINION_CONSENT_GRANTED","client.auth.getUser()",
                  "client.functions.invoke('nova-consultation40-submit'",
                  "data.survey === SURVEY_ID", "data.code === 'RECORDED'",
                  "textContent = item.text",
                  "cache:'no-store'", "radio.autocomplete = 'off'",
                  "function clearLocalDemo()", "window.addEventListener('pageshow'",
                   "window.addEventListener('pagehide'",
                  "new AbortController()", "setTimeout(() => controller.abort(), 15000)",
                   "signal:controller.signal", "clearTimeout(timeoutId)",
                   "if (!COLLECTION_OPEN && !LIVE_OPINION_CONSENT_GRANTED) clearLocalDemo()",
                  "!COLLECTION_OPEN || !LIVE_OPINION_CONSENT_GRANTED",
                  "La case d'accord de démonstration n'autorise PAS une collecte future.",
                  "crypto.subtle.digest('SHA-256', manifestBytes)",
                  "readBoundedManifest(r,controller)", "actual !== APPROVED_MANIFEST_SHA256",
                  "new TextDecoder('utf-8', {fatal:true})",
                  "response.body.getReader()", "reader.read()", "reader.releaseLock()",
                  "total>65536", "controller.abort()", "result.set(part,offset)",
                  "Number(declared)>65536",
                  "data.version !== '1.0.0'",
                  "data.choices.join(',') !== 'pour,contre,sans_opinion'"],
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
                "validAnswers(body.answers)","ORIGIN_NOT_ALLOWED","error?.code === '23505'",
                "readBoundedJson(req)","MAX_REQUEST_BYTES","REQUEST_TOO_LARGE"],
        "body":["req.body.getReader()","if (total > MAX_REQUEST_BYTES)",
                "reader.cancel()","reader.releaseLock()","JSON.parse(raw)"],
        "config":["[functions.nova-consultation40-submit]\nverify_jwt = true"],
        "index":['href="consultation-40.html"', 'id="consultations"', 'id="nova-survey-directory-40"',
                 'id="nova-survey-directory-64"', 'collecte fermée',
                 'src="assets/nova-sondage-icone.webp"',
                 'class="nova-survey-directory-icon-link"',
                 'aria-label="Ouvrir le sondage référendaire consultatif de 40 questions"',
                 'aria-label="Ouvrir le sondage citoyen de 64 propositions"'],
        "portal":['id="sondages-nova"', 'id="home-sondage-40"',
                  'id="home-sondage-64"',
                  'href="/projets/projet-nova/consultation-40.html"',
                  'href="/projets/projet-nova/sondage.html"',
                  'src="/projets/projet-nova/assets/nova-sondage-icone.webp"',
                  'collecte des réponses désactivée', 'non officiel et non représentatif']
    }
    for key, markers in required.items():
        for marker in markers:
            if marker not in text[key]:
                issues.append(f"{key}: contrat manquant {marker}")
    if "await req.text()" in text["edge"]:
        issues.append("Corps Nova 40 lu sans limite de flux")
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
    if not ICON.is_file() or hashlib.sha256(ICON.read_bytes()).hexdigest()!=ICON_SHA256:
        issues.append("Icône officielle des sondages absente ou modifiée sans validation")
    if issues:raise SystemExit("\n".join(issues))
    if args.self_test:
        muts=[
            ("client","const COLLECTION_OPEN = false","const COLLECTION_OPEN = true"),
            ("client","const LIVE_OPINION_CONSENT_GRANTED = false","const LIVE_OPINION_CONSENT_GRANTED = true"),
            ("client","!COLLECTION_OPEN || !LIVE_OPINION_CONSENT_GRANTED","!COLLECTION_OPEN || false"),
            ("page",'id="sondage-privacy-warning"','id="avis-absent"'),
            ("page",'Cette case ne constitue pas un consentement à une future collecte.',
             'Cette case permet toute collecte future.'),
            ("page",'autocomplete="off"','autocomplete="on"'),
            ("client","radio.autocomplete = 'off'","radio.autocomplete = 'on'"),
            ("client","window.addEventListener('pageshow'","window.addEventListener('pagehide'"),
            ("client","window.addEventListener('pagehide'","window.addEventListener('visibilitychange'"),
            ("client","setTimeout(() => controller.abort(), 15000)","setTimeout(() => {}, 15000)"),
            ("client","signal:controller.signal","signal:undefined"),
            ("client","clearTimeout(timeoutId)","void timeoutId"),
            ("client","if (!COLLECTION_OPEN && !LIVE_OPINION_CONSENT_GRANTED) clearLocalDemo()",
             "if (false) clearLocalDemo()"),
            ("portal",'id="sondages-nova"','id="lien-sondage-absent"'),
            ("portal",'src="/projets/projet-nova/assets/nova-sondage-icone.webp"','src="/assets/image-inexistante.webp"'),
            ("portal",'id="home-sondage-64"','id="accès-64-supprimé"'),
            ("index",'id="nova-survey-directory-40"','id="acces-40-absent"'),
            ("index",'id="nova-survey-directory-64"','id="acces-64-absent"'),
            ("index",'src="assets/nova-sondage-icone.webp"','src="assets/icone-manquante.webp"'),
            ("client","!eligible()","false"),
            ("client","answers.size!==40","false"),
            ("client","age18Confirmed:true","age18Confirmed:false"),
            ("client","explicitConsent:LIVE_OPINION_CONSENT_GRANTED","explicitConsent:true"),
            ("client","textContent = item.text","innerHTML = item.text"),
            ("client","data.code === 'RECORDED'","true"),
            ("client","crypto.subtle.digest('SHA-256', manifestBytes)","Promise.resolve(new ArrayBuffer(32))"),
            ("client","actual !== APPROVED_MANIFEST_SHA256","false"),
            ("client","response.body.getReader()","response.arrayBuffer()"),
            ("client","total>65536","false"),
            ("client","reader.releaseLock()","void reader"),
            ("client","readBoundedManifest(r,controller)","r.json()"),
            ("client","data.survey === SURVEY_ID","true"),
            ("sql","enable row level security","disable row level security"),
            ("sql","!= 40","!= 39"),
            ("edge","NOVA40_COLLECTION_ENABLED","ENABLE_ALL"),
            ("edge","requiredUser(req)","null"),
            ("edge","validAnswers(body.answers)","true"),
            ("edge","readBoundedJson(req)","req.text()"),
            ("body","if (total > MAX_REQUEST_BYTES)","if (false)"),
            ("config","verify_jwt = true","verify_jwt = false")
        ]
        for key,old,new in muts:
            altered=dict(text);altered[key]=altered[key].replace(old,new)
            assert validate(altered), "Régression non détectée: "+old
        for field,value in [("minimumAge",16),("collectionOpen",True)]:
            obj=json.loads(text["manifest"]);obj[field]=value
            altered=dict(text);altered["manifest"]=json.dumps(obj)
            assert validate(altered), "Régression de manifeste non détectée"
        obj=json.loads(text["manifest"])
        obj["questions"][19]["text"]="Question centrale modifiée sans approbation"
        altered=dict(text);altered["manifest"]=json.dumps(obj,ensure_ascii=False)
        assert validate(altered), "Modification intermédiaire du corpus non détectée"
        print(f"OK consultation 40 : {len(muts) + 3} mutations de sécurité, âge, corpus et accès refusées")
    print("OK consultation Nova : 40 questions Pour/Contre, 18+, collecte désactivée, RLS")
if __name__=="__main__":main()
