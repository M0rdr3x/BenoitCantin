#!/usr/bin/env python3
"""Scénarios négatifs contre la réactivation des formulaires Projet Nova.

Aucun HTTP distant, aucune écriture, aucun courriel envoyé.
"""
from __future__ import annotations

import contextlib
import io
from unittest.mock import patch

import validate_nova_form_decommission as guard


def evaluate(overrides: dict[str, str]) -> tuple[int, str]:
    original = guard.read
    def fixture(path: str) -> str:
        return overrides.get(path, original(path))
    output = io.StringIO()
    with patch.object(guard, "read", side_effect=fixture):
        with contextlib.redirect_stdout(output):
            result = guard.main()
            # Contrôle supplémentaire distinct du validateur de main verrouillé
            # par empreinte Git ; vérifie les deux canaux publics séparés.
            contact = guard.read("contact.html")
            for required in ("Canaux séparés", 'href="../../contact.html"', "/compte/"):
                if required not in contact:
                    print("ECHEC: séparation des canaux Projet Nova: " + required)
                    result = 1
    return result, output.getvalue()


def main() -> int:
    status, message = evaluate({})
    if status:
        raise AssertionError("Page et documentation sûres rejetées: " + message)

    cases = [
        (
            "ancien formulaire actif",
            "contact.html",
            guard.read("contact.html") + '<form method="post"></form>',
            "formulaire HTML",
        ),
        (
            "canaux mélangés",
            "contact.html",
            guard.read("contact.html").replace("Canaux séparés", "Canaux communs"),
            "séparation des canaux",
        ),
        (
            "confirmation mensongère",
            "merci-formulaire.html",
            guard.read("merci-formulaire.html")
            + "Votre formulaire de soutien et de préadhésion a été transmis.",
            "ancien état trompeur",
        ),
        (
            "retrait du noarchive",
            "merci-formulaire.html",
            guard.read("merci-formulaire.html").replace("noarchive", "index", 1),
            "robots incomplet",
        ),
        (
            "perte de redirection",
            "formulaire-soutien.html",
            guard.read("formulaire-soutien.html").replace(
                'content="0; url=/projets/projet-nova/recrutement.html"',
                'content="0; url=/compte/"',
            ),
            "meta refresh exacte",
        ),
        (
            "ancien prestataire mentionné",
            "FORMULAIRE_CONTACT.md",
            guard.read("FORMULAIRE_CONTACT.md") + "\nhttps://formspree.io/f/old\n",
            "endpoint Formspree",
        ),
        (
            "ancien canal administratif",
            "ADMINISTRATION_FORMULAIRES.md",
            guard.read("ADMINISTRATION_FORMULAIRES.md")
            + "\nkingtyrano@gmail.com\n",
            "adresse administrative privée",
        ),
    ]
    for label, filename, altered, expected in cases:
        if altered == guard.read(filename):
            raise AssertionError("Mutation inactive: " + label)
        state, messages = evaluate({filename: altered})
        if state == 0 or expected not in messages:
            raise AssertionError(
                f"Régression non détectée : {label}: état={state}, détails={messages[:250]}"
            )
    print(
        f"OK formulaires Nova : scénario normal + {len(cases)} mutations "
        "détectées, aucun prestataire actif et canaux séparés."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
