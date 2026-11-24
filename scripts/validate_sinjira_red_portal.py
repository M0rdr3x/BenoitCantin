#!/usr/bin/env python3
"""Palette officielle SINJIRA sur l'accueil : rouge, noir, métal."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
CSS = ROOT / "assets/css/home-sinjira-only-v1.css"

def get_rule(css, selector):
    m = re.search(re.escape(selector) + r"\{([^{}]+)\}", css)
    return m.group(1) if m else ""

def is_red(rgba):
    m = re.search(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", rgba)
    if not m:
        return False
    red, green, blue = map(int, m.groups())
    return red >= 150 and red > 1.45 * green and red > 1.35 * blue

def check():
    html = HTML.read_text("utf-8")
    css = CSS.read_text("utf-8")
    err = []
    prefix = ".home-page.home-sinjira-only "
    for name in (".home-sinjira-cosmos::before", ".home-sinjira-cosmos::after", ".sinjira-orbit"):
        rule = get_rule(css, prefix + name)
        border = re.search(r"(?:^|;)border:1px solid (rgba?\([^)]+\))", rule)
        if not border or not is_red(border.group(1)):
            err.append("Contour non rouge : " + name)
        if "radial-gradient(" not in rule or "box-shadow:" not in rule:
            err.append("Éclairage et profondeur non conformes : " + name)
    for token in ("--sinjira-crimson:#db202c", "--sinjira-ember:#ff5b4e",
                  "--sinjira-metal:#ac8781"):
        if token not in css:
            err.append("Couleur de référence absente : " + token)
    for old in ("rgba(219,173,247", "rgba(172,140,239", "rgba(166,83,109",
                "rgba(134,80,178", "rgba(120,61,82", "#c4bbd8"):
        if old in css:
            err.append("Ancien halo mauve encore présent : " + old)
    if 'home-sinjira-only-v1.css?v=1.1.0' not in html:
        err.append("Cache CSS pas invalidé")
    if 'src="/assets/icons/sinjira-officiel-20261120.png"' not in html or "sinjira.svg" in html:
        err.append("Image officielle absente ou ancienne cible encore présente")
    glows = re.findall(r'--card-glow:(rgba?\([^)]+\))', html)
    if len(glows) != 4 or not all(is_red(glow) for glow in glows):
        err.append("Les quatre rubriques ne partagent pas la palette rouge/noire")
    if ":focus-visible" not in css or "prefers-reduced-motion:reduce" not in css:
        err.append("Protection d'accessibilité supprimée")
    if "@media(max-width:700px)" not in css or "@media(max-width:420px)" not in css:
        err.append("Adaptation cellulaire absente")
    if "Projet Nova" in html or 'href="/projets/projet-nova/"' in html:
        err.append("Projet Nova est revenu dans l'accueil")
    return err

if __name__ == "__main__":
    errors = check()
    if errors:
        print("ECHEC : " + "; ".join(errors))
        sys.exit(1)
    print("OK : trois cercles rouges/noirs, emblème, quatre rubriques, cache et accessibilité")
