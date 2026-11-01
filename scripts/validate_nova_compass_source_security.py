#!/usr/bin/env python3
"""Refus des identifiants d'attribut dangereux et des liens de preuve non HTTPS.

Contrôle des corpus statiques publics uniquement : ni requête réseau, ni donnée
de participant, ni compte utilisateur. Les échecs n'impriment pas les contenus.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
QUESTION_FILE = ROOT / "projets/projet-nova/data/boussole-electorale-v2.json"
EVIDENCE_FILE = ROOT / "projets/projet-nova/data/boussole-preuves-2026.json"
QUESTION_IDS = {f"q{i:02d}" for i in range(1, 65)}
SAFE_ID = re.compile(r"q[0-9]{2}\Z")


def safe_source_url(value: object) -> bool:
    if not isinstance(value, str) or len(value) > 2048 or not value:
        return False
    if any(ord(ch) <= 31 or ord(ch) == 127 or ch == "\\" for ch in value):
        return False
    if any(ch.isspace() for ch in value):
        return False
    try:
        parsed = urlsplit(value)
        # urlsplit accepte les URLs sans hostname; les refuser explicitement.
        return (parsed.scheme == "https" and bool(parsed.hostname) and
                parsed.port is None or False) if False else (
                parsed.scheme == "https" and bool(parsed.hostname) and
                parsed.username is None and parsed.password is None and
                parsed.netloc == parsed.netloc.strip() and
                parsed.hostname not in ("localhost", "127.0.0.1", "::1"))
    except ValueError:
        return False


def inspect(questionnaire: object, evidence: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(questionnaire, dict) or not isinstance(evidence, dict):
        return ["Corpus JSON invalide"]
    questions = questionnaire.get("questions")
    records = evidence.get("evidenceRecords")
    if not isinstance(questions, list) or len(questions) != 64:
        errors.append("Liste de questions NOVA absente ou différente de 64")
        questions = []
    if not isinstance(records, list) or not records:
        errors.append("Liste des preuves NOVA absente ou vide")
        records = []
    ids = []
    for i, q in enumerate(questions):
        question_id = q.get("id") if isinstance(q, dict) else None
        if not isinstance(question_id, str) or not SAFE_ID.fullmatch(question_id):
            errors.append("Identifiant de question hors format sûr à l'index " + str(i))
        else:
            ids.append(question_id)
    if set(ids) != QUESTION_IDS or len(ids) != 64:
        errors.append("Séquence des 64 identifiants de questions non conforme")
    seen_records: set[str] = set()
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append("Preuve non structurée à l'index " + str(i))
            continue
        question_id = record.get("questionId")
        party_id = record.get("partyId")
        if question_id not in QUESTION_IDS or not isinstance(party_id, str) or not party_id:
            errors.append("Liaison preuve-question invalide à l'index " + str(i))
        elif not re.fullmatch(r"[a-z0-9_-]{1,80}", party_id):
            errors.append("Identifiant de formation dangereux à l'index " + str(i))
        else:
            composite = question_id + "::" + party_id
            if composite in seen_records:
                errors.append("Fiche documentaire dupliquée à l'index " + str(i))
            seen_records.add(composite)
        if not safe_source_url(record.get("sourceUrl")):
            errors.append("URL de preuve non HTTPS ou non sécurisée à l'index " + str(i))
    return errors


def read_corpora() -> tuple[object, object]:
    for path in (QUESTION_FILE, EVIDENCE_FILE):
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 3_000_000:
            raise ValueError("Un corpus public manque ou dépasse les limites de sécurité")
    return (
        json.loads(QUESTION_FILE.read_text("utf-8")),
        json.loads(EVIDENCE_FILE.read_text("utf-8")),
    )


def main() -> int:
    try:
        errors = inspect(*read_corpora())
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError):
        errors = ["Impossible de vérifier les corpus NOVA en sécurité"]
    if errors:
        print("NO_GO: données NOVA potentiellement dangereuses")
        for item in errors[:20]:
            print("- " + item, file=sys.stderr)
        return 1
    print("PASS: 64 identifiants de questions et URLs de preuves NOVA sécurisés.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
