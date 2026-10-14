#!/usr/bin/env python3
"""P50H: audit local, read-only, of a *public evidence template*. Never grants GO."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

GATES = tuple(f"B{i:02d}" for i in range(1, 15))
POST = frozenset({"B12", "B14"})
STATES = frozenset({"NON_DOCUMENTE", "A_VERIFIER", "VERIFIE_HORS_DEPOT", "REJETE"})
SNAPSHOT = ("main", "pr_636", "pr_638", "pr_640", "pr_645", "pr_646")
REQUIRED_GUARDS = ("Ne pas fusionner PR 640", "Ne pas activer de formulaire",
                   "La CI ne signe aucune decision humaine")
SHA = re.compile(r"^[0-9a-f]{40}$")
EV = re.compile(r"^EV-[A-Z0-9-]{8,60}$")

def inspect(data: object) -> dict:
    problems = []
    if not isinstance(data, dict):
        return {"status": "MODELE_INVALIDE", "problems": ["ROOT_NOT_OBJECT"],
                "decision_publication": "NO_GO_AUTOMATIQUE"}
    if data.get("schema_version") != "P50H-1":
        problems.append("SCHEMA_INATTENDU")
    if data.get("nature") != "MODELE_PUBLIC_SANS_PREUVE_PRIVEE":
        problems.append("MODELE_NON_PUBLIC_OU_NON_CONFORME")
    snapshots = data.get("snapshot_source")
    if not isinstance(snapshots, dict) or any(
            not isinstance(snapshots.get(k), str) or not SHA.fullmatch(snapshots[k])
            for k in SNAPSHOT):
        problems.append("SNAPSHOT_INCOMPLET_OU_INVALIDE")
    gates = data.get("portes")
    if not isinstance(gates, list):
        gates = []
        problems.append("REGISTRE_ABSENT")
    found = {}
    for item in gates:
        if not isinstance(item, dict):
            problems.append("ENTREE_NON_OBJET"); continue
        gate_id = item.get("id")
        if gate_id not in GATES or gate_id in found:
            problems.append("PORTE_INCONNUE_OU_DUPLIQUEE"); continue
        found[gate_id] = item
        if item.get("phase") != ("POST" if gate_id in POST else "PRE"):
            problems.append("MAUVAISE_PHASE_" + gate_id)
        state = item.get("statut")
        if state not in STATES:
            problems.append("ETAT_INVALIDE_" + gate_id)
        if not isinstance(item.get("role_requis"), str) or not item["role_requis"].strip():
            problems.append("ROLE_MANQUANT_" + gate_id)
        ref = item.get("reference_preuve", "")
        when = item.get("date_verification", "")
        if state == "VERIFIE_HORS_DEPOT":
            if not isinstance(ref, str) or not EV.fullmatch(ref):
                problems.append("REFERENCE_NON_VERIFIABLE_" + gate_id)
            try:
                date.fromisoformat(when)
            except (TypeError, ValueError):
                problems.append("DATE_NON_VALIDE_" + gate_id)
        elif ref or when:
            problems.append("PREUVE_SANS_VERIFICATION_" + gate_id)
    if set(found) != set(GATES):
        problems.append("PORTES_MANQUANTES")
    horizon = data.get("horizon")
    if not isinstance(horizon, dict) or (
        set(horizon.get("pre_deploiement", [])) != set(GATES) - POST
        or set(horizon.get("post_deploiement", [])) != POST
        or len(horizon.get("pre_deploiement", [])) != 12
        or len(horizon.get("post_deploiement", [])) != 2):
        problems.append("HORIZON_INVALIDE")
    guards = data.get("garde_fous", [])
    if not isinstance(guards, list) or any(g not in guards for g in REQUIRED_GUARDS):
        problems.append("VERROU_MANQUANT")
    roles = data.get("habilitations")
    if not isinstance(roles, dict) or len(roles) < 7 or any(
        not isinstance(v, dict) or not isinstance(v.get("atteste"), bool) or
        not isinstance(v.get("reference_preuve"), str) for v in roles.values()):
        problems.append("HABILITATIONS_MAL_FORMEES")
    decision = data.get("decision")
    if not isinstance(decision, dict) or (
            decision.get("statut") != "NO_GO" or
            decision.get("mandat_signe_externe") is not False or
            decision.get("publication_realisee") is not False):
        problems.append("DECISION_PUBLIQUE_INTERDITE")
    # A template is always incomplete as a real-world proof even if all entries say VERIFIED.
    counts = {state: sum(v.get("statut") == state for v in found.values()) for state in sorted(STATES)}
    return {
        "status": "MODELE_VALIDEMENT_STRUCTURE" if not problems else "MODELE_INVALIDE",
        "problems": sorted(set(problems)),
        "portes_total": len(found),
        "portes_pre": len(set(found) - POST),
        "portes_post": len(set(found) & POST),
        "etats": counts,
        "preuves_authentifiees_par_ce_script": 0,
        "revues_github_verifiees_en_ligne": False,
        "habilitations_verifiees_en_ligne": False,
        "publication_verifiee_en_ligne": False,
        "decision_publication": "NO_GO_AUTOMATIQUE",
        "note": "Contrôle de cohérence documentaire; aucune authentification ou autorisation."
    }

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registre", type=Path,
        default=Path(__file__).resolve().parents[1] / "projets" / "projet-nova" /
                "controles" / "P50H_REGISTRE_PUBLIC_MODELE.json")
    parser.add_argument("--rapport", type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.registre.read_text(encoding="utf-8"))
        result = inspect(data)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result = {"status": "MODELE_INVALIDE", "problems": ["LECTURE_OU_JSON_INVALIDE"],
                  "decision_publication": "NO_GO_AUTOMATIQUE", "detail": type(exc).__name__}
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True, exist_ok=True)
        args.rapport.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0 if result["status"] == "MODELE_VALIDEMENT_STRUCTURE" else 2

if __name__ == "__main__":
    sys.exit(main())
