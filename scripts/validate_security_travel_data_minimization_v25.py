#!/usr/bin/env python3
"""Fail-closed guard for Mode Voyage browser data minimization."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = ROOT / "assets/js/sinjira-security-center-v24-4-98.js"
WORKFLOW = ROOT / ".github/workflows/sinjira-security-travel-data-minimization-v25.yml"


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def extract_between(source: str, start: str, end: str) -> str:
    begin = source.find(start)
    if begin < 0:
        return ""
    finish = source.find(end, begin + len(start))
    return source[begin:] if finish < 0 else source[begin:finish]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate(controller: str, workflow: str) -> list[str]:
    errors: list[str] = []
    dense = compact(controller)
    render = extract_between(controller, "function renderTravel(rows){", "function renderChallenges")
    load = extract_between(controller, "async function loadState(meta,context=null){", "async function saveSettings")
    flow = workflow.lower()

    require(errors, bool(render), "renderTravel function missing")
    require(errors, bool(load), "loadState function missing")
    require(errors, "consttravelNowIso=newDate().toISOString();" in compact(load),
            "travel query must capture one current-time boundary")
    require(errors,
            ".from('security_travel_plans').select('id,status,starts_at,ends_at,destinations')" in dense,
            "travel query must select only the five required fields")
    require(errors, ".from('security_travel_plans').select('*')" not in dense,
            "travel query must never fetch all retained columns")
    require(errors, ".eq('status','active').gte('ends_at',travelNowIso)" in compact(load),
            "travel query must request active, unexpired plans only")
    require(errors, ".order('starts_at',{ascending:true})" in compact(load),
            "travel plans must be ordered from the nearest start forward")

    render_dense = compact(render)
    require(errors, "row?.status==='active'" in render_dense,
            "renderTravel must defensively reject non-active rows")
    require(errors, "endsAt>=now" in render_dense,
            "renderTravel must defensively reject expired rows")
    require(errors, "delete_after" not in render.lower(),
            "retention timestamp must never be part of the browser travel view")
    require(errors, ".innerHTML" not in render,
            "Mode Voyage rendering must not use innerHTML")
    require(errors, "node.replaceChildren()" in render_dense,
            "Mode Voyage rendering must replace stale DOM before display")
    require(errors, "document.createElement(" in render,
            "Mode Voyage rendering must use DOM nodes")
    require(errors, ".textContent=" in render_dense,
            "Mode Voyage values must be written via textContent")
    require(errors, "article.dataset.travelSafeItem='true';" in render_dense,
            "each Mode Voyage card must remain compatible with the #422 safe-item boundary")
    require(errors, "emptyState.dataset.travelSafeItem='true';" in render_dense,
            "empty Mode Voyage state must remain compatible with the #422 safe-item boundary")
    require(errors, "AucunModeVoyageactifoufutur." in render_dense,
            "empty state must not imply retained travel history")
    require(errors, "Actifmaintenant" in render_dense and "Àvenir" in render_dense,
            "travel UI must expose only human-readable active/future state")

    require(errors,
            "Une vérification MFA récente est requise pour activer le Mode Voyage. Aucune activation n’a été effectuée." in controller,
            "travel activation must keep a specific fail-closed AAL2 message")
    require(errors,
            "Une vérification MFA récente est requise pour annuler ce Mode Voyage. Aucune annulation n’a été effectuée." in controller,
            "travel cancellation must keep a specific fail-closed AAL2 message")
    require(errors, "friendlySecurityError(err,'travel-create')" in compact(controller),
            "travel creation errors must use the travel-specific security context")
    require(errors, "errorContext='travel-cancel'" in compact(controller),
            "travel cancellation errors must use the travel-specific security context")

    require(errors, "permissions:\n  contents: read" in workflow,
            "workflow permissions must stay read-only")
    require(errors, "node --check assets/js/sinjira-security-center-v24-4-98.js" in workflow,
            "workflow must syntax-check the controller")
    require(errors,
            "python3 scripts/validate_security_travel_data_minimization_v25.py --self-test" in workflow,
            "workflow must mutation-test the minimization guard")
    require(errors,
            "python3 scripts/validate_security_travel_data_minimization_v25.py" in workflow,
            "workflow must run the minimization validator")
    require(errors, "supabase db push" not in flow and "supabase functions deploy" not in flow,
            "minimization workflow must never deploy")

    return errors


def mutate_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"self-test setup failed for {label}: expected one exact match")
    return source.replace(old, new, 1)


def self_test(controller: str, workflow: str) -> list[str]:
    try:
        mutations = [
            ("wildcard select", mutate_once(controller,
                ".select('id,status,starts_at,ends_at,destinations')", ".select('*')", "wildcard select"), workflow),
            ("status filter removed", mutate_once(controller,
                ".eq('status','active')", "", "status filter"), workflow),
            ("expiry filter removed", mutate_once(controller,
                ".gte('ends_at',travelNowIso)", "", "expiry filter"), workflow),
            ("retention leaked", mutate_once(controller,
                "period.textContent=`${formatDate(row.starts_at)} → ${formatDate(row.ends_at)}`;",
                "period.textContent=`${formatDate(row.starts_at)} → ${formatDate(row.ends_at)} · ${row.delete_after}`;",
                "retention leak"), workflow),
            ("unsafe HTML renderer", mutate_once(controller,
                "node.replaceChildren();", "node.innerHTML='';", "unsafe renderer"), workflow),
            ("safe marker removed", mutate_once(controller,
                "article.dataset.travelSafeItem='true';", "article.dataset.travelItem='true';", "safe marker"), workflow),
            ("AAL2 cancellation weakened", mutate_once(controller,
                "Une vérification MFA récente est requise pour annuler ce Mode Voyage. Aucune annulation n’a été effectuée.",
                "Une vérification MFA récente est requise.", "AAL2 cancellation"), workflow),
            ("self-test skipped", controller, mutate_once(workflow,
                "python3 scripts/validate_security_travel_data_minimization_v25.py --self-test",
                "python3 scripts/validate_security_travel_data_minimization_v25.py",
                "workflow self-test")),
        ]
    except ValueError as exc:
        return [str(exc)]

    failures: list[str] = []
    for name, mutated_controller, mutated_workflow in mutations:
        if not validate(mutated_controller, mutated_workflow):
            failures.append(f"mutation escaped validator: {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    controller = CONTROLLER.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    errors = self_test(controller, workflow) if args.self_test else validate(controller, workflow)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Mode Voyage browser data minimization: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
