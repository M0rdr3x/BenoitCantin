#!/usr/bin/env python3
"""Fail-closed guardrails for the ephemeral Mode Voyage security-center view."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = Path("assets/js/sinjira-security-v24-4-99.js")
WORKFLOW = Path(".github/workflows/sinjira-security-travel-visibility-v25.yml")


def validate_text(client: str, workflow: str) -> list[str]:
    errors: list[str] = []

    required_client = (
        "const travelList=document.querySelector('[data-security-travel-list]');",
        "if(travelList){\n  travelList.hidden=true;\n  travelObserver.observe",
        ".from('security_travel_plans')",
        ".select('id,status,starts_at,ends_at,destinations')",
        ".eq('status','active')",
        ".gte('ends_at',nowIso)",
        ".order('starts_at',{ascending:true})",
        "row?.status==='active'",
        "endsMs>=nowMs",
        "Aucun Mode Voyage actif ou futur.",
        "data-travel-safe-item",
        "event.stopImmediatePropagation();",
        "},true);",
        "security_cancel_travel_plan",
        "AAL2_REQUIRED",
        "Une vérification MFA récente est requise pour annuler ce Mode Voyage. Aucune annulation n’a été effectuée.",
        "Il n’est plus utilisé pour le signal géographique.",
    )
    for needle in required_client:
        if needle not in client:
            errors.append(f"contrat client absent: {needle}")

    if ".select('*')" in client:
        errors.append("la vue Voyage ne doit pas charger toutes les colonnes")
    if "delete_after" in client:
        errors.append("delete_after est une règle de rétention et ne doit pas piloter l’affichage utilisateur")

    travel_start = client.find("function safeTravelNode")
    travel_end = client.find("const observer=", travel_start)
    if travel_start < 0 or travel_end < 0:
        errors.append("frontière du module Voyage introuvable")
    else:
        travel_section = client[travel_start:travel_end]
        if ".innerHTML" in travel_section:
            errors.append("la vue Voyage doit construire le DOM sans innerHTML")
        for forbidden in ("geolocation", "latitude", "longitude", "raw_ip", "ip_address", "hotel", "flight", "itinerary"):
            if forbidden in travel_section.lower():
                errors.append(f"donnée ou collecte précise interdite dans la vue Voyage: {forbidden}")

    required_workflow = (
        "python3 scripts/validate_security_travel_visibility_v25.py --self-test",
        "python3 scripts/validate_security_travel_visibility_v25.py",
        "assets/js/sinjira-security-v24-4-99.js",
        "scripts/validate_security_travel_visibility_v25.py",
    )
    for needle in required_workflow:
        if needle not in workflow:
            errors.append(f"workflow incomplet: {needle}")

    return errors


def validate(root: Path) -> list[str]:
    missing = [str(path) for path in (CLIENT, WORKFLOW) if not (root / path).is_file()]
    if missing:
        return [f"fichier requis absent: {path}" for path in missing]
    return validate_text(
        (root / CLIENT).read_text(encoding="utf-8"),
        (root / WORKFLOW).read_text(encoding="utf-8"),
    )


def self_test() -> None:
    client = (ROOT / CLIENT).read_text(encoding="utf-8")
    workflow = (ROOT / WORKFLOW).read_text(encoding="utf-8")
    baseline = validate_text(client, workflow)
    if baseline:
        raise SystemExit("SELF-TEST impossible, baseline invalide:\n- " + "\n- ".join(baseline))

    mutations = {
        "statut actif retiré": (client.replace(".eq('status','active')", ".neq('status','cancelled')", 1), workflow),
        "fin du voyage non bornée": (client.replace(".gte('ends_at',nowIso)", ".order('ends_at')", 1), workflow),
        "chargement select étoile": (client.replace(".select('id,status,starts_at,ends_at,destinations')", ".select('*')", 1), workflow),
        "rétention utilisée comme historique": (client.replace("const nowIso=new Date().toISOString();", "const nowIso=new Date().toISOString();\n    const delete_after='history';", 1), workflow),
        "vue non masquée": (client.replace("if(travelList){\n  travelList.hidden=true;\n  travelObserver.observe", "if(travelList){\n  travelObserver.observe", 1), workflow),
        "capture annulation retirée": (client.replace("},true);\n\ndocument.addEventListener('click',async event=>", "},false);\n\ndocument.addEventListener('click',async event=>", 1), workflow),
        "message MFA générique": (client.replace("Une vérification MFA récente est requise pour annuler ce Mode Voyage. Aucune annulation n’a été effectuée.", "Une vérification MFA est requise.", 1), workflow),
        "injection HTML dans vue Voyage": (client.replace("node.textContent=text;", "node.innerHTML=text;", 1), workflow),
        "validation CI retirée": (client, workflow.replace("python3 scripts/validate_security_travel_visibility_v25.py --self-test", "echo self-test-retire", 1)),
    }

    for label, (mut_client, mut_workflow) in mutations.items():
        if not validate_text(mut_client, mut_workflow):
            raise SystemExit(f"SELF-TEST fail-open: {label}")

    print(f"OK: {len(mutations)}/{len(mutations)} régressions Mode Voyage détectées")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    errors = validate(ROOT)
    if errors:
        raise SystemExit("Validation Mode Voyage échouée:\n- " + "\n- ".join(errors))
    print("OK: vue Mode Voyage éphémère, active/future uniquement, annulation AAL2 explicite.")


if __name__ == "__main__":
    main()
