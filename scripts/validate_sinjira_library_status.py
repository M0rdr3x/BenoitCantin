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


def audit_commerce(purchases: str, licenses: str) -> list[str]:
    problems: list[str] = []
    if "Aucun achat payant associé pour le moment" in purchases:
        problems.append("Achats : fausse absence de paiement affirmée avant vérification")
    if "Cette section ne consulte pas actuellement d'historique de paiements" not in purchases:
        problems.append("Achats : limite du suivi des paiements non expliquée")
    if 'href="/compte/bibliotheque.html"' not in purchases:
        problems.append("Achats : lien vers les droits numériques vérifiés absent")
    if "Licences SINJIRA™ — mode gratuit" in licenses:
        problems.append("Licences : statut gratuit généralisé sans base")
    if "codes et droits numériques du compte" not in licenses:
        problems.append("Licences : distinction code et droits absente")
    return problems


def self_test() -> None:
    html = (ROOT / "compte/bibliotheque.html").read_text("utf-8")
    js = (ROOT / "assets/js/sinjira-library-v24-4-61.js").read_text("utf-8")
    assert not audit(html, js), audit(html, js)
    purchases = (ROOT / "compte/mes-achats.html").read_text("utf-8")
    licenses = (ROOT / "compte/licences.html").read_text("utf-8")
    assert not audit_commerce(purchases, licenses), audit_commerce(purchases, licenses)
    for broken in (
        purchases.replace(
            "Historique des paiements en ligne",
            "Aucun achat payant associé pour le moment"
        ),
        purchases.replace('href="/compte/bibliotheque.html"',
                          'href="/compte/page-inexistante.html"'),
    ):
        assert audit_commerce(broken, licenses), "Régression Achats acceptée"
    assert audit_commerce(purchases, licenses.replace(
        "codes et droits numériques du compte", "mode gratuit"
    )), "Régression Licences acceptée"
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
    errors.extend(audit_commerce(
        (ROOT / "compte/mes-achats.html").read_text("utf-8"),
        (ROOT / "compte/licences.html").read_text("utf-8")
    ))
    for error in errors:
        print("ERREUR : " + error)
    if errors:
        return 1
    print("OK : les droits de bibliothèque sont présentés sans supposition")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
