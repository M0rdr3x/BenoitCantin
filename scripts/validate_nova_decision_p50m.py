#!/usr/bin/env python3
"""Projet Nova P50M: vérification STRICTEMENT DOCUMENTAIRE d'un instantané GitHub.
Ne contacte aucun service. Ne vérifie aucune pièce privée. Ne délivre jamais GO.
"""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

PR_NUMBERS = (636,638,640,645,646,647,648,649,650,651)
CHECK_IDS = tuple("C%02d" % n for n in range(1,6))
Q_IDS = tuple("Q%02d" % n for n in range(1,10))
M_IDS = tuple("M%02d" % n for n in range(1,13))
B_IDS = tuple("B%02d" % n for n in range(1,15))
KNOWN_ZERO_REVIEWS = frozenset((636,638,650,651))
GUARDS = frozenset((
    "PR_640_NE_JAMAIS_FUSIONNER",
    "FORMULAIRES_EXTERNES_NON_REACTIVES",
    "AUCUNE_COLLECTE_ELECTORALE",
    "V3_40_NON_MODIFIEE",
    "AUCUNE_PREUVE_PRIVEE_DANS_GITHUB",
    "AUCUN_GO_PAR_TEST_AUTOMATIQUE",
))
SHA = re.compile(r"[0-9a-f]{40}\Z")
EXPECTED_BOOLEAN_FALSE = (
    "mailbox_technical_audit_performed",
    "personal_data_read_or_exported",
    "formal_legal_advice_authenticated",
    "privacy_review_authenticated",
    "deployment_operator_mandate_authenticated",
    "rollback_on_host_authenticated",
    "real_http_publication_validated",
    "official_electoral_authorization_authenticated",
    "real_human_decision_signed",
)

def validate(document: object) -> dict:
    issues = []
    if not isinstance(document, dict):
        return {"structure": "INVALIDE", "anomalies": ["RACINE_NON_OBJET"],
                "decision": "NO_GO_AUTOMATIQUE"}
    if document.get("schema_version") != "P50M-1.0":
        issues.append("SCHEMA_INVALIDE")
    if document.get("nature") != "MODELE_PUBLIC_DE_CONTROLE_NON_PROBANT":
        issues.append("NATURE_INVALIDE")
    try:
        date.fromisoformat(document.get("source_snapshot_date", ""))
    except (ValueError, TypeError):
        issues.append("DATE_INVALIDE")
    if document.get("source") != "GITHUB_CONNECTOR_READ_ONLY_NON_CONTINU":
        issues.append("SOURCE_NON_FIABLE_OU_MODIFIEE")
    if document.get("project_identity") != "Projet Nova" or document.get("future_conditional_identity") != "Parti Nova":
        issues.append("IDENTITE_INCORRECTE")
    if not isinstance(document.get("main_sha"), str) or not SHA.fullmatch(document["main_sha"]):
        issues.append("SHA_MAIN_INVALIDE")
    if document.get("runtime_status") != "NO_GO" or document.get("public_actions_authorized") != []:
        issues.append("AUTORISATION_NON_RECEVABLE")
    guards = document.get("guards")
    if not isinstance(guards, list) or len(guards) != len(GUARDS) or set(guards) != GUARDS:
        issues.append("GARDE_FOU_MANQUANT")
    if any(document.get(field) is not False for field in EXPECTED_BOOLEAN_FALSE):
        issues.append("FAUSSE_ATTESTATION_REELLE")
    prs = document.get("pull_requests")
    if not isinstance(prs, list) or len(prs) != len(PR_NUMBERS):
        issues.append("PR_MANQUANTES")
    else:
        seen = set()
        for p in prs:
            if not isinstance(p, dict):
                issues.append("PR_MAL_FORMEE"); continue
            number = p.get("number")
            if type(number) is not int or number not in PR_NUMBERS or number in seen:
                issues.append("PR_INCONNUE_OU_DUPLIQUEE"); continue
            seen.add(number)
            if not isinstance(p.get("head_sha"), str) or not SHA.fullmatch(p["head_sha"]):
                issues.append("SHA_PR_INVALIDE_" + str(number))
            if any(p.get(k) is not expected for k,expected in
                   (("open",True),("draft",True),("merged",False),
                    ("eligible_for_automatic_merge",False))):
                issues.append("PR_PROMUE_SANS_PREUVE_" + str(number))
            count = p.get("formal_reviews_observed")
            scope = p.get("review_count_verification")
            if number in KNOWN_ZERO_REVIEWS:
                if count != 0 or type(count) is not int or scope != "INTERROGE_SUR_GITHUB_LE_2026_10_14":
                    issues.append("REVUE_FICTIVE_" + str(number))
            elif count is not None or scope != "NON_VERIFIE_PAR_CE_RELEVE":
                issues.append("REVUE_NON_RELEVE_" + str(number))
        if seen != set(PR_NUMBERS):
            issues.append("PR_MANQUANTES")
    for field, ids, expected_status in (
        ("human_checks", CHECK_IDS, "NON_ATTESTE"),
        ("legal_evidence", Q_IDS, "NON_RECU"),
        ("mail_evidence", M_IDS, "NON_DOCUMENTE"),
        ("publication_gates", B_IDS, "NON_VALIDE"),
    ):
        rows = document.get(field)
        if not isinstance(rows, list) or len(rows) != len(ids):
            issues.append("REGISTRE_INCOMPLET_" + field)
            continue
        seen = set()
        for row in rows:
            if not isinstance(row, dict):
                issues.append("LIGNE_INVALIDE_" + field); continue
            rid = row.get("id")
            if rid not in ids or rid in seen:
                issues.append("IDENTIFIANT_INVALIDE_" + field); continue
            seen.add(rid)
            if row.get("status") != expected_status:
                issues.append("FAUSSE_ATTESTATION_" + rid)
            if field == "publication_gates":
                try:
                    phase = "POST" if int(rid[-2:]) in (12,14) else "PRE"
                except ValueError:
                    phase = "PRE"
                if row.get("phase") != phase:
                    issues.append("PHASE_INVALIDE_" + rid)
            if field == "human_checks" and (not isinstance(row.get("object"), str) or not row["object"]):
                issues.append("OBJET_MANQUANT_" + rid)
        if seen != set(ids):
            issues.append("REGISTRE_INCOMPLET_" + field)
    pages = document.get("known_editorial_gaps")
    if pages != ["participer.html", "avis-legal.html"]:
        issues.append("ECARTS_PUBLICS_MODIFIES")
    # The public document never contains identities, source documents or authentication artifacts.
    allowed = {
        "schema_version", "nature", "source_snapshot_date", "source", "main_sha",
        "project_identity", "future_conditional_identity", "pull_requests",
        "human_checks", "legal_evidence", "mail_evidence", "publication_gates",
        "known_editorial_gaps", *EXPECTED_BOOLEAN_FALSE, "runtime_status",
        "public_actions_authorized", "guards", "note",
    }
    if set(document) != allowed:
        issues.append("CHAMPS_PUBLICS_SUPPLEMENTAIRES_OU_MANQUANTS")
    return {
        "structure": "MODELE_VALIDE_NON_PROBANT" if not issues else "INVALIDE",
        "anomalies": sorted(set(issues)),
        "revues_reelles_authentifiees": 0,
        "mandats_reels_authentifies": 0,
        "pieces_reelles_authentifiees": 0,
        "audit_reel_de_messagerie_effectue": False,
        "verification_live_github_effectuee": False,
        "decision": "NO_GO_AUTOMATIQUE",
        "explication": "Le contrôle de schéma ne certifie ni les faits externes ni une autorisation."
    }

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registre", type=Path, default=Path(__file__).resolve().parents[1] /
       "projets/projet-nova/controles/P50M_ETAT_PUBLIC_DECISION.json")
    p.add_argument("--rapport", type=Path)
    a = p.parse_args(argv)
    try:
        result = validate(json.loads(a.registre.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError):
        result = {"structure": "INVALIDE", "anomalies": ["REGISTRE_ABSENT_OU_ILLISIBLE"],
                  "decision": "NO_GO_AUTOMATIQUE"}
    s = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if a.rapport:
        a.rapport.parent.mkdir(parents=True, exist_ok=True)
        a.rapport.write_text(s, encoding="utf-8")
    else:
        print(s, end="")
    return 0 if result["structure"] == "MODELE_VALIDE_NON_PROBANT" else 2

if __name__ == "__main__":
    sys.exit(main())
