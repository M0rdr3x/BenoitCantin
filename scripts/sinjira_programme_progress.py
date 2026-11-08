#!/usr/bin/env python3
"""SINJIRA — bilan de maturité reproductible, sans dates ni preuves inventées.

Le bilan et le test sont locaux : pas d'accès réseau, compte, manuscrit ou API.
100 % de maturité estimée NE suffit pas à autoriser une mise en production.
"""
from __future__ import annotations

import argparse
import datetime as dt
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs/sinjira/programme-readiness-2026-11-08.json"
DOMAIN_WEIGHTS = {
    "site_public": 10,
    "auth_securite": 15,
    "romans_lecture": 15,
    "registre_personnages": 10,
    "jeux": 15,
    "communaute": 10,
    "monde_codex": 10,
    "commerce": 5,
    "mon_ia": 5,
    "qa_lancement": 5,
}
REQUIRED_GATES = frozenset({
    "reader_v32_prod", "reader_two_devices", "private_book_access",
    "fracture_rpc_rls", "fracture_rules_server", "security_sessions",
    "mobile_csp_performance", "community_moderation", "world_register",
    "editorial_approval", "commerce_legal", "ai_privacy",
    "release_acceptance",
})
SHA_RE = re.compile(r"^[a-f0-9]{40}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _valid_date(value: object) -> bool:
    if not isinstance(value, str) or not ISO_DATE_RE.fullmatch(value):
        return False
    try:
        dt.date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _source(value: object) -> bool:
    return isinstance(value, str) and value.startswith(
        "https://github.com/M0rdr3x/BenoitCantin/"
    ) and len(value) > len("https://github.com/M0rdr3x/BenoitCantin/")


def validate_report(data: object) -> list[str]:
    if not isinstance(data, dict):
        return ["INVALID_ROOT"]
    errors: list[str] = []
    if data.get("schema") != "sinjira-programme-readiness/v1":
        errors.append("INVALID_SCHEMA")
    if data.get("scope") != "SINJIRA_ONLY_EXCLUDES_PROJET_NOVA":
        errors.append("WRONG_SCOPE")
    if data.get("baseline_source") != "docs/SINJIRA_PROGRAMME_AVANCEMENT_2026-11-07.md":
        errors.append("WRONG_BASELINE")
    if not _valid_date(data.get("reference_date")):
        errors.append("INVALID_REFERENCE_DATE")
    if data.get("estimate_uncertainty_percentage_points") != 10:
        errors.append("UNCERTAINTY_NOT_DOCUMENTED")

    domains = data.get("domains")
    if not isinstance(domains, list):
        domains = []
        errors.append("INVALID_DOMAINS")
    names = [d.get("id") for d in domains if isinstance(d, dict)]
    if len(domains) != len(DOMAIN_WEIGHTS) or len(names) != len(domains) or (
        set(names) != set(DOMAIN_WEIGHTS) or len(set(names)) != len(names)
    ):
        errors.append("DOMAIN_INVENTORY_DRIFT")
    for item in domains:
        if not isinstance(item, dict):
            continue
        key = item.get("id")
        if key not in DOMAIN_WEIGHTS:
            continue
        value = item.get("maturity")
        if (type(item.get("weight")) is not int
                or item["weight"] != DOMAIN_WEIGHTS[key]):
            errors.append("WEIGHT_CHANGED:" + key)
        if type(value) not in (int, float) or not (0 <= value <= 100):
            errors.append("BAD_MATURITY:" + key)
        if not isinstance(item.get("missing_evidence"), str) or not item["missing_evidence"].strip():
            errors.append("MISSING_DOMAIN_GAP:" + key)

    gates = data.get("gates")
    if not isinstance(gates, list):
        gates = []
        errors.append("INVALID_GATES")
    ids = [g.get("id") for g in gates if isinstance(g, dict)]
    if (len(gates) != len(REQUIRED_GATES) or len(ids) != len(gates)
            or set(ids) != REQUIRED_GATES or len(set(ids)) != len(ids)):
        errors.append("GATE_INVENTORY_DRIFT")
    for g in gates:
        if not isinstance(g, dict):
            continue
        gate_id = str(g.get("id"))
        status = g.get("status")
        if status not in ("OPEN", "VERIFIED"):
            errors.append("BAD_GATE_STATUS:" + gate_id)
        if g.get("priority") not in ("P0", "P1", "P2"):
            errors.append("BAD_GATE_PRIORITY:" + gate_id)
        if not isinstance(g.get("acceptance"), str) or len(g["acceptance"]) < 25:
            errors.append("MISSING_ACCEPTANCE:" + gate_id)
        if not _source(g.get("tracking_url")):
            errors.append("MISSING_TRACKER:" + gate_id)
        evidence = g.get("evidence_url")
        checked = g.get("validated_at")
        if status == "VERIFIED":
            if not _source(evidence) or not _valid_date(checked):
                errors.append("UNPROVEN_GATE:" + gate_id)
        elif evidence is not None or checked is not None:
            errors.append("UNVERIFIED_GATE_HAS_PROOF:" + gate_id)

    forecast = data.get("forecast")
    if not isinstance(forecast, dict):
        errors.append("INVALID_FORECAST")
        forecast = {}
    finish = forecast.get("estimated_completion_date")
    if finish is not None:
        if (not _valid_date(finish)
                or not _source(forecast.get("evidence_url"))
                or not _valid_date(forecast.get("evidence_as_of"))):
            errors.append("UNSUPPORTED_FINISH_DATE")
    if not isinstance(forecast.get("reason"), str) or len(forecast["reason"]) < 30:
        errors.append("FORECAST_EXPLANATION_MISSING")

    launch = data.get("launch")
    if not isinstance(launch, dict):
        launch = {}
        errors.append("INVALID_LAUNCH")
    if type(launch.get("approved")) is not bool or type(launch.get("complete")) is not bool:
        errors.append("INVALID_RELEASE_FLAGS")
    if launch.get("approved"):
        if not _valid_date(launch.get("approved_at")) or not _source(launch.get("evidence_url")):
            errors.append("UNPROVEN_RELEASE_APPROVAL")
    elif launch.get("approved_at") is not None or launch.get("evidence_url") is not None:
        errors.append("MALFORMED_RELEASE_APPROVAL")
    if launch.get("complete"):
        if not launch.get("approved"):
            errors.append("RELEASE_WITHOUT_APPROVAL")
        if any(g.get("status") != "VERIFIED" for g in gates if isinstance(g, dict)) or len(gates) != len(REQUIRED_GATES):
            errors.append("RELEASE_WITH_OPEN_GATES")
        if any(d.get("maturity") != 100 for d in domains if isinstance(d, dict)) or len(domains) != len(DOMAIN_WEIGHTS):
            errors.append("RELEASE_WITH_INCOMPLETE_DOMAINS")

    deliveries = data.get("recent_verified_deliveries")
    if not isinstance(deliveries, list) or not deliveries:
        errors.append("NO_DELIVERY_PROOF")
    else:
        for i, d in enumerate(deliveries):
            if (not isinstance(d, dict) or type(d.get("pr")) is not int
                    or not SHA_RE.fullmatch(str(d.get("merge_commit", "")))
                    or not isinstance(d.get("scope"), str)
                    or len(d["scope"]) < 20):
                errors.append(f"INVALID_DELIVERY_PROOF:{i}")
    return errors


def summarize(data: dict) -> dict:
    errors = validate_report(data)
    if errors:
        raise ValueError("; ".join(errors))
    weight_total = sum(DOMAIN_WEIGHTS.values())
    if weight_total != 100:
        raise ValueError("La somme des pondérations doit être 100")
    weighted = sum(
        (Decimal(str(row["weight"])) * Decimal(str(row["maturity"])) / Decimal(100)
         for row in data["domains"]),
        Decimal(0),
    )
    displayed = int(weighted.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    open_gates = [g["id"] for g in data["gates"] if g["status"] != "VERIFIED"]
    launch_ready = bool(
        not open_gates and weighted == Decimal(100)
        and data["launch"]["approved"] and data["launch"]["complete"]
    )
    return {
        "maturity_estimate": float(weighted),
        "maturity_rounded": displayed,
        "remaining_estimate": float(Decimal(100) - weighted),
        "uncertainty_percentage_points": data["estimate_uncertainty_percentage_points"],
        "date_of_completion": data["forecast"]["estimated_completion_date"],
        "unverified_gates": open_gates,
        "open_gate_count": len(open_gates),
        "launch_ready": launch_ready,
        "launch_decision": "GO" if launch_ready else "NO_GO",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Avancement SINJIRA : vérification sans date fictive")
    p.add_argument("--register", type=Path, default=REGISTER)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    try:
        info = summarize(json.loads(args.register.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("ECHEC de validité du registre :", exc)
        return 1
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print(f"SINJIRA : {info['maturity_estimate']} % (≈ {info['maturity_rounded']} %),"
              f" reste {info['remaining_estimate']} %, ±"
              f"{info['uncertainty_percentage_points']} points.")
        print(f"Sortie : {info['launch_decision']}; "
              f"{info['open_gate_count']} jalons sans validation complète.")
        if info["date_of_completion"] is None:
            print("Date de fin : indéterminable sans preuves de durée du chemin critique.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
