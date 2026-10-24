#!/usr/bin/env python3
"""P53G : couverture de 1343 organismes MAMH 2024, sans éliminations interorganismes."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "projets" / "projet-nova" / "etudes"
FILES = {
    "p53g": BASE / "P53G_COUVERTURE_1343_ORGANISMES_2024.json",
    "p53e": BASE / "P53E_PREUVES_HISTORIQUES_MUNICIPALES.json",
    "p53f": BASE / "P53F_FLUX_INTERADMIN_2024.json",
    "p52a": BASE / "P52A_REGISTRE_PREUVES_FISCALES.json",
}
LOCAL = BASE / "sources" / "P53E_MAMH_2024_MUNICIPALITES_LOCALES_SELECTION.csv"
OTHER = BASE / "sources" / "P53G_MAMH_2024_249_ORGANISMES_COMPLEMENTAIRES.csv"
SHA_LOCAL = "11f940092a6a7eb54bf7dc39c6e5b4b44e73c82e9bb34ce7aae2e7278269aa5e"
SHA_OTHER = "65e3bb97fd9a8bb3bfb16eef77f35036e60cb53a0796cdd491894ad7267db9b0"
SHA_ORIGINAL = "151c0a2b1fc0dfac8c8cc3dba04b74f5c49fbb98fdfd78251925959d1ad35fff"
DECIMAL = re.compile(r"^-?\d+(?:\.\d+)?$")
NO_GO = "NO_GO_AUTOMATIQUE"
COLS = (["cod_geo","nom_organisme","type_org","CRIIX00016","CRIIX00018","CRIIX00405"]
        + [f"CRIIX{i:05d}" for i in range(406,418)])
REVENUE_KEYS = ("revenus","taxes","quotes_parts","transferts","services")
MONEY_COLUMNS = {
    "revenus":"CRIIX00405", "taxes":"CRIIX00406",
    "quotes_parts":"CRIIX00408", "transferts":"CRIIX00409",
    "services":"CRIIX00410"
}
GROUPS = [
 ("Municipalité locale",1094,"32367623561","17337284213","846987123","5376508934","4241481713"),
 ("Communauté métropolitaine",2,"120512321","0","103069005","7270072","39292"),
 ("Municipalité régionale de comté",85,"1417481157","0","524693431","505120735","232058279"),
 ("Organisme public de transport",12,"7122045861","0","1291408741","1751297223","3670417807"),
 ("Régie intermunicipale",150,"636013686","0","382050797","75876140","108472472"),
]
SUMS = {"revenus":"41663676586","taxes":"17337284213","quotes_parts":"3148209097",
        "transferts":"7716073104","services":"8252469563"}
GUARDS = (
 "categories_405_406_a_417_reconciliees_ligne_par_ligne",
 "identifiants_geo_distincts_1343",
 "aucun_appariement_payeurs_beneficiaires_etabli",
 "les_sommes_de_recettes_sont_brutes_non_consolidees",
 "certains_organismes_deja_consolides_dans_leurs_rapports",
 "blancs_non_equivalents_a_recettes_nulles",
 "valeurs_negatives_conservees",
 "transferts_non_ajoutes_au_budget_quebec",
 "annees_2024_et_2026_2027_non_assimilables",
 "pas_d_elimination_sans_preuve_transactionnelle",
 "aucun_taux_Nova_calcule"
)

def must(ok, error):
    if not ok:
        raise ValueError(error)

def read(path):
    p=Path(path)
    must(p.is_file() and not p.is_symlink() and
         0 < p.stat().st_size < 800000,"REGISTRE_JSON_ABSENT")
    d=json.loads(p.read_text(encoding="utf-8"))
    must(type(d) is dict,"REGISTRE_DOIT_ETRE_OBJET")
    return d

def dollars(raw):
    if raw == "":
        return None
    must(type(raw) is str and DECIMAL.fullmatch(raw),"MONTANT_NON_NUMERIQUE")
    d=Decimal(raw)
    must(d.is_finite() and d==d.to_integral_value(),"MONTANT_NON_ENTIER")
    return int(d)

def csv_source(path,sha,expected_count):
    p=Path(path)
    must(p.is_file() and not p.is_symlink() and
         0 < p.stat().st_size < 250000,"SOURCE_SELECTION_ABSENTE")
    contents=p.read_bytes()
    must(hashlib.sha256(contents).hexdigest()==sha,"EMP REINTE_SHA256_INCORRECTE".replace(" ",""))
    try:
        reader=csv.DictReader(io.StringIO(contents.decode("utf-8")))
        must(reader.fieldnames==COLS,"COLONNES_INCOMPATIBLES")
        rows=list(reader)
    except (UnicodeDecodeError,csv.Error) as exc:
        raise ValueError("CSV_INVALIDE") from exc
    must(len(rows)==expected_count,"NOMBRE_ORGANISMES_INCORRECT")
    must(all(list(r)==COLS and r.get(None) is None and
             r["cod_geo"] and r["nom_organisme"] and r["type_org"]
             for r in rows),"LIGNE_SOURCE_INCOMPLETE")
    must(len(set(r["cod_geo"] for r in rows))==expected_count,
         "CODE_GEO_DUPLIQUE")
    return rows

def reconstruct(local,other):
    must(len(local)==1094 and len(other)==249,"DEUX_SNAPSHOTS_MANQUANTS")
    must(all(r["type_org"]=="Municipalité locale" for r in local),"LOCALES_NON_LOCALES")
    must(all(r["type_org"]!="Municipalité locale" for r in other),"AUTRES_MAL_CLASSES")
    allrows=local+other
    must(len(set(r["cod_geo"] for r in allrows))==1343,"RECOUVREMENT_IDENTIFIANTS")
    for row in allrows:
        total=dollars(row["CRIIX00405"])
        must(total is not None,"TOTAL_REVENUS_MANQUANT")
        parts=[dollars(row[f"CRIIX{i:05d}"]) for i in range(406,418)]
        must(total==sum(0 if x is None else x for x in parts),
             "CATEGORIES_REVENUS_NON_RECONCILIEES")
    computed=[]
    for group,count,*expected in GROUPS:
        subset=[r for r in allrows if r["type_org"]==group]
        must(len(subset)==count,"TYPE_ORGANISME_INCOMPLET_"+group)
        row={"type_org":group,"effectif":count}
        for key,exp in zip(REVENUE_KEYS,expected):
            values=[dollars(r[MONEY_COLUMNS[key]]) for r in subset]
            row[key]=str(sum(x for x in values if x is not None))
            must(row[key]==exp,"REVENU_INCONCORDANT_"+key+"_"+group)
        computed.append(row)
    totals={k:str(sum(int(x[k]) for x in computed)) for k in REVENUE_KEYS}
    must(totals==SUMS,"SOMMES_GLOBALES_INEXACTES")
    return computed,totals

def validate(d,local,other):
    must(set(d)==set(FILES),"QUATRE_REFERENCES_REQUISES")
    m,e,f,p=(d[x] for x in FILES)
    must(m.get("schema_version")=="P53G-1" and m.get("jalon")=="P53G" and
         m.get("date_reference")=="2026-10-21" and
         m.get("statut")=="DONNEES_REELLES_2024_POUR_1343_ORGANISMES_SANS_CONSOLIDATION_INTERORGANISMES",
         "P53G_SCHEMA_INVALIDE")
    refs=m.get("sources",{})
    must(refs=={
         "p53e":str(FILES["p53e"].relative_to(ROOT)),
         "p53f":str(FILES["p53f"].relative_to(ROOT)),
         "p52a":str(FILES["p52a"].relative_to(ROOT)),
         "locale":str(LOCAL.relative_to(ROOT)),
         "complementaire":str(OTHER.relative_to(ROOT)),
    },"SOURCES_DOCUMENTAIRES_MODIFIEES")
    s=m.get("provenance",{})
    must(s.get("titre")=="Données réelles 2024 — Simple occurrence" and
         s.get("producteur")=="Ministère des Affaires municipales et de l'Habitation" and
         s.get("url")=="https://mamh.gouv.qc.ca/fichiersdonneesouvertes/Données-réelles-2024-SimpleOccurrence.csv" and
         s.get("licence_affichee")=="CC-BY 4.0" and
         s.get("annee")==2024 and
         s.get("original_octets_observes")==20254172 and
         s.get("original_sha256_observe")==SHA_ORIGINAL and
         s.get("original_integral_archive_dans_git") is False and
         s.get("colonnes_originales")==7336 and
         s.get("lignes_originales")==1343 and
         s.get("selection_locale_sha256")==SHA_LOCAL and
         s.get("selection_complementaire_sha256")==SHA_OTHER and
         s.get("selection_complementaire_git_blob")=="1bc877c5f85384ad6538c30df66093483b0bed85" and
         s.get("selection_complementaire_octets")==32233 and
         s.get("selection_colonnes")==18 and
         s.get("contre_avis_comptable_independant_obtenu") is False,
         "PROVENANCE_HISTORIQUE_FALSIFIEE")
    must(e.get("schema_version")=="P53E-1" and
         e.get("bilan",{}).get("municipalites_locales_retenues")==1094 and
         e.get("bilan",{}).get("decision")==NO_GO and
         e.get("sources",{}).get("donnees",{}).get("sha256_derive")==SHA_LOCAL and
         e.get("observations_de_reference",{}).get("revenus_totaux_municipalites_locales_2024_cad")=="32367623561",
         "P53E_SOURCE_MODIFIEE")
    must(f.get("schema")=="P53F-1" and
         f.get("bilan",{}).get("decision")==NO_GO and
         f.get("bilan",{}).get("appariements_confirmes")==0 and
         f.get("totaux",{}).get("montant_eliminations_certifiees") is None,
         "P53F_FAUSSE_CONSOLIDATION")
    must(p.get("status")=="PROPOSITION_NON_ADOPTEE" and
         p.get("automatic_go") is False and
         p.get("financial_model_certified") is False and
         p.get("human_reviews_received") is False and
         len(p.get("required_evidence",[]))==20 and
         all(x.get("statut")=="NON_VALIDE" and
             x.get("preuve_independante_obtenue") is False
             for x in p["required_evidence"]),
         "P52A_PREUVE_MANQUANTE")
    groups,totals=reconstruct(local,other)
    must(m.get("types_organismes")==groups and
         m.get("totaux_bruts_cad")==totals and
         m.get("total_complementaire_cad")=="9296053025" and
         int(groups[0]["revenus"])+9296053025==int(totals["revenus"]),
         "SOMME_INTERGROUPES_FAUSSE")
    must(m.get("addition_brute_quotes_et_transferts_cad")=="10864282201" and
         int(totals["quotes_parts"])+int(totals["transferts"])==10864282201 and
         m.get("eliminations_interorganismes_certifiees_cad") is None and
         m.get("recettes_consolidees_tous_organismes_cad") is None and
         m.get("recettes_equivalentes_budget_2026_2027_mcad") is None and
         m.get("reforme_Nova_rendement_mcad") is None,
         "SOMME_NON_CONSOLIDEE_CONVERTIE_EN_TRESORERIE")
    rules=m.get("controles",{})
    must(type(rules) is dict and set(rules)==set(GUARDS) and
         all(rules[k] is True for k in GUARDS),
         "REGLES_ANTI_DOUBLE_COMPTE_SUPPRIMEES")
    must(m.get("bilan")=={
        "organismes_recenses":1343,"organismes_complementaires_ajoutes":249,
        "types_distincts":5,"appariements_reciproques_recus":0,
        "eliminations_certifiees":0,"preuves_F01_F20_validees":0,
        "valeurs_Nova_inconnues":1320,"taux_Nova_adoptes":0,
        "publication_autorisee":False,"fusion_autorisee":False,
        "adoption_autorisee":False,"decision":NO_GO,
    },"BILAN_FAUSSEMENT_CERTIFIE")
    return {
        "jalon":"P53G","annee_comptable":2024,
        "organismes_denombrables":1343,
        "municipalites_locales":1094,
        "mrc_regies_transport_communautes":249,
        "familles_organismes":5,
        "enveloppe_recettes_brutes_CAD":int(totals["revenus"]),
        "enveloppe_additionnelle_non_locale_CAD":9296053025,
        "quotes_parts_recues_brutes_CAD":int(totals["quotes_parts"]),
        "transferts_recus_bruts_CAD":int(totals["transferts"]),
        "quotes_et_transferts_exposition_brute_CAD":10864282201,
        "reconciliations_des_12_postes_par_organisme":1343,
        "recettes_consolidees_interorganismes_certifiees":False,
        "eliminations_transactionnelles_documentees":0,
        "annees_fiscales_harmonisees":False,
        "originaux_20mo_archives_sur_git":False,
        "preuves_F01_F20_non_validees":20,
        "parametres_Nova_inconnus":1320,
        "publication_autorisee":False,"fusion_autorisee":False,
        "adoption_autorisee":False,"decision":NO_GO
    }

def csv_summary(groups):
    out=io.StringIO(newline="")
    w=csv.writer(out,lineterminator="\n")
    w.writerow(["annee","type_organisme","nombre","revenus_bruts_CAD",
                "taxes_CAD","quotes_parts_CAD","transferts_CAD",
                "services_CAD","montant_elimine_CERTIFIE"])
    for row in groups:
        w.writerow([2024,row["type_org"],row["effectif"],row["revenus"],
                    row["taxes"],row["quotes_parts"],row["transferts"],
                    row["services"],""])
    return out.getvalue()

def create(path,txt):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8",newline="") as f:
        f.write(txt)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for k,v in FILES.items():
        parser.add_argument("--"+k,type=Path,default=v)
    parser.add_argument("--selection-locale",type=Path,default=LOCAL)
    parser.add_argument("--selection-complementaire",type=Path,default=OTHER)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--export-csv",type=Path)
    parser.add_argument("--exiger-consolidation",action="store_true")
    args=parser.parse_args(argv)
    try:
        data={k:read(getattr(args,k)) for k in FILES}
        local=csv_source(args.selection_locale,SHA_LOCAL,1094)
        other=csv_source(args.selection_complementaire,SHA_OTHER,249)
        result=validate(data,local,other)
        groups=data["p53g"]["types_organismes"]
        if args.rapport and args.export_csv:
            must(args.rapport.resolve()!=args.export_csv.resolve(),"DEUX_SORTIES_IDENTIQUES")
        if args.rapport:create(args.rapport,json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        if args.export_csv:create(args.export_csv,csv_summary(groups))
        if not args.rapport and not args.export_csv:
            print(json.dumps(result,ensure_ascii=False,indent=2))
        return 3 if args.exiger_consolidation else 0
    except (OSError,ValueError,UnicodeError,TypeError,KeyError,InvalidOperation) as exc:
        print(json.dumps({"jalon":"P53G","statut":"REJET_CONTROLE",
              "categorie":type(exc).__name__,
              "publication_autorisee":False,"fusion_autorisee":False,
              "adoption_autorisee":False,"decision":NO_GO},ensure_ascii=False))
        return 2
if __name__=="__main__":
    sys.exit(main())
