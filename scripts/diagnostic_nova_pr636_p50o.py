#!/usr/bin/env python3
"""P50O — diagnostic en lecture seule du validateur candidat PR 636.

Charge explicitement le module Python depuis un checkout local au SHA figé.
N'inspecte aucune personne, n'ouvre aucun courriel, ne déploie rien et ne délivre jamais de GO.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import tempfile

CANDIDATE_COMMIT = "6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb"
FILES = (
    "participer.html", "avis-legal.html", "recrutement.html",
    "confidentialite.html", "contact.html"
)
BASE = {
    "participer.html": (
        'contact volontaire, formulaires externes suspendus '
        '<a href="recrutement.html">Participer</a>'
        '<a href="confidentialite.html">Confidentialité</a>'
    ),
    "avis-legal.html": "Le site n’exploite actuellement pas de formulaire externe.",
    "recrutement.html": "Aucun paiement, contact volontaire direct",
    "confidentialite.html": "Les formulaires publics externes sont suspendus.",
    "contact.html": (
        '<a href="mailto:officiellenovaparti@gmail.com">Écrire au Projet Nova</a>'
    ),
}
PROBES = (
    {
        "id":"C01", "categorie":"controle_positif",
        "name":"Balise form explicite",
        "page":"contact.html",
        "append":'<form action="/post"></form>',
        "expected_rejection":True
    },
    {
        "id":"C02", "categorie":"controle_positif",
        "name":"Fournisseur Formspree explicite",
        "page":"participer.html",
        "append":'<iframe src="https://formspree.io/f/example"></iframe>',
        "expected_rejection":True
    },
    {
        "id":"C03", "categorie":"controle_positif",
        "name":"Ancien PDF de soutien lié",
        "page":"participer.html",
        "append":'<a href="visionneuse.html?doc=formulaire-soutien">Ancien document</a>',
        "expected_rejection":True
    },
    {
        "id":"F01", "categorie":"couverture_incomplete",
        "name":"Lien vers Google Forms",
        "page":"participer.html",
        "append":'<a href="https://forms.gle/EXEMPLE">Formulaire externe</a>',
        "expected_rejection":True
    },
    {
        "id":"F02", "categorie":"couverture_incomplete",
        "name":"Iframe Google Forms",
        "page":"participer.html",
        "append":'<iframe src="https://docs.google.com/forms/d/e/EXEMPLE/viewform"></iframe>',
        "expected_rejection":True
    },
    {
        "id":"F03", "categorie":"couverture_incomplete",
        "name":"Lien Typeform",
        "page":"contact.html",
        "append":'<a href="https://exemple.typeform.com/to/ABC">Formulaire</a>',
        "expected_rejection":True
    },
    {
        "id":"F04", "categorie":"couverture_incomplete",
        "name":"Lien Jotform",
        "page":"contact.html",
        "append":'<a href="https://www.jotform.com/form/EXEMPLE">Formulaire</a>',
        "expected_rejection":True
    },
    {
        "id":"F05", "categorie":"couverture_incomplete",
        "name":"Paiement Stripe Checkout",
        "page":"participer.html",
        "append":'<a href="https://checkout.stripe.com/c/pay/EXEMPLE">Payer</a>',
        "expected_rejection":True
    },
    {
        "id":"F06", "categorie":"couverture_incomplete",
        "name":"Bouton don PayPal",
        "page":"recrutement.html",
        "append":'<a href="https://www.paypal.com/donate?hosted_button_id=EXEMPLE">Don</a>',
        "expected_rejection":True
    },
    {
        "id":"F07", "categorie":"couverture_incomplete",
        "name":"Chaîne mailto sans lien actif dans un commentaire HTML",
        "page":"contact.html",
        "replace":'<!-- mailto:officiellenovaparti@gmail.com -->',
        "expected_rejection":True
    },
    {
        "id":"F08", "categorie":"couverture_incomplete",
        "name":"Script référant à un fournisseur externe non reconnu",
        "page":"contact.html",
        "append":'<script>const url="https://forms.gle/EXEMPLE";</script>',
        "expected_rejection":True
    }
)


def make_fixture(directory: Path, override: dict | None=None) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for page in FILES:
        value = BASE[page]
        if override and override["page"] == page:
            value = override.get("replace", value) + override.get("append", "")
        (directory/page).write_text(value, encoding="utf-8")


def load_candidate(path: Path):
    if not path.is_file():
        raise FileNotFoundError("VALIDATEUR_CANDIDAT_NON_DISPONIBLE")
    spec = importlib.util.spec_from_file_location("nova_p50o_candidat", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("MODULE_CANDIDAT_ILLISIBLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "validate", None)):
        raise RuntimeError("FONCTION_VALIDATE_ABSENTE")
    return module.validate


def diagnose(validate):
    with tempfile.TemporaryDirectory(prefix="nova-p50o-") as td:
        root = Path(td)/"site"
        make_fixture(root)
        baseline = validate(root)
        cases = []
        if baseline:
            return {
                "audit": "BASE_NON_CONFORME",
                "anomalies": ["BASE_FICTIVE_REJETEE"],
                "cas": [], "angles_morts_reproduits": 0,
                "decision": "NO_GO_AUTOMATIQUE",
            }
        for case in PROBES:
            make_fixture(root, case)
            messages = validate(root)
            if not isinstance(messages, list):
                return {
                    "audit":"FORMAT_IMPREVU", "anomalies":["VALIDATE_RENVOIE_AUTRE_CHOSe_QU_UNE_LISTE"],
                    "cas":cases,"angles_morts_reproduits":0,
                    "decision":"NO_GO_AUTOMATIQUE",
                }
            detected = bool(messages)
            cases.append({
                "id":case["id"],"type":case["categorie"],"objet":case["name"],
                "rejet_attendu":case["expected_rejection"],"rejet_observe":detected,
                "ecart":case["expected_rejection"] and not detected,
                "nombre_signaux":len(messages),
            })
        miss = [x for x in cases if x["ecart"]]
        return {
            "audit":"DIAGNOSTIC_TERMINE",
            "cas":cases,"cas_total":len(cases),
            "angles_morts_reproduits":len(miss),
            "identifiants_ecarts":[x["id"] for x in miss],
            "aucune_surface_reelle_ouverte":True,
            "approbation_humaine":False,"autorisation_juridique":False,
            "decision":"NO_GO_AUTOMATIQUE",
            "limite":"Les contre-exemples montrent des lacunes de détection du validateur et non une collecte effectivement active sur le site.",
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True,
                        help="scripts/validate_nova_publication_p50b.py du checkout figé PR 636")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = diagnose(load_candidate(args.candidate))
    except (OSError, ValueError, RuntimeError) as exc:
        result = {
            "audit":"NON_EXECUTABLE",
            "anomalies":[str(exc)],
            "decision":"NO_GO_AUTOMATIQUE",
        }
    result["candidate_commit"] = CANDIDATE_COMMIT
    result["horodatage_utc"] = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if result["audit"] == "DIAGNOSTIC_TERMINE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
