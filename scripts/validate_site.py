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
OFFICIAL_HOSTS = {'www.benoitcantin.com', 'benoitcantin.com'}
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
        # Les ancres HTML historiques <a name="..."> sont également
        # des destinations valides pour les liens interpages.
        if tag == 'a' and d.get('name'):
            self.ids.append(str(d['name']))

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
    """Résout aussi les URL absolues des domaines officiels vers le dépôt.

    Les liens externes restent hors périmètre. Une URL qui cible un dossier
    doit mener à son index.html : un dossier sans index n'est pas une page.
    """
    if not raw or raw.startswith('#'):
        return None
    u = urlparse(raw)
    if u.scheme or u.netloc:
        if u.scheme.lower() not in {'', 'http', 'https'} or (u.hostname or '').lower() not in OFFICIAL_HOSTS:
            return None
    path = unquote(u.path)
    if not path and u.netloc:
        path = '/'
    if not path:
        return None
    q = (ROOT / path.lstrip('/')) if path.startswith('/') else (page.parent / path)
    if path.endswith('/') or q.is_dir():
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


def cross_page_fragment_errors(pages: dict[Path, Parser]) -> list[str]:
    """Détecte les sections supprimées sur une autre page publique.

    Les URL externes restent hors périmètre; les deux domaines officiels
    sont traités comme des liens locaux lorsqu'une page du dépôt existe.
    Les ancres construites uniquement en JavaScript ne peuvent pas être
    déduites du HTML statique : ce contrôle vise les ancres documentaires.
    """
    errors: list[str] = []
    for page, parsed_page in pages.items():
        for tag, raw in parsed_page.refs:
            if tag != 'a':
                continue
            url = urlparse(raw)
            if not url.fragment or not url.path:
                continue
            if url.scheme or url.netloc:
                if url.scheme.lower() not in {'https', 'http'} or (url.hostname or '').lower() not in OFFICIAL_HOSTS:
                    continue
                # Ne suivre que le chemin, jamais les paramètres de requête.
                target = resolve(page, url.path)
            else:
                target = resolve(page, raw)
            if target is None or target not in pages:
                continue
            fragment = unquote(url.fragment)
            if fragment not in pages[target].ids:
                source_rel = page.relative_to(ROOT).as_posix()
                target_rel = target.relative_to(ROOT).as_posix()
                errors.append(
                    f'Ancre interpage introuvable dans {source_rel}: '
                    f'{raw} (cible {target_rel}#{fragment})'
                )
    return errors


def test_cross_page_fragment_contract() -> list[str]:
    """Cas positifs/négatifs, vérifiés par la CI sans accès réseau."""
    base = ROOT / '__ci_fragment_fixture__'
    origin, destination = base / 'origin.html', base / 'destination.html'
    page = Parser()
    page.feed(
        '<a href="destination.html#valide">Lien correct</a>'
        '<a href="destination.html#absente">Lien cassé</a>'
        '<a href="destination.html#ancien">Lien legacy</a>'
        '<a href="destination.html#caf%C3%A9">Lien encodé</a>'
        '<a href="https://www.benoitcantin.com/__ci_fragment_fixture__/destination.html#valide">URL officielle valide</a>'
        '<a href="https://www.benoitcantin.com/__ci_fragment_fixture__/destination.html#absente-officielle">URL officielle invalide</a>'
        '<a href="https://exemple.invalid/docs#autre">URL externe</a>'
        '<a href="#intra">Ancre locale vérifiée ailleurs</a>'
    )
    target = Parser()
    target.feed('<section id="valide"></section><a name="ancien"></a><h2 id="café"></h2>')
    errors = cross_page_fragment_errors({origin: page, destination: target})
    if (len(errors) != 2 or not any('destination.html#absente' in error for error in errors)
            or not any('absente-officielle' in error for error in errors)):
        return ['Auto-test des liens interpages défaillant : cas valide, absent, legacy ou encodé']
    return []


def test_official_link_resolution_contract() -> list[str]:
    """Protège les liens publics absolus et les chemins de dossiers."""
    origin = ROOT / 'index.html'
    cases = {
        'https://www.benoitcantin.com/': ROOT / 'index.html',
        'https://benoitcantin.com/compte/': ROOT / 'compte/index.html',
        '//www.benoitcantin.com/compte/': ROOT / 'compte/index.html',
        '/assets/': ROOT / 'assets/index.html',
        '/assets': ROOT / 'assets/index.html',
        'https://www.benoitcantin.com/__ci_lien_absent__.html': ROOT / '__ci_lien_absent__.html',
    }
    errors: list[str] = []
    for href, expected in cases.items():
        actual = resolve(origin, href)
        if actual != expected.resolve():
            errors.append(f'Auto-test résolution des liens publics défaillant: {href} -> {actual}')
    for href in ('https://exemple.invalid/compte/', '//exemple.invalid/compte/', 'mailto:contact@example.org', '#contenu'):
        if resolve(origin, href) is not None:
            errors.append(f'Auto-test liens externes/spéciaux défaillant: {href}')
    # La cible fabriquée est absente; cela vérifie le cas que le
    # validateur de références doit désormais signaler.
    if (ROOT / '__ci_lien_absent__.html').exists():
        errors.append('Fixture inattendue présente: __ci_lien_absent__.html')
    return errors


def main() -> int:
    errors: list[str] = test_cross_page_fragment_contract() + test_official_link_resolution_contract()
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

    page_parsers: dict[Path, Parser] = {}
    for page in htmls:
        rel = page.relative_to(ROOT).as_posix()
        text = page.read_text('utf-8', errors='ignore')
        parser = Parser()
        try:
            parser.feed(text)
            parser.close()
            page_parsers[page.resolve()] = parser
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

    # Les liens page.html#section doivent aussi rejoindre une ancre
    # existante sur leur page de destination.
    errors.extend(cross_page_fragment_errors(page_parsers))

    # Contrat de continuité des navigations : les pages de secours et de
    # référence doivent servir le même script que l'accueil, sous peine de
    # conserver les anciens comportements du menu après changement de page.
    expected_site_script = {
        '404.html', 'univers.html', 'compte/vie-privee.html',
        'transparence-ia.html', 'confidentialite.html',
        'gouvernance-vie-privee.html', 'avis-legal.html',
    }
    expected_nova_script = {
        'projets/projet-nova/registre-rencontres.html',
        'projets/projet-nova/visionneuse.html',
        'projets/projet-nova/document.html',
        'projets/projet-nova/code-conduite.html',
        'projets/projet-nova/finances.html',
    }
    for rel, version, script_path in (
        *((rel, '24.4.100', 'assets/js/site.js') for rel in sorted(expected_site_script)),
        *((rel, '26.1.0', 'script.js') for rel in sorted(expected_nova_script)),
    ):
        page = ROOT / rel
        if not page.is_file():
            errors.append(f'Parcours public manquant: {rel}')
            continue
        html = page.read_text('utf-8', errors='replace')
        script_sources = re.findall(r"""<script[^>]*src=["']([^"']+)["']""", html, re.I)
        versions = [
            src.split('?v=', 1)[1] if '?v=' in src else '(sans version)'
            for src in script_sources if src.split('?', 1)[0].endswith(script_path)
        ]
        if versions != [version]:
            errors.append(f'Navigation incohérente dans {rel}: version {version} attendue, trouvée {versions}')
        if 'data-menu-toggle' not in html or 'data-main-nav' not in html:
            errors.append(f'Navigation mobile absente sur le parcours public: {rel}')

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
    print('OK: routes, ancres locales et interpages, dépendances, sécurité statique et JavaScript cohérents.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
