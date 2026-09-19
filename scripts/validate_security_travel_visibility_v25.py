#!/usr/bin/env python3
"""Fail-closed guardrails for the converged ephemeral Mode Voyage security-center view."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = Path("assets/js/sinjira-security-center-v24-4-98.js")
EXTENSION = Path("assets/js/sinjira-security-v24-4-99.js")
WORKFLOW = Path(".github/workflows/sinjira-security-travel-visibility-v25.yml")


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def extract_between(source: str, start: str, end: str) -> str:
    begin = source.find(start)
    if begin < 0:
        return ""
    finish = source.find(end, begin + len(start))
    return source[begin:] if finish < 0 else source[begin:finish]


def validate_text(core: str, extension: str, workflow: str) -> list[str]:
    errors: list[str] = []
    dense = compact(core)
    render = extract_between(core, "function renderTravel(rows){", "function renderChallenges")
    load = extract_between(core, "async function loadState(meta,context=null){", "async function saveSettings")
    render_dense = compact(render)
    load_dense = compact(load)

    required = (
        ".from('security_travel_plans').select('id,status,starts_at,ends_at,destinations')",
        ".eq('status','active')",
        ".gte('ends_at',travelNowIso)",
        ".order('starts_at',{ascending:true})",
        "row?.status==='active'",
        "Aucun Mode Voyage actif ou futur.",
        "Une vérification MFA récente est requise pour annuler ce Mode Voyage. Aucune annulation n’a été effectuée.",
        "Il n’est plus utilisé pour le signal géographique.",
        "Une vérification MFA récente est requise pour cette action de sécurité.",
    )
    for needle in required:
        if needle not in core:
            errors.append(f"contrat contrôleur absent: {needle}")

    if "consttravelNowIso=newDate().toISOString();" not in load_dense:
        errors.append("la vue Voyage doit capturer une borne temporelle unique par chargement")
    if "endsAt>=now" not in render_dense:
        errors.append("la vue Voyage doit filtrer défensivement les voyages expirés")
    if "article.dataset.travelSafeItem='true';" not in render_dense:
        errors.append("chaque carte Voyage doit porter le marqueur sûr de convergence")
    if "emptyState.dataset.travelSafeItem='true';" not in render_dense:
        errors.append("l’état vide Voyage doit porter le marqueur sûr de convergence")
    if "node.replaceChildren();" not in render_dense:
        errors.append("la vue Voyage doit effacer explicitement le DOM précédent")
    if "document.createElement(" not in render:
        errors.append("la vue Voyage doit construire des nœuds DOM")
    if ".textContent=" not in render_dense:
        errors.append("la vue Voyage doit écrire les valeurs via textContent")
    if ".innerHTML" in render:
        errors.append("la vue Voyage ne doit pas utiliser innerHTML")
    if "delete_after" in render.lower():
        errors.append("delete_after ne doit jamais piloter l’affichage Voyage")
    if ".from('security_travel_plans').select('*')" in dense:
        errors.append("la vue Voyage ne doit pas charger toutes les colonnes")

    for forbidden in ("geolocation", "latitude", "longitude", "raw_ip", "ip_address", "hotel", "flight", "itinerary"):
        if forbidden in render.lower():
            errors.append(f"donnée ou collecte précise interdite dans la vue Voyage: {forbidden}")

    for forbidden in ("security_travel_plans", "travelCancel", "travel visibility", "refreshVisibleTravel", "renderVisibleTravel"):
        if forbidden in extension:
            errors.append(f"l’extension V24.4.99 ne doit pas dupliquer le Mode Voyage: {forbidden}")

    required_workflow = (
        "assets/js/sinjira-security-center-v24-4-98.js",
        "assets/js/sinjira-security-v24-4-99.js",
        "scripts/validate_security_travel_visibility_v25.py",
        "node --check assets/js/sinjira-security-center-v24-4-98.js",
        "python3 scripts/validate_security_travel_visibility_v25.py --self-test",
        "python3 scripts/validate_security_travel_visibility_v25.py",
        "permissions:\n  contents: read",
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


def mutate_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"self-test setup failed for {label}: expected one exact match")
    return source.replace(old, new, 1)


def self_test() -> None:
    core = (ROOT / CORE).read_text(encoding="utf-8")
    extension = (ROOT / EXTENSION).read_text(encoding="utf-8")
    workflow = (ROOT / WORKFLOW).read_text(encoding="utf-8")
    baseline = validate_text(core, extension, workflow)
    if baseline:
        raise SystemExit("SELF-TEST impossible, baseline invalide:\n- " + "\n- ".join(baseline))

    try:
        mutations = {
            "statut actif retiré": (mutate_once(core, ".eq('status','active')", ".neq('status','cancelled')", "status"), extension, workflow),
            "fin non bornée": (mutate_once(core, ".gte('ends_at',travelNowIso)", "", "expiry"), extension, workflow),
            "chargement select étoile": (mutate_once(core, ".select('id,status,starts_at,ends_at,destinations')", ".select('*')", "select"), extension, workflow),
            "rétention affichée": (mutate_once(core, "period.textContent=`${formatDate(row.starts_at)} → ${formatDate(row.ends_at)}`;", "period.textContent=`${formatDate(row.starts_at)} → ${formatDate(row.ends_at)} · ${row.delete_after}`;", "retention"), extension, workflow),
            "injection HTML": (mutate_once(core, "node.replaceChildren();", "node.innerHTML='';", "html"), extension, workflow),
            "marqueur sûr retiré": (mutate_once(core, "article.dataset.travelSafeItem='true';", "article.dataset.travelItem='true';", "marker"), extension, workflow),
            "MFA Voyage générique": (mutate_once(core, "Une vérification MFA récente est requise pour annuler ce Mode Voyage. Aucune annulation n’a été effectuée.", "Une vérification MFA est requise.", "aal2"), extension, workflow),
            "duplication Voyage extension": (core, extension + "\nconst travel='security_travel_plans';\n", workflow),
            "validation CI retirée": (core, extension, mutate_once(workflow, "python3 scripts/validate_security_travel_visibility_v25.py --self-test", "echo self-test-retire", "workflow")),
        }
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

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
    print("OK: vue Mode Voyage convergée, minimale, éphémère et sans duplication.")


if __name__ == "__main__":
    main()
