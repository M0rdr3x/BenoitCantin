#!/usr/bin/env python3
"""Preuve SEO des 3 catalogues : canoniques, partages, schémas et visuels officiels.

Évite de présenter des images cassées aux moteurs sociaux et la divergence
entre les URL officielles des catégories. Lecture du dépôt seulement.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re

from validate_sinjira_catalogues import BASE, BANNERS, PAGES, ROOT, ROUTES


class Metadata(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: list[str] = []
        self.titles: list[str] = []
        self.in_title = False
        self.links: list[dict[str, str]] = []
        self.meta: list[dict[str, str]] = []
        self.schema: list[str] = []
        self.in_schema = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {k: v or "" for k, v in attrs}
        if tag == "html":
            self.lang.append(data.get("lang", ""))
        if tag == "title":
            self.in_title = True
        if tag == "link":
            self.links.append(data)
        if tag == "meta":
            self.meta.append(data)
        if tag == "script" and data.get("type") == "application/ld+json":
            self.in_schema = True
            self.schema.append("")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.in_schema:
            self.in_schema = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.titles.append(data)
        if self.in_schema:
            self.schema[-1] += data


def verify_html(kind: str, html: str) -> list[str]:
    errors: list[str] = []
    parser = Metadata()
    parser.feed(html)
    route = BASE + ROUTES[kind]
    image = BASE + "/" + BANNERS[kind]["path"]
    canonical = [x.get("href") for x in parser.links
                 if x.get("rel") == "canonical"]
    if canonical != [route]:
        errors.append(f"{kind}: URL canonique absente, dupliquée ou incorrecte")

    for lang in ("fr-CA", "x-default"):
        values = [x.get("href") for x in parser.links
                  if x.get("rel") == "alternate" and x.get("hreflang") == lang]
        if values != [route]:
            errors.append(f"{kind}: langue {lang} non conforme")

    title = "".join(parser.titles).strip()
    if parser.lang != ["fr-CA"] or not title or title.count("| SINJIRA") != 1:
        errors.append(f"{kind}: langue ou titre HTML incorrect")
    if len([x for x in parser.meta if x.get("name") == "description"]) != 1:
        errors.append(f"{kind}: description SEO absente ou dupliquée")

    expected = {
        "og:locale": "fr_CA",
        "og:type": "website",
        "og:title": title,
        "og:url": route,
        "og:image": image,
        "twitter:card": "summary_large_image",
        "twitter:title": title,
        "twitter:image": image,
    }
    for key, val in expected.items():
        attr = "name" if key.startswith("twitter:") else "property"
        values = [x.get("content") for x in parser.meta if x.get(attr) == key]
        if values != [val]:
            errors.append(f"{kind}: métadonnée {key} absente, multiple ou divergente")
    for prefix in ("og", "twitter"):
        for suffix in ("description", "image:alt"):
            key = f"{prefix}:{suffix}"
            attr = "name" if prefix == "twitter" else "property"
            values = [x.get("content", "").strip() for x in parser.meta
                      if x.get(attr) == key]
            if len(values) != 1 or len(values[0]) < (30 if suffix == "description" else 18):
                errors.append(f"{kind}: {key} absent ou insuffisant")
    if len(parser.schema) != 1:
        errors.append(f"{kind}: une déclaration JSON-LD unique attendue")
    else:
        try:
            data = json.loads(parser.schema[0])
        except (json.JSONDecodeError, ValueError):
            errors.append(f"{kind}: JSON-LD illisible")
        else:
            nodes = data.get("@graph") if isinstance(data, dict) and isinstance(data.get("@graph"), list) else [data]
            matches = [node for node in nodes
                       if isinstance(node, dict) and node.get("@type") == "CollectionPage"]
            if len(matches) != 1 or matches[0].get("url") != route or (
                matches[0].get("name") != title or
                matches[0].get("inLanguage") != "fr-CA"
            ):
                errors.append(f"{kind}: CollectionPage JSON-LD désalignée")
    return errors


def audit(root: Path) -> list[str]:
    issues: list[str] = []
    for kind in ROUTES:
        path = root / PAGES[kind]
        if not path.is_file() or path.is_symlink():
            issues.append(f"{kind}: fichier de catalogue absent")
        else:
            issues.extend(verify_html(kind, path.read_text("utf-8")))
    return issues


def self_test() -> None:
    for kind in ROUTES:
        html = (ROOT / PAGES[kind]).read_text("utf-8")
        assert not verify_html(kind, html), verify_html(kind, html)
        url = BASE + "/" + BANNERS[kind]["path"]
        for broken in (
            html.replace(url, BASE + "/assets/media/banner-missing.webp"),
            re.sub(r'<meta[^>]+(?:name|property)="(?:twitter|og):image:alt"[^>]*>', "", html),
            html.replace(BASE + ROUTES[kind], BASE + "/projets/sinjira/autre/"),
            html.replace("fr_CA", "en_US"),
            html.replace('type="application/ld+json"', 'type="text/plain"'),
        ):
            assert verify_html(kind, broken), (
                f"{kind}: métadonnées sociales/canoniques malformées acceptées"
            )
    print("OK métadonnées : 3 catalogues, canoniques, JSON-LD, "
          "OG/Twitter, images exactes et mutations négatives")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    errors = audit(args.root.resolve())
    for error in errors:
        print("ERREUR : " + error)
    if errors:
        return 1
    print("OK métadonnées des catalogues SINJIRA : partage et SEO cohérents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
