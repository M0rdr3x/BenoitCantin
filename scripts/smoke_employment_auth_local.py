#!/usr/bin/env python3
"""Smoke HTTP local bidirectionnel Emploi V25.

Deux utilisateurs entièrement synthétiques traversent Supabase Auth puis PostgREST.
Chacun possède ses propres données et doit rester incapable de lire ou modifier celles
de l'autre. Aucun service_role, aucune donnée de production et aucune offre réelle.
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

PROFILE_TITLE = {
    "a": "Profil synthétique local A",
    "b": "Profil synthétique local B",
}
EMPLOYER = {
    "a": "Employeur synthétique local A",
    "b": "Employeur synthétique local B",
}
ROLE = {
    "a": "Rôle synthétique local A",
    "b": "Rôle synthétique local B",
}


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
    headers = {"apikey": ANON_KEY, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    if prefer_representation:
        headers["Prefer"] = "return=representation"
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(f"{API_URL}{path}", data=data, headers=headers, method=method)
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
    password = f"SINJIRA-Local-{label.upper()}-2026!"
    response = request(
        "POST",
        "/auth/v1/signup",
        body={
            "email": email,
            "password": password,
            "data": {
                "pseudo": f"Smoke Emploi {label.upper()}",
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


def expect_rejected(response: Response, context: str) -> None:
    require(response.status >= 400, f"{context}: rejet RLS attendu, reçu HTTP {response.status} {response.raw}")


def profile_body(user_id: str, label: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "professional_title": PROFILE_TITLE[label],
        "summary": f"Donnée synthétique locale {label.upper()} — aucune donnée personnelle réelle.",
        "search_status": "open" if label == "a" else "actively_looking",
        "preferred_location": f"Zone synthétique {label.upper()}",
        "remote_preference": "flexible" if label == "a" else "remote",
        "skills": [f"test-local-{label}"],
    }


def application_body(user_id: str, label: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "employer_name": EMPLOYER[label],
        "role_title": ROLE[label],
        "location_label": f"Lieu synthétique {label.upper()}",
        "source_url": f"https://example.invalid/sinjira-employment-smoke-{label}",
        "status": "saved",
        "private_notes": f"Donnée synthétique locale {label.upper()} — aucune candidature réelle.",
    }


def create_profile(token: str, user_id: str, label: str) -> None:
    rows = expect_rows(
        request(
            "POST",
            "/rest/v1/employment_profiles?select=user_id,professional_title,search_status",
            token=token,
            body=profile_body(user_id, label),
            prefer_representation=True,
        ),
        1,
        f"création profil {label.upper()}",
    )
    require(rows[0].get("user_id") == user_id, f"profil {label.upper()} créé pour le mauvais utilisateur")
    require(rows[0].get("professional_title") == PROFILE_TITLE[label], f"titre profil {label.upper()} inattendu")


def create_application(token: str, user_id: str, label: str) -> str:
    row = expect_rows(
        request(
            "POST",
            "/rest/v1/employment_applications?select=id,user_id,employer_name,role_title,status",
            token=token,
            body=application_body(user_id, label),
            prefer_representation=True,
        ),
        1,
        f"création candidature {label.upper()}",
    )[0]
    require(row.get("user_id") == user_id, f"candidature {label.upper()} créée pour le mauvais utilisateur")
    require(row.get("employer_name") == EMPLOYER[label], f"employeur synthétique {label.upper()} inattendu")
    application_id = row.get("id")
    require(isinstance(application_id, str) and application_id, f"id candidature {label.upper()} absent")
    return application_id


def assert_profile_visibility(token: str, own_user: str, other_user: str, label: str) -> None:
    own_rows = expect_rows(
        request("GET", "/rest/v1/employment_profiles?select=user_id,professional_title", token=token),
        1,
        f"liste propriétaire profil {label.upper()}",
    )
    require(own_rows[0].get("user_id") == own_user, f"{label.upper()} voit un profil qui ne lui appartient pas")
    require(own_rows[0].get("professional_title") == PROFILE_TITLE[label], f"profil propre {label.upper()} inattendu")
    expect_rows(
        request(
            "GET",
            f"/rest/v1/employment_profiles?user_id=eq.{encoded(other_user)}&select=user_id,professional_title",
            token=token,
        ),
        0,
        f"isolation SELECT profil autre depuis {label.upper()}",
    )


def assert_application_visibility(token: str, own_id: str, other_id: str, own_user: str, label: str) -> None:
    own_rows = expect_rows(
        request("GET", "/rest/v1/employment_applications?select=id,user_id,status", token=token),
        1,
        f"liste propriétaire candidature {label.upper()}",
    )
    require(own_rows[0].get("id") == own_id and own_rows[0].get("user_id") == own_user,
            f"{label.upper()} voit une candidature qui ne lui appartient pas")
    expect_rows(
        request(
            "GET",
            f"/rest/v1/employment_applications?id=eq.{encoded(other_id)}&select=id,user_id,status",
            token=token,
        ),
        0,
        f"isolation SELECT candidature autre depuis {label.upper()}",
    )


def assert_other_profile_write_blocked(token: str, other_user: str, label: str) -> None:
    expect_rows(
        request(
            "PATCH",
            f"/rest/v1/employment_profiles?user_id=eq.{encoded(other_user)}&select=user_id,professional_title",
            token=token,
            body={"professional_title": f"Intrusion synthétique {label.upper()}"},
            prefer_representation=True,
        ),
        0,
        f"isolation UPDATE profil autre depuis {label.upper()}",
    )
    expect_rows(
        request(
            "DELETE",
            f"/rest/v1/employment_profiles?user_id=eq.{encoded(other_user)}&select=user_id",
            token=token,
            prefer_representation=True,
        ),
        0,
        f"isolation DELETE profil autre depuis {label.upper()}",
    )


def assert_other_application_write_blocked(token: str, other_id: str, label: str) -> None:
    expect_rows(
        request(
            "PATCH",
            f"/rest/v1/employment_applications?id=eq.{encoded(other_id)}&select=id,status",
            token=token,
            body={"status": "accepted"},
            prefer_representation=True,
        ),
        0,
        f"isolation UPDATE candidature autre depuis {label.upper()}",
    )
    expect_rows(
        request(
            "DELETE",
            f"/rest/v1/employment_applications?id=eq.{encoded(other_id)}&select=id",
            token=token,
            prefer_representation=True,
        ),
        0,
        f"isolation DELETE candidature autre depuis {label.upper()}",
    )


def main() -> int:
    require(API_URL.startswith("http://127.0.0.1") or API_URL.startswith("http://localhost"), "API locale obligatoire")
    require(bool(ANON_KEY), "clé anon locale absente")

    token_a, user_a = signup("a")
    token_b, user_b = signup("b")
    require(user_a != user_b, "les deux comptes synthétiques doivent être distincts")

    # Le module est privé pour un navigateur non authentifié.
    anon_profiles = request("GET", "/rest/v1/employment_profiles?select=user_id")
    anon_applications = request("GET", "/rest/v1/employment_applications?select=id,user_id")
    require(anon_profiles.status >= 400, f"anon ne doit pas lire les profils: HTTP {anon_profiles.status}")
    require(anon_applications.status >= 400, f"anon ne doit pas lire les candidatures: HTTP {anon_applications.status}")

    # INSERT cross-user avant toute ligne légitime : le rejet vient de RLS, pas d'une unicité existante.
    expect_rejected(
        request("POST", "/rest/v1/employment_profiles", token=token_b,
                body=profile_body(user_a, "a"), prefer_representation=True),
        "B ne peut pas créer le profil de A",
    )
    expect_rejected(
        request("POST", "/rest/v1/employment_profiles", token=token_a,
                body=profile_body(user_b, "b"), prefer_representation=True),
        "A ne peut pas créer le profil de B",
    )

    create_profile(token_a, user_a, "a")
    create_profile(token_b, user_b, "b")

    assert_profile_visibility(token_a, user_a, user_b, "a")
    assert_profile_visibility(token_b, user_b, user_a, "b")
    assert_other_profile_write_blocked(token_a, user_b, "a")
    assert_other_profile_write_blocked(token_b, user_a, "b")

    # Les deux profils restent intacts après les tentatives réciproques.
    intact_a = expect_rows(
        request("GET", f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_a)}&select=user_id,professional_title", token=token_a),
        1,
        "profil A intact après tentative B",
    )
    intact_b = expect_rows(
        request("GET", f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_b)}&select=user_id,professional_title", token=token_b),
        1,
        "profil B intact après tentative A",
    )
    require(intact_a[0].get("professional_title") == PROFILE_TITLE["a"], "B a altéré le profil A")
    require(intact_b[0].get("professional_title") == PROFILE_TITLE["b"], "A a altéré le profil B")

    app_a = create_application(token_a, user_a, "a")
    app_b = create_application(token_b, user_b, "b")

    assert_application_visibility(token_a, app_a, app_b, user_a, "a")
    assert_application_visibility(token_b, app_b, app_a, user_b, "b")

    # INSERT candidature cross-user dans les deux sens.
    expect_rejected(
        request("POST", "/rest/v1/employment_applications", token=token_b,
                body=application_body(user_a, "a"), prefer_representation=True),
        "B ne peut pas créer une candidature pour A",
    )
    expect_rejected(
        request("POST", "/rest/v1/employment_applications", token=token_a,
                body=application_body(user_b, "b"), prefer_representation=True),
        "A ne peut pas créer une candidature pour B",
    )

    assert_other_application_write_blocked(token_a, app_b, "a")
    assert_other_application_write_blocked(token_b, app_a, "b")

    # Chaque propriétaire conserve ses droits UPDATE sur sa propre ligne.
    updated_a = expect_rows(
        request("PATCH", f"/rest/v1/employment_applications?id=eq.{encoded(app_a)}&select=id,user_id,status",
                token=token_a, body={"status": "applied"}, prefer_representation=True),
        1,
        "UPDATE candidature A par A",
    )
    updated_b = expect_rows(
        request("PATCH", f"/rest/v1/employment_applications?id=eq.{encoded(app_b)}&select=id,user_id,status",
                token=token_b, body={"status": "interview"}, prefer_representation=True),
        1,
        "UPDATE candidature B par B",
    )
    require(updated_a[0].get("status") == "applied", "A n'a pas pu modifier sa candidature")
    require(updated_b[0].get("status") == "interview", "B n'a pas pu modifier sa candidature")

    # Chaque propriétaire peut aussi modifier son profil, sans toucher à l'autre.
    owner_profile_a = expect_rows(
        request("PATCH", f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_a)}&select=user_id,search_status",
                token=token_a, body={"search_status": "actively_looking"}, prefer_representation=True),
        1,
        "UPDATE profil A par A",
    )
    owner_profile_b = expect_rows(
        request("PATCH", f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_b)}&select=user_id,search_status",
                token=token_b, body={"search_status": "open"}, prefer_representation=True),
        1,
        "UPDATE profil B par B",
    )
    require(owner_profile_a[0].get("user_id") == user_a, "UPDATE propriétaire A incohérent")
    require(owner_profile_b[0].get("user_id") == user_b, "UPDATE propriétaire B incohérent")

    # Nettoyage local par chaque propriétaire.
    expect_rows(
        request("DELETE", f"/rest/v1/employment_applications?id=eq.{encoded(app_a)}&select=id", token=token_a,
                prefer_representation=True),
        1,
        "DELETE candidature A par A",
    )
    expect_rows(
        request("DELETE", f"/rest/v1/employment_applications?id=eq.{encoded(app_b)}&select=id", token=token_b,
                prefer_representation=True),
        1,
        "DELETE candidature B par B",
    )
    expect_rows(
        request("DELETE", f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_a)}&select=user_id", token=token_a,
                prefer_representation=True),
        1,
        "DELETE profil A par A",
    )
    expect_rows(
        request("DELETE", f"/rest/v1/employment_profiles?user_id=eq.{encoded(user_b)}&select=user_id", token=token_b,
                prefer_representation=True),
        1,
        "DELETE profil B par B",
    )

    expect_rows(request("GET", "/rest/v1/employment_profiles?select=user_id", token=token_a), 0, "nettoyage profils A")
    expect_rows(request("GET", "/rest/v1/employment_profiles?select=user_id", token=token_b), 0, "nettoyage profils B")
    expect_rows(request("GET", "/rest/v1/employment_applications?select=id", token=token_a), 0, "nettoyage candidatures A")
    expect_rows(request("GET", "/rest/v1/employment_applications?select=id", token=token_b), 0, "nettoyage candidatures B")

    print(
        "OK smoke Emploi V25: deux comptes Auth locaux possèdent chacun profil+candidature, anon bloqué, "
        "CRUD propriétaire et isolation RLS bidirectionnelle SELECT/INSERT/UPDATE/DELETE vérifiés."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
