#!/usr/bin/env python3
"""Contrôle sans réseau des avant-projets Nova 64/40 en lecture seule.

Vérifie les textes exactement, les options, le statut fermé et l'absence
d'éléments de saisie ou de code réseau. Sources GitHub anciennes conservées.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT / "projets" / "projet-nova"
DRAFTS = ROOT / "docs" / "nova-sondages"
PAGE = NOVA / "sondages-a-valider.html"
SOURCE_SHA = "5726b7262a89ddb42d210407c6d5473cc815feb0"


def validate() -> list[str]:
    errors: list[str] = []
    body = PAGE.read_text(encoding="utf-8")
    a = json.loads((DRAFTS / "sondage-64-candidat-v1.json").read_text(encoding="utf-8"))
    b = json.loads((DRAFTS / "consultation-40-candidat-v1.json").read_text(encoding="utf-8"))
    compass = json.loads((NOVA / "data" / "boussole-electorale-v2.json").read_text(encoding="utf-8"))

    if a.get("minimumAge") != 18 or len(a.get("questions", [])) != 64:
        errors.append("Corpus candidat opinion 64 ou âge invalide")
    if b.get("minimumAge") != 18 or b.get("collectionOpen") is not False or len(b.get("questions", [])) != 40:
        errors.append("Corpus candidat consultatif 40 ou collecte non fermée")
    if a.get("answers") != [-3, -2, -1, 0, 1, 2, 3, "skip"]:
        errors.append("Choix du sondage de 64 questions non conformes")
    if b.get("choices") != ["pour", "contre", "sans_opinion"]:
        errors.append("Choix de la consultation de 40 questions non conformes")
    for expected_type, source, count in (("opinion", a, 64), ("consultation", b, 40)):
        matches = re.findall(
            r'<li data-type="' + expected_type +
            r'" data-id="(q[0-9]{2})"><p>(.*?)</p></li>',
            body,
            re.DOTALL,
        )
        if len(matches) != count:
            errors.append(f"HTML : {expected_type}, {len(matches)}/{count} propositions")
            continue
        for index, ((listed_id, listed_text), question) in enumerate(zip(matches, source["questions"]), start=1):
            expected_id = "q" + str(index).zfill(2)
            if listed_id != expected_id or question.get("id") != expected_id:
                errors.append(f"{expected_type}: ordre ou identifiant incorrect Q{index}")
            if html.unescape(listed_text) != question.get("text"):
                errors.append(f"{expected_type}: formulation modifiée Q{index}")

    candidate_by_id = {q["id"]: q["text"] for q in a["questions"]}
    compass_by_id = {q["id"]: q["text"] for q in compass["questions"]}
    if candidate_by_id != compass_by_id:
        errors.append("Le corpus 64 candidat ne correspond plus à sa source boussole : revue de version requise")

    if not all(snippet in body for snippet in (
        '<meta name="robots" content="noindex,follow">',
        "Aucune réponse n’est enregistrée ici",
        "aucun vote possible",
        "non approuvés",
        "pas un référendum officiel",
        SOURCE_SHA,
        'id="sondage-64"',
        'id="consultation-40"',
    )):
        errors.append("Prévisualisation : avertissement ou provenance absent")
    if re.search(r"<\s*(form|input|textarea|select|button|script)\b", body, re.I):
        errors.append("Prévisualisation : élément interactif susceptible de recueillir des réponses")
    if re.search(r"\b(fetch\(|XMLHttpRequest|navigator\.sendBeacon|localStorage|sessionStorage)\b", body, re.I):
        errors.append("Prévisualisation : collecte ou stockage de données suspect")
    if re.search(r'href="(?:https?://[^"]*\.(?:js|ts)|[^"]*submit[^"]*)"', body, re.I):
        errors.append("Prévisualisation : lien de soumission ou script non attendu")

    home = (NOVA / "index.html").read_text(encoding="utf-8")
    poll_page = (NOVA / "sondage-citoyen.html").read_text(encoding="utf-8")
    if 'href="sondages-a-valider.html"' not in home or 'href="sondages-a-valider.html"' not in poll_page:
        errors.append("Accès aux projets de questionnaires absent de l'accueil ou du sondage")
    if 'id="poll-send"' not in poll_page or 'id="poll-live-status"' not in poll_page:
        errors.append("Page du sondage de huit questions détériorée")
    if not (NOVA / "data/sondage-citoyen-v1.json").is_file():
        errors.append("Corpus du sondage de huit questions absent")
    return errors


if __name__ == "__main__":
    failures = validate()
    for failure in failures:
        print("ECHEC questionnaire candidat :", failure)
    if failures:
        raise SystemExit(1)
    print("OK Nova : 64 + 40 formulations candidates identiques aux sources, aucune saisie, 18+, aucune collecte, liens publics.")
