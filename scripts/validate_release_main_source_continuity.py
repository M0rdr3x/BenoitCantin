#!/usr/bin/env python3
"""Assurer la continuité des fichiers uniquement présents sur main (2026-10-22).

Les empreintes sont celles des blobs de main
9ed5f70cbe7022f25a679346a1288701f3b09067.
Leur restauration dans le dépôt ne permet PAS leur publication Web.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.build_netlify_public import relative_path_allowed

ROOT = Path(__file__).resolve().parents[1]

MAIN_ONLY_BLOBS = {
    ".github/workflows/audit-web-release-merge.yml": "635852ae2aa414d19b304bd71eba967b96ea5016",
    ".github/workflows/publication-boundary-watch.yml": "55fad0cdef1ae6c2e59fba89f81657e0c65867f4",
    ".github/workflows/validate-account-auth-security-shell.yml": "ac406a35d09d7a1a025db6d1b632080f3af5248d",
    ".github/workflows/validate-account-core-shell.yml": "d455405d457f1c4579c08cc8da33c1899b7354f4",
    ".github/workflows/validate-account-personal-tools-shell.yml": "18b2e913e06b3c4a5fe98f6f8a0a3145640e13f5",
    ".github/workflows/validate-account-privacy-shell.yml": "87d4766d3de5af72886b911d38ea903fce38d7aa",
    ".github/workflows/validate-account-secondary-shell.yml": "6bc896b384a585c293085f755c761ed97a0d55cb",
    ".github/workflows/validate-account-social-shell.yml": "fc99311ef10aadc96d99137b186e1834c3d26f7a",
    ".github/workflows/validate-account-specialized-shell.yml": "a50753d7fda2bb25af8a911b668d6437f9251046",
    ".github/workflows/validate-admin-shell.yml": "8932b23b6eae42a1d6cd0a7387de8952d38a5de3",
    ".github/workflows/verify-web-release-candidate.yml": "e5f2c2b6b713fe37705de0b76247e5c927867d86",
    "assets/js/home-assistant-lazy-v24-5-2.js": "a5d790a4efb191be0474aacf3a2f29ee3095c319",
    "projets/sinjira/romans/livre-1-release.json": "1af72998236b02a90742fdd90c6112cd59c946a5",
    "scripts/audit_web_release_merge.py": "e197e0d5919c1b2f9d42ef863557eb3879ca0a7a",
    "scripts/validate_account_auth_security_shell.py": "b1c71a04562b3279c50a4c83823c31c0025be491",
    "scripts/validate_account_core_shell.py": "0af21f4155f60f8c56d5a47c9d1cb218397e2013",
    "scripts/validate_account_personal_tools_shell.py": "9ee7e596e364e8ba6e0aca4388f716a6b302ede6",
    "scripts/validate_account_privacy_shell.py": "bf0c74f4fdae5b1e858f435982388199395a5a3b",
    "scripts/validate_account_secondary_shell.py": "ebdbd5f2e6fb4d958ee590579e86050e9caae1bf",
    "scripts/validate_account_social_shell.py": "aa9c579a44acc9b497395477cee3ce4747fedebc",
    "scripts/validate_account_specialized_shell.py": "bc6389c8942bff00ded05c403f3d276a3f16d960",
    "scripts/validate_admin_shell.py": "079f310d8bee73f2a4cd40f0da9a89858fb68624",
    "scripts/validate_error_pages.py": "e267612fa2605dd1fd08573686c82d3003c120a8",
    "scripts/validate_nova_form_decommission.py": "20823fe31c15374c368e1adb82661d42bff6a4c3",
    "scripts/validate_nova_legacy_routes.py": "998a6c6543d8d020ce63c8d98dfdac15953fccd1",
    "scripts/validate_public_root_shell.py": "4dd0e81b95c2fc8f4d2972296c23e2e1a07a1093",
    "scripts/validate_publication_live_boundary.py": "95895130538ee9ace56dc15d76ff587d0cccaa9c",
    "scripts/validate_sinjira_public_shell.py": "9f25f279accde6c3d4e6535525f14e0541eaf71d",
    "supabase/functions/get-novel-file-url/index.ts": "255004178c053fcaf5fe1f5ad7e8ba789b54d914",
}


def git_blob_sha(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def validate() -> list[str]:
    errors: list[str] = []
    if len(MAIN_ONLY_BLOBS) != 29:
        errors.append("Inventaire main-only incomplet: 29 blobs attendus")
    for rel, expected in sorted(MAIN_ONLY_BLOBS.items()):
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"Source main absente: {rel}")
            continue
        observed = git_blob_sha(path.read_bytes())
        if observed != expected:
            errors.append(f"Source main modifiée sans revue: {rel} ({observed})")

    strictly_private = [
        "projets/sinjira/romans/livre-1-release.json",
        "supabase/functions/get-novel-file-url/index.ts",
        "scripts/validate_publication_live_boundary.py",
        ".github/workflows/verify-web-release-candidate.yml",
    ]
    for rel in strictly_private:
        if relative_path_allowed(Path(rel)):
            errors.append(f"Fuite d'artefact: {rel} aurait été publié")

    public_asset = "assets/js/home-assistant-lazy-v24-5-2.js"
    if not relative_path_allowed(Path(public_asset)):
        errors.append(f"Asset JS public absent de l'allowlist: {public_asset}")
    return errors


def self_test() -> list[str]:
    errors: list[str] = []
    cases = [(b"test", "30d74d258442c7c65512eafab474568dd706c430")]
    for raw, known in cases:
        if git_blob_sha(raw) != known:
            errors.append("Calcul du SHA Git blob incorrect")
    if not MAIN_ONLY_BLOBS.get("supabase/functions/get-novel-file-url/index.ts"):
        errors.append("Source backend du roman hors inventaire")
    return errors


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    problems = self_test() if args.self_test else validate()
    if problems:
        for line in problems:
            print("ECHEC:", line)
        raise SystemExit(1)
    print("OK: intégrité des sources main et confinement des métadonnées privées du roman.")
