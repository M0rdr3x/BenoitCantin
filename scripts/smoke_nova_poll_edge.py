#!/usr/bin/env python3
"""Smoke HTTP non destructif du sondage NOVA déployé, en état fermé."""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
URL = "https://gpvivleexywljowcqkru.supabase.co/functions/v1/nova-civic-poll"
ORIGIN = "https://www.benoitcantin.com"
LOCAL = json.loads((ROOT / "projets/projet-nova/data/sondage-citoyen-v1.json").read_text(encoding="utf-8"))
def request(method: str, origin: str, data: bytes | None = None):
    headers={"Origin":origin,"User-Agent":"NovaCivicPoll-ReadOnlyPreflight/1.0"}
    if data is not None: headers["Content-Type"]="application/json"
    req=Request(URL,data=data,headers=headers,method=method)
    try:
        with urlopen(req,timeout=15) as resp:
            return resp.status,resp.headers,resp.read(65536)
    except HTTPError as err:
        return err.code,err.headers,err.read(65536)

def public_get_with_retry(fetch=request, sleep=time.sleep):
    """Tolérer au maximum deux incidents transitoires GET, jamais un POST."""
    for attempt in range(3):
        try:
            result=fetch("GET",ORIGIN)
        except (URLError,TimeoutError):
            if attempt==2: raise
        else:
            if result[0]!=503 or attempt==2:
                return result
        sleep(0.3 * (2 ** attempt))
    raise AssertionError("Chemin de nouvelle tentative inattendu")


def self_test():
    attempts=[]
    delays=[]
    def temporary(method,origin):
        attempts.append((method,origin))
        return (200 if len(attempts)==3 else 503,{},b"{}")
    assert public_get_with_retry(temporary,delays.append)[0]==200
    assert len(attempts)==3 and delays==[0.3,0.6]
    attempts.clear();delays.clear()
    def forbidden(method,origin):
        attempts.append((method,origin))
        return 403,{},b""
    assert public_get_with_retry(forbidden,delays.append)[0]==403
    assert len(attempts)==1 and not delays
    attempts.clear();delays.clear()
    def unavailable(method,origin):
        attempts.append((method,origin))
        return 503,{},b""
    assert public_get_with_retry(unavailable,delays.append)[0]==503
    assert len(attempts)==3 and delays==[0.3,0.6]
    print("OK : reprise GET bornée et vérifiée; aucun POST répété.")


def main():
    try:
        status, headers, payload = public_get_with_retry()
        assert status==200,f"GET public indisponible: {status}"
        assert headers.get("Access-Control-Allow-Origin")==ORIGIN, "CORS absent"
        assert "no-store" in headers.get("Cache-Control",""),"Réponse cacheable"
        data=json.loads(payload)
        assert data.get("version")==LOCAL["version"]
        assert data.get("open") is False,"ALERTE: scrutin ouvert sans approbation"
        assert data.get("resultsVisible") is False,"ALERTE: instantané publié avant lancement"
        assert data.get("ballots") is None,"ALERTE: compteur trop précis"
        questions=data.get("questions")
        assert isinstance(questions,list) and len(questions)==8
        for remote, local in zip(questions,LOCAL["questions"]):
            assert remote["id"]==local["id"] and remote["text"]==local["text"],"Corpus différent"
            assert remote.get("counts") is None,"Compteurs individuels exposés"
        s, headers, content=request("OPTIONS",ORIGIN)
        assert s==204,f"Preflight invalide: {s}"
        assert headers.get("Access-Control-Allow-Origin")==ORIGIN
        s, _, _=request("GET","https://untrusted.invalid")
        assert s==403,f"Origine étrangère acceptée: {s}"
        # Ne transmet AUCUN bulletin: corps volontairement vide, scrutin fermé.
        s,_,_=request("POST",ORIGIN,b"{}")
        assert s==503,f"Envoi possible malgré la fermeture: {s}"
        print("OK: Edge NOVA en ligne, questionnaire concordant, résultats masqués, CORS, scrutin fail-closed.")
        return 0
    except (AssertionError,URLError,TimeoutError,ValueError) as e:
        print("ECHEC: smoke Edge NOVA :", str(e))
        return 1

if __name__=="__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        raise SystemExit(main())
