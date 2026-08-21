#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'www.benoitcantin.com'
BASE_URL = f'https://{DOMAIN}'
MANIFESTS = [ROOT / 'manifest.webmanifest', ROOT / 'site.webmanifest']
REQUIRED_PUBLIC_ROUTES = {
    f'{BASE_URL}/projets/sinjira/communaute/',
    f'{BASE_URL}/projets/sinjira/monde-parallele/',
}
REQUIRED_OFFLINE_ROUTES = {
    '/projets/sinjira/communaute/',
    '/projets/sinjira/monde-parallele/',
}
REQUIRED_SHORTCUTS = {
    '/app/',
    '/projets/sinjira/romans/',
    '/projets/sinjira/registre/',
    '/projets/sinjira/monde-parallele/',
}
CACHE_PREFIX = 'benoitcantin-v24-4-94-'


def local_target(raw: str, base: Path | None = None) -> Path | None:
    raw = str(raw or '').strip()
    if not raw or raw.startswith(('#', '//', 'data:', 'blob:', 'mailto:', 'tel:', 'javascript:')):
        return None
    parsed = urlparse(raw)
    if parsed.scheme in {'http', 'https'}:
        if parsed.netloc != DOMAIN:
            return None
        path = unquote(parsed.path)
    else:
        path = unquote(parsed.path)
    if not path:
        return None
    target = ROOT / path.lstrip('/') if path.startswith('/') else ((base or ROOT) / path)
    if path.endswith('/'):
        target = target / 'index.html'
    if not target.exists() and target.suffix == '' and (target / 'index.html').exists():
        target = target / 'index.html'
    return target.resolve()


def load_manifest(path: Path, errors: list[str]) -> dict:
    if not path.exists():
        errors.append(f'Manifeste PWA absent: {path.name}')
        return {}
    try:
        data = json.loads(path.read_text('utf-8'))
    except Exception as exc:
        errors.append(f'Manifeste PWA invalide {path.name}: {exc}')
        return {}
    if not isinstance(data, dict):
        errors.append(f'Manifeste PWA invalide {path.name}: racine JSON non objet.')
        return {}
    return data


def validate_manifests(errors: list[str]) -> None:
    loaded = [(path, load_manifest(path, errors)) for path in MANIFESTS]
    for path, data in loaded:
        if not data:
            continue
        name = str(data.get('name') or '')
        short = str(data.get('short_name') or '')
        app_id = str(data.get('id') or '')
        start = str(data.get('start_url') or '')
        scope = str(data.get('scope') or '')
        display = str(data.get('display') or '')
        if 'SINJIRA' not in name.upper() or 'SINJIRA' not in short.upper():
            errors.append(f'{path.name}: branding PWA autre que SINJIRA™.')
        if app_id != '/projets/sinjira/':
            errors.append(f'{path.name}: id PWA inattendu: {app_id or "—"}')
        if start != '/app/':
            errors.append(f'{path.name}: start_url doit ouvrir l’app sociale /app/: {start or "—"}')
        if display not in {'standalone', 'fullscreen', 'minimal-ui'}:
            errors.append(f'{path.name}: display PWA invalide ou absent: {display or "—"}')
        start_target = local_target(start, path.parent)
        if start_target is None or not start_target.exists():
            errors.append(f'{path.name}: start_url introuvable: {start or "—"}')
        if not scope.startswith('/'):
            errors.append(f'{path.name}: scope doit être absolu au site: {scope or "—"}')
        icons = data.get('icons')
        if not isinstance(icons, list) or not icons:
            errors.append(f'{path.name}: aucune icône PWA.')
        else:
            for icon in icons:
                if not isinstance(icon, dict):
                    errors.append(f'{path.name}: entrée d’icône invalide.')
                    continue
                src = str(icon.get('src') or '')
                target = local_target(src, path.parent)
                if target is None or not target.exists():
                    errors.append(f'{path.name}: icône introuvable: {src or "—"}')
                sizes = str(icon.get('sizes') or '')
                if not sizes:
                    errors.append(f'{path.name}: taille d’icône absente pour {src or "—"}.')

        shortcuts = data.get('shortcuts')
        if not isinstance(shortcuts, list) or not shortcuts:
            errors.append(f'{path.name}: raccourcis PWA absents.')
        else:
            urls = {str(item.get('url') or '') for item in shortcuts if isinstance(item, dict)}
            missing = sorted(REQUIRED_SHORTCUTS - urls)
            if missing:
                errors.append(f'{path.name}: raccourcis SINJIRA™ manquants: ' + ', '.join(missing))
            for url in urls:
                target = local_target(url, path.parent)
                if target is None or not target.exists():
                    errors.append(f'{path.name}: raccourci introuvable: {url or "—"}')
                if url.lower().startswith(('/compte/', '/admin/', '/supabase/')):
                    errors.append(f'{path.name}: raccourci PWA privé interdit: {url}')

    if all(data for _, data in loaded):
        canonical = loaded[0][1]
        legacy = loaded[1][1]
        fields = ['id', 'name', 'short_name', 'description', 'start_url', 'scope', 'display', 'orientation', 'background_color', 'theme_color', 'lang', 'categories', 'icons', 'shortcuts']
        drift = [field for field in fields if canonical.get(field) != legacy.get(field)]
        if drift:
            errors.append('Les deux manifestes PWA divergent: ' + ', '.join(drift))


def validate_sitemap(errors: list[str]) -> None:
    path = ROOT / 'sitemap.xml'
    if not path.exists():
        errors.append('sitemap.xml absent.')
        return
    try:
        tree = ET.parse(path)
    except Exception as exc:
        errors.append(f'sitemap.xml invalide: {exc}')
        return
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    locs = [str(node.text or '').strip() for node in tree.findall('.//sm:loc', ns)]
    if not locs:
        errors.append('sitemap.xml ne contient aucune URL.')
        return
    duplicates = sorted({url for url in locs if locs.count(url) > 1})
    if duplicates:
        errors.append('sitemap.xml contient des URL dupliquées: ' + ', '.join(duplicates))
    missing_required = sorted(REQUIRED_PUBLIC_ROUTES - set(locs))
    if missing_required:
        errors.append('sitemap.xml omet des espaces publics SINJIRA™: ' + ', '.join(missing_required))
    for url in locs:
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.netloc != DOMAIN:
            errors.append(f'URL sitemap hors domaine HTTPS canonique: {url}')
            continue
        if parsed.query or parsed.fragment:
            errors.append(f'URL sitemap avec query/fragment: {url}')
        lower_path = parsed.path.lower()
        if lower_path.startswith(('/app/', '/compte/', '/admin/', '/supabase/')):
            errors.append(f'URL privée présente dans le sitemap: {url}')
        target = local_target(url)
        if target is None or not target.exists():
            errors.append(f'URL sitemap sans fichier local: {url}')


def validate_robots(errors: list[str]) -> None:
    path = ROOT / 'robots.txt'
    if not path.exists():
        errors.append('robots.txt absent.')
        return
    text = path.read_text('utf-8', errors='ignore')
    expected_sitemap = f'Sitemap: {BASE_URL}/sitemap.xml'
    if expected_sitemap not in text:
        errors.append('robots.txt ne référence pas le sitemap canonique.')
    for protected in ['/app/', '/compte/', '/admin/', '/supabase/']:
        if not re.search(rf'^Disallow:\s*{re.escape(protected)}\s*$', text, re.M | re.I):
            errors.append(f'robots.txt ne bloque pas {protected}')


def validate_cname(errors: list[str]) -> None:
    path = ROOT / 'CNAME'
    if not path.exists():
        errors.append('CNAME absent.')
        return
    value = path.read_text('utf-8').strip().lower()
    if value != DOMAIN:
        errors.append(f'CNAME inattendu: {value or "—"}; attendu: {DOMAIN}')


def validate_service_worker(errors: list[str]) -> None:
    path = ROOT / 'sw.js'
    if not path.exists():
        errors.append('Service Worker sw.js absent.')
        return
    text = path.read_text('utf-8', errors='ignore')
    match = re.search(r'\bconst\s+CORE\s*=\s*\[(.*?)\];', text, re.S)
    if not match:
        errors.append('sw.js: liste CORE introuvable.')
        return
    refs = re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))
    if not refs:
        errors.append('sw.js: liste CORE vide.')
    missing_offline = sorted(REQUIRED_OFFLINE_ROUTES - set(refs))
    if missing_offline:
        errors.append('sw.js CORE omet des espaces SINJIRA™ majeurs: ' + ', '.join(missing_offline))
    for required in ['/manifest.webmanifest', '/assets/js/sinjira-pwa-install.js', '/assets/css/sinjira-mobile-app-v24-4-94.css', '/assets/js/sinjira-mobile-social-v24-4-94.js', '/android-chrome-192x192.png', '/android-chrome-512x512.png']:
        if required not in refs:
            errors.append(f'sw.js CORE omet la ressource mobile: {required}')
    for raw in refs:
        target = local_target(raw, ROOT)
        if target is None or not target.exists():
            errors.append(f'sw.js CORE référence un fichier absent: {raw}')
    cache_match = re.search(r"\bconst\s+CACHE\s*=\s*['\"]([^'\"]+)['\"]", text)
    if not cache_match:
        errors.append('sw.js: nom de cache explicite absent.')
    elif not cache_match.group(1).startswith(CACHE_PREFIX):
        errors.append(f'sw.js: cache obsolète {cache_match.group(1)!r}; préfixe attendu {CACHE_PREFIX!r}.')
    if "u.pathname.startsWith('/app/')" not in text:
        errors.append('sw.js: l’app sociale n’est plus explicitement network-only/no-store.')
    if "u.pathname.startsWith('/compte/')" not in text:
        errors.append('sw.js: les pages Compte ne sont plus explicitement network-only/no-store.')


def validate_install_runtime(errors: list[str]) -> None:
    installer = ROOT / 'assets/js/sinjira-pwa-install.js'
    site = ROOT / 'assets/js/site.js'
    session = ROOT / 'assets/js/v19-session.js'
    app = ROOT / 'app/index.html'
    if not installer.exists():
        errors.append('Runtime d’installation PWA absent.')
        return
    text = installer.read_text('utf-8', errors='ignore')
    site_text = site.read_text('utf-8', errors='ignore') if site.exists() else ''
    session_text = session.read_text('utf-8', errors='ignore') if session.exists() else ''
    app_text = app.read_text('utf-8', errors='ignore') if app.exists() else ''
    for marker, message in [
        ('beforeinstallprompt', 'Invite Android/Chromium beforeinstallprompt absente.'),
        ('appinstalled', 'Événement appinstalled absent.'),
        ("navigator.serviceWorker.register('/sw.js'", 'Enregistrement global du Service Worker absent.'),
        ('apple-touch-icon', 'Icône d’écran d’accueil iOS absente.'),
        ('Sur iPhone/iPad', 'Aide d’installation iPhone/iPad absente.'),
        ('display-mode: standalone', 'Détection du mode installé absente.'),
    ]:
        if marker not in text:
            errors.append(message)
    if '/assets/js/sinjira-pwa-install.js?v=24.4.93' not in site_text:
        errors.append('site.js ne charge pas le runtime PWA V24.4.93.')
    if 'serviceWorker.register' in session_text:
        errors.append('v19-session.js enregistre encore un deuxième Service Worker.')
    if "p?.display_name||p?.pseudo||'Mon compte'" not in session_text:
        errors.append('Le menu session ne priorise pas le nom affiché sur le pseudo historique.')
    for marker in ['mobile-app-topbar','mobile-app-bottom-nav','data-real-post-form','data-real-feed','sinjira-mobile-social-v24-4-94.js']:
        if marker not in app_text:
            errors.append(f'App sociale V24.4.94 incomplète: {marker}')
    if 'name="robots" content="noindex,nofollow"' not in app_text:
        errors.append('App sociale privée sans noindex,nofollow.')


def validate_offline(errors: list[str]) -> None:
    path = ROOT / 'offline.html'
    if not path.exists():
        errors.append('offline.html absent.')
        return
    text = path.read_text('utf-8', errors='ignore')
    if 'hors ligne' not in text.lower():
        errors.append('offline.html ne décrit pas clairement l’état hors ligne.')
    for raw in re.findall(r'(?:href|src)=["\']([^"\']+)["\']', text, re.I):
        target = local_target(raw, path.parent)
        if target is not None and not target.exists():
            errors.append(f'offline.html référence un fichier absent: {raw}')


def main() -> int:
    errors: list[str] = []
    validate_manifests(errors)
    validate_sitemap(errors)
    validate_robots(errors)
    validate_cname(errors)
    validate_service_worker(errors)
    validate_install_runtime(errors)
    validate_offline(errors)

    if errors:
        print(f'ECHEC PWA/SEO: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK PWA/SEO V24.4.94: lancement dans l’app sociale, installation Android/iOS, navigation mobile, cache privé/public et identité de profil cohérents.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
