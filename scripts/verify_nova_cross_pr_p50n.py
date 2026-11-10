#!/usr/bin/env python3
"""P50N — vérification en lecture seule de 4 arbres Git figés.

Vérifie les blobs réels des trois pages, l'indépendance des correctifs 636/638,
leur identité avec la validation de la PR 640 et le SHA-256 des statuts.
Ne vérifie ni les mandats, ni la production et ne délivre JAMAIS GO.
"""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

ROOT_REL = Path("projets/projet-nova")
PAGES = ("participer.html", "avis-legal.html", "code-conduite.html")
REFS = ("main", "pr636", "pr638", "pr640")
OLD = {
    "participer.html": "formulaire intégré de soutien et de préadhésion",
    "avis-legal.html": "Les formulaires servent uniquement à communiquer",
    "code-conduite.html": "Gouvernance du Parti Nova",
}
EXPECTED_NEW = {
    "participer.html": ("contact volontaire", "formulaires externes", "suspendus"),
    "avis-legal.html": ("n’exploite actuellement pas de formulaire externe",),
    "code-conduite.html": ("Gouvernance du Projet Nova", "non adopté"),
}
FORMS = re.compile(r"(?:formspree\.io|formsubmit\.co|forms\.gle|"
                   r"docs\.google\.com/forms|jotform\.com|typeform\.com)", re.I)
PAYMENTS = re.compile(r"(?:checkout\.stripe\.com|paypal\.com/donate)", re.I)
SHA = re.compile(r"^[0-9a-f]{40}$")

class PageScan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms = 0
        self.external = 0
        self.payments = 0
        self.links = set()
        self.scripts = []
        self.inside_script = False
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "form":
            self.forms += 1
        if tag == "script":
            self.inside_script = True
        for key in ("href", "action", "formaction", "src", "data-url"):
            value = data.get(key)
            if not isinstance(value, str):
                continue
            if FORMS.search(value):
                self.external += 1
            if PAYMENTS.search(value):
                self.payments += 1
            if tag == "a" and key == "href":
                self.links.add(value)
    def handle_endtag(self, tag):
        if tag == "script":
            self.inside_script = False
    def handle_data(self, value):
        if self.inside_script:
            self.scripts.append(value)
    def finalize(self):
        joined = "\n".join(self.scripts)
        if FORMS.search(joined):
            self.external += 1
        if PAYMENTS.search(joined):
            self.payments += 1

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()

def evaluate(manifest: object, trees: dict) -> dict:
    errors = []
    observations = {}
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "P50N-1.0":
        return {"resultat_technique":"INCOMPLET", "ecarts":["SCHEMA_INVALIDE"],
                "decision":"NO_GO_AUTOMATIQUE", "revue_humaine_effectuee":False}
    guards = manifest.get("garde_fous", {})
    if not isinstance(guards, dict) or guards != {
        "fusionner_pr640":False, "etat_publication":"NO_GO",
        "revues_humaines_obtenues":False,
        "habilitations_prouvees":False,
        "mise_en_ligne_verifiee":False
    }:
        errors.append("VERROUS_INSTITUTIONNELS_MODIFIES")
    refs = manifest.get("refs", {})
    if not isinstance(refs, dict) or set(refs) != set(REFS) or any(
        not isinstance(refs.get(ref), str) or not SHA.fullmatch(refs[ref]) for ref in REFS
    ):
        errors.append("REFS_GIT_INVALIDES")
    spec = manifest.get("fichiers", {})
    if not isinstance(spec, dict) or set(spec) != set(PAGES):
        errors.append("MANIFESTE_PAGES_INCOMPLET")
        spec = {}
    blobs = {}
    contents = {}
    for ref in REFS:
        tree = trees.get(ref)
        if not isinstance(tree, Path):
            errors.append("ARBRE_ABSENT_" + ref)
            continue
        for page in PAGES:
            try:
                raw = (tree / ROOT_REL / page).read_bytes()
                decoded = raw.decode("utf-8")
            except (OSError, UnicodeError):
                errors.append("PAGE_NON_LISIBLE_" + ref + "_" + page)
                continue
            blob = git_blob_sha(raw)
            blobs[(ref, page)] = blob
            contents[(ref, page)] = decoded
            expected = spec.get(page, {})
            if not isinstance(expected, dict) or expected.get(ref) != blob:
                errors.append("BLOB_INATTENDU_" + ref + "_" + page)
    if len(blobs) == len(REFS) * len(PAGES):
        for page in PAGES:
            if OLD[page].casefold() not in contents[("main", page)].casefold():
                errors.append("BASE_A_REQUALIFIER_" + page)
        for page in ("participer.html", "avis-legal.html"):
            if blobs[("main", page)] != blobs[("pr638", page)]:
                errors.append("CHEVAUCHEMENT_PR638_" + page)
            if blobs[("pr636", page)] != blobs[("pr640", page)]:
                errors.append("INTEGRATION_DIVERGENTE_PR636_" + page)
        page = "code-conduite.html"
        if blobs[("main", page)] != blobs[("pr636", page)]:
            errors.append("CHEVAUCHEMENT_PR636_" + page)
        if blobs[("pr638", page)] != blobs[("pr640", page)]:
            errors.append("INTEGRATION_DIVERGENTE_PR638_" + page)
        for page in PAGES:
            target = "pr638" if page == "code-conduite.html" else "pr636"
            text = contents[(target, page)]
            folded = text.casefold()
            if OLD[page].casefold() in folded:
                errors.append("ANCIENNE_FORMULATION_" + page)
            if not all(marker.casefold() in folded for marker in EXPECTED_NEW[page]):
                errors.append("CORRECTION_INCOMPLETE_" + page)
            p = PageScan()
            p.feed(text)
            p.finalize()
            if p.forms or p.external or p.payments:
                errors.append("COLLECTE_OU_PAIEMENT_DANS_PAGE_" + page)
            if page == "participer.html" and not {
                "recrutement.html", "confidentialite.html"
            }.issubset(p.links):
                errors.append("LIENS_PARTICIPATION_MANQUANTS")
            observations[page] = {
                "source": target,
                "egal_a_pr640": blobs[(target, page)] == blobs[("pr640", page)],
                "blobs_github_conformes": True if not any(
                    x in errors for x in ("BLOB_INATTENDU_" + target + "_" + page,
                                         "BLOB_INATTENDU_pr640_" + page)) else False,
                "formulaires_html": p.forms,
                "fournisseurs_collecte_detectes": p.external,
                "paiements_detectes": p.payments,
            }
    # Cross-check the original public source manifest's digest after PR638.
    for ref in ("pr638", "pr640"):
        try:
            base = trees[ref] / ROOT_REL
            cfg = json.loads((base / "data/sources.json").read_text(encoding="utf-8"))
            item = cfg["documents"]["statuts"]["parts"][0]
            if item["path"] != "official/reference/statuts.md":
                errors.append("MANIFESTE_STATUTS_CHEMIN_" + ref)
            path = base / "official/reference/statuts.md"
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if item["sha256"].lower() != digest:
                errors.append("MANIFESTE_STATUTS_SHA256_" + ref)
            observations["statuts_"+ref] = {"empreinte_sha256_coherente":item["sha256"].lower()==digest}
        except (KeyError, TypeError, OSError, ValueError, UnicodeError):
            errors.append("MANIFESTE_STATUTS_ILLISIBLE_" + ref)
    return {
        "resultat_technique": "COHERENCE_SNAPSHOT_VERIFIEE" if not errors else "INCOMPLET_OU_ECART",
        "ecarts": sorted(set(errors)),
        "trois_pages": observations,
        "controle_limite_aux_fichiers": True,
        "revue_humaine_effectuee": False,
        "controle_http_production_effectue": False,
        "habilitation_legalement_verifiee": False,
        "decision": "NO_GO_AUTOMATIQUE",
        "condition_reprise": "Relever de nouveau les commits et revues, habilitations, plan de retour et recette apres autorisation."
    }

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",type=Path,default=Path(__file__).resolve().parents[1] /
                   "projets/projet-nova/controles/P50N_INSTANTANE_REVUE_CROISEE.json")
    p.add_argument("--trees-root",type=Path,required=True,
                   help="Répertoire avec sous-dossiers main, pr636, pr638, pr640")
    p.add_argument("--report",type=Path)
    args = p.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        manifest = None
    report = evaluate(manifest, {ref:args.trees_root/ref for ref in REFS})
    output = json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(output,encoding="utf-8")
    else:
        print(output,end="")
    return 0 if report["resultat_technique"]=="COHERENCE_SNAPSHOT_VERIFIEE" else 2

if __name__ == "__main__":
    sys.exit(main())
