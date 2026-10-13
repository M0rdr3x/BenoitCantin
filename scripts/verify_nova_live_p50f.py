#!/usr/bin/env python3
"""Projet Nova P50F — verification publique en lecture seule, sans collecte.

Retour 0 : 4 pages conformes. Retour 2 : non conformite ou erreur reseau.
Ce controle ne confere aucune habilitation juridique ou electorale.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

BASE = "https://www.benoitcantin.com/projets/projet-nova/"
EXPECTED = {
    "participer.html": {
        "required": ["La participation citoyenne commence par un contact volontaire et limité",
                     "Les formulaires externes de soutien, de préadhésion et de signature sont suspendus"],
        "forbidden": ["qui contient le formulaire intégré de soutien et de préadhésion",
                      "Soutenir Projet Nova et accéder au formulaire de recrutement."],
    },
    "avis-legal.html": {
        "required": ["n’exploite actuellement pas de formulaire externe de participation ni de contact"],
        "forbidden": ["Les formulaires servent uniquement à communiquer avec le Projet Nova"],
    },
    "code-conduite.html": {
        "required": ["Gouvernance du Projet Nova | Projet Nova",
                     "Projet Nova prépare les règles démocratiques"],
        "forbidden": ["Gouvernance du Parti Nova | Projet Nova",
                      "Le Parti Nova doit être soumis à des règles démocratiques"],
    },
    "recrutement.html": {
        "required": ["Participer sans créer un dossier inutile", "contact volontaire direct", "Aucun paiement"],
        "forbidden": [],
    },
}

def normalized(body: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(body.replace("&nbsp;", " "))).strip()

def evaluate(name: str, body: str, status: int, final_url: str) -> dict:
    if name not in EXPECTED:
        raise ValueError("Page non autorisee")
    text = normalized(body)
    issues = []
    requested = urlparse(BASE + name)
    dest = urlparse(final_url)
    if status != 200:
        issues.append("HTTP " + str(status))
    if dest.scheme != requested.scheme or dest.netloc != requested.netloc or dest.path != requested.path:
        issues.append("Hote, protocole ou chemin final inattendu")
    for value in EXPECTED[name]["required"]:
        if value not in text:
            issues.append("Mention absente : " + value)
    for value in EXPECTED[name]["forbidden"]:
        if value in text:
            issues.append("Ancienne mention maintenue : " + value)
    if name in ("participer.html", "recrutement.html", "avis-legal.html"):
        if re.search(r"<form\b", body, flags=re.IGNORECASE):
            issues.append("Formulaire HTML present")
        if re.search(r"formspree\.io/f/|formsubmit\.co", body, flags=re.IGNORECASE):
            issues.append("Fournisseur de formulaire externe present")
    return {
        "page": name,
        "url_attendue": BASE + name,
        "url_finale": final_url,
        "http_status": status,
        "sha256_page": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "resultat": "CONFORME" if not issues else "NON_CONFORME",
        "ecarts": issues,
    }

def read_public(url: str) -> tuple[str, int, str]:
    # Domaine et chemins sont fixes dans EXPECTED; pas de cible configurable.
    request = urllib.request.Request(url, headers={"User-Agent": "ProjetNovaVerificationPublique/1.0"})
    with urllib.request.urlopen(request, timeout=18) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError("Page trop volumineuse")
        return data.decode(charset, errors="replace"), response.status, response.geturl()

def run() -> dict:
    pages = []
    for name in EXPECTED:
        url = BASE + name
        try:
            body, code, destination = read_public(url)
            pages.append(evaluate(name, body, code, destination))
        except (urllib.error.URLError, TimeoutError, ValueError, UnicodeError) as ex:
            pages.append({
                "page": name, "url_attendue": url,
                "resultat": "ERREUR_RESEAU",
                "ecarts": [str(ex)[:160]],
            })
    ok = sum(p["resultat"] == "CONFORME" for p in pages)
    return {
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "objet": "Recette technique publique de quatre pages, sans effet legal",
        "statut": "PUBLIÉ_ET_CONFORME" if ok == len(EXPECTED) else "NON_PRET_PUBLICATION",
        "pages_conformes": ok, "pages_verifiees": len(EXPECTED), "pages": pages,
        "limites": "Aucun effet sur W0, W1, le statut juridique ou l'autorisation electorale.",
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    report = run()
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(payload, encoding="utf-8")
    print(payload)
    return 0 if report["statut"] == "PUBLIÉ_ET_CONFORME" else 2

if __name__ == "__main__":
    sys.exit(main())
