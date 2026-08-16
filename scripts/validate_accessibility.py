#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRITICAL_PAGES = [
    ROOT / "index.html",
    ROOT / "a-propos.html",
    ROOT / "contact.html",
    ROOT / "projets" / "sinjira" / "index.html",
    ROOT / "projets" / "sinjira" / "registre" / "index.html",
    ROOT / "projets" / "projet-nova" / "index.html",
]


class AuditParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.title_depth = 0
        self.title_text = ""
        self.h1_count = 0
        self.main_ids = set()
        self.links = []
        self.images_missing_alt = 0
        self.buttons_without_name = 0
        self._button_depth = 0
        self._button_text = []
        self._button_has_name = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = (a.get("lang") or "").strip()
        elif tag == "title":
            self.title_depth += 1
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            if a.get("id"):
                self.main_ids.add(a["id"])
        elif tag == "a":
            self.links.append((a.get("href") or "", (a.get("class") or ""), a.get("aria-label") or ""))
        elif tag == "img" and "alt" not in a:
            self.images_missing_alt += 1
        elif tag == "button":
            self._button_depth = 1
            self._button_text = []
            self._button_has_name = bool((a.get("aria-label") or "").strip() or (a.get("title") or "").strip())
        elif self._button_depth:
            self._button_depth += 1

    def handle_endtag(self, tag):
        if tag == "title" and self.title_depth:
            self.title_depth -= 1
        if self._button_depth:
            self._button_depth -= 1
            if tag == "button" and self._button_depth == 0:
                if not self._button_has_name and not "".join(self._button_text).strip():
                    self.buttons_without_name += 1

    def handle_data(self, data):
        if self.title_depth:
            self.title_text += data
        if self._button_depth:
            self._button_text.append(data)


def main() -> int:
    errors = []
    for page in CRITICAL_PAGES:
        if not page.exists():
            errors.append(f"Page critique absente: {page.relative_to(ROOT)}")
            continue
        parser = AuditParser()
        parser.feed(page.read_text("utf-8", errors="ignore"))
        rel = page.relative_to(ROOT)
        if not parser.lang:
            errors.append(f"{rel}: attribut lang absent sur <html>.")
        if not parser.title_text.strip():
            errors.append(f"{rel}: <title> vide ou absent.")
        if parser.h1_count != 1:
            errors.append(f"{rel}: exactement un H1 attendu, trouvé {parser.h1_count}.")
        if not parser.main_ids:
            errors.append(f"{rel}: repère <main id=...> absent.")
        has_skip = any("skip-link" in classes.split() and href.startswith("#") for href, classes, _ in parser.links)
        if not has_skip:
            errors.append(f"{rel}: lien d’évitement .skip-link absent.")
        if parser.images_missing_alt:
            errors.append(f"{rel}: {parser.images_missing_alt} image(s) sans attribut alt.")
        if parser.buttons_without_name:
            errors.append(f"{rel}: {parser.buttons_without_name} bouton(s) sans nom accessible.")

    css = (ROOT / "assets" / "css" / "site.css").read_text("utf-8", errors="ignore")
    if ":focus-visible" not in css:
        errors.append("assets/css/site.css: style :focus-visible absent.")
    if "prefers-reduced-motion" not in css:
        errors.append("assets/css/site.css: prise en charge prefers-reduced-motion absente.")
    if ".skip-link" not in css:
        errors.append("assets/css/site.css: style du lien d’évitement absent.")

    if errors:
        print(f"ECHEC accessibilité: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1
    print("OK accessibilité: repères, titres, alternatives, clavier et réduction des animations vérifiés sur les pages critiques.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
