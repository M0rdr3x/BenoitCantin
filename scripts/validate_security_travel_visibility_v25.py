#!/usr/bin/env python3
"""Fail-closed guardrails for the ephemeral Mode Voyage security-center view."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = Path("assets/js/sinjira-security-center-v24-4-98.js")
EXTENSION = Path("assets/js/sinjira-security-v24-4-99.js")
WORKFLOW = Path(".github/workflows/sinjira-security-travel-visibility-v25.yml")


def validate_text(core: str, extension: str, workflow: str) -> list[str]:
    errors: list[str] = []

    required_core = (
        "function safeTravelNode(tag,text,className='')",
        "node.textContent=text;",
        "function renderTravel(rows)",
        "function listVisibleTravel()",
        ".from('security_travel_plans')",
        ".select('id,status,starts_at,ends_at,destinations')",
        ".eq('status','active')",
        ".gte('ends_at',nowIso)",
        ".order('starts_at',{ascending:true})",
        "row?.status==='active'",
        "endsMs>=nowMs",
        "Aucun Mode Voyage actif ou futur.",
        "listVisibleTravel(),",
        "security_cancel_travel_plan",
        "if(!(await cancelTravel(target)))return",
        "Une vérification MFA récente est requise pour annuler ce Mode Voyage. Aucune annulation n’a été effectuée.",
        "Il n’est plus utilisé pour le signal géographique.",
        "Une vérification MFA récente est requise pour cette action de sécurité.",
    )
    for needle in required_core:
        if needle not in core:
            errors.append(f"contrat contrôleur absent: {needle}")

    travel_start = core.find("function safeTravelNode")
    travel_end = core.find("function renderChallenges", travel_start)
    if travel_start < 0 or travel_end < 0:
        errors.append("frontière du module Voyage introuvable dans le contrôleur principal")
    else:
        travel_section = core[travel_start:travel_end]
        if ".innerHTML" in travel_section:
            errors.append("la vue Voyage doit construire le DOM sans innerHTML")
        if ".select('*')" in travel_section:
            errors.append("la vue Voyage ne doit pas charger toutes les colonnes")
        if "delete_after" in travel_section:
            errors.append("delete_after est une règle de rétention et ne doit pas piloter l’affichage utilisateur")
        for forbidden in ("geolocation", "latitude", "longitude", "raw_ip", "ip_address", "hotel", "flight", "itinerary"):
            if forbidden in travel_section.lower():
                errors.append(f"donnée ou collecte précise interdite dans la vue Voyage: {forbidden}")

    for forbidden in ("security_travel_plans", "travelCancel", "travel visibility", "refreshVisibleTravel", "renderVisibleTravel"):
        if forbidden in extension:
            errors.append(f"l’extension V24.4.99 ne doit plus dupliquer le Mode Voyage: {forbidden}")

    required_workflow = (
        "assets/js/sinjira-security-center-v24-4-98.js",
        "assets/js/sinjira-security-v24-4-99.js",
        "scripts/validate_security_travel_visibility_v25.py",
        "node --check assets/js/sinjira-security-center-v24-4-98.js",
        "python3 scripts/validate_security_travel_visibility_v25.py --self-test",
        "python3 scripts/validate_security_travel_visibility_v25.py",
    )
    for needle in required_workflow:
        if needle not in workflow:
            errors.append(f"workflow incomplet: {needle}")

    return errors


def validate(root: Path) -> list[str]:
    required = (CORE, EXTENSION, WORKFLOW)
    missing = [str(path) for path in required if not (root / path).is_file()]
    if missing:
        return [f"fichier requis absent: {path}" for path in missing]
    return validate_text(
        (root / CORE).read_text(encoding="utf-8"),
        (root / EXTENSION).read_text(encoding="utf-8"),
        (root / WORKFLOW).read_text(encoding="utf-8"),
    )


def self_test() -> None:
    core = (ROOT / CORE).read_text(encoding="utf-8")
    extension = (ROOT / EXTENSION).read_text(encoding="utf-8")
    workflow = (ROOT / WORKFLOW).read_text(encoding="utf-8")
    baseline = validate_text(core, extension, workflow)
    if baseline:
        raise SystemExit("SELF-TEST impossible, baseline invalide:\n- " + "\n- ".join(baseline))

    mutations = {
        "statut actif retiré": (core.replace(".eq('status','active')", ".neq('status','cancelled')", 1), extension, workflow),
        "fin du voyage non bornée": (core.replace(".gte('ends_at',nowIso)", ".order('ends_at')", 1), extension, workflow),
        "chargement select étoile": (core.replace(".select('id,status,starts_at,ends_at,destinations')", ".select('*')", 1), extension, workflow),
        "rétention utilisée comme historique": (core.replace("const nowIso=new Date().toISOString();", "const nowIso=new Date().toISOString();\n  const delete_after='history';", 1), extension, workflow),
        "chargement principal contourné": (core.replace("    listVisibleTravel(),", "    getSupabase().from('security_travel_plans').select('*'),", 1), extension, workflow),
        "injection HTML dans vue Voyage": (core.replace("node.textContent=text;", "node.innerHTML=text;", 1), extension, workflow),
        "message MFA Voyage générique": (core.replace("Une vérification MFA récente est requise pour annuler ce Mode Voyage. Aucune annulation n’a été effectuée.", "Une vérification MFA est requise.", 1), extension, workflow),
        "duplication Voyage dans extension": (core, extension + "\nconst travel='security_travel_plans';\n", workflow),
        "syntax check retiré": (core, extension, workflow.replace("node --check assets/js/sinjira-security-center-v24-4-98.js", "echo syntax-check-retire", 1)),
        "validation CI retirée": (core, extension, workflow.replace("python3 scripts/validate_security_travel_visibility_v25.py --self-test", "echo self-test-retire", 1)),
        "géolocalisation précise introduite": (core.replace("const nowIso=new Date().toISOString();", "const nowIso=new Date().toISOString();\n  const latitude='forbidden';", 1), extension, workflow),
    }

    for label, (mut_core, mut_extension, mut_workflow) in mutations.items():
        if not validate_text(mut_core, mut_extension, mut_workflow):
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
    print("OK: contrôleur Mode Voyage unique, minimal, actif/futur uniquement et annulation AAL2 explicite.")


if __name__ == "__main__":
    main()
