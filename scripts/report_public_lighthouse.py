#!/usr/bin/env python3
"""Mesurer les pages publiques avant de fixer des seuils par parcours."""
import json
import re
from urllib.parse import urlsplit
import sys
from pathlib import Path
from check_lighthouse import THRESHOLDS, METRICS, valid_number


def local_resource_details(audit, expected_url):
    """Limiter la sortie aux ressources statiques locales et à leurs mesures."""
    origin = urlsplit(expected_url)
    pending = [audit.get("details", {})]
    seen = set()
    rows = []
    visited = 0
    while pending and visited < 2000 and len(rows) < 15:
        item = pending.pop()
        visited += 1
        if isinstance(item, list):
            pending.extend(reversed(item[:100]))
        elif isinstance(item, dict):
            url = item.get("url")
            if isinstance(url, str):
                parsed = urlsplit(url)
                path = parsed.path
                if ((parsed.scheme, parsed.netloc) == (origin.scheme, origin.netloc)
                        and re.fullmatch(r"/(?:assets/(?:css|js|media|icons)/[a-zA-Z0-9._-]+|projets/sinjira/(?:[a-zA-Z0-9_-]+/)*[a-zA-Z0-9._-]+\.css)", path)
                        and path not in seen):
                    seen.add(path)
                    row = {"path": path}
                    for key in ("wastedBytes", "totalBytes", "wastedMs", "duration",
                                "transferSize", "resourceSize"):
                        value = item.get(key)
                        if valid_number(value, float("inf")):
                            row[key] = round(value, 2)
                    rows.append(row)
            pending.extend(v for k, v in item.items()
                           if k in ("items", "subItems", "details") and isinstance(v, (dict, list)))
    return rows


def target_diagnostics(audit):
    """Ne retourner que des sélecteurs CSS simples et les dimensions numériques.
    Aucun texte, extrait HTML, URL, valeur d'attribut ni identifiant de compte."""
    rows = []
    seen = set()
    details = audit.get("details")
    if not isinstance(details, dict):
        return rows
    for item in details.get("items", [])[:30]:
        if not isinstance(item, dict):
            continue
        for key in ("node", "overlappingNode"):
            node = item.get(key)
            if not isinstance(node, dict):
                continue
            selector = node.get("selector")
            if (not isinstance(selector, str) or len(selector) > 240
                    or not re.fullmatch(r"[a-zA-Z0-9_.#>+~ :()-]+", selector)
                    or selector in seen):
                continue
            seen.add(selector)
            row = {"role": key, "selector": selector}
            rect = node.get("boundingRect", {})
            if isinstance(rect, dict):
                for dimension in ("width", "height"):
                    value = rect.get(dimension)
                    if valid_number(value, 100000):
                        row[dimension] = round(value, 2)
            rows.append(row)
    return rows


def self_test():
    fixture = {"details": {"items": [
        {"node": {"selector": "footer > div.footer-col > a:nth-child(2)",
                  "boundingRect": {"width": 90, "height": 18},
                  "snippet": "PRIVATE_TEST"}},
        {"node": {"selector": "a[href='private-test']"}},
    ]}}
    rows = target_diagnostics(fixture)
    assert len(rows) == 1 and rows[0]["height"] == 18
    assert "PRIVATE_TEST" not in json.dumps(rows)
    assert local_resource_details(
        {"details": {"items": [{"url": "http://127.0.0.1:4173/projets/sinjira/sinjira.css?v=1"}]}},
        "http://127.0.0.1:4173/projets/sinjira/"
    ) == [{"path": "/projets/sinjira/sinjira.css"}]


def main():
    if len(sys.argv) != 3:
        print("Usage: report_public_lighthouse.py <rapport.json> <URL locale attendue>")
        return 2
    self_test()
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
            if audit_id in ("image-delivery-insight", "render-blocking-insight", "bootup-time"):
                for row in local_resource_details(audit, sys.argv[2]):
                    print(f"RESOURCE {audit_id}: {json.dumps(row, sort_keys=True)}")
        for ref in categories["accessibility"].get("auditRefs", []):
            audit_id = ref.get("id", "")
            if not isinstance(audit_id, str) or not re.fullmatch(r"[a-z0-9-]{1,100}", audit_id):
                continue
            score = audits.get(audit_id, {}).get("score")
            weight = ref.get("weight", 0)
            if valid_number(score, 1) and score < 1 and valid_number(weight, float("inf")) and weight > 0:
                print(f"ACCESSIBILITY {audit_id}: {score}")
                if audit_id == "target-size":
                    for row in target_diagnostics(audits[audit_id]):
                        print(f"TARGET {json.dumps(row, sort_keys=True)}")
        # Les écarts sont diagnostiques; une mesure manquante reste bloquante.
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ECHEC diagnostic : {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
