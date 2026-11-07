#!/usr/bin/env python3
"""P53F: reconcile 2024 local municipal revenues; never auto-eliminate intergovernmental flows."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "manifest":D/"P53F_FLUX_INTERADMIN_2024.json",
 "p53e":D/"P53E_PREUVES_HISTORIQUES_MUNICIPALES.json",
 "p53d":D/"P53D_ACQUISITION_MUNICIPALE_2024.json",
 "p53a":D/"P53A_REGISTRE_RECETTES_ET_COMPETENCES.json",
 "lacunes":D/"P53A_LACUNES_HORS_PERIMETRE.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
SOURCE=D/"sources"/"P53E_MAMH_2024_MUNICIPALITES_LOCALES_SELECTION.csv"
SOURCE_SHA="11f940092a6a7eb54bf7dc39c6e5b4b44e73c82e9bb34ce7aae2e7278269aa5e"
EXPECTED={
 "CRIIX00406":("taxes",17337284213,1093,1,0,0,1093),
 "CRIIX00408":("quotes_parts",846987123,467,627,39,298,130),
 "CRIIX00409":("transferts",5376508934,1085,9,1,0,1084),
 "CRIIX00407":("compensations",1001301216,1011,83,0,0,1011),
 "CRIIX00410":("services",4241481713,1073,21,0,0,1073),
}
ALL_CATEGORIES=[f"CRIIX{x:05d}" for x in range(406,418)]
CODE=re.compile(r"-?\d+\Z")
NO_GO="NO_GO_AUTOMATIQUE"
GUARDS={
 "pas_eliminer_candidats_sans_appariement",
 "preserver_negatifs_et_blancs",
 "taxes_foncieres_incluses_dans_taxes",
 "revenus_incluent_transferts_et_quotes_parts",
 "services_compensations_a_verifier",
 "exclure_mrc_regies_transports",
 "2024_non_assimilable_budget_2026_2027",
 "pas_de_taux_nova_derive"
}
CRITERIA=[
 "payeur","beneficiaire","periode","ecriture_reciproque",
 "montant_et_signe","perimetre","preuve_originale","audit_independant"
]

def ensure(ok,reason):
 if not ok:raise ValueError(reason)

def load(path):
 p=Path(path)
 ensure(p.is_file() and not p.is_symlink() and
        0<p.stat().st_size<=800000,"FICHIER_JSON_INVALIDE")
 obj=json.loads(p.read_text(encoding="utf-8"))
 ensure(type(obj) is dict,"JSON_OBJECT_REQUIS")
 return obj

def parse_source(path=SOURCE):
 p=Path(path)
 ensure(p.is_file() and not p.is_symlink() and
        p.stat().st_size==136871,"EXTRAIT_CSV_TAILLE_SOURCE_INVALIDE")
 raw=p.read_bytes()
 ensure(hashlib.sha256(raw).hexdigest()==SOURCE_SHA,
        "EXTRAIT_CSV_SHA256_INCORRECT")
 rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
 ensure(len(rows)==1094,"NOMBRE_ORGANISMES_INCORRECT")
 keys=["cod_geo","nom_organisme","type_org","CRIIX00016","CRIIX00018",
       "CRIIX00405"]+ALL_CATEGORIES
 ensure(list(rows[0])==keys,"CHAMPS_ATTENDUS_INCORRECTS")
 ensure(all(list(r)==keys and r.get(None) is None and
            r["type_org"]=="Municipalité locale" and
            bool(r["cod_geo"]) and bool(r["nom_organisme"])
            for r in rows),"MUNICIPALITES_HORS_CHAMP_OU_CSV_INVALIDE")
 ensure(len({r["cod_geo"] for r in rows})==1094,"CODE_GEO_DUPLIQUE")
 return rows

def signed(raw):
 if raw=="":return None
 ensure(type(raw) is str and CODE.fullmatch(raw),
        "NOMBRE_NON_ENTIER_OU_NON_SIGNE")
 return int(raw)

def aggregate(rows):
 ensure(type(rows) is list and len(rows)==1094,
        "NOMBRE_ORGANISMES_INATTENDU")
 result={}
 for k,(role,expected,n,blanks,neg,zeros,pos) in EXPECTED.items():
  values=[signed(r[k]) for r in rows]
  present=[v for v in values if v is not None]
  result[k]={
   "code":k,"classe":role,"montant_cad":str(sum(present)),
   "observations":len(present),"blancs":1094-len(present),
   "negatifs":sum(1 for x in present if x<0),
   "zeros":sum(1 for x in present if x==0),
   "positifs":sum(1 for x in present if x>0),
   "contrepartie_certifiee":False,"montant_elimine_cad":None
  }
  ensure((sum(present),len(present),1094-len(present),
         result[k]["negatifs"],result[k]["zeros"],result[k]["positifs"])
         ==(expected,n,blanks,neg,zeros,pos),"SERIE_CATEGORIE_ALTEREE_"+k)
 reconciled=0
 for r in rows:
  parent=signed(r["CRIIX00405"])
  ensure(parent is not None,"TOTAL_REVENUS_MANQUANT")
  detail=sum(signed(r[c]) or 0 for c in ALL_CATEGORIES)
  ensure(parent==detail,"DOUZE_CATEGORIES_NON_RAPPROCHEES")
  reconciled+=1
 summary={
  "revenus":sum(signed(r["CRIIX00405"]) for r in rows),
  "taxes":int(result["CRIIX00406"]["montant_cad"]),
  "quotes_parts":int(result["CRIIX00408"]["montant_cad"]),
  "transferts":int(result["CRIIX00409"]["montant_cad"]),
  "compensations":int(result["CRIIX00407"]["montant_cad"]),
  "services":int(result["CRIIX00410"]["montant_cad"]),
  "foncier":sum(signed(r["CRIIX00016"]) or 0 for r in rows)
 }
 summary["autres"]=summary["revenus"]-summary["taxes"]-summary["quotes_parts"]-summary["transferts"]
 summary["candidats"]=summary["quotes_parts"]+summary["transferts"]
 ensure(summary=={
  "revenus":32367623561,"taxes":17337284213,
  "quotes_parts":846987123,"transferts":5376508934,
  "compensations":1001301216,"services":4241481713,
  "foncier":15085531572,"autres":8806843291,
  "candidats":6223496057},"PARTITIONS_HISTORIQUES_NON_VERIFIEES")
 return result,summary,reconciled

def validate(documents,rows):
 ensure(set(documents)==set(FILES),"REGISTRES_D_ENTREE_MANQUANTS")
 m,e,d,a,g,p=(documents[k] for k in FILES)
 ensure(m.get("schema")=="P53F-1" and m.get("date")=="2026-10-21" and
        m.get("annee")==2024 and
        m.get("statut")=="OBSERVATIONS_NON_CONSOLIDEES","P53F_SCHEMA_INVALIDE")
 expected_ref={k:str(FILES[k].relative_to(ROOT)) for k in FILES if k!="manifest"}
 expected_ref["csv"]=str(SOURCE.relative_to(ROOT))
 ensure(m.get("ref")==expected_ref,"REFERENCES_CROISEES_MODIFIEES")
 scope=m.get("périmètre",{})
 ensure(scope=={
  "organismes":"Municipalité locale","nombre":1094,
  "unite":"CAD","source_sha256":SOURCE_SHA},
  "ANNEE_OU_PERIMETRE_ERRONE")
 ensure(e.get("schema_version")=="P53E-1" and
        e.get("bilan",{}).get("municipalites_locales_retenues")==1094 and
        e.get("bilan",{}).get("decision")==NO_GO and
        e.get("sources",{}).get("donnees",{}).get("sha256_derive")==SOURCE_SHA and
        e.get("observations_de_reference",{}).get("revenus_totaux_municipalites_locales_2024_cad")=="32367623561" and
        e["observations_de_reference"].get("montant_net_sans_doublon_tous_paliers_2024_cad") is None,
        "P53E_REFERENCE_MODIFIEE")
 ensure(d.get("schema_version")=="P53D-1" and
        d.get("bilan",{}).get("decision")==NO_GO and
        d.get("sources",{}).get("statcan",{}).get("octets_zip_authentifies") is False,
        "P53D_PROVENANCE_ALTÉRÉE")
 ensure(a.get("schema_version")=="P53A-1" and
        a.get("compartiments_non_additionner_aux_lignes",{}).get("total_budget_quebec_mcad")=="166492" and
        a.get("bilan",{}).get("decision")==NO_GO,
        "P53A_AUTRE_EXERCICE_CONFONDU")
 ensure(g.get("schema_version")=="P53A-LACUNES-1" and
        len(g.get("dossiers",[]))==9 and
        all(x.get("montant_mcad") is None and
            x.get("recette_nova_mcad") is None for x in g["dossiers"]) and
        g.get("bilan",{}).get("decision")==NO_GO,
        "LACUNES_2026_CHIFFREES_SANS_PREUVE")
 ensure(p.get("status")=="PROPOSITION_NON_ADOPTEE" and
        p.get("automatic_go") is False and
        p.get("financial_model_certified") is False and
        p.get("human_reviews_received") is False and
        len(p.get("required_evidence",[]))==20 and
        all(x.get("statut")=="NON_VALIDE" and
            x.get("preuve_independante_obtenue") is False
            for x in p["required_evidence"]),
        "P52A_FAUSSE_APPROBATION")
 detail,summary,count=aggregate(rows)
 ensure(type(m.get("postes")) is list and
        m["postes"]==list(detail.values()),"DETAIL_STATISTIQUE_OU_SIGNATURE_FICTIVE")
 totals=m.get("totaux",{})
 ensure(totals=={
  "taxes":str(summary["taxes"]),
  "quotes_parts":str(summary["quotes_parts"]),
  "transferts":str(summary["transferts"]),
  "reste_non_taxes_ni_quotes_ni_transferts":str(summary["autres"]),
  "revenus":str(summary["revenus"]),
  "foncier_deja_dans_taxes":str(summary["foncier"]),
  "candidats_a_appariement_non_eliminables":str(summary["candidats"]),
  "compensations_dans_reste":str(summary["compensations"]),
  "services_dans_reste":str(summary["services"]),
  "montant_eliminations_certifiees":None,
  "revenus_consolides":None,
  "revenus_2026_2027":None,
 },"DONNEE_AGREGEE_FICTIVE_OU_DOUBLE_COMPTEE")
 ap=m.get("appariement",{})
 ensure(ap=={
  "pieces_a_obtenir":CRITERIA,
  "transactions_appariees":0,
  "montant_net_justifie":None,
  "publication_autorisee":False
 },"FAUSSES_CONTREPARTIES")
 ensure(type(m.get("regles")) is dict and
        set(m["regles"])==GUARDS and
        all(m["regles"][k] is True for k in GUARDS),
        "CONTRAINTES_CONSOLIDATION_SUPPRIMEES")
 ensure(m.get("bilan")=={
  "comptes":1094,"appariements_confirmes":0,
  "preuves_F01_F20":0,"inconnues_nova":1320,
  "publication_autorisee":False,"fusion_autorisee":False,
  "adoption_autorisee":False,"decision":NO_GO
 },"FAUSSE_VALIDATION_NO_GO")
 return {
  "jalon":"P53F","annee":2024,
  "municipalites_locales":count,
  "revenus_bruts_CAD":summary["revenus"],
  "taxes_CAD":summary["taxes"],
  "quotes_parts_CAD":summary["quotes_parts"],
  "transferts_CAD":summary["transferts"],
  "reste_hors_taxes_quotes_transferts_CAD":summary["autres"],
  "exposition_susceptible_appariement_CAD":summary["candidats"],
  "transactions_appariees":0,
  "eliminations_confirmees_CAD":None,
  "consolidation_interadministrations_certifiee":False,
  "montants_2026_2027_verifies":False,
  "preuves_F01_F20_non_validees":20,
  "parametres_Nova_inconnus":1320,
  "publication_autorisee":False,"fusion_autorisee":False,
  "adoption_autorisee":False,"decision":NO_GO
 }

def export(rows):
 stream=io.StringIO(newline="")
 w=csv.writer(stream,lineterminator="\n")
 w.writerow(["code_municipal","annee","quotes_parts_CAD","transferts_CAD",
             "compensations_CAD","services_rendus_CAD",
             "organisme_payeur","transaction_correspondante","appariement_confirme"])
 for r in rows:
  w.writerow([r["cod_geo"],2024,r["CRIIX00408"],r["CRIIX00409"],
              r["CRIIX00407"],r["CRIIX00410"],"","","NON"])
 return stream.getvalue()

def save(path,body):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as f:f.write(body)

def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__)
 for k,v in FILES.items():ap.add_argument("--"+k,type=Path,default=v)
 ap.add_argument("--source-csv",type=Path,default=SOURCE)
 ap.add_argument("--rapport",type=Path)
 ap.add_argument("--export-csv",type=Path)
 ap.add_argument("--exiger-appariements",action="store_true")
 args=ap.parse_args(argv)
 try:
  d={k:load(getattr(args,k)) for k in FILES}
  rows=parse_source(args.source_csv)
  r=validate(d,rows)
  if args.rapport and args.export_csv:
   ensure(args.rapport.resolve()!=args.export_csv.resolve(),
          "RAPPORT_ET_CSV_IDENTIQUES")
  if args.rapport:save(args.rapport,json.dumps(r,ensure_ascii=False,indent=2)+"\n")
  if args.export_csv:save(args.export_csv,export(rows))
  if not args.rapport and not args.export_csv:
   print(json.dumps(r,ensure_ascii=False,indent=2))
  return 3 if args.exiger_appariements else 0
 except (OSError,ValueError,UnicodeError,KeyError,TypeError) as ex:
  print(json.dumps({"jalon":"P53F","statut":"REJET",
        "classe_erreur":type(ex).__name__,
        "publication_autorisee":False,"fusion_autorisee":False,
        "adoption_autorisee":False,"decision":NO_GO},ensure_ascii=False))
  return 2
if __name__=="__main__":
 sys.exit(main())
