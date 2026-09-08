#!/usr/bin/env python3
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / 'scripts' / 'validate_live_social_activation_gate_v25.py'
spec = importlib.util.spec_from_file_location('live_activation_gate', MODULE_PATH)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

VERSIONS = tuple(version for version, _ in gate.REQUIRED_MIGRATIONS)
LIVE = gate.LIVE_TABLES
MOUNT = (('compte/communaute.html', 'sinjira-live-ui-shell-v25.js'),)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def verdict(*, ledger=(), production=(), planned=LIVE, mounts=()):
    return gate.evaluate_activation(
        ledger_versions=ledger,
        production_tables=production,
        planned_tables=planned,
        mounts=mounts,
    )


current = verdict()
check(current['status'] == 'DARK_LAUNCH_BLOCKED_AS_EXPECTED', 'état dark launch attendu')
check(current['activation_ready'] is False, 'activation ne doit pas être prête')
check(len(current['missing_versions']) == 8, 'les 8 migrations doivent être exigées')
check(set(current['missing_production']) == set(LIVE), 'les 5 tables En direct doivent rester hors production')
check(not current['errors'], 'dark launch non monté doit être valide')

premature = verdict(mounts=MOUNT)
check(premature['status'] == 'INVALID', 'montage prématuré doit être invalide')
check(any('Montage En direct direct ou transitif interdit' in error for error in premature['errors']), 'erreur montage manquante')

one_table = frozenset({sorted(LIVE)[0]})
partial = verdict(production=one_table, planned=LIVE - one_table)
check(partial['status'] == 'INVALID', 'promotion partielle doit être invalide')
check(any('Promotion schéma En direct interdite' in error for error in partial['errors']), 'erreur promotion partielle manquante')

overlap = verdict(production=one_table, planned=LIVE)
check(overlap['status'] == 'INVALID', 'chevauchement prod/planned doit être invalide')
check(any('à la fois production et PLANNED_LOCAL_TABLES' in error for error in overlap['errors']), 'erreur chevauchement manquante')

ledger_only = verdict(ledger=VERSIONS)
check(ledger_only['status'] == 'INVALID', 'ledger seul ne suffit pas')
check(ledger_only['ledger_ready'] is True, 'ledger devrait être prêt')
check(ledger_only['schema_ready'] is False, 'schéma ne devrait pas être prêt')
check(any('manifeste production non convergé' in error for error in ledger_only['errors']), 'erreur manifeste manquante')

ready = verdict(ledger=VERSIONS, production=LIVE, planned=frozenset())
check(ready['status'] == 'READY_NOT_MOUNTED', 'preuve complète non montée attendue')
check(ready['activation_ready'] is True, 'activation devrait être prête')
check(not ready['errors'], 'preuve complète ne doit pas produire d’erreur')

mounted = verdict(ledger=VERSIONS, production=LIVE, planned=frozenset(), mounts=MOUNT)
check(mounted['status'] == 'READY_MOUNTED', 'montage avec preuve complète attendu')
check(not mounted['errors'], 'montage prêt ne doit pas produire d’erreur')

manifest_sample = "EXPECTED_TABLES={'social_live_rooms','profiles'}\nPLANNED_LOCAL_TABLES={'foo'}\n"
check(gate.parse_manifest_collection(manifest_sample, 'EXPECTED_TABLES') == frozenset({'social_live_rooms', 'profiles'}), 'parser EXPECTED_TABLES incorrect')
check(gate.parse_manifest_collection(manifest_sample, 'PLANNED_LOCAL_TABLES') == frozenset({'foo'}), 'parser PLANNED_LOCAL_TABLES incorrect')

parsed = gate.parse_ledger_versions('# preuve\n20260908120000 sinjira_v25_live_social_foundation\n\n20260908121000 sinjira_v25_live_social_realtime_eligibility\n')
check(parsed == ('20260908120000', '20260908121000'), 'parser ledger incorrect')
try:
    gate.parse_ledger_versions('20260908120000\n')
except ValueError:
    pass
else:
    raise AssertionError('ledger sans nom de migration aurait dû être refusé')

check(gate.SCRIPT_MOUNT_RE.search('<script type="module" src="/assets/js/sinjira-live-ui-shell-v25.js"></script>'), 'script shell mount non détecté')
check(gate.SCRIPT_MOUNT_RE.search('<script type="module" src="/assets/js/sinjira-live-invites-ui-v25.js"></script>'), 'script invitations mount non détecté')
check(gate.SCRIPT_MOUNT_RE.search('<script type="module" src="/assets/js/sinjira-live-community-bridge-v25.js"></script>'), 'script pont Communauté mount non détecté')
check(gate.STYLE_MOUNT_RE.search('<link rel="stylesheet" href="/assets/css/v25-live-share-codes.css">'), 'style codes mount non détecté')
check(gate.STYLE_MOUNT_RE.search('<link rel="stylesheet" href="/assets/css/v25-live-invites.css">'), 'style invitations mount non détecté')
check(not gate.SCRIPT_MOUNT_RE.search('<p>sinjira-live-invites-ui-v25.js</p>'), 'mention texte invitations ne doit pas être un mount')
check(not gate.SCRIPT_MOUNT_RE.search('<p>sinjira-live-community-bridge-v25.js</p>'), 'mention texte pont Communauté ne doit pas être un mount')

# Le garde doit suivre un graphe d’import local depuis un script réellement monté.
with TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / 'compte').mkdir()
    (root / 'assets' / 'js').mkdir(parents=True)
    (root / 'compte' / 'communaute.html').write_text(
        '<script type="module" src="../assets/js/community.js?v=1"></script>',
        encoding='utf-8',
    )
    (root / 'assets' / 'js' / 'community.js').write_text(
        "import './helper.js';\n",
        encoding='utf-8',
    )
    (root / 'assets' / 'js' / 'helper.js').write_text(
        "export async function open(){ return import('./sinjira-live-community-bridge-v25.js'); }\n",
        encoding='utf-8',
    )
    mounts = gate.find_html_mounts(root)
    check(
        any(
            path == 'compte/communaute.html'
            and 'sinjira-live-community-bridge-v25.js' in asset
            and 'assets/js/community.js -> assets/js/helper.js' in asset
            for path, asset in mounts
        ),
        'import En direct transitif depuis un runtime monté non détecté',
    )

# Une simple chaîne sans syntaxe import ne doit pas être considérée comme activation.
with TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / 'compte').mkdir()
    (root / 'assets' / 'js').mkdir(parents=True)
    (root / 'compte' / 'communaute.html').write_text(
        '<script type="module" src="../assets/js/community.js"></script>',
        encoding='utf-8',
    )
    (root / 'assets' / 'js' / 'community.js').write_text(
        "const roadmap='sinjira-live-community-bridge-v25.js';\n",
        encoding='utf-8',
    )
    check(not gate.find_html_mounts(root), 'simple mention JS ne doit pas être un montage transitif')

print('OK tests garde activation En direct V25: 8 migrations, 5 tables, convergence manifeste, montages directs et imports transitifs depuis les runtimes HTML fail-closed couverts.')
