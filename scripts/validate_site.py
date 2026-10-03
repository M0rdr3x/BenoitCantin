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
PERSONAL_CONTACT_PAGE = ROOT / 'contact.html'
LEGACY_PERSONAL_FORMSPREE_ENDPOINT = 'https://formspree.io/f/xdenkzrv'
NOVA_FORMSPREE_ENDPOINT = 'https://formspree.io/f/xkolwjdg'
PERSONAL_CONTACT_PENDING_STATE = 'pending-separate-endpoint'
PERSONAL_CONTACT_ACTIVE_STATE = 'active-separate-endpoint'
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
        for copy in PERSONAL_CONTACT_ACTIVE_COPIES:
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
        for copy in PERSONAL_CONTACT_PENDING_COPIES:
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
        + ''.join(PERSONAL_CONTACT_PENDING_COPIES)
        + "<script>var PERSONAL_ENDPOINT='';" + runtime_gate + "</script>"
    )
    active_endpoint = 'https://formspree.io/f/personalSafe42'
    active_contact = (
        '<form id="contact-general" data-personal-formspree-state="active-separate-endpoint">'
        '<button aria-disabled="true" disabled id="contact-submit">Envoyer</button></form>'
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
        'texte actif retiré': active_contact.replace(PERSONAL_CONTACT_ACTIVE_COPIES[0], ''),
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


def main() -> int:
    self_test_personal_contact_contract()
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
    print('OK: routes, ancres, dépendances, sécurité statique et JavaScript cohérents.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
