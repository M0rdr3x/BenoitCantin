#!/usr/bin/env python3
"""Surveillance HTTP indépendante de la frontière de publication SINJIRA.

La validation du dépôt ne prouve pas que l'hébergeur publie la bonne racine.
Le contrôle en lecture seule exige une réponse 404 pour les routes techniques
sans télécharger leur corps. Le confinement actuel GitHub Pages et la migration
Netlify cible produisent des diagnostics séparés : un écart d'architecture
ne doit pas masquer un verdict de confidentialité du site.
"""
from __future__ import annotations

import argparse
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE_URL = "https://www.benoitcantin.com"
TECHNICAL_ROUTES = (
    "/supabase/config.toml",
    "/tests/e2e/test_public_site.py",
    "/mobile-native/App.tsx",
    "/scripts/build_netlify_public.py",
    "/docs/README.md",
    "/.github/workflows/validate-site.yml",
    # Fichiers de travail réellement présents dans le dépôt et qui doivent
    # être exclus du site Web, même sous un sous-dossier dit public.
    "/projets/projet-nova/official/versions/V322/V322_CURRENT_STATE.json",
    "/projets/projet-nova/official/versions/V316/README.md",
    "/projets/projet-nova/data/modele_comptabilite.csv",
    # Trois exports JSON non approuvés repérés dans le rendu Jekyll le 03/11.
    "/projets/projet-nova/data/diagnostic-g0-sante-premiere-ligne-2025.json",
    "/projets/projet-nova/data/registre-donnees-services-nova-sinjira.json",
    "/projets/projet-nova/data/reperes-financiers-nova-sinjira-2026.json",
    "/projets/projet-nova/data/plan-acquisition-donnees-g0-sante.json",
    "/projets/projet-nova/CNAME_APRES_NAMECHEAP.txt",
    "/assets/icons/README.md",
    # Refus des chemins techniques et des exports réellement versionnés.
    # Ces sentinelles couvrent plusieurs dossiers/formats non contrôlés par
    # les onze sondes initiales. Aucun contenu n'est téléchargé.
    "/_config.yml",
    "/netlify.toml",
    "/vercel.json",
    "/supabase/production-migration-ledger.txt",
    "/supabase/functions/_shared/auth.ts",
    "/supabase/functions/send-game-report/index.ts",
    "/supabase/migrations/20260824013042_sinjira_v24_5_14_admin_privacy_safety_aal2_hardening.sql",
    "/scripts/validate_publication_live_boundary.py",
    "/scripts/test_publication_live_boundary.py",
    "/docs/SUPABASE_PRODUCTION_RUNBOOK.md",
    "/mobile-native/package.json",
    "/mobile-native/NativeProfileHub.tsx",
    "/.github/workflows/supabase-production-preflight.yml",
    "/projets/sinjira/codex/livre-i-delivery-contract.json",
    "/projets/projet-nova/README.md",
    "/projets/projet-nova/official/versions/V317/V317_CYBERSECURITE_RESILIENCE_CONTINUITE_STATE.json",
    "/projets/projet-nova/official/versions/V317/V317_REGISTRE_CHANGEMENTS_SECURITE_CONFIGURATIONS_MODELE.csv",
    "/projets/projet-nova/official/versions/V316/V316_FINAL_INDEPENDENT_VERIFICATION.json",
    "/ADMINISTRATION_FORMULAIRES.md",
)
TIMEOUT_SECONDS = 12


class RefuseRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Une redirection vers / ou vers une page HTML ne vaut pas un 404.
        return None


def validate_public_boundary(statuses: Mapping[str, int]) -> list[str]:
    """Vérifie les vraies réponses HTTP, quel que soit l'hébergeur.

    Le contrat de confinement est exigeant : 404 exact, ni 403, ni redirection,
    ni erreur serveur, ni absence de résultat. Aucun corps n'est récupéré.
    """
    errors: list[str] = []
    if statuses.get("/") != 200:
        errors.append("La page d'accueil officielle ne répond pas en HTTP 200.")
    for route in TECHNICAL_ROUTES:
        observed = statuses.get(route)
        if observed != 404:
            actual = str(observed) if observed is not None else "indisponible"
            errors.append(f"Chemin technique non confiné: {route} -> HTTP {actual} (404 attendu).")
    return errors


def validate_target_hosting(statuses: Mapping[str, int], *, netlify: bool) -> list[str]:
    """Alerte opérationnelle distincte : migration d'hébergement non terminée."""
    errors: list[str] = []
    if statuses.get("/") != 200:
        errors.append("La page d'accueil officielle ne répond pas en HTTP 200.")
    if not netlify:
        errors.append(
            "La réponse de l'accueil ne prouve pas l'hébergement Netlify "
            "(x-nf-request-id / Server: Netlify absents)."
        )
    return errors


def validate_observations(statuses: Mapping[str, int], *, netlify: bool) -> list[str]:
    """Compatibilité du verdict historique strict : confidentialité ET cible."""
    errors = validate_public_boundary(statuses)
    for error in validate_target_hosting(statuses, netlify=netlify):
        if error not in errors:
            errors.append(error)
    return errors


def self_test() -> None:
    good: dict[str, int] = {"/": 200}
    good.update({route: 404 for route in TECHNICAL_ROUTES})
    if validate_observations(good, netlify=True):
        raise AssertionError("Le cas nominal isolé a été refusé.")
    for route in TECHNICAL_ROUTES:
        for status in (200, 301, 302, 403, 500):
            bad = dict(good)
            bad[route] = status
            if not any(route in error for error in validate_observations(bad, netlify=True)):
                raise AssertionError(f"Fuite ou redirection non détectée: {route}, HTTP {status}")
        bad = dict(good)
        del bad[route]
        if not any(route in error for error in validate_observations(bad, netlify=True)):
            raise AssertionError(f"Absence de preuve non détectée: {route}")
    if not validate_observations(good, netlify=False):
        raise AssertionError("Hébergement non qualifié accepté.")
    bad_home = dict(good)
    bad_home["/"] = 503
    if not validate_observations(bad_home, netlify=True):
        raise AssertionError("Accueil non disponible accepté.")
    print("OK: fixtures de confinement HTTP, redirections et hébergement fail-closed.")


def read_status(opener, route: str) -> tuple[int, bool]:
    # Origine fixe, sans URL, hostname ni identifiants fournis par l'utilisateur.
    request = Request(
        BASE_URL + route,
        headers={
            "User-Agent": "SINJIRA-publication-boundary/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Accept": "*/*",
        },
        method="GET",
    )
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            status = int(response.status)
            headers = response.headers
            return status, bool(headers.get("x-nf-request-id")) or (
                "netlify" in headers.get("Server", "").lower()
            )
    except HTTPError as error:
        try:
            return int(error.code), bool(error.headers.get("x-nf-request-id")) or (
                "netlify" in error.headers.get("Server", "").lower()
            )
        finally:
            error.close()


def live(*, mode: str = "strict") -> int:
    if mode not in ("strict", "boundary", "hosting"):
        raise ValueError("Mode de vérification inconnu")
    opener = build_opener(RefuseRedirect())
    observations: dict[str, int] = {}
    origin_is_netlify = False
    # L'alerte de migration n'a besoin que des en-têtes de l'accueil.
    routes = ("/",) if mode == "hosting" else ("/", *TECHNICAL_ROUTES)
    for route in routes:
        try:
            status, netlify = read_status(opener, route)
        except (URLError, OSError, TimeoutError) as error:
            # Ne jamais transformer une erreur réseau en 404 réputé conforme.
            print(f"ECHEC réseau sur {route}: {type(error).__name__}")
            return 1
        observations[route] = status
        if route == "/":
            origin_is_netlify = netlify
        print(f"{route}: HTTP {status}")
    if mode == "boundary":
        errors = validate_public_boundary(observations)
    elif mode == "hosting":
        errors = validate_target_hosting(observations, netlify=origin_is_netlify)
    else:
        errors = validate_observations(observations, netlify=origin_is_netlify)
    if errors:
        print(f"ECHEC: {len(errors)} écart(s) de publication; aucune donnée de réponse affichée.")
        for error in errors:
            print("- " + error)
        return 1
    if mode == "hosting":
        print("PASS: cible Netlify confirmée par la réponse de l'accueil.")
    elif mode == "boundary":
        print(f"PASS: {len(TECHNICAL_ROUTES)} routes techniques en HTTP 404; confidentialité validée.")
    else:
        print(f"PASS: {len(TECHNICAL_ROUTES)} routes techniques en HTTP 404 et origine Netlify confirmée.")
    print("Ce contrôle ne remplace pas le smoke complet de sécurité et des en-têtes #450.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Contrôler la frontière HTTP du site public.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true", help="Fixtures locales sans réseau.")
    group.add_argument("--live", action="store_true", help="Verdict strict historique: confidentialité et Netlify.")
    group.add_argument("--live-boundary", action="store_true", help="Vérifier uniquement le 404 des sources techniques.")
    group.add_argument("--live-hosting", action="store_true", help="Vérifier uniquement la migration Netlify cible.")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.live_boundary:
        return live(mode="boundary")
    if args.live_hosting:
        return live(mode="hosting")
    return live(mode="strict")


if __name__ == "__main__":
    raise SystemExit(main())
