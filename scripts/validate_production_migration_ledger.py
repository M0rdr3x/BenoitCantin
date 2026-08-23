#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, tempfile, sys

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'supabase' / 'production-migration-ledger.txt'
MIG = ROOT / 'supabase' / 'migrations'
BUILDER = ROOT / 'scripts' / 'build_supabase_production_workspace.py'
ROW_RE = re.compile(r'^(\d{14})\s+([a-zA-Z0-9_]+)$')
FILE_RE = re.compile(r'^(\d{14})_(.+)\.sql$')
EXPECTED_COUNT = 152
EXPECTED_FIRST = '20260809050252'
EXPECTED_LAST = '20260823033756'


def ledger_rows():
    out = []
    for i, raw in enumerate(LEDGER.read_text('utf-8').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        m = ROW_RE.fullmatch(line)
        if not m:
            raise SystemExit(f'Ledger invalide ligne {i}: {line}')
        out.append((m.group(1), m.group(2)))
    return out


def main():
    errors = []
    rows = ledger_rows()
    versions = [v for v, _ in rows]
    if len(rows) != EXPECTED_COUNT: errors.append(f'Ledger: {len(rows)} versions au lieu de {EXPECTED_COUNT}.')
    if versions != sorted(versions): errors.append('Ledger non trié.')
    if len(versions) != len(set(versions)): errors.append('Versions dupliquées dans le ledger.')
    if not versions or versions[0] != EXPECTED_FIRST: errors.append('Première version production inattendue.')
    if not versions or versions[-1] != EXPECTED_LAST: errors.append('Dernière version production inattendue.')

    local = []
    for path in sorted(MIG.glob('*.sql')):
        m = FILE_RE.fullmatch(path.name)
        if not m:
            errors.append(f'Nom de migration invalide: {path.name}')
            continue
        local.append((m.group(1), path.name))
    local_versions = [v for v, _ in local]
    if len(local_versions) != len(set(local_versions)): errors.append('Deux fichiers locaux partagent le même timestamp.')

    future = [(v, name) for v, name in local if v > EXPECTED_LAST]
    with tempfile.TemporaryDirectory(prefix='sinjira-ledger-') as td:
        out = Path(td) / 'supabase'
        proc = subprocess.run([sys.executable, str(BUILDER), '--output', str(out)], cwd=ROOT, capture_output=True, text=True)
        if proc.returncode:
            errors.append('Builder workspace en échec: ' + (proc.stderr or proc.stdout).strip())
        else:
            generated = []
            for path in sorted((out / 'migrations').glob('*.sql')):
                m = FILE_RE.fullmatch(path.name)
                if not m:
                    errors.append(f'Fichier workspace invalide: {path.name}')
                    continue
                generated.append((m.group(1), path.name))
            if [v for v, _ in generated] != versions + [v for v, _ in future]: errors.append('Le workspace lié ne reproduit pas exactement le ledger + migrations futures.')
            for _, name in generated[:len(rows)]:
                text = (out / 'migrations' / name).read_text('utf-8', errors='ignore')
                if 'Marqueur de déploiement lié uniquement' not in text: errors.append(f'Version déjà appliquée contient du DDL dans le workspace: {name}')
            for _, name in future:
                if not (out / 'migrations' / name).exists(): errors.append(f'Migration future absente du workspace: {name}')

    if errors:
        print(f'ECHEC ledger production: {len(errors)} problème(s).')
        for err in errors: print('- ' + err)
        return 1
    print(f'OK ledger production: {EXPECTED_COUNT} versions distantes protégées; {len(future)} migration(s) future(s) transmissible(s).')
    return 0

if __name__ == '__main__': raise SystemExit(main())
