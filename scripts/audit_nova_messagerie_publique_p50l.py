#!/usr/bin/env python3
"""P50L — audit documentaire des pages HTML publiques, sans réseau ni boîte courriel.
La CI peut réussir tout en signalant des écarts éditoriaux existants.
"""
import argparse
from collections import Counter
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

PAGES = ("contact.html", "recrutement.html", "confidentialite.html",
         "participer.html", "avis-legal.html")
REQUIRED = {
    "contact.html": ("contact",),
    "recrutement.html": ("participer",),
    "confidentialite.html": ("renseignement",),
    "participer.html": ("participation",),
    "avis-legal.html": ("projet nova",),
}
OLD_CLAIMS = {
    "participer.html": ("formulaire intégré de soutien et de préadhésion",),
    "avis-legal.html": ("les formulaires servent uniquement à communiquer",),
}
EXTERNAL_FORMS = re.compile(
    r"(?:formspree\.io|forms\.gle|docs\.google\.com/forms|typeform\.com|jotform\.com)",
    re.I)
SENSITIVE_PAYMENTS = re.compile(r"(?:checkout\.stripe\.com|paypal\.com/donate)", re.I)

class Scanner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.form_count = 0
        self.mailto_count = 0
        self.external_forms = 0
        self.payment_links = 0
        self.parts = []
        self.target_count = 0
        self._scripts = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.form_count += 1
        if tag == "script":
            self._scripts = True
        for key in ("href", "src", "action", "formaction", "data-url"):
            value = attrs.get(key)
            if not isinstance(value, str):
                continue
            self.target_count += 1
            if value.strip().lower().startswith("mailto:"):
                self.mailto_count += 1
            if EXTERNAL_FORMS.search(value):
                self.external_forms += 1
            if SENSITIVE_PAYMENTS.search(value):
                self.payment_links += 1
    def handle_endtag(self, tag):
        if tag == "script":
            self._scripts = False
    def handle_data(self, data):
        if not self._scripts:
            self.parts.append(data)

def inspect_page(name, html):
    if name not in PAGES:
        raise ValueError("PAGE_HORS_PERIMETRE")
    scan = Scanner()
    scan.feed(html)
    normalized = " ".join(" ".join(scan.parts).lower().split())
    old = [i for i, value in enumerate(OLD_CLAIMS.get(name, ()))
           if value in normalized]
    expected = all(token in normalized for token in REQUIRED[name])
    return {
        "page": name,
        "lecture": "SOURCE_HTML_LOCALE_SEULEMENT",
        "liens_courriel_compte": scan.mailto_count,
        "balises_formulaire_compte": scan.form_count,
        "liens_vers_formulaires_externes_compte": scan.external_forms,
        "liens_de_paiement_sensibles_compte": scan.payment_links,
        "marqueurs_redactionnels_obsoletes": len(old),
        "texte_minimal_present": expected,
        "alerte_redactionnelle": bool(old),
        "alerte_surface_technique": bool(scan.form_count or scan.external_forms or scan.payment_links),
        "preuve_de_fonctionnement_messagerie": False,
        "preuve_de_mise_en_ligne": False,
    }

def inspect_model(data):
    issues = []
    if not isinstance(data, dict):
        return ["MODELE_ABSENT_OU_INVALIDE"]
    if data.get("schema_version") != "P50L-1" or data.get("type") != "MODELE_PUBLIC_NON_PROBANT":
        issues.append("MAUVAIS_SCHEMA")
    if data.get("identity") != "Projet Nova" or data.get("future_identity_conditional") != "Parti Nova":
        issues.append("IDENTITE_INVALIDE")
    if data.get("decision") != "NO_GO":
        issues.append("AUTORISATION_INTERDITE")
    try:
        date.fromisoformat(data.get("observation_date", ""))
    except (ValueError, TypeError):
        issues.append("DATE_INVALIDE")
    if not isinstance(data.get("main_sha"), str) or not re.fullmatch(r"[a-f0-9]{40}", data["main_sha"]):
        issues.append("SHA_MAIN_INVALIDE")
    constraints = data.get("constraints")
    expected = (
        "inbox_read", "messages_collected", "real_evidence_authenticated",
        "mailbox_provider_verified", "mailbox_location_verified",
        "mailbox_retention_verified", "privacy_officer_mandate_verified",
        "legal_regime_verified", "formal_efvp_signed", "deployment_proven",
        "form_reactivation_authorized", "financial_collection_authorized",
    )
    if (not isinstance(constraints, dict)
        or set(constraints) != set(expected)
        or any((type(constraints[k]) is not int or constraints[k] != 0) if
               k in ("messages_collected", "real_evidence_authenticated")
               else constraints[k] is not False for k in expected)):
        issues.append("PREUVE_OU_ACCES_REEL_FAUSSEMENT_ATTESTE")
    guards = data.get("frozen_guards")
    required_guards = {
        "NE_PAS_FUSIONNER_PR_640", "AUCUN_FORMULAIRE_REACTIVE",
        "AUCUN_MESSAGE_PRIVE_OU_JOURNAL_DANS_GITHUB", "CI_NON_EQUIVALENT_AUTORISATION",
        "V3_40_INCHANGEE", "NO_GO_PREUVES_NON_ATTESTEES",
    }
    if not isinstance(guards, list) or len(guards) != 6 or set(guards) != required_guards:
        issues.append("GARDE_FOU_MANQUANT")
    rows = data.get("requirements")
    if not isinstance(rows, list) or len(rows) != 12:
        issues.append("EXIGENCES_INCOMPLETES")
    else:
        codes = set()
        for row in rows:
            if not isinstance(row, dict):
                issues.append("EXIGENCE_NON_OBJET")
                continue
            code = row.get("id")
            if code not in {f"M{i:02d}" for i in range(1, 13)} or code in codes:
                issues.append("CODE_INVALIDE_OU_DUPLIQUE")
                continue
            codes.add(code)
            if (set(row) != {
                "id", "topic", "role_target", "state", "private_evidence_received",
                "verified_real_world", "public_evidence_reference",
            } or row.get("state") != "NON_DOCUMENTE"
                or row.get("private_evidence_received") is not False
                or row.get("verified_real_world") is not False
                or row.get("public_evidence_reference") != ""
                or not isinstance(row.get("topic"), str)
                or not isinstance(row.get("role_target"), str)):
                issues.append("EXIGENCE_FAUSSEMENT_ATTESTEE_" + code)
        if len(codes) != 12:
            issues.append("EXIGENCES_INCOMPLETES")
    pages = data.get("source_pages")
    if (not isinstance(pages, list) or len(pages) != len(PAGES) or
        {x.get("page") for x in pages if isinstance(x, dict)} != set(PAGES) or
        any(not isinstance(x, dict) or not re.fullmatch(r"[a-f0-9]{40}", x.get("sha", ""))
            for x in pages)):
        issues.append("SOURCES_NON_VERIFIABLES")
    return sorted(set(issues))

def run(source_root, model):
    base = Path(source_root) / "projets/projet-nova"
    result = []
    for name in PAGES:
        try:
            result.append(inspect_page(name, (base / name).read_text(encoding="utf-8")))
        except (OSError, UnicodeError, ValueError):
            result.append({"page": name, "lecture": "INDISPONIBLE",
                           "alerte_redactionnelle": None,
                           "alerte_surface_technique": None,
                           "preuve_de_fonctionnement_messagerie": False,
                           "preuve_de_mise_en_ligne": False})
    issues = inspect_model(model)
    missing = [v["page"] for v in result if v["lecture"] == "INDISPONIBLE"]
    return {
        "jalon": "P50L", "source": "FICHIERS_LOCAUX_NON_HTTP",
        "pages": result,
        "modele_structurel": "VALIDE" if not issues else "INVALIDE",
        "problemes_modele": issues,
        "pages_absentes": missing,
        "pages_avec_alertes_redactionnelles": [r["page"] for r in result
                                               if r.get("alerte_redactionnelle") is True],
        "pages_avec_surface_de_collecte": [r["page"] for r in result
                                           if r.get("alerte_surface_technique") is True],
        "messagerie_effectivement_auditee": False,
        "efvp_signee": False, "autorisation_juridique_verifiee": False,
        "decision": "NO_GO_AUTOMATIQUE",
        "verification_executable": "OK_LECTURE_SEULE" if not missing and not issues
                                 else "INCOMPLETE_OU_INVALIDE",
        "limite": "L'execution du script et une CI verte ne prouvent ni conformité ni déploiement.",
    }

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--modele", type=Path)
    p.add_argument("--rapport", type=Path)
    args = p.parse_args(argv)
    path = args.modele or (args.repo / "projets/projet-nova/controles/P50L_REGISTRE_PUBLIC_12_VERIFICATIONS.json")
    try:
        model = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        model = None
    report = run(args.repo, model)
    out = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True, exist_ok=True)
        args.rapport.write_text(out, encoding="utf-8")
    else:
        print(out, end="")
    return 0 if report["verification_executable"] == "OK_LECTURE_SEULE" else 2

if __name__ == "__main__":
    sys.exit(main())
