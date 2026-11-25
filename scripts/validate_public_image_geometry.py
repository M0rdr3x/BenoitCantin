#!/usr/bin/env python3
"""Vérifier les dimensions intrinsèques et les descripteurs WebP des pages publiques."""
from html.parser import HTMLParser
from pathlib import Path
import struct
import hashlib
import json
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "projets/sinjira/index.html": 1,
    "projets/sinjira/romans/index.html": 3,
    "projets/sinjira/jeux/index.html": 3,
    "projets/sinjira/communaute/index.html": 1,
}


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.images.append(dict(attrs))


def dimensions(path):
    data = path.read_bytes()
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError(f"WebP invalide : {path.name}")
    kind = data[12:16]
    if kind == b"VP8X":
        return tuple(1 + int.from_bytes(data[i:i+3], "little") for i in (24, 27))
    if kind == b"VP8 " and data[23:26] == bytes((157, 1, 42)):
        return tuple(v & 0x3fff for v in struct.unpack_from("<HH", data, 26))
    if kind == b"VP8L" and data[20] == 0x2f:
        bits = int.from_bytes(data[21:25], "little")
        return (1 + (bits & 0x3fff), 1 + ((bits >> 14) & 0x3fff))
    raise ValueError(f"En-tête WebP non reconnu : {path.name}")


def resolve(page, src):
    parsed = urlsplit(src)
    if parsed.scheme or parsed.netloc:
        raise ValueError("Image externe interdite dans ce contrat")
    path = (ROOT / parsed.path.lstrip("/") if parsed.path.startswith("/")
            else page.parent / parsed.path).resolve()
    if not path.is_relative_to(ROOT / "assets/media"):
        raise ValueError("Image hors répertoire public")
    return path


def validate_posters():
    manifest = json.loads((ROOT / "scripts/category_posters_manifest.json").read_text("utf-8"))
    expected = {f"sinjira-{name}-poster-{width}.webp"
                for name in ("litterature", "jeux") for width in (480, 840)}
    if set(manifest) != expected:
        raise ValueError("Manifeste des quatre affiches incomplet")
    for name, info in manifest.items():
        path = ROOT / "assets/media" / name
        data = path.read_bytes()
        if (len(data) != info["bytes"] or len(data) >= 250_000
                or hashlib.sha256(data).hexdigest() != info["sha256"]
                or dimensions(path) != (info["width"], info["height"])):
            raise ValueError(f"Affiche invalide : {name}")
    print("OK intégrité des quatre affiches adaptatives.")


def main():
    validate_posters()
    manifest = json.loads((ROOT / "scripts/public_image_variants_manifest.json").read_text("utf-8"))
    expected_variants = {f"sinjira-brand-{w}.webp" for w in (64,128,192)}
    expected_variants |= {f"sinjira-{n}-public-{w}.webp" for n in ("communaute","demo-promo","resistance") for w in (480,720)}
    if set(manifest) != expected_variants:
        raise ValueError("Manifeste des neuf variantes incomplet")
    for name, info in manifest.items():
        path = ROOT / "assets/media" / name
        data = path.read_bytes()
        if (len(data) != info["bytes"] or len(data) >= info["original"]
                or hashlib.sha256(data).hexdigest() != info["sha256"]
                or dimensions(path) != (info["width"], info["height"])):
            raise ValueError(f"Variante invalide : {name}")
    for relative in (*PAGES, "projets/sinjira/registre/index.html", "projets/sinjira/codex/index.html"):
        page = ROOT / relative
        parser = Images()
        parser.feed(page.read_text("utf-8"))
        logos = [a for a in parser.images if a.get("src") in (
            "/assets/icons/sinjira-favicon.png", "/assets/icons/sinjira-officiel-20261120.png")]
        if len(logos) < 2:
            raise ValueError(f"{relative}: logos absents")
        for a in logos:
            if a.get("width") in ("47", "58", "80"):
                expected_set = ", ".join(f"/assets/media/sinjira-brand-{w}.webp {w}w" for w in (64,128,192))
                if a.get("srcset") != expected_set or a.get("sizes") != a["width"] + "px":
                    raise ValueError(f"{relative}: logo adaptatif absent")
    print("OK intégrité et usage des neuf variantes publiques.")
    count = 0
    for relative, expected in PAGES.items():
        page = ROOT / relative
        parser = Images()
        parser.feed(page.read_text("utf-8"))
        images = [a for a in parser.images if a.get("src", "").endswith(".webp")]
        if len(images) != expected:
            raise ValueError(f"{relative}: {len(images)} illustrations au lieu de {expected}")
        if sum(a.get("fetchpriority") == "high" for a in images) != 1:
            raise ValueError(f"{relative}: une seule illustration prioritaire attendue")
        for a in images:
            path = resolve(page, a["src"])
            if dimensions(path) != (int(a["width"]), int(a["height"])):
                raise ValueError(f"{relative}: dimensions erronées de {path.name}")
            if relative in ("projets/sinjira/romans/index.html", "projets/sinjira/jeux/index.html") and a.get("fetchpriority") == "high":
                name = "litterature" if "/romans/" in relative else "jeux"
                expected_set = (f"../../../assets/media/sinjira-{name}-poster-480.webp 480w, "
                                f"../../../assets/media/sinjira-{name}-poster-840.webp 840w")
                if a.get("srcset") != expected_set or path.name != f"sinjira-{name}-poster-840.webp" or not a.get("sizes"):
                    raise ValueError(f"{relative}: affiche adaptative absente")
            if a.get("decoding") != "async":
                raise ValueError(f"{relative}: décodage non asynchrone")
            for item in a.get("srcset", "").split(","):
                if not item.strip():
                    continue
                src, descriptor = item.split()
                if descriptor != f"{dimensions(resolve(page, src))[0]}w":
                    raise ValueError(f"{relative}: largeur srcset erronée : {src}")
            count += 1
    print(f"OK dimensions, priorité et srcset : {count} illustrations sur {len(PAGES)} pages.")


if __name__ == "__main__":
    main()
