#!/usr/bin/env python3
"""Projet Nova P52V: preparer une grille de mission F09, sans avis humain fictif."""
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
 "mission":D/"P52V_REGISTRE_MISSION_F09.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
 "p52n":D/"P52N_CAHIER_MANDATS_ET_CONSULTATION.json",
 "p52q":D/"P52Q_DOSSIERS_INSTRUCTION_VAGUE1.json",
 "p52u":D/"P52U_INSTRUCTION_HUMAINE_F09.json",
 "p52j":D/"P52J_RELECTURE_PRIMAIRE_BUDGET_2026_2027.json",
 "p52s":D/"P52S_RECEPISSES_HTTPS_OBSERVES_2026_10_20.json",
}
URLS=(
 "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/index.asp",
 "https://www.assnat.qc.ca/fr/travaux-parlementaires/assemblee-nationale/43-2/journal-debats/20260318so/documents-deposes.html",
 "https://cpaquebec.ca/fr/trouver-un-cpa/tableau-de-lordre/intro/"
)
KEYS={"position","source_id","page_tableau_pdf_zero","page_imprimee",
      "unite","identifiant_ligne_P52J","valeur_attendue_lecture_non_certifiee",
      "resultat_extraction_automatisee_P52U","statut_relecture_humaine",
      "montant_confirme_par_expert","divergence_documentee",
      "reference_d_avis_avec_acces_restreint","signature_humaine_authentifiee"}
SELECT_BOOL={
 "autorite_de_mandatement_identifiee","mandat_accepte_par_professionnel",
 "qualification_verifiee","competence_finances_publiques_verifiee",
 "cadre_juridique_des_services_valide",
 "verification_conflits_interets_effectuee",
 "engagement_confidentialite_effectif","contrat_signe"}
AUDIT_FLAGS={
 "document_controle_integre_et_exhaustif",
 "copie_originale_archivée_hors_depot",
 "avis_externe_independant_obtenu","evidence_confidentielle_dans_git",
 "association_ligne_montant_certifiee",
 "comparaison_avec_resultats_reels_effectuee",
 "approbation_democratique_obtenue",
 "publication_autorisee","fusion_autorisee","adoption_autorisee"}
EXPECTED_C={"C%02d"%n for n in range(1,13)}
EXPECTED_L={"L%02d"%n for n in range(1,9)}

def need(cond,reason):
 if not cond:raise ValueError(reason)
def read(path):
 p=Path(path)
 need(p.is_file() and not p.is_symlink() and
      0<p.stat().st_size<=500000,"DOCUMENT_JSON_MANQUANT_OU_TROP_GRAND")
 o=json.loads(p.read_text(encoding="utf-8"))
 need(type(o) is dict,"JSON_OBJET_REQUIS")
 return o

def verify(d):
 need(type(d) is dict and set(d)==set(FILES),"SEPT_REGISTRES_ATTENDUS")
 m,a,n,q,u,j,s=(d[x] for x in FILES)
 need(m.get("schema_version")=="P52V-1" and m.get("jalon")=="P52V" and
      m.get("date_reference")=="2026-10-20" and
      m.get("statut")=="DOSSIER_TRANSMISSIBLE_POUR_CANDIDATURE_SANS_MANDAT" and
      m.get("periode_budget")=="2026-2027" and
      m.get("unite")=="M_CAD" and m.get("preuve")=="F09",
      "MISSION_P52V_SCHEMA_INVALIDE")
 need(m.get("references")=={
      key:str(FILES[key].relative_to(ROOT)) for key in FILES if key!="mission"},
      "CHAINAGE_REFERENCES_INCOMPLET")
 need(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
      a.get("automatic_go") is False and
      a.get("financial_model_certified") is False and
      a.get("rates_selected") is False and
      a.get("human_reviews_received") is False and
      [x.get("id") for x in a.get("required_evidence",[])]==
         [f"F{i:02d}" for i in range(1,21)] and
      all(x.get("statut")=="NON_VALIDE" and
          x.get("preuve_independante_obtenue") is False and
          x.get("decision_autorisee") is False
          for x in a["required_evidence"]),
      "P52A_FAUSSE_VALIDATION")
 need(n.get("schema_version")=="P52N-1" and
      n.get("controles_transversaux",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
      n["controles_transversaux"].get("contrat_ou_depense_non_engage") is True and
      len(n.get("mandats",[]))==20,"P52N_INCOHERENT")
 mandate=next((x for x in n["mandats"] if x.get("id")=="F09"),None)
 need(mandate is not None and mandate.get("statut")=="MANDAT_NON_LANCE" and
      mandate.get("responsable_fonctionnel")=="Comptable finances publiques" and
      mandate.get("expert_mandate") is False and
      mandate.get("avis_externe_signe") is False and
      mandate.get("livrable_recu") is False and
      mandate.get("budget_mandat_chiffre") is None and
      mandate.get("cout_reel") is None,"P52N_FAUX_MANDAT")
 need(q.get("schema_version")=="P52Q-1" and
      q.get("gouvernance",{}).get("decision")=="NO_GO_AUTOMATIQUE",
      "P52Q_DECISION_NON_ETABLIE")
 q09=next((x for x in q.get("dossiers",[]) if x.get("id")=="F09"),None)
 need(q09 is not None and q09.get("statut")==
      "DOSSIER_DOCUMENTAIRE_A_INSTRUIRE" and
      q09.get("expert_reel_mandate") is False and
      q09.get("avis_favorable_recu") is False and
      q09.get("decision_adoption_autorisee") is False,
      "P52Q_FAUSSE_EXPERTISE")
 need(u.get("schema_version")=="P52U-1" and
      u.get("decision")=="NO_GO_AUTOMATIQUE" and
      u.get("relecture_humaine",{}).get("statut")=="A_MANDATER" and
      u["relecture_humaine"].get("avis_independant_signe") is False and
      u["relecture_humaine"].get("mandat_reel_verifie") is False,
      "P52U_FAUSSE_SIGNATURE")
 need(j.get("schema_version")=="P52J-1" and
      j.get("validation_de_nature",{}).get("preuve_F09_independamment_attestee") is False and
      j["validation_de_nature"].get("decision")=="NO_GO_AUTOMATIQUE",
      "P52J_FAUSSE_SIGNATURE")
 need(s.get("schema_version")=="P52S-RECU-1" and
      s.get("run_id")==39491881661 and
      s.get("gouvernance",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
      len(s.get("sources",[]))==2,
      "P52S_RECEPISSES_MANQUANTS")
 ref=m.get("references_officielles_a_consulter")
 need(type(ref) is list and len(ref)==3 and
      [x.get("type") for x in ref]==[
        "PUBLICATION_MINISTERE","ASSEMBLEE_NATIONALE","ORDRE_PROFESSIONNEL"] and
      [x.get("url") for x in ref]==list(URLS) and
      [x.get("verification_edition_sous_mandat",x.get("verification_candidat_effectuee"))
       for x in ref]==[False,False,False],
      "REFERENCES_PUBLIQUES_FICTIVEMENT_VERIFIEES")
 review=m.get("points_de_relecture")
 need(type(review) is list and len(review)==39,
      "TRENTE_NEUF_POSITIONS_REQUISES")
 source_docs=u.get("documents")
 need(type(source_docs) is list and len(source_docs)==2 and
      [x.get("id") for x in source_docs]==[
        "DISC2026_T3","PLAN2026_F2"],"DOCUMENTS_P52U_INATTENDUS")
 expected=[]
 for i,document in enumerate(source_docs):
  need(document.get("taille_attendue_octets")==s["sources"][i].get("taille_octets") and
       document.get("sha256_attendu_octets_recus")==
          s["sources"][i].get("sha256_octets_recus") and
       len(document.get("valeurs_attendues",[]))==[29,10][i],
       "P52U_VERS_P52S_INCOHERENT")
  for jx,line in enumerate(document["valeurs_attendues"]):
   expected.append({
    "position":("DISC" if i==0 else "PLAN")+"-%02d"%(jx+1),
    "source_id":document["id"],
    "page_tableau_pdf_zero":document["page_tableau_pdf_zero"],
    "page_imprimee":"27" if i==0 else "F.9",
    "unite":"M_CAD",
    "identifiant_ligne_P52J":line["id"],
    "valeur_attendue_lecture_non_certifiee":line["valeur_mcad"],
    "resultat_extraction_automatisee_P52U":
       "PRESENT_SUR_PAGE_SANS_ASSOCIATION_LIGNE_ATTESTEE",
    "statut_relecture_humaine":"NON_EXAMINE",
    "montant_confirme_par_expert":None,
    "divergence_documentee":None,
    "reference_d_avis_avec_acces_restreint":None,
    "signature_humaine_authentifiee":False
   })
 for actual,exp in zip(review,expected):
  need(type(actual) is dict and set(actual)==KEYS and actual==exp,
       "LIGNE_P52V_ALTÉRÉE_OU_VALIDEE_SANS_SIGNATURE")
 need([x["identifiant_ligne_P52J"] for x in review[:21]]==
      [x["id"] for x in j["transcription_discours_tableau3"]["lignes_revenus"]] and
      [x["identifiant_ligne_P52J"] for x in review[21:29]]==
      list(j["transcription_discours_tableau3"]["sous_totaux_officiels_mcad"]) and
      [x["identifiant_ligne_P52J"] for x in review[29:]]==
      list(j["transcription_plan_budgetaire_f2"]["montants_signes_comme_affiches_mcad"]),
      "P52V_TRACABILITE_P52J_INVALID")
 common=(("revenus_autonomes","134361"),
         ("transferts_federaux","32131"),("revenus_totaux","166492"))
 for label,val in common:
  need(sum(x["identifiant_ligne_P52J"]==label and
           x["valeur_attendue_lecture_non_certifiee"]==val
           for x in review)==2,"CROISEMENT_DES_TABLEAUX_FALSIFIE")
 checks=m.get("controles_contradictoires")
 need(type(checks) is list and len(checks)==12 and
      {x.get("id") for x in checks}==EXPECTED_C and
      [x["id"] for x in checks]==sorted(EXPECTED_C) and
      all(x.get("statut")=="NON_EXECUTE_HUMAIN" and
          type(x.get("objet")) is str and len(x["objet"])>30
          for x in checks),"DOUZE_CONTROLES_HUMAINS_REQUIS")
 for id_,amount in (("C03","134361"),("C04","32131"),("C05","166492")):
  one=next(x for x in checks if x["id"]==id_)
  need(one.get("montant_reperage")==amount and
       one.get("type")=="INTER_TABLEAUX","TROIS_CROISEMENTS_INEXACTS")
 deliverables=m.get("livrables_au_mandat")
 need(type(deliverables) is list and len(deliverables)==8 and
      {x.get("id") for x in deliverables}==EXPECTED_L and
      all(x.get("etat")=="NON_RECU" and
          x.get("preuve_documentaire_externe") is None and
          x.get("controle_d_authenticite") is False and
          type(x.get("objet")) is str and len(x["objet"])>20
          for x in deliverables),"HUIT_LIVRABLES_NON_RECUS_ATTENDUS")
 select=m.get("selection_candidat")
 need(type(select) is dict and
      select.get("statut")=="NON_LANCE" and
      set(k for k,v in select.items() if k in SELECT_BOOL)==SELECT_BOOL and
      all(select[k] is False for k in SELECT_BOOL) and
      select.get("nom_candidat") is None and
      select.get("devis_reels_recus")==0 and
      select.get("budget_mandat_autorise_cad") is None and
      type(select.get("fonds_engages_cad")) is int and
      select.get("fonds_engages_cad")==0,"CANDIDAT_OU_DEPENSE_FICTIFS")
 audit=m.get("audit_et_protection")
 need(type(audit) is dict and
      set(audit)==AUDIT_FLAGS|{"decision"} and
      all(audit[x] is False for x in AUDIT_FLAGS) and
      audit.get("decision")=="NO_GO_AUTOMATIQUE","GO_OU_REVUE_FICTIVE")
 stats=m.get("bilan")
 need(type(stats) is dict and
      stats.get("positions_a_revoir")==39 and
      stats.get("positions_discours")==29 and stats.get("positions_plan")==10 and
      stats.get("correspondances_inter_documents_a_revoir")==3 and
      stats.get("controles_humains_en_attente")==12 and
      stats.get("livrables_professionnels_en_attente")==8 and
      stats.get("points_confirmes_par_humain")==0 and
      stats.get("expertises_independantes_signees")==0 and
      stats.get("preuves_F01_F20_encore_non_validees")==20 and
      stats.get("valeurs_financieres_nova_encore_inconnues")==1320 and
      stats.get("decision")=="NO_GO_AUTOMATIQUE",
      "BILAN_FAUSSE_CLOTURE")
 return {
  "jalon":"P52V","schema_version":"P52V-1",
  "positions_de_relecture_pret_a_transmettre":39,
  "positions_discours":29,"positions_plan":10,
  "croisements_inter_tableaux_a_verifier":3,
  "controles_humains_non_executes":12,
  "livrables_experts_non_recus":8,
  "candidats_identifies_et_verifies":0,
  "avis_humains_reellement_signes":0,
  "preuves_F01_F20_non_validees":20,
  "donnees_financieres_inconnues":1320,
  "publication_autorisee":False,
  "fusion_autorisee":False,
  "adoption_autorisee":False,
  "decision":"NO_GO_AUTOMATIQUE"
 }

def csv_rows(d):
 m=d["mission"]
 lines=[["position","source_id","page_imprimee","libelle_interne_p52j",
         "valeur_attendue_M_CAD_non_certifiee","valeur_relue_par_expert",
         "libelle_officiel_verifie","verdict_humain","reserve_et_page_justificative",
         "piece_archivee_reference_restraint"]]
 for r in m["points_de_relecture"]:
  lines.append([r["position"],r["source_id"],r["page_imprimee"],
                r["identifiant_ligne_P52J"],
                r["valeur_attendue_lecture_non_certifiee"],
                "","","","",""])
 buff=io.StringIO(newline="")
 writer=csv.writer(buff,lineterminator="\n")
 writer.writerows(lines)
 return buff.getvalue()

def save_new(path,content):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as out:out.write(content)

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 for key,path in FILES.items():p.add_argument("--"+key,type=Path,default=path)
 p.add_argument("--rapport",type=Path)
 p.add_argument("--export-csv",type=Path)
 p.add_argument("--exiger-expertise",action="store_true")
 args=p.parse_args(argv)
 try:
  d={k:read(getattr(args,k)) for k in FILES}
  result=verify(d)
  out=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
  # Valider AVANT l'export pour ne jamais produire un CSV issu d'une fausse approbation.
  if args.rapport and args.export_csv:
   need(args.rapport.resolve()!=args.export_csv.resolve(),
        "RAPPORT_ET_CSV_MEME_CHEMIN")
  if args.rapport:
   save_new(args.rapport,out)
  if args.export_csv:
   save_new(args.export_csv,csv_rows(d))
  if not args.rapport and not args.export_csv:print(out,end="")
  return 3 if args.exiger_expertise else 0
 except (OSError,ValueError,KeyError,TypeError,UnicodeError) as exc:
  result={"jalon":"P52V","etat":"REJET_TECHNIQUE",
          "categorie_erreur":type(exc).__name__,
          "publication_autorisee":False,"fusion_autorisee":False,
          "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"}
  print(json.dumps(result,ensure_ascii=False,indent=2))
  return 2

if __name__=="__main__":
 sys.exit(main())
