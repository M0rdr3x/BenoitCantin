#!/usr/bin/env python3
import json
import sys
from pathlib import Path

THRESHOLDS = {
    "performance": 0.75,
    "accessibility": 0.90,
    "best-practices": 0.85,
    "seo": 0.90,
}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_lighthouse.py <rapport.json>")
        return 2
    report_path = Path(sys.argv[1])
    report = json.loads(report_path.read_text("utf-8"))
    categories = report.get("categories", {})
    failures = []
    for name, minimum in THRESHOLDS.items():
        score = categories.get(name, {}).get("score")
        if score is None:
            failures.append(f"{name}: score absent")
            continue
        pct = round(score * 100)
        print(f"{name}: {pct}% (minimum {round(minimum * 100)}%)")
        if score < minimum:
            failures.append(f"{name}: {pct}% < {round(minimum * 100)}%")

    audits = report.get("audits", {})
    metrics = {
        "largest-contentful-paint": 4500,
        "cumulative-layout-shift": 0.25,
        "total-blocking-time": 600,
    }
    for audit_id, maximum in metrics.items():
        numeric = audits.get(audit_id, {}).get("numericValue")
        if numeric is None:
            continue
        # CLS est sans unité; LCP/TBT sont en millisecondes.
        if audit_id == "cumulative-layout-shift":
            print(f"CLS: {numeric:.3f} (maximum {maximum})")
        else:
            print(f"{audit_id}: {round(numeric)} ms (maximum {maximum} ms)")
        if numeric > maximum:
            failures.append(f"{audit_id}: {numeric:.3f} > {maximum}")

    if failures:
        print("ECHEC Lighthouse mobile:")
        for item in failures:
            print("- " + item)
        return 1
    print("OK Lighthouse mobile: performance, accessibilité, bonnes pratiques, SEO et métriques de stabilité sous contrôle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
