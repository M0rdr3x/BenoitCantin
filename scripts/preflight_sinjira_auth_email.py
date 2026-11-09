#!/usr/bin/env python3
"""Lecture seule des réglages Auth hébergés; aucune sortie de secret ni modèle."""
import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT="gpvivleexywljowcqkru"
SITE="https://www.benoitcantin.com"
CONFIRM=SITE+"/compte/confirmer.html"
API="https://api.supabase.com/v1/projects/"+PROJECT+"/config/auth"
WORKFLOW=Path(__file__).resolve().parents[1]/".github/workflows/sinjira-auth-email-production-preflight.yml"


def audit(config):
    passed,failed,warnings=[],[],[]
    def check(label,valid):
        (passed if valid else failed).append(label)
    if not isinstance(config,dict):
        return [],["Configuration Auth non reconnue"],[]
    check("Site URL",isinstance(config.get("site_url"),str) and config["site_url"].rstrip("/")==SITE)
    check("Inscription ouverte",config.get("disable_signup") is False)
    check("Courriel activé",config.get("external_email_enabled") is True)
    check("Confirmation requise",config.get("mailer_autoconfirm") is False)
    allowed=config.get("uri_allow_list")
    urls={s.strip().rstrip("/") for s in allowed.split(",")} if isinstance(allowed,str) else set()
    check("URL de retour permise",bool(urls & {CONFIRM,SITE+"/**"}))
    content=config.get("mailer_templates_confirmation_content")
    check("Modèle sécurisé par fragment",isinstance(content,str) and
          CONFIRM+"#token_hash={{ .TokenHash }}" in content and
          "type=email" in content and "{{ .ConfirmationURL }}" not in content)
    subject=config.get("mailer_subjects_confirmation")
    check("Objet de confirmation défini",isinstance(subject,str) and bool(subject.strip()))
    check("MFA TOTP disponible",config.get("mfa_totp_enroll_enabled") is True and
          config.get("mfa_totp_verify_enabled") is True)
    minlength=config.get("password_min_length")
    check("Longueur minimale douze",type(minlength) is int and minlength>=12)
    # Ces paramètres existent dans GET /config/auth. Leur présence ne valide ni
    # les secrets SMTP masqués par l'API ni la livraison des messages.
    smtp_host=config.get("smtp_host")
    check("Serveur SMTP personnalisé renseigné",
          isinstance(smtp_host,str) and bool(smtp_host.strip()) and
          smtp_host.strip().lower() not in ("localhost","127.0.0.1","0.0.0.0","::1"))
    smtp_port=config.get("smtp_port")
    port_text=str(smtp_port).strip() if type(smtp_port) in (int,str) else ""
    check("Port SMTP valide",port_text.isdecimal() and 1<=int(port_text)<=65535)
    sender=config.get("smtp_admin_email")
    check("Adresse expéditrice SMTP valide",
          isinstance(sender,str) and 0<len(sender)<=254 and
          sender.count("@")==1 and "." in sender.rsplit("@",1)[-1] and
          not any(c.isspace() for c in sender))
    smtp_user=config.get("smtp_user")
    check("Identifiant SMTP renseigné",isinstance(smtp_user,str) and bool(smtp_user.strip()))
    warnings.append("SMTP : secret et livraison réelle non vérifiables par ce prévol")
    if config.get("password_hibp_enabled") is not True:
        warnings.append("Protection HIBP absente ou non vérifiée; offre Supabase à confirmer")
    return passed,failed,warnings


def selftest():
    workflow=WORKFLOW.read_text(encoding="utf-8")
    assert "environment: production" in workflow
    assert "workflow_dispatch:" in workflow
    assert "PREFLIGHT-READ-ONLY" in workflow
    assert "secrets.SUPABASE_ACCESS_TOKEN" in workflow
    # Aucun téléchargement tiers de Python: le runner Ubuntu 24.04 fournit
    # Python 3.12, validé avant l'auto-test et avant la lecture privée.
    assert "actions/setup-python@" not in workflow
    assert workflow.count("python3 -c 'import sys; assert sys.version_info[:2] == (3, 12)") == 2
    assert workflow.count("environment: production") == 1
    assert workflow.count("github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'") == 1
    assert workflow.count("secrets.SUPABASE_ACCESS_TOKEN") == 1
    assert workflow.count("python3 scripts/preflight_sinjira_auth_email.py --remote") == 1
    for illegal in ("--request PATCH","--request POST","--request DELETE","--request PUT","supabase db"):
        assert illegal not in workflow,"Méthode mutante interdite"
    good={"site_url":SITE,"disable_signup":False,"external_email_enabled":True,
          "mailer_autoconfirm":False,"uri_allow_list":CONFIRM,
          "mailer_templates_confirmation_content":
              '<a href="'+CONFIRM+'#token_hash={{ .TokenHash }}&amp;type=email">Confirmer</a>',
          "mailer_subjects_confirmation":"Confirmez votre compte",
          "mfa_totp_enroll_enabled":True,"mfa_totp_verify_enabled":True,
          "password_min_length":12,"password_hibp_enabled":False,
          "smtp_host":"smtp.example.org","smtp_port":"587",
          "smtp_admin_email":"no-reply@example.org","smtp_user":"smtp-account"}
    ok,bad,warn=audit(good)
    assert len(ok)==13 and not bad and len(warn)==2
    mutations=[
        ({"site_url":"https://invalid.example"},"Site URL"),
        ({"disable_signup":True},"Inscription ouverte"),
        ({"mailer_autoconfirm":True},"Confirmation requise"),
        ({"uri_allow_list":SITE+"/profile"},"URL de retour permise"),
        ({"mailer_templates_confirmation_content":'<a href="{{ .ConfirmationURL }}">Cliquez</a>'},"Modèle sécurisé par fragment"),
        ({"mailer_subjects_confirmation":""},"Objet de confirmation défini"),
        ({"mfa_totp_verify_enabled":False},"MFA TOTP disponible"),
        ({"password_min_length":8},"Longueur minimale douze"),
        ({"external_email_enabled":False},"Courriel activé"),
        ({"smtp_host":""},"Serveur SMTP personnalisé renseigné"),
        ({"smtp_host":"127.0.0.1"},"Serveur SMTP personnalisé renseigné"),
        ({"smtp_port":"not-a-port"},"Port SMTP valide"),
        ({"smtp_port":"0"},"Port SMTP valide"),
        ({"smtp_admin_email":"not-an-email"},"Adresse expéditrice SMTP valide"),
        ({"smtp_user":""},"Identifiant SMTP renseigné"),
    ]
    for update,label in mutations:
        _,failed,_=audit({**good,**update})
        assert label in failed,"Régression non détectée : "+label
    assert len(audit({})[1])==13
    assert not audit({**good,"uri_allow_list":SITE+"/**"})[1]
    print("OK prévol Auth : treize contrats, quinze régressions et wildcard testés.")


def remote():
    token=os.environ.get("SUPABASE_ACCESS_TOKEN","").strip()
    if not token:
        print("ÉCHEC : accès Management API réservé à l'environnement production")
        return 2
    request=Request(API,headers={"Authorization":"Bearer "+token,
                                "Accept":"application/json"},method="GET")
    try:
        with urlopen(request,timeout=18) as response:
            if response.status!=200:
                raise ValueError()
            raw=response.read(5_000_001)
        if len(raw)>5_000_000:
            raise ValueError()
        config=json.loads(raw)
    except (HTTPError,URLError,OSError,TimeoutError,ValueError):
        print("ÉCHEC : lecture Auth impossible (aucune donnée privée affichée)")
        return 2
    passed,failed,warnings=audit(config)
    for value in passed:
        print("PASS :",value)
    for value in failed:
        print("ÉCHEC :",value)
    for value in warnings:
        print("AVERTISSEMENT :",value)
    print("BILAN :",len(passed),"OK,",len(failed),"à corriger,",len(warnings),"avertissement(s)")
    print("Pas de changement de configuration ni de preuve de livraison de courriel.")
    return 1 if failed else 0


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--remote",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        selftest()
        raise SystemExit(0)
    raise SystemExit(remote())
