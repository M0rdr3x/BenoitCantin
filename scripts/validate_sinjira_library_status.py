#!/usr/bin/env python3
"""Preuve hors ligne : ne jamais inventer les achats ou le rôle du membre.

Ce test vérifie le contrat du frontend uniquement. Les autorisations
réelles restent imposées côté Supabase/RLS et par les fonctions privées.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Structure(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.summary = 0
        self.live = 0
        self.counter_names: list[str] = []
        self.routes: set[str] = set()
        self.numbers: list[str] = []
        self.reading_summary = False
        self.summary_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "span" and "data-library-summary" in data:
            self.summary += 1
            self.live += int(data.get("aria-live") == "polite")
            self.reading_summary = True
        if tag == "strong":
            for name in ("project", "read", "entitlement", "request"):
                key = "data-library-" + name + "-count"
                if key in data:
                    self.counter_names.append(key)
                    self.numbers.append(data.get("aria-label") or "")
        if tag == "a" and data.get("href", "").startswith("/projets/sinjira/"):
            self.routes.add(data["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "span":
            self.reading_summary = False

    def handle_data(self, data: str) -> None:
        if self.reading_summary:
            self.summary_text += data


def audit(html: str, js: str) -> list[str]:
    structure = Structure()
    structure.feed(html)
    errors: list[str] = []
    if structure.summary != 1 or structure.live != 1:
        errors.append("Région de statut aria-live manquante ou dupliquée")
    if "Vérification de vos accès et droits numériques en cours" not in structure.summary_text:
        errors.append("Aucun état initial neutre de vérification")
    if "Aucun achat ou service payant n’est activé actuellement" in html:
        errors.append("Fausse affirmation d'absence d'achat avant authentification")
    if len(set(structure.counter_names)) != 4 or len(structure.counter_names) != 4:
        errors.append("Statistiques des quatre ressources incomplètes")
    if len(structure.numbers) != 4 or any(v != "En cours de vérification" for v in structure.numbers):
        errors.append("Zéro droits avant réponse API non autorisé")
    for category in ("romans", "jeux", "logiciels"):
        if f"/projets/sinjira/{category}/" not in structure.routes:
            errors.append("Raccourci de catégorie manquant: " + category)
    expectations = (
        "const isOwner=!ownerResult.error&&ownerResult.data===true;",
        "const isAdmin=!adminResult.error&&adminResult.data===true;",
        "const rolesVerified=!ownerResult.error&&!adminResult.error;",
        "const entitlementsVerified=!entitlementsResult.error;",
        "entitlementsVerified?entitlements.length:'—'",
        "if(!entitlementsVerified){",
        "Vérification temporairement indisponible",
        "renderEntitlements(entitlements,isOwner,entitlementsVerified)",
        "Aucun droit numérique explicite confirmé pour ce compte.",
        "Certains droits ne peuvent pas être vérifiés pour le moment.",
        "getSupabase().functions.invoke('get-novel-file-url'",
        "const errors=[adminResult,ownerResult,projectsResult",
    )
    for marker in expectations:
        if marker not in js:
            errors.append("Contrat de droits incomplet: " + marker[:60])
    if "data-open-full-novel" in html:
        errors.append("Bouton de roman intégral avant droits vérifiés")
    return errors


def self_test() -> None:
    html = (ROOT / "compte/bibliotheque.html").read_text("utf-8")
    js = (ROOT / "assets/js/sinjira-library-v24-4-61.js").read_text("utf-8")
    assert not audit(html, js), audit(html, js)
    for broken in (
        html.replace("Vérification de vos accès et droits numériques en cours…",
                     "Aucun achat ou service payant n’est activé actuellement."),
        html.replace('data-library-summary aria-live="polite"',
                     'data-library-summary'),
        html.replace('/projets/sinjira/logiciels/', '/projets/sinjira/faux/'),
    ):
        assert audit(broken, js), "Texte ou raccourci trompeur accepté"
    for broken in (
        js.replace("const entitlementsVerified=!entitlementsResult.error;",
                   "const entitlementsVerified=true;"),
        js.replace("const isOwner=!ownerResult.error&&ownerResult.data===true;",
                   "const isOwner=true;"),
        js.replace("if(!entitlementsVerified){", "if(false){"),
    ):
        assert audit(html, broken), "Droits accordés sans vérification acceptés"
    print("OK bibliothèque : chargement neutre et erreurs de droits non assimilées à zéro")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    html = (ROOT / "compte/bibliotheque.html").read_text("utf-8")
    js = (ROOT / "assets/js/sinjira-library-v24-4-61.js").read_text("utf-8")
    errors = audit(html, js)
    for error in errors:
        print("ERREUR : " + error)
    if errors:
        return 1
    print("OK : les droits de bibliothèque sont présentés sans supposition")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
