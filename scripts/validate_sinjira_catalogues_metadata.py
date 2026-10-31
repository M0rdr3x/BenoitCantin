#!/usr/bin/env python3
"""Preuve SEO des 3 catalogues : canoniques, partages, schémas et visuels officiels.

Évite de présenter des images cassées aux moteurs sociaux et la divergence
entre les URL officielles des catégories. Lecture du dépôt seulement.
"""
from __future__ import annotations

import argparse
import hashlib
from tempfile import TemporaryDirectory
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


def audit(root: Path, built: Path | None = None) -> list[str]:
    issues: list[str] = []
    if built is not None and (not built.is_dir() or built.is_symlink()):
        return ["Répertoire de sortie Jekyll absent ou symbolique"]
    for kind in ROUTES:
        relative = PAGES[kind]
        path = root / relative
        if not path.is_file() or path.is_symlink():
            issues.append(f"{kind}: fichier de catalogue source absent")
            continue
        original = path.read_bytes()
        issues.extend(verify_html(kind, original.decode("utf-8")))
        if built is None:
            continue

        # Audit au niveau des OCTETS de l'artefact réel, pas seulement
        # du code source. Jekyll ne doit ni transformer les métadonnées
        # ni altérer ou omettre les visuels de partage officiels.
        delivered = built / relative
        if not delivered.is_file() or delivered.is_symlink():
            issues.append(f"{kind}: page absente ou symbolique dans _site")
        else:
            published = delivered.read_bytes()
            if published != original:
                issues.append(f"{kind}: HTML altéré par la compilation Jekyll")
            try:
                issues.extend(verify_html(kind, published.decode("utf-8")))
            except UnicodeDecodeError:
                issues.append(f"{kind}: HTML généré non UTF-8")

        banner = BANNERS[kind]
        banner_path = banner["path"]
        source_image = root / banner_path
        output_image = built / banner_path
        if not source_image.is_file() or source_image.is_symlink():
            issues.append(f"{kind}: visuel officiel absent des sources")
        if not output_image.is_file() or output_image.is_symlink():
            issues.append(f"{kind}: image de partage absente ou symbolique dans _site")
            continue
        output_bytes = output_image.read_bytes()
        if hashlib.sha256(output_bytes).hexdigest() != banner["sha256"]:
            issues.append(f"{kind}: image partagée non conforme à l'empreinte officielle")
        if source_image.is_file() and not source_image.is_symlink():
            if output_bytes != source_image.read_bytes():
                issues.append(f"{kind}: image WebP altérée pendant la compilation Jekyll")
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
    # Le test négatif simule l'artefact _site sans compiler Jekyll.
    # Toute disparition/altération de page OU de WebP doit être refusée.
    with TemporaryDirectory() as directory:
        built = Path(directory) / "_site"
        for kind in ROUTES:
            for relative in (PAGES[kind], BANNERS[kind]["path"]):
                source = ROOT / relative
                dest = built / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(source.read_bytes())
        assert not audit(ROOT, built), audit(ROOT, built)
        page = built / PAGES["romans"]
        original_html = page.read_bytes()
        page.write_bytes(original_html.replace(
            b"twitter:image", b"twitter:missing", 1
        ))
        assert any("romans:" in msg for msg in audit(ROOT, built)), (
            "Métadonnées du HTML Jekyll modifiées sans détection"
        )
        page.write_bytes(original_html)
        page.unlink()
        assert any("page absente" in msg for msg in audit(ROOT, built)), (
            "Page publiée absente non détectée"
        )
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_bytes(original_html)
        image = built / BANNERS["logiciels"]["path"]
        original_image = image.read_bytes()
        image.write_bytes(original_image[:-1] + bytes([original_image[-1] ^ 1]))
        assert any("empreinte officielle" in msg for msg in audit(ROOT, built)), (
            "Image de partage remplacée sous le même nom acceptée"
        )
        image.write_bytes(original_image)
        image.unlink()
        assert any("image de partage absente" in msg for msg in audit(ROOT, built)), (
            "Image WebP absente du build acceptée"
        )
        assert audit(ROOT, built / "non-existant"), (
            "Répertoire Jekyll inexistant accepté"
        )

    print("OK métadonnées : 3 catalogues, canoniques, JSON-LD, "
          "OG/Twitter, images exactes et mutations négatives source/_site")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--built", type=Path,
                        help="Vérifier les 3 pages et 3 WebP dans l'artefact Jekyll")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    errors = audit(args.root.resolve(),
                   args.built.resolve() if args.built is not None else None)
    for error in errors:
        print("ERREUR : " + error)
    if errors:
        return 1
    print("OK métadonnées SINJIRA : partage, SEO"
          + (" et octets des 3 pages/3 WebP Jekyll" if args.built else " source")
          + " conformes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
