#!/usr/bin/env python3
"""Contrôle statique des cinq pages de participation du Projet Nova.

Bloque les formulaires, iframes, liens vers des services connus de collecte et
paiement et les déclarations éditoriales obsolètes. Le scanner HTML n'exécute
pas le JavaScript, n'inventorie pas le serveur et ne certifie pas la production.
"""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "projets" / "projet-nova"
PAGES = (
    "participer.html", "avis-legal.html", "recrutement.html",
    "confidentialite.html", "contact.html"
)
PUBLIC_EMAIL = "officiellenovaparti@gmail.com"
OLD_CLAIMS = (
    "qui contient le formulaire intégré de soutien et de préadhésion",
    "Soutenir Projet Nova et accéder au formulaire de recrutement.",
    "Les formulaires servent uniquement à communiquer avec le Projet Nova",
)
URL_PATTERN = re.compile(r"https?://[^\s\"'<>)}\]]+", re.I)
SKIP_TEXT_TAGS = {"script", "style", "template"}


def _domain_is(host: str, suffix: str) -> bool:
    return host == suffix or host.endswith("." + suffix)


def suspicious_destination(value: str) -> str | None:
    """Règle ciblée pour les fournisseurs explicitement bloqués à ce stade.

    Détecte aussi les URL protocol-relative et quelques encodages statiques.
    Il faut revue de code et recette: les scripts externes ne sont pas exécutés
    ni inspectés au-delà de leurs références HTML.
    """
    if not isinstance(value, str):
        return None
    # Decode percent-encoding and JS escaped slashes in static links/strings.
    # Bounded decoding avoids relying on untrusted deeply nested encodings.
    normalized = value
    for _ in range(3):
        updated = unquote(normalized).replace(r"\/", "/")
        if updated == normalized:
            break
        normalized = updated
    candidates = [normalized]
    candidates.extend(URL_PATTERN.findall(normalized))
    for candidate in candidates:
        try:
            candidate = candidate.strip().strip(";,")
            # Browser-normal protocol-relative links must be inspected too.
            if candidate.startswith("//"):
                candidate = "https:" + candidate
            url = urlsplit(candidate)
        except ValueError:
            continue
        if url.scheme not in ("http", "https"):
            continue
        host = (url.hostname or "").casefold().rstrip(".")
        path = (url.path or "").casefold()
        if (host == "forms.gle" or
            (host == "docs.google.com" and path.startswith("/forms")) or
            _domain_is(host, "formspree.io") or
            _domain_is(host, "formsubmit.co") or
            _domain_is(host, "typeform.com") or
            _domain_is(host, "jotform.com")):
            return "fournisseur de formulaire externe"
        if (host in ("checkout.stripe.com", "buy.stripe.com", "paypal.me") or
            (_domain_is(host, "paypal.com") and (
                path.startswith("/donate") or
                path.startswith("/paypalme") or
                (path == "/cgi-bin/webscr" and
                 any(token in url.query.casefold() for token in
                     ("cmd=_donations", "cmd=_xclick", "cmd=_s-xclick")))
            ))):
            return "service de paiement ou de don"
    return None


class SiteHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms = 0
        self.iframes = 0
        self.links: set[str] = set()
        self.mailto_valid = False
        self.external: list[str] = []
        self.visible: list[str] = []
        self.ignore: list[str] = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag in SKIP_TEXT_TAGS:
            self.ignore.append(tag)
        if tag == "form":
            self.forms += 1
        if tag == "iframe":
            # No iframe is needed on the five participation/privacy pages.
            self.iframes += 1
        for key, value in attrs.items():
            if not isinstance(value, str):
                continue
            reason = suspicious_destination(value)
            if reason:
                self.external.append(reason)
        if tag == "a":
            href = attrs.get("href", "")
            if isinstance(href, str):
                self.links.add(href)
                if (href.lower().startswith("mailto:") and
                    "template" not in self.ignore and
                    "hidden" not in attrs and
                    str(attrs.get("aria-hidden") or "").casefold() != "true" and
                    "display:none" not in str(attrs.get("style") or "").replace(" ", "").casefold()):
                    try:
                        address = urlsplit(href).path
                    except ValueError:
                        address = ""
                    if address.casefold() == PUBLIC_EMAIL:
                        self.mailto_valid = True

    def handle_startendtag(self, tag, attributes):
        self.handle_starttag(tag, attributes)
        if tag in SKIP_TEXT_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in SKIP_TEXT_TAGS and tag in self.ignore:
            self.ignore.remove(tag)

    def handle_data(self, data):
        # Search script strings separately even though they are not visible.
        if "script" in self.ignore:
            reason = suspicious_destination(data)
            if reason:
                self.external.append(reason)
        elif not self.ignore:
            self.visible.append(data)


def validate(site_root: Path) -> list[str]:
    problems = []
    pages: dict[str, tuple[str, SiteHTML]] = {}
    for name in PAGES:
        path = site_root / name
        if not path.is_file():
            problems.append(f"Page absente : {name}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            problems.append(f"{name} : source illisible ou non UTF-8")
            continue
        page = SiteHTML()
        page.feed(content)
        page.close()
        pages[name] = (content, page)
        if page.forms:
            problems.append(f"{name} : élément form interdit")
        if page.iframes:
            problems.append(f"{name} : iframe interdit dans le périmètre")
        if page.external:
            problems.append(f"{name} : destination externe de collecte ou paiement ({', '.join(sorted(set(page.external)))})")
        if any(phrase.casefold() in content.casefold() for phrase in OLD_CLAIMS):
            problems.append(f"{name} : ancienne déclaration de formulaire actif")

    if "participer.html" in pages:
        content, page = pages["participer.html"]
        visible = " ".join(page.visible).casefold()
        for phrase in ("contact volontaire", "formulaires externes", "suspendus"):
            if phrase not in visible:
                problems.append(f"participer.html : mention visible manquante — {phrase}")
        for href in ("recrutement.html", "confidentialite.html"):
            if href not in page.links:
                problems.append(f"participer.html : lien actif manquant vers {href}")
        if "visionneuse.html?doc=formulaire-soutien" in content:
            problems.append("participer.html : ancien lien de soutien encore actif")

    if "avis-legal.html" in pages:
        _, page = pages["avis-legal.html"]
        visible = " ".join(page.visible).casefold()
        if "n’exploite actuellement pas de formulaire externe" not in visible:
            problems.append("avis-legal.html : suspension du formulaire non décrite de manière visible")

    if "recrutement.html" in pages:
        _, page = pages["recrutement.html"]
        visible = " ".join(page.visible).casefold()
        if "aucun paiement" not in visible:
            problems.append("recrutement.html : interdiction de paiement non indiquée")
        if "contact volontaire direct" not in visible:
            problems.append("recrutement.html : contact volontaire non confirmé")

    if "confidentialite.html" in pages:
        _, page = pages["confidentialite.html"]
        visible = " ".join(page.visible).casefold()
        if "formulaires publics externes" not in visible:
            problems.append("confidentialite.html : suspension des formulaires absente")

    if "contact.html" in pages:
        _, page = pages["contact.html"]
        if not page.mailto_valid:
            problems.append("contact.html : lien actif du courriel public manquant")

    return problems


def main() -> int:
    results = validate(ROOT)
    if results:
        for problem in results:
            print("ÉCHEC:", problem)
        return 1
    print("OK : cohérence statique de cinq pages publiques de Projet Nova.")
    print("Limites : pas de contrôle des scripts externes dynamiques, des courriels,")
    print("de la production, des habilitations ou de la légalité électorale.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
