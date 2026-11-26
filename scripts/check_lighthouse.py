#!/usr/bin/env python3
"""Contrat de performance mobile : empêcher les régressions silencieuses."""
import json
import math
import sys
from pathlib import Path

# Seuils de recette (marge CI), distincts des objectifs terrain Core Web Vitals.
THRESHOLDS = {
    "performance": 0.90,
    "accessibility": 0.95,
    "best-practices": 0.95,
    "seo": 0.95,
}
METRICS = {
    "largest-contentful-paint": 3500,
    "cumulative-layout-shift": 0.10,
    "total-blocking-time": 200,
}


def valid_number(value, maximum):
    return (type(value) in (int, float)
            and 0 <= value <= maximum and math.isfinite(value))


def validate(report, emit=print):
    failures = []
    if not isinstance(report, dict):
        return ["Rapport Lighthouse invalide."]
    if report.get("runtimeError"):
        failures.append("Lighthouse signale une erreur d'exécution.")
    categories = report.get("categories")
    audits = report.get("audits")
    if not isinstance(categories, dict) or not isinstance(audits, dict):
        return failures + ["Rapport Lighthouse incomplet."]
    for name, minimum in THRESHOLDS.items():
        category = categories.get(name)
        score = category.get("score") if isinstance(category, dict) else None
        if not valid_number(score, 1):
            failures.append(f"{name}: score absent ou invalide")
            continue
        pct = round(score * 100)
        emit(f"{name}: {pct}% (minimum {round(minimum * 100)}%)")
        if score < minimum:
            failures.append(f"{name}: {pct}% < {round(minimum * 100)}%")

    for audit_id, maximum in METRICS.items():
        audit = audits.get(audit_id)
        numeric = audit.get("numericValue") if isinstance(audit, dict) else None
        if not valid_number(numeric, float("inf")):
            failures.append(f"{audit_id}: mesure absente ou invalide")
            continue
        if audit_id == "cumulative-layout-shift":
            emit(f"CLS: {numeric:.3f} (maximum {maximum})")
        else:
            emit(f"{audit_id}: {round(numeric)} ms (maximum {maximum} ms)")
        if numeric > maximum:
            failures.append(f"{audit_id}: {numeric:.3f} > {maximum}")
    return failures


def diagnostic_metrics(report, emit=print):
    """Diagnostics numériques bornés, sans URL, DOM ou contenu utilisateur."""
    audits = report.get("audits", {})
    if not isinstance(audits, dict):
        return
    for audit_id in ("mainthread-work-breakdown", "bootup-time", "long-tasks",
                     "render-blocking-insight", "image-delivery-insight"):
        audit = audits.get(audit_id)
        if not isinstance(audit, dict):
            continue
        value = audit.get("numericValue")
        if valid_number(value, float("inf")):
            emit(f"DIAGNOSTIC {audit_id}: {value:.2f}")
        savings = audit.get("metricSavings")
        if isinstance(savings, dict):
            for metric in ("LCP", "FCP", "TBT", "CLS", "INP"):
                value = savings.get(metric)
                if valid_number(value, float("inf")):
                    emit(f"DIAGNOSTIC {audit_id} {metric}: {value:.2f}")


def self_test():
    def good():
        return {
            "categories": {name: {"score": value} for name, value in THRESHOLDS.items()},
            "audits": {name: {"numericValue": value} for name, value in METRICS.items()},
        }
    quiet = lambda _: None
    assert not validate(good(), quiet), "Les limites inclusives doivent être acceptées."
    for name, minimum in THRESHOLDS.items():
        report = good()
        report["categories"][name]["score"] = minimum - 0.01
        assert validate(report, quiet), name
        for invalid in (None, True, "0.95", -1, 1.1, float("nan"), float("inf")):
            report = good()
            report["categories"][name]["score"] = invalid
            assert validate(report, quiet), (name, invalid)
    for name, maximum in METRICS.items():
        report = good()
        report["audits"][name]["numericValue"] = maximum + 0.001
        assert validate(report, quiet), name
        for invalid in (None, False, "0", -1, float("nan"), float("inf")):
            report = good()
            report["audits"][name]["numericValue"] = invalid
            assert validate(report, quiet), (name, invalid)
        report = good()
        del report["audits"][name]
        assert validate(report, quiet), name
    report = good()
    report["runtimeError"] = {"code": "TEST_ERROR"}
    assert validate(report, quiet), "Erreur d'exécution non détectée."
    assert validate({}, quiet) and validate([], quiet)
    diagnostics = []
    diagnostic_metrics({"audits": {"bootup-time": {
        "numericValue": 300, "metricSavings": {"TBT": 100, "secret": 9},
        "details": {"url": "https://example.invalid/?secret=1"}}}}, diagnostics.append)
    assert diagnostics == ["DIAGNOSTIC bootup-time: 300.00",
                           "DIAGNOSTIC bootup-time TBT: 100.00"]
    print("OK auto-tests du contrat Lighthouse : limites, mesures absentes et rapports invalides.")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_lighthouse.py <rapport.json> ou --self-test")
        return 2
    self_test()
    if sys.argv[1] == "--self-test":
        return 0
    try:
        report = json.loads(Path(sys.argv[1]).read_text("utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ECHEC Lighthouse : rapport illisible ({exc})")
        return 1
    failures = validate(report)
    if failures:
        if isinstance(report, dict):
            diagnostic_metrics(report)
        print("ECHEC Lighthouse mobile:")
        for item in failures:
            print("- " + item)
        return 1
    print("OK Lighthouse mobile: performance, accessibilité, bonnes pratiques, SEO et métriques de stabilité sous contrôle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
