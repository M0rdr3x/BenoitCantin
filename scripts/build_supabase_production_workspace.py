#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, re, shutil, sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SUPABASE = ROOT / 'supabase'
LEDGER = SOURCE_SUPABASE / 'production-migration-ledger.txt'
REVIEWED_BATCH = SOURCE_SUPABASE / 'production-reviewed-migration-batch.txt'
MIG_RE = re.compile(r'^(\d{14})_(.+)\.sql$')
BATCH_RE = re.compile(r'^(\d{14})\s+([a-zA-Z0-9_]+)\s+([0-9a-f]{40})$')


def read_ledger():
    rows = []
    for lineno, line in enumerate(LEDGER.read_text('utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or not re.fullmatch(r'\d{14}', parts[0]):
            raise SystemExit(f'Ledger invalide ligne {lineno}: {line}')
        rows.append((parts[0], parts[1].strip()))
    versions = [v for v, _ in rows]
    if versions != sorted(versions):
        raise SystemExit('Ledger production non trié.')
    if len(versions) != len(set(versions)):
        raise SystemExit('Ledger production avec version dupliquée.')
    if not rows:
        raise SystemExit('Ledger production vide.')
    return rows


def git_blob_sha1(path):
    data = path.read_bytes()
    header = f'blob {len(data)}\0'.encode('ascii')
    return hashlib.sha1(header + data).hexdigest()


def read_reviewed_batch(cutoff):
    if not REVIEWED_BATCH.is_file():
        raise SystemExit('Lot de migrations production revu absent.')

    rows = []
    for lineno, raw in enumerate(REVIEWED_BATCH.read_text('utf-8').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        match = BATCH_RE.fullmatch(line)
        if not match:
            raise SystemExit(f'Lot de migrations production invalide ligne {lineno}: {line}')
        version, name, blob_sha = match.groups()
        rows.append((version, name, blob_sha))

    versions = [version for version, _, _ in rows]
    if versions != sorted(versions):
        raise SystemExit('Lot de migrations production non trié.')
    if len(versions) != len(set(versions)):
        raise SystemExit('Lot de migrations production avec version dupliquée.')
    if any(version <= cutoff for version in versions):
        raise SystemExit('Le lot revu contient une migration déjà couverte par le ledger production.')
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    out = Path(args.output).resolve()
    if out == SOURCE_SUPABASE.resolve():
        raise SystemExit('Refus de modifier supabase/ source.')

    rows = read_ledger()
    cutoff = rows[-1][0]
    reviewed = read_reviewed_batch(cutoff)
    reviewed_names = [f'{version}_{name}.sql' for version, name, _ in reviewed]

    local_future = []
    for src in sorted((SOURCE_SUPABASE / 'migrations').glob('*.sql')):
        match = MIG_RE.fullmatch(src.name)
        if not match:
            raise SystemExit(f'Nom de migration invalide: {src.name}')
        if match.group(1) > cutoff:
            local_future.append(src.name)

    if local_future != reviewed_names:
        unexpected = sorted(set(local_future) - set(reviewed_names))
        missing = sorted(set(reviewed_names) - set(local_future))
        details = []
        if unexpected:
            details.append('non revue(s): ' + ', '.join(unexpected))
        if missing:
            details.append('attendue(s) absente(s): ' + ', '.join(missing))
        raise SystemExit(
            'Le lot de migrations production revu ne correspond pas exactement aux migrations futures locales'
            + (': ' + '; '.join(details) if details else '.')
        )

    for version, name, expected_blob_sha in reviewed:
        src = SOURCE_SUPABASE / 'migrations' / f'{version}_{name}.sql'
        actual_blob_sha = git_blob_sha1(src)
        if actual_blob_sha != expected_blob_sha:
            raise SystemExit(
                f'Contenu de migration modifié depuis la revue: {src.name} '
                f'(attendu {expected_blob_sha}, obtenu {actual_blob_sha}).'
            )

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SOURCE_SUPABASE, out, ignore=shutil.ignore_patterns('migrations', '.temp'))
    migout = out / 'migrations'
    migout.mkdir(parents=True, exist_ok=True)

    # Les versions déjà présentes en production deviennent des marqueurs uniquement
    # dans l'espace de déploiement lié. Le SQL de reconstruction reste intact dans le dépôt.
    for version, name in rows:
        (migout / f'{version}_{name}.sql').write_text(
            f'-- Ledger production SINJIRA™ : migration {version}_{name} déjà appliquée.\n'
            '-- Marqueur de déploiement lié uniquement; ne contient volontairement aucun DDL.\n',
            encoding='utf-8',
        )

    future = []
    for version, name, _ in reviewed:
        src = SOURCE_SUPABASE / 'migrations' / f'{version}_{name}.sql'
        dst = migout / src.name
        if dst.exists():
            raise SystemExit(f'Collision future: {src.name}')
        shutil.copy2(src, dst)
        future.append(src.name)

    print(
        f'Workspace Supabase production construit: {len(rows)} version(s) déjà appliquée(s), '
        f'{len(future)} migration(s) future(s) explicitement revue(s).'
    )
    if future:
        print('Migrations futures revues:')
        for name in future:
            print('- ' + name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
