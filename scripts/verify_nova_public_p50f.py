#!/usr/bin/env python3
"""Contrôle POSTPUBLICATION en lecture seule — Projet Nova.

Ce programme évalue le contenu effectivement servi par quatre URL publiques.
Il ne modifie aucune page, ne soumet aucun formulaire et ne certifie aucun
statut juridique, politique, électoral ou W0/W1.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

BASE = "https://www.benoitcantin.com/projets/projet-nova/"
EXPECT = {
    "participer.html": {
        "required": ("La participation citoyenne commence par un contact volontaire et limité",
                     "Les formulaires externes de soutien, de préadhésion et de signature sont suspendus"),
        "forbidden": ("qui contient le formulaire intégré de soutien et de préadhésion",
                      "Soutenir Projet Nova et accéder au formulaire de recrutement."),
    },
    "avis-legal.html": {
        "required": ("n’exploite actuellement pas de formulaire externe de participation ni de contact",),
        "forbidden": ("Les formulaires servent uniquement à communiquer avec le Projet Nova",),
    },
    "code-conduite.html": {
        "required": ("Gouvernance du Projet Nova | Projet Nova",
                     "Projet Nova prépare les règles démocratiques"),
        "forbidden": ("Gouvernance du Parti Nova | Projet Nova",
                      "Le Parti Nova doit être soumis à des règles démocratiques"),
    },
    "recrutement.html": {
        "required": ("Participer sans créer un dossier inutile", "contact volontaire direct", "Aucun paiement"),
        "forbidden": (),
    },
}
ACTIVE_FORM_PAGES = {"participer.html", "avis-legal.html", "recrutement.html"}


def normalize(body: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(body.replace("&nbsp;", " "))).strip()


def evaluate(name: str, body: str, status: int, final_url: str, content_type: str = "text/html") -> dict:
    if name not in EXPECT:
        raise ValueError("Page hors du périmètre autorisé")
    expected_url = BASE + name
    problems = []
    content = normalize(body)
    if status != 200:
        problems.append(f"HTTP {status}")
    if content_type.split(";")[0].lower().strip() not in ("text/html", "application/xhtml+xml"):
        problems.append("Réponse non HTML")
    parsed = urlparse(final_url)
    if parsed.scheme != "https" or parsed.netloc != urlparse(BASE).netloc or parsed.path != urlparse(expected_url).path:
        problems.append("Redirection ou origine inattendue")
    for term in EXPECT[name]["required"]:
        if term not in content:
            problems.append(f"Marqueur attendu absent : {term}")
    for term in EXPECT[name]["forbidden"]:
        if term in content:
            problems.append(f"Ancienne formulation encore visible : {term}")
    if name in ACTIVE_FORM_PAGES:
        if re.search(r"<form\b", body, re.IGNORECASE):
            problems.append("Formulaire HTML à revoir")
        if re.search(r"formspree\.io/f/|formsubmit\.co/", body, re.IGNORECASE):
            problems.append("Point de collecte externe visible")
    return {"page": name, "url": final_url, "http_status": status,
            "sha256_html": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "etat": "CONFORME" if not problems else "NON_CONFORME", "ecarts": problems}


def fetch(name: str) -> tuple[str, int, str, str]:
    if name not in EXPECT:
        raise ValueError("Page non autorisée")
    request = urllib.request.Request(BASE + name, headers={
        "User-Agent": "ProjetNovaPostPublication/1.0 (+controle-public)",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    with urllib.request.urlopen(request, timeout=20, context=ssl.create_default_context()) as response:
        data = response.read(1_500_001)
        if len(data) > 1_500_000:
            raise ValueError("Page plus grande que la limite de contrôle")
        encoding = response.headers.get_content_charset() or "utf-8"
        return data.decode(encoding, errors="replace"), response.status, response.geturl(), response.headers.get("Content-Type", "")


def run(fetcher=fetch) -> dict:
    checks = []
    for name in EXPECT:
        try:
            body, status, url, content_type = fetcher(name)
            checks.append(evaluate(name, body, status, url, content_type))
        except urllib.error.HTTPError as exc:
            checks.append({"page": name, "url": BASE + name, "http_status": exc.code,
                           "etat": "NON_CONFORME", "ecarts": [f"HTTP {exc.code}"]})
        except (urllib.error.URLError, OSError, TimeoutError, ValueError, UnicodeError) as exc:
            checks.append({"page": name, "url": BASE + name,
                           "etat": "ERREUR_RESEAU", "ecarts": [type(exc).__name__]})
    valid = sum(item["etat"] == "CONFORME" for item in checks)
    return {
        "controle": "P50F — site public Projet Nova",
        "horodatage_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "4 pages publiques, lecture seule, aucun formulaire soumis",
        "statut": "PUBLIÉ_ET_CONFORME" if valid == len(EXPECT) else "NON_CONFORME_OU_NON_PUBLIE",
        "pages_conformes": valid,
        "pages_attendues": len(EXPECT),
        "pages": checks,
        "limites": "Preuve technique de pages HTTP. Ne vaut ni approbation éditoriale humaine, ni autorisation électorale, ni clôture W0/W1."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Vérifier la publication des correctifs éditoriaux Projet Nova.")
    parser.add_argument("--output", type=Path, default=Path("artifacts/nova_publication_p50f.json"))
    args = parser.parse_args()
    report = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"État: {report['statut']} ({report['pages_conformes']}/{report['pages_attendues']})")
    for page in report["pages"]:
        print(f"- {page['page']}: {page['etat']} ({len(page['ecarts'])} écart(s))")
    print(f"Rapport: {args.output}")
    return 0 if report["statut"] == "PUBLIÉ_ET_CONFORME" else 2


if __name__ == "__main__":
    sys.exit(main())
