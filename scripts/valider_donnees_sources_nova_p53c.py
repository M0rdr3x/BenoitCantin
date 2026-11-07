#!/usr/bin/env python3
"""P53C: verify CRA's original 2024 tax CSV bytes, reconciliations and scope limits."""
import argparse
import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "registre":D/"P53C_SOURCE_PRIMAIRE_ARC_ET_LACUNES_MUNICIPALES.json",
 "p53a":D/"P53A_REGISTRE_RECETTES_ET_COMPETENCES.json",
 "lacunes":D/"P53A_LACUNES_HORS_PERIMETRE.json",
 "p53b":D/"P53B_SOURCES_ET_COTISATIONS_2026.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
SOURCE=D/"sources"/"P53C_ARC_TBL03_2024_FR_ORIGINAL.csv"
EXPECTED_SHA="a1df2cf1600809f3e2274ad8f6348263080437cfaeb5ed7e86efb24d628cacf1"
BLOB_SHA="b733fe50cff367d08462fde36312207d7ff2e295"
SOURCE_URL="https://www.canada.ca/content/dam/cra-arc/prog-policy/stats/itstb-sipti/2024/tbl03_fr.csv"
PDF_URL="https://www.canada.ca/content/dam/cra-arc/prog-policy/stats/itstb-sipti/2024/tbl03_fr.pdf"
STATCAN_URL="https://www150.statcan.gc.ca/n1/tbl/csv/10100020-fra.zip"
BRACKETS=(
 ("tranche_55867_ou_moins_milliers_cad","5564856"),
 ("tranche_55867_111733_milliers_cad","16863643"),
 ("tranche_111733_173205_milliers_cad","7303699"),
 ("tranche_173205_246752_milliers_cad","3310900"),
 ("tranche_246752_et_plus_milliers_cad","10506796"),
)
INT=re.compile(r"^\d+$")
RULES=(
 "annee_imposition_2024_nequivaut_pas_budget_2026_2027",
 "impots_federaux_particuliers_non_equivalents_recettes_federales_toutes_sources",
 "recettes_M_2026_2027_du_Quebec_non_additives_directement_aux_impots_2024",
 "somme_de_tranches_permet_ecart_arrondi_1_millier",
 "transferts_intergouvernementaux_a_ne_pas_doubler",
 "taxes_municipales_non_confondre_impot_scolaire_budget_Quebec",
 "statut_F02_toujours_NON_VALIDE",
 "aucune_validation_independante_inventee"
)

def must(condition,message):
 if not condition:raise ValueError(message)

def read(path):
 p=Path(path)
 must(p.is_file() and not p.is_symlink() and
      0<p.stat().st_size<=650000,"REGISTRE_ABSENT_OU_TROP_GRAND")
 obj=json.loads(p.read_text(encoding="utf-8"))
 must(type(obj) is dict,"JSON_OBJET_REQUIS")
 return obj

def read_original(path):
 p=Path(path)
 must(p.is_file() and not p.is_symlink() and
      p.stat().st_size==1059,"CSV_ORIGINAL_ABSENT_OU_TAILLE_INCORRECTE")
 raw=p.read_bytes()
 must(hashlib.sha256(raw).hexdigest()==EXPECTED_SHA,
      "CSV_ORIGINAL_SHA256_DIFFERENT")
 try:text=raw.decode("cp1252")
 except UnicodeDecodeError as exc:raise ValueError("ENCODAGE_SOURCE_INCORRECT") from exc
 rows=list(csv.reader(io.StringIO(text)))
 must(len(rows)==16 and len(rows[0])==7 and
      rows[0][0]=="Province ou territoire",
      "CSV_ENTETE_OU_NOMBRE_LIGNES_INCORRECT")
 must(all(len(r)==7 for r in rows),"STRUCTURE_COLONNES_INVALIDE")
 match=[r for r in rows[1:] if r[0].strip()=="Québec"]
 must(len(match)==1,"QUEBEC_ABSENT_OU_DUPLIQUE")
 q=match[0]
 expected=[val for _,val in BRACKETS]+["43549895"]
 must([v.strip() for v in q[1:]]==expected,
      "IMPOT_FEDERAL_NET_QUEBEC_CHANGE")
 canada=[r for r in rows[1:] if r[0].strip()=="Tout le Canada"]
 must(len(canada)==1 and canada[0][-1].strip()=="222652101",
      "TOTAL_CANADA_REFERENCE_INATTENDU")
 must(all(INT.fullmatch(v) for v in expected),"MONTANT_SOURCE_NON_NUMERIQUE")
 return {"lignes_csv_incluant_entete":len(rows),
         "montants_quebec_milliers_cad":expected,
         "montant_canada_milliers_cad":"222652101",
         "source_sha256":hashlib.sha256(raw).hexdigest()}

def verify(d,original):
 must(type(d) is dict and set(d)==set(FILES),"CINQ_REGISTRES_ATTENDUS")
 m,a,g,b,p=(d[k] for k in FILES)
 must(m.get("schema_version")=="P53C-1" and m.get("jalon")=="P53C" and
      m.get("date_reference")=="2026-10-21" and
      m.get("annee_impot_observee")==2024 and
      m.get("reference_exercice_budget_quebec")=="2026-2027" and
      m.get("statut")=="CSV_ORIGINAL_ARC_2024_VERIFIE_MUNICIPALITES_EN_ATTENTE" and
      m.get("dossier_F01_F20_certifie") is False,
      "SOURCE_HISTORIQUE_PRESENTEE_COMME_REFORME")
 must(m.get("chainage_documents")=={
   "p53a":str(FILES["p53a"].relative_to(ROOT)),
   "lacunes":str(FILES["lacunes"].relative_to(ROOT)),
   "p53b":str(FILES["p53b"].relative_to(ROOT)),
   "p52a":str(FILES["p52a"].relative_to(ROOT)),
   "document_original_archetype":str(SOURCE.relative_to(ROOT))},
      "CHAINAGE_SOURCES_BRISÉ")
 must(a.get("schema_version")=="P53A-1" and
      a.get("bilan",{}).get("lignes_recettes")==21 and
      a["bilan"].get("montants_nova_inconnus")==1320 and
      a["bilan"].get("decision")=="NO_GO_AUTOMATIQUE" and
      a.get("compartiments_non_additionner_aux_lignes",{}).get(
        "total_budget_quebec_mcad")=="166492",
      "BUDGET_PROVINCIAL_FAUSSEMENT_CHANGE")
 must(g.get("schema_version")=="P53A-LACUNES-1" and
      g.get("bilan",{}).get("postes_chiffres")==0 and
      len(g.get("dossiers",[]))==9 and
      all(x.get("montant_mcad") is None and
          x.get("recette_nova_mcad") is None
          for x in g["dossiers"]),
      "P53A_LACUNES_TRANSFORMEES_EN_RECETTES")
 must(b.get("schema_version")=="P53B-1" and
      b.get("bilan",{}).get("montants_hors_budget_certifiés")==0 and
      b["bilan"].get("montants_financiers_nova_inconnus")==1320 and
      b["bilan"].get("decision")=="NO_GO_AUTOMATIQUE" and
      [x.get("id") for x in b.get("dossiers",[])]==[
        "E%02d"%i for i in range(1,10)] and
      all(x.get("montant_annuel_reel_quebec_mcad") is None and
          x.get("utilisable_pour_modele_nova") is False
          for x in b["dossiers"]),
      "BAREMES_FICTIVEMENT_CONVERTIS_EN_MONTANTS")
 must(p.get("status")=="PROPOSITION_NON_ADOPTEE" and
      p.get("automatic_go") is False and
      p.get("human_reviews_received") is False and
      p.get("financial_model_certified") is False and
      len(p.get("required_evidence",[]))==20 and
      all(x.get("statut")=="NON_VALIDE" and
          x.get("preuve_independante_obtenue") is False
          for x in p["required_evidence"]),
      "PREUVES_FISCALES_FICTIVES")
 s=m.get("source_fiscale_ARC",{})
 must(s.get("organisme")=="Agence du revenu du Canada" and
      s.get("catalogue")==
        "https://open.canada.ca/data/fr/dataset/66e95b48-3ac3-414f-ae54-2c4e21105dda" and
      s.get("url_csv_original")==SOURCE_URL and
      s.get("url_pdf_contrelecture")==PDF_URL and
      s.get("annee_imposition")==2024 and
      s.get("date_donnees_arrete")=="2025-11-30" and
      s.get("date_publication_catalogue")=="2026-02-25" and
      s.get("licence_declaree_catalogue")=="Licence du gouvernement ouvert - Canada" and
      s.get("ligne_geographique")=="Québec" and
      s.get("unite_originale")=="MILLIERS_DE_DOLLARS_CAD" and
      s.get("encodage_original")=="windows-1252" and
      s.get("taille_octets")==1059 and
      s.get("sha256_octets_originaux")==EXPECTED_SHA and
      s.get("git_blob_sha")==BLOB_SHA and
      s.get("archivage_octets_originaux_dans_PR") is True and
      s.get("recoupement_du_total_et_cinq_tranches_avec_pdf_officiel") is True and
      s.get("octets_pdf_originaux_archives_et_hashes") is False and
      s.get("avis_expert_comptable_independant_signe") is False and
      s.get("province_de_imposition_pas_proxy_exhaustif_tresorerie") is True and
      s.get("caveat_arrondis_millier") is True,
      "PROVENANCE_ARC_NON_REPRODUCTIBLE")
 must(original["source_sha256"]==s["sha256_octets_originaux"],
      "OCTETS_ORIGINAUX_NON_IDENTIQUES")
 obs=m.get("donnees_quebec_2024",{})
 must(all(obs.get(key)==val for key,val in BRACKETS),
      "DECLARATION_DES_TRANCHES_INCOMPLETE")
 val=[int(x) for x in original["montants_quebec_milliers_cad"]]
 must(val[:5]==[int(x[1]) for x in BRACKETS] and
      sum(val[:5])==43549894 and val[5]==43549895 and
      val[5]-sum(val[:5])==1,
      "ARRONDI_ARC_NON_VERIFIE")
 must(obs.get("somme_cinq_tranches_milliers_cad")=="43549894" and
      obs.get("total_quebec_officiel_milliers_cad")=="43549895" and
      obs.get("ecart_arrondis_total_moins_somme_milliers_cad")=="1" and
      obs.get("total_historique_millions_cad")=="43549.895" and
      obs.get("total_historique_milliards_cad")=="43.549895" and
      (Decimal(obs["total_quebec_officiel_milliers_cad"])/1000)==
        Decimal(obs["total_historique_millions_cad"]) and
      (Decimal(obs["total_quebec_officiel_milliers_cad"])/1000000)==
        Decimal(obs["total_historique_milliards_cad"]) and
      all(obs.get(k) is None for k in (
        "montant_pour_exercice_2026_2027_mcad",
        "montant_federal_toutes_taxes_2026_2027_mcad",
        "rendement_impot_nova_mcad")),
      "MONTANT_ANNUEL_NON_COMPARABLE")
 local=m.get("municipal",{})
 must(local.get("source")==STATCAN_URL and
      local.get("identifiant_tableau")=="10-10-0020-01" and
      local.get("catalogue")==
         "https://open.canada.ca/data/en/dataset/b28ce95f-a075-4ea9-89b9-ca955f94689d" and
      local.get("annee_a_extraire")==2024 and
      local.get("unite_tableau")=="MILLIONS_DE_DOLLARS_CAD" and
      local.get("source_zip_original_recue") is False and
      local.get("source_zip_SHA256") is None and
      local.get("incident_acquisition")=="REPONSE_HTML_INDISPONIBILITE_SITE_AU_LIEU_DE_ZIP" and
      local.get("derniere_diffusion_page_constatee")=="2025-11-21" and
      local.get("geographie_quebec_et_finances_classifiees_verifiees") is False and
      local.get("postes_p53a_en_attente")==["E04","E05"] and
      local.get("montant_taxes_foncieres_mcad") is None and
      local.get("montant_autres_recettes_mcad") is None and
      local.get("preuve_externe_attestee") is False,
      "STATCAN_ZIP_NON_VERIFIE")
 c=m.get("comparabilite")
 must(type(c) is dict and set(c)==set(RULES) and
      all(c[k] is True for k in RULES),
      "ANNEES_ET_PERIMETRES_TROMPEURS")
 stats=m.get("bilan",{})
 must(stats=={
    "csv_officiel_brut_recupere":1,
    "source_originale_archivee_et_sha256_reproductible":1,
    "montants_historique_impot_federal_quebec_observes":1,
    "categories_municipales_documentees_sans_zip":2,
    "recettes_municipales_verifiees_et_chiffrees":0,
    "recettes_2026_2027_federales_certifiees":0,
    "preuves_F01_F20_validees":0,
    "valeurs_nova_inconnues":1320,
    "taux_nova_adoptes":0,
    "publication_autorisee":False,
    "fusion_autorisee":False,
    "adoption_autorisee":False,
    "decision":"NO_GO_AUTOMATIQUE"},
    "BILAN_FAUSSEMENT_CERTIFIE")
 return {
  "jalon":"P53C","schema_version":"P53C-1",
  "annee_impot_ARC":2024,
  "source_csv_octets_verifies":1059,
  "csv_original_sha256_verifie":True,
  "impot_federal_net_particuliers_quebec_2024_milliers_cad":43549895,
  "impot_federal_net_particuliers_quebec_2024_millions_cad":"43549.895",
  "difference_arrondis_5_tranches_milliers_cad":1,
  "recettes_federales_quebec_2026_2027_certifiees":False,
  "source_zip_municipale_acquise":False,
  "recettes_municipales_2024_et_2026_2027_chiffrees":0,
  "preuves_F01_F20_non_validees":20,
  "valeurs_nova_inconnues":1320,
  "fusion_autorisee":False,
  "publication_autorisee":False,
  "adoption_autorisee":False,
  "decision":"NO_GO_AUTOMATIQUE"
 }

def export_csv(d):
 obs=d["registre"]["donnees_quebec_2024"]
 buffer=io.StringIO(newline="")
 writer=csv.writer(buffer,lineterminator="\n")
 writer.writerow(["annee_imposition","territoire","type","tranche_declaration",
                  "impot_federal_net_milliers_cad","annee_budget_quebec_differente",
                  "certification_externe"])
 for key,val in BRACKETS:
  writer.writerow(["2024","Québec","TRANCHE",key,obs[key],"2026-2027","NON"])
 writer.writerow(["2024","Québec","TOTAL_PUBLIE","Toutes les tranches",
                  obs["total_quebec_officiel_milliers_cad"],"2026-2027","NON"])
 return buffer.getvalue()

def write_new(path,content):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as f:f.write(content)

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 for key,path in FILES.items():parser.add_argument("--"+key,type=Path,default=path)
 parser.add_argument("--csv-original",type=Path,default=SOURCE)
 parser.add_argument("--rapport",type=Path)
 parser.add_argument("--export-csv",type=Path)
 parser.add_argument("--exiger-consolidation",action="store_true")
 args=parser.parse_args(argv)
 try:
  docs={k:read(getattr(args,k)) for k in FILES}
  original=read_original(args.csv_original)
  result=verify(docs,original)
  if args.rapport and args.export_csv:
   must(args.rapport.resolve()!=args.export_csv.resolve(),
        "FICHIERS_SORTIE_IDENTIQUES")
  if args.rapport:write_new(args.rapport,json.dumps(result,ensure_ascii=False,indent=2)+"\n")
  if args.export_csv:write_new(args.export_csv,export_csv(docs))
  if not args.rapport and not args.export_csv:
   print(json.dumps(result,ensure_ascii=False,indent=2))
  return 3 if args.exiger_consolidation else 0
 except (OSError,ValueError,UnicodeError,KeyError,TypeError) as ex:
  print(json.dumps({"jalon":"P53C","etat":"REJET_PREUVE",
        "categorie_erreur":type(ex).__name__,
        "fusion_autorisee":False,"publication_autorisee":False,
        "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"},
        ensure_ascii=False))
  return 2

if __name__=="__main__":
 sys.exit(main())
