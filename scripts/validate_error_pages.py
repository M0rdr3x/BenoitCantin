#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]

GLOBAL_NAV = (
    "/",
    "/projets/sinjira/",
    "/projets/sinjira/romans/",
    "/projets/sinjira/registre/",
    "/projets/sinjira/communaute/",
    "/compte/",
)

ERROR_PAGES = {
    "404.html": {
        "title": "Page introuvable",
        "markers": (
            "Erreur 404",
            "Retour à l’accueil",
            "Ouvrir SINJIRA™",
            "Nous contacter",
        ),
    },
    "offline.html": {
        "title": "Hors ligne",
        "markers": (
            "Vous êtes hors ligne.",
            "Réessayer la connexion",
            "Aucune donnée privée",
        ),
    },
}


def local_target(raw: str, base: Path) -> Path | None:
    raw = str(raw or "").strip()
    if not raw or raw.startswith(("#", "//", "data:", "blob:", "mailto:", "tel:", "javascript:")):
        return None
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc not in {"www.benoitcantin.com", "benoitcantin.com"}:
            return None
        path = unquote(parsed.path)
    else:
        path = unquote(parsed.path)
    if not path:
        return None
    target = ROOT / path.lstrip("/") if path.startswith("/") else base / path
    if path.endswith("/"):
        target = target / "index.html"
    if not target.exists() and target.suffix == "" and (target / "index.html").exists():
        target = target / "index.html"
    return target.resolve()


def robots_value(html: str) -> str:
    for tag in re.findall(r"<meta\b[^>]*>", html, re.I):
        if re.search(r"\bname=[\"']robots[\"']", tag, re.I):
            match = re.search(r"\bcontent=[\"']([^\"']+)[\"']", tag, re.I)
            if match:
                return match.group(1).lower()
    return ""


def validate_page(rel: str, cfg: dict[str, object], errors: list[str]) -> None:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"{rel}: fichier absent.")
        return

    html = path.read_text("utf-8", errors="strict")
    robots = robots_value(html)
    for marker in ("noindex", "nofollow", "noarchive"):
        if marker not in robots:
            errors.append(f"{rel}: robots privé/erreur incomplet, {marker} absent.")

    if str(cfg["title"]).lower() not in html.lower():
        errors.append(f"{rel}: titre attendu absent: {cfg['title']}")

    if 'class="skip-link"' not in html or 'href="#contenu"' not in html:
        errors.append(f"{rel}: lien d’évitement vers #contenu absent.")
    if '<main id="contenu" tabindex="-1">' not in html:
        errors.append(f"{rel}: cible de lien d’évitement non focalisable.")

    header = re.search(r"<header\b[\s\S]*?</header>", html, re.I)
    if not header:
        errors.append(f"{rel}: en-tête global absent.")
    else:
        shell = header.group(0)
        for marker in (
            "data-menu-toggle",
            'aria-controls="navigation-principale"',
            'id="navigation-principale"',
            "data-main-nav",
        ):
            if marker not in shell:
                errors.append(f"{rel}: contrat menu mobile absent: {marker}")
        for href in GLOBAL_NAV:
            if f'href="{href}"' not in shell and f"href='{href}'" not in shell:
                errors.append(f"{rel}: destination globale absente: {href}")

    if "/assets/js/site.js" not in html:
        errors.append(f"{rel}: runtime global site.js absent.")

    for marker in cfg["markers"]:
        if str(marker).lower() not in html.lower():
            errors.append(f"{rel}: contenu de secours absent: {marker}")

    for raw in re.findall(r'(?:href|src)=[\"\']([^\"\']+)[\"\']', html, re.I):
        target = local_target(raw, path.parent)
        if target is not None and not target.exists():
            errors.append(f"{rel}: ressource/lien local absent: {raw}")

    # Une page d'erreur doit aussi offrir un contact public sans promotion
    # d'un programme archivé; ce lien reste indépendant du menu principal.
    if rel == "404.html" and 'href="/contact.html"' not in html:
        errors.append("404: lien de contact absent.")

    runtime = (ROOT / "assets/js/error-pages-ux-v1.js").read_text("utf-8")
    if "/assets/js/error-pages-ux-v1.js" not in html or "/assets/css/error-pages-ux-v1.css" not in html:
        errors.append(f"{rel}: ressources externes de secours absentes.")
    if re.search(r'\b(?:onclick|onload|onerror|style)\s*=', html, re.I) or re.search(r'<script\b(?![^>]*\bsrc=)', html, re.I):
        errors.append(f"{rel}: script/style inline incompatible avec CSP stricte.")

    if rel == "404.html":
        for legacy, target in (
            ("'/sinjira'", "'/projets/sinjira/'"),
            ("'/admin'", "'/admin/sinjira/'"),
        ):
            if legacy not in runtime or target not in runtime:
                errors.append(f"{rel}: redirection de compatibilité perdue: {legacy} -> {target}")

    if rel == "offline.html":
        if 'role="status"' not in html or 'aria-live="polite"' not in html:
            errors.append(f"{rel}: annonce accessible de reprise réseau absente.")
        if "location.reload()" not in runtime or "data-error-retry hidden" not in html:
            errors.append(f"{rel}: action de nouvelle tentative absente.")
        if 'data-error-status' not in html or 'aria-atomic="true"' not in html:
            errors.append(f"{rel}: annonce réseau dynamique incomplète.")
        if "actualisez la page dans votre navigateur" not in html:
            errors.append(f"{rel}: solution de repli sans JavaScript absente.")


def validate_offline_runtime(errors: list[str]) -> None:
    # Exécute le vrai script dans un DOM minimal, sans réseau ni données privées.
    harness = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('assets/js/error-pages-ux-v1.js', 'utf8');
function run(path, online, missing = false) {
  const events = {}, clicks = {};
  let reloads = 0;
  const button = { hidden: true, addEventListener: (name, fn) => { clicks[name] = fn; } };
  const status = { textContent: '' };
  const navigator = { onLine: online };
  vm.runInNewContext(source, {
    document: { body: {dataset: {errorPage: 'offline'}},
      querySelector: selector => selector === '[data-error-retry]' ? button : (missing ? null : status) },
    window: {addEventListener: (name, fn) => { events[name] = fn; }},
    location: {pathname: path, reload: () => { reloads++; }},
    navigator
  });
  return {events, clicks, button, status, navigator, reloads: () => reloads};
}
const a = run('/compte/profil.html', false);
assert.equal(a.button.hidden, false);
assert.match(a.status.textContent, /semble déconnecté/);
a.navigator.onLine = true;
a.events.online();
assert.match(a.status.textContent, /connexion possible/);
assert.match(a.status.textContent, /encore être indisponible/);
assert.equal(a.reloads(), 0);
a.navigator.onLine = false;
a.events.offline();
assert.match(a.status.textContent, /semble déconnecté/);
a.clicks.click();
assert.equal(a.reloads(), 1);
const b = run('/offline.html', true);
assert.equal(b.button.hidden, true);
assert.equal(b.clicks.click, undefined);
assert.match(b.status.textContent, /Revenez à l’accueil/);
assert.equal(b.reloads(), 0);
const c = run('/compte/', true, true);
assert.equal(c.button.hidden, true);
assert.deepEqual(Object.keys(c.events), []);
"""
    try:
        result = subprocess.run(
            ["node", "-e", harness], cwd=ROOT, capture_output=True,
            text=True, timeout=15, check=False,
        )
        if result.returncode:
            errors.append("Runtime hors ligne: " + result.stderr.strip())
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"Runtime hors ligne non testé: {exc}")


def main() -> int:
    errors: list[str] = []
    for rel, cfg in ERROR_PAGES.items():
        validate_page(rel, cfg, errors)
    validate_offline_runtime(errors)

    if errors:
        print(f"ECHEC pages de résilience: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK pages de résilience: 404 et hors-ligne sont noindex, accessibles, "
        "mobiles et reliées au shell public sans dépendance privée."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
