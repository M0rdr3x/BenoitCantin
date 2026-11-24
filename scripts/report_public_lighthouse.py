#!/usr/bin/env python3
"""Mesurer les pages publiques avant de fixer des seuils par parcours."""
import json
import sys
from pathlib import Path
from check_lighthouse import THRESHOLDS, METRICS, valid_number


def main():
    if len(sys.argv) != 3:
        print("Usage: report_public_lighthouse.py <rapport.json> <URL locale attendue>")
        return 2
    try:
        report = json.loads(Path(sys.argv[1]).read_text("utf-8"))
        if not isinstance(report, dict) or report.get("runtimeError"):
            raise ValueError("Rapport invalide ou erreur Lighthouse")
        if report.get("requestedUrl") != sys.argv[2] or report.get("finalDisplayedUrl") != sys.argv[2]:
            raise ValueError("URL auditée différente de la page attendue")
        categories = report["categories"]
        audits = report["audits"]
        deviations = []
        print("BASELINE " + sys.argv[2])
        for name, threshold in THRESHOLDS.items():
            value = categories[name]["score"]
            if not valid_number(value, 1):
                raise ValueError(f"Score invalide : {name}")
            print(f"BASELINE {name}: {value * 100:.0f}%")
            if value < threshold:
                deviations.append(name)
        for name, threshold in METRICS.items():
            value = audits[name]["numericValue"]
            if not valid_number(value, float("inf")):
                raise ValueError(f"Mesure invalide : {name}")
            print(f"BASELINE {name}: {value:.3f}")
            if value > threshold:
                deviations.append(name)
        print("BASELINE écarts aux objectifs accueil : " + (", ".join(deviations) or "aucun"))
        # Rendre les principaux diagnostics actionnables sans journaliser les URL
        # externes, les données de formulaire, les chaînes de requête ou le DOM.
        for audit_id in ("lcp-breakdown-insight", "lcp-discovery-insight",
                         "render-blocking-insight", "image-delivery-insight",
                         "mainthread-work-breakdown", "bootup-time",
                         "long-tasks", "layout-shift-elements"):
            audit = audits.get(audit_id)
            if not isinstance(audit, dict):
                continue
            score = audit.get("score")
            numeric = audit.get("numericValue")
            savings = audit.get("metricSavings")
            safe = {}
            if valid_number(score, 1):
                safe["score"] = score
            if valid_number(numeric, float("inf")):
                safe["numericValue"] = round(numeric, 2)
            if isinstance(savings, dict):
                safe["metricSavings"] = {k: round(v, 2) for k, v in savings.items()
                                         if k in ("LCP", "FCP", "TBT", "CLS", "INP")
                                         and valid_number(v, float("inf"))}
            if safe:
                print(f"DETAIL {audit_id}: {json.dumps(safe, sort_keys=True)}")
        # Les écarts sont diagnostiques; une mesure manquante reste bloquante.
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ECHEC diagnostic : {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
