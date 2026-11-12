#!/usr/bin/env python3
"""P53A: revenus budgétaires vérifiables, périmètres manquants et NO_GO."""
import argparse
import csv
import io
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "registre":D/"P53A_REGISTRE_RECETTES_ET_COMPETENCES.json",
 "lacunes":D/"P53A_LACUNES_HORS_PERIMETRE.json",
 "p52c":D/"P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json",
 "p52j":D/"P52J_RELECTURE_PRIMAIRE_BUDGET_2026_2027.json",
 "p52z":D/"P52Z_MATRICE_FISCALITE_JURIDICTIONS.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
GROUP_CLASSES={
 "impots_sur_revenu_et_biens":"PRELEVEMENTS_ET_IMPOTS_A_QUALIFIER",
 "taxes_consommation":"PRELEVEMENT_A_EXAMINER",
 "entreprises_gouvernement":"REVENU_ENTREPRISE_PUBLIQUE_NON_TAXE",
 "droits_permis_redevances":"RECETTE_MIXTE_A_DECOMPOSER",
 "revenus_divers":"RECETTE_MIXTE_A_DECOMPOSER",
 "transferts_federaux":"TRANSFERT_FEDERAL_NON_FISCAL",
}
TOPIC_GROUP={
 "impots_sur_revenu_et_biens":("T01","F05"),
 "taxes_consommation":("T09","F07"),
 "entreprises_gouvernement":("T09","F09"),
 "droits_permis_redevances":("T09","F07"),
 "revenus_divers":("T09","F07"),
 "transferts_federaux":("T11","F02"),
}
SUPPLEMENT=[
 ("E01","FEDERAL","T02","F02"),
 ("E02","FEDERAL","T04","F02"),
 ("E03","FEDERAL","T06","F03"),
 ("E04","MUNICIPAL","T07","F04"),
 ("E05","MUNICIPAL","T07","F04"),
 ("E06","REGIMES_CONTRIBUTIFS","T09","F07"),
 ("E07","FEDERAL","T09","F07"),
 ("E08","REGIMES_CONTRIBUTIFS","T09","F07"),
 ("E09","FEDERAL","T09","F07"),
]
RULES={
 "ventes_aggregat_pas_tvq_seule","cotisations_pas_automatiquement_abolies",
 "entreprises_publiques_pas_impots","droits_et_redevances_a_ventiler",
 "transferts_federaux_pas_taxes_provinciales",
 "transferts_non_garantis_souverainete","ne_pas_double_compter_sous_totaux",
 "service_dette_dans_depenses_totales",
 "provision_et_fonds_generations_distincts",
 "taux_nova_non_deductible_des_chiffres_actuels",
}
GUARDS={"publication_autorisee","fusion_autorisee","adoption_autorisee"}
REG_KEYS={
 "id","libelle","groupe","nature_p52c","montant_mcad","source","position",
 "classe","juridiction","question_p52z","preuve_p52a","statut_regime_canada",
 "statut_regime_souverain","reforme_adoptee","recette_nova_mcad",
 "cout_remplacement_mcad","avis_signe"
}
GAP_KEYS={
 "id","objet","juridiction","question_p52z","preuve_p52a","montant_mcad",
 "periode_comparable_verifiee","source_officielle_extraite_et_authentifiee",
 "perimetre_et_double_comptage_valide","recette_nova_mcad"
}
NUM=re.compile(r"-?\d+\Z")

def must(condition,msg):
 if not condition:raise ValueError(msg)

def number(s):
 must(type(s) is str and NUM.fullmatch(s),"VALEUR_BUDGET_INVALIDE")
 return int(s)

def read(path):
 p=Path(path)
 must(p.is_file() and not p.is_symlink() and
      0<p.stat().st_size<=650000,"SOURCE_ABSENTE_OU_TROP_GRANDE")
 data=json.loads(p.read_text(encoding="utf-8"))
 must(type(data) is dict,"OBJET_JSON_ATTENDU")
 return data

def validate(d):
 must(type(d) is dict and set(d)==set(FILES),"SIX_REGISTRES_REQUIS")
 m,g,c,j,z,a=(d[key] for key in FILES)
 must(m.get("schema_version")=="P53A-1" and m.get("jalon")=="P53A" and
      m.get("date_reference")=="2026-10-20" and
      m.get("periode")=="2026-2027" and m.get("unite")=="M_CAD" and
      m.get("statut")=="PREVISIONS_PROVINCIALES_PARTIELLES_NON_CONSOLIDEES",
      "P53A_SOURCE_NATURE_INVALIDE")
 must(m.get("references")=={
     key:str(FILES[key].relative_to(ROOT))
     for key in ("p52c","p52j","p52z","p52a","lacunes")},
     "P53A_REFERENCES_INCOHERENTES")
 must(c.get("schema_version")=="P52C-1" and
      c.get("periode")=="2026-2027" and c.get("unite")=="M_CAD" and
      c.get("statut")=="REFERENCE_OFFICIELLE_MARS_2026_PREVISION_NON_REALISEE" and
      c.get("decision")=="NO_GO_AUTOMATIQUE","P52C_REFERENCE_INVALIDE")
 must(j.get("schema_version")=="P52J-1" and
      j.get("validation_de_nature",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
      j["validation_de_nature"].get("preuve_F09_independamment_attestee") is False,
      "P52J_INDEPENDANCE_FAUSSE")
 must(z.get("schema_version")=="P52Z-1" and
      z.get("bilan",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
      [q.get("id") for q in z.get("questions",[])]==[
         "T%02d"%i for i in range(1,13)],"P52Z_COMPETENCE_INVALIDE")
 must(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
      a.get("automatic_go") is False and
      a.get("financial_model_certified") is False and
      [p.get("id") for p in a.get("required_evidence",[])]==[
         "F%02d"%i for i in range(1,21)] and
      all(p.get("statut")=="NON_VALIDE" and
          p.get("preuve_independante_obtenue") is False
          for p in a["required_evidence"]),
      "P52A_PREUVE_FISCALE_FICTIVE")
 must(m.get("perimetre")=={
      "gouvernement_quebec_uniquement":True,
      "taxes_federales_hors_perimetre":True,
      "taxes_municipales_hors_perimetre":True,
      "previsions_non_resultats":True,
      "pouvoirs_souverains_non_acquis":True},
      "PERIMETRE_TROMPEUR")
 rows=m.get("lignes");official=c.get("lignes_revenus")
 jrows=j["transcription_discours_tableau3"]["lignes_revenus"]
 must(type(rows) is list and len(rows)==21 and
      type(official) is list and len(official)==21 and
      type(jrows) is list and len(jrows)==21,"VINGT_ET_UNE_LIGNES_REQUISES")
 buckets={"income":0,"other_taxes":0,"non_tax":0,"federal":0}
 groups={group:0 for group in GROUP_CLASSES}
 for i,(r,ref,jref) in enumerate(zip(rows,official,jrows)):
  must(type(r) is dict and set(r)==REG_KEYS,"SCHEMA_LIGNE_INVALIDE")
  must(r.get("id")==ref.get("id")==jref.get("id") and
       r.get("libelle")==ref.get("libelle") and
       r.get("groupe")==ref.get("groupe") and
       r.get("nature_p52c")==ref.get("nature") and
       r.get("source")==ref.get("source_id")=="DISC2026_T3" and
       r.get("montant_mcad")==ref.get("valeur_mcad")==jref.get("valeur_mcad") and
       type(r.get("position")) is int and r["position"]==i+1,
       "VALEUR_OFFICIELLE_OU_LIGNE_MODIFIEE")
  group=r["groupe"]
  must(group in GROUP_CLASSES,"GROUPE_NON_RECONNU")
  cls=GROUP_CLASSES[group];topic,proof=TOPIC_GROUP[group]
  if r["id"] in ("impot_particuliers","impot_societes"):
   cls="IMPOT_REVENUS_ACTUEL_NON_GARANTI_NOVA"
  if r["id"]=="foncier_scolaire":topic,proof="T08","F04"
  if r["id"]=="cotisations_sante":topic,proof="T09","F07"
  if r["id"]=="taxes_vente":topic,proof="T03","F07"
  must(r.get("classe")==cls and
       r.get("question_p52z")==topic and
       r.get("preuve_p52a")==proof and
       r.get("juridiction")==(
       "TRANSFERT_CANADA_VERS_QUEBEC" if group=="transferts_federaux"
       else "BUDGET_QUEBEC") and
       r.get("statut_regime_canada")=="DECISION_A_DOCUMENTER" and
       r.get("statut_regime_souverain")=="CONTINUITE_NON_ACQUISE" and
       r.get("reforme_adoptee") is False and
       r.get("recette_nova_mcad") is None and
       r.get("cout_remplacement_mcad") is None and
       r.get("avis_signe") is False,
       "REFORME_OU_CLASSEMENT_INVENTE")
  val=number(r["montant_mcad"])
  must(val>=0,"RECETTE_NEGATIVE_NON_ATTENDUE")
  groups[group]+=val
  if cls=="IMPOT_REVENUS_ACTUEL_NON_GARANTI_NOVA":buckets["income"]+=val
  elif group=="transferts_federaux":buckets["federal"]+=val
  elif group in ("impots_sur_revenu_et_biens","taxes_consommation"):
   buckets["other_taxes"]+=val
  else:buckets["non_tax"]+=val
 subtotal=c["sous_totaux_officiels_mcad"]
 must(m.get("sous_totaux_officiels_mcad")==subtotal and
      j["transcription_discours_tableau3"]["sous_totaux_officiels_mcad"]==subtotal,
      "SOUS_TOTAUX_OFFICIELS_ALTERES")
 for group in GROUP_CLASSES:
  must(groups[group]==number(subtotal[group]),"SOMME_GROUPE_INEXACTE")
 own=sum(groups[x] for x in GROUP_CLASSES if x!="transferts_federaux")
 must(own==number(subtotal["revenus_autonomes"])==134361 and
      groups["transferts_federaux"]==number(subtotal["transferts_federaux"])==32131 and
      own+groups["transferts_federaux"]==number(subtotal["revenus_totaux"])==166492,
      "RECONCILIATION_REVENUS_INVALIDE")
 must(buckets=={"income":65327,"other_taxes":40731,
                "non_tax":28303,"federal":32131},"QUATRE_COMPARTIMENTS_INEXACTS")
 partition=m.get("compartiments_non_additionner_aux_lignes",{})
 must(partition=={
     "impots_revenu_quebec_existants_mcad":"65327",
     "autres_prelevements_identifies_mcad":"40731",
     "entreprises_droits_et_divers_mcad":"28303",
     "transferts_federaux_mcad":"32131",
     "total_budget_quebec_mcad":"166492",
     "recettes_nouvelles_nova_mcad":None,
     "revenus_federaux_municipaux_mcad":None},
      "PARTITIONS_TROMPEUSES")
 dcost=c.get("depenses_et_ajustements_officiels_mcad")
 must(m.get("depenses_officielles_mcad")==dcost,
      "COUTS_OFFICIELS_ALTERES")
 must(number(dcost["depenses_portefeuilles"])==160489 and
      number(dcost["service_dette"])==10268 and
      number(dcost["depenses_totales"])==170757 and
      160489+10268==170757 and
      number(dcost["provision_eventualites"])==2000 and
      166492-170757-2000==number(dcost["deficit_comptable"])==-6265 and
      number(dcost["versements_fonds_generations"])==2347 and
      -6265-2347==number(dcost["solde_budgetaire_loi_equilibre"])==-8612,
      "SOLDE_BUDGETAIRE_NON_CONCORDANT")
 must(set(m.get("regles",{}))==RULES and
      all(m["regles"][key] is True for key in RULES),
      "REGLE_PERIMETRE_SUPPRIMEE")
 must(g.get("schema_version")=="P53A-LACUNES-1" and
      g.get("statut")=="DONNEES_HORS_BUDGET_NON_ACQUISES" and
      g.get("reference_p53a")==str(FILES["registre"].relative_to(ROOT)),
      "LACUNES_ABSENTES")
 source=g.get("source_municipale_candidate",{})
 must(source=={
    "url":"https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1010002001",
    "tableau":"10-10-0020-01",
    "selection_geographie_annee_et_nature_reelle":False},
    "SOURCE_MUNICIPALE_FAUSSEMENT_IMPORTEE")
 gaps=g.get("dossiers")
 must(type(gaps) is list and len(gaps)==9 and
      [x.get("id") for x in gaps]==[p[0] for p in SUPPLEMENT],
      "NEUF_LACUNES_MANQUANTES")
 for r,ref in zip(gaps,SUPPLEMENT):
  ident,level,topic,proof=ref
  must(type(r) is dict and set(r)==GAP_KEYS and
       r.get("id")==ident and r.get("juridiction")==level and
       r.get("question_p52z")==topic and r.get("preuve_p52a")==proof and
       type(r.get("objet")) is str and len(r["objet"])>=12 and
       r.get("montant_mcad") is None and
       r.get("recette_nova_mcad") is None and
       r.get("periode_comparable_verifiee") is False and
       r.get("source_officielle_extraite_et_authentifiee") is False and
       r.get("perimetre_et_double_comptage_valide") is False,
       "MONTANT_HORS_PERIMETRE_INVENTE")
 must(g.get("bilan")=={
      "lacunes":9,"postes_chiffres":0,
      "consolidation_tous_niveaux":False,
      "publication_autorisee":False,"fusion_autorisee":False,
      "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"},
      "FAUSSE_CONSOLIDATION")
 status=m.get("bilan",{})
 must(status=={
     "lignes_recettes":21,"lacunes_hors_perimetre":9,
     "preuves_F01_F20_certifiees":0,"montants_nova_inconnus":1320,
     "avis_experts_reels":0,"taux_fiscaux_adoptes":0,
     "publication_autorisee":False,"fusion_autorisee":False,
     "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"},
     "FAUSSE_CERTIFICATION")
 return {
    "jalon":"P53A","schema_version":"P53A-1",
    "recettes_gouvernement_quebec_mcad":166492,
    "recettes_autonomes_quebec_mcad":134361,
    "transferts_federaux_dans_budget_mcad":32131,
    "impots_revenu_existant_quebec_mcad":65327,
    "autres_prelevements_a_instruire_mcad":40731,
    "revenus_entreprises_droits_divers_mcad":28303,
    "depenses_totales_avec_service_dette_mcad":170757,
    "deficit_comptable_mcad":-6265,
    "solde_loi_equilibre_mcad":-8612,
    "lignes_recettes_budget":21,
    "lacunes_sans_montant":9,
    "consolidation_intergouvernementale_obtenue":False,
    "revenus_du_projet_nova_certifies":False,
    "preuves_F01_F20_non_validees":20,
    "valeurs_nova_inconnues":1320,
    "publication_autorisee":False,"fusion_autorisee":False,
    "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"}

def csv_export(doc):
 out=io.StringIO(newline="")
 wr=csv.writer(out,lineterminator="\n")
 wr.writerow(["id","libelle","perimetre","classe","montant_mcad_prevu_ou_vide",
              "source","juridiction_p52z","preuve_p52a",
              "scenario_canada_a_evaluer","scenario_souverain_a_evaluer",
              "avis_independant_recu"])
 for x in doc["registre"]["lignes"]:
  wr.writerow([x["id"],x["libelle"],"GOUVERNEMENT_QUEBEC",
               x["classe"],x["montant_mcad"],x["source"],
               x["question_p52z"],x["preuve_p52a"],"","",""])
 for x in doc["lacunes"]["dossiers"]:
  wr.writerow([x["id"],x["objet"],x["juridiction"],
               "HORS_PERIMETRE_SANS_MONTANT","",
               "SOURCE_EXTERNE_A_INSTRUIRE",
               x["question_p52z"],x["preuve_p52a"],"","",""])
 return out.getvalue()

def save(path,content):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as f:f.write(content)

def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__)
 for key,path in FILES.items():ap.add_argument("--"+key,type=Path,default=path)
 ap.add_argument("--rapport",type=Path)
 ap.add_argument("--export-csv",type=Path)
 ap.add_argument("--exiger-completude",action="store_true")
 args=ap.parse_args(argv)
 try:
  docs={key:read(getattr(args,key)) for key in FILES}
  report=validate(docs)
  if args.rapport and args.export_csv:
   must(args.rapport.resolve()!=args.export_csv.resolve(),
        "RAPPORT_ET_CSV_MEME_CHEMIN")
  if args.rapport:save(args.rapport,json.dumps(report,ensure_ascii=False,indent=2)+"\n")
  if args.export_csv:save(args.export_csv,csv_export(docs))
  if not args.rapport and not args.export_csv:
   print(json.dumps(report,ensure_ascii=False,indent=2))
  return 3 if args.exiger_completude else 0
 except (OSError,ValueError,KeyError,TypeError,UnicodeError) as ex:
  print(json.dumps({"jalon":"P53A","etat":"CONTROLE_REJETE",
    "categorie_erreur":type(ex).__name__,
    "publication_autorisee":False,"fusion_autorisee":False,
    "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"},ensure_ascii=False))
  return 2

if __name__=="__main__":
 sys.exit(main())
