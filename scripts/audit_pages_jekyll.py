#!/usr/bin/env python3
"""Audit fail-closed du build Jekyll Pages. Aucun acces reseau, aucune publication."""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

FORBIDDEN_DIRS = {'.github', 'docs', 'mobile-native', 'scripts', 'supabase', 'tests'}
FORBIDDEN_PATHS = {
    'supabase/config.toml',
    'tests/e2e/test_public_site.py',
    'mobile-native/App.tsx',
    'scripts/validate_site.py',
    '.github/workflows/validate-site.yml',
}
REQUIRED_PUBLIC = {
    'index.html', '404.html', 'CNAME', 'robots.txt', 'sitemap.xml',
    'assets/js/site.js', 'compte/index.html', 'projets/projet-nova/index.html',
    'projets/sinjira/index.html',
}
TECHNICAL_SUFFIXES = {'.md', '.py', '.sql', '.ts', '.tsx', '.toml', '.yml', '.yaml'}
SAFE_ROOT_TEXT = {'robots.txt', 'humans.txt', 'ads.txt'}


def config_values(text: str, key: str) -> list[str]:
    """Lire seulement les tableaux YAML de chaines, sans evaluer du YAML non fiable."""
    lines = text.splitlines()
    result: list[str] = []
    inside = False
    for line in lines:
        if re.match(r'^\w[\w-]*:\s*(?:#.*)?$', line):
            inside = line.split(':', 1)[0] == key
            continue
        if not inside or not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.fullmatch(r'\s+-\s+["\x27]?([^"\x27#]+?)["\x27]?\s*', line)
        if not match:
            raise ValueError(f'Entree non prise en charge dans {key}: {line}')
        result.append(match.group(1).strip())
    return result


def audit_source(root: Path) -> list[str]:
    errors: list[str] = []
    if (root / '.nojekyll').exists():
        errors.append('.nojekyll desactive Jekyll et donc les exclusions')
    cfg = root / '_config.yml'
    if not cfg.is_file():
        return errors + ['_config.yml absent']
    content = cfg.read_text('utf-8')
    try:
        excluded = config_values(content, 'exclude')
        included = config_values(content, 'include')
    except ValueError as exc:
        return errors + [str(exc)]
    if len(excluded) != len(set(excluded)):
        errors.append('Entrées exclude dupliquées')
    for directory in sorted(FORBIDDEN_DIRS):
        if directory not in excluded:
            errors.append(f'Repertoire technique non exclu: {directory}')
    if '.well-known' not in included:
        errors.append('Inclure explicitement .well-known pour les preuves de securite futures')
    for entry in root.iterdir():
        if entry.is_file() and (entry.suffix.lower() in TECHNICAL_SUFFIXES
                               or entry.suffix.lower() == '.txt' and entry.name not in SAFE_ROOT_TEXT):
            if entry.name not in excluded and entry.name != '_config.yml':
                errors.append(f'Source technique racine non exclue: {entry.name}')
    return errors


def audit_output(root: Path, destination: Path) -> list[str]:
    errors: list[str] = []
    if not destination.is_dir():
        return ['Artefact Jekyll absent']
    for public_file in sorted(REQUIRED_PUBLIC):
        if not (destination / public_file).is_file():
            errors.append(f'Page ou asset public disparu: {public_file}')
    for bad in sorted(FORBIDDEN_DIRS | FORBIDDEN_PATHS):
        if (destination / bad).exists() or (destination / bad).is_symlink():
            errors.append(f'Fichier ou repertoire technique publie: {bad}')
    for path in destination.rglob('*'):
        rel = path.relative_to(destination).as_posix()
        if path.is_symlink():
            errors.append(f'Symlink interdit dans le publish: {rel}')
        if path.is_file() and path.suffix.lower() in TECHNICAL_SUFFIXES:
            errors.append(f'Source technique publiee: {rel}')
    if (root / '.well-known/security.txt').is_file() and not (destination / '.well-known/security.txt').is_file():
        errors.append('security.txt source present mais absent du build')
    if (destination / '.nojekyll').exists():
        errors.append('Build Jekyll contient .nojekyll')
    if (destination / '_config.yml').exists():
        errors.append('Configuration Jekyll publiee')
    if (destination / 'CNAME').is_file():
        actual = (destination / 'CNAME').read_text('utf-8').strip()
        expected = (root / 'CNAME').read_text('utf-8').strip()
        if actual != expected:
            errors.append('CNAME different de la source approuvee')
    return errors


def self_test() -> None:
    with tempfile.TemporaryDirectory() as name:
        root = Path(name) / 'source'
        out = Path(name) / 'build'
        root.mkdir()
        out.mkdir()
        (root / '_config.yml').write_text(
            'exclude:\n' + ''.join(f'  - "{value}"\n' for value in sorted(FORBIDDEN_DIRS))
            + 'include:\n  - ".well-known"\n', 'utf-8')
        (root / 'CNAME').write_text('www.example.test\n', 'utf-8')
        for path in REQUIRED_PUBLIC:
            target = out / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('www.example.test\n' if path == 'CNAME' else 'fixture', 'utf-8')
        assert not audit_source(root), audit_source(root)
        assert not audit_output(root, out), audit_output(root, out)
        for bad in FORBIDDEN_PATHS:
            target = out / bad
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('private', 'utf-8')
            assert audit_output(root, out), f'Publication interdite non détectée: {bad}'
            target.unlink()
        (root / '.nojekyll').touch()
        assert audit_source(root), 'Bypass .nojekyll non detecte'
        (root / '.nojekyll').unlink()
        (out / 'index.html').unlink()
        assert audit_output(root, out), 'Page publique manquante non detectee'
        print('OK autotests confinement Pages: fuites techniques, .nojekyll et pages manquantes refuses')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='.')
    parser.add_argument('--built')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    root = Path(args.source).resolve()
    errors = audit_source(root)
    if args.built:
        errors.extend(audit_output(root, Path(args.built).resolve()))
    if errors:
        for error in errors:
            print('ERREUR: ' + error, file=sys.stderr)
        return 1
    print('OK Pages confinement: source Jekyll et contenu public testes sans publication')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
