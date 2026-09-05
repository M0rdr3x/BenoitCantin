#!/usr/bin/env python3
"""Smoke HTTP local Emploi V25.

Deux utilisateurs entièrement synthétiques traversent Supabase Auth puis PostgREST.
Aucune donnée de production, aucun service_role et aucun contenu sensible ne sont utilisés.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


API_URL = os.environ.get("SINJIRA_LOCAL_API_URL", "").rstrip("/")
ANON_KEY = os.environ.get("SINJIRA_LOCAL_ANON_KEY", "")


def fail(message: str) -> None:
    print(f"ECHEC smoke Emploi V25: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


@dataclass(frozen=True)
class Response:
    status: int
    body: Any
    raw: str


def request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    prefer_representation: bool = False,
) -> Response:
    url = f"{API_URL}{path}"
    headers = {"apikey": ANON_KEY, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    if prefer_representation:
        headers["Prefer"] = "return=representation"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except OSError as exc:
        fail(f"requête {method} {path} impossible: {exc}")

    try:
        parsed = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        parsed = raw
    return Response(status=status, body=parsed, raw=raw)


def signup(label: str) -> tuple[str, str]:
    email = f"sinjira-employment-smoke-{label}@example.com"
    password = f"SINJIRA-Local-{label}-2026!"
    response = request(
        "POST",
        "/auth/v1/signup",
        body={
            "email": email,
            "password": password,
            "data": {
                "pseudo": f"Smoke Emploi {label}",
                "birth_date": "1990-01-15",
                "date_of_birth": "1990-01-15",
                "gender": "Homme",
                "sex": "male",
            },
        },
    )
    require(response.status in (200, 201), f"signup {label} refusé: HTTP {response.status} {response.raw}")
    require(isinstance(response.body, dict), f"signup {label}: réponse JSON invalide")
    token = response.body.get("access_token")
    user = response.body.get("user") or {}
    user_id = user.get("id") if isinstance(user, dict) else None
    require(isinstance(token, str) and token, f"signup {label}: access_token absent")
    require(isinstance(user_id, str) and user_id, f"signup {label}: user.id absent")
    return token, user_id


def encoded(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def expect_rows(response: Response, expected: int, context: str) -> list[dict[str, Any]]:
    require(response.status in (200, 201), f"{context}: HTTP {response.status} {response.raw}")
    require(isinstance(response.body, list), f"{context}: réponse liste attendue, reçu {response.body!r}")
    require(len(response.body) == expected, f"{context}: {expected} ligne(s) attendue(s), reçu {len(response.body)}")
    require(all(isinstance(row, dict) for row in response.body), f"{context}: ligne JSON invalide")
    return response.body


def main() -> int:
    require(API_URL.startswith("http://127.0.0.1") or API_URL.startswith("http://localhost"), "API locale obligatoire")
    require(bool(ANON_KEY), "clé anon locale absente")

    token_a, user_a = signup("a")
    token_b, user_b = signup("b")
    require(user_a != user_b, "les deux comptes synthétiques doivent être distincts")

    # Un navigateur anonyme ne peut pas lire le module privé.
    anon = request("GET", "/rest/v1/employment_profiles?select=user_id")
    require(anon.status >= 400, f"anon ne doit pas lire employment_profiles: HTTP {anon.status} {anon.raw}")

    # Utilisateur A crée et relit son profil.
    created_profile = expect_rows(
        request(
            "POST",
            "/rest/v1/employment_profiles?select=user_id,professional_title,search_status",
            token=token_a,
            body={
                "user_id": user_a,
                "professional_title": "Profil synthétique A",
                "summary": "Donnée locale non sensible pour vérifier la RLS.",
                "search_status": "open",
                "remote_preference": "flexible",
                "skills": ["test-local"],
            },
            prefer_representation=True,
        ),
        1,
        "création profil A",
    )
    require(created_profile[0].get("user_id") == user_a, "profil A créé pour le mauvais utilisateur")

    own_profile = expect_rows(
        request(
            "GET",
            f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_a)}&select=user_id,professional_title",
            token=token_a,
        ),
        1,
        "lecture profil A par A",
    )
    require(own_profile[0].get("professional_title") == "Profil synthétique A", "profil A inattendu")

    # Utilisateur B ne voit pas le profil A.
    expect_rows(
        request(
            "GET",
            f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_a)}&select=user_id,professional_title",
            token=token_b,
        ),
        0,
        "isolation SELECT profil A depuis B",
    )

    # B ne peut pas usurper A lors d'un INSERT.
    forged_profile = request(
        "POST",
        "/rest/v1/employment_profiles",
        token=token_b,
        body={"user_id": user_a, "professional_title": "Usurpation interdite"},
        prefer_representation=True,
    )
    require(forged_profile.status >= 400, f"B a pu insérer un profil pour A: HTTP {forged_profile.status} {forged_profile.raw}")

    # B ne peut ni modifier ni supprimer la ligne A : PostgREST retourne zéro ligne affectée.
    expect_rows(
        request(
            "PATCH",
            f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_a)}&select=user_id,professional_title",
            token=token_b,
            body={"professional_title": "Intrusion B"},
            prefer_representation=True,
        ),
        0,
        "isolation UPDATE profil A depuis B",
    )
    expect_rows(
        request(
            "DELETE",
            f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_a)}&select=user_id",
            token=token_b,
            prefer_representation=True,
        ),
        0,
        "isolation DELETE profil A depuis B",
    )

    intact_profile = expect_rows(
        request(
            "GET",
            f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_a)}&select=user_id,professional_title",
            token=token_a,
        ),
        1,
        "profil A intact après attaques B",
    )
    require(intact_profile[0].get("professional_title") == "Profil synthétique A", "B a altéré le profil A")

    # Même frontière pour le suivi des candidatures.
    application = expect_rows(
        request(
            "POST",
            "/rest/v1/employment_applications?select=id,user_id,employer_name,role_title,status",
            token=token_a,
            body={
                "user_id": user_a,
                "employer_name": "Entreprise Test Locale",
                "role_title": "Rôle Synthétique",
                "status": "saved",
                "private_notes": "Aucune donnée réelle; smoke RLS local uniquement.",
            },
            prefer_representation=True,
        ),
        1,
        "création candidature A",
    )[0]
    application_id = application.get("id")
    require(isinstance(application_id, str) and application_id, "id candidature A absent")

    expect_rows(
        request(
            "GET",
            f"/rest/v1/employment_applications?id=eq.{encoded(application_id)}&select=id,user_id,status",
            token=token_b,
        ),
        0,
        "isolation SELECT candidature A depuis B",
    )

    forged_application = request(
        "POST",
        "/rest/v1/employment_applications",
        token=token_b,
        body={
            "user_id": user_a,
            "employer_name": "Usurpation interdite",
            "role_title": "Ne doit pas exister",
        },
        prefer_representation=True,
    )
    require(
        forged_application.status >= 400,
        f"B a pu créer une candidature pour A: HTTP {forged_application.status} {forged_application.raw}",
    )

    expect_rows(
        request(
            "PATCH",
            f"/rest/v1/employment_applications?id=eq.{encoded(application_id)}&select=id,status",
            token=token_b,
            body={"status": "accepted"},
            prefer_representation=True,
        ),
        0,
        "isolation UPDATE candidature A depuis B",
    )
    expect_rows(
        request(
            "DELETE",
            f"/rest/v1/employment_applications?id=eq.{encoded(application_id)}&select=id",
            token=token_b,
            prefer_representation=True,
        ),
        0,
        "isolation DELETE candidature A depuis B",
    )

    # A conserve ses droits CRUD et la ligne n'a pas été altérée par B.
    updated_application = expect_rows(
        request(
            "PATCH",
            f"/rest/v1/employment_applications?id=eq.{encoded(application_id)}&select=id,user_id,status",
            token=token_a,
            body={"status": "applied"},
            prefer_representation=True,
        ),
        1,
        "UPDATE candidature A par A",
    )
    require(updated_application[0].get("status") == "applied", "A n'a pas pu mettre à jour sa candidature")

    # Nettoyage fonctionnel local par le propriétaire; la pile sera ensuite détruite par CI.
    expect_rows(
        request(
            "DELETE",
            f"/rest/v1/employment_applications?id=eq.{encoded(application_id)}&select=id",
            token=token_a,
            prefer_representation=True,
        ),
        1,
        "DELETE candidature A par A",
    )
    expect_rows(
        request(
            "DELETE",
            f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_a)}&select=user_id",
            token=token_a,
            prefer_representation=True,
        ),
        1,
        "DELETE profil A par A",
    )

    print(
        "OK smoke Emploi V25: Auth locale réelle, anon bloqué, propriétaire CRUD, "
        "isolation cross-user SELECT/INSERT/UPDATE/DELETE sur profils et candidatures."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
