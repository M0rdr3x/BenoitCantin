#!/usr/bin/env python3
"""P56U: cohérence des 16 articles candidats avec les preuves P56S/P56T/P56O.

Ne certifie ni programme ni finances. Un contrôle textuel ne remplace pas
une revue éditoriale et un avis constitutionnel indépendant.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import sys
from decimal import Decimal

PREFACE="Version de travail du 8 novembre 2026"
MUST_HAVE={
1:("revenu disponible","microsimulation"),
2:("deux prélèvements","paradis fiscaux"),
3:("redevance","redevances"),
4:("42,875 G$","48,570 G$"),
5:("120,433 G$","165,049 G$"),
6:("travailleurs","efficacité"),
7:("crédits","prestations"),
8:("dette","équilibre"),
9:("entreprises","aides"),
10:("contre-tarif","commerce"),
11:("Québec dans le Canada","Québec souverain"),
12:("municipalités","taxe scolaire"),
13:("l'appauvrissement","revenu disponible"),
14:("Publication","publique"),
15:("transition","juridique"),
16:("2031-2032","2036-2037")
}
SOURCE_PATHS=[
"projets/projet-nova/etudes/P56S_TROIS_OPTIONS_FISCALES_2027_2031_ET_CONDITIONS_PROTECTION.json",
"projets/projet-nova/etudes/P56T_BASE_OFFICIELLE_DEPENSES_PORTEFEUILLES_2025_2029_PROTECTION_SERVICES.json",
"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json"
]
def must(ok,why):
    if not ok:
        raise ValueError(why)

def evaluer(text,options,services,cloture,barometre):
    must(type(text) is str and text.startswith("# Projet Nova — Chapitre candidat P56U") and
         PREFACE in text and "NO_GO_AUTOMATIQUE" in text and
         "non adopté" in text, "CHAPITRE_PRESENTE_COMME_ADOPTE")
    headings=re.findall(r"(?m)^### Article ([0-9]+) — ([^\n]+)",text)
    must(len(headings)==16 and [int(n) for n,_ in headings]==list(range(1,17)) and
         all(len(label)>=20 for _,label in headings),
         "SEIZE_ARTICLES_EN_ORDRE_REQUIS")
    pieces=re.split(r"(?m)^### Article [0-9]+ — [^\n]+",text)
    must(len(pieces)==17,"STRUCTURE_TEXTE_NON_VALIDABLE")
    for number,keywords in MUST_HAVE.items():
        chunk=pieces[number].lower()
        must(all(word.lower() in chunk for word in keywords),
             f"ARTICLE_{number}_PROTECTION_OUBLIEE")
    must(options.get("schema_version")=="P56S-1" and
         options.get("decision")=="NO_GO_AUTOMATIQUE" and
         services.get("schema_version")=="P56T-1" and
         services.get("decision")=="NO_GO_AUTOMATIQUE" and
         cloture.get("schema_version")=="P56O-1" and
         cloture.get("definition_terminee",{}).get("etat_actuel_termine") is False and
         barometre.get("score_estimatif")==53 and
         barometre.get("schema_version")=="P55N-1",
         "PREUVES_BASE_NON_CONFIRMEES")
    pivot=next(x for x in services["annees"] if x["exercice"]=="2027-2028")
    must(pivot["noyau_sante_education_superieur_famille_mcad"]=="120433" and
         pivot["total_portefeuilles_publie_mcad"]=="165049" and
         "120,433 G$" in pieces[5] and
         "165,049 G$" in pieces[5],
         "DEPENSES_SERVICES_CHAPITRE_NON_CONCORDANTES")
    option_full=next(x for x in options["options"] if x["id"]=="S3_CIBLE_DEUX_PRELEVEMENTS")
    budget=next(x for x in option_full["resultats_par_exercice"] if x["exercice"]=="2027-2028")
    must(Decimal(budget["recettes_retirees_uniquement_dans_le_test_mcad"])==Decimal(42875) and
         Decimal(budget["solde_loi_sans_nouveau_financement_si_retrait_test_mcad"])==Decimal(-48570) and
         "42,875 G$" in pieces[4] and
         "48,570 G$" in pieces[4],
         "RECETTES_REMPLACEMENT_NON_CONCORDANTES")
    section_end=text[text.index("## Annexe A"): ]
    for literal in (
        "600 montants P52B","720 incidences P52D","20 preuves P52A",
        "53 % estimés","dix portes de clôture non démontrées",
        "Aucune des options S1/S2/S3","Aucune loi adoptée"):
        must(literal in section_end,"ANNEXE_PREUVE_OU_STATUT_OUBLIE_"+literal)
    for path in SOURCE_PATHS:
        must(path in text,"REFERENCE_ABSENTE_"+path)
    must("Aucune fusion" not in text or "main" in text,
         "STATUT_VERSION_NON_EXPLICITE")
    return {
      "jalon":"P56U","articles":16,
      "mentions_pouvoir_achat_protegees":True,
      "services_2027_2028_pivot_mcad":pivot["noyau_sante_education_superieur_famille_mcad"],
      "depenses_totales_portefeuilles_2027_2028_mcad":pivot["total_portefeuilles_publie_mcad"],
      "recettes_a_remplacer_2027_2028_mcad":"42875",
      "deficit_test_2027_2028_mcad":"-48570",
      "conditions_finales_documentairement_demontrees":0,
      "score_interne_estime":53,
      "textes_officiellement_adoptes":False,
      "budget_reforme_certifie":False,
      "programme_termine":False,
      "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    for a in ("chapitre","p56s","p56t","p56o","barometre"):
        ap.add_argument("--"+a,required=True,type=Path)
    ap.add_argument("--exiger-programme-adopte",action="store_true")
    ap.add_argument("--rapport",type=Path)
    args=ap.parse_args(argv)
    if args.exiger_programme_adopte:
        print("REFUS: chapitre non adopté, aucun taux ni budget certifié",file=sys.stderr)
        return 3
    try:
        def load(path):
            return json.loads(path.read_text(encoding="utf-8"))
        result=evaluer(args.chapitre.read_text(encoding="utf-8"),
                       load(args.p56s),load(args.p56t),load(args.p56o),load(args.barometre))
        output=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if args.rapport:
            with args.rapport.open("x",encoding="utf-8") as file:
                file.write(output)
        else:
            print(output,end="")
        return 0
    except (OSError,TypeError,ValueError,KeyError,json.JSONDecodeError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
