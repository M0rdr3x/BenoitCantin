#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        raise AssertionError(f'Fichier absent: {path}')
    return p.read_text('utf-8', errors='ignore')


def require(text: str, markers: list[str], label: str) -> None:
    missing = [m for m in markers if m not in text]
    if missing:
        raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text: str, markers: list[str], label: str) -> None:
    found = [m for m in markers if m in text]
    if found:
        raise AssertionError(f'{label}: marqueurs interdits: {found}')


def validate_security_script_version(page: str) -> None:
    """Imposer un fichier JS versionné, unique, sans régression TOTP.

    Les révisions de cache supérieures à 24.4.69 sont valides; exiger
    exactement 24.4.69 cassait la CI après la révision sécuritaire 24.4.70.
    """
    versions = re.findall(
        r'<script\\b[^>]*\\ssrc="\\.\\./assets/js/v24-security\\.js\\?v=(\\d+\\.\\d+\\.\\d+)"[^>]*>',
        page,
    )
    if len(versions) != 1:
        raise AssertionError(
            f'interface sécurité sessions: exactement un script v24-security versionné attendu, obtenu: {versions}'
        )
    version = tuple(int(component) for component in versions[0].split('.'))
    if version < (24, 4, 69):
        raise AssertionError(
            f'interface sécurité sessions: version JS TOTP trop ancienne: {versions[0]}'
        )


def main() -> int:
    core = read('assets/js/sinjira-supabase.js')
    security = read('assets/js/v24-security.js')
    page = read('compte/securite.html')
    auth_pages = read('assets/js/sinjira-auth-pages.js')

    require(core, [
        "export async function signOut()",
        "auth.signOut({scope:'local'})",
        "location.href='/compte/connexion.html'",
    ], 'déconnexion ordinaire locale')

    require(security, [
        "[data-session-signout-others]",
        "[data-session-signout-global]",
        "auth.signOut({scope:'others'})",
        "auth.signOut({scope:'global'})",
        "location.replace('/compte/connexion.html?sessions=closed')",
        "confirm('Déconnecter toutes les autres sessions SINJIRA™",
        "confirm('Déconnecter ce compte de tous les appareils",
    ], 'gestion explicite des sessions')

    require(page, [
        'data-session-signout-others',
        'data-session-signout-global',
        'Déconnecter les autres appareils',
        'Déconnecter tous les appareils',
        'Déconnexion ordinaire limitée à l’appareil courant.',
        'sinjira-account.js?v=24.4.68',
    ], 'interface sécurité sessions')

    validate_security_script_version(page)

    # Une ancienne URL de cache pourrait masquer la correction TOTP déployée.
    forbid(page, [
        'v24-security.js?v=24.4.68',
    ], 'ancienne URL TOTP après mise à jour')

    # Un changement de mot de passe est une opération de sécurité forte : il doit
    # continuer de fermer toutes les sessions, contrairement à la déconnexion normale.
    require(auth_pages, [
        "auth.signOut({scope:'global'})",
        'Toutes les sessions ont été fermées',
    ], 'réinitialisation mot de passe globale')

    forbid(security + page, [
        'stripe',
        'paypal',
        'twilio',
        "factorType:'phone'",
        'api.openai.com',
        'OPENAI_API_KEY',
    ], 'aucun service payant dans la gestion des sessions')

    print('OK sessions V24.4.68: déconnexion locale par défaut, autres/global explicites et reset mot de passe global conservé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
