#!/usr/bin/env python3
"""Contrôle lecture seule du vrai site NOVA, sans bulletin ni secret.

Utilisable quotidiennement après déploiement; --self-test n'accède jamais au réseau.
Les comparaisons des bundles visent à détecter un contenu public absent ou périmé.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT / "projets" / "projet-nova"
ORIGIN = "https://www.benoitcantin.com"
API_ORIGIN = "https://gpvivleexywljowcqkru.supabase.co"
API = API_ORIGIN + "/functions/v1/nova-civic-poll"
PREFIX = "/projets/projet-nova/"
TIMEOUT = 12
MAX_BODY = 950_000


class FixedHostRedirects(HTTPRedirectHandler):
    def __init__(self, hostname: str):
        super().__init__()
        self.hostname = hostname

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        url = urlparse(newurl)
        if url.scheme != "https" or url.hostname != self.hostname:
            raise ValueError("Redirection hors du domaine autorisé")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def request(url: str, allowed_host: str, *, origin: str | None = None, binary: bool = False):
    target = urlparse(url)
    if target.scheme != "https" or target.hostname != allowed_host:
        raise ValueError("Hôte de contrôle non autorisé")
    headers = {
        "User-Agent": "NOVA-Public-ReadOnly-Monitor/1.0",
        "Accept": "application/json, text/javascript, text/html, */*",
        "Cache-Control": "no-cache",
    }
    if origin:
        headers["Origin"] = origin
    opener = build_opener(FixedHostRedirects(allowed_host))
    req = Request(url, headers=headers, method="GET")
    try:
        with opener.open(req, timeout=TIMEOUT) as response:
            data = response.read(MAX_BODY + 1)
            if len(data) > MAX_BODY:
                raise ValueError("Réponse public trop volumineuse")
            return response.status, response.headers, data if binary else data.decode("utf-8")
    except HTTPError as err:
        return err.code, err.headers, b"" if binary else ""


def stable_api_get(getter=request, sleep=time.sleep):
    """Trois lectures GET maximum si l'API a un incident 503 bref."""
    for attempt in range(3):
        try:
            response=getter(API, urlparse(API_ORIGIN).hostname or "", origin=ORIGIN)
        except (URLError,TimeoutError):
            if attempt==2: raise
        else:
            if response[0]!=503 or attempt==2:
                return response
        sleep(0.3 * (2 ** attempt))
    raise ValueError("Réessais API épuisés")


def review_page_ok(html_source: str) -> bool:
    """Une page candidate ne recueille pas d'avis politique."""
    return (
        len(re.findall(r'<li data-type="opinion" data-id="q[0-9]{2}">', html_source)) == 64
        and len(re.findall(r'<li data-type="consultation" data-id="q[0-9]{2}">', html_source)) == 40
        and 'Aucune réponse n’est enregistrée ici' in html_source
        and 'noindex,follow' in html_source
        and not re.search(r'<\s*(form|input|button|script)\b', html_source, re.I)
    )


def decode_bundle(source: str, variable: str):
    prefix = "window." + variable + " = "
    if source.count(prefix) != 1:
        raise ValueError("Affectation du corpus absente ou dupliquée : " + variable)
    data = source.split(prefix, 1)[1].strip()
    if not data.endswith(";"):
        raise ValueError("Fin de corpus public invalide : " + variable)
    return json.loads(data[:-1])


def compare_local_bundle(raw: str, variable: str, source_filename: str):
    local = (NOVA / "assets" / source_filename).read_text(encoding="utf-8")
    if decode_bundle(raw, variable) != decode_bundle(local, variable):
        raise ValueError("Le contenu publié diverge de la source GitHub : " + source_filename)


def script_order(html: str, bundle: str, application: str):
    one = html.find(bundle)
    two = html.find(application)
    if one < 0 or two < 0 or one >= two:
        raise ValueError("Chargement JavaScript incorrect : " + bundle)


def script_ref(html: str, filename: str) -> str:
    """Récupérer l'unique script versionné attendu (aucun chemin de repli ambigu)."""
    scripts = re.findall(r'<script\b[^>]*\bsrc="([^"]+)"', html, re.I)
    hits = [src for src in scripts if src.split("?", 1)[0] == "assets/" + filename]
    if len(hits) != 1 or "?" not in hits[0]:
        raise ValueError("Référence JavaScript absente, dupliquée ou non versionnée : " + filename)
    return hits[0]


def assert_scripts_match_source(deployed_html: str, source_html: str,
                                bundle: str, application: str, dependencies=()):
    """Vérifier versions, présence et ordre des scripts nécessaires à l'interface."""
    names = (bundle, *dependencies, application)
    expected = [script_ref(source_html, name) for name in names]
    actual = [script_ref(deployed_html, name) for name in names]
    if actual != expected:
        raise ValueError("Versions des scripts publics déployés différentes du code source : " + ", ".join(names))
    for before, after in zip(expected, expected[1:]):
        script_order(deployed_html, before, after)


def compare_local_application(raw: str, source_filename: str):
    """Vérifier les octets du code applicatif rendu public, pas seulement son HTTP 200."""
    local = (NOVA / "assets" / source_filename).read_text(encoding="utf-8")
    if raw != local:
        raise ValueError("Script public périmé ou divergent : " + source_filename)


def validate_opening_state(local_poll, response):
    """Le serveur ne doit jamais accepter des votes sur un corpus marqué provisoire."""
    if not isinstance(local_poll.get("published"), bool):
        raise ValueError("État de publication du corpus public invalide")
    if not isinstance(response.get("open"), bool):
        raise ValueError("État d'ouverture de l'API invalide")
    if response["open"] and not local_poll["published"]:
        raise ValueError("INCIDENT : serveur de vote ouvert sur un questionnaire public non approuvé")


def self_test():
    reads=[]
    delays=[]
    def transient(url,host,*,origin=None):
        reads.append(url)
        return (200 if len(reads)==3 else 503,{},'{}')
    assert stable_api_get(transient,delays.append)[0]==200
    assert len(reads)==3 and delays==[0.3,0.6]
    reads.clear();delays.clear()
    def fail_forever(url,host,*,origin=None):
        reads.append(url)
        return 503,{},''
    assert stable_api_get(fail_forever,delays.append)[0]==503
    assert len(reads)==3
    source = 'window.__NOVA_TEST = {"questions": [], "published": false};'
    assert decode_bundle(source, "__NOVA_TEST") == {"questions": [], "published": False}
    try:
        decode_bundle(source + "\nwindow.__NOVA_TEST = {};", "__NOVA_TEST")
    except ValueError:
        pass
    else:
        raise AssertionError("Affectation JS dupliquée non détectée")
    validate_opening_state({"published": False},{"open": False})
    validate_opening_state({"published": True},{"open": True})
    try:
        validate_opening_state({"published": False},{"open": True})
    except ValueError:
        pass
    else:
        raise AssertionError("Activation serveur accidentelle non détectée")
    script_order('<script src="a.js"></script><script src="b.js"></script>', "a.js", "b.js")
    civic_scripts = ('<script defer src="assets/sondage-public-corpus.js?v=1"></script>'
                     '<script defer src="assets/nova-civic-integrity.js?v=2"></script>'
                     '<script defer src="assets/sondage-citoyen.js?v=14"></script>')
    deps = ("nova-civic-integrity.js",)
    assert_scripts_match_source(civic_scripts, civic_scripts,
                                "sondage-public-corpus.js", "sondage-citoyen.js", deps)
    for damaged in (
        civic_scripts.replace('<script defer src="assets/nova-civic-integrity.js?v=2"></script>', ''),
        civic_scripts.replace("nova-civic-integrity.js?v=2", "nova-civic-integrity.js?v=0"),
        civic_scripts.replace('<script defer src="assets/nova-civic-integrity.js?v=2"></script>', '') +
          '<script defer src="assets/nova-civic-integrity.js?v=2"></script>',
    ):
        try:
            assert_scripts_match_source(damaged, civic_scripts,
                                        "sondage-public-corpus.js", "sondage-citoyen.js", deps)
        except ValueError:
            pass
        else:
            raise AssertionError("Dépendance d'intégrité absente, périmée ou mal ordonnée acceptée")

    local_scripts = '<script defer src="assets/sondage-public-corpus.js?v=1"></script><script defer src="assets/sondage-citoyen.js?v=9"></script>'
    assert_scripts_match_source(local_scripts, local_scripts, "sondage-public-corpus.js", "sondage-citoyen.js")
    try:
        assert_scripts_match_source(local_scripts.replace("v=9", "v=8"), local_scripts,
                                    "sondage-public-corpus.js", "sondage-citoyen.js")
    except ValueError:
        pass
    else:
        raise AssertionError("Un ancien script applicatif déployé doit être rejeté")
    try:
        assert_scripts_match_source(local_scripts.replace("v=1", "v=0"), local_scripts,
                                    "sondage-public-corpus.js", "sondage-citoyen.js")
    except ValueError:
        pass
    else:
        raise AssertionError("Un ancien corpus public déployé doit être rejeté")
    try:
        script_ref(local_scripts + '<script defer src="assets/sondage-citoyen.js?v=9"></script>',
                   "sondage-citoyen.js")
    except ValueError:
        pass
    else:
        raise AssertionError("Un script applicatif chargé deux fois doit être rejeté")
    try:
        script_order('<script src="b.js"></script><script src="a.js"></script>', "a.js", "b.js")
    except ValueError:
        pass
    else:
        raise AssertionError("Scripts inversés non détectés")
    assert not review_page_ok("<form><li data-type='opinion'>x</li></form>")
    print("OK : test de contrôle HTTP NOVA en lecture seule.")


def main():
    errors = []
    checks = 0

    def verify(path: str, expected: int = 200):
        nonlocal checks
        status, headers, body = request(ORIGIN + path, "www.benoitcantin.com")
        checks += 1
        if status != expected:
            raise ValueError(f"{path}: HTTP {status} au lieu de {expected}")
        return body

    def verify_media(path: str, expected_type: str, magic: bytes):
        nonlocal checks
        status, headers, data = request(ORIGIN + path, "www.benoitcantin.com", binary=True)
        checks += 1
        if status != 200:
            raise ValueError(f"{path}: ressource visuelle absente (HTTP {status})")
        if headers.get_content_type() != expected_type:
            raise ValueError(f"{path}: type de fichier inattendu")
        if not data.startswith(magic):
            raise ValueError(f"{path}: signature de fichier incorrecte")
        if expected_type == "image/webp" and data[8:12] != b"WEBP":
            raise ValueError(f"{path}: fichier WebP invalide")
        return data

    try:
        home = verify(PREFIX)
        if "sondage-citoyen.html" not in home or "boussole-electorale.html" not in home:
            raise ValueError("Liens vers sondage et boussole absents de l'accueil")
        if home.count('src="assets/sondage-citoyen.svg"') < 2:
            raise ValueError("Illustration du sondage absente des accès d'accueil")
        if home.count('src="../../assets/media/nova-boussole-electorale-v2.webp"') < 2:
            raise ValueError("Illustration officielle de la boussole absente des accès d'accueil")
        verify_media(PREFIX + "assets/sondage-citoyen.svg", "image/svg+xml", b"<svg")
        verify_media("/assets/media/nova-boussole-electorale-v2.webp", "image/webp", b"RIFF")

        preview_html = verify(PREFIX + "sondages-a-valider.html")
        if not review_page_ok(preview_html):
            raise ValueError("Les 104 questions candidates ou la lecture seule ne sont pas conformes")
        poll_html = verify(PREFIX + "sondage-citoyen.html")
        compass_html = verify(PREFIX + "boussole-electorale.html")
        if 'href="sondages-a-valider.html"' not in poll_html:
            raise ValueError("Le sondage public n'indique pas le projet 64/40")
        assert_scripts_match_source(poll_html, (NOVA / "sondage-citoyen.html").read_text("utf-8"),
                                    "sondage-public-corpus.js", "sondage-citoyen.js",
                                    dependencies=("nova-civic-integrity.js",))
        assert_scripts_match_source(compass_html, (NOVA / "boussole-electorale.html").read_text("utf-8"),
                                    "boussole-public-corpus.js", "boussole-electorale.js",
                                    dependencies=("nova-civic-integrity.js",))

        remote_poll = verify(PREFIX + "assets/sondage-public-corpus.js")
        remote_compass = verify(PREFIX + "assets/boussole-public-corpus.js")
        compare_local_bundle(remote_poll, "__NOVA_POLL_PUBLIC_CORPUS", "sondage-public-corpus.js")
        compare_local_bundle(remote_compass, "__NOVA_COMPASS_PUBLIC_CORPORA", "boussole-public-corpus.js")

        compare_local_application(verify(PREFIX + "assets/nova-civic-integrity.js"), "nova-civic-integrity.js")
        compare_local_application(verify(PREFIX + "assets/sondage-citoyen.js"), "sondage-citoyen.js")
        compare_local_application(verify(PREFIX + "assets/boussole-electorale.js"), "boussole-electorale.js")

        status, headers, data = stable_api_get()
        checks += 1
        if status != 200 or headers.get("Access-Control-Allow-Origin") != ORIGIN:
            raise ValueError(f"API NOVA inaccessible ou CORS absent: HTTP {status}")
        response = json.loads(data)
        local_poll = decode_bundle(
            (NOVA / "assets/sondage-public-corpus.js").read_text("utf-8"),
            "__NOVA_POLL_PUBLIC_CORPUS",
        )
        validate_opening_state(local_poll, response)
        if response.get("version") != local_poll["version"] or len(response.get("questions") or []) != 8:
            raise ValueError("Le questionnaire serveur et la version du site divergent")
        if [(q["id"],q["text"]) for q in response["questions"]] != [
            (q["id"],q["text"]) for q in local_poll["questions"]
        ]:
            raise ValueError("Texte des questions serveur différent du corpus public")
        if response.get("minPublicBallots") != 10:
            raise ValueError("Seuil de protection des résultats non conforme")
        if response.get("resultsVisible") is False:
            if response.get("ballots") is not None or any(q.get("counts") is not None for q in response["questions"]):
                raise ValueError("Petits effectifs exposés avant publication")

        for private in ("/supabase/config.toml", "/scripts/build_netlify_public.py"):
            private_status, _, _ = request(ORIGIN + private, "www.benoitcantin.com")
            checks += 1
            if private_status not in (403,404,410):
                raise ValueError(f"Fichier technique accessible : {private} (HTTP {private_status})")

    except (ValueError, OSError, URLError, UnicodeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(str(exc))

    if errors:
        for item in errors:
            print("ECHEC surveillance NOVA :", item)
        return 1
    print(f"OK NOVA en ligne : {checks} réponses HTTP, corpus publics intègres, API conforme, fichiers privés bloqués, sans vote.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        raise SystemExit(main())
