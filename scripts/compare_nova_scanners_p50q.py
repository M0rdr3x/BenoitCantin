#!/usr/bin/env python3
"""P50Q: comparer deux validateurs sur 14 scénarios synthétiques.

Les modules sont chargés depuis des arbres Git figés externes.
Aucune fusion, requête réseau, lecture de courriels ou écriture dans le site.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile

BASE = {
    "participer.html": 'contact volontaire, formulaires externes suspendus '
                       '<a href="recrutement.html">Participer</a>'
                       '<a href="confidentialite.html">Confidentialité</a>',
    "avis-legal.html": "Le site n’exploite actuellement pas de formulaire externe",
    "recrutement.html": "Aucun paiement; contact volontaire direct",
    "confidentialite.html": "Les formulaires publics externes sont suspendus.",
    "contact.html": '<a href="mailto:officiellenovaparti@gmail.com">Contact</a>',
}
CASES = (
    ("U01", "URL relative au protocole : Google Forms", "participer.html",
     '<a href="//forms.gle/fictif">Form</a>', None, True),
    ("U02", "URL relative au protocole : Stripe", "participer.html",
     '<a href="//checkout.stripe.com/fictif">Don</a>', None, True),
    ("U03", "URL encodee en parametre de redirection", "contact.html",
     '<a href="/redir?to=https%3A%2F%2Fforms.gle%2Ffictif">Lien</a>', None, True),
    ("U04", "Double encodage en parametre de redirection", "participer.html",
     '<a href="/redir?to=https%253A%252F%252Fforms.gle%252Ffictif">Lien</a>', None, True),
    ("U05", "URL JS et barres obliques echappees", "contact.html",
     r'<script>let target="https:\/\/forms.gle\/fictif";</script>', None, True),
    ("U06", "Ancien paiement PayPal webscr", "recrutement.html",
     '<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_donations">Don</a>', None, True),
    ("U07", "Paiement PayPal chemin paypalme", "recrutement.html",
     '<a href="https://www.paypal.com/paypalme/fictif">Don</a>', None, True),
    ("U08", "Mailto uniquement dans template", "contact.html", "",
     '<template><a href="mailto:officiellenovaparti@gmail.com">Contact</a></template>', True),
    ("U09", "Mailto masque avec attribut hidden", "contact.html", "",
     '<a hidden href="mailto:officiellenovaparti@gmail.com">Contact</a>', True),
    ("U10", "Mailto aria-hidden", "contact.html", "",
     '<a aria-hidden="true" href="mailto:officiellenovaparti@gmail.com">Contact</a>', True),
    ("U11", "Mailto style display none", "contact.html", "",
     '<a style="display: none" href="mailto:officiellenovaparti@gmail.com">Contact</a>', True),
    ("N01", "Domaine ressemblant a forms.gle mais distinct", "contact.html",
     '<a href="https://forms.gle.example.org/page">Source</a>', None, False),
    ("N02", "Lien institutionnel neutre relatif au protocole", "contact.html",
     '<a href="//www.electionsquebec.qc.ca/fr/">Source</a>', None, False),
    ("N03", "Chemin PayPal documentaire neutre", "contact.html",
     '<a href="https://www.paypal.com/cgi-bin/webscr?cmd=help">Documentation</a>', None, False),
)

def module_validate(path: Path):
    if not path.is_file():
        raise OSError("MODULE_ABSENT")
    spec = importlib.util.spec_from_file_location(
        "p50q_candidate_" + str(abs(hash(str(path)))), str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("MODULE_INVALIDE")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.validate

def run_one(func, code):
    with tempfile.TemporaryDirectory(prefix="nova-p50q-") as d:
        root=Path(d)
        for name, html in BASE.items():
            (root/name).write_text(html,encoding="utf-8")
        if code is not None:
            id_,desc,page,append,replacement,expected=code
            content=BASE[page] if replacement is None else replacement
            (root/page).write_text(content+append,encoding="utf-8")
        result=func(root)
        if not isinstance(result,list):
            raise RuntimeError("SORTIE_VALIDATION_INATTENDUE")
        return bool(result)

def compare(before,after):
    cases=[]
    if run_one(before,None) or run_one(after,None):
        return {"statut":"INVALIDE", "anomalie":"BASE_FICTIVE_REJETEE",
                "decision":"NO_GO_AUTOMATIQUE"}
    for row in CASES:
        label,desc,page,add,replace,expected=row
        observed_before=run_one(before,row)
        observed_after=run_one(after,row)
        cases.append({"id":label,"scenario":desc,"rejet_attendu":expected,
                      "ancien_rejet":observed_before,"nouveau_rejet":observed_after,
                      "ancien_conforme":observed_before==expected,
                      "nouveau_conforme":observed_after==expected})
    positive=[x for x in cases if x["rejet_attendu"]]
    negative=[x for x in cases if not x["rejet_attendu"]]
    old_misses=[x["id"] for x in cases if not x["ancien_conforme"]]
    new_misses=[x["id"] for x in cases if not x["nouveau_conforme"]]
    return {
        "statut":"COMPARAISON_EXECUTEE",
        "scenarios":len(cases),
        "scenarios_blocage":len(positive),
        "scenarios_negatifs":len(negative),
        "ecarts_avant":len(old_misses),
        "ecarts_apres":len(new_misses),
        "identifiants_ecarts_avant":old_misses,
        "identifiants_ecarts_apres":new_misses,
        "tests":cases,
        "decision":"NO_GO_AUTOMATIQUE",
        "preuve_de_production":False,
        "revue_humaine_independante":False,
        "note":"Une comparaison de parsers statiques ne prouve pas l'absence de flux externes ni de publication.",
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--report", type=Path)
    opts=p.parse_args(argv)
    try:
        output=compare(module_validate(opts.original),module_validate(opts.candidate))
    except (OSError,ValueError,RuntimeError) as ex:
        output={"statut":"INVALIDE", "anomalie":str(ex), "decision":"NO_GO_AUTOMATIQUE"}
    payload=json.dumps(output,ensure_ascii=False,indent=2)+"\n"
    if opts.report:
        opts.report.parent.mkdir(parents=True,exist_ok=True)
        opts.report.write_text(payload,encoding="utf-8")
    else:
        print(payload,end="")
    return 0 if output["statut"]=="COMPARAISON_EXECUTEE" else 2

if __name__=="__main__":
    raise SystemExit(main())
