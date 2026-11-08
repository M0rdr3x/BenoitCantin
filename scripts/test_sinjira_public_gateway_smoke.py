#!/usr/bin/env python3
"""SINJIRA — parcours HTTP externe, sans identifiants ni changement de données."""
from __future__ import annotations

import argparse
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SITE="https://www.benoitcantin.com"
API="https://gpvivleexywljowcqkru.supabase.co/functions/v1"
PAGE_CONTRACTS={
    "/compte/inscription.html":('data-signup-form','formspree_receipt_opt_in'),
    "/compte/confirmer.html":('data-confirm-button','sinjira-confirm-email.js'),
    "/projets/sinjira/registre/":(
        'data-character-form','formspree_receipt_opt_in',
        'sinjira-character-registry.js?v=24.5.8',
    ),
}
FUNCTIONS=("notify-account-confirmation","submit-character-questionnaire")
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


def self_test():
    for path,markers in PAGE_CONTRACTS.items():
        assert check_public_page(path,markers,
            lambda r:(200,(" ".join(markers)).encode("utf-8")))[0]
        assert not check_public_page(path,markers,
            lambda r:(200,b"<html>ancienne version</html>"))[0]
        assert not check_public_page(path,markers,
            lambda r:(503,b"maintenance"))[0]
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
    print("PASS contrôles négatifs locaux : pages, JWT obligatoire, aucun secret.")


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
    for slug in FUNCTIONS:
        try:
            passed,reason=check_private_gateway(slug)
        except (URLError,TimeoutError,OSError,ValueError):
            passed,reason=False,"échec réseau"
        print(("PASS" if passed else "FAIL")+" JWT "+slug+" : "+reason)
        if not passed:
            failures.append(slug)
    print("BILAN : "+str(len(PAGE_CONTRACTS)+len(FUNCTIONS)-len(failures))+
          "/"+str(len(PAGE_CONTRACTS)+len(FUNCTIONS))+" contrôles publics.")
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
