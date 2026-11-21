#!/usr/bin/env python3
"""Contrôle en lecture seule des fichiers techniques sur le domaine public.

N'inspecte aucun compte, n'envoie pas de formulaire, ne télécharge pas le corps
des réponses : uniquement les codes HTTP de chemins fixes approuvés.
"""
from __future__ import annotations

import argparse
import urllib.error
import urllib.request

BASE = "https://www.benoitcantin.com"
TIMEOUT_SECONDS = 8

# Des chemins existants dans le dépôt, mais JAMAIS approuvés à la publication.
FORBIDDEN = (
    "/supabase/config.toml",
    "/scripts/build_netlify_public.py",
    "/tests/e2e/test_public_site.py",
    "/mobile-native/App.tsx",
    "/docs/README.md",
    "/.github/workflows/deploy-github-pages-isolated.yml",
    "/netlify.toml",
    "/package.json",
    "/.git/config",
    "/.env",
    "/projets/projet-nova/official/versions/V316/README.md",
    "/projets/sinjira/codex/livre-i-delivery-contract.json",
    # Fonctions Edge et migration : des programmes serveur, jamais des assets web.
    "/supabase/functions/security-context/index.ts",
    "/supabase/functions/get-novel-file-url/index.ts",
    "/supabase/migrations/20260910193000_sinjira_v25_device_challenge_session_binding.sql",
    # Audits / workflow GitHub internes.
    "/scripts/validate_jekyll_emergency_pages.py",
    "/.github/workflows/emergency-jekyll-pages-guard.yml",
    # Contrats de publication et corpus de travail, explicitement exclus du site.
    "/projets/sinjira/romans/livre-1-release.json",
    "/projets/sinjira/romans/roman-4-release.json",
    "/projets/projet-nova/official/versions/V322/V322_CURRENT_STATE.json",
    "/projets/projet-nova/data/registre-donnees-services-nova-sinjira.json",
    "/projets/projet-nova/data/diagnostic-g0-sante-premiere-ligne-2025.json",
)
EXPECTED_PUBLIC = (
    "/",
    "/.well-known/security.txt",
    "/projets/projet-nova/",
    "/projets/sinjira/",
)
ALLOWED_DENIALS = frozenset((403, 404, 410))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Ne jamais suivre une redirection vers un hôte tiers ni masquer un 302."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def http_status(path: str) -> int:
    # Aucune URL dynamique : le moniteur ne sert pas de scanner générique.
    assert path in FORBIDDEN or path in EXPECTED_PUBLIC
    request = urllib.request.Request(
        BASE + path,
        method="GET",
        headers={
            "User-Agent": "BenoitCantin-PublicSecurityBoundary/1.0",
            "Accept": "*/*",
            "Cache-Control": "no-cache",
        },
    )
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status
    except urllib.error.HTTPError as error:
        # Les 403/404/410 sont le résultat attendu. Ne jamais lire leur corps.
        try:
            return error.code
        finally:
            error.close()


def validate_statuses(statuses: dict[str, int]) -> list[str]:
    errors: list[str] = []
    for path in FORBIDDEN:
        status = statuses.get(path)
        if status not in ALLOWED_DENIALS:
            # 200 : publication confirmée. 3xx, 5xx ou None : résultat à revoir.
            errors.append(f"CHEMIN TECHNIQUE NON CONFINE : {path}, HTTP {status}")
    for path in EXPECTED_PUBLIC:
        status = statuses.get(path)
        if status != 200:
            errors.append(f"PAGE PUBLIQUE INDISPONIBLE : {path}, HTTP {status}")
    return errors


def self_test() -> None:
    assert BASE == "https://www.benoitcantin.com"
    assert len(FORBIDDEN) == 22, "La liste des sources techniques surveillées ne doit pas rétrécir"
    assert len(set(FORBIDDEN + EXPECTED_PUBLIC)) == len(FORBIDDEN + EXPECTED_PUBLIC)
    for path in FORBIDDEN + EXPECTED_PUBLIC:
        assert path.startswith("/") and not path.startswith("//")
        assert "?" not in path and "#" not in path and "\\" not in path
        assert ".." not in path and "%" not in path

    safe = {path: 404 for path in FORBIDDEN}
    safe.update({path: 200 for path in EXPECTED_PUBLIC})
    assert not validate_statuses(safe)
    mutations = 0
    # Chaque chemin technique DOIT être refusé ; ne pas seulement
    # vérifier le premier élément de la liste.
    for path in FORBIDDEN:
        for status in (403, 404, 410):
            attempt = {**safe, path: status}
            assert not validate_statuses(attempt), f"Refus légitime de {path} rejeté"
            mutations += 1
        for status in (200, 206, 301, 302, 307, 308, 429, 500, None):
            attempt = {**safe, path: status}
            assert validate_statuses(attempt), f"{path} HTTP {status} non détecté"
            mutations += 1
    for path in EXPECTED_PUBLIC:
        for status in (301, 302, 403, 404, 410, 429, 500, None):
            attempt = {**safe, path: status}
            assert validate_statuses(attempt), f"Panne publique {path} HTTP {status} non détectée"
            mutations += 1
    assert not NoRedirect().redirect_request(None, None, 301, "", {}, "https://evil.example/")
    print(f"OK frontière publique : {len(FORBIDDEN)} chemins techniques, {len(EXPECTED_PUBLIC)} pages publiques, {mutations} mutations HTTP validées.")


def check_live() -> int:
    statuses: dict[str, int] = {}
    for path in FORBIDDEN + EXPECTED_PUBLIC:
        try:
            statuses[path] = http_status(path)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            # Indisponibilité ≠ absence de fuite : échouer sans exposer
            # l'exception réseau (proxy / en-têtes / autres détails).
            print(f"INDETERMINE: {path} ({type(exc).__name__})")
            return 1
        print(f"HTTP {statuses[path]} {path}")
    errors = validate_statuses(statuses)
    for error in errors:
        print(error)
    if errors:
        return 1
    print(f"OK : aucune des {len(FORBIDDEN)} routes techniques testées n'est accessible; {len(EXPECTED_PUBLIC)} pages publiques disponibles.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    return check_live()


if __name__ == "__main__":
    raise SystemExit(main())
