#!/usr/bin/env python3
"""Contrôle technique et strict de quatre pages PUBLIQUES de Projet Nova."""
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
from urllib.parse import urljoin, urlsplit

BASE_URL = "https://www.benoitcantin.com/projets/projet-nova/"
EXPECTED_HOST = "www.benoitcantin.com"
PREFIX = "/projets/projet-nova/"
PAGES = {
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
        "forbidden": ("qui contient le formulaire intégré de soutien et de préadhésion",),
    },
}


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value.replace("&nbsp;", " "))).strip()


def exact_public_url(url: str, name: str) -> bool:
    parsed = urlsplit(url)
    return (parsed.scheme == "https" and parsed.netloc.lower() == EXPECTED_HOST
            and parsed.path == PREFIX + name and not parsed.query and not parsed.fragment
            and parsed.username is None and parsed.password is None)


def evaluate(name: str, body: str, status: int, final_url: str,
             content_type: str = "text/html") -> dict:
    if name not in PAGES:
        raise ValueError("Page hors périmètre.")
    text = normalize(body)
    gaps = []
    if status != 200:
        gaps.append(f"HTTP {status}")
    if not exact_public_url(final_url, name):
        gaps.append("Origine HTTPS ou chemin final inattendu.")
    if not content_type.lower().startswith(("text/html", "application/xhtml+xml")):
        gaps.append("Content-Type non HTML.")
    if not re.search(r"<html\b", body, flags=re.IGNORECASE):
        gaps.append("Corps HTML non reconnaissable.")
    for marker in PAGES[name]["required"]:
        if marker not in text:
            gaps.append("Marqueur requis absent : " + marker)
    for marker in PAGES[name]["forbidden"]:
        if marker in text:
            gaps.append("Ancienne formulation présente : " + marker)
    if name in ("participer.html", "avis-legal.html", "recrutement.html"):
        if re.search(r"<form\b", body, flags=re.IGNORECASE):
            gaps.append("Formulaire HTML actif à examiner.")
    return {"page": name, "url_finale": final_url, "statut_http": status,
            "content_type": content_type, "sha256_html": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "resultat": "CONFORME_TECHNIQUE" if not gaps else "ECART", "ecarts": gaps}


class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        name = urlsplit(req.full_url).path.rsplit("/", 1)[-1]
        if not exact_public_url(newurl, name):
            raise urllib.error.URLError("Redirection refusée hors du chemin public attendu.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(name: str) -> tuple[str, int, str, str]:
    opener = urllib.request.build_opener(StrictRedirect())
    request = urllib.request.Request(urljoin(BASE_URL, name), headers={
        "User-Agent": "ProjetNovaAuditP50F/1.0 (lecture publique)",
        "Cache-Control": "no-cache", "Pragma": "no-cache",
        "Accept": "text/html,application/xhtml+xml",
    })
    with opener.open(request, timeout=15) as response:
        body = response.read(1_500_001)
        if len(body) > 1_500_000:
            raise ValueError("Page au-delà de 1,5 Mo.")
        charset = response.headers.get_content_charset() or "utf-8"
        return body.decode(charset, errors="replace"), response.status, response.geturl(), response.headers.get("Content-Type", "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Recette lecture seule du site public Projet Nova.")
    parser.add_argument("--json-output", type=Path, default=Path("nova_publication_p50f.json"))
    parser.add_argument("--offline", action="store_true", help="N'effectue aucune requête; pages NON_VERIFIEES.")
    args = parser.parse_args()
    results = []
    for name in PAGES:
        url = urljoin(BASE_URL, name)
        if args.offline:
            results.append({"page": name, "url_finale": url, "resultat": "NON_VERIFIE", "ecarts": ["Mode hors ligne."]})
            continue
        try:
            results.append(evaluate(name, *fetch(name)))
        except (urllib.error.URLError, TimeoutError, UnicodeError, ValueError) as exc:
            results.append({"page": name, "url_finale": url, "resultat": "ERREUR_RESEAU",
                            "ecarts": [str(exc)[:180]]})
    passed = sum(x["resultat"] == "CONFORME_TECHNIQUE" for x in results)
    report = {"date_utc": datetime.now(timezone.utc).isoformat(),
              "decision_technique": "VERIFICATION_TECHNIQUE_REUSSIE" if passed == len(PAGES) else "PUBLICATION_NON_CONFIRMEE",
              "pages_conformes": passed, "pages_total": len(PAGES), "pages": results,
              "limites": "Contrôle HTTP seulement : pas d'autorisation électorale, W0 NON_CLOTUREE, W1 NO_GO."}
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed == len(PAGES) else 2


if __name__ == "__main__":
    sys.exit(main())
