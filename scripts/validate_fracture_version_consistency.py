#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase' / 'migrations'
ENGINE_VERSION = '24.4.6'


def read(path: Path) -> str:
    return path.read_text('utf-8', errors='ignore')


def latest_function(files: list[Path], name: str) -> tuple[Path | None, str]:
    rx = re.compile(
        rf'create\s+(?:or\s+replace\s+)?function\s+(?:public\.)?{re.escape(name)}\s*\([^)]*\).*?\$\$.*?\$\$\s*;',
        re.I | re.S,
    )
    for path in reversed(files):
        matches = list(rx.finditer(read(path)))
        if matches:
            return path, matches[-1].group(0)
    return None, ''


def compact(text: str) -> str:
    return re.sub(r'\s+', '', text.lower())


def main() -> int:
    errors: list[str] = []
    files = sorted(MIG.glob('*.sql'))
    sql = '\n'.join(read(path) for path in files)
    normalized = compact(sql)

    start_path, start = latest_function(files, 'fracture_engine_start')
    state_path, state = latest_function(files, 'fracture_engine_get_state')
    health_path, health = latest_function(files, 'fracture_engine_health')

    if not start_path:
        errors.append('fracture_engine_start introuvable.')
    else:
        start_compact = compact(start)
        expected = f"setengine_version='{ENGINE_VERSION}',engine_status='playing'"
        if expected not in start_compact:
            errors.append(
                f'{start_path.name}: fracture_engine_start ne persiste pas engine_version={ENGINE_VERSION} au démarrage.'
            )
        for stale in ("engine_version='24.4.0'", "engine_version='24.4.1'"):
            if stale in start_compact:
                errors.append(f'{start_path.name}: version historique encore active dans fracture_engine_start: {stale}')

    if not state_path:
        errors.append('fracture_engine_get_state introuvable.')
    else:
        state_compact = compact(state)
        for marker in ('canonical_engine_version', "'{engine_version}'", 'p.engine_version'):
            if marker not in state_compact:
                errors.append(f'{state_path.name}: état Fracture sans canonisation de version: {marker}')
        if f"coalesce(canonical_engine_version,'{ENGINE_VERSION}')" not in state_compact:
            errors.append(f'{state_path.name}: repli de version différent de {ENGINE_VERSION}.')

    if not health_path:
        errors.append('fracture_engine_health introuvable.')
    else:
        health_compact = compact(health)
        for marker in (
            f"'engine_version','{ENGINE_VERSION}'",
            "'version_consistent'",
            "'active_version_mismatches'",
            "engine_statusin('lobby','playing','final_vote')",
        ):
            if marker not in health_compact:
                errors.append(f'{health_path.name}: diagnostic de cohérence de version incomplet: {marker}')

    if f"altercolumnengine_versionsetdefault'{ENGINE_VERSION}'" not in normalized:
        errors.append(f'La valeur par défaut de fracture_parties.engine_version n’est pas {ENGINE_VERSION}.')
    if "engine_versionisdistinctfrom'24.4.6'" not in normalized:
        errors.append('Aucune réparation explicite des parties actives ayant une version divergente.')

    if errors:
        print(f'ECHEC cohérence Fracture: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print(
        f'OK cohérence Fracture: démarrage, état public, valeur par défaut, réparation active et health sont verrouillés sur le moteur {ENGINE_VERSION}.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
