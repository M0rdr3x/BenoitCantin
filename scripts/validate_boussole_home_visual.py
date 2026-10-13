#!/usr/bin/env python3
"""Contrat anti-image-cassée pour la Boussole électorale de l'accueil.

Lecture seule et sans dépendance : vérifie le WebP spécifique à l'accueil, sa
signature VP8/RIFF, dimensions, octets et les références HTML cache-bustées.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ("assets/media/nova-boussole-electorale.webp",)
URL = "/assets/media/nova-boussole-electorale.webp?v=20261013-fix"
SHA = "f4f2f5bafe5413d2fde82892e147e5f200d5658934a88d6ded8a182b24ef8121"


def check_bytes(data: bytes) -> list[str]:
    if not 1000 < len(data) < 30000:
        return ["Taille WebP inattendue"]
    issues: list[str] = []
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP" or data[12:16] != b"VP8 ":
        return ["Signature RIFF/WEBP/VP8 incorrecte"]
    if struct.unpack_from("<I", data, 4)[0] + 8 != len(data):
        issues.append("Taille RIFF incorrecte")
    block = struct.unpack_from("<I", data, 16)[0]
    if block + 20 + (block & 1) != len(data):
        issues.append("Bloc VP8 tronqué")
    if data[23:26] != b"\x9d\x01\x2a":
        issues.append("Image-clé VP8 absente")
    width = struct.unpack_from("<H", data, 26)[0] & 0x3fff
    height = struct.unpack_from("<H", data, 28)[0] & 0x3fff
    if (width, height) != (160, 160):
        issues.append("Dimensions WebP incorrectes")
    if hashlib.sha256(data).hexdigest() != SHA:
        issues.append("Empreinte SHA-256 du visuel non conforme")
    return issues


def audit(root: Path, built: Path | None = None) -> list[str]:
    issues: list[str] = []
    for rel in IMAGES:
        source = root / rel
        if not source.is_file() or source.is_symlink():
            issues.append("Image source Boussole absente: " + rel)
            continue
        data = source.read_bytes()
        issues.extend(rel + ": " + issue for issue in check_bytes(data))
        if built is not None:
            published = built / rel
            if (not published.is_file() or published.is_symlink()
                    or published.read_bytes() != data):
                issues.append("Image WebP absente ou modifiée par Jekyll: " + rel)
    page = root / "index.html"
    if not page.is_file():
        return issues + ["Accueil source absent"]
    html = page.read_text("utf-8")
    if html.count(URL) != 3:
        issues.append("Trois références accueil/aperçu Boussole non synchronisées")
    if not re.search(
        r'<a\b[^>]*class="[^"]*node-boussole-home[^"]*"[^>]*'
        r'data-core-src="' + re.escape(URL) + r'"', html,
    ):
        issues.append("Aperçu central Boussole non corrigé")
    if not re.search(
        r'<img src="' + re.escape(URL)
        + r'" alt="" width="132" height="132" loading="eager"', html,
    ):
        issues.append("Image Boussole non prioritaire dans l'orbite")
    if built is not None:
        dest = built / "index.html"
        if not dest.is_file() or dest.read_bytes() != page.read_bytes():
            issues.append("Accueil transformé ou absent du build Jekyll")
    return issues


def self_test() -> None:
    good = (ROOT / IMAGES[0]).read_bytes()
    assert not check_bytes(good), check_bytes(good)
    for bad in (
        good[:-2],
        b"FAIL" + good[4:],
        good[:26] + b"\x80\x00" + good[28:],
        good[:80] + bytes([good[80] ^ 1]) + good[81:],
    ):
        assert check_bytes(bad), "WebP incorrect accepté"
    assert not audit(ROOT), audit(ROOT)
    with tempfile.TemporaryDirectory() as name:
        built = Path(name)
        for rel in (*IMAGES, "index.html"):
            target = built / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / rel).read_bytes())
        assert not audit(ROOT, built), audit(ROOT, built)
        (built / IMAGES[0]).unlink()
        assert audit(ROOT, built), "Image absente de l'artefact acceptée"
    print("OK Boussole: RIFF VP8, dimensions, SHA-256, accueil, cache et Jekyll")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--built", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    issues = audit(ROOT, args.built)
    for issue in issues:
        print("ERREUR : " + issue)
    if issues:
        return 1
    print("OK : visuel Boussole intègre et présent dans le parcours d'accueil")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
