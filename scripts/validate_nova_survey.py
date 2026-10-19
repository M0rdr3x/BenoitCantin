#!/usr/bin/env python3
"""Validation anti-régression du sondage politique sensible Nova 18+.

Aucune connexion réseau; aucun compte ni réponse de personne réelle.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT / "projets/projet-nova"
FILES = {
    "page": NOVA / "sondage.html",
    "client": NOVA / "assets/sondage.js",
    "style": NOVA / "assets/sondage.css",
    "manifest": NOVA / "data/sondage-questions-v1.json",
    "source": NOVA / "data/boussole-electorale-v2.json",
    "index": NOVA / "index.html",
    "method": NOVA / "SONDAGE_METHODOLOGIE_ET_ACTIVATION.md",
    "sql": ROOT / "supabase/migrations/20261019170000_nova_adult_opinion_survey_v1.sql",
    "edge": ROOT / "supabase/functions/nova-survey-submit/index.ts",
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
           'non représentative', '64 propositions')
    demand("client", "const COLLECTION_OPEN = false;",
           "function eligible()", "$('sondage-age').checked",
           "$('sondage-consent').checked",
           "selections.size !== questions.length",
           "explicitConsent: true", "age18Confirmed: true",
           "validManifest(manifest)", "question.id",
           "value !== 'skip'", "const answers = Object.create(null)",
           "client.auth.getUser()", "client.functions.invoke('nova-survey-submit'",
           "if (!COLLECTION_OPEN || recorded || submitting || !eligible()) return",
           "if (recorded) return", "text.textContent = label")
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
           "new TextEncoder().encode(raw).length > 8192")
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


def validate() -> list[str]:
    missing = [key for key, path in FILES.items() if not path.is_file()]
    if missing:
        return ["Fichiers de sondage manquants : " + ", ".join(missing)]
    data = {key: path.read_text("utf-8") for key, path in FILES.items()}
    return check_text(data) + check_questions(data["manifest"], data["source"])


def self_test() -> None:
    payload = {key: path.read_text("utf-8") for key, path in FILES.items()}
    assert not check_text(payload), check_text(payload)
    assert not check_questions(payload["manifest"], payload["source"])
    mutations = [
        ("client", "const COLLECTION_OPEN = false;", "const COLLECTION_OPEN = true;"),
        ("client", "$('sondage-age').checked", "true"),
        ("client", "$('sondage-consent').checked", "true"),
        ("client", "client.auth.getUser()", "null"),
        ("client", "explicitConsent: true", "explicitConsent: false"),
        ("page", 'id="sondage-submit" type="button" disabled',
         'id="sondage-submit" type="button"'),
        ("page", "non représentative", "représentative"),
        ("edge", "NOVA_SURVEY_COLLECTION_ENABLED", "SURVEY_ALWAYS_OPEN"),
        ("edge", "validAnswers(body.answers)", "true"),
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
    print("OK sondage Nova : 15 mutations de consentement, âge, droits et corpus refusées")


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
