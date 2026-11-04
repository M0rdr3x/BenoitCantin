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




def reject_source_symlinks(source: Path) -> None:
    """Ne jamais suivre un lien du dépôt lors d'une copie vers la production."""
    if source.is_symlink() or not source.is_dir():
        raise SystemExit('Arborescence Supabase source absente ou symbolique.')
    for candidate in source.rglob('*'):
        if candidate.is_symlink():
            raise SystemExit(f'Lien symbolique interdit dans Supabase : {candidate.relative_to(source)}')


def quarantine_unreviewed_edge_deploys(workspace: Path) -> tuple[str, ...]:
    """Retirer les routes non autorisées du déploiement générique.

    La suppression est limitée à la COPIE temporaire des fonctions. Les
    fonctions déjà déployées dans Supabase restent actives et inchangées.
    Toute dérive du contrat source/configuration fait échouer le prévol.
    """
    import tomllib

    config_path = workspace / 'config.toml'
    if config_path.is_symlink() or not config_path.is_file():
        raise SystemExit('Configuration Supabase du workspace absente ou symbolique.')
    original = config_path.read_text('utf-8')
    parsed = tomllib.loads(original)
    functions_config = parsed.get('functions')
    if not isinstance(functions_config, dict):
        raise SystemExit('Inventaire Edge Functions invalide.')

    quarantine = (
        ('security-context', True),
        ('nova-civic-poll', False),
    )
    config = original
    for slug, jwt_required in quarantine:
        folder = workspace / 'functions' / slug
        entry = folder / 'index.ts'
        if folder.is_symlink() or not folder.is_dir() or entry.is_symlink() or not entry.is_file():
            raise SystemExit(f'Fonction sensible incomplète ou symbolique : {slug}.')
        # Valeurs exactes et aucun autre paramètre susceptible de modifier
        # l'authentification ou le comportement au prochain déploiement.
        if functions_config.get(slug) != {'verify_jwt': jwt_required}:
            raise SystemExit(f'Configuration de sécurité inattendue : {slug}.')
        expected_line = f'[functions.{slug}]\nverify_jwt = {str(jwt_required).lower()}\n'
        if config.count(expected_line) != 1:
            raise SystemExit(f'Bloc TOML inattendu : {slug}.')
        source = entry.read_text('utf-8')
        if slug == 'security-context':
            # Production vérifiée en lecture seule : cette RPC candidate
            # n'existe pas encore; éviter de remplacer la fonction active.
            if 'service_security_evaluate_context_session' not in source:
                raise SystemExit('Contrat security-context modifié : revue indépendante obligatoire.')
        else:
            # Une fonction publique utilisant service_role ne doit jamais
            # devenir déployable par la synchronisation générique implicite.
            expected = ('Deno.env.get("NOVA_POLL_ENABLED") === "true"', 'if(!await confirmCaptcha(payload.captchaToken))', 'SUPABASE_SERVICE_ROLE_KEY')
            if any(marker not in source for marker in expected):
                raise SystemExit('Contrat public NOVA modifié : revue indépendante obligatoire.')
        config = config.replace(expected_line, '', 1)

    candidate = workspace / 'NOVA_POLL_SCHEMA_PREDEPLOY.sql'
    if candidate.is_symlink() or not candidate.is_file():
        raise SystemExit('SQL candidat NOVA absent ou symbolique : arrêt du déploiement.')
    # S'assurer que les deux fonctions ont disparu de l'inventaire TOML
    # avant de supprimer leur copie et jamais une source du dépôt.
    retained = tomllib.loads(config).get('functions', {})
    if set(retained) != set(functions_config) - {slug for slug, _ in quarantine}:
        raise SystemExit('Contrat de quarantaine TOML non respecté.')
    for slug, _ in quarantine:
        shutil.rmtree(workspace / 'functions' / slug)
    candidate.unlink()
    config_path.write_text(config, encoding='utf-8')
    for slug, _ in quarantine:
        if (workspace / 'functions' / slug).exists() or slug in tomllib.loads(config_path.read_text('utf-8')).get('functions', {}):
            raise SystemExit(f'Fonction non approuvée encore déployable : {slug}.')
    if candidate.exists():
        raise SystemExit('SQL candidat NOVA encore présent dans le workspace.')
    return tuple(slug for slug, _ in quarantine)


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

    reject_source_symlinks(SOURCE_SUPABASE)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SOURCE_SUPABASE, out, ignore=shutil.ignore_patterns('migrations', '.temp'))
    quarantined = quarantine_unreviewed_edge_deploys(out)
    print('Edge Functions isolées du déploiement générique : ' + ', '.join(quarantined))
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
