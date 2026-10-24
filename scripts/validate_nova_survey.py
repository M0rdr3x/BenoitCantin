#!/usr/bin/env python3
"""Validation anti-régression du sondage politique sensible Nova 18+.

Aucune connexion réseau; aucun compte ni réponse de personne réelle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT / "projets/projet-nova"
# Empreinte du manifeste figé; sa modification exige une nouvelle vague/version.
APPROVED_MANIFEST_SHA256 = "67df5052a3a09f23ecfa43e2882dcf7a0b6f1a85f1aad4e2f4159aab06570738"
APPROVED_COMPASS_SHA256 = "5d65a6067142fbba59a81edeaac49dc1befd82aa281c6e11e2f2509a1aee9109"
APPROVED_DOCUMENTARY_SHA256 = {
    "documentary_parties": "69ca01c66e54586a809a151fb73ff383aeb6bf80dccab8036eba365d9d4e8784",
    "documentary_sources": "2b3b226cc02375f51458dcd24588346b2574338ea91b592d8414926ce010113a",
    "documentary_evidence": "09503ddd60aaed5f3aa6e03058d218a83f80361556f8e6431211ee84ac08ad79",
}
FILES = {
    "page": NOVA / "sondage.html",
    "client": NOVA / "assets/sondage.js",
    "compass_client": NOVA / "assets/boussole-electorale.js",
    "documentary_parties": NOVA / "data/boussole-partis-2026.json",
    "documentary_sources": NOVA / "data/boussole-sources-partis-2026.json",
    "documentary_evidence": NOVA / "data/boussole-preuves-2026.json",
    "style": NOVA / "assets/sondage.css",
    "manifest": NOVA / "data/sondage-questions-v1.json",
    "source": NOVA / "data/boussole-electorale-v2.json",
    "index": NOVA / "index.html",
    "method": NOVA / "SONDAGE_METHODOLOGIE_ET_ACTIVATION.md",
    "sql": ROOT / "supabase/candidate-migrations/20261019170000_nova_adult_opinion_survey_v1.sql",
    "edge": ROOT / "supabase/functions/nova-survey-submit/index.ts",
    "body": ROOT / "supabase/functions/_shared/nova_survey_body.mjs",
    "config": ROOT / "supabase/config.toml",
}


def check_text(payload: dict[str, str]) -> list[str]:
    issues: list[str] = []
    def demand(file: str, *markers: str) -> None:
        for marker in markers:
            if marker not in payload[file]:
                issues.append(f"{file}: protection manquante {marker!r}")

    demand("page", 'id="sondage-age"', 'id="sondage-consent"',
           'id="sondage-start" type="button" disabled',
           'id="sondage-submit" type="button" disabled',
           'id="sondage-choices"', 'id="sondage-progress"',
           'id="sondage-back"', 'id="sondage-next"',
           'id="sondage-question-heading"', 'noindex,follow',
           'non représentative', '64 propositions',
           'id="sondage-review-list"', 'id="sondage-answered"',
           'id="sondage-consent" type="checkbox" autocomplete="off"',
           'id="sondage-form" novalidate autocomplete="off"',
           'Cette case ne constitue pas un consentement à une future collecte.',
           'Toute collecte future exigera un consentement distinct')
    demand("client", "const APPROVED_MANIFEST_SHA256 = '" + APPROVED_MANIFEST_SHA256 + "';",
           "globalThis.crypto?.subtle", "readBoundedManifest(response,controller)",
           "readBoundedManifest(compassResponse,controller)",
           "response.body.getReader()", "reader.read()", "reader.releaseLock()",
           "total>65536", "controller.abort()", "result.set(part,offset)",
           "Number(declared)>65536", "crypto.subtle.digest('SHA-256', manifestBytes)",
           "observed !== APPROVED_MANIFEST_SHA256",
           "TextDecoder('utf-8', { fatal: true })")
    demand("client", "const APPROVED_COMPASS_SHA256 = '"+APPROVED_COMPASS_SHA256+"';",
           "globalThis.crypto.subtle.digest('SHA-256',compassBytes)",
           "hex(compassDigest)!==APPROVED_COMPASS_SHA256")
    demand("compass_client", 'const APPROVED_COMPASS_SHA256 = "'+APPROVED_COMPASS_SHA256+'";',
           'globalThis.crypto.subtle.digest("SHA-256",bytes)',
           "fetchApprovedQuestionCorpus()", "actual!==APPROVED_COMPASS_SHA256",
           'new TextDecoder("utf-8",{fatal:true})')
    if hashlib.sha256(payload["source"].encode("utf-8")).hexdigest() != APPROVED_COMPASS_SHA256:
        issues.append("Questionnaire Boussole modifié sans revue de version")
    demand("compass_client", "const APPROVED_DOCUMENTARY_SHA256 = Object.freeze({",
           "fetchLimitedBytes(DATA_URL,65536)",
           "fetchLimitedBytes(url,maxBytes)",
           "signal:controller.signal",
           "setTimeout(()=>controller.abort(),20000)",
           "clearTimeout(timeoutId)",
           "response.body.getReader()",
           "reader.read()", "reader.releaseLock()",
           "total>maxBytes", "controller.abort()",
           "bytes.set(part,offset)",
           "Number(declared)>maxBytes",
           "fetchApprovedDocumentary(PARTY_DATA_URL)",
           "fetchApprovedDocumentary(PARTY_SOURCE_DATA_URL)",
           "fetchApprovedDocumentary(EVIDENCE_DATA_URL)",
           'globalThis.crypto.subtle.digest("SHA-256",bytes)',
           "observed!==approved", "ArrayBuffer.isView(value)",
           "value.BYTES_PER_ELEMENT!==1", "total+=value.byteLength")
    for key, digest in APPROVED_DOCUMENTARY_SHA256.items():
        size = len(payload[key].encode("utf-8"))
        if size > (524288 if key == "documentary_evidence" else 65536) or not size:
            issues.append(key + " : taille documentaire interdite")
        if hashlib.sha256(payload[key].encode("utf-8")).hexdigest() != digest:
            issues.append(key + " : corpus documentaire modifié sans revue")
        if payload["compass_client"].count('"'+digest+'"') != 1:
            issues.append(key + " : empreinte documentaire absente du navigateur")
    demand("client", "const COLLECTION_OPEN = false;",
           "const LIVE_OPINION_CONSENT_GRANTED = false;",
           "function eligible()", "$('sondage-age').checked",
           "$('sondage-consent').checked",
           "selections.size !== questions.length",
           "explicitConsent: LIVE_OPINION_CONSENT_GRANTED", "age18Confirmed: true",
           "validManifest(manifest)", "question.id",
           "value !== 'skip'", "const answers = Object.create(null)",
           "client.auth.getUser()", "client.functions.invoke('nova-survey-submit'",
            "data.code !== 'RECORDED'", "data.survey !== SURVEY_ID",
           "if (!COLLECTION_OPEN || !LIVE_OPINION_CONSENT_GRANTED || recorded || submitting || !eligible()) return",
           "if (!LIVE_OPINION_CONSENT_GRANTED) throw new Error('LIVE_CONSENT_REQUIRED')",
           "if (recorded) return", "text.textContent = label",
           "editingReview = true", "choiceNames.get(selections.get(question.id))",
           "list.replaceChildren()", "step = 0;",
           "input.autocomplete = 'off'",
           "function clearLocalDemo()", "window.addEventListener('pageshow'",
           "window.addEventListener('pagehide'",
           "new AbortController()",
           "setTimeout(() => controller.abort(), 15000)",
           "signal: controller.signal", "clearTimeout(timeoutId)",
           "if (!COLLECTION_OPEN && !LIVE_OPINION_CONSENT_GRANTED) clearLocalDemo()",
           "L'accord de démonstration ne vaut PAS consentement à la collecte")
    demand("page", 'id="sondage-reset-question"', 'id="sondage-reset-finish"',
           'id="sondage-privacy-warning"', "Une fois une contribution agrégée")
    demand("client", "selections.clear()", "'sondage-consent').checked = false",
           "window.confirm(", "'sondage-introduction').hidden = false")
    demand("index", 'href="sondage.html"', 'Sondage citoyen 18+')
    demand("sql", "create table if not exists public.nova_survey_participants",
           "create table if not exists public.nova_survey_aggregate_counts",
           "primary key (survey_version, participant_hash)",
           "primary key (survey_version, question_id, response_value)",
           "enable row level security",
           "revoke all on public.nova_survey_participants from public, anon, authenticated",
           "revoke all on public.nova_survey_aggregate_counts from public, anon, authenticated",
           "security definer set search_path = ''",
           "jsonb_each_text(p_answers)", "!= 64",
           "raise exception 'ALREADY_SUBMITTED' using errcode='23505'",
           "grant execute on function public.nova_survey_submit_v1(text,text,jsonb)",
           "to service_role")
    demand("edge", "requiredUser(req)", "NOVA_SURVEY_COLLECTION_ENABLED",
           "!== 'true'", "NOVA_SURVEY_PEPPER",
           "crypto.subtle.sign('HMAC'", "age18Confirmed !== true",
           "explicitConsent !== true", "validAnswers(body.answers)",
           "error?.code === '23505'", "ORIGIN_NOT_ALLOWED",
           "service.rpc('nova_survey_submit_v1'",
           "readBoundedJson(req)", "MAX_REQUEST_BYTES", "REQUEST_TOO_LARGE")
    demand("body", "req.body.getReader()", "if (total > MAX_REQUEST_BYTES)",
           "reader.cancel()", "reader.releaseLock()", "JSON.parse(raw)")
    if "await req.text()" in payload["edge"]:
        issues.append("Corps Nova lu sans limite de flux")
    demand("config", "[functions.nova-survey-submit]\nverify_jwt = true")
    demand("method", "non", "représentatif", "confidentialité",
           "18 ans", "Aucun résultat", "COLLECTION_OPEN")
    if "localStorage.setItem" in payload["client"] or "sessionStorage.setItem" in payload["client"]:
        issues.append("Aucune opinion ne doit être stockée dans le navigateur")
    if "fetch('https://formspree.io" in payload["client"] or "formspree.io/f/" in payload["page"]:
        issues.append("Envoi vers un fournisseur tiers interdit")
    if "create policy" in payload["sql"].lower():
        issues.append("Les tables sensibles doivent rester sans politique de lecture publique")
    return issues


def check_questions(snapshot: str, original: str) -> list[str]:
    issues: list[str] = []
    try:
        survey = json.loads(snapshot)
        compass = json.loads(original)
    except (ValueError, TypeError):
        return ["Manifeste des questions invalide"]
    if survey.get("id") != "nova-consultation-64-v1" or survey.get("minimumAge") != 18:
        issues.append("Âge minimal et version du sondage incorrects")
    if survey.get("sourceVersion") != "2.2.0":
        issues.append("Version source non figée")
    expected = [
        {"id": q["id"], "axis": q["axis"], "text": q["text"]}
        for q in compass.get("questions", [])
    ]
    if len(expected) != 64 or survey.get("questions") != expected:
        issues.append("Les 64 questions doivent correspondre au corpus source approuvé")
    if survey.get("answers") != [-3, -2, -1, 0, 1, 2, 3, "skip"]:
        issues.append("Échelle ou option Sans opinion altérée")
    if survey.get("type") != "consultation_volontaire_non_representative":
        issues.append("Représentativité de la consultation non précisée")
    return issues


def check_manifest_integrity(raw: bytes) -> list[str]:
    if hashlib.sha256(raw).hexdigest() != APPROVED_MANIFEST_SHA256:
        return ["Manifeste 64 questions : empreinte SHA-256 modifiée sans revue"]
    return []


def validate() -> list[str]:
    missing = [key for key, path in FILES.items() if not path.is_file()]
    if missing:
        return ["Fichiers de sondage manquants : " + ", ".join(missing)]
    data = {key: path.read_text("utf-8") for key, path in FILES.items()}
    return (check_text(data) + check_questions(data["manifest"], data["source"])
            + check_manifest_integrity(FILES["manifest"].read_bytes()))


def self_test() -> None:
    payload = {key: path.read_text("utf-8") for key, path in FILES.items()}
    assert not check_text(payload), check_text(payload)
    assert not check_questions(payload["manifest"], payload["source"])
    assert not check_manifest_integrity(FILES["manifest"].read_bytes())
    for key in APPROVED_DOCUMENTARY_SHA256:
        mutated = dict(payload)
        mutated[key] += " "
        assert check_text(mutated), key + " : altération d'un octet acceptée"
    assert check_manifest_integrity(FILES["manifest"].read_bytes() + b" ")
    assert check_manifest_integrity(b"")
    mutations = [
        ("client", "const COLLECTION_OPEN = false;", "const COLLECTION_OPEN = true;"),
        ("client", "const LIVE_OPINION_CONSENT_GRANTED = false;", "const LIVE_OPINION_CONSENT_GRANTED = true;"),
        ("client", "globalThis.crypto.subtle.digest('SHA-256',compassBytes)", "Promise.resolve(new ArrayBuffer(32))"),
        ("client", "hex(compassDigest)!==APPROVED_COMPASS_SHA256", "false"),
        ("client", "response.body.getReader()", "response.arrayBuffer()"),
        ("client", "total>65536", "false"),
        ("client", "reader.releaseLock()", "void reader"),
        ("client", "readBoundedManifest(compassResponse,controller)", "compassResponse.json()"),
        ("compass_client", 'globalThis.crypto.subtle.digest("SHA-256",bytes)', "Promise.resolve(new ArrayBuffer(32))"),
        ("compass_client", "actual!==APPROVED_COMPASS_SHA256", "false"),
        ("compass_client", "observed!==approved", "false"),
        ("compass_client", "signal:controller.signal", "signal:undefined"),
        ("compass_client", "response.body.getReader()", "response.arrayBuffer()"),
        ("compass_client", "total>maxBytes", "false"),
        ("compass_client", "ArrayBuffer.isView(value)", "true"),
        ("compass_client", "value.BYTES_PER_ELEMENT!==1", "false"),
        ("compass_client", "total+=value.byteLength", "total+=0"),
        ("compass_client", "reader.releaseLock()", "void reader"),
        ("compass_client", "clearTimeout(timeoutId)", "/* arrêt du délai perdu */"),
        ("compass_client", "fetchApprovedDocumentary(EVIDENCE_DATA_URL)", "Promise.resolve({})"),
        ("client", "if (!LIVE_OPINION_CONSENT_GRANTED) throw new Error('LIVE_CONSENT_REQUIRED')", "if (false) throw new Error('LIVE_CONSENT_REQUIRED')"),
        ("client", "selections.clear()", "/* purge neutralisée */"),
        ("page", 'id="sondage-review-list"', 'id="récapitulatif-perdu"'),
        ("page", 'Cette case ne constitue pas un consentement à une future collecte.',
         'Cette case permet toute collecte future.'),
        ("page", 'autocomplete="off"', 'autocomplete="on"'),
        ("client", "input.autocomplete = 'off'", "input.autocomplete = 'on'"),
        ("client", "window.addEventListener('pageshow'", "window.addEventListener('pagehide'"),
        ("client", "window.addEventListener('pagehide'", "window.addEventListener('visibilitychange'"),
        ("client", "setTimeout(() => controller.abort(), 15000)", "setTimeout(() => {}, 15000)"),
        ("client", "signal: controller.signal", "signal: undefined"),
        ("client", "clearTimeout(timeoutId)", "void timeoutId"),
        ("client", "if (!COLLECTION_OPEN && !LIVE_OPINION_CONSENT_GRANTED) clearLocalDemo()",
         "if (false) clearLocalDemo()"),
        ("client", "editingReview = true", "editingReview = false"),
        ("client", "choiceNames.get(selections.get(question.id))", "null"),
        ("page", 'id="sondage-privacy-warning"', 'id="avis-absent"'),
        ("client", "$('sondage-age').checked", "true"),
        ("client", "$('sondage-consent').checked", "true"),
        ("client", "client.auth.getUser()", "null"),
        ("client", "globalThis.crypto?.subtle", "true"),
        ("client", "response.arrayBuffer()", "response.json()"),
        ("client", "observed !== APPROVED_MANIFEST_SHA256", "false"),
        ("client", "data.code !== 'RECORDED'", "false"),
        ("client", "data.survey !== SURVEY_ID", "false"),
        ("client", "explicitConsent: LIVE_OPINION_CONSENT_GRANTED", "explicitConsent: true"),
        ("page", 'id="sondage-submit" type="button" disabled',
         'id="sondage-submit" type="button"'),
        ("page", "non représentative", "représentative"),
        ("edge", "NOVA_SURVEY_COLLECTION_ENABLED", "SURVEY_ALWAYS_OPEN"),
        ("edge", "validAnswers(body.answers)", "true"),
        ("edge", "readBoundedJson(req)", "req.text()"),
        ("body", "if (total > MAX_REQUEST_BYTES)", "if (false)"),
        ("edge", "requiredUser(req)", "null"),
        ("sql", "enable row level security", "disable row level security"),
        ("sql", "jsonb_each_text(p_answers)", "jsonb_array_elements(p_answers)"),
        ("config", "verify_jwt = true", "verify_jwt = false"),
    ]
    for key, old, new in mutations:
        assert old in payload[key], "Mutation indisponible : " + old
        altered = dict(payload)
        altered[key] = altered[key].replace(old, new)
        assert check_text(altered), "Régression non détectée : " + old
    obj = json.loads(payload["manifest"])
    obj["questions"][0]["text"] = "Question changée après lancement"
    assert check_questions(json.dumps(obj), payload["source"])
    obj = json.loads(payload["manifest"])
    obj["minimumAge"] = 16
    assert check_questions(json.dumps(obj), payload["source"])
    print(f"OK sondage Nova : {len(mutations)} mutations de consentement, réception, âge, droits et corpus refusées")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    errors = validate()
    if errors:
        for error in errors:
            print("ERREUR sondage Nova :", error)
        raise SystemExit(1)
    print("OK sondage Nova : 64 questions, 18+, confidentialité, SQL/RLS et fonction privées")
