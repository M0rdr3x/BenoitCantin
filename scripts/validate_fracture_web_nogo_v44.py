#!/usr/bin/env python3
"""SINJIRA — Fracture V44: garde anti-réactivation Web non approuvée.

Contrôle statique FAIL-CLOSED des pages publiques. Pas d'appel réseau,
pas de connexion Supabase, pas d'inspection de données utilisateur.
N'est pas une preuve de sécurité de toutes les dépendances JavaScript.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAY = ROOT / "projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html"
LANDING = ROOT / "projets/sinjira/jeux/fracture-du-reseau-mere/index.html"

ALLOWED_PLAY_SCRIPTS = frozenset({
    "/assets/js/site.js",
    "/assets/js/v19-session.js",
})
BANNED_INTERACTIVE_TAGS = frozenset({
    "form", "input", "textarea", "select", "iframe", "object", "embed",
})
BANNED_DATA_PREFIXES = (
    "data-fracture-start",
    "data-fracture-join",
    "data-fracture-lobby",
    "data-fracture-party",
    "data-game-action",
)
BANNED_RUNTIME_TOKENS = (
    "fracture_engine_start",
    "fracture_engine_submit_",
    "fracture_engine_pick",
    "create_fracture_party",
    "join_fracture_party",
    "sinjira-fracture-online.js",
    "getsupabase(",
)
REQUIRED_PLAY_TEXT = (
    "mode web en mise à niveau",
    "temporairement suspendues",
    "sièges invisibles",
    "contrôle humain",
    "2n cartes",
    "deux passages",
    "3 points",
)


class PageInspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.script_sources: list[str] = []
        self.inline_scripts: list[str] = []
        self.hrefs: list[str] = []
        self.text: list[str] = []
        self._script_depth = 0
        self._script_contents: list[str] = []

    def handle_starttag(self, tag: str, attributes):
        attrs = dict(attributes)
        if tag in BANNED_INTERACTIVE_TAGS:
            self.errors.append(f"Balise interactive interdite : {tag}")
        for key, value in attributes:
            if key.startswith("on"):
                self.errors.append(f"Gestionnaire JavaScript inline interdit : {key}")
            if key.startswith(BANNED_DATA_PREFIXES):
                self.errors.append(f"Commande de lobby interdite : {key}")
            if key in {"href", "src", "action", "formaction"} and value:
                stripped = value.strip().lower()
                if stripped.startswith(("javascript:", "data:text/html", "vbscript:")):
                    self.errors.append(f"URL exécutable interdite : {key}")
        if tag == "script":
            src = attrs.get("src")
            if src:
                self.script_sources.append(src)
            else:
                self._script_depth += 1
                self._script_contents.append("")
        if tag == "a":
            self.hrefs.append(attrs.get("href") or "")

    def handle_endtag(self, tag: str):
        if tag == "script" and self._script_depth:
            self._script_depth -= 1
            self.inline_scripts.append(self._script_contents.pop())

    def handle_data(self, data: str):
        if self._script_depth:
            self._script_contents[-1] += data
        else:
            self.text.append(data)

    def handle_startendtag(self, tag: str, attrs):
        self.handle_starttag(tag, attrs)
        if tag == "script":
            self.handle_endtag(tag)


def validate_public_fracture(play_html: str, landing_html: str) -> list[str]:
    errors: list[str] = []
    play = PageInspector()
    play.feed(play_html)
    play.close()
    errors.extend(play.errors)
    for src in play.script_sources:
        path = src.split("?", 1)[0].split("#", 1)[0]
        if path not in ALLOWED_PLAY_SCRIPTS:
            errors.append(f"Script non approuvé dans le mode Web suspendu : {path}")
    if len(play.script_sources) != 2 or set(
        src.split("?", 1)[0] for src in play.script_sources
    ) != ALLOWED_PLAY_SCRIPTS:
        errors.append("Les seuls scripts attendus sont site.js et v19-session.js.")
    if play.inline_scripts:
        errors.append("Script inline interdit sur le mode Web suspendu.")
    text = " ".join(play.text).lower()
    for phrase in REQUIRED_PLAY_TEXT:
        if phrase not in text:
            errors.append(f"État de suspension ou règle de référence absent : {phrase}")
    for target in ("regles.html", "feuille-de-score.html"):
        if target not in play.hrefs:
            errors.append(f"Alternative physique ou règles indisponible : {target}")
    for token in BANNED_RUNTIME_TOKENS:
        if token in play_html.lower():
            errors.append(f"Initialisation de moteur non approuvée : {token}")
    if re.search(r"<\s*meta\b[^>]*\bhttp-equiv\s*=\s*['\"]?refresh", play_html, re.I):
        errors.append("Redirection automatique non approuvée.")
    landing = PageInspector()
    landing.feed(landing_html)
    landing.close()
    errors.extend(landing.errors)
    if "jouer.html" not in landing.hrefs:
        errors.append("Le statut de suspension n'est plus accessible depuis la présentation.")
    for src in landing.script_sources:
        if "fracture-online" in src.lower() or "fracture-engine" in src.lower():
            errors.append("Moteur historique chargé depuis la présentation publique.")
    return errors


def validate_files() -> list[str]:
    return validate_public_fracture(
        PLAY.read_text(encoding="utf-8"),
        LANDING.read_text(encoding="utf-8"),
    )


if __name__ == "__main__":
    failures = validate_files()
    for finding in failures:
        print("ÉCHEC V44:", finding)
    if failures:
        raise SystemExit(1)
    print("OK V44 — pages de Fracture publiques toujours sans lobby actif.")
