#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / 'scripts' / 'smoke_sensitive_aal2_local.py'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-sensitive-aal2-v25.yml'
CONFIG = ROOT / 'supabase' / 'config.toml'


def fail(message: str) -> None:
    print(f'ECHEC smoke AAL2 V25: {message}', file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> int:
    for path in (SMOKE, WORKFLOW, CONFIG):
        require(path.is_file(), f'fichier manquant: {path.relative_to(ROOT)}')
    smoke = SMOKE.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')
    config = CONFIG.read_text('utf-8')

    require('/auth/v1/signup' in smoke, 'signup Auth local absent')
    require('/auth/v1/token?grant_type=password' in smoke, 'reconnexion AAL1 absente')
    require('/auth/v1/factors' in smoke, 'enrôlement MFA absent')
    require('/challenge' in smoke and '/verify' in smoke, 'challenge/verify TOTP absents')
    require('hashlib.sha1' in smoke and 'hmac.new' in smoke, 'génération TOTP locale bornée absente')
    require('get("aal") == "aal2"' in smoke, 'preuve du claim JWT aal2 absente')
    require('MFA_SETUP_REQUIRED' in smoke, 'preuve sans facteur absente')
    require('MFA_REQUIRED' in smoke, 'preuve session aal1 après enrôlement absente')
    require('/functions/v1/{function_name}' in smoke, 'appel Edge local absent')
    require('"personal-ai"' in smoke and '"conscience-vault"' in smoke, 'les deux zones sensibles doivent être testées')
    require('SECURITY_CHALLENGE_REQUIRED' in smoke, 'le moteur de risque après AAL2 doit rester accepté comme barrière supplémentaire')
    require('MFA_STATE_UNAVAILABLE' in smoke, 'le smoke doit échouer fermé si l’état MFA devient indisponible')
    require('127.0.0.1' in smoke and 'localhost' in smoke, 'le smoke doit refuser une cible non locale')
    require('gpvivleexywljowcqkru' not in smoke, 'le projet production ne doit jamais être ciblé')

    privileged_markers = (
        'SUPABASE_SERVICE_ROLE_KEY', 'SERVICE_ROLE_KEY', 'SUPABASE_ACCESS_TOKEN',
        'sb_secret_', '/auth/v1/admin/',
    )
    for marker in privileged_markers:
        require(marker not in smoke, f'identifiant privilégié interdit dans le smoke: {marker}')

    # Le CLI Supabase local doit permettre exactement le facteur TOTP utilisé par le produit.
    require('[auth.mfa.totp]' in config, 'bloc auth.mfa.totp local absent')
    mfa_block = config.split('[auth.mfa.totp]', 1)[1]
    mfa_block = mfa_block.split('\n[', 1)[0]
    require(re.search(r'^enroll_enabled\s*=\s*true\s*$', mfa_block, re.MULTILINE) is not None,
            'enrôlement TOTP local doit être activé')
    require(re.search(r'^verify_enabled\s*=\s*true\s*$', mfa_block, re.MULTILINE) is not None,
            'vérification TOTP locale doit être activée')
    require('[auth.mfa.phone]' not in config, 'le smoke AAL2 ne doit pas activer le MFA téléphone')
    require('[auth.passkey]' not in config, 'le smoke AAL2 ne doit pas activer les passkeys')
    require('[functions.personal-ai]' in config and '[functions.conscience-vault]' in config,
            'configuration des deux Edge sensibles absente')
    require(config.count('verify_jwt = true') >= 2, 'JWT doit rester requis sur les fonctions sensibles')

    require('workflow_dispatch:' in workflow, 'déclenchement manuel absent')
    require('pull_request:' in workflow, 'validation PR absente')
    require('supabase start' in workflow, 'pile Supabase complète obligatoire')
    require('supabase db start' not in workflow, 'db start seul ne suffit pas pour Auth + Edge')
    require('python3 scripts/validate_sensitive_aal2_smoke.py' in workflow, 'validateur AAL2 non exécuté')
    require('python3 scripts/smoke_sensitive_aal2_local.py' in workflow, 'smoke AAL2 non exécuté')
    require('SINJIRA_LOCAL_API_URL="$API_URL"' in workflow, 'URL locale non injectée')
    require('SINJIRA_LOCAL_ANON_KEY="$ANON_KEY"' in workflow, 'clé publique locale non injectée')
    require('--no-verify-jwt' not in workflow, 'la vérification JWT Edge ne doit jamais être désactivée')
    require('SUPABASE_ACCESS_TOKEN' not in workflow, 'PAT production interdit')
    require('environment: production' not in workflow, 'le smoke local ne doit jamais demander l’environnement production')
    secret_refs = set(re.findall(r'secrets\.([A-Z0-9_]+)', workflow))
    require(not secret_refs, f'secrets GitHub interdits dans le smoke local: {sorted(secret_refs)}')

    print('OK smoke AAL2 V25: TOTP local activé, JWT aal2 vérifié, Mon IA + Coffre couverts sans privilège de contournement.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
