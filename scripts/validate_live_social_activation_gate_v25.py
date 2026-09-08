#!/usr/bin/env python3
import ast
import re
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
HTML_SCRIPT_SRC_RE = re.compile(
    r'<script\b[^>]*\bsrc\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)
MODULE_IMPORT_RE = re.compile(
    r'(?:\bfrom\s*|\bimport\s*(?:\(\s*)?)["\']([^"\']+)["\']',
    re.IGNORECASE,
)
LIVE_MODULE_NAME_RE = re.compile(r'(sinjira-live-[A-Za-z0-9_-]+\.js)', re.IGNORECASE)
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
    "'**/*.html'",
    'scripts/test_live_social_activation_gate_v25.py',
    'scripts/validate_live_social_activation_gate_v25.py',
)


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


def find_html_mounts(root):
    root = Path(root).resolve()
    mounts = set()
    for path in sorted(root.rglob('*.html')):
        text = path.read_text('utf-8', errors='ignore')
        html_rel = path.relative_to(root).as_posix()
        for match in SCRIPT_MOUNT_RE.finditer(text):
            mounts.add((html_rel, match.group(1)))
        for match in STYLE_MOUNT_RE.finditer(text):
            mounts.add((html_rel, match.group(1)))

        # Suivre aussi les imports locaux depuis chaque script réellement monté.
        # Cela bloque un contournement du dark launch par import statique/dynamique
        # depuis un runtime déjà présent dans une page, même via plusieurs helpers.
        for match in HTML_SCRIPT_SRC_RE.finditer(text):
            script = _resolve_local_asset(root, path.parent, match.group(1))
            if script is None:
                continue
            _walk_local_js_imports(root, script, html_rel, mounts, set(), ())
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
    activation_ready = ledger_ready and schema_ready
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

    if mounts and not activation_ready:
        rendered = ', '.join(f'{path}:{asset}' for path, asset in mounts)
        errors.append('Montage En direct direct ou transitif interdit sans preuve production complète: ' + rendered)

    if errors:
        status = 'INVALID'
    elif activation_ready and mounts:
        status = 'READY_MOUNTED'
    elif activation_ready:
        status = 'READY_NOT_MOUNTED'
    else:
        status = 'DARK_LAUNCH_BLOCKED_AS_EXPECTED'

    return {
        'status': status,
        'activation_ready': activation_ready,
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
            'aucun montage direct ou transitif détecté.'
        )
    elif verdict['status'] == 'READY_NOT_MOUNTED':
        print('OK garde activation En direct V25: preuve production complète; interface encore non montée.')
    else:
        print('OK garde activation En direct V25: preuve production complète et montage En direct autorisé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
