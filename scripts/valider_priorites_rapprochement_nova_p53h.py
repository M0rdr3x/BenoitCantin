#!/usr/bin/env python3
"""P53H : priorisation de 1343 organismes MAMH 2024 sans appariement présumé."""
import argparse
import csv
import importlib.util
import io
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "p53h":D/"P53H_PRIORITES_VERIFICATION_2024.json",
 "p53g":D/"P53G_COUVERTURE_1343_ORGANISMES_2024.json",
 "p53f":D/"P53F_FLUX_INTERADMIN_2024.json",
 "p53e":D/"P53E_PREUVES_HISTORIQUES_MUNICIPALES.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
LOCAL=D/"sources"/"P53E_MAMH_2024_MUNICIPALITES_LOCALES_SELECTION.csv"
OTHER=D/"sources"/"P53G_MAMH_2024_249_ORGANISMES_COMPLEMENTAIRES.csv"
P53G_SCRIPT=ROOT/"scripts"/"valider_couverture_organismes_nova_p53g.py"
GUARDS={
 "annee":2024,
 "unit":"CAD",
 "population_complete":1343,
 "types_distincts":5,
 "critere":"VALEUR_ABSOLUE_DE_SOMME_SIGNEE_QUOTES_PARTS_ET_TRANSFERTS_RECUS",
 "nombre_cibles_prioritaires":25,
 "tri_descendant_puis_code_org_ascendant":True,
 "blancs_sont_non_renseignes_pas_zero_constate":True,
 "montants_negatifs_conserves":True,
 "revenu_recipient_ne_prouve_pas_depense_du_payeur":True,
 "organismes_priorises_pas_coupables_d_erreur":True,
 "rang_ne_signifie_pas_montant_eliminable":True,
 "exercice_2024_pas_projection_2026_2027":True,
 "exclusion_du_budget_federal_et_quebec_incompatible":True,
}
ORDER=[
 "Municipalité locale","Municipalité régionale de comté",
 "Communauté métropolitaine","Régie intermunicipale",
 "Organisme public de transport"
]
REQUIREMENTS=[
 "IDENTIFIER_ORGANISME_PAYEUR_DISTINCT_ET_REGIME_COMPTABLE",
 "EXIGER_PIECE_DE_CHARGE_DU_PAYEUR_ET_PIECE_DE_RECETTE_DU_BENEFICIAIRE",
 "RECONCILIER_PERIODE_TITRE_NATURE_MONTANT_SIGNE_DEVISE_ET_STATUT",
 "ELIMINER_SEULEMENT_SI_LES_DEUX_CONTREPARTIES_APPARTIENNENT_AU_PERIMETRE",
 "RECONCILIER_SUBVENTIONS_FEDERALES_OU_PROVINCIALES_AVANT_AGREGATION",
 "SIGNER_AVIS_COMPTABLE_INDEPENDANT_ET_DATE_VERSION_DE_SOURCE"
]
NO_GO="NO_GO_AUTOMATIQUE"

def must(x,message):
 if not x:raise ValueError(message)

def read(path):
 p=Path(path)
 must(p.is_file() and not p.is_symlink() and
      0<p.stat().st_size<750000,"JSON_SOURCE_ABSENTE_OU_INVALIDE")
 o=json.loads(p.read_text(encoding="utf-8"))
 must(type(o) is dict,"OBJET_JSON_ATTENDU")
 return o

def upstream_module():
 spec=importlib.util.spec_from_file_location("nova_p53g_upstream",P53G_SCRIPT)
 must(spec is not None and spec.loader is not None,"P53G_SCRIPT_ABSENT")
 module=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(module)
 return module

def source_rows(g=None,local=LOCAL,other=OTHER):
 g=g or upstream_module()
 local_rows=g.csv_source(local,g.SHA_LOCAL,1094)
 other_rows=g.csv_source(other,g.SHA_OTHER,249)
 g.reconstruct(local_rows,other_rows)
 return local_rows,other_rows

def priorities(rows):
 must(type(rows) is list and len(rows)==1343,"TOTAL_MUNICIPAL_INCORRECT")
 summaries={key:{
  "type_org":key,"effectif":0,
  "quotes_parts_cad":"0","transferts_cad":"0","exposition_signee_cad":"0",
  "organismes_flux_positif":0,"organismes_flux_negatif":0,
  "organismes_flux_nul":0,"organismes_deux_champs_vides":0,
  "contreparties_documentees":0,"eliminations_certifiees_cad":None
 } for key in ORDER}
 all_items=[]
 for r in rows:
  kind=r["type_org"]
  must(kind in summaries,"TYPE_ORGANISME_INCONNU")
  q=None if r["CRIIX00408"]=="" else int(r["CRIIX00408"])
  t=None if r["CRIIX00409"]=="" else int(r["CRIIX00409"])
  amount=(q or 0)+(t or 0)
  a=summaries[kind]
  a["effectif"]+=1
  a["quotes_parts_cad"]=str(int(a["quotes_parts_cad"])+(q or 0))
  a["transferts_cad"]=str(int(a["transferts_cad"])+(t or 0))
  a["exposition_signee_cad"]=str(int(a["exposition_signee_cad"])+amount)
  if amount>0:a["organismes_flux_positif"]+=1
  elif amount<0:a["organismes_flux_negatif"]+=1
  else:a["organismes_flux_nul"]+=1
  if q is None and t is None:a["organismes_deux_champs_vides"]+=1
  all_items.append({
   "code_organisme":r["cod_geo"],
   "nom_organisme":r["nom_organisme"],
   "type_org":kind,
   "quotes_parts_cad":None if q is None else str(q),
   "transferts_cad":None if t is None else str(t),
   "flux_candidats_signes_cad":str(amount),
   "montant_absolu_cad":str(abs(amount)),
   "contrepartie_payeur_identifiee":False,
   "piece_originale_correspondante":None,
   "appariement_reciproque_confirme":False,
  })
 all_items.sort(key=lambda r:(-int(r["montant_absolu_cad"]),r["code_organisme"]))
 top=[{"rang":i+1,**r} for i,r in enumerate(all_items[:25])]
 groups=list(summaries.values())
 total=sum(int(g["exposition_signee_cad"]) for g in groups)
 chosen=sum(int(x["flux_candidats_signes_cad"]) for x in top)
 must(total==10864282201 and chosen==7069371200,"PRIORISATION_INCOHERENTE")
 must(sum(g["effectif"] for g in groups)==1343,"DECOMPTE_ANNUEL")
 must(sum(int(g["quotes_parts_cad"]) for g in groups)==3148209097,
      "QUOTES_PARTS_GROUPES_INEXACTES")
 must(sum(int(g["transferts_cad"]) for g in groups)==7716073104,
      "TRANSFERTS_GROUPES_INEXACTS")
 return groups,top,all_items

def validate(documents,local,other):
 must(type(documents) is dict and set(documents)==set(FILES),"CINQ_REFERENCES_REQUISES")
 m,g,f,e,a=(documents[k] for k in FILES)
 must(m.get("schema_version")=="P53H-1" and m.get("jalon")=="P53H" and
      m.get("date_reference")=="2026-10-21" and
      m.get("statut")=="PRIORISATION_RAPPROCHEMENT_SANS_PREUVE_DE_DOUBLE_COMPTE",
      "SCHEMA_NON_CERTIFIE_REQUIS")
 expected_refs={
  "p53g":str(FILES["p53g"].relative_to(ROOT)),
  "p53f":str(FILES["p53f"].relative_to(ROOT)),
  "p53e":str(FILES["p53e"].relative_to(ROOT)),
  "p52a":str(FILES["p52a"].relative_to(ROOT)),
  "csv_local":str(LOCAL.relative_to(ROOT)),
  "csv_complementaire":str(OTHER.relative_to(ROOT))}
 must(m.get("references")==expected_refs,"REFERENCES_CHANGEES")
 must(m.get("regles_priorisation")==GUARDS,"REGLES_DE_PRUDENCE_SUPPRIMEES")
 gmodule=upstream_module()
 upstream={
   "p53g":g,"p53e":e,"p53f":f,"p52a":a
 }
 upstream_report=gmodule.validate(upstream,local,other)
 must(upstream_report.get("decision")==NO_GO and
      upstream_report.get("organismes_denombrables")==1343 and
      upstream_report.get("recettes_consolidees_interorganismes_certifiees") is False,
      "P53G_CONSOLIDATION_FICTIVE")
 groups,top,all_items=priorities(local+other)
 must(m.get("groupes")==groups,"DECOMPTE_PAR_GROUPE_INCORRECT")
 must(m.get("priorites_relecture")==top,"CLASSEMENT_NON_REPRODUCTIBLE")
 observed=m.get("chiffres_controle",{})
 must(observed=={
  "total_flux_recus_quotes_et_transferts_signes_cad":"10864282201",
  "somme_montants_candidats_top25_cad":"7069371200",
  "ratio_top25_sur_flux_totaux":"7069371200/10864282201",
  "total_transferts_seuls_cad":"7716073104",
  "total_quotes_parts_seules_cad":"3148209097",
  "recettes_comptables_brutes_1343_organismes_cad":"41663676586",
  "montant_eliminable_preuve_cad":None,
  "recettes_publiques_consolidees_cad":None,
  "montant_projet_nova_2026_2027_cad":None,
 },"MONTANTS_CONFONDUS_AVEC_ECONOMIES")
 must(m.get("instructions_de_verification")==REQUIREMENTS,
      "PROTOCOLE_HUMAIN_ABSENT")
 must(m.get("bilan")=={
  "lignes_analysees":1343,"groupes":5,"organismes_top25":25,
  "operations_reciproques_demontrees":0,
  "eliminations_reelles_certifiees":0,
  "avis_comptables_independants_signes":0,
  "preuves_F01_F20_validees":0,
  "montants_nova_inconnus":1320,
  "taux_nova_adoptes":0,
  "publication_autorisee":False,
  "fusion_autorisee":False,"adoption_autorisee":False,
  "decision":NO_GO
 },"CERTIFICATION_FISCALE_INVENTEE")
 return {
  "jalon":"P53H","annee":2024,
  "organismes_2024_controles":len(all_items),
  "organismes_priorises":len(top),
  "groupes":len(groups),
  "exposition_brute_signee_a_etudier_CAD":10864282201,
  "exposition_signee_top25_CAD":7069371200,
  "concentration_top25_pourcent_approx":"65.07",
  "appariements_reciproques_documentes":0,
  "eliminations_certifiees_CAD":None,
  "credits_budgetaires_2026_2027_justifies":False,
  "preuves_fiscales_validees":0,
  "parametres_financiers_Nova_inconnus":1320,
  "publication_autorisee":False,
  "fusion_autorisee":False,"adoption_autorisee":False,
  "decision":NO_GO
 }

def export_csv(items):
 stream=io.StringIO(newline="")
 writer=csv.writer(stream,lineterminator="\n")
 writer.writerow([
  "priorite","code_organisme","nom_organisme","type_org",
  "quotes_parts_recues_2024_CAD","transferts_recus_2024_CAD",
  "somme_signee_2024_CAD","montant_absolu_CAD",
  "payeur_identifie","piece_depense_reciproque","avis_independant",
  "montant_elimination_certifie_CAD"
 ])
 for i,row in enumerate(items):
  writer.writerow([
   i+1,row["code_organisme"],row["nom_organisme"],row["type_org"],
   "" if row["quotes_parts_cad"] is None else row["quotes_parts_cad"],
   "" if row["transferts_cad"] is None else row["transferts_cad"],
   row["flux_candidats_signes_cad"],row["montant_absolu_cad"],
   "","","",""
  ])
 return stream.getvalue()

def save_new(path,content):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as f:f.write(content)

def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__)
 for key,path in FILES.items():ap.add_argument("--"+key,type=Path,default=path)
 ap.add_argument("--csv-local",type=Path,default=LOCAL)
 ap.add_argument("--csv-complementaire",type=Path,default=OTHER)
 ap.add_argument("--rapport",type=Path)
 ap.add_argument("--export-csv",type=Path)
 ap.add_argument("--exiger-appariement",action="store_true")
 args=ap.parse_args(argv)
 try:
  docs={key:read(getattr(args,key)) for key in FILES}
  loc,other=source_rows(local=args.csv_local,other=args.csv_complementaire)
  result=validate(docs,loc,other)
  if args.rapport and args.export_csv:
   must(args.rapport.resolve()!=args.export_csv.resolve(),"SORTIES_IDENTIQUES")
  if args.rapport:save_new(args.rapport,json.dumps(result,ensure_ascii=False,indent=2)+"\n")
  if args.export_csv:
   _,_,items=priorities(loc+other)
   save_new(args.export_csv,export_csv(items))
  if not args.rapport and not args.export_csv:
   print(json.dumps(result,ensure_ascii=False,indent=2))
  return 3 if args.exiger_appariement else 0
 except (OSError,ValueError,UnicodeError,TypeError,KeyError,ImportError) as exc:
  print(json.dumps({"jalon":"P53H","etat":"CONTROLE_REJETE",
        "classe_erreur":type(exc).__name__,
        "publication_autorisee":False,
        "fusion_autorisee":False,"adoption_autorisee":False,
        "decision":NO_GO},ensure_ascii=False))
  return 2

if __name__=="__main__":
 sys.exit(main())
