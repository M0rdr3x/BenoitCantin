#!/usr/bin/env python3
"""Générer uniquement les affiches publiques de catégories, sans modifier les originaux.

Utilise Chromium/Playwright déjà employé par la CI, sans service externe.
Les fichiers sont écrits dans un dossier de sortie explicitement choisi.
"""
import argparse
import base64
import hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("sinjira-litterature", "sinjira-jeux")
WIDTHS = (480, 840)
QUALITY = 0.82
MAX_BYTES = 250_000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--emit-base64", action="store_true",
                        help="Transmettre uniquement les miniatures publiques via le journal CI.")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            for name in SOURCES:
                original = ROOT / "assets/media" / (name + ".webp")
                source = original.read_bytes()
                uri = "data:image/webp;base64," + base64.b64encode(source).decode("ascii")
                for width in WIDTHS:
                    result = page.evaluate("""async ({uri,width,quality}) => {
                      const img = new Image();
                      img.src = uri;
                      await img.decode();
                      if (img.naturalWidth < width) throw new Error("Source trop petite");
                      const canvas = document.createElement("canvas");
                      canvas.width = width;
                      canvas.height = Math.round(img.naturalHeight * width / img.naturalWidth);
                      const ctx = canvas.getContext("2d");
                      ctx.imageSmoothingEnabled = true;
                      ctx.imageSmoothingQuality = "high";
                      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                      return {uri:canvas.toDataURL("image/webp",quality),
                              width:canvas.width,height:canvas.height};
                    }""", {"uri": uri, "width": width, "quality": QUALITY})
                    if not result["uri"].startswith("data:image/webp;base64,"):
                        raise SystemExit("Encodeur WebP indisponible")
                    data = base64.b64decode(result["uri"].split(",", 1)[1], validate=True)
                    if not (data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
                        raise SystemExit("Format WebP invalide")
                    if len(data) >= min(MAX_BYTES, len(source)):
                        raise SystemExit(f"Miniature trop lourde : {name} {width} px ({len(data)} octets)")
                    target = f"{name}-poster-{width}.webp"
                    (args.output / target).write_bytes(data)
                    digest = hashlib.sha256(data).hexdigest()
                    print(f"POSTER_IMAGE {target} {result['width']}x{result['height']} {len(source)} -> {len(data)} bytes sha256={digest}")
                    if args.emit_base64:
                        payload = base64.b64encode(data).decode("ascii")
                        chunks = [payload[i:i+3000] for i in range(0, len(payload), 3000)]
                        for i, chunk in enumerate(chunks):
                            print(f"POSTER_WEBP|{target}|{i+1}/{len(chunks)}|{chunk}")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
