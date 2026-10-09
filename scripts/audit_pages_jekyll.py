#!/usr/bin/env python3
"""Audit fail-closed du build Jekyll Pages. Aucun acces reseau, aucune publication."""
from __future__ import annotations

import argparse
import hashlib
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
# Jekyll ne doit pas transformer silencieusement les pages HTML et assets statiques.
BYTE_IDENTICAL_FILES = {
    'index.html', '404.html', 'CNAME', 'robots.txt', 'sitemap.xml',
    'assets/js/site.js', 'compte/index.html',
    'projets/sinjira/index.html', 'projets/projet-nova/index.html',
}
# Gel des 30 documents déjà servis dans official/ : toute addition exige une revue explicite.
PUBLIC_REFERENCE_FILES = frozenset({
    "projets/projet-nova/official/reference/architecture-numerique-interoperabilite-reversibilite.md",
    "projets/projet-nova/official/reference/corpus.md",
    "projets/projet-nova/official/reference/cybersecurite-resilience-continuite.md",
    "projets/projet-nova/official/reference/finances.md",
    "projets/projet-nova/official/reference/identite-numerique-vie-privee.md",
    "projets/projet-nova/official/reference/programme.md",
    "projets/projet-nova/official/reference/statuts.md",
    "projets/projet-nova/official/versions/V316/README.md",
    "projets/projet-nova/official/versions/V316/V316_FINAL_STATE_SUMMARY.md",
    "projets/projet-nova/official/versions/V316/V316_IDENTITE_NUMERIQUE_VIE_PRIVEE_ACCES_AUDIT.md",
    "projets/projet-nova/official/versions/V317/README.md",
    "projets/projet-nova/official/versions/V317/V317_CYBERSECURITE_RESILIENCE_CONTINUITE.md",
    "projets/projet-nova/official/versions/V317/V317_FINAL_STATE_SUMMARY.md",
    "projets/projet-nova/official/versions/V318/README.md",
    "projets/projet-nova/official/versions/V318/V318_ARCHITECTURE_NUMERIQUE_INTEROPERABILITE_REVERSIBILITE.md",
    "projets/projet-nova/official/versions/V318/V318_FINAL_STATE_SUMMARY.md",
    "projets/projet-nova/official/versions/V319/README.md",
    "projets/projet-nova/official/versions/V319/V319_FINAL_STATE_SUMMARY.md",
    "projets/projet-nova/official/versions/V319/V319_SOUVERAINETE_DONNEES_ARCHIVES_REPRODUCTIBILITE.md",
    "projets/projet-nova/official/versions/V320/README.md",
    "projets/projet-nova/official/versions/V320/V320_FINAL_STATE_SUMMARY.md",
    "projets/projet-nova/official/versions/V320/V320_SEPARATION_DEPENSES_PUBLIQUES_SECTEUR_PRIVE.md",
    "projets/projet-nova/official/versions/V320/V320_VALIDATION_REPORT.md",
    "projets/projet-nova/official/versions/V321/README.md",
    "projets/projet-nova/official/versions/V321/V321_AUTONOMIE_OPERATIONNELLE_PUBLIQUE_CAPACITES_CRITIQUES_CONTINUITE.md",
    "projets/projet-nova/official/versions/V321/V321_FINAL_STATE_SUMMARY.md",
    "projets/projet-nova/official/versions/V321/V321_VALIDATION_REPORT.md",
    "projets/projet-nova/official/versions/V322/README.md",
    "projets/projet-nova/official/versions/V322/V322_FINAL_STATE_SUMMARY.md",
    "projets/projet-nova/official/versions/V322/V322_VALIDATION_REPORT.md",
})

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
    for group in ('assets/icons', 'projets/projet-nova'):
        directory = root / group
        if directory.is_dir():
            for item in directory.iterdir():
                if item.is_file() and item.suffix.lower() in TECHNICAL_SUFFIXES:
                    if item.relative_to(root).as_posix() not in excluded:
                        errors.append(f'Document technique non exclu: {item.relative_to(root).as_posix()}')
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
    for public_file in sorted(BYTE_IDENTICAL_FILES):
        original, built = root / public_file, destination / public_file
        if original.is_file() and built.is_file():
            if hashlib.sha256(original.read_bytes()).digest() != hashlib.sha256(built.read_bytes()).digest():
                errors.append(f'Page/asset modifie par Jekyll: {public_file}')
    for bad in sorted(FORBIDDEN_DIRS | FORBIDDEN_PATHS):
        if (destination / bad).exists() or (destination / bad).is_symlink():
            errors.append(f'Fichier ou repertoire technique publie: {bad}')
    for path in destination.rglob('*'):
        rel = path.relative_to(destination).as_posix()
        if path.is_symlink():
            errors.append(f'Symlink interdit dans le publish: {rel}')
        if path.is_file() and path.suffix.lower() in TECHNICAL_SUFFIXES:
            if not (path.suffix.lower() == '.md' and rel in PUBLIC_REFERENCE_FILES):
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
        (root / 'index.html').write_text('fixture', 'utf-8')
        assert not audit_source(root), audit_source(root)
        assert not audit_output(root, out), audit_output(root, out)
        for bad in FORBIDDEN_PATHS:
            target = out / bad
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('private', 'utf-8')
            assert audit_output(root, out), f'Publication interdite non détectée: {bad}'
            target.unlink()
        (out / 'index.html').write_text('mutation', 'utf-8')
        assert audit_output(root, out), 'Transformation HTML non detectee'
        (out / 'index.html').write_text('fixture', 'utf-8')
        extra = out / 'projets/projet-nova/official/versions/non-approuve.md'
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text('nouveau', 'utf-8')
        assert audit_output(root, out), 'Nouveau document officiel non approuve'
        extra.unlink()
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
