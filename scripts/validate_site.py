#!/usr/bin/env python3
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTS = {'.html', '.js', '.css', '.json', '.md', '.txt', '.xml', '.webmanifest', '.sql', '.ts', '.tsx'}
SECRET_PATTERNS = [
    re.compile(r'SUPABASE_SERVICE_ROLE_KEY\s*[:=]\s*[\'\"]?[A-Za-z0-9._-]{20,}', re.I),
    re.compile(r'OPENAI_API_KEY\s*[:=]\s*[\'\"]?sk-[A-Za-z0-9_-]{16,}', re.I),
    re.compile(r'sk-proj-[A-Za-z0-9_-]{16,}'),
    re.compile(r'\bsb_secret_[A-Za-z0-9._-]{20,}\b'),
]
SKIP_SCHEMES = {'http', 'https', 'mailto', 'tel', 'javascript', 'data', 'blob'}
ACTIVE_SINJIRA_PREFIXES = ('projets/sinjira/', 'compte/', 'admin/')
# L'application React Native possède sa propre validation TypeScript/Expo.
# Le validateur du site statique ne doit donc pas interpréter ses imports npm
# ou sa résolution .ts/.tsx comme des dépendances de fichiers du site Web.
NATIVE_MOBILE_PREFIX = 'mobile-native/'
# Ces deux fichiers gardent volontairement la casse legacy /Admin/ uniquement pour
# protéger/réécrire d'anciens favoris et caches. Ils ne constituent pas des liens actifs.
LEGACY_ADMIN_COMPAT_FILES = {'sw.js', 'assets/js/v24-3-3-runtime.js'}


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str]] = []
        self.ids: list[str] = []
        self.fragment_refs: list[str] = []
        self.missing_alt: list[str] = []
        self.unsafe_blank: list[str] = []
        self.refreshes: list[str] = []
        self._buttons: list[dict[str, object]] = []
        self.unnamed_buttons = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = dict(attrs)
        if d.get('id'):
            self.ids.append(str(d['id']))

        attr = {
            'a': 'href',
            'img': 'src',
            'script': 'src',
            'link': 'href',
            'source': 'src',
            'video': 'src',
            'audio': 'src',
            'iframe': 'src',
            'form': 'action',
        }.get(tag)
        if attr and d.get(attr):
            raw = str(d[attr])
            self.refs.append((tag, raw))
            parsed = urlparse(raw)
            if tag == 'a' and parsed.fragment and not parsed.path and not parsed.scheme:
                self.fragment_refs.append(unquote(parsed.fragment))

        if tag == 'img' and 'alt' not in d:
            self.missing_alt.append(str(d.get('src') or '(source inconnue)'))

        if tag == 'a' and str(d.get('target') or '').lower() == '_blank':
            rel = {x.lower() for x in str(d.get('rel') or '').split()}
            if 'noopener' not in rel:
                self.unsafe_blank.append(str(d.get('href') or '(lien inconnu)'))

        if tag == 'meta' and str(d.get('http-equiv') or '').lower() == 'refresh':
            content = str(d.get('content') or '')
            m = re.search(r'url\s*=\s*[\'\"]?([^\'\";]+)', content, re.I)
            if m:
                target = m.group(1).strip()
                self.refreshes.append(target)
                self.refs.append(('meta-refresh', target))

        if tag == 'button':
            named = bool((d.get('aria-label') or '').strip() if isinstance(d.get('aria-label'), str) else d.get('aria-label'))
            named = named or bool((d.get('title') or '').strip() if isinstance(d.get('title'), str) else d.get('title'))
            self._buttons.append({'named': named, 'text': []})

    def handle_endtag(self, tag: str) -> None:
        if tag == 'button' and self._buttons:
            button = self._buttons.pop()
            text = ''.join(button['text']).strip()  # type: ignore[arg-type]
            if not button['named'] and not text:
                self.unnamed_buttons += 1

    def handle_data(self, data: str) -> None:
        if self._buttons:
            self._buttons[-1]['text'].append(data)  # type: ignore[union-attr]


def all_files() -> list[Path]:
    return [
        p for p in ROOT.rglob('*')
        if p.is_file() and '.git' not in p.parts and 'node_modules' not in p.parts
    ]


def is_external_or_special(raw: str) -> bool:
    if not raw or raw.startswith(('#', '//')):
        return True
    u = urlparse(raw)
    return u.scheme.lower() in SKIP_SCHEMES


def resolve(page: Path, raw: str) -> Path | None:
    if not raw or raw.startswith(('#', 'mailto:', 'tel:', 'javascript:', 'data:', 'blob:', '//')):
        return None
    u = urlparse(raw)
    if u.scheme in {'http', 'https'}:
        return None
    path = unquote(u.path)
    if not path:
        return None
    q = (ROOT / path.lstrip('/')) if path.startswith('/') else (page.parent / path)
    if path.endswith('/'):
        q = q / 'index.html'
    if not q.exists() and q.suffix == '' and (q / 'index.html').exists():
        q = q / 'index.html'
    return q.resolve()


def resolve_code_ref(source: Path, raw: str) -> Path | None:
    if not raw or raw.startswith(('#', '//', 'npm:', 'jsr:', 'node:', 'data:', 'blob:')):
        return None
    u = urlparse(raw)
    if u.scheme in {'http', 'https'}:
        return None
    path = unquote(u.path)
    if not path:
        return None
    return ((ROOT / path.lstrip('/')) if path.startswith('/') else (source.parent / path)).resolve()


def active_sinjira(rel: str) -> bool:
    normalized = rel.replace('\\', '/')
    return normalized.startswith(ACTIVE_SINJIRA_PREFIXES)


def main() -> int:
    errors: list[str] = []
    files = all_files()
    htmls = [p for p in files if p.suffix.lower() == '.html']
    js = [p for p in files if p.suffix.lower() == '.js']
    css = [p for p in files if p.suffix.lower() == '.css']
    code = [
        p for p in files
        if p.suffix.lower() in {'.js', '.ts'}
        and not p.relative_to(ROOT).as_posix().startswith(NATIVE_MOBILE_PREFIX)
    ]

    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        if p.name == '1':
            errors.append(f"Fichier parasite nommé '1': {rel}")
        if re.search(r'SINJIRA.*Livre.*01.*La.*Cendre.*Jugement(?!.*DEMO).*\.pdf$', rel, re.I) or re.search(r'MAITRE.*CORRIGE.*\.pdf$', rel, re.I):
            errors.append(f'Roman intégral potentiellement public: {rel}')
        if p.suffix.lower() in TEXT_EXTS and p.stat().st_size <= 3_000_000:
            text = p.read_text('utf-8', errors='ignore')
            for rx in SECRET_PATTERNS:
                if rx.search(text):
                    errors.append(f'Secret potentiel dans {rel}')
            if active_sinjira(rel) and 'formspree' in text.lower():
                errors.append(f'Formspree encore référencé dans une zone SINJIRA active: {rel}')
            if rel not in LEGACY_ADMIN_COMPAT_FILES and not rel.startswith('Admin/') and re.search(r"[\'\"]\/Admin\/", text):
                errors.append(f'Lien interne legacy /Admin/ dans {rel}')

    for page in htmls:
        rel = page.relative_to(ROOT).as_posix()
        text = page.read_text('utf-8', errors='ignore')
        parser = Parser()
        try:
            parser.feed(text)
            parser.close()
        except Exception as exc:
            errors.append(f'HTML impossible à analyser dans {rel}: {exc}')
            continue

        duplicates = sorted({x for x in parser.ids if parser.ids.count(x) > 1})
        if duplicates:
            errors.append(f"IDs dupliqués dans {rel}: {', '.join(duplicates)}")

        missing_fragments = sorted({frag for frag in parser.fragment_refs if frag and frag not in parser.ids})
        if missing_fragments:
            errors.append(f"Ancres locales introuvables dans {rel}: {', '.join(missing_fragments)}")

        if parser.missing_alt:
            errors.append(f"Image(s) sans attribut alt dans {rel}: {', '.join(parser.missing_alt[:8])}")
        if parser.unsafe_blank:
            errors.append(f"Lien(s) target=_blank sans rel=noopener dans {rel}: {', '.join(parser.unsafe_blank[:8])}")
        if parser.unnamed_buttons:
            errors.append(f"Bouton(s) sans nom accessible détecté(s) dans {rel}: {parser.unnamed_buttons}")

        for tag, raw in parser.refs:
            target = resolve(page, raw)
            if target is not None and not target.exists():
                errors.append(f'Référence manquante dans {rel} ({tag}): {raw}')
            if tag == 'meta-refresh' and target is not None and target == page.resolve():
                errors.append(f'Redirection vers elle-même dans {rel}: {raw}')

        # Évite le contenu actif HTTP non chiffré dans les pages HTTPS.
        for tag, raw in parser.refs:
            if raw.lower().startswith('http://') and tag in {'script', 'img', 'iframe', 'link', 'source', 'video', 'audio'}:
                errors.append(f'Ressource HTTP non sécurisée dans {rel} ({tag}): {raw}')

    # Dépendances locales CSS : url(...)
    css_url_rx = re.compile(r'url\(\s*([\'\"]?)([^\'\")]+)\1\s*\)', re.I)
    for sheet in css:
        rel = sheet.relative_to(ROOT).as_posix()
        text = sheet.read_text('utf-8', errors='ignore')
        for _, raw in css_url_rx.findall(text):
            raw = raw.strip()
            target = resolve_code_ref(sheet, raw)
            if target is not None and not target.exists():
                errors.append(f'Référence CSS manquante dans {rel}: {raw}')

    # Imports ES modules / Deno du site statique. L'app native est validée séparément.
    import_patterns = [
        re.compile(r'\bfrom\s*[\'\"]([^\'\"]+)[\'\"]'),
        re.compile(r'\bimport\s*[\'\"]([^\'\"]+)[\'\"]'),
        re.compile(r'\bimport\s*\(\s*[\'\"]([^\'\"]+)[\'\"]\s*\)'),
    ]
    for source in code:
        rel = source.relative_to(ROOT).as_posix()
        text = source.read_text('utf-8', errors='ignore')
        refs: set[str] = set()
        for pattern in import_patterns:
            refs.update(pattern.findall(text))
        for raw in sorted(refs):
            target = resolve_code_ref(source, raw)
            if target is not None and not target.exists():
                errors.append(f'Import local manquant dans {rel}: {raw}')

    critical_routes = [
        'index.html',
        '404.html',
        'admin/index.html',
        'admin/sinjira/index.html',
        'compte/index.html',
        'compte/profil.html',
        'compte/mon-personnage.html',
        'compte/reseau-personnage.html',
        'projets/sinjira/index.html',
        'projets/sinjira/registre/index.html',
        'projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html',
        'projets/sinjira/jeux/fracture-du-reseau-mere/partie.html',
        'projets/sinjira/jeux/fracture-du-reseau-mere/fin-de-partie.html',
    ]
    for rel in critical_routes:
        if not (ROOT / rel).exists():
            errors.append(f'Route critique absente: {rel}')

    try:
        subprocess.run(['node', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for p in js:
            r = subprocess.run(['node', '--check', str(p)], text=True, capture_output=True)
            if r.returncode:
                errors.append(f'Erreur JavaScript dans {p.relative_to(ROOT)}: {r.stderr.strip()}')
    except (FileNotFoundError, subprocess.CalledProcessError):
        print('AVERTISSEMENT: Node indisponible, validation JS ignorée.')

    print(
        f'Validation SINJIRA profonde: {len(htmls)} HTML, {len(css)} CSS, '
        f'{len(js)} JS, {len(files)} fichiers.'
    )
    if errors:
        print(f'ECHEC: {len(errors)} problème(s).')
        for e in errors:
            print('- ' + e)
        return 1
    print('OK: routes, ancres, dépendances, sécurité statique et JavaScript cohérents.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
