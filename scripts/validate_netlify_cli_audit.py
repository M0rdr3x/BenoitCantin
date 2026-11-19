#!/usr/bin/env python3
"""Fail-closed vulnerability gate for the locked Netlify CLI toolchain.

Processes an npm audit --json report. Never needs tokens, npm, or network itself.
Reports moderate/low advisories without accepting high/critical vulnerabilities.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SEVERITIES = ("info", "low", "moderate", "high", "critical")


def inspect(payload: bytes, exit_status: int) -> tuple[list[str], dict[str, int]]:
    issues: list[str] = []
    counts: dict[str, int] = {}
    if exit_status not in {0, 1}:
        issues.append(f"npm audit non exécutable ou interrompu (code {exit_status})")
    try:
        root = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return issues + ["réponse d'audit npm manquante ou JSON invalide"], {}
    if not isinstance(root, dict) or root.get("error"):
        return issues + ["npm audit a signalé une erreur non exploitable"], {}
    meta = root.get("metadata")
    stats = meta.get("vulnerabilities") if isinstance(meta, dict) else None
    if not isinstance(stats, dict):
        return issues + ["résumé des vulnérabilités npm absent"], {}
    for field in (*SEVERITIES, "total"):
        value = stats.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            issues.append(f"compteur d'audit invalide : {field}")
        else:
            counts[field] = value
    if len(counts) != len(SEVERITIES) + 1:
        return issues, counts
    if sum(counts[name] for name in SEVERITIES) != counts["total"]:
        issues.append("somme des gravités incompatible avec le total de npm audit")
    if exit_status == 0 and counts["total"] > 0:
        issues.append("npm audit a retourné succès malgré des vulnérabilités")
    if exit_status == 1 and counts["total"] == 0:
        issues.append("npm audit a retourné erreur sans vulnérabilité documentée")
    if counts["critical"] or counts["high"]:
        issues.append(
            f"vulnérabilités élevées ou critiques interdites : "
            f"high={counts['high']}, critical={counts['critical']}"
        )
    return issues, counts


def self_test() -> None:
    def audit(low: int = 0, moderate: int = 0, high: int = 0, critical: int = 0):
        stats = {
            "info": 0, "low": low, "moderate": moderate,
            "high": high, "critical": critical,
            "total": low + moderate + high + critical,
        }
        return json.dumps({"metadata": {"vulnerabilities": stats}}).encode()

    passed = audit(low=2, moderate=16)
    if inspect(passed, 1)[0]:
        raise AssertionError("audit sans high ni critical refusé")
    clean = audit()
    if inspect(clean, 0)[0]:
        raise AssertionError("audit sans vulnérabilité refusé")
    mutants = {
        "high": (audit(high=1), 1),
        "critical": (audit(critical=1), 1),
        "npm failure": (passed, 2),
        "fichier vide": (b"", 1),
        "contenu non JSON": (b"{", 1),
        "npm error": (b'{"error":{"code":"EAUDITNOLOCK"}}', 1),
        "résumé absent": (b'{"metadata":{}}', 1),
        "résumé négatif": (audit().replace(b'"total": 0', b'"total": -1'), 0),
        "total falsifié": (audit(high=1).replace(b'"total": 1', b'"total": 0'), 1),
        "status incohérent positif": (passed, 0),
        "status incohérent négatif": (clean, 1),
        "booléen à la place du compteur": (
            audit(high=1).replace(b'"high": 1', b'"high": true'), 1
        ),
    }
    for label, (body, code) in mutants.items():
        if not inspect(body, code)[0]:
            raise AssertionError(f"mutation non détectée : {label}")
    print(f"OK: garde npm audit fail-closed et {len(mutants)} mutations adversariales.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path, nargs="?")
    parser.add_argument("--exit-status", type=int, default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.report is None or args.exit_status is None:
        parser.error("fichier audit JSON et --exit-status obligatoires")
    try:
        payload = args.report.read_bytes()
    except OSError as exc:
        print(f"ERREUR: rapport audit inaccessible : {exc}")
        return 1
    issues, counts = inspect(payload, args.exit_status)
    if counts:
        print("Résultat npm audit : " + ", ".join(
            f"{name}={counts.get(name, '?')}" for name in (*SEVERITIES, "total")
        ))
    for issue in issues:
        print("ERREUR:", issue)
    if issues:
        return 1
    print("OK: aucune vulnérabilité npm élevée ou critique détectée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
