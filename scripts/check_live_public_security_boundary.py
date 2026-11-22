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
    workflow_self_test()
    print(f"OK frontière publique : {len(FORBIDDEN)} chemins techniques, {len(EXPECTED_PUBLIC)} pages publiques, {mutations} mutations HTTP validées.")


# Ce contrat empêche les futurs refactorings YAML de désactiver en silence
# la surveillance sur les pushes portant sur des fichiers non-techniques.
# Le moniteur lui-même s'autoteste sans accès réseau sur pull_request.
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/live-public-security-boundary.yml"


def workflow_contract_errors(source: str) -> list[str]:
    failures: list[str] = []
    if source.count("\non:\n") != 1 or "\npermissions:\n" not in source:
        return ["Déclencheurs YAML du moniteur introuvables ou ambigus"]
    event_yaml = source.split("\non:\n", 1)[1].split("\npermissions:\n", 1)[0]
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    for line in event_yaml.splitlines():
        if line.startswith("  ") and not line.startswith("    ") and ":" in line and not line.lstrip().startswith("#"):
            name, sep, rest = line.strip().partition(":")
            if sep and name in {"pull_request", "push", "schedule", "workflow_dispatch"} and not rest.strip():
                if name in blocks:
                    failures.append(f"Déclencheur dupliqué : {name}")
                blocks[name] = []
                current = name
                continue
            failures.append(f"Déclencheur inattendu : {line.strip()}")
            current = None
        elif current is not None:
            blocks[current].append(line)

    for mandatory in ("pull_request", "push", "schedule", "workflow_dispatch"):
        if mandatory not in blocks:
            failures.append(f"Déclencheur obligatoire manquant : {mandatory}")
    push = "\n".join(blocks.get("push", []))
    if "    branches: [main]" not in push:
        failures.append("Tout push sur main doit déclencher la sonde")
    if any(token in push for token in ("paths:", "paths-ignore:", "tags:", "branches-ignore:")):
        failures.append("Filtre paths/tags interdit sur push : surveillance de TOUS les commits main")
    pr = "\n".join(blocks.get("pull_request", []))
    if "    branches: [main]" not in pr:
        failures.append("Tests hors réseau obligatoires sur les PR vers main")
    if "    paths:" not in pr:
        failures.append("Le périmètre de tests PR doit rester explicite")
    for required in (
        "      - 'scripts/check_live_public_security_boundary.py'",
        "      - '.github/workflows/live-public-security-boundary.yml'",
    ):
        if required not in pr:
            failures.append(f"Chemin de test PR manquant : {required.strip()}")
    if "pull_request_target:" in source:
        failures.append("pull_request_target interdit")
    if "    - cron: '23 11 * * *'" not in "\n".join(blocks.get("schedule", [])):
        failures.append("Récurrence de contrôle quotidien absente")
    if "  live-boundary:\n" not in source:
        failures.append("Job de contrôle HTTPS de production absent")
    expected_if = (
        "    if: github.event_name == 'push' || github.event_name == 'schedule' "
        "|| github.event_name == 'workflow_dispatch'"
    )
    if expected_if not in source:
        failures.append("Sonde réelle interdite sur PR et obligatoire sur push/cron/manual")
    if "    needs: deterministic-contract" not in source:
        failures.append("Sonde réelle doit dépendre des tests hors réseau")
    if "        run: python3 scripts/check_live_public_security_boundary.py --self-test" not in source:
        failures.append("Contrat hors réseau manquant")
    if "        run: python3 scripts/check_live_public_security_boundary.py --live" not in source:
        failures.append("Commande de sonde HTTPS manquante")
    if source.count("persist-credentials: false") != 2:
        failures.append("Deux checkouts sans jetons persistants obligatoires")
    if "permissions:\n  contents: read" not in source:
        failures.append("Permissions globales read-only requises")
    return failures


def workflow_self_test() -> None:
    original = WORKFLOW.read_text(encoding="utf-8", errors="strict")
    errors = workflow_contract_errors(original)
    if errors:
        raise AssertionError("Contrat CI non conforme : " + "; ".join(errors))
    mutations = (
        ("push limité à deux fichiers",
         "  push:\n    branches: [main]",
         "  push:\n    branches: [main]\n    paths:\n      - 'scripts/check_live_public_security_boundary.py'"),
        ("push limité par paths-ignore",
         "  push:\n    branches: [main]",
         "  push:\n    branches: [main]\n    paths-ignore:\n      - 'projets/**'"),
        ("push non limité à main",
         "  push:\n    branches: [main]",
         "  push:\n    branches: [feature]"),
        ("push supprimé",
         "  push:\n    branches: [main]\n", ""),
        ("cron supprimé",
         "  schedule:\n    - cron: '23 11 * * *'\n", ""),
        ("dispatch manuel supprimé",
         "  workflow_dispatch:\n", ""),
        ("PR privilégiée",
         "  pull_request:\n", "  pull_request_target:\n"),
        ("PR de validation absente",
         "  pull_request:\n", "  only_request:\n"),
        ("sonde HTTPS exécutée sur PR",
         "    if: github.event_name == 'push' || github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'",
         "    if: github.event_name == 'pull_request' || github.event_name == 'push'"),
        ("plus de dépendance au test",
         "    needs: deterministic-contract\n", ""),
        ("commande live retirée",
         "        run: python3 scripts/check_live_public_security_boundary.py --live",
         "        run: echo disabled"),
        ("credentials persistants",
         "          persist-credentials: false",
         "          persist-credentials: true"),
    )
    for title, old, replacement in mutations:
        if old not in original:
            raise AssertionError(f"Mutation sans cible : {title}")
        modified = original.replace(old, replacement, 1)
        if not workflow_contract_errors(modified):
            raise AssertionError(f"Affaiblissement du moniteur non détecté : {title}")
    print(f"OK CI : {len(mutations)} régressions de fréquence/droits/interdiction réseau PR rejetées.")



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
