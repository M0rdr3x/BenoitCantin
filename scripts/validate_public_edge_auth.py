#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'supabase' / 'config.toml'

# Toute fonction de cette liste est publique volontairement et doit posséder
# son propre mécanisme de sécurité applicatif. Ajouter une nouvelle exception
# exige donc une modification explicite et révisable de ce fichier.
INTENTIONAL_PUBLIC_FUNCTIONS = {
    'send-game-report': 'génération/téléchargement public borné; envoi externe désactivé par défaut',
    'get-document-url': 'documents publics approuvés; authentification utilisateur optionnelle',
    'life-story-delivery': 'accès posthume par jeton opaque dédié, sans Compte SINJIRA requis',
}

# Permission JWT préparée dans le dépôt, mais strictement interdite dans
# l'artefact de production tant que la revue anti-abus/SQL n'est pas terminée.
# Ne pas mélanger cette liste à INTENTIONAL_PUBLIC_FUNCTIONS.
STAGED_PUBLIC_FUNCTIONS = {
    'nova-civic-poll': 'prépublication fermée: CAPTCHA/HMAC, sans source dans le workspace production',
}


def main() -> int:
    if not CONFIG.exists():
        print('ECHEC: supabase/config.toml est absent.')
        return 1

    with CONFIG.open('rb') as handle:
        config = tomllib.load(handle)

    functions = config.get('functions', {})
    if not isinstance(functions, dict):
        print('ECHEC: bloc [functions.*] invalide dans supabase/config.toml.')
        return 1

    errors: list[str] = []
    explicit_public: set[str] = set()

    for name, settings in functions.items():
        if not isinstance(settings, dict):
            errors.append(f'{name}: configuration de fonction invalide')
            continue

        verify_jwt = settings.get('verify_jwt')
        if verify_jwt is False:
            explicit_public.add(name)
        elif verify_jwt is not None and not isinstance(verify_jwt, bool):
            errors.append(f'{name}: verify_jwt doit être un booléen TOML')

    reviewed = set(INTENTIONAL_PUBLIC_FUNCTIONS) | set(STAGED_PUBLIC_FUNCTIONS)
    unexpected = explicit_public - reviewed
    missing = reviewed - explicit_public

    for name in sorted(unexpected):
        errors.append(
            f'{name}: nouvelle Edge Function publique non autorisée; '
            'documenter son mécanisme de sécurité avant d’ajouter une exception'
        )

    for name in sorted(missing):
        errors.append(
            f'{name}: le contrat public attendu a changé; '
            'valider explicitement l’impact fonctionnel avant de modifier cette exception'
        )

    for name in sorted(explicit_public):
        function_entry = ROOT / 'supabase' / 'functions' / name / 'index.ts'
        if not function_entry.exists():
            errors.append(f'{name}: fonction publique configurée mais index.ts absent')

    # La liste des exceptions de production ne doit jamais intégrer NOVA.
    # Le builder revu supprime physiquement la source et le bloc TOML avant
    # tout "supabase functions deploy" global.
    builder = ROOT / 'scripts' / 'build_supabase_production_workspace.py'
    if STAGED_PUBLIC_FUNCTIONS:
        source = builder.read_text('utf-8') if builder.is_file() else ''
        for staged in STAGED_PUBLIC_FUNCTIONS:
            if staged in INTENTIONAL_PUBLIC_FUNCTIONS:
                errors.append(f'{staged}: prépublication confondue avec fonction déjà autorisée.')
            if (f"'functions' / '{staged}'" not in source
                    or "shutil.rmtree(staged)" not in source
                    or "cfg_pattern.sub('', cfg_text)" not in source):
                errors.append(f'{staged}: exclusion physique du workspace de production non prouvée.')

    if errors:
        print(f'ECHEC: {len(errors)} problème(s) dans le contrat des Edge Functions publiques.')
        for error in errors:
            print(f'- {error}')
        return 1

    print('OK: JWT public vérifié : fonctions canoniques et prépublication exclue du déploiement.')
    for name in sorted(INTENTIONAL_PUBLIC_FUNCTIONS):
        print(f'- {name}: {INTENTIONAL_PUBLIC_FUNCTIONS[name]}')
    for name in sorted(STAGED_PUBLIC_FUNCTIONS):
        print(f'- {name}: {STAGED_PUBLIC_FUNCTIONS[name]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
