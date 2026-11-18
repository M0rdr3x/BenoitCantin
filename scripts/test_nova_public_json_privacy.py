#!/usr/bin/env python3
"""Tests sans secrets de l'allowlist JSON publique du site Projet Nova."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from build_netlify_public import (
    PROJECT_NOVA_PUBLIC_DATA_JSON,
    canonical_public_data_key,
    public_data_json_errors,
    public_data_payload_violations,
)

PRIVATE_KEYS = (
    "user_id", "userId", "User-ID", "USER.ID", "usér_id",
    "emailAddress", "contactEmail", "user-email", "e_mail",
    "phoneNumber", "mobilePhone", "telephone-number",
    "ipAddress", "clientIP", "respondentId", "voterId",
    "participantId", "accountId", "deviceFingerprint",
    "ballotId", "ballotChoices", "rawVotes", "voteChoices",
    "surveyResponses", "questionnaireAnswers", "rawResponses",
    "accessToken", "refreshToken", "sessionId", "sessionToken",
    "apiKey", "secretKey", "passwordHash", "recoveryCodes",
    "dateOfBirth", "birthDate", "dateNaissance",
    "homeAddress", "postalAddress", "creditCardNumber",
    "socialInsuranceNumber", "passportNumber",
    "firstName", "lastName", "fullName", "oauthToken",
)

SAFE_KEYS = (
    "responseScale", "importanceWeights", "partyComparison",
    "candidateCount2026", "officialElectionName2026",
    "evidenceRecords", "questionnaireBinding",
    "questionWording", "noPartyNames", "axis", "id",
    "status", "reason", "pdf", "lastVerified",
)


def exercise_key_boundary() -> None:
    for key in PRIVATE_KEYS:
        payload = {"version": 1, "metadata": {"records": [{"public": True, key: "masked"}]}}
        errors = public_data_payload_violations(payload)
        if "clé de donnée individuelle interdite" not in errors and (
            "clé de donnée publique non ASCII, audit requis" not in errors
        ):
            raise AssertionError(f"Champ individuel non refusé: {key!r}")

    for key in SAFE_KEYS:
        payload = {"metadata": {key: "sans donnée individuelle"}}
        errors = public_data_payload_violations(payload)
        if errors:
            raise AssertionError(f"Clé publique réelle refusée: {key!r}, {errors}")

    for key in ("user\u200bid", "user\u202eid", "сontactEmail", "προσωπικό", "réponse"):
        errors = public_data_payload_violations({key: "inconnu"})
        if "clé de donnée publique non ASCII, audit requis" not in errors:
            raise AssertionError(f"Confusable non ASCII non refusé: {key!r}")

    if canonical_public_data_key("User-ID") != "userid":
        raise AssertionError("Les séparateurs arbitraires doivent être normalisés")
    if canonical_public_data_key("refreshToken") != canonical_public_data_key("refresh_token"):
        raise AssertionError("Un alias camelCase contourne l'audit")
    if "adresse courriel dans une donnée publique" not in public_data_payload_violations(
        {"summary": "private.person@example.org"}
    ):
        raise AssertionError("Détection historique d'adresses courriel affaiblie")


def exercise_approved_json_scan() -> None:
    with TemporaryDirectory(prefix="nova-json-security-") as root:
        output = Path(root)
        for rel in PROJECT_NOVA_PUBLIC_DATA_JSON:
            path = output / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"version": "1", "responseScale": ["oui", "non"]}),
                encoding="utf-8",
            )
        if errors := public_data_json_errors(output):
            raise AssertionError(f"Fixture publique saine refusée: {errors}")

        target = output / "projets/projet-nova/data/actualites.json"
        target.write_text(
            json.dumps({"published": True, "entries": [{"userId": "not-real"}]}),
            encoding="utf-8",
        )
        errors = public_data_json_errors(output)
        if not any("actualites.json" in error and "individuelle" in error for error in errors):
            raise AssertionError("Un export individuel camelCase est publiable")

        target.write_text(
            json.dumps({"published": True, "entries": [{"usеrId": "not-real"}]}),
            encoding="utf-8",
        )
        errors = public_data_json_errors(output)
        if not any("actualites.json" in error and "non ASCII" in error for error in errors):
            raise AssertionError("Un export avec confusable Unicode est publiable")


def main() -> int:
    exercise_key_boundary()
    exercise_approved_json_scan()
    print(
        "PASS: "
        f"{len(PRIVATE_KEYS)} alias sensibles refusés, "
        f"{len(SAFE_KEYS)} clés publiques légitimes acceptées, "
        "Unicode confusable rejeté, analyse réelle des 12 JSON contrôlée"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
