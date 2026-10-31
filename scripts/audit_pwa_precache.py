#!/usr/bin/env python3
"""Prouver que toutes les ressources CORE de la PWA seront servies par Jekyll.

L'installation du service worker utilise Promise.all(CORE) : une seule
ressource absente fait échouer l'installation. Vérification hors réseau,
sur les sources et sur l'artefact qui sera réellement livré.
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

EXPECTED_COUNT = 48
CORE_START = re.compile(r"\bconst\s+CORE\s*=\s*\[([\s\S]*?)\]\s*;")
CORE_TOKEN = re.compile(r"'([^'\\]*)'")
ALLOWED_URL = re.compile(r"/[a-zA-Z0-9_./-]*\Z")
NOVA_SURVEY_NETWORK_ONLY = (
    "/projets/projet-nova/consultation-40.html",
    "/projets/projet-nova/sondage.html",
    "/projets/projet-nova/assets/consultation-40.js",
    "/projets/projet-nova/assets/sondage.js",
    "/projets/projet-nova/assets/sondage.css",
    "/projets/projet-nova/data/consultation-40-v1.json",
    "/projets/projet-nova/data/sondage-questions-v1.json",
    "/projets/projet-nova/resultats-sondages.html",
    "/projets/projet-nova/assets/resultats-sondages.js",
    "/projets/projet-nova/data/resultats-sondages-publics-v1.json",
)
PRIVATE_PREFIXES = (
    "/app", "/compte", "/Admin", "/admin", "/histoire-de-vie",
    "/supabase", "/api", "/auth", "/rest", "/storage", "/functions",
    "/edge", "/account", "/login", "/logout", "/.well-known",
)


def extract_core(source: str) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    matches = CORE_START.findall(source)
    if len(matches) != 1:
        return [], ["Liste CORE du service worker absente ou dupliquée"]
    body = matches[0]
    paths = CORE_TOKEN.findall(body)
    leftovers = CORE_TOKEN.sub("", body)
    if leftovers.strip(" \n\t\r,"):
        problems.append("Contenu CORE non littéral : chemins non vérifiables")
    if len(paths) != EXPECTED_COUNT:
        problems.append(
            f"Inventaire PWA modifié : {len(paths)} au lieu de {EXPECTED_COUNT} chemins"
        )
    if len(paths) != len(set(paths)):
        problems.append("Chemin PWA dupliqué dans CORE")
    for route in paths:
        parts = route.split("/")
        if (not ALLOWED_URL.fullmatch(route) or route.startswith("//")
                or any(p in {".", ".."} for p in parts) or
                route.endswith("//") or
                route in NOVA_SURVEY_NETWORK_ONLY or
                any(route == private or route.startswith(private + "/")
                    for private in PRIVATE_PREFIXES)):
            problems.append(f"Route privée ou non canonique dans CORE: {route}")
    for required in (
        "/", "/offline.html", "/manifest.webmanifest",
        "/projets/sinjira/romans/", "/projets/sinjira/jeux/",
        "/projets/sinjira/logiciels/",
    ):
        if required not in paths:
            problems.append(f"Coquille PWA indispensable absente de CORE: {required}")
    return paths, problems


def built_path(route: str) -> str:
    if route.endswith("/"):
        return route.lstrip("/") + "index.html"
    return route.lstrip("/")


def audit(source: Path, built: Path | None) -> list[str]:
    if not source.is_dir():
        return ["Dossier source PWA absent"]
    script = source / "sw.js"
    if not script.is_file() or script.is_symlink():
        return ["Service worker source manquant ou symbolique"]
    try:
        paths, errors = extract_core(script.read_text("utf-8"))
    except (OSError, UnicodeError):
        return ["Service worker illisible"]
    if built is not None and not built.is_dir():
        errors.append("Artefact Jekyll PWA manquant")
        return errors
    for path in NOVA_SURVEY_NETWORK_ONLY:
        if ("'" + path + "'") not in script.read_text("utf-8"):
            errors.append(f"Chemin Nova sans exclusion PWA explicite : {path}")
    for marker in ("!surveyNetworkOnly(u.pathname)", "||surveyNetworkOnly(u.pathname)||"):
        if marker not in script.read_text("utf-8"):
            errors.append(f"Garde PWA des sondages supprimée : {marker}")
    for route in paths:
        rel = built_path(route)
        source_target = source / rel
        if not source_target.is_file() or source_target.is_symlink():
            errors.append(f"Ressource CORE absente de la source: {route} -> {rel}")
        if built is not None:
            delivered = built / rel
            if not delivered.is_file() or delivered.is_symlink():
                errors.append(f"Ressource CORE absente de _site: {route} -> {rel}")
    return errors


def self_test() -> None:
    real_source = Path(__file__).resolve().parents[1]
    real_sw = (real_source / "sw.js").read_text("utf-8")
    routes, errors = extract_core(real_sw)
    assert not errors and len(routes) == EXPECTED_COUNT, errors
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "source"
        built = Path(directory) / "_site"
        root.mkdir()
        built.mkdir()
        (root / "sw.js").write_text(real_sw, "utf-8")
        for route in routes:
            for parent in (root, built):
                file = parent / built_path(route)
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(b"public-core-fixture")
        assert not audit(root, built), audit(root, built)
        # Des trois catalogues, aucun ne peut disparaître de l'artefact
        # Jekyll sans casser la disponibilité hors ligne.
        for route in ("/offline.html", "/projets/sinjira/romans/",
                      "/projets/sinjira/jeux/", "/projets/sinjira/logiciels/"):
            for parent, fragment in (
                (root, "absente de la source"),
                (built, "absente de _site"),
            ):
                missing = parent / built_path(route)
                missing.unlink()
                assert any(fragment in error and route in error
                           for error in audit(root, built)), (
                    f"CORE manquant non détecté : {route}"
                )
                missing.write_bytes(b"public-core-fixture")
        sw_file = root / "sw.js"
        modified = real_sw.replace("'/offline.html'", "'/api/private'", 1)
        assert modified != real_sw
        sw_file.write_text(modified, "utf-8")
        assert any("privée" in e or "indispensable" in e
                   for e in audit(root, built)), "Route privée CORE acceptée"
        modified = real_sw.replace("'/offline.html'", "'/'", 1)
        sw_file.write_text(modified, "utf-8")
        assert any("dupliqué" in e for e in audit(root, built)), (
            "Doublon de route CORE accepté"
        )
        modified = real_sw.replace("'/offline.html'", "'/introuvable.html'", 1)
        sw_file.write_text(modified, "utf-8")
        assert any("introuvable.html" in e for e in audit(root, built)), (
            "Nouvelle route sans fichier acceptée"
        )
        sw_file.write_text(real_sw.replace("||surveyNetworkOnly(u.pathname)||", "||", 1), "utf-8")
        assert any("Garde PWA" in e for e in audit(root, built)), (
            "Neutralisation de la lecture réseau Nova non détectée"
        )
        sw_file.write_text(real_sw, "utf-8")
        assert not audit(root, built), audit(root, built)
    print("OK PWA : 48 chemins CORE, dont Romans/Jeux/Logiciels, source+Jekyll présents, "
          "routes privées, doublons et 404 futures bloqués")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--source")
    parser.add_argument("--built")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.source:
        parser.error("--source requis")
    errors = audit(Path(args.source).resolve(),
                   Path(args.built).resolve() if args.built else None)
    for issue in errors:
        print("ERREUR: " + issue, file=sys.stderr)
    if errors:
        return 1
    print(f"OK : {EXPECTED_COUNT} ressources PWA présentes" +
          (" dans la source et dans _site" if args.built else " dans la source"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
