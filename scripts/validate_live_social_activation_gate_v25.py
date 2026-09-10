#!/usr/bin/env python3
import ast
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'supabase' / 'production-migration-ledger.txt'
MIGRATIONS = ROOT / 'supabase' / 'migrations'
MANIFEST = ROOT / 'scripts' / 'validate_production_schema_manifest.py'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-live-social-activation-gate-v25.yml'

REQUIRED_MIGRATIONS = (
    ('20260908120000', 'sinjira_v25_live_social_foundation'),
    ('20260908121000', 'sinjira_v25_live_social_realtime_eligibility'),
    ('20260908122000', 'sinjira_v25_live_social_helper_invoker'),
    ('20260908130000', 'sinjira_v25_live_social_moderation'),
    ('20260908131000', 'sinjira_v25_live_social_private_invites'),
    ('20260908132000', 'sinjira_v25_live_social_safety_convergence'),
    ('20260908140000', 'sinjira_v25_live_social_typed_commands'),
    ('20260908150000', 'sinjira_v25_live_social_share_codes'),
)

LIVE_TABLES = frozenset({
    'social_live_rooms',
    'social_live_room_members',
    'social_live_messages',
    'social_live_room_invites',
    'social_live_room_share_codes',
})

# Une convergence technique n'est jamais une autorisation de publication.
# L'activation publique d'En direct reste une décision humaine séparée et explicite.
PUBLIC_ACTIVATION_POLICY = 'HUMAN_REVIEW_REQUIRED'

# Conservées pour les tests/contrats historiques; find_html_mounts() utilise aussi
# HTMLParser afin de couvrir les attributs HTML valides non guillemetés.
SCRIPT_MOUNT_RE = re.compile(
    r'<script\b[^>]*\bsrc\s*=\s*["\'][^"\']*'
    r'(sinjira-live-(?:ui-shell-v25|ui-v25|share-codes-ui-v25|invites-ui-v25|community-bridge-v25)\.js)[^"\']*["\']',
    re.IGNORECASE,
)
STYLE_MOUNT_RE = re.compile(
    r'<link\b[^>]*\bhref\s*=\s*["\'][^"\']*'
    r'(v25-live-(?:ui|share-codes|invites)\.css)[^"\']*["\']',
    re.IGNORECASE,
)
MODULE_IMPORT_RE = re.compile(
    r'(?:\bfrom\s*|\bimport\s*(?:\(\s*)?)["\']([^"\']+)["\']',
    re.IGNORECASE,
)
CSS_COMMENT_RE = re.compile(r'/\*.*?\*/', re.DOTALL)
CSS_IMPORT_RE = re.compile(
    r'@import\s+(?:url\(\s*)?(?:["\']([^"\']+)["\']|([^\s);]+))\s*\)?',
    re.IGNORECASE,
)
LIVE_MODULE_NAME_RE = re.compile(r'(sinjira-live-[A-Za-z0-9_-]+\.js)', re.IGNORECASE)
LIVE_STYLE_NAME_RE = re.compile(r'(v25-live-[A-Za-z0-9_-]+\.css)', re.IGNORECASE)
LEDGER_ROW_RE = re.compile(r'^(\d{14})\s+[A-Za-z0-9_]+$')
FORBIDDEN_WORKFLOW_MARKERS = (
    'SUPABASE_ACCESS_TOKEN',
    'SUPABASE_DB_PASSWORD',
    'db push',
    '--linked',
    'functions deploy',
    'migration repair',
    'db reset',
    'inputs.apply',
)
REQUIRED_WORKFLOW_MARKERS = (
    "'assets/js/**/*.js'",
    "'assets/css/**/*.css'",
    "'**/*.html'",
    'scripts/test_live_social_activation_gate_v25.py',
    'scripts/validate_live_social_activation_gate_v25.py',
)


class _MountedAssetParser(HTMLParser):
    """Extrait les assets référencés et les scripts/styles inline exécutables."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.script_srcs = []
        self.style_hrefs = []
        self.inline_scripts = []
        self.inline_styles = []
        self._inline_script_parts = None
        self._inline_style_parts = None

    def handle_starttag(self, tag, attrs):
        attrs = {str(key).lower(): value for key, value in attrs if key}
        tag = str(tag).lower()
        if tag == 'script':
            src = attrs.get('src')
            if src:
                self.script_srcs.append(src)
                self._inline_script_parts = None
            else:
                self._inline_script_parts = []
        elif tag == 'link':
            href = attrs.get('href')
            if href:
                self.style_hrefs.append(href)
        elif tag == 'style':
            self._inline_style_parts = []

    def handle_data(self, data):
        if self._inline_script_parts is not None:
            self._inline_script_parts.append(data)
        if self._inline_style_parts is not None:
            self._inline_style_parts.append(data)

    def handle_endtag(self, tag):
        tag = str(tag).lower()
        if tag == 'script' and self._inline_script_parts is not None:
            self.inline_scripts.append(''.join(self._inline_script_parts))
            self._inline_script_parts = None
        elif tag == 'style' and self._inline_style_parts is not None:
            self.inline_styles.append(''.join(self._inline_style_parts))
            self._inline_style_parts = None


def parse_ledger_versions(text):
    versions = []
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        match = LEDGER_ROW_RE.fullmatch(line)
        if not match:
            raise ValueError(f'Ledger production invalide ligne {line_number}: {line}')
        versions.append(match.group(1))
    return tuple(versions)


def parse_manifest_collection(source, name):
    tree = ast.parse(source)
    for statement in tree.body:
        value_node = None
        if isinstance(statement, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in statement.targets):
                value_node = statement.value
        elif isinstance(statement, ast.AnnAssign):
            if isinstance(statement.target, ast.Name) and statement.target.id == name:
                value_node = statement.value
        if value_node is not None:
            value = ast.literal_eval(value_node)
            if not isinstance(value, (list, tuple, set, frozenset)):
                raise ValueError(f'{name} doit être une collection littérale.')
            return frozenset(str(item) for item in value)
    raise ValueError(f'Collection manifeste absente: {name}')


def _clean_asset_reference(value):
    return str(value).split('#', 1)[0].split('?', 1)[0].strip()


def _resolve_local_asset(root, base_dir, reference):
    cleaned = _clean_asset_reference(reference)
    lower = cleaned.lower()
    if not cleaned or lower.startswith(('http://', 'https://', '//', 'data:', 'blob:')):
        return None
    candidate = (root / cleaned.lstrip('/')) if cleaned.startswith('/') else (base_dir / cleaned)
    try:
        resolved = candidate.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return resolved


def _walk_local_js_imports(root, entry, html_rel, mounts, visited, chain):
    try:
        entry_rel = entry.relative_to(root).as_posix()
    except ValueError:
        return
    if entry_rel in visited or not entry.is_file() or entry.suffix.lower() != '.js':
        return
    visited.add(entry_rel)
    source = entry.read_text('utf-8', errors='ignore')
    current_chain = chain + (entry_rel,)
    for match in MODULE_IMPORT_RE.finditer(source):
        reference = match.group(1)
        live_match = LIVE_MODULE_NAME_RE.search(_clean_asset_reference(reference))
        if live_match:
            asset = live_match.group(1)
            mounts.add((html_rel, f"{asset} via {' -> '.join(current_chain)}"))
            continue
        target = _resolve_local_asset(root, entry.parent, reference)
        if target is not None and target.suffix.lower() == '.js':
            _walk_local_js_imports(root, target, html_rel, mounts, visited, current_chain)


def _walk_inline_js_imports(root, base_dir, html_rel, source, mounts):
    for match in MODULE_IMPORT_RE.finditer(source):
        reference = match.group(1)
        cleaned = _clean_asset_reference(reference)
        live_match = LIVE_MODULE_NAME_RE.search(cleaned)
        if live_match:
            mounts.add((html_rel, f'{live_match.group(1)} via script inline'))
            continue
        target = _resolve_local_asset(root, base_dir, reference)
        if target is not None and target.suffix.lower() == '.js':
            _walk_local_js_imports(
                root,
                target,
                html_rel,
                mounts,
                set(),
                (f'{html_rel}::<script-inline>',),
            )


def _css_import_references(source):
    source = CSS_COMMENT_RE.sub('', source)
    for match in CSS_IMPORT_RE.finditer(source):
        reference = match.group(1) or match.group(2)
        if reference:
            yield reference


def _walk_local_css_imports(root, entry, html_rel, mounts, visited, chain):
    try:
        entry_rel = entry.relative_to(root).as_posix()
    except ValueError:
        return
    if entry_rel in visited or not entry.is_file() or entry.suffix.lower() != '.css':
        return
    visited.add(entry_rel)
    source = entry.read_text('utf-8', errors='ignore')
    current_chain = chain + (entry_rel,)
    for reference in _css_import_references(source):
        cleaned = _clean_asset_reference(reference)
        live_match = LIVE_STYLE_NAME_RE.search(cleaned)
        if live_match:
            mounts.add((html_rel, f"{live_match.group(1)} via {' -> '.join(current_chain)}"))
            continue
        target = _resolve_local_asset(root, entry.parent, reference)
        if target is not None and target.suffix.lower() == '.css':
            _walk_local_css_imports(root, target, html_rel, mounts, visited, current_chain)


def _walk_inline_css_imports(root, base_dir, html_rel, source, mounts):
    for reference in _css_import_references(source):
        cleaned = _clean_asset_reference(reference)
        live_match = LIVE_STYLE_NAME_RE.search(cleaned)
        if live_match:
            mounts.add((html_rel, f'{live_match.group(1)} via style inline'))
            continue
        target = _resolve_local_asset(root, base_dir, reference)
        if target is not None and target.suffix.lower() == '.css':
            _walk_local_css_imports(
                root,
                target,
                html_rel,
                mounts,
                set(),
                (f'{html_rel}::<style-inline>',),
            )


def find_html_mounts(root):
    root = Path(root).resolve()
    mounts = set()
    for path in sorted(root.rglob('*.html')):
        text = path.read_text('utf-8', errors='ignore')
        html_rel = path.relative_to(root).as_posix()
        parser = _MountedAssetParser()
        parser.feed(text)
        parser.close()

        for reference in parser.script_srcs:
            cleaned = _clean_asset_reference(reference)
            live_match = LIVE_MODULE_NAME_RE.search(cleaned)
            if live_match:
                mounts.add((html_rel, live_match.group(1)))
                continue
            script = _resolve_local_asset(root, path.parent, reference)
            if script is not None:
                _walk_local_js_imports(root, script, html_rel, mounts, set(), ())

        for reference in parser.style_hrefs:
            live_match = LIVE_STYLE_NAME_RE.search(_clean_asset_reference(reference))
            if live_match:
                mounts.add((html_rel, live_match.group(1)))
                continue
            style = _resolve_local_asset(root, path.parent, reference)
            if style is not None:
                _walk_local_css_imports(root, style, html_rel, mounts, set(), ())

        for source in parser.inline_scripts:
            _walk_inline_js_imports(root, path.parent, html_rel, source, mounts)

        for source in parser.inline_styles:
            _walk_inline_css_imports(root, path.parent, html_rel, source, mounts)

    return tuple(sorted(mounts))


def evaluate_activation(*, ledger_versions, production_tables, planned_tables, mounts):
    required_versions = frozenset(version for version, _ in REQUIRED_MIGRATIONS)
    ledger = frozenset(ledger_versions)
    production = frozenset(production_tables)
    planned = frozenset(planned_tables)
    mounts = tuple(mounts)

    missing_versions = tuple(version for version, _ in REQUIRED_MIGRATIONS if version not in ledger)
    missing_production = tuple(sorted(LIVE_TABLES - production))
    still_planned = tuple(sorted(LIVE_TABLES & planned))
    promoted = LIVE_TABLES & production

    ledger_ready = required_versions.issubset(ledger)
    schema_ready = not missing_production and not still_planned
    technical_ready = ledger_ready and schema_ready

    # La convergence technique est une information de préparation, jamais une
    # autorisation de publier. Il n'existe volontairement aucun flag automatisé
    # capable de transformer cette preuve en décision humaine.
    activation_ready = False
    human_activation_required = True
    errors = []

    overlap = production & planned & LIVE_TABLES
    if overlap:
        errors.append(
            'Tables En direct à la fois production et PLANNED_LOCAL_TABLES: '
            + ', '.join(sorted(overlap))
        )

    if promoted and not ledger_ready:
        errors.append(
            'Promotion schéma En direct interdite avant preuve des 8 migrations dans le ledger production; '
            'migrations manquantes: ' + ', '.join(missing_versions)
        )

    if ledger_ready and not schema_ready:
        detail = []
        if missing_production:
            detail.append('non classées EXPECTED_TABLES: ' + ', '.join(missing_production))
        if still_planned:
            detail.append('encore PLANNED_LOCAL_TABLES: ' + ', '.join(still_planned))
        errors.append('Ledger En direct complet mais manifeste production non convergé: ' + '; '.join(detail))

    if mounts:
        rendered = ', '.join(f'{path}:{asset}' for path, asset in mounts)
        errors.append(
            'Montage En direct public interdit: convergence technique insuffisante; '
            'activation humaine explicite et séparée requise: ' + rendered
        )

    if errors:
        status = 'INVALID'
    elif technical_ready:
        status = 'TECHNICALLY_READY_DARK_LAUNCH'
    else:
        status = 'DARK_LAUNCH_BLOCKED_AS_EXPECTED'

    return {
        'status': status,
        'activation_ready': activation_ready,
        'technical_ready': technical_ready,
        'human_activation_required': human_activation_required,
        'activation_policy': PUBLIC_ACTIVATION_POLICY,
        'ledger_ready': ledger_ready,
        'schema_ready': schema_ready,
        'missing_versions': missing_versions,
        'missing_production': missing_production,
        'still_planned': still_planned,
        'mounts': mounts,
        'errors': tuple(errors),
    }


def validate_required_migration_files(errors):
    for version, name in REQUIRED_MIGRATIONS:
        path = MIGRATIONS / f'{version}_{name}.sql'
        if not path.is_file():
            errors.append(f'Migration En direct requise absente: {path.relative_to(ROOT)}')


def validate_workflow_static(errors):
    if not WORKFLOW.is_file():
        errors.append('Workflow du garde activation En direct absent.')
        return
    text = WORKFLOW.read_text('utf-8')
    lower = text.lower()
    for marker in FORBIDDEN_WORKFLOW_MARKERS:
        if marker.lower() in lower:
            errors.append(f'Workflow garde activation contient une primitive/secret interdit: {marker}')
    for marker in REQUIRED_WORKFLOW_MARKERS:
        if marker.lower() not in lower:
            errors.append(f'Workflow garde activation ne couvre pas son contrat: {marker}')


def main():
    structural_errors = []
    validate_required_migration_files(structural_errors)
    validate_workflow_static(structural_errors)

    try:
        ledger_versions = parse_ledger_versions(LEDGER.read_text('utf-8'))
    except (OSError, ValueError) as exc:
        structural_errors.append(str(exc))
        ledger_versions = ()

    try:
        manifest_source = MANIFEST.read_text('utf-8')
        production_tables = parse_manifest_collection(manifest_source, 'EXPECTED_TABLES')
        planned_tables = parse_manifest_collection(manifest_source, 'PLANNED_LOCAL_TABLES')
    except (OSError, SyntaxError, ValueError) as exc:
        structural_errors.append(f'Manifeste production illisible: {exc}')
        production_tables = frozenset()
        planned_tables = frozenset()

    mounts = find_html_mounts(ROOT)
    verdict = evaluate_activation(
        ledger_versions=ledger_versions,
        production_tables=production_tables,
        planned_tables=planned_tables,
        mounts=mounts,
    )
    errors = structural_errors + list(verdict['errors'])

    if errors:
        for error in errors:
            print(f'ERREUR garde activation En direct V25: {error}')
        raise SystemExit(1)

    if verdict['status'] == 'DARK_LAUNCH_BLOCKED_AS_EXPECTED':
        print(
            'OK garde activation En direct V25: dark launch maintenu; '
            f"{len(verdict['missing_versions'])}/8 migrations En direct non prouvées dans le ledger production; "
            'aucun montage direct, transitif JS/CSS ou inline détecté.'
        )
    else:
        print(
            'OK garde activation En direct V25: convergence technique complète; '
            'dark launch maintenu et activation publique toujours soumise à une décision humaine explicite séparée.'
        )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
