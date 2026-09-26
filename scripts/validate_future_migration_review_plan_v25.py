#!/usr/bin/env python3
"""Garde documentaire des migrations futures non revues.

Ce garde ne marque aucune migration comme revue. Il vérifie seulement que le plan
humain de revue énumère exactement le delta local qui n'est ni dans le ledger
production ni dans le lot production explicitement revu.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase" / "migrations"
LEDGER = ROOT / "supabase" / "production-migration-ledger.txt"
REVIEWED = ROOT / "supabase" / "production-reviewed-migration-batch.txt"
PLAN = ROOT / "docs" / "SINJIRA_V25_FUTURE_MIGRATIONS_REVIEW_PLAN_2026-09-20.md"

MIGRATION_RE = re.compile(r"^(\d{14})_([A-Za-z0-9_]+)\.sql$")
LEDGER_RE = re.compile(r"^(\d{14})\s+([A-Za-z0-9_]+)$")
REVIEWED_RE = re.compile(r"^(\d{14})\s+([A-Za-z0-9_]+)\s+[0-9a-f]{40}$")
PLAN_RE = re.compile(r"^- \[ \] \x60(\d{14}_[A-Za-z0-9_]+\.sql)\x60\s*$")
PLAN_CHECKED_RE = re.compile(r"^- \[[xX]\] \x60(\d{14}_[A-Za-z0-9_]+\.sql)\x60\s*$")


def useful_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text("utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def production_cutoff() -> str:
    rows = useful_lines(LEDGER)
    parsed = []
    for line in rows:
        match = LEDGER_RE.fullmatch(line)
        if not match:
            raise ValueError(f"Ligne ledger invalide: {line}")
        parsed.append(match.group(1))
    if not parsed:
        raise ValueError("Ledger production vide.")
    if parsed != sorted(parsed):
        raise ValueError("Ledger production non trié.")
    return parsed[-1]


def reviewed_names() -> list[str]:
    names: list[str] = []
    for line in useful_lines(REVIEWED):
        match = REVIEWED_RE.fullmatch(line)
        if not match:
            raise ValueError(f"Ligne reviewed batch invalide: {line}")
        names.append(f"{match.group(1)}_{match.group(2)}.sql")
    return names


def local_future(cutoff: str) -> list[str]:
    rows: list[tuple[str, str]] = []
    for path in MIGRATIONS.glob("*.sql"):
        match = MIGRATION_RE.fullmatch(path.name)
        if not match:
            raise ValueError(f"Nom de migration invalide: {path.name}")
        if match.group(1) > cutoff:
            rows.append((match.group(1), path.name))
    rows.sort()
    return [name for _, name in rows]


def planned_names(plan_text: str) -> list[str]:
    planned: list[str] = []
    for raw in plan_text.splitlines():
        line = raw.strip()
        checked = PLAN_CHECKED_RE.fullmatch(line)
        if checked:
            raise ValueError(
                "Le plan préparatoire ne doit pas marquer une migration comme approuvée/revue: "
                + checked.group(1)
            )
        match = PLAN_RE.fullmatch(line)
        if match:
            planned.append(match.group(1))
    return planned


def validate(plan_text: str | None = None) -> list[str]:
    errors: list[str] = []
    try:
        cutoff = production_cutoff()
        reviewed = reviewed_names()
        future = local_future(cutoff)
    except ValueError as exc:
        return [str(exc)]

    reviewed_set = set(reviewed)
    future_set = set(future)
    missing_reviewed = [name for name in reviewed if name not in future_set]
    if missing_reviewed:
        errors.append(
            "Le reviewed batch référence des migrations absentes du futur local: "
            + ", ".join(missing_reviewed)
        )

    non_reviewed = [name for name in future if name not in reviewed_set]

    if plan_text is None:
        if not PLAN.is_file():
            return [f"Plan de revue absent: {PLAN.relative_to(ROOT)}"]
        plan_text = PLAN.read_text("utf-8")

    for marker in (
        "Statut : préparation de revue uniquement.",
        "Ce document ne constitue **aucune approbation**",
        "0 changement du ledger production",
        "0 déploiement production",
    ):
        if marker not in plan_text:
            errors.append(f"Marqueur de non-approbation absent du plan: {marker}")

    try:
        planned = planned_names(plan_text)
    except ValueError as exc:
        errors.append(str(exc))
        planned = []

    status_match = re.search(r"(\d+)\s*/\s*(\d+)\s+migrations\s*:\s*\*\*NON REVUES\*\*", plan_text)
    if not status_match:
        errors.append("Le plan n'indique pas explicitement le nombre de migrations NON REVUES.")
    else:
        left, right = map(int, status_match.groups())
        if left != right or left != len(non_reviewed):
            errors.append(
                f"Le compteur NON REVUES du plan ({left}/{right}) ne correspond pas au delta courant ({len(non_reviewed)})."
            )

    if len(planned) != len(set(planned)):
        errors.append("Le plan contient une migration en double.")

    if planned != non_reviewed:
        unexpected = [name for name in planned if name not in non_reviewed]
        missing = [name for name in non_reviewed if name not in planned]
        if unexpected:
            errors.append("Le plan contient des migrations qui ne sont plus dans le delta non revu: " + ", ".join(unexpected))
        if missing:
            errors.append("Le plan omet des migrations futures non revues: " + ", ".join(missing))
        if not unexpected and not missing:
            errors.append("Le plan contient le bon ensemble mais pas dans l'ordre chronologique canonique.")

    return errors


def self_test() -> int:
    plan = PLAN.read_text("utf-8")
    names = planned_names(plan)
    if not names:
        print("Auto-test plan migrations: ÉCHEC — aucune migration détectée.")
        return 1

    mutations = {
        "migration retirée": plan.replace(f"- [ ] `{names[0]}`", "", 1),
        "migration cochée": plan.replace(f"- [ ] `{names[0]}`", f"- [x] `{names[0]}`", 1),
        "migration dupliquée": plan.replace(f"- [ ] `{names[0]}`", f"- [ ] `{names[0]}`\n- [ ] `{names[0]}`", 1),
        "marqueur non-approbation retiré": plan.replace("Ce document ne constitue **aucune approbation**", "Ce document constitue une approbation", 1),
    }

    failures = [name for name, mutated in mutations.items() if not validate(mutated)]
    if failures:
        print("Auto-test plan migrations: ÉCHEC")
        for failure in failures:
            print("- mutation dangereuse acceptée:", failure)
        return 1

    print(f"Auto-test plan migrations: OK ({len(mutations)}/{len(mutations)} mutations rejetées)")
    return 0


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        return self_test()

    errors = validate()
    if errors:
        print(f"ECHEC plan migrations futures: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    cutoff = production_cutoff()
    reviewed = reviewed_names()
    future = local_future(cutoff)
    non_reviewed = [name for name in future if name not in set(reviewed)]
    print(
        "OK plan migrations futures: "
        f"{len(reviewed)} migration(s) déjà dans le lot revu, "
        f"{len(non_reviewed)} migration(s) futures explicitement non revues et documentées; "
        "aucune approbation implicite."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
