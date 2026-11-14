#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
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


class ScriptSourceCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == 'script':
            attributes = dict(attrs)
            self.sources.append((attributes.get('src') or '', attributes.get('type') or ''))


def require_fresh_security_script(page: str) -> None:
    """Assurer une unique référence de module authentique, avec cache-bust non obsolète."""
    parser = ScriptSourceCollector()
    parser.feed(page)
    parser.close()
    candidates = [(url, kind) for url, kind in parser.sources if 'v24-security.js' in url]
    if len(candidates) != 1:
        raise AssertionError('interface sécurité sessions: module v24-security.js absent ou dupliqué')
    url, kind = candidates[0]
    match = re.fullmatch(r'\.\./assets/js/v24-security\.js\?v=(\d+)\.(\d+)\.(\d+)', url)
    if not match:
        raise AssertionError('interface sécurité sessions: URL du module de sécurité non canonique')
    if kind != 'module':
        raise AssertionError('interface sécurité sessions: le script TOTP doit être exécuté en module')
    if tuple(map(int, match.groups())) < (24, 4, 69):
        raise AssertionError('interface sécurité sessions: version obsolète du module TOTP')


def self_test() -> None:
    """Mutations synthétiques : la CI doit refuser une régression du chargement MFA."""
    safe = '<script src="../assets/js/v24-security.js?v=24.4.70" type="module"></script>'
    require_fresh_security_script(safe)
    mutations = {
        'module absent': '<script src="../assets/js/site.js?v=1" type="module"></script>',
        'module dupliqué': safe + safe,
        'version TOTP révoquée': safe.replace('24.4.70', '24.4.68'),
        'script distant': safe.replace('../assets/js/', 'https://untrusted.example/'),
        'version flottante': safe.replace('?v=24.4.70', '?v=latest'),
        'module désactivé': safe.replace('type="module"', 'type="text/javascript"'),
    }
    for label, invalid in mutations.items():
        try:
            require_fresh_security_script(invalid)
        except AssertionError:
            continue
        raise AssertionError(f'Auto-test défectueux: régression non détectée : {label}')


def main() -> int:
    self_test()
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

    require_fresh_security_script(page)

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
