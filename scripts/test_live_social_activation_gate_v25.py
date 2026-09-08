#!/usr/bin/env python3
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / 'scripts' / 'validate_live_social_activation_gate_v25.py'
spec = importlib.util.spec_from_file_location('live_activation_gate', MODULE_PATH)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

VERSIONS = tuple(version for version, _ in gate.REQUIRED_MIGRATIONS)
PUBLIC = gate.LIVE_PUBLIC_TABLES
PRIVATE = gate.LIVE_PRIVATE_TABLES
ALL = gate.LIVE_TABLES
MOUNT = (('compte/communaute.html', 'sinjira-live-ui-shell-v25.js'),)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def verdict(*, ledger=(), public=(), private=(), planned=ALL, mounts=()):
    return gate.evaluate_activation(
        ledger_versions=ledger,
        production_public=public,
        production_private=private,
        planned=planned,
        mounts=mounts,
    )


# État actuel attendu: dark launch sans erreur, rien de monté.
current = verdict()
check(current['status'] == 'DARK_LAUNCH_BLOCKED_AS_EXPECTED', 'état dark launch attendu')
check(current['activation_ready'] is False, 'activation ne doit pas être prête')
check(len(current['missing_versions']) == 8, 'les 8 migrations doivent être exigées')
check(not current['errors'], 'dark launch non monté doit être valide')

# Un montage prématuré doit échouer.
premature = verdict(mounts=MOUNT)
check(premature['status'] == 'INVALID', 'montage prématuré doit être invalide')
check(any('Montage HTML En direct interdit' in error for error in premature['errors']), 'erreur montage manquante')

# Une promotion partielle du manifeste avant le ledger doit échouer, même sans montage.
partial_public = frozenset({next(iter(PUBLIC))})
partial = verdict(public=partial_public, planned=ALL - partial_public)
check(partial['status'] == 'INVALID', 'promotion partielle doit être invalide')
check(any('Promotion schéma En direct interdite' in error for error in partial['errors']), 'erreur promotion partielle manquante')

# Une table ne peut pas être production et PLANNED à la fois.
overlap = verdict(public=partial_public, planned=ALL)
check(overlap['status'] == 'INVALID', 'chevauchement prod/planned doit être invalide')
check(any('à la fois production et PLANNED' in error for error in overlap['errors']), 'erreur chevauchement manquante')

# Ledger complet sans convergence du manifeste doit échouer.
ledger_only = verdict(ledger=VERSIONS)
check(ledger_only['status'] == 'INVALID', 'ledger seul ne suffit pas')
check(ledger_only['ledger_ready'] is True, 'ledger devrait être prêt')
check(ledger_only['schema_ready'] is False, 'schéma ne devrait pas être prêt')
check(any('manifeste production non convergé' in error for error in ledger_only['errors']), 'erreur manifeste manquante')

# État prêt sans montage: autorisé mais non activé.
ready = verdict(ledger=VERSIONS, public=PUBLIC, private=PRIVATE, planned=frozenset())
check(ready['status'] == 'READY_NOT_MOUNTED', 'preuve complète non montée attendue')
check(ready['activation_ready'] is True, 'activation devrait être prête')
check(not ready['errors'], 'preuve complète ne doit pas produire d’erreur')

# État prêt + montage: le garde autorise alors explicitement le montage.
mounted = verdict(ledger=VERSIONS, public=PUBLIC, private=PRIVATE, planned=frozenset(), mounts=MOUNT)
check(mounted['status'] == 'READY_MOUNTED', 'montage avec preuve complète attendu')
check(not mounted['errors'], 'montage prêt ne doit pas produire d’erreur')

# Le parser ledger doit ignorer commentaires/vides et refuser les lignes libres.
parsed = gate.parse_ledger_versions('# preuve\n20260908120000 sinjira_v25_live_social_foundation\n\n20260908121000 sinjira_v25_live_social_realtime_eligibility\n')
check(parsed == ('20260908120000', '20260908121000'), 'parser ledger incorrect')
try:
    gate.parse_ledger_versions('20260908120000\n')
except ValueError:
    pass
else:
    raise AssertionError('ledger sans nom de migration aurait dû être refusé')

# Les balises HTML sont détectées, une simple mention texte ne l’est pas.
check(gate.SCRIPT_MOUNT_RE.search('<script type="module" src="/assets/js/sinjira-live-ui-shell-v25.js"></script>'), 'script mount non détecté')
check(gate.STYLE_MOUNT_RE.search('<link rel="stylesheet" href="/assets/css/v25-live-share-codes.css">'), 'style mount non détecté')
check(not gate.SCRIPT_MOUNT_RE.search('<p>sinjira-live-ui-shell-v25.js</p>'), 'mention texte ne doit pas être un mount')

print('OK tests garde activation En direct V25: 8 migrations, convergence manifeste et montage HTML fail-closed couverts.')
