#!/usr/bin/env python3
"""Nova : prévol hors ligne de confidentialité entre deux bilans publics.

Ce programme ne publie rien, ne lit aucun bulletin individuel et n'autorise
pas l'ouverture des sondages. La comparaison exige le DERNIER bilan publié :
un historique incomplet ne permet pas d'exclure une attaque par différences.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

from validate_nova_public_results import (
    MAX_PUBLIC_BYTES,
    SURVEYS,
    parse_public_snapshot,
    validate,
)


def compare(previous: dict, candidate: dict) -> list[str]:
    errors = ["Bilan précédent invalide : " + e for e in validate(previous, review=True)]
    errors += ["Bilan candidat invalide : " + e for e in validate(candidate, review=True)]
    if errors:
        return errors
    if candidate["publicationStatus"] != "approved_aggregate":
        return ["Pas de bilan approuvé à comparer ; aucune publication autorisée"]

    previous_published = previous["publicationStatus"] == "approved_aggregate"
    if previous_published and candidate["publishedOn"] <= previous["publishedOn"]:
        errors.append("La nouvelle date doit être postérieure à la dernière publication")
    any_change = False

    for survey_id in SURVEYS:
        old = previous["surveys"][survey_id]
        new = candidate["surveys"][survey_id]
        if old["status"] == "not_open":
            # Première publication : seuil initial et cellules déjà vérifiés.
            if new["status"] == "approved_aggregate":
                any_change = True
            continue
        if new["status"] != "approved_aggregate":
            errors.append(f"{survey_id} : retrait d'un bilan déjà publié interdit")
            continue

        before = old["respondents"]
        after = new["respondents"]
        added = after - before
        if added < 0:
            errors.append(f"{survey_id} : compte des répondants en diminution")
            continue
        if added and added < 30:
            errors.append(f"{survey_id} : différence entre bilans de moins de 30 personnes")
        if added:
            any_change = True

        for prior, current in zip(old["questions"], new["questions"]):
            question = prior["id"]
            if prior["status"] != current["status"]:
                errors.append(f"{survey_id}/{question} : changement de suppression non revu")
                continue
            if prior["status"] == "suppressed":
                continue
            differences = [
                current["counts"][value] - prior["counts"][value]
                for value in SURVEYS[survey_id][1]
            ]
            if any(delta < 0 for delta in differences):
                errors.append(f"{survey_id}/{question} : diminution de modalité")
            if sum(differences) != added:
                errors.append(f"{survey_id}/{question} : différences incohérentes")
            if any(0 < delta < 10 for delta in differences):
                errors.append(f"{survey_id}/{question} : petite cellule révélée par différence")

    if not any_change:
        errors.append("Aucune nouvelle vague collective à publier")
    return errors


def read_local(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Fichier absent ou lien symbolique refusé")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_PUBLIC_BYTES:
        raise ValueError("Taille de bilan public invalide")
    return parse_public_snapshot(raw.decode("utf-8", errors="strict"))


def self_test() -> None:
    """Tests exclusivement synthétiques : aucune opinion d'une personne réelle."""
    root = Path(__file__).resolve().parents[1]
    closed_path = root / "projets/projet-nova/data/resultats-sondages-publics-v1.json"
    closed = read_local(closed_path)
    assert not validate(closed, review=True)

    first = deepcopy(closed)
    first.update(publicationStatus="approved_aggregate",
                 publicationApproved=True, privacyReviewApproved=True,
                 publishedOn="2026-10-24", source="Cas de test synthétique",
                 notes="Totaux synthétiques ; ne pas publier.")
    survey = first["surveys"]["nova-orientations-40-v1"]
    survey.update(status="approved_aggregate", respondents=60, questions=[
        {"id": f"q{i:02d}", "status": "published", "total": 60,
         "counts": {"pour": 30, "contre": 30, "sans_opinion": 0}}
        for i in range(1, 41)
    ])
    assert not compare(closed, first), compare(closed, first)

    later = deepcopy(first)
    later["publishedOn"] = "2026-10-25"
    s = later["surveys"]["nova-orientations-40-v1"]
    s["respondents"] = 90
    for row in s["questions"]:
        row["total"] = 90
        row["counts"]["pour"] += 30
    assert not compare(first, later), compare(first, later)

    def rejected(mutator) -> None:
        case = deepcopy(later)
        mutator(case)
        assert compare(first, case), "Une différence divulguante a été acceptée"

    rejected(lambda x: x["surveys"]["nova-orientations-40-v1"].update(respondents=61))
    rejected(lambda x: x["surveys"]["nova-orientations-40-v1"]["questions"][0][
        "counts"].update(pour=51, contre=39))
    rejected(lambda x: x["surveys"]["nova-orientations-40-v1"]["questions"][0][
        "counts"].update(pour=49, contre=41))
    rejected(lambda x: x["surveys"]["nova-orientations-40-v1"]["questions"][0][
        "counts"].update(pour=29, contre=61))
    rejected(lambda x: x["surveys"]["nova-orientations-40-v1"]["questions"][0].update(
        status="suppressed", **{"counts": None}))
    rejected(lambda x: x.update(publishedOn="2026-10-24"))
    rejected(lambda x: x["surveys"]["nova-orientations-40-v1"].update(status="not_open"))
    assert compare(first, first), "Republication sans nouvelle vague acceptée"
    assert compare(closed, closed), "L'état fermé présenté comme publication"
    fake64 = deepcopy(first)
    fake64["surveys"]["nova-consultation-64-v1"].update(
        status="approved_aggregate", respondents=60,
        questions=[
            {"id": f"q{i:02d}", "status": "published", "total": 60,
             "counts": {"-3": 30, "-2": 30, "-1": 0, "0": 0,
                        "1": 0, "2": 0, "3": 0, "skip": 0}}
            for i in range(1, 65)
        ])
    assert not compare(closed, fake64)
    print("OK Nova : bilans synthétiques, nouvelles vagues, petits deltas et retraits testés")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--previous", type=Path, help="Dernier bilan public réellement publié")
    p.add_argument("--candidate", type=Path, help="Nouveau bilan proposé, jamais publié automatiquement")
    p.add_argument("--self-test", action="store_true", help="Tester uniquement des agrégats synthétiques")
    args = p.parse_args()
    if args.self_test:
        self_test()
        if args.previous is None and args.candidate is None:
            return 0
    if args.previous is None or args.candidate is None:
        p.error("Fournir --previous et --candidate, ou utiliser --self-test")
    try:
        errors = compare(read_local(args.previous), read_local(args.candidate))
    except (OSError, ValueError, UnicodeError) as exc:
        print("REFUS : bilan illisible ou invalide :", type(exc).__name__)
        return 1
    if errors:
        for reason in errors:
            print("REFUS :", reason)
        return 1
    print("PREVOL TECHNIQUE OK : revue confidentialité et approbation humaine toujours obligatoires")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
