#!/usr/bin/env python3
"""SINJIRA — parcours HTTP externe, sans identifiants ni changement de données."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SITE="https://www.benoitcantin.com"
API="https://gpvivleexywljowcqkru.supabase.co/functions/v1"
AUTH_SETTINGS="https://gpvivleexywljowcqkru.supabase.co/auth/v1/settings"
PUBLIC_CONFIG=(Path(__file__).resolve().parents[1]/"assets/js/sinjira-supabase-config.js")
PAGE_CONTRACTS={
    "/compte/inscription.html":('data-signup-form','formspree_receipt_opt_in'),
    "/compte/confirmer.html":('data-confirm-button','sinjira-confirm-email.js'),
    "/projets/sinjira/registre/":(
        'data-character-form','formspree_receipt_opt_in',
        'sinjira-character-registry.js?v=24.5.8',
    ),
}
FUNCTIONS=("notify-account-confirmation","submit-character-questionnaire")
JS_SCRIPTS={
    "/assets/js/v24-signup.js?v=24.5.3":("getSupabase().auth.signUp(", "formspree_receipt_opt_in"),
    "/assets/js/sinjira-confirm-email.js?v=2":("getSupabase().auth.verifyOtp(", "notify-account-confirmation"),
    "/assets/js/sinjira-character-registry.js?v=24.5.8":("auth.mfa.getAuthenticatorAssuranceLevel()", "submit-character-questionnaire"),
    "/assets/js/sinjira-supabase.js":(
        "createClient(", "isSinjiraBackendConfigured",
        "import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.0/+esm';"
    ),
    "/assets/js/sinjira-supabase-config.js":("supabasePublishableKey", "paidFeaturesEnabled"),
}

AUTH_ERROR=re.compile(r'authorization|jwt|apikey|api key|authentication|unauthori[sz]ed|missing.*token',re.I)


def fetch(request:Request,limit=200_000):
    try:
        with urlopen(request,timeout=13) as response:
            return response.status,response.read(limit+1)
    except HTTPError as error:
        return error.code,error.read(min(limit+1,2048))


def check_public_page(path,markers,fetcher=fetch):
    url=SITE+path
    status,body=fetcher(Request(url,headers={"Accept":"text/html",
                                              "Cache-Control":"no-cache"}))
    if status!=200 or len(body)>200_000:
        return False,"statut HTTP inattendu ou page trop longue"
    bodytext=body.decode("utf-8",errors="replace")
    if any(marker not in bodytext for marker in markers):
        return False,"marqueur public attendu absent"
    return True,"HTTP 200; contenu publié conforme"


def check_js_script(path, markers, fetcher=None):
    request=Request(SITE+path,headers={"Accept":"application/javascript,text/javascript",
                                         "Cache-Control":"no-cache"},method="GET")
    if fetcher is None:
        try:
            with urlopen(request,timeout=13) as res:
                status,mime,body=res.status,res.headers.get_content_type(),res.read(180001)
        except HTTPError as err:
            status,mime,body=err.code,err.headers.get_content_type(),err.read(2048)
    else:
        status,mime,body=fetcher(request)
    if status!=200 or mime not in ("application/javascript","text/javascript"):
        return False,"HTTP ou MIME JavaScript invalide"
    if len(body)>180000 or not body:
        return False,"fichier JS vide ou trop volumineux"
    if any(m not in body.decode("utf-8",errors="replace") for m in markers):
        return False,"script incomplet ou version erronée"
    return True,"HTTP 200, MIME JavaScript et version attendue"


def check_private_gateway(slug,fetcher=fetch):
    # Un corps vide/inoffensif; aucun compte, jeton ou donnée de questionnaire.
    # Sans authentification, le filtre JWT doit refuser avant le code métier.
    url=API+"/"+slug
    request=Request(url,data=b"{}",method="POST",headers={
        "Content-Type":"application/json",
        "Accept":"application/json",
        "Cache-Control":"no-store",
    })
    status,body=fetcher(request,2048)
    response=body.decode("utf-8",errors="replace")
    if status not in (401,403) or not AUTH_ERROR.search(response):
        return False,"requête anonyme non refusée explicitement par Auth/JWT"
    return True,"POST anonyme rejeté par la porte d'authentification"



def publishable_key():
    # La clé publishable est déjà livrée au navigateur : jamais de secret admin.
    content=PUBLIC_CONFIG.read_text(encoding="utf-8")
    match=re.search(r"supabasePublishableKey:\s*'((?:sb_publishable_)[A-Za-z0-9_-]+)'",content)
    if not match:
        raise ValueError("clé publique du site absente ou invalide")
    return match.group(1)


def check_auth_public_settings(fetcher=fetch,key=None):
    # GoTrue expose ce sous-ensemble de réglages via GET /auth/v1/settings.
    # Le corps de réponse, la clé publique et d'autres paramètres ne sont pas loggés.
    if key is None:
        key=publishable_key()
    if not re.fullmatch(r"sb_publishable_[A-Za-z0-9_-]{15,}",key):
        return False,"clé publique invalide"
    req=Request(AUTH_SETTINGS,headers={
        "Accept":"application/json",
        "apikey":key,
        "Cache-Control":"no-cache",
    },method="GET")
    status,body=fetcher(req,8192)
    if status!=200 or len(body)>8192:
        return False,"réglages Auth publics indisponibles"
    try:
        data=json.loads(body)
    except (ValueError,UnicodeDecodeError):
        return False,"réponse Auth publique invalide"
    if not isinstance(data,dict):
        return False,"réponse Auth inattendue"
    external=data.get("external")
    if not isinstance(external,dict) or external.get("email") is not True:
        return False,"fournisseur Email non confirmé comme actif"
    if data.get("disable_signup") is not False:
        return False,"inscriptions non confirmées comme actives"
    if data.get("mailer_autoconfirm") is not False:
        return False,"confirmation obligatoire non vérifiée"
    return True,"Email actif, inscription ouverte, confirmation obligatoire"


def self_test():
    for path,markers in PAGE_CONTRACTS.items():
        assert check_public_page(path,markers,
            lambda r:(200,(" ".join(markers)).encode("utf-8")))[0]
        assert not check_public_page(path,markers,
            lambda r:(200,b"<html>ancienne version</html>"))[0]
        assert not check_public_page(path,markers,
            lambda r:(503,b"maintenance"))[0]
    for path,markers in JS_SCRIPTS.items():
        def good(req):
            assert req.full_url==SITE+path and req.get_method()=="GET" and req.data is None
            return 200,"application/javascript",(" ".join(markers)).encode("utf-8")
        assert check_js_script(path,markers,good)[0]
        for status,mime,body in (
            (200,"text/html",(" ".join(markers)).encode("utf-8")),
            (404,"application/javascript",b"Not Found"),
            (200,"application/javascript",b"ancien script"),
            (200,"application/javascript",b"x"*180001),
        ):
            assert not check_js_script(path,markers,
                 lambda r,s=status,m=mime,b=body:(s,m,b))[0]
    # Détecter une régression de publication même si l'ancien SDK
    # fournit encore createClient() et réussirait les contrôles génériques.
    sdk_path="/assets/js/sinjira-supabase.js"
    sdk_markers=JS_SCRIPTS[sdk_path]
    old_sdk=(
        "import { createClient } from "
        "'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';"
    )
    stale_fixture=("createClient( isSinjiraBackendConfigured "+old_sdk).encode("utf-8")
    assert not check_js_script(
        sdk_path,sdk_markers,
        lambda request:(200,"application/javascript",stale_fixture)
    )[0], "La production ne doit pas accepter l'ancien SDK flottant."
    for slug in FUNCTIONS:
        def rejected(r,limit):
            assert r.get_method()=="POST"
            assert r.data==b"{}"
            assert r.get_header("Authorization") is None
            return 401,b'{"message":"Missing authorization header"}'
        assert check_private_gateway(slug,rejected)[0]
        for status,payload in [
            (200,b'{"ok":true}'),
            (403,b"Forbidden"),
            (405,b"Method not allowed"),
            (503,b"Unavailable"),
        ]:
            assert not check_private_gateway(slug,
                 lambda r,n,s=status,b=payload:(s,b))[0]
    valid_settings={"external":{"email":True},
                    "disable_signup":False,"mailer_autoconfirm":False}
    def settings_response(data,status=200):
        return lambda req,n: (
            status,json.dumps(data).encode("utf-8")
        )
    def settings_good(req,limit):
        assert req.full_url==AUTH_SETTINGS
        assert req.get_method()=="GET"
        assert req.get_header("Authorization") is None
        assert req.get_header("Apikey")=="sb_publishable_TEST_TEST_TEST_TEST_TEST"
        assert req.data is None
        return 200,json.dumps(valid_settings).encode("utf-8")
    assert check_auth_public_settings(settings_good,
              key="sb_publishable_TEST_TEST_TEST_TEST_TEST")[0]
    mutations=[
        ({"external":{"email":False}},"email"),
        ({"disable_signup":True},"signup"),
        ({"mailer_autoconfirm":True},"autoconfirm"),
        ({"external":{}},"missing email"),
        ({"mailer_autoconfirm":None},"missing confirmation"),
    ]
    for patch,label in mutations:
        invalid={**valid_settings,**patch}
        assert not check_auth_public_settings(settings_response(invalid),
                    key="sb_publishable_TEST_TEST_TEST_TEST_TEST")[0],label
    assert not check_auth_public_settings(settings_response(valid_settings,401),
            key="sb_publishable_TEST_TEST_TEST_TEST_TEST")[0]
    assert not check_auth_public_settings(lambda req,n:(200,b"not-json"),
            key="sb_publishable_TEST_TEST_TEST_TEST_TEST")[0]
    assert not check_auth_public_settings(lambda req,n:(200,b"x"*8193),
            key="sb_publishable_TEST_TEST_TEST_TEST_TEST")[0]
    assert not check_auth_public_settings(settings_good,key="invalid-key")[0]
    print("PASS contrôles négatifs locaux : pages, SDK épinglé, JWT et Auth publique, aucun secret.")


def production_test():
    failures=[]
    for path,markers in PAGE_CONTRACTS.items():
        try:
            passed,reason=check_public_page(path,markers)
        except (URLError,TimeoutError,OSError,ValueError):
            passed,reason=False,"échec réseau"
        print(("PASS" if passed else "FAIL")+" page "+path+" : "+reason)
        if not passed:
            failures.append(path)
    for path,markers in JS_SCRIPTS.items():
        try:
            passed,reason=check_js_script(path,markers)
        except (URLError,TimeoutError,OSError,ValueError):
            passed,reason=False,"échec réseau JS"
        print(("PASS" if passed else "FAIL")+" script "+path+" : "+reason)
        if not passed:
            failures.append(path)
    for slug in FUNCTIONS:
        try:
            passed,reason=check_private_gateway(slug)
        except (URLError,TimeoutError,OSError,ValueError):
            passed,reason=False,"échec réseau"
        print(("PASS" if passed else "FAIL")+" JWT "+slug+" : "+reason)
        if not passed:
            failures.append(slug)
    try:
        passed,reason=check_auth_public_settings()
    except (URLError,TimeoutError,OSError,ValueError):
        passed,reason=False,"échec de lecture Auth publique"
    print(("PASS" if passed else "FAIL")+" Auth /settings : "+reason)
    if not passed:
        failures.append("auth_public_settings")
    print("BILAN : "+str(len(PAGE_CONTRACTS)+len(JS_SCRIPTS)+len(FUNCTIONS)+1-len(failures))+
          "/"+str(len(PAGE_CONTRACTS)+len(JS_SCRIPTS)+len(FUNCTIONS)+1)+" contrôles publics.")
    print("Sans authentification, sans données personnelles, sans preuve de réception email.")
    return 1 if failures else 0


def main():
    parser=argparse.ArgumentParser()
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--public",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    return production_test()


if __name__=="__main__":
    raise SystemExit(main())
