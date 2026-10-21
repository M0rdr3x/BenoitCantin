#!/usr/bin/env python3
"""P53E: reproduire 1094 comptes municipaux 2024 MAMH, sans consolidation fiscale."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "p53e":D/"P53E_PREUVES_HISTORIQUES_MUNICIPALES.json",
 "p53d":D/"P53D_ACQUISITION_MUNICIPALE_2024.json",
 "p53c":D/"P53C_SOURCE_PRIMAIRE_ARC_ET_LACUNES_MUNICIPALES.json",
 "lacunes":D/"P53A_LACUNES_HORS_PERIMETRE.json",
 "p53a":D/"P53A_REGISTRE_RECETTES_ET_COMPETENCES.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
CSV_SOURCE=D/"sources"/"P53E_MAMH_2024_MUNICIPALITES_LOCALES_SELECTION.csv"
DESC_SOURCE=D/"sources"/"P53E_MAMH_2024_DICTIONNAIRE_SELECTION.json"
EXPECTED_CSV_SHA="11f940092a6a7eb54bf7dc39c6e5b4b44e73c82e9bb34ce7aae2e7278269aa5e"
EXPECTED_DESC_SHA="4b895a835dbe2d1090a6c576f013b88bc43843ab512de1b4a97c3deab35caedb"
RAW_SOURCE_SHA="151c0a2b1fc0dfac8c8cc3dba04b74f5c49fbb98fdfd78251925959d1ad35fff"
RAW_DICT_SHA="23cd037a93d0ea7a8acd21a768838df8b6cd6a88d827778be68ee82f5186f542"
MAMH_BASE="https://mamh.gouv.qc.ca/fichiersdonneesouvertes/"
BASE_COLS=["cod_geo","nom_organisme","type_org"]
METRICS={
 "CRIIX00016":(1093,"15085531572"),
 "CRIIX00018":(1093,"13325713274"),
 "CRIIX00405":(1094,"32367623561"),
 "CRIIX00406":(1093,"17337284213"),
 "CRIIX00407":(1011,"1001301216"),
 "CRIIX00408":(467,"846987123"),
 "CRIIX00409":(1085,"5376508934"),
 "CRIIX00410":(1073,"4241481713"),
 "CRIIX00411":(1092,"1570344297"),
 "CRIIX00412":(922,"406458649"),
 "CRIIX00413":(315,"297962354"),
 "CRIIX00414":(1089,"372348360"),
 "CRIIX00415":(1064,"907643296"),
 "CRIIX00416":(25,"1135268"),
 "CRIIX00417":(16,"8168138"),
}
COLUMNS=BASE_COLS+list(METRICS)
ADDENDS=[f"CRIIX{i:05d}" for i in range(406,418)]
RULES={
 "taxes_foncieres_incluses_dans_taxes_totales",
 "total_revenus_inclut_taxes_et_transferts",
 "autres_revenus_hors_taxes_et_transferts_inclut_possiblement_quotes_parts_interadmin",
 "transfer_comptable_pas_a_additionner_aux_comptes_provinciaux",
 "filtre_municipalites_locales_ne_vaut_pas_tout_secteur_municipal",
 "source_extraite_et_filtre_intermediaire_pas_archive_integrale",
 "fichier_brut_modifiable_journalierement_retelecharger_et_empreinter",
 "taux_taxe_Nova_non_derivable_des_comptes_2024",
 "exercice_2024_pas_exercice_2026_2027",
 "aucune_certification_externe_des_totaux",
 "blanc_foncier_pas_recette_zero",
}
DEC=re.compile(r"^-?\d+(?:\.\d+)?$")
NO_GO="NO_GO_AUTOMATIQUE"

def require(ok,message):
 if not ok:raise ValueError(message)

def read(path):
 p=Path(path)
 require(p.is_file() and not p.is_symlink() and
         0<p.stat().st_size<750000,"REGISTRE_ABSENT_OU_DANGEREUX")
 obj=json.loads(p.read_text(encoding="utf-8"))
 require(type(obj) is dict,"JSON_OBJECT_REQUIS")
 return obj

def money(s):
 require(type(s) is str and bool(DEC.fullmatch(s)),"MONTANT_MUNICIPAL_INVALIDE")
 val=Decimal(s)
 require(val.is_finite() and val==val.to_integral_value(),"MONTANT_MUNICIPAL_NON_ENTIER")
 return int(val)

def load_snapshots(csv_path=CSV_SOURCE,desc_path=DESC_SOURCE):
 csv_path,desc_path=Path(csv_path),Path(desc_path)
 require(csv_path.is_file() and not csv_path.is_symlink() and
         csv_path.stat().st_size==136871,"EXTRACTION_CSV_ABSENTE")
 require(desc_path.is_file() and not desc_path.is_symlink() and
         0<desc_path.stat().st_size<20000,"DICTIONNAIRE_EXTRAIT_ABSENT")
 raw=csv_path.read_bytes()
 desc_raw=desc_path.read_bytes()
 require(hashlib.sha256(raw).hexdigest()==EXPECTED_CSV_SHA,
         "CSV_ARCHIVE_SHA256_INVALIDE")
 require(hashlib.sha256(desc_raw).hexdigest()==EXPECTED_DESC_SHA,
         "DICTIONNAIRE_ARCHIVE_SHA256_INVALIDE")
 try:rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
 except UnicodeDecodeError as err:raise ValueError("CSV_NON_UTF8") from err
 require(len(rows)==1094,"NOMBRE_MUNICIPALITES_INCORRECT")
 require(list(rows[0])==COLUMNS,"CHAMPS_SOURCE_INEXACTS")
 require(all(list(row)==COLUMNS for row in rows),"SCHEMA_LIGNE_INVALIDE")
 codes=[r["cod_geo"] for r in rows]
 require(len(set(codes))==1094,"CODE_MUNICIPAL_DUPLIQUE")
 require(all(r["type_org"]=="Municipalité locale" and
             bool(r["cod_geo"]) and bool(r["nom_organisme"]) for r in rows),
         "ORGANISME_HORS_PERIMETRE")
 dictionary=json.loads(desc_raw.decode("utf-8"))
 require(type(dictionary) is list and len(dictionary)==15,
         "QUINZE_CODES_DOCUMENTES_REQUIS")
 desc_by={}
 for entry in dictionary:
  require(type(entry) is dict and set(entry)=={
    "Code de postes","Sous-section","Sujet",
    "Facettes (exercice - type de données - consolidation - compétences - spécifique)"
  },"DESCRIPTION_ENTREE_INVALIDE")
  code=entry["Code de postes"]
  require(code in METRICS and code not in desc_by and
          entry["Sous-section"]==("S27" if code.startswith("CRIIX000") else "S7") and
          "Exercice en cours - Réalisations - Intégral - Intégral" in
           entry["Facettes (exercice - type de données - consolidation - compétences - spécifique)"] and
          type(entry["Sujet"]) is str and len(entry["Sujet"])>28,
          "CODE_COMPTABLE_NON_VERIFIE")
  desc_by[code]=entry
 require(list(sorted(desc_by))==sorted(METRICS),"DICTIONNAIRE_INCOMPLET")
 require("Taxes - Sur la valeur foncière" in desc_by["CRIIX00016"]["Sujet"] and
         "Taxe foncière générale" in desc_by["CRIIX00018"]["Sujet"] and
         desc_by["CRIIX00405"]["Sujet"].endswith("Revenus") and
         desc_by["CRIIX00406"]["Sujet"].endswith("Revenus - Taxes") and
         desc_by["CRIIX00409"]["Sujet"].endswith("Revenus - Transferts"),
         "INTERPRETATION_COMPTABLE_INCORRECTE")
 return rows,dictionary

def compute(rows):
 require(type(rows) is list and len(rows)==1094,"1094_COMPTES_ATTENDUS")
 stats={}
 for key,(expected_present,expected_sum) in METRICS.items():
  vals=[money(r[key]) for r in rows if r[key].strip()]
  stats[key]={"observations_non_vides":len(vals),
              "blancs":len(rows)-len(vals),
              "total_cad":str(sum(vals))}
  require(stats[key]=={
    "observations_non_vides":expected_present,
    "blancs":1094-expected_present,
    "total_cad":expected_sum
  },"DECOMPOSITION_HISTORIQUE_NON_CONCORDANTE_"+key)
 discrepancies=0
 for r in rows:
  parent=money(r["CRIIX00405"])
  children=sum(money(r[k]) if r[k].strip() else 0 for k in ADDENDS)
  if parent!=children:discrepancies+=1
 require(discrepancies==0,"CATEGORIES_MUNICIPALES_NON_RECONCILIEES")
 blanks=[r["cod_geo"] for r in rows if not r["CRIIX00016"].strip()]
 require(blanks==["45080"],"FONCIER_SANS_DECLARATION_NON_SIGNALE")
 prop=int(stats["CRIIX00016"]["total_cad"])
 tax=int(stats["CRIIX00406"]["total_cad"])
 transfers=int(stats["CRIIX00409"]["total_cad"])
 total=int(stats["CRIIX00405"]["total_cad"])
 other=total-tax-transfers
 require(prop<=tax<=total and other==9653830414,
         "PARTITIONS_REVENU_SANS_DOUBLE_COMPTE_INCORRECTES")
 return stats,{"foncier_cad":str(prop),"taxes_cad":str(tax),
   "transferts_cad":str(transfers),"revenus_cad":str(total),
   "hors_taxes_hors_transferts_cad":str(other),
   "ecarts_de_rapprochement":discrepancies,
   "code_foncier_manquant":blanks}

def audit(docs,rows,dictionary):
 require(type(docs) is dict and set(docs)==set(FILES),"SIX_REGISTRES_ATTENDUS")
 m,d,c,g,a,p=(docs[key] for key in FILES)
 require(m.get("schema_version")=="P53E-1" and m.get("jalon")=="P53E" and
         m.get("date_reference")=="2026-10-21" and
         m.get("statut")==
          "OBSERVATIONS_MUNICIPALES_HISTORIQUES_2024_SANS_CONSOLIDATION_INTERGOUVERNEMENTALE",
         "P53E_REVENDICATIONS_NON_CONFORMES")
 require(m.get("references")=={
   key:str(FILES[key].relative_to(ROOT)) for key in FILES if key!="p53e"
 }, "REFERENCES_PREUVES_AMONT_BRISÉES")
 src=m.get("sources",{}).get("donnees",{})
 require(src.get("organisme")=="Ministère des Affaires municipales et de l'Habitation" and
         src.get("url")==MAMH_BASE+"Données-réelles-2024-SimpleOccurrence.csv" and
         src.get("resource_id")=="f36db61a-86ea-405c-9fd5-c1453c68bd60" and
         src.get("license")=="CC-BY 4.0" and
         src.get("telechargement_date")=="2026-10-21" and
         src.get("metadata_resource_modification")=="2026-10-21T08:20:28" and
         src.get("taille_octets_original")=="20254172" and
         src.get("sha256_original_telecharge")==RAW_SOURCE_SHA and
         src.get("original_brut_entier_archive_dans_depot") is False and
         src.get("annee_comptable")=="2024" and
         src.get("fichier_derive_local")==str(CSV_SOURCE.relative_to(ROOT)) and
         src.get("taille_derive_octets")=="136871" and
         src.get("sha256_derive")==EXPECTED_CSV_SHA and
         src.get("blob_git_derive")=="420df2642a6d96174477f5ead9501070dc491f3c" and
         src.get("avis_expert_independant_authentifie") is False,
         "SOURCE_MAMH_NON_REPRODUCTIBLE")
 srcd=m.get("sources",{}).get("dictionnaire",{})
 require(srcd.get("url")==MAMH_BASE+"Données-réelles-2024-DescriptionPoste.csv" and
         srcd.get("resource_id")=="b2d411ac-2a30-4e97-8188-9a112042e383" and
         srcd.get("taille_octets_original")=="1749357" and
         srcd.get("sha256_original_telecharge")==RAW_DICT_SHA and
         srcd.get("original_brut_entier_archive_dans_depot") is False and
         srcd.get("description_retenue")==str(DESC_SOURCE.relative_to(ROOT)) and
         srcd.get("sha256_description_retenue")==EXPECTED_DESC_SHA and
         srcd.get("blob_git_description_retenue")=="ee5f8d85adb370b9f1f55406e3dc4896a4b9bd5e" and
         srcd.get("avis_expert_independant_authentifie") is False,
         "DICTIONNAIRE_MAMH_NON_REPRODUCTIBLE")
 meth=m.get("methode",{})
 require(meth.get("annee")==2024 and
         meth.get("fichier_brut_lignes_organismes")==1343 and
         meth.get("fichier_brut_colonnes")==7336 and
         meth.get("dictionnaire_lignes")==8003 and
         meth.get("filtre_type_org_egal")=="Municipalité locale" and
         meth.get("municipalites_locales_retenues")==1094 and
         meth.get("codes_geo_distincts")==1094 and
         meth.get("organismes_hors_filtre")==249 and
         meth.get("champ_territorial")=="cod_geo" and
         meth.get("colonnes_derivees")==COLUMNS and
         meth.get("absence_doublons_codes_geo_verifiee") is True and
         meth.get("somme_en_dollars_CAD") is True and
         meth.get("champs_vides_ne_signifient_pas_zero_declaration") is True and
         meth.get("nombres_decimal_non_arrondis_avant_sommation") is True and
         meth.get("rapprochement_categories_CRIIX00406_a_CRIIX00417_vers_CRIIX00405") is True and
         meth.get("ecarts_de_rapprochement_individuels")==0 and
         meth.get("valeurs_absentes_comptees_comme_0_uniquement_dans_controle_additif") is True and
         meth.get("inclusion_périmetre")=="MUNICIPALITES_LOCALES_SEULEMENT" and
         meth.get("n_inclut_pas_MRC_regies_organismes_transport") is True,
         "METHODE_SOURCES_NON_VERIFIEE")
 stats,results=compute(rows)
 captured=m.get("champs_reconciliation")
 require(type(captured) is list and len(captured)==len(METRICS) and
         [r.get("code") for r in captured]==list(METRICS),"CODES_FISCAUX_A_RECONCILIER")
 for item in captured:
  key=item["code"]
  require(item.get("observations_non_vides")==stats[key]["observations_non_vides"] and
          item.get("blancs")==stats[key]["blancs"] and
          item.get("total_cad")==stats[key]["total_cad"] and
          item.get("provenance")=="MAMH_2024_MUNICIPALITES_LOCALES",
          "STATISTIQUE_MUNICIPALE_MODIFIEE")
 obs=m.get("observations_de_reference",{})
 require(obs.get("taxes_foncieres_toutes_categories_2024_cad")==results["foncier_cad"] and
         obs.get("taxe_fonciere_generale_sous_categorie_2024_cad")=="13325713274" and
         obs.get("taxes_municipales_totales_2024_cad")==results["taxes_cad"] and
         obs.get("revenus_totaux_municipalites_locales_2024_cad")==results["revenus_cad"] and
         obs.get("transferts_municipalites_locales_2024_cad")==results["transferts_cad"] and
         obs.get("autres_revenus_hors_taxes_et_transferts_2024_cad")==results["hors_taxes_hors_transferts_cad"] and
         obs.get("montant_net_sans_doublon_tous_paliers_2024_cad") is None and
         obs.get("montant_comparable_budget_2026_2027_mcad") is None and
         obs.get("revenus_du_systeme_nova_mcad") is None and
         obs.get("codes_taxation_fonciere_sans_valeur")==results["code_foncier_manquant"] and
         obs.get("annee")==2024,"OBSERVATIONS_DEVENUES_TAXES_NOVA")
 rules=m.get("périmètre_et_risques")
 require(type(rules) is dict and set(rules)==RULES and
         all(rules[k] is True for k in RULES),"AVERTISSEMENTS_CONSOLIDATION_EFFACES")
 require(d.get("schema_version")=="P53D-1" and
         d.get("bilan",{}).get("decision")==NO_GO and
         d.get("sources",{}).get("mamH",{}).get("dictionnaire_38_champs_valide") is False and
         d["bilan"].get("montants_municipaux_foncier_reels_certifies")==0,
         "P53D_PROFIL_TROMPEUR")
 require(c.get("schema_version")=="P53C-1" and
         c.get("donnees_quebec_2024",{}).get("total_historique_millions_cad")=="43549.895" and
         c.get("bilan",{}).get("decision")==NO_GO,
         "P53C_ARC_NON_COMPARABLE")
 require(g.get("schema_version")=="P53A-LACUNES-1" and
         len(g.get("dossiers",[]))==9 and
         all(v.get("montant_mcad") is None and v.get("recette_nova_mcad") is None
             for v in g["dossiers"]) and
         g.get("bilan",{}).get("decision")==NO_GO,"FAUSSE_RECETTE_2026_2027")
 require(a.get("schema_version")=="P53A-1" and
         a.get("compartiments_non_additionner_aux_lignes",{}).get("total_budget_quebec_mcad")=="166492" and
         a.get("bilan",{}).get("decision")==NO_GO,"BUDGET_PROVINCIAL_INCOMPATIBLE")
 require(p.get("status")=="PROPOSITION_NON_ADOPTEE" and
         p.get("automatic_go") is False and
         p.get("human_reviews_received") is False and
         p.get("financial_model_certified") is False and
         len(p.get("required_evidence",[]))==20 and
         all(e.get("statut")=="NON_VALIDE" and
             e.get("preuve_independante_obtenue") is False for e in p["required_evidence"]),
         "P52A_PREUVES_INVENTEES")
 bill=m.get("bilan",{})
 require(bill=={
   "originaux_sources_telecharges_sha256_observes":2,
   "originaux_complets_dans_git":0,
   "snapshots_derives_verifiables_dans_git":2,
   "municipalites_locales_retenues":1094,
   "champs_numeriques_reconcilies":15,
   "categories_historique_E04_E05_documentees":2,
   "reconcilations_individuelles_sans_ecart":1094,
   "budget_2026_2027_municipal_certifie":0,
   "consolidation_tous_gouvernements_certifiee":False,
   "preuves_F01_F20_validees":0,
   "valeurs_nova_inconnues":1320,
   "publication_autorisee":False,"fusion_autorisee":False,
   "adoption_autorisee":False,"decision":NO_GO
 }, "FAUSSE_CERTIFICATION_FINANCIERE")
 return {
   "jalon":"P53E","schema_version":"P53E-1",
   "annee_comptable":2024,
   "municipalites_locales_analysees":1094,
   "municipalites_avec_taxe_fonciere_renseignee":1093,
   "ecarts_rapprochements":results["ecarts_de_rapprochement"],
   "taxes_foncieres_2024_observees_cad":results["foncier_cad"],
   "taxes_municipales_totales_2024_cad":results["taxes_cad"],
   "revenus_municipaux_locaux_totaux_2024_cad":results["revenus_cad"],
   "transferts_municipaux_2024_cad":results["transferts_cad"],
   "revenus_hors_taxes_et_transferts_2024_cad":results["hors_taxes_hors_transferts_cad"],
   "sha256_deux_extractions_git_verifies":True,
   "sha256_originaux_observes_hors_git":True,
   "montants_municipaux_2026_2027_certifies":False,
   "consolidation_interadministrations_certifiee":False,
   "preuves_F01_F20_non_validees":20,
   "valeurs_nova_inconnues":1320,
   "publication_autorisee":False,"fusion_autorisee":False,
   "adoption_autorisee":False,"decision":NO_GO
 }

def save_new(path,content):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as f:f.write(content)

def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__)
 for name,path in FILES.items():ap.add_argument("--"+name,type=Path,default=path)
 ap.add_argument("--csv-selection",type=Path,default=CSV_SOURCE)
 ap.add_argument("--dictionnaire",type=Path,default=DESC_SOURCE)
 ap.add_argument("--rapport",type=Path)
 ap.add_argument("--exiger-consolidation",action="store_true")
 args=ap.parse_args(argv)
 try:
  docs={name:read(getattr(args,name)) for name in FILES}
  rows,dic=load_snapshots(args.csv_selection,args.dictionnaire)
  report=audit(docs,rows,dic)
  if args.rapport:save_new(args.rapport,json.dumps(report,ensure_ascii=False,indent=2)+"\n")
  else:print(json.dumps(report,ensure_ascii=False,indent=2))
  return 3 if args.exiger_consolidation else 0
 except (OSError,ValueError,UnicodeError,TypeError,KeyError,InvalidOperation) as err:
  print(json.dumps({"jalon":"P53E","statut":"SOURCE_OU_CALCUL_REJETE",
    "classe_erreur":type(err).__name__,
    "publication_autorisee":False,"fusion_autorisee":False,
    "adoption_autorisee":False,"decision":NO_GO},ensure_ascii=False))
  return 2
if __name__=="__main__":
 sys.exit(main())
