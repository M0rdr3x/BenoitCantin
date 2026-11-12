#!/usr/bin/env python3
"""P53D: verify a captured MAMH 2024 row without inventing municipal revenues."""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "manifest":D/"P53D_ACQUISITION_MUNICIPALE_2024.json",
 "p53c":D/"P53C_SOURCE_PRIMAIRE_ARC_ET_LACUNES_MUNICIPALES.json",
 "p53b":D/"P53B_SOURCES_ET_COTISATIONS_2026.json",
 "lacunes":D/"P53A_LACUNES_HORS_PERIMETRE.json",
 "p53a":D/"P53A_REGISTRE_RECETTES_ET_COMPETENCES.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
SOURCE=D/"sources"/"P53D_MAMH_PROFIL_2024_AGREGAT_QUEBEC_CAPTURE.csv"
SHA="6acff78c6fd6122d6630f0a8f8eea7e59e265946"
CODE=re.compile(r"(?:CIALC|CIAIC|CIIIC)\d{5}")
FLAGS=[
 "code_PROV_ne_demontre_pas_recettes_consolidees",
 "champs_CIALC_CIAIC_CIIIC_sans_dictionnaire_pas_taxes",
 "fichier_mamh_2024_pas_memes_definitions_que_statcan",
 "source_capture_non_equivalente_a_archive_octets_originaux",
 "absence_SHA256_original_doit_rester_visible",
 "annee_municipale_2024_distincte_budget_quebec_2026_2027",
 "transferts_entre_paliers_a_exclure_du_cumul",
 "taxe_scolaire_budget_Quebec_pas_taxe_municipale",
 "impot_federal_net_2024_pas_taxe_municipale",
 "pas_d_imputation_depuis_taux_ou_ratios",
 "donnees_provisoires_pas_certification_independante",
]

def need(ok,msg):
 if not ok:raise ValueError(msg)

def read(p):
 p=Path(p)
 need(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<750000,"ABSENT_OR_UNSAFE_JSON")
 d=json.loads(p.read_text(encoding="utf-8"))
 need(type(d) is dict,"INVALID_JSON_OBJECT")
 return d

def capture(path=SOURCE):
 p=Path(path)
 need(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<50000,"CAPTURE_ABSENT")
 raw=p.read_bytes()
 blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
 need(blob==SHA,"CAPTURE_GIT_BLOB_MISMATCH")
 rows=list(csv.reader(io.StringIO(raw.decode("utf-8"))))
 need(len(rows)==2 and all(len(r)==41 for r in rows),"CAPTURE_MALFORMED")
 h,v=rows
 need(h[:3]==["an_edition","an_donnee","cod_prov"] and
      v[:3]==["2024","2024","PROV"],"CAPTURE_BAD_YEAR_OR_GEO")
 need(len(set(h))==41 and
      all(re.fullmatch(r"(?:CIALC|CIAIC|CIIIC)\d{5}",x) for x in h[3:]) and
      all(re.fullmatch(r"-?\d+(?:\.\d+)?",x) for x in v[3:]),
      "CAPTURE_UNINTERPRETABLE_CODES")
 return {"header":h,"values":v,"git_blob":blob}

def verify(d,raw):
 need(set(d)==set(FILES),"SIX_REGISTERS_REQUIRED")
 m,c,b,g,a,p=(d[k] for k in FILES)
 need(m.get("schema_version")=="P53D-1" and m.get("jalon")=="P53D" and
      m.get("date_reference")=="2026-10-21" and
      m.get("statut")=="CAPTURE_CSV_MAMH_2024_AGREGE_CODAGE_A_DECODER",
      "P53D_STATE_INVALID")
 need(m.get("references")=={
   k:str(FILES[k].relative_to(ROOT)) for k in FILES if k!="manifest"
 },"REFERENCES_INVALID")
 source=m.get("sources",{}).get("mamH",{})
 need(source.get("url_csv")==
      "https://mamh.gouv.qc.ca/fichiersdonneesouvertes/PF-2024-2024-Prov.csv" and
      source.get("fiche")==
      "https://www.donneesquebec.ca/recherche/dataset/profil-financier-des-municipalites-locales/resource/5dec077d-4ef9-4e22-99e9-0c4f3a6dd52d" and
      source.get("licence_fiche")=="CC-BY 4.0" and
      source.get("edition")==source.get("annee_donnee")==2024 and
      source.get("geographie_code")=="PROV" and
      source.get("chemin_extrait_captured")==str(SOURCE.relative_to(ROOT)) and
      source.get("sha_git_du_texte_capture")==raw["git_blob"]==SHA and
      source.get("nature_capture")=="TRANSCRIPTION_TEXTE_CSV_PAR_EXTRACTION_TIERCE_NON_HACHAGE_DU_FICHIER_ORIGINAL" and
      source.get("octets_source_origine_authentifies") is False and
      source.get("sha256_fichier_original") is None and
      source.get("nombre_lignes_donnees")==1 and
      source.get("nombre_colonnes")==41 and
      source.get("nombre_identifiants")==3 and
      source.get("nombre_champs_numeriques_codes")==38 and
      source.get("valeurs_de_revenu_municipal_reconciliees")==0 and
      source.get("dictionnaire_38_champs_valide") is False,
      "MAMH_FALSIFIED_OR_INTERPRETED")
 st=m.get("sources",{}).get("statcan",{})
 need(st.get("tableau")=="10-10-0020-01" and
      st.get("url_zip")=="https://www150.statcan.gc.ca/n1/tbl/csv/10100020-fra.zip" and
      st.get("octets_zip_authentifies") is False and
      st.get("sha256_zip_original") is None and
      st.get("toutes_variables_geo_2024_extraites") is False and
      st.get("remplacement_automatique_par_donnees_mamh_interdit") is True,
      "STATCAN_FALSELY_IMPORTED")
 items=m.get("lignes_ciblees")
 need(type(items) is list and [x.get("id") for x in items]==["E04","E05"] and
      all(x.get("montant_mcad") is None and
          x.get("source_agregat_statcan_certifiee") is False and
          x.get("donnee_mamh_convertible_en_montant_fiscal") is False
          for x in items),"FICTITIOUS_MUNICIPAL_REVENUE")
 flags=m.get("garde_fous",{})
 need(type(flags) is dict and set(flags)==set(FLAGS) and
      all(flags[k] is True for k in FLAGS),"MISSING_NO_DOUBLE_COUNT_GUARDS")
 need(c.get("schema_version")=="P53C-1" and
      c.get("municipal",{}).get("source_zip_original_recue") is False and
      c["municipal"].get("montant_taxes_foncieres_mcad") is None and
      c["municipal"].get("montant_autres_recettes_mcad") is None and
      c.get("bilan",{}).get("decision")=="NO_GO_AUTOMATIQUE",
      "P53C_FALSELY_COMPLETE")
 need(b.get("schema_version")=="P53B-1" and
      b.get("bilan",{}).get("montants_hors_budget_certifiés")==0 and
      b["bilan"].get("decision")=="NO_GO_AUTOMATIQUE",
      "P53B_FALSELY_COMPLETE")
 need(g.get("schema_version")=="P53A-LACUNES-1" and
      len(g.get("dossiers",[]))==9 and
      [x.get("id") for x in g["dossiers"][3:5]]==["E04","E05"] and
      all(x.get("montant_mcad") is None for x in g["dossiers"]) and
      g.get("bilan",{}).get("decision")=="NO_GO_AUTOMATIQUE",
      "P53A_EXTERNAL_GAPS_FAKED")
 need(a.get("schema_version")=="P53A-1" and
      a.get("compartiments_non_additionner_aux_lignes",{}).get("total_budget_quebec_mcad")=="166492" and
      a.get("bilan",{}).get("decision")=="NO_GO_AUTOMATIQUE",
      "P53A_QUEBEC_BUDGET_CHANGED")
 need(p.get("status")=="PROPOSITION_NON_ADOPTEE" and
      p.get("automatic_go") is False and
      len(p.get("required_evidence",[]))==20 and
      all(x.get("statut")=="NON_VALIDE" and
          x.get("preuve_independante_obtenue") is False
          for x in p["required_evidence"]),
      "FALSE_PROOF_CERTIFICATION")
 bill=m.get("bilan",{})
 need(bill=={
  "sources_municipales_capturees_en_texte":1,
  "sources_originales_zip_statcan_recues":0,
  "champs_numeriques_codes_a_qualifier":38,
  "lignes_provinciales_mamh_2024":1,
  "montants_municipaux_foncier_reels_certifies":0,
  "montants_municipaux_autres_revenus_certifies":0,
  "preuves_F01_F20_validees":0,
  "valeurs_nova_inconnues":1320,
  "publication_autorisee":False,"fusion_autorisee":False,
  "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"
 },"FALSE_MUNICIPAL_COMPLETENESS")
 return {
 "jalon":"P53D","champs_codes_non_qualifies":38,
 "source_mamh_2024_capturee_et_integrite_git_ok":True,
 "octets_originaux_mamh_sha256_verifies":False,
 "statcan_zip_acquis":False,
 "montants_municipaux_certifies":0,
 "preuves_F01_F20_non_validees":20,
 "valeurs_nova_inconnues":1320,
 "fusion_autorisee":False,"publication_autorisee":False,
 "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"
 }

def export_csv(raw):
 f=io.StringIO(newline="")
 w=csv.writer(f,lineterminator="\n")
 w.writerow(["annee","code_province","indicateur_code","valeur_brute_non_qualifiee","montant_fiscal_mcad"])
 for key,value in zip(raw["header"][3:],raw["values"][3:]):
  w.writerow(["2024","PROV",key,value,""])
 return f.getvalue()

def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__)
 for k,path in FILES.items():ap.add_argument("--"+k,type=Path,default=path)
 ap.add_argument("--capture-csv",type=Path,default=SOURCE)
 ap.add_argument("--rapport",type=Path)
 ap.add_argument("--export-csv",type=Path)
 ap.add_argument("--exiger-recettes-municipales",action="store_true")
 args=ap.parse_args(argv)
 try:
  docs={k:read(getattr(args,k)) for k in FILES}
  extracted=capture(args.capture_csv)
  summary=verify(docs,extracted)
  if args.rapport and args.export_csv:
   need(args.rapport.resolve()!=args.export_csv.resolve(),"SAME_OUTPUT_PATH")
  for path,body in (
    (args.rapport,json.dumps(summary,ensure_ascii=False,indent=2)+"\n"),
    (args.export_csv,export_csv(extracted))):
   if path:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8",newline="") as f:f.write(body)
  if not args.rapport and not args.export_csv:
   print(json.dumps(summary,ensure_ascii=False,indent=2))
  return 3 if args.exiger_recettes_municipales else 0
 except (OSError,ValueError,KeyError,UnicodeError,TypeError) as exc:
  print(json.dumps({"jalon":"P53D","etat":"REJET",
    "erreur":type(exc).__name__,"decision":"NO_GO_AUTOMATIQUE"}))
  return 2
if __name__=="__main__":
 sys.exit(main())
