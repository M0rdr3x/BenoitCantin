#!/usr/bin/env python3
"""P53B: nine external-source gaps and observed 2026 payroll rates, never aggregate yields."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import io
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "p53b":D/"P53B_SOURCES_ET_COTISATIONS_2026.json",
 "p53a":D/"P53A_REGISTRE_RECETTES_ET_COMPETENCES.json",
 "lacunes":D/"P53A_LACUNES_HORS_PERIMETRE.json",
 "p52z":D/"P52Z_MATRICE_FISCALITE_JURIDICTIONS.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
URLS={
 "ARC2024":"https://www.canada.ca/fr/agence-revenu/programmes/a-propos-agence-revenu-canada-arc/statistiques-revenu-statistiques-tps-tvh/statistiques-impot-particuliers-tranche-imposition/statistiques-impot-particuliers-tranche-imposition-edition-2026-annee-imposition-2024.html",
 "STATCAN_LOCAL":"https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1010002001",
 "MAMH_LOCAL":"https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier?annee=2023&organisme=31122",
 "RRQ2026":"https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/calcul-des-retenues-et-des-cotisations/cotisations-au-rrq/maximum-des-gains-admissibles-et-taux-de-cotisation/",
 "AE2026":"https://www.canada.ca/fr/emploi-developpement-social/programmes/assurance-emploi/ae-liste/rapports/cotisation/taux2026.html",
 "RQAP2026":"https://www.quebec.ca/entreprises-et-travailleurs-autonomes/administrer-gerer/embauche-gestion-personnel/assurance-parentale/taux-cotisations",
 "CRA_T1_2024":"https://www.canada.ca/fr/agence-revenu/programmes/a-propos-agence-revenu-canada-arc/statistiques-revenu-statistiques-tps-tvh/statistiques-finales-t1/annee-imposition-2024.html",
 "STATCAN_PENSION":"https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1010002201",
 "ARC_PAIE_2026":"https://www.canada.ca/fr/agence-revenu/services/formulaires-publications/retenues-paie/t4032-tables-retenues-paie/t4032qc-jan/t4032qc-janvier-information-generale.html"
}
TASKS={
 "E01":("ARC2024","ANNEE_IMPOSITION_2024","F02","T02"),
 "E02":("CRA_T1_2024","PAS_SOURCE_TPS_QUEBEC","F02","T04"),
 "E03":("CRA_T1_2024","PAS_SOURCE_DOUANE_QUEBEC","F03","T06"),
 "E04":("STATCAN_LOCAL","EXERCICE_ANNUEL_JUSQU_A_2024","F04","T07"),
 "E05":("MAMH_LOCAL","PUBLICATIONS_2024","F04","T07"),
 "E06":("RRQ2026","BAREME_2026","F07","T09"),
 "E07":("AE2026","BAREME_2026","F07","T09"),
 "E08":("RQAP2026","BAREME_2026","F07","T09"),
 "E09":("ARC_PAIE_2026","PAS_SOURCE_ACCISES_AGREGEES","F07","T09")
}
RATES={
 "RRQ_BASE_SALARIE_2026":("RRQ2026","RRQ","6.30"),
 "RRQ_BASE_EMPLOYEUR_2026":("RRQ2026","RRQ","6.30"),
 "RRQ_SUPPLEMENT_SALARIE_2026":("RRQ2026","RRQ","4.00"),
 "RRQ_SUPPLEMENT_EMPLOYEUR_2026":("RRQ2026","RRQ","4.00"),
 "AE_SALARIE_QUEBEC_2026":("AE2026","AE","1.30"),
 "AE_EMPLOYEUR_QUEBEC_2026":("AE2026","AE","1.82"),
 "RQAP_SALARIE_2026":("RQAP2026","RQAP","0.430"),
 "RQAP_EMPLOYEUR_2026":("RQAP2026","RQAP","0.602"),
 "RQAP_AUTONOME_2026":("RQAP2026","RQAP","0.764")
}
CAPS={
 "rrq_exemption_generale_cad":"3500",
 "rrq_max_gains_base_cad":"74600",
 "rrq_max_supplement_cad":"85000",
 "rrq_base_max_salarie_cad":"4479.30",
 "rrq_supplement_max_salarie_cad":"416.00",
 "ae_max_remuneration_assurable_cad":"68900",
 "ae_max_salarie_cad":"895.70",
 "ae_max_employeur_cad":"1253.98",
 "rqap_max_salarie_cad":"442.90",
 "rqap_max_employeur_cad":"620.06",
 "rqap_max_autonome_cad":"786.92"
}
RULES={
 "barèmes_2026_ne_sont_pas_recettes_agregées",
 "source_T1_2024_n_est_pas_budget_2026_2027",
 "données_municipales_2024_ne_sont_pas_budget_2026_2027",
 "cotisations_régimes_ne_sont_pas_impôts_sur_revenu",
 "deux_taxes_n_abolissent_pas_les_droits_a_prestations",
 "pas_d_imputation_d_impot_fédéral_depuis_totaux_nationaux",
 "pas_d_imputation_de_TPS_ou_douanes_à_partir_de_T1",
 "pas_d_addition_des_transferts_entre_administrations",
 "plafonds_employeurs_et_salariés_sont_distincts",
 "calculs_de_plafonds_non_suffisants_pour_soutenir_une_reforme",
 "aucune_reconduction_automatique_de_transferts_en_souveraineté"
}

def need(ok,reason):
 if not ok:raise ValueError(reason)

def read(path):
 p=Path(path)
 need(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=600000,
      "SOURCE_JSON_ABSENTE_OU_TROP_GRANDE")
 obj=json.loads(p.read_text(encoding="utf-8"))
 need(type(obj) is dict,"JSON_OBJECT_ATTENDU")
 return obj

def dec(raw):
 need(type(raw) is str and bool(re.fullmatch(r"\d+(?:\.\d{1,3})?",raw)),
      "DECIMALE_INVALIDE")
 return Decimal(raw)

def verify(docs):
 need(type(docs) is dict and set(docs)==set(FILES),
      "CINQ_SOURCES_ATTENDUES")
 m,a,g,z,p=(docs[k] for k in FILES)
 need(m.get("schema_version")=="P53B-1" and m.get("jalon")=="P53B" and
      m.get("date_reference")=="2026-10-20" and
      m.get("statut")=="SOURCES_REPEREES_BAREMES_OBSERVES_REVENUS_HORS_BUDGET_NON_CONSOLIDES",
      "P53B_SCHEMA_INVALIDE")
 need(m.get("references")=={key:str(FILES[key].relative_to(ROOT))
      for key in FILES if key!="p53b"},"P53B_LIENS_MANQUANTS")
 need(a.get("schema_version")=="P53A-1" and
      a.get("bilan",{}).get("lignes_recettes")==21 and
      a["bilan"].get("montants_nova_inconnus")==1320 and
      a["bilan"].get("decision")=="NO_GO_AUTOMATIQUE" and
      a.get("perimetre",{}).get("taxes_federales_hors_perimetre") is True,
      "P53A_REFERENCE_INVALIDE")
 need(g.get("schema_version")=="P53A-LACUNES-1" and
      g.get("bilan",{}).get("lacunes")==9 and
      g["bilan"].get("postes_chiffres")==0 and
      g["bilan"].get("consolidation_tous_niveaux") is False and
      g["bilan"].get("decision")=="NO_GO_AUTOMATIQUE",
      "LACUNES_NON_RECUES")
 need(z.get("schema_version")=="P52Z-1" and
      z.get("bilan",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
      [r.get("id") for r in z.get("questions",[])]==[
          "T%02d"%i for i in range(1,13)],
      "REFERENTIEL_JURIDIQUE_MANQUANT")
 need(p.get("status")=="PROPOSITION_NON_ADOPTEE" and
      p.get("automatic_go") is False and
      p.get("financial_model_certified") is False and
      p.get("rates_selected") is False and
      [r.get("id") for r in p.get("required_evidence",[])]==[
          "F%02d"%i for i in range(1,21)] and
      all(r.get("statut")=="NON_VALIDE" and
          r.get("preuve_independante_obtenue") is False
          for r in p["required_evidence"]),
      "PREUVES_FISCALES_FAUSSEMENT_VALIDES")
 sources=m.get("sources")
 need(type(sources) is list and len(sources)==9 and
      [r.get("id") for r in sources]==list(URLS),
      "NEUF_SOURCES_OFFICIELLES_ATTENDUES")
 for s in sources:
  need(type(s) is dict and s.get("url")==URLS[s["id"]] and
       type(s.get("periode")) is str and len(s["periode"])>=11 and
       type(s.get("nature")) is str and len(s["nature"])>=12 and
       type(s.get("description")) is str and len(s["description"])>35 and
       s.get("consulte_page_officielle_2026_10_20") is True and
       s.get("extraction_structurée_et_SHA256_verifies") is False and
       s.get("avis_independant_obtenu") is False and
       s.get("donnees_publiques_sans_microdonnees") is True,
       "SOURCE_NON_AUTHENTIFIEE_DECLAREE_COMPLETE")
 gaprows=m.get("dossiers")
 need(type(gaprows) is list and len(gaprows)==9 and
      [r.get("id") for r in gaprows]==list(TASKS),
      "NEUF_DOSSIERS_CIBLES_ATTENDUS")
 need(len(g.get("dossiers",[]))==9 and
      [r.get("id") for r in g["dossiers"]]==list(TASKS),
      "LACUNES_P53A_MODIFIEES")
 for row,base in zip(gaprows,g["dossiers"]):
  src,period,proof,topic=TASKS[row["id"]]
  need(row.get("source_id")==src and
       row.get("comparabilite")==period and
       row.get("fpreuve")==proof==base["preuve_p52a"] and
       row.get("jur")==topic==base["question_p52z"] and
       type(row.get("travail")) is str and len(row["travail"])>75 and
       row.get("etat_donnees")=="ASSIETTE_OU_MONTANT_ANNUEL_NON_RECU" and
       row.get("montant_annuel_reel_quebec_mcad") is None and
       row.get("annee_montant_validee") is None and
       row.get("ventilation_province_prouvee") is False and
       row.get("transferts_dedoubles") is False and
       row.get("avis_expert_independant_signe") is False and
       row.get("utilisable_pour_modele_nova") is False and
       base.get("montant_mcad") is None and
       base.get("recette_nova_mcad") is None,
       "FAUSSE_COHERENCE_OU_MONTANT_EXTERNE")
 rates=m.get("barèmes_2026")
 need(type(rates) is list and len(rates)==9 and
      [r.get("id") for r in rates]==list(RATES),
      "NEUF_BAREMES_VERIFIES_REQUIS")
 for r in rates:
  src,family,rate=RATES[r["id"]]
  need(r.get("source_id")==src and r.get("famille")==family and
       type(r.get("annee")) is int and r["annee"]==2026 and
       r.get("unite")=="TAUX_POURCENT" and r.get("valeur")==rate and
       type(r.get("assiette")) is str and len(r["assiette"])>=30 and
       r.get("montant_agrege_mcad") is None,
       "BAREME_HISTORIQUE_MODIFIE_OU_TAXE_NOVA_FICTIVE")
 cap=m.get("plafonds_2026")
 need(cap==CAPS,"PLAFONDS_OFFICIELS_A_CONTROLER")
 need((dec(cap["rrq_max_gains_base_cad"])-dec(cap["rrq_exemption_generale_cad"]))*
      dec(RATES["RRQ_BASE_SALARIE_2026"][2])/100 ==
      dec(cap["rrq_base_max_salarie_cad"]),
      "RRQ_BASE_PLAFOND_ARITHMETIQUE")
 need((dec(cap["rrq_max_supplement_cad"])-dec(cap["rrq_max_gains_base_cad"]))*
      dec(RATES["RRQ_SUPPLEMENT_SALARIE_2026"][2])/100 ==
      dec(cap["rrq_supplement_max_salarie_cad"]),
      "RRQ_SUPPLEMENT_PLAFOND_ARITHMETIQUE")
 need(dec(cap["ae_max_remuneration_assurable_cad"])*
      dec(RATES["AE_SALARIE_QUEBEC_2026"][2])/100 ==
      dec(cap["ae_max_salarie_cad"]) and
      dec(cap["ae_max_remuneration_assurable_cad"])*
      dec(RATES["AE_EMPLOYEUR_QUEBEC_2026"][2])/100 ==
      dec(cap["ae_max_employeur_cad"]),
      "AE_TAUX_PLAFONDS_NON_CONCORDANTS")
 # The RQAP maxima must come from the government source, not inference to a total contribution.
 for role in ("salarie","employeur","autonome"):
  value=dec(cap["rqap_max_"+role+"_cad"])
  need(value>0 and value<1000,"RQAP_PLAFONDS_INCORRECTS")
 rules=m.get("règles_non_additivité")
 need(type(rules) is dict and set(rules)==RULES and
      all(rules[x] is True for x in RULES),"PRECAUTIONS_FISCALES_EFFACEES")
 stats=m.get("bilan")
 need(stats=={
    "sources_publiques_identifiées":9,
    "barèmes_principaux_2026_relevés":9,
    "dossiers_de_lacunes_couverts":9,
    "montants_hors_budget_certifiés":0,
    "barèmes_transposés_en_recettes_totales":0,
    "années_comparables_validées":0,
    "preuves_F01_F20_validées":0,
    "montants_financiers_nova_inconnus":1320,
    "publication_autorisée":False,"fusion_autorisée":False,
    "adoption_autorisée":False,"decision":"NO_GO_AUTOMATIQUE"},
    "FAUSSE_COMPLETUDE_ENREGISTREE")
 return {
    "jalon":"P53B","schema_version":"P53B-1",
    "sources_officielles_reperees":9,
    "taux_contributifs_2026_releves":9,
    "plafonds_rrq_et_ae_reconcilies":True,
    "lacunes_hors_budget_documentees":9,
    "lacunes_hors_budget_chiffrees":0,
    "annees_comparables_et_consolidees":0,
    "barèmes_convertis_en_recettes_fiscales":0,
    "preuves_F01_F20_non_validees":20,
    "donnees_nova_inconnues":1320,
    "fusion_autorisee":False,"publication_autorisee":False,
    "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"}

def csv_gaps(m):
 buf=io.StringIO(newline="")
 wr=csv.writer(buf,lineterminator="\n")
 wr.writerow(["lacune","source_id","periode_source","preuve_a_obtenir","montant_annuel_quebec_MCAD","controle_source","anti_double_compte_valide"])
 for r in m["dossiers"]:
  wr.writerow([r["id"],r["source_id"],r["comparabilite"],r["travail"],"","",""])
 return buf.getvalue()

def csv_rates(m):
 buf=io.StringIO(newline="")
 wr=csv.writer(buf,lineterminator="\n")
 wr.writerow(["parametre","source","annee","famille","taux_pourcent","assiette","recette_totale_MCAD_inconnue"])
 for r in m["barèmes_2026"]:
  wr.writerow([r["id"],r["source_id"],r["annee"],r["famille"],r["valeur"],r["assiette"],""])
 return buf.getvalue()

def save_new(path,content):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as f:f.write(content)

def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__)
 for k,path in FILES.items():ap.add_argument("--"+k,type=Path,default=path)
 ap.add_argument("--rapport",type=Path)
 ap.add_argument("--export-csv",type=Path)
 ap.add_argument("--export-baremes-csv",type=Path)
 ap.add_argument("--exiger-consolidation",action="store_true")
 args=ap.parse_args(argv)
 try:
  d={k:read(getattr(args,k)) for k in FILES}
  summary=verify(d)
  paths=[x for x in (args.rapport,args.export_csv,args.export_baremes_csv) if x]
  need(len({x.resolve() for x in paths})==len(paths),"DESTINATIONS_IDENTIQUES")
  if args.rapport:save_new(args.rapport,json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
  if args.export_csv:save_new(args.export_csv,csv_gaps(d["p53b"]))
  if args.export_baremes_csv:save_new(args.export_baremes_csv,csv_rates(d["p53b"]))
  if not paths:print(json.dumps(summary,ensure_ascii=False,indent=2))
  return 3 if args.exiger_consolidation else 0
 except (OSError,ValueError,UnicodeError,TypeError,KeyError,InvalidOperation) as exc:
  print(json.dumps({"jalon":"P53B","statut":"REJET_CONTROLE",
    "categorie_erreur":type(exc).__name__,
    "fusion_autorisee":False,"publication_autorisee":False,
    "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"},ensure_ascii=False))
  return 2
if __name__=="__main__":
 sys.exit(main())
