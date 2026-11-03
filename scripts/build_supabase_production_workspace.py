#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, re, shutil, sys, tomllib

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

    # La consultation NOVA n'est qu'une source candidate. Le workflow de
    # production utilise "supabase functions deploy" sans nom, donc il
    # déploierait accidentellement cette nouvelle route verify_jwt=false si
    # nous copiions son dossier. Refuser fermé tant que la revue SQL, CAPTCHA,
    # anti-abus et l'autorisation d'ouverture ne sont pas terminées.
    staged = out / 'functions' / 'nova-civic-poll'
    if not staged.is_dir() or staged.is_symlink():
        raise SystemExit('Le sondage NOVA en prépublication n a pas une source normale vérifiable.')
    cfg_path = out / 'config.toml'
    cfg_text = cfg_path.read_text('utf-8')
    cfg_pattern = re.compile(
        r'(?ms)^\\[functions\\.nova-civic-poll\\]\\s*\\n'
        r'verify_jwt\\s*=\\s*false\\s*\\Z'
    )
    if len(cfg_pattern.findall(cfg_text)) != 1:
        raise SystemExit('Configuration NOVA inattendue: ne jamais déployer la route publique implicitement.')
    cfg_text = cfg_pattern.sub('', cfg_text)
    cfg_path.write_text(cfg_text, encoding='utf-8')
    if 'nova-civic-poll' in tomllib.loads(cfg_text).get('functions', {}):
        raise SystemExit('La fonction NOVA reste présente dans le config de production.')
    shutil.rmtree(staged)
    candidate_sql = out / 'NOVA_POLL_SCHEMA_PREDEPLOY.sql'
    if not candidate_sql.is_file():
        raise SystemExit('Le SQL NOVA en préparation est manquant: revue requise.')
    candidate_sql.unlink()
    if staged.exists() or candidate_sql.exists():
        raise SystemExit('Le sondage NOVA a fui dans le workspace de production.')
    print('Prépublication NOVA isolée: fonction, configuration JWT et schéma SQL candidat exclus.')

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
