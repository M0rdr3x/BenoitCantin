#!/usr/bin/env python3
"""SINJIRA — deux soumissions Formspree synthétiques SUR VALIDATION EXPLICITE.

Aucun participant, identifiant de compte, mot de passe, image ou questionnaire
n'est utilisé. Aucun retry automatique; n'affirme jamais la livraison email.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ENDPOINTS = {
    "compte": "https://formspree.io/f/xzeeqynp",
    "registre": "https://formspree.io/f/mrppvrwa",
}
CONFIRMATION = "AUTORISER_DEUX_TESTS_FORMSPREE"
INBOX = "sinjiraofficiel@gmail.com"
EXPECTED_REPO = "M0rdr3x/BenoitCantin"
WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/sinjira-formspree-synthetic-smoke.yml"


def payloads(run_id: str) -> list[tuple[str, str, dict[str, str]]]:
    if not re.fullmatch(r"[0-9]{1,18}", run_id):
        raise ValueError("Numéro de workflow invalide")
    date = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = []
    for kind, url in ENDPOINTS.items():
        fields = {
            "email": INBOX,
            "event": "TEST_TECHNIQUE_SINJIRA_" + kind.upper(),
            "reference": "TEST-SINJIRA-" + run_id + "-" + kind,
            "message": ("TEST TECHNIQUE SINJIRA sans donnée de participant. "
                        "Ce message n'est ni une inscription ni un enregistrement de dossier. "
                        "Vérifiez seulement la notification de test dans Formspree."),
            "date": date,
        }
        out.append((kind, url, fields))
    return out


def authorized(env: dict[str, str]) -> bool:
    return (
        env.get("CONFIRMATION") == CONFIRMATION
        and env.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and env.get("GITHUB_REF") == "refs/heads/main"
        and env.get("GITHUB_ACTIONS") == "true"
        and env.get("GITHUB_REPOSITORY") == EXPECTED_REPO
        and bool(re.fullmatch(r"[0-9]{1,18}", env.get("GITHUB_RUN_ID", "")))
    )


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def send_one(kind: str, url: str, fields: dict[str, str]) -> bool:
    if url != ENDPOINTS[kind] or set(fields) != {
        "email", "event", "reference", "message", "date"
    } or fields["email"] != INBOX or not fields["event"].startswith("TEST_TECHNIQUE_SINJIRA_"):
        raise ValueError("Soumission synthétique non autorisée")
    request = Request(
        url,
        data=json.dumps(fields, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "User-Agent": "SINJIRA-Formspree-Synthetic-QA/1.0",
        },
    )
    opener = build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=12) as reply:
            status = reply.status
            reply.read(4096)
    except HTTPError as error:
        status = error.code
        error.close()
    except (URLError, TimeoutError, OSError):
        print("FAIL " + kind + " : erreur réseau; aucune nouvelle tentative automatique.")
        return False
    if 200 <= status < 300:
        print("PASS " + kind + " : Formspree a accepté le POST (HTTP 2xx).")
        return True
    print("FAIL " + kind + " : Formspree n'a pas accepté le POST (HTTP non 2xx).")
    return False


def self_test() -> None:
    content = WORKFLOW.read_text(encoding="utf-8")
    for required in ("workflow_dispatch:", "environment: production",
                     "secrets:", "AUTORISER_DEUX_TESTS_FORMSPREE",
                     "scripts/probe_sinjira_formspree_synthetic.py --live"):
        # Le seul libellé « secrets: » ne doit PAS être nécessaire : le
        # contrôle exige au contraire qu'aucun secret ne soit consulté.
        if required == "secrets:":
            assert required not in content, "Un secret GitHub serait inutile"
        else:
            assert required in content, "Contrat workflow manquant : " + required
    assert "push:" not in content, "Un push ne doit jamais envoyer un test tiers"
    tests = payloads("123456")
    assert len(tests) == 2 and len(set(item[1] for item in tests)) == 2
    for kind, url, data in tests:
        assert url.startswith("https://formspree.io/f/")
        assert data["email"] == INBOX
        assert data["event"] == "TEST_TECHNIQUE_SINJIRA_" + kind.upper()
        assert set(data) == {"email", "event", "reference", "message", "date"}
        for forbidden in ("password", "photo", "questionnaire", "token", "user_id"):
            assert forbidden not in json.dumps(data).lower()
    assert not authorized({})
    valid = {
        "CONFIRMATION": CONFIRMATION,
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": EXPECTED_REPO,
        "GITHUB_RUN_ID": "123456",
    }
    assert authorized(valid)
    for name, alternative in (
        ("CONFIRMATION", "NO"), ("GITHUB_EVENT_NAME", "pull_request"),
        ("GITHUB_REF", "refs/heads/feature"), ("GITHUB_ACTIONS", "false"),
        ("GITHUB_REPOSITORY", "other/repo"), ("GITHUB_RUN_ID", "a"),
    ):
        assert not authorized({**valid, name: alternative})
    for bad in ("../admin", "1e10", "0\nabc"):
        try:
            payloads(bad)
            raise AssertionError("Identifiant invalide accepté")
        except ValueError:
            pass
    print("PASS tests de garde : deux destinations, données fictives, aucune exécution automatique.")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not authorized(dict(os.environ)):
        print("REFUS : lancement manuel, approbation et branche main obligatoires.")
        return 2
    accepted = 0
    for kind, url, fields in payloads(os.environ["GITHUB_RUN_ID"]):
        accepted += int(send_one(kind, url, fields))
    print(f"BILAN : {accepted}/2 POST techniques acceptés par Formspree.")
    print("IMPORTANT : l'acceptation HTTP ne prouve ni la livraison à la boîte "
          "administrative ni l'activation des accusés automatiques.")
    return 0 if accepted == 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
