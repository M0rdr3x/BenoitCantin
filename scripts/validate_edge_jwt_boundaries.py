#!/usr/bin/env python3
"""Contrat fail-closed des exceptions JWT Edge et des routes déployables.

Aucune connexion au projet Supabase : lecture locale TOML + sources TypeScript.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "supabase/config.toml"
FUNCTIONS = ROOT / "supabase/functions"
ANONYMOUS_ALLOWED = frozenset({
    "get-document-url", "send-game-report", "life-story-delivery"
})

# Une simple modification verify_jwt=false doit échouer dans la CI sauf pour
# les trois exceptions dont le contrôle d'accès applicatif est vérifié.
REQUIRED_GATES = {
    "get-document-url": (
        "const MAX_REQUEST_BYTES=512",
        "readBoundedRequestText(req,MAX_REQUEST_BYTES)",
        "const service=serviceClient(),user=await optionalUser(req)",
        "doc.status!=='approved'",
        "doc.projects?.status!=='active'",
        "if(userRank<requiredRank)",
        "externalUrlAllowed(url)",
        "createSignedUrl(doc.storage_path,600)",
    ),
    "send-game-report": (
        "readBoundedRequestText(req, MAX_REQUEST_BYTES)",
        "const PAID_EXTERNAL_SERVICES_ENABLED=false",
        "const user = await optionalUser(req)",
        "if (!PAID_EXTERNAL_SERVICES_ENABLED)",
        "if (!user?.email)",
        "body?.mode === 'email'",
    ),
    "life-story-delivery": (
        "readBoundedRequestText(req, MAX_REQUEST_BYTES)",
        "if (!allowedOrigin(req))",
        "if(!/^[a-f0-9]{64}$/.test(body.token))",
        "sha256Hex(token)",
        ".eq('token_hash', hash)",
        "link.revoked_at",
        "Number(link.download_count)",
        "service_life_story_register_download",
    ),
}


def verify_config(config: dict, discovered: set[str]) -> list[str]:
    errors: list[str] = []
    configured = config.get("functions")
    if not isinstance(configured, dict):
        return ["Configuration [functions] absente"]
    for name in sorted(discovered - configured.keys()):
        errors.append(f"Fonction sans contrat JWT: {name}")
    for name in sorted(configured.keys() - discovered):
        errors.append(f"Configuration JWT sans fonction source: {name}")
    for name in sorted(discovered & configured.keys()):
        values = configured[name]
        if not isinstance(values, dict) or type(values.get("verify_jwt")) is not bool:
            errors.append(f"verify_jwt absent ou non booléen: {name}")
        elif values["verify_jwt"] is not (name not in ANONYMOUS_ALLOWED):
            errors.append(f"verify_jwt incohérent avec la liste fermée: {name}")
    return errors


def verify_gates(name: str, code: str) -> list[str]:
    errors = []
    if "req.method!=='POST'" not in code and "req.method !== 'POST'" not in code:
        errors.append(f"{name}: POST obligatoire")
    for gate in REQUIRED_GATES[name]:
        if gate not in code:
            errors.append(f"{name}: garde applicatif absent: {gate}")
    if "await req.text()" in code or "await req.json()" in code:
        errors.append(f"{name}: lecture brute non bornée")
    return errors


def self_test(config: dict, source: dict[str, str], names: set[str]) -> None:
    assert not verify_config(config, names), verify_config(config, names)
    for name, code in source.items():
        assert not verify_gates(name, code), name
        for marker in REQUIRED_GATES[name]:
            assert verify_gates(name, code.replace(marker, "removed", 1)), (
                f"Protection JWT non détectée: {name} / {marker}"
            )
    # Une nouvelle fonction est inaccessible par défaut tant que le contrat
    # explicite verify_jwt=true n'a pas été ajouté.
    assert verify_config(config, names | {"unexpected-public-edge"})
    changed = {"functions": {key: dict(val) for key, val in config["functions"].items()}}
    changed["functions"]["admin-console"]["verify_jwt"] = False
    assert verify_config(changed, names)
    changed["functions"]["admin-console"]["verify_jwt"] = "true"
    assert verify_config(changed, names)
    changed["functions"].pop("admin-console")
    assert verify_config(changed, names)
    for name, code in source.items():
        bad = code.replace("req.method!=='POST'", "req.method!=='GET'", 1)
        bad = bad.replace("req.method !== 'POST'", "req.method !== 'GET'", 1)
        assert bad != code and verify_gates(name, bad)
        assert verify_gates(name, code + "\nawait req.text();")
    print("OK : toutes les mutations JWT, lecteur, méthode et garde refusées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        config = tomllib.loads(CONFIG.read_text("utf-8"))
    except (OSError, ValueError) as error:
        print("ECHEC : configuration JWT illisible:", type(error).__name__)
        return 1
    discovered = {
        entry.name for entry in FUNCTIONS.iterdir()
        if entry.is_dir() and (entry / "index.ts").is_file()
    }
    errors = verify_config(config, discovered)
    source = {}
    for name in sorted(ANONYMOUS_ALLOWED):
        try:
            source[name] = (FUNCTIONS / name / "index.ts").read_text("utf-8")
        except (OSError, UnicodeError):
            errors.append(f"Fonction publique examinée absente: {name}")
    if len(source) == len(ANONYMOUS_ALLOWED):
        for name, code in source.items():
            errors.extend(verify_gates(name, code))
    if errors:
        for e in errors:
            print("ECHEC sécurité JWT Edge:", e)
        return 1
    if args.self_test:
        self_test(config, source, discovered)
    print(f"OK : {len(discovered)} fonctions déclarées ; "
          "3 exceptions JWT munies de gardes applicatifs, aucune nouvelle exception.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
