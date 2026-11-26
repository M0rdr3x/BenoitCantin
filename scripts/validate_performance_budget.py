#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlparse
import re
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TEXT_LIMITS = {".js": 550_000, ".css": 550_000, ".html": 650_000}
IMAGE_LIMIT = 1_500_000
HOME_CARD_IMAGE_TOTAL_LIMIT = 200_000
HOME_THUMBNAIL_LIMIT = 100_000
EXCLUDED_DIRS = {".git", "node_modules", ".venv", "dist", "build"}
CRITICAL_PAGES = [
    ROOT / "index.html",
    ROOT / "projets" / "sinjira" / "index.html",
    ROOT / "projets" / "sinjira" / "registre" / "index.html",
    ROOT / "projets" / "projet-nova" / "index.html",
]


def iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


def resolve_asset(page: Path, value: str) -> Path | None:
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or value.startswith("data:"):
        return None
    clean = parsed.path
    if clean.startswith("/"):
        return ROOT / clean.lstrip("/")
    return (page.parent / clean).resolve()


def validate_session_runtime(errors):
    # Simule uniquement la fenêtre et remplace l'import réseau par un espion.
    # Le reste du runtime est exécuté tel quel, sans connexion ni compte.
    harness = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('assets/js/home-session-lazy-v24-5-1.js', 'utf8');
const target = "import('./v19-session.js?v=24.5.1')";
assert.equal(source.split(target).length, 2);
function run(readyState) {
  const events = new Map(), timers = new Map();
  let imports = 0;
  const window = {
    addEventListener: (name, cb) => events.set(name, cb),
    removeEventListener: (name, cb) => { if (events.get(name) === cb) events.delete(name); },
    setTimeout: (cb, ms) => { assert.equal(ms, 60000); timers.set(1, cb); return 1; },
    clearTimeout: id => timers.delete(id)
  };
  vm.runInNewContext(source.replace(target, 'loadModule()'), {
    window, document: {readyState}, loadModule: () => { imports++; return Promise.resolve(); }
  });
  return {events, timers, imports: () => imports};
}
for (const event of ['pointerdown','touchstart','keydown']) {
  const early = run('interactive');
  const callback = early.events.get(event);
  assert.equal(early.timers.size, 0);
  callback();
  callback();
  assert.equal(early.imports(), 1);
  assert.equal(early.events.size, 0);
  assert.equal(early.timers.size, 0);
}
const late = run('interactive');
late.events.get('load')();
assert.equal(late.timers.size, 1);
late.events.get('keydown')();
assert.equal(late.imports(), 1);
assert.equal(late.events.size, 0);
assert.equal(late.timers.size, 0);
const idle = run('complete');
idle.timers.get(1)();
assert.equal(idle.imports(), 1);
assert.equal(idle.events.size, 0);
assert.equal(idle.timers.size, 0);
"""
    try:
        result = subprocess.run(["node", "-e", harness], cwd=ROOT,
                                capture_output=True, text=True, timeout=15)
        if result.returncode:
            errors.append("Session accueil : " + result.stderr.strip())
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"Session accueil non testée : {exc}")


def main() -> int:
    errors = []

    # Les budgets texte s’appliquent à tout le runtime versionné.
    for path in iter_files():
        limit = TEXT_LIMITS.get(path.suffix.lower())
        if limit and path.stat().st_size > limit:
            errors.append(
                f"{path.relative_to(ROOT)}: {path.stat().st_size:,} octets dépasse le budget de {limit:,}."
            )

    # Pour les images, on contrôle les actifs réellement chargés par les pages
    # critiques plutôt que des archives/documentations qui ne pénalisent pas le web.
    image_refs = set()
    for page in CRITICAL_PAGES:
        if not page.exists():
            continue
        html = page.read_text("utf-8", errors="ignore")
        for value in re.findall(r"<img\b[^>]*\bsrc=[\"']([^\"']+)", html, flags=re.I):
            asset = resolve_asset(page, value)
            if asset and asset.suffix.lower() in {".webp", ".avif", ".png", ".jpg", ".jpeg"}:
                image_refs.add(asset)
    for asset in sorted(image_refs):
        if not asset.exists():
            errors.append(f"Actif image critique absent: {asset.relative_to(ROOT)}")
        elif asset.stat().st_size > IMAGE_LIMIT:
            errors.append(
                f"{asset.relative_to(ROOT)}: {asset.stat().st_size:,} octets dépasse le budget image critique de {IMAGE_LIMIT:,}."
            )

    home = (ROOT / "index.html").read_text("utf-8", errors="ignore")
    if 'data-disable-sinjira-assistant="true"' not in home:
        errors.append("index.html: l’assistant doit être explicitement désactivé sur l’accueil.")
    if '/assets/js/home-assistant-lazy-v24-5-2.js' in home or '/assets/js/sinjira-assistant.js' in home:
        errors.append("index.html: aucun runtime assistant ne doit être chargé sur l’accueil désactivé.")
    session_loader = ROOT / "assets" / "js" / "home-session-lazy-v24-5-1.js"
    if '/assets/js/home-session-lazy-v24-5-1.js?v=24.5.2' not in home:
        errors.append("index.html: loader session différé absent.")
    if not session_loader.exists():
        errors.append("Loader session accueil V24.5.1 absent.")
    else:
        session_text = session_loader.read_text("utf-8", errors="ignore")
        for marker in ("pointerdown", "touchstart", "keydown", "setTimeout(loadSession,60000)"):
            if marker not in session_text:
                errors.append(f"Loader session accueil insuffisamment différé: {marker}")

    validate_session_runtime(errors)

    script_count = len(re.findall(r"<script\b", home, flags=re.I))
    stylesheet_count = len(re.findall(r"<link\b[^>]*rel=[\"']stylesheet[\"']", home, flags=re.I))
    if script_count > 6:
        errors.append(f"index.html: {script_count} scripts; budget maximal 6.")
    if stylesheet_count > 7:
        errors.append(f"index.html: {stylesheet_count} feuilles de style; budget maximal 7.")

    manifest = json.loads((ROOT / "scripts/home_thumbnails_manifest.json").read_text("utf-8"))
    expected = {f"sinjira-{name}-home-{width}.webp"
                for name in ("registre", "jeux", "communaute") for width in (160, 336)}
    if set(manifest) != expected:
        errors.append("Manifeste des six miniatures incomplet.")
    for name in sorted(expected):
        asset = ROOT / "assets/media" / name
        if not asset.is_file():
            errors.append(f"Miniature manquante : {name}")
            continue
        data = asset.read_bytes()
        info = manifest.get(name, {})
        if (len(data) != info.get("bytes") or len(data) >= HOME_THUMBNAIL_LIMIT
                or hashlib.sha256(data).hexdigest() != info.get("sha256")
                or data[:4] != b"RIFF" or data[8:12] != b"WEBP"):
            errors.append(f"Miniature invalide ou modifiée : {name}")

    cards = re.findall(r'<a class="home-project".*?</a>', home, flags=re.I | re.S)
    if len(cards) != 4:
        errors.append(f"index.html: 4 cartes principales attendues, trouvé {len(cards)}.")
    else:
        card_image_bytes = 0
        for idx, card in enumerate(cards, start=1):
            image = re.search(r"<img\b[^>]*>", card, flags=re.I)
            if not image:
                errors.append(f"index.html: carte {idx} sans image.")
                continue
            tag = image.group(0)
            if 'loading="lazy"' not in tag:
                errors.append(f"index.html: image de la carte {idx} sans loading=lazy.")
            if 'decoding="async"' not in tag:
                errors.append(f"index.html: image de la carte {idx} sans decoding=async.")
            if 'fetchpriority="low"' not in tag:
                errors.append(f"index.html: image secondaire {idx} sans priorité basse.")
            if not re.search(r'\bwidth="[1-9]\d*"', tag) or not re.search(r'\bheight="[1-9]\d*"', tag):
                errors.append(f"index.html: dimensions de la carte {idx} manquantes.")
            src = re.search(r'\bsrc="([^"]+)"', tag)
            asset = resolve_asset(ROOT / "index.html", src.group(1)) if src else None
            if asset is None or not asset.is_file():
                errors.append(f"index.html: image locale de la carte {idx} absente.")
            else:
                candidates = [asset]
                srcset = re.search(r'\bsrcset="([^"]+)"', tag)
                if idx > 1:
                    name = ("registre", "jeux", "communaute")[idx - 2]
                    expected_set = (f"/assets/media/sinjira-{name}-home-160.webp 160w, "
                                    f"/assets/media/sinjira-{name}-home-336.webp 336w")
                    if not srcset or srcset.group(1) != expected_set or not re.search(r'\bsizes="[^"]+"', tag):
                        errors.append(f"index.html: variantes adaptatives de la carte {idx} absentes.")
                    if srcset:
                        for item in srcset.group(1).split(","):
                            candidate = resolve_asset(ROOT / "index.html", item.strip().split()[0])
                            if candidate is None or not candidate.is_file():
                                errors.append(f"index.html: variante de la carte {idx} manquante.")
                            else:
                                candidates.append(candidate)
                card_image_bytes += max(candidate.stat().st_size for candidate in candidates)
        print(f"Images des quatre cartes accueil : {card_image_bytes:,} octets.")
        if card_image_bytes > HOME_CARD_IMAGE_TOTAL_LIMIT:
            errors.append(f"index.html: poids cumulé des cartes {card_image_bytes:,} > {HOME_CARD_IMAGE_TOTAL_LIMIT:,} octets.")

    if errors:
        print(f"ECHEC budgets performance: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1
    print(f"OK performance: {len(image_refs)} image(s) critiques, budgets texte et chargement différé de l’accueil sont sous contrôle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
