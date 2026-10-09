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
LEGACY_ADMIN_COMPAT_FILES = {'sw.js', 'assets/js/v24-3-3-runtime.js', 'vercel.json'}
PERSONAL_CONTACT_PAGE = ROOT / 'contact.html'
LEGACY_PERSONAL_FORMSPREE_ENDPOINT = 'https://formspree.io/f/xdenkzrv'
NOVA_FORMSPREE_ENDPOINT = 'https://formspree.io/f/xkolwjdg'
PERSONAL_CONTACT_PENDING_STATE = 'pending-separate-endpoint'
PERSONAL_CONTACT_ACTIVE_STATE = 'active-separate-endpoint'
PERSONAL_CONTACT_PENDING_META = 'Canaux de contact de Benoit Cantin pour SINJIRA™, le Registre des Consciences, la vie privée et Projet Nova. Formulaire personnel temporairement désactivé.'
PERSONAL_CONTACT_ACTIVE_META = 'Canaux de contact de Benoit Cantin pour SINJIRA™, le Registre des Consciences, la vie privée et Projet Nova. Formulaire personnel actif sur un canal distinct.'
PERSONAL_CONTACT_PENDING_HERO = 'Choisissez la destination concernée. Le formulaire personnel reste temporairement désactivé pendant la configuration de son canal distinct; Projet Nova conserve son contact officiel séparé.'
PERSONAL_CONTACT_ACTIVE_HERO = 'Choisissez la destination concernée. Le formulaire personnel utilise son canal Formspree distinct; Projet Nova conserve son contact officiel séparé.'
PERSONAL_CONTACT_PENDING_SECURITY = 'Le formulaire personnel est temporairement désactivé. Ne publiez pas un signalement de sécurité contenant des détails sensibles sur un canal public. À sa réactivation, choisissez « Sécurité / vulnérabilité » et ne transmettez aucun mot de passe, clé ou jeton.'
PERSONAL_CONTACT_ACTIVE_SECURITY = 'Pour signaler un problème de sécurité, choisissez « Sécurité / vulnérabilité » dans le formulaire. Indiquez la page concernée, le comportement observé et les étapes de reproduction, sans transmettre de mot de passe, clé, jeton ou donnée personnelle inutile.'
PERSONAL_CONTACT_PENDING_PRIVACY_COPY = '<strong>Le formulaire personnel du portail est actuellement désactivé</strong>'
PERSONAL_CONTACT_PENDING_GOVERNANCE_COPY = 'Le formulaire officiel de contact personnel peut rester désactivé tant qu’un endpoint Formspree distinct de Projet Nova n’est pas configuré et vérifié.'
PERSONAL_CONTACT_ACTIVE_PRIVACY_COPY = '<strong>Le formulaire personnel du portail utilise un endpoint Formspree distinct de Projet Nova configuré et vérifié</strong>'
PERSONAL_CONTACT_ACTIVE_GOVERNANCE_COPY = 'Le formulaire officiel de contact personnel utilise un endpoint Formspree distinct de Projet Nova configuré et vérifié.'
PERSONAL_CONTACT_PENDING_COPIES = (
    'Pendant la configuration de ce nouvel endpoint personnel, le formulaire reste volontairement désactivé',
    'Lorsque le formulaire personnel sera réactivé, il utilisera <strong>Formspree</strong> avec un endpoint distinct de Projet Nova',
    'Aucune soumission personnelle n’est envoyée à Formspree tant que le nouvel endpoint distinct n’est pas configuré.',
)
PERSONAL_CONTACT_ACTIVE_COPIES = (
    'Le formulaire personnel utilise un endpoint Formspree distinct de Projet Nova, configuré et vérifié.',
    'Le formulaire personnel utilise <strong>Formspree</strong> avec un endpoint distinct de Projet Nova configuré et vérifié',
    'Les soumissions personnelles sont envoyées uniquement au canal Formspree personnel distinct de Projet Nova.',
)


def srcset_urls(raw: str) -> list[str]:
    """Extraire les URL de srcset sans casser une URL data: contenant une virgule.

    Un candidat s'arrête à l'espace précédant son descripteur (480w, 2x),
    ou à la virgule finale pour les candidats sans descripteur.
    """
    urls: list[str] = []
    index = 0
    while index < len(raw):
        while index < len(raw) and (raw[index].isspace() or raw[index] == ','):
            index += 1
        start = index
        while index < len(raw) and not raw[index].isspace():
            index += 1
        token = raw[start:index]
        if not token:
            break
        urls.append(token.rstrip(','))
        if token.endswith(','):
            continue
        parentheses = 0
        while index < len(raw):
            char = raw[index]
            if char == '(':
                parentheses += 1
            elif char == ')' and parentheses:
                parentheses -= 1
            elif char == ',' and not parentheses:
                index += 1
                break
            index += 1
    return [url for url in urls if url]

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

        # Une image responsive peut disposer d'un src valide mais d'un srcset
        # brisé pour mobile / haute densité. Chaque URL est une dépendance
        # vérifiée au même titre que src, y compris sous <picture>/<source>.
        candidates = ('srcset',) if tag in {'img', 'source'} else ('imagesrcset',) if tag == 'link' else ()
        for candidate_attr in candidates:
            if d.get(candidate_attr):
                for candidate_url in srcset_urls(str(d[candidate_attr])):
                    self.refs.append((tag, candidate_url))

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


def test_srcset_contract() -> list[str]:
    """Cas mobile/densité, data URI, virgule encodée et preload d'image."""
    errors: list[str] = []
    cases = {
        'a-480.webp 480w, a-960.webp 960w': ['a-480.webp', 'a-960.webp'],
        '/assets/a.webp 1x, /assets/b.webp 2x': ['/assets/a.webp', '/assets/b.webp'],
        'a.webp, b.webp': ['a.webp', 'b.webp'],
        'data:image/svg+xml,%3Csvg%3E 1x, photo.webp 2x': [
            'data:image/svg+xml,%3Csvg%3E', 'photo.webp'
        ],
        'photo%2Cretina.webp 2x': ['photo%2Cretina.webp'],
    }
    for raw, expected in cases.items():
        if srcset_urls(raw) != expected:
            errors.append(f'Auto-test srcset défaillant pour: {raw}')

    parser = Parser()
    parser.feed(
        '<picture><source srcset="tablet.webp 768w, desktop.webp 1200w">'
        '<img src="fallback.webp" srcset="mobile.webp 1x, mobile@2x.webp 2x" alt="Image">'
        '</picture>'
        '<link rel="preload" as="image" imagesrcset="preload.webp 2x">'
    )
    actual = [raw for tag, raw in parser.refs if raw != 'fallback.webp']
    expected = ['tablet.webp', 'desktop.webp', 'mobile.webp', 'mobile@2x.webp', 'preload.webp']
    if actual != expected:
        errors.append(f'Auto-test extraction des références HTML srcset: {actual}')
    return errors


def validate_personal_contact_contract(contact_text: str, privacy_text: str, governance_text: str) -> list[str]:
    errors: list[str] = []
    if LEGACY_PERSONAL_FORMSPREE_ENDPOINT in contact_text:
        errors.append('Ancien endpoint Formspree personnel xdenkzrv encore présent dans contact.html')
    if NOVA_FORMSPREE_ENDPOINT in contact_text:
        errors.append('Endpoint Formspree Projet Nova interdit dans contact.html')

    endpoint_matches = re.findall(r"var PERSONAL_ENDPOINT='([^']*)'", contact_text)
    if len(endpoint_matches) != 1:
        errors.append('Déclaration PERSONAL_ENDPOINT unique requise dans contact.html')
        endpoint = ''
    else:
        endpoint = endpoint_matches[0].strip()

    pending_marker = f'data-personal-formspree-state="{PERSONAL_CONTACT_PENDING_STATE}"'
    active_marker = f'data-personal-formspree-state="{PERSONAL_CONTACT_ACTIVE_STATE}"'
    pending = pending_marker in contact_text
    active = active_marker in contact_text
    if pending == active:
        errors.append('État Formspree personnel unique requis: pending ou active-separate-endpoint')

    form_match = re.search(r'<form\b[^>]*\bid=["\']contact-general["\'][^>]*>', contact_text, re.I)
    if not form_match:
        errors.append('Formulaire personnel #contact-general introuvable')
    else:
        opening_form = form_match.group(0)
        if re.search(r'\baction\s*=', opening_form, re.I) or re.search(r'\bmethod\s*=', opening_form, re.I):
            errors.append('Le formulaire personnel doit rester sans action/method statique; le JS les pose seulement après validation endpoint')

    if 'id="contact-submit"' not in contact_text:
        errors.append('Bouton contact personnel identifiable absent')
    if 'aria-disabled="true"' not in contact_text or not re.search(r'<button\b[^>]*\bdisabled\b[^>]*\bid=["\']contact-submit["\']', contact_text, re.I):
        errors.append('Bouton contact personnel doit rester désactivé par défaut avant validation JavaScript')
    if '<option value="Projet Nova">Projet Nova</option>' in contact_text:
        errors.append('Projet Nova ne doit plus être routé par le formulaire personnel')
    runtime_gate = "form.getAttribute('data-personal-formspree-state')==='active-separate-endpoint'&&/^https:\\/\\/formspree\\.io\\/f\\/[A-Za-z0-9_-]+$/.test(PERSONAL_ENDPOINT)"
    if runtime_gate not in contact_text:
        errors.append('Le runtime contact doit exiger état active-separate-endpoint ET endpoint Formspree valide')

    if not endpoint:
        if not pending or active:
            errors.append('Endpoint personnel vide exige data-personal-formspree-state=pending-separate-endpoint')
        for copy in PERSONAL_CONTACT_PENDING_COPIES:
            if copy not in contact_text:
                errors.append(f'Texte public pending manquant dans contact.html: {copy}')
        if contact_text.count(PERSONAL_CONTACT_PENDING_META) != 4:
            errors.append('Métadonnées Contact pending: 4 occurrences exactes requises (description/OG/Twitter/JSON-LD)')
        for copy in (PERSONAL_CONTACT_PENDING_HERO, PERSONAL_CONTACT_PENDING_SECURITY):
            if copy not in contact_text:
                errors.append(f'Texte public pending manquant dans contact.html: {copy}')
        for copy in (*PERSONAL_CONTACT_ACTIVE_COPIES, PERSONAL_CONTACT_ACTIVE_META, PERSONAL_CONTACT_ACTIVE_HERO, PERSONAL_CONTACT_ACTIVE_SECURITY):
            if copy in contact_text:
                errors.append('Texte public actif interdit tant que le contact personnel est pending')
        if PERSONAL_CONTACT_PENDING_PRIVACY_COPY not in privacy_text:
            errors.append('Politique de confidentialité non alignée sur le contact personnel fail-closed')
        if PERSONAL_CONTACT_PENDING_GOVERNANCE_COPY not in governance_text:
            errors.append('Gouvernance vie privée non alignée sur le contact personnel fail-closed')
    else:
        if not re.fullmatch(r'https://formspree\.io/f/[A-Za-z0-9_-]+', endpoint):
            errors.append('Endpoint Formspree personnel invalide dans contact.html')
        if endpoint in {LEGACY_PERSONAL_FORMSPREE_ENDPOINT, NOVA_FORMSPREE_ENDPOINT}:
            errors.append('Endpoint Formspree personnel doit être distinct des endpoints historiques/Nova')
        if not active or pending:
            errors.append('Endpoint personnel configuré exige data-personal-formspree-state=active-separate-endpoint')
        for copy in PERSONAL_CONTACT_ACTIVE_COPIES:
            if copy not in contact_text:
                errors.append(f'Texte public actif manquant dans contact.html: {copy}')
        if contact_text.count(PERSONAL_CONTACT_ACTIVE_META) != 4:
            errors.append('Métadonnées Contact actives: 4 occurrences exactes requises (description/OG/Twitter/JSON-LD)')
        for copy in (PERSONAL_CONTACT_ACTIVE_HERO, PERSONAL_CONTACT_ACTIVE_SECURITY):
            if copy not in contact_text:
                errors.append(f'Texte public actif manquant dans contact.html: {copy}')
        for copy in (*PERSONAL_CONTACT_PENDING_COPIES, PERSONAL_CONTACT_PENDING_META, PERSONAL_CONTACT_PENDING_HERO, PERSONAL_CONTACT_PENDING_SECURITY):
            if copy in contact_text:
                errors.append('Texte public pending interdit avec un endpoint personnel actif')
        if PERSONAL_CONTACT_ACTIVE_PRIVACY_COPY not in privacy_text:
            errors.append('Politique de confidentialité doit confirmer explicitement l’activation du canal personnel distinct')
        if PERSONAL_CONTACT_ACTIVE_GOVERNANCE_COPY not in governance_text:
            errors.append('Gouvernance vie privée doit confirmer explicitement l’activation du canal personnel distinct')

    return errors


def self_test_personal_contact_contract() -> None:
    runtime_gate = "function endpointReady(){return form.getAttribute('data-personal-formspree-state')==='active-separate-endpoint'&&/^https:\\/\\/formspree\\.io\\/f\\/[A-Za-z0-9_-]+$/.test(PERSONAL_ENDPOINT)}"
    pending_contact = (
        '<form id="contact-general" data-personal-formspree-state="pending-separate-endpoint">'
        '<button aria-disabled="true" disabled id="contact-submit">Configuration</button></form>'
        + (PERSONAL_CONTACT_PENDING_META * 4)
        + PERSONAL_CONTACT_PENDING_HERO
        + PERSONAL_CONTACT_PENDING_SECURITY
        + ''.join(PERSONAL_CONTACT_PENDING_COPIES)
        + "<script>var PERSONAL_ENDPOINT='';" + runtime_gate + "</script>"
    )
    active_endpoint = 'https://formspree.io/f/personalSafe42'
    active_contact = (
        '<form id="contact-general" data-personal-formspree-state="active-separate-endpoint">'
        '<button aria-disabled="true" disabled id="contact-submit">Envoyer</button></form>'
        + (PERSONAL_CONTACT_ACTIVE_META * 4)
        + PERSONAL_CONTACT_ACTIVE_HERO
        + PERSONAL_CONTACT_ACTIVE_SECURITY
        + ''.join(PERSONAL_CONTACT_ACTIVE_COPIES)
        + f"<script>var PERSONAL_ENDPOINT='{active_endpoint}';" + runtime_gate + "</script>"
    )
    pending_privacy = PERSONAL_CONTACT_PENDING_PRIVACY_COPY
    pending_governance = PERSONAL_CONTACT_PENDING_GOVERNANCE_COPY
    active_privacy = PERSONAL_CONTACT_ACTIVE_PRIVACY_COPY
    active_governance = PERSONAL_CONTACT_ACTIVE_GOVERNANCE_COPY

    if validate_personal_contact_contract(pending_contact, pending_privacy, pending_governance):
        raise SystemExit('ERREUR auto-test contact personnel: état pending valide refusé.')
    if validate_personal_contact_contract(active_contact, active_privacy, active_governance):
        raise SystemExit('ERREUR auto-test contact personnel: état actif distinct valide refusé.')

    cases = {
        'endpoint rempli mais état pending': active_contact.replace(PERSONAL_CONTACT_ACTIVE_STATE, PERSONAL_CONTACT_PENDING_STATE),
        'endpoint historique réintroduit': active_contact.replace(active_endpoint, LEGACY_PERSONAL_FORMSPREE_ENDPOINT),
        'endpoint Nova réintroduit': active_contact.replace(active_endpoint, NOVA_FORMSPREE_ENDPOINT),
        'action statique ajoutée': pending_contact.replace('<form id="contact-general"', '<form action="https://formspree.io/f/test" id="contact-general"'),
        'déclaration endpoint retirée': pending_contact.replace("var PERSONAL_ENDPOINT='';", "var OTHER_ENDPOINT='';"),
        'garde runtime état actif retirée': pending_contact.replace("form.getAttribute('data-personal-formspree-state')==='active-separate-endpoint'&&", ''),
        'texte pending retiré': pending_contact.replace(PERSONAL_CONTACT_PENDING_COPIES[0], ''),
        'métadonnée pending retirée': pending_contact.replace(PERSONAL_CONTACT_PENDING_META, '', 1),
        'hero pending retiré': pending_contact.replace(PERSONAL_CONTACT_PENDING_HERO, '', 1),
        'sécurité pending retirée': pending_contact.replace(PERSONAL_CONTACT_PENDING_SECURITY, '', 1),
        'texte actif retiré': active_contact.replace(PERSONAL_CONTACT_ACTIVE_COPIES[0], ''),
        'métadonnée active retirée': active_contact.replace(PERSONAL_CONTACT_ACTIVE_META, '', 1),
        'hero actif retiré': active_contact.replace(PERSONAL_CONTACT_ACTIVE_HERO, '', 1),
        'sécurité active retirée': active_contact.replace(PERSONAL_CONTACT_ACTIVE_SECURITY, '', 1),
    }
    for name, mutated_contact in cases.items():
        errors = validate_personal_contact_contract(
            mutated_contact,
            active_privacy if 'endpoint ' in name and name != 'endpoint rempli mais état pending' else pending_privacy,
            active_governance if 'endpoint ' in name and name != 'endpoint rempli mais état pending' else pending_governance,
        )
        if not errors:
            raise SystemExit(f'ERREUR auto-test contact personnel: affaiblissement non détecté: {name}')

    stale_docs = validate_personal_contact_contract(active_contact, pending_privacy, pending_governance)
    if not any('confidentialité' in error or 'Gouvernance' in error for error in stale_docs):
        raise SystemExit('ERREUR auto-test contact personnel: documentation pending acceptée avec endpoint actif.')



def validate_service_worker_privacy(sw_text: str) -> list[str]:
    errors: list[str] = []
    required_markers = (
        "u.pathname==='/app'",
        "u.pathname.startsWith('/app/')",
        "u.pathname==='/compte'",
        "u.pathname.startsWith('/compte/')",
        "u.pathname==='/Admin'",
        "u.pathname.startsWith('/Admin/')",
        "u.pathname==='/admin'",
        "u.pathname.startsWith('/admin/')",
        "u.pathname==='/histoire-de-vie'",
        "u.pathname.startsWith('/histoire-de-vie/')",
        "u.pathname==='/supabase'",
        "u.pathname.startsWith('/supabase/')",
        "const releaseMarker=u.pathname==='/.well-known/release.json';",
        "if(releaseMarker){e.respondWith(fetch(new Request(r,{cache:'no-store'})));return}",
        "if(privatePath){e.respondWith(fetch(new Request(r,{cache:'no-store'}))",
        "function cacheableResponse(resp)",
        "resp.headers.get('Cache-Control')",
        "cc.indexOf('no-store')===-1",
        "if(cacheableResponse(resp)){const cp=resp.clone();",
        "if(cacheableResponse(resp))caches.open(CACHE)",
        "u.pathname.indexOf('/documents/')===-1",
    )
    for marker in required_markers:
        if marker not in sw_text:
            errors.append(f'Service worker: garde privée/no-store absente: {marker}')
    if "caches.open(CACHE).then(c=>c.put(r,cp))" not in sw_text:
        errors.append('Service worker: stratégie document publique attendue absente.')
    return errors


def self_test_service_worker_privacy(sw_text: str) -> None:
    clean = validate_service_worker_privacy(sw_text)
    if clean:
        raise SystemExit('ERREUR auto-test service worker: cas sain refusé: ' + ' | '.join(clean))

    mutations = {
        'histoire de vie recachable': sw_text.replace("u.pathname==='/histoire-de-vie'||u.pathname.startsWith('/histoire-de-vie/')||", '', 1),
        'compte sans slash recachable': sw_text.replace("u.pathname==='/compte'||", '', 1),
        'release marker recachable': sw_text.replace(
            "if(releaseMarker){e.respondWith(fetch(new Request(r,{cache:'no-store'})));return}",
            "if(releaseMarker){return}",
            1,
        ),
        'no-store privé retiré': sw_text.replace(
            "if(privatePath){e.respondWith(fetch(new Request(r,{cache:'no-store'}))",
            "if(privatePath){e.respondWith(fetch(r)",
            1,
        ),
        'réponses no-store recachables': sw_text.replace("cc.indexOf('no-store')===-1", "true", 1),
        'documents recachables': sw_text.replace("u.pathname.indexOf('/documents/')===-1", "true", 1),
    }
    for label, mutated in mutations.items():
        if mutated == sw_text:
            raise SystemExit(f'ERREUR auto-test service worker: mutation sans effet: {label}')
        if not validate_service_worker_privacy(mutated):
            raise SystemExit(f'ERREUR auto-test service worker: affaiblissement non détecté: {label}')



def validate_livre_i_demo_reader_text(demo_html: str, reader_js: str, progress_js: str) -> list[str]:
    errors: list[str] = []
    required_demo = (
        'Édition démo · 84 pages · Prologue + chapitres 1 à 3',
        'data-reader-total-pages="84"',
        'data-reader-page-number max="84"',
        'type="number" value="1"/> / 84',
        'data-reader-progress-native max="84" value="1">1 sur 84',
    )
    for marker in required_demo:
        if marker not in demo_html:
            errors.append(f'Livre I démo: marqueur 84 pages absent: {marker}')
    if 'max="83"' in demo_html or '/ 83<' in demo_html or '>1 sur 83<' in demo_html:
        errors.append('Livre I démo: ancien plafond 83 pages encore présent dans le HTML.')

    required_reader = (
        'const configuredTotalPages=Number(document.body.dataset.readerTotalPages||84);',
        'const totalPages=Number.isFinite(configuredTotalPages)&&configuredTotalPages>0?Math.floor(configuredTotalPages):84;',
        'Math.round((safePage/totalPages)*100)',
        'Math.min(totalPages,Math.max(1,saved))',
        'Math.round(current/totalPages*100)',
        '${current} sur ${totalPages}',
        'Math.min(totalPages,current+1)',
        'Math.min(totalPages,Math.max(1,Number(input.value)||1))',
    )
    for marker in required_reader:
        if marker not in reader_js:
            errors.append(f'Livre I lecteur: contrat 84 pages absent: {marker}')
    if '/83' in reader_js or 'Math.min(83' in reader_js or '${current} sur 83' in reader_js:
        errors.append('Livre I lecteur: ancien calcul 83 pages encore présent.')

    if 'Math.round((pageValue/84)*100)' not in progress_js:
        errors.append('Livre I progression canonique: calcul 84 pages absent.')
    if 'pageValue/83' in progress_js:
        errors.append('Livre I progression canonique: ancien calcul 83 pages encore présent.')
    return errors


def self_test_livre_i_demo_reader() -> None:
    demo = (
        '<body data-reader-total-pages="84"><span>Édition démo · 84 pages · Prologue + chapitres 1 à 3</span>'
        '<input data-reader-page-number max="84" type="number" value="1"/> / 84'
        '<progress data-reader-progress-native max="84" value="1">1 sur 84</progress>'
    )
    reader = (
        'const configuredTotalPages=Number(document.body.dataset.readerTotalPages||84);'
        'const totalPages=Number.isFinite(configuredTotalPages)&&configuredTotalPages>0?Math.floor(configuredTotalPages):84;'
        'Math.round((safePage/totalPages)*100);'
        'Math.min(totalPages,Math.max(1,saved));'
        'Math.round(current/totalPages*100);'
        '${current} sur ${totalPages};'
        'Math.min(totalPages,current+1);'
        'Math.min(totalPages,Math.max(1,Number(input.value)||1));'
    )
    progress = 'Math.round((pageValue/84)*100)'
    clean = validate_livre_i_demo_reader_text(demo, reader, progress)
    if clean:
        raise SystemExit('ERREUR auto-test Livre I 84 pages: cas sain rejeté: ' + '; '.join(clean))

    cases = {
        'HTML 83 pages': (demo.replace('max="84"', 'max="83"', 1), reader, progress),
        'lecteur 83 pages': (demo, reader.replace('current/totalPages', 'current/83', 1), progress),
        'plafond de lecture 83': (demo, reader.replace('Math.min(totalPages,current+1)', 'Math.min(83,current+1)'), progress),
        'attribut du lecteur 83': (demo.replace('data-reader-total-pages="84"', 'data-reader-total-pages="83"'), reader, progress),
        'progression 83 pages': (demo, reader, progress.replace('pageValue/84', 'pageValue/83')),
    }
    for label, values in cases.items():
        if not validate_livre_i_demo_reader_text(*values):
            raise SystemExit(f'ERREUR auto-test Livre I 84 pages: régression non détectée: {label}')
    print(f'OK auto-tests Livre I 84 pages: {len(cases)} régressions détectées.')


def main() -> int:
    self_test_personal_contact_contract()
    self_test_livre_i_demo_reader()
    sw_path = ROOT / 'sw.js'
    if not sw_path.is_file():
        raise SystemExit('ERREUR: sw.js absent pour la validation de confidentialité PWA.')
    sw_text = sw_path.read_text('utf-8', errors='strict')
    self_test_service_worker_privacy(sw_text)
    errors: list[str] = (
        test_cross_page_fragment_contract()
        + test_official_link_resolution_contract()
        + test_srcset_contract()
    )
    errors.extend(validate_service_worker_privacy(sw_text))

    demo_path = ROOT / 'projets/sinjira/romans/lire-demo.html'
    reader_path = ROOT / 'assets/js/sinjira-reader.js'
    progress_path = ROOT / 'assets/js/sinjira-reader-progress-v24-4-61.js'
    for required_path in (demo_path, reader_path, progress_path):
        if not required_path.is_file():
            errors.append(f'Livre I démo: fichier requis absent: {required_path.relative_to(ROOT).as_posix()}')
    if demo_path.is_file() and reader_path.is_file() and progress_path.is_file():
        errors.extend(validate_livre_i_demo_reader_text(
            demo_path.read_text('utf-8', errors='strict'),
            reader_path.read_text('utf-8', errors='strict'),
            progress_path.read_text('utf-8', errors='strict'),
        ))
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

    # Verifier les ancres interpages, y compris les domaines officiels.
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

    # Contrat d’activation du formulaire personnel : transition explicite pending -> active.
    if not PERSONAL_CONTACT_PAGE.is_file():
        errors.append('Page de contact personnelle absente: contact.html')
    else:
        privacy_path = ROOT / 'confidentialite.html'
        governance_path = ROOT / 'gouvernance-vie-privee.html'
        contact_text = PERSONAL_CONTACT_PAGE.read_text('utf-8', errors='ignore')
        privacy_text = privacy_path.read_text('utf-8', errors='ignore') if privacy_path.is_file() else ''
        governance_text = governance_path.read_text('utf-8', errors='ignore') if governance_path.is_file() else ''
        if not privacy_path.is_file():
            errors.append('Politique de confidentialité absente pour le contrat contact personnel')
        if not governance_path.is_file():
            errors.append('Gouvernance vie privée absente pour le contrat contact personnel')
        errors.extend(validate_personal_contact_contract(contact_text, privacy_text, governance_text))

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
    print('OK: routes, ancres locales et interpages, images responsives, confidentialite et JavaScript coherents.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
