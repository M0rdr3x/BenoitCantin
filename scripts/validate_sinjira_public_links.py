#!/usr/bin/env python3
"""Prouver que les quatre portails SINJIRA ne pointent vers aucun fichier exclu de Pages.

Les fichiers peuvent exister dans le dépôt mais être ABSENTS de _site.
Leur existence locale ne suffit jamais : seul l'inventaire de publication
(généré ou source) établit qu'une route est réellement prévue.
Aucune requête réseau, aucun accès à un compte ni lecture de contenu privé.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from validate_sinjira_catalogues import PAGES, ROOT

INVENTORY = "scripts/pages_public_inventory.txt"
GENERATED = "scripts/pages_generated_inventory.txt"
HOST = "www.benoitcantin.com"


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str]] = []
        self.base_elements = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "base":
            self.base_elements += 1  # Altering relative URL resolution is forbidden.
        for attr in ("href", "src", "srcset", "poster"):
            value = data.get(attr)
            if not value:
                continue
            if (attr == "href" and tag not in {"a", "link"}
                    or attr == "src" and tag not in {
                        "img", "script", "source", "iframe", "video", "audio",
                    }
                    or attr == "srcset" and tag not in {"img", "source"}
                    or attr == "poster" and tag != "video"):
                continue
            if attr == "srcset":
                for entry in value.split(","):
                    fields = entry.strip().split()
                    if fields:
                        self.references.append((f"{tag}.{attr}", fields[0]))
            else:
                self.references.append((f"{tag}.{attr}", value))
        if tag == "meta" and (
            data.get("property") == "og:image"
            or data.get("name") == "twitter:image"
        ):
            self.references.append(("meta.social", data.get("content") or ""))


def read_allowlist(root: Path, name: str) -> set[str]:
    return {line.strip() for line in (root / name).read_text("utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")}


def verify_target(page: Path, ref: str, root: Path,
                  public: set[str], generated: set[str]) -> str | None:
    # urllib.parse supprime silencieusement certains caractères ASCII
    # au début des URL. Refuser la valeur HTML brute avant toute analyse
    # évite qu'un lien ambigu contourne la liste des ressources publiques.
    if ref != ref.strip() or any(ord(char) < 32 or ord(char) == 127 for char in ref):
        return "Espacement ou caractère de contrôle dans le lien"
    if "\\" in ref:
        return "Séparateur de chemin ambigu"
    try:
        parts = urlsplit(ref)
    except ValueError:
        return "URL malformée"
    if parts.scheme and parts.scheme.lower() not in {
        "http", "https", "mailto", "tel",
    }:
        return "Protocole exécutable ou non autorisé"
    if parts.scheme in {"mailto", "tel"}:
        return None
    # Un nom DNS avec un point final, un port :443 ou des identifiants
    # désigne toujours l'hôte officiel, même si netloc != HOST. Ne jamais
    # traiter cette variante comme un site tiers hors de l'allowlist.
    if "%" in parts.netloc or "\\" in parts.netloc:
        return "Autorité URL ambiguë"
    if parts.username is not None or parts.password is not None:
        return "Identifiants intégrés dans l'URL interdits"
    hostname = (parts.hostname or "").rstrip(".").lower()
    if hostname == HOST:
        if parts.netloc != HOST or parts.scheme != "https":
            return "Lien interne non canonique : HTTPS et hôte exact requis"
    elif parts.netloc:
        return None  # Sites tiers explicites; jamais une variante de HOST.
    if parts.scheme == "http":
        return "Lien interne HTTP non sécurisé"
    if not parts.path and parts.fragment and not parts.query:
        return None
    raw = unquote(parts.path)
    if ("\\" in raw or "\x00" in raw or raw.startswith("//")
            or "%2f" in parts.path.lower() or "%5c" in parts.path.lower()):
        return "Chemin encodé ambigu"
    candidate = ((root / raw.lstrip("/")) if raw.startswith("/")
                 else (page.parent / raw))
    if not raw:
        candidate = page
    elif raw.endswith("/"):
        candidate = candidate / "index.html"
    candidate = candidate.resolve()
    try:
        relative = candidate.relative_to(root.resolve()).as_posix()
    except ValueError:
        return "Lien sortant de la racine publique"
    if relative in generated:
        return None
    if relative not in public:
        return "Route absente de l'inventaire Pages approuvé"
    if not candidate.is_file() or candidate.is_symlink():
        return "Fichier public absent ou symbolique"
    return None


def audit(root: Path) -> list[str]:
    try:
        public = read_allowlist(root, INVENTORY)
        generated = read_allowlist(root, GENERATED)
    except OSError:
        return ["Inventaires de publication Pages introuvables"]
    errors: list[str] = []
    for category, rel in PAGES.items():
        page = root / rel
        if not page.is_file():
            errors.append(f"Page de catalogue manquante: {rel}")
            continue
        references = References()
        references.feed(page.read_text("utf-8"))
        if references.base_elements:
            errors.append(f"{category}: élément HTML base non autorisé")
        for tag, ref in references.references:
            issue = verify_target(page, ref, root, public, generated)
            if issue:
                errors.append(f"{category} / {tag} / {ref[:120]} : {issue}")
    return errors


def self_test(root: Path) -> None:
    public = read_allowlist(root, INVENTORY)
    generated = read_allowlist(root, GENERATED)
    page = root / PAGES["accueil"]
    for ref in (
        "/", "romans/", "/projets/sinjira/logiciels/?nav=1#contenu",
        "/compte/bibliotheque.html",
        "https://www.benoitcantin.com/assets/media/sinjira-jeux-banniere-2026.webp",
        "#contenu",
    ):
        assert verify_target(page, ref, root, public, generated) is None, ref
    for ref in (
        "/projets/sinjira/categorie-inexistante/",
        "/scripts/validate_sinjira_catalogues.py",
        "/supabase/config.toml",
        "../../../../fichiers-prives/index.html",
        "javascript:alert(1)",
        "http://www.benoitcantin.com/projets/sinjira/",
        "/projets/sinjira/%2Fsecret",
    ):
        assert verify_target(page, ref, root, public, generated), (
            "Destination interdite acceptée: " + ref
        )
    parser = References()
    parser.feed('<a href="/scripts/validate_sinjira_catalogues.py">Lien</a>'
                '<img srcset="/assets/media/banniere-absente.webp 2x">')
    assert len(parser.references) == 2
    assert all(verify_target(page, url, root, public, generated)
               for _, url in parser.references)
    parser = References()
    parser.feed('<base href="/scripts/"><a href="nimportequoi">X</a>')
    assert parser.base_elements == 1
    issues = audit(root)
    assert not issues, "\n".join(issues)
    print("OK liens publics SINJIRA: exclusions Pages, 4 portails, srcset et liens privés refusés")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test(ROOT)
    issues = audit(ROOT)
    for error in issues:
        print("ERREUR : " + error)
    if issues:
        return 1
    print("OK: chaque lien et ressource locale des 4 portails est approuvé dans Pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
