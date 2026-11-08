#!/usr/bin/env python3
"""Contrat défensif du socle mécanique Fracture V36. Aucun backend activé."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/"assets/js/sinjira-fracture-mechanics-v36.mjs"
TESTS=ROOT/"tests/games/test_fracture_mechanics_v36.mjs"
RULES=ROOT/"projets/sinjira/jeux/fracture-du-reseau-mere/regles.html"
GAME=ROOT/"projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html"
DOC=ROOT/"docs/SINJIRA_FRACTURE_MOTEUR_V36.md"

def validate():
    errors=[]
    module=MODEL.read_text(encoding="utf-8")
    tests=TESTS.read_text(encoding="utf-8")
    rules=RULES.read_text(encoding="utf-8")
    game=GAME.read_text(encoding="utf-8")
    doc=DOC.read_text(encoding="utf-8")
    expected=[
        "FRACTURE_AGENTS", "FRACTURE_OPERATION_COUNTS",
        "1:30,2:12,3:3", "fractureSeats", "fractureOperationDeck",
        "fractureValidateDeck", "fractureDealRound", "fractureBuildCentre",
        "fractureTwoPasses", "fractureRevealOperationCards",
        "fractureSeatController", "center.length!==config.cardsCentre",
        "discard.length!==config.seats", "hands.some(hand=>hand.cards.length!==2)",
        "express&&h<13", "r%2===1?config.duoFirst:3-config.duoFirst",
    ]
    for item in expected:
        if item not in module:
            errors.append("Contrat moteur absent : "+item)
    for item in [
        "90 cartes", "30×1", "12×2", "3×3", "2N cartes",
        "Deux passages", "Solo", "Duo"
    ]:
        if item not in rules:
            errors.append("Règle de référence non retrouvée : "+item)
    if "Mode Web en mise à niveau" not in game:
        errors.append("L'ancien moteur de jeu Web ne doit pas être réactivé")
    for item in ["12", "fractureBuildCentre", "fractureTwoPasses",
                 "fractureSeatController", "assert.throws"]:
        if item not in tests:
            errors.append("Tests mécaniques absents : "+item)
    for item in ["frontière de sécurité", "ne modifie ni Supabase",
                 "mains et les identités secrètes",
                 "pas la livraison du jeu multijoueur"]:
        if item not in doc:
            errors.append("Documentation des limites absente : "+item)
    # Seuls les exports métiers sont autorisés : pas de réseau, accès DOM,
    # cookies, stockage persistant ou comptes dans le moteur pur.
    no_comments=re.sub(r"/\\*[\\s\\S]*?\\*/|//[^\\n]*","",module)
    for pattern in [
        r"\\bfetch\\s*\\(", r"\\blocalStorage\\s*[.\\[]",
        r"\\bsessionStorage\\s*[.\\[]", r"\\bindexedDB\\b",
        r"\\bdocument\\s*[.\\[]", r"\\bwindow\\s*[.\\[]",
        r"\\bgetSupabase\\s*\\(", r"\\b(?:client|db|s)\\.from\\s*\\(",
        r"\\bWebSocket\\s*\\(", r"\\beval\\s*\\(",
    ]:
        if re.search(pattern,no_comments):
            errors.append("Capacité externe interdite dans le moteur : "+pattern)
    return errors

if __name__=="__main__":
    errors=validate()
    for error in errors:
        print("ÉCHEC:",error)
    if not errors:
        print("OK: mécanique Fracture V36, règles Déduction simplifiée, zéro réseau ni donnée privée")
    raise SystemExit(bool(errors))
