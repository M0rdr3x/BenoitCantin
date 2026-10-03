#!/usr/bin/env python3
"""Garde A1 d'isolation entre répétition, publication publique et production."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWED = ROOT / "supabase/production-reviewed-migration-batch.txt"
LEDGER = ROOT / "supabase/production-migration-ledger.txt"
DELIVERY = ROOT / "projets/sinjira/codex/livre-i-delivery-contract.json"
ROMANS = ROOT / "projets/sinjira/romans"
READER = ROMANS / "lire-integral.html"

EXPECTED_REVIEWED_BLOB = "2392a7b9f2ce06952555446771933b05d6d47387"
EXPECTED_LEDGER_BLOB = "0eb7b0d886e9f24d5592b7014ed4d92d28fded63"
MAX_READER_SHELL_BYTES = 128 * 1024
FORBIDDEN_PUBLIC_BOOK_SUFFIXES = {
    ".pdf", ".epub", ".mobi", ".azw", ".azw3",
}


def fail(message: str) -> None:
    raise ValueError(message)


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def collect_public_files(root: Path) -> list[tuple[str, int]]:
    files: list[tuple[str, int]] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append((path.relative_to(ROOT).as_posix(), path.stat().st_size))
    return files


def validate_inputs(
    reviewed: bytes,
    ledger: bytes,
    delivery: dict,
    public_files: list[tuple[str, int]],
) -> None:
    if git_blob_sha1(reviewed) != EXPECTED_REVIEWED_BLOB:
        fail("production-reviewed: contenu différent de la base main A1 autorisée")
    if git_blob_sha1(ledger) != EXPECTED_LEDGER_BLOB:
        fail("ledger production: contenu différent de la base main A1 autorisée")

    if delivery.get("publication_state") != "prepared_not_deployed":
        fail("Livre I: état de publication doit rester prepared_not_deployed")
    if delivery.get("human_gate_required") is not True:
        fail("Livre I: garde humaine explicite requise")

    full = delivery.get("full_edition")
    if not isinstance(full, dict):
        fail("Livre I: contrat full_edition absent")
    for key in ("public_repository_allowed", "public_static_url_allowed", "production_deployment_authorized"):
        if full.get(key) is not False:
            fail(f"Livre I: {key} doit rester false")
    if full.get("activation_requires_explicit_human_decision") is not True:
        fail("Livre I: activation production doit rester une décision humaine explicite")

    reader_size = None
    for relative, size in public_files:
        suffix = Path(relative).suffix.lower()
        if suffix in FORBIDDEN_PUBLIC_BOOK_SUFFIXES:
            fail(f"publication publique interdite détectée: {relative}")
        if relative == "projets/sinjira/romans/lire-integral.html":
            reader_size = size

    if reader_size is None:
        fail("Livre I: shell lecteur intégral absent")
    if reader_size > MAX_READER_SHELL_BYTES:
        fail("Livre I: shell lecteur intégral anormalement volumineux; contenu embarqué possible")


def load_inputs() -> tuple[bytes, bytes, dict, list[tuple[str, int]]]:
    return (
        REVIEWED.read_bytes(),
        LEDGER.read_bytes(),
        json.loads(DELIVERY.read_text(encoding="utf-8")),
        collect_public_files(ROMANS),
    )


def self_test(values: tuple[bytes, bytes, dict, list[tuple[str, int]]]) -> None:
    reviewed, ledger, delivery, public_files = values
    validate_inputs(*values)

    delivery_prod = copy.deepcopy(delivery)
    delivery_prod["full_edition"]["production_deployment_authorized"] = True

    mutations = {
        "reviewed modifié": (reviewed + b"\n# mutation\n", ledger, delivery, public_files),
        "ledger modifié": (reviewed, ledger + b"\n# mutation\n", delivery, public_files),
        "autorisation production": (reviewed, ledger, delivery_prod, public_files),
        "PDF intégral public": (
            reviewed,
            ledger,
            delivery,
            public_files + [("projets/sinjira/romans/SINJIRA_Livre_I_integral.pdf", 1)],
        ),
        "lecteur avec contenu embarqué": (
            reviewed,
            ledger,
            delivery,
            [
                (path, MAX_READER_SHELL_BYTES + 1 if path == "projets/sinjira/romans/lire-integral.html" else size)
                for path, size in public_files
            ],
        ),
    }

    for label, mutated in mutations.items():
        try:
            validate_inputs(*mutated)
        except ValueError:
            continue
        fail(f"auto-test non détecté: {label}")

    print(f"OK isolation A1: {len(mutations)}/{len(mutations)} dérives critiques détectées")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    values = load_inputs()
    if args.self_test:
        self_test(values)
        return

    validate_inputs(*values)
    print(
        "OK isolation A1: reviewed/ledger identiques à main, Livre I non autorisé production, "
        "aucun format intégral public et lecteur web limité à un shell."
    )


if __name__ == "__main__":
    main()
