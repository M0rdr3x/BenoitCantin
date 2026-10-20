#!/usr/bin/env python3
"""P52Y: transfert vers autorités réelles sans attribution, approbation ni merge."""
import argparse
import csv
import io
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "plan":D/"P52Y_PLAN_ACTIONS_HUMAINES_ET_GITHUB.json",
 "journal":D/"P52Y_JOURNAL_DECISIONS_VIDE.json",
 "p52x":D/"P52X_PRECONDITIONS_AUTORITE_ET_CONFIDENTIALITE.json",
 "p52w":D/"P52W_MATRICE_SELECTION_ET_GARDES_F09.json",
 "p52v":D/"P52V_REGISTRE_MISSION_F09.json",
 "p52n":D/"P52N_CAHIER_MANDATS_ET_CONSULTATION.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
ACTIONS={
 "A01":("MANDAT",1,[],"X01 X03"),
 "A02":("MANDAT",1,["A01"],"X02 X07"),
 "A03":("MANDAT",2,["A01","A02"],"X04"),
 "A04":("MANDAT",2,["A02","A03"],"X05 X06"),
 "A05":("MANDAT",2,["A02","A03"],"X09 X10 X11"),
 "A06":("MANDAT",3,["A03","A04","A05"],"X08 X12"),
 "A07":("GITHUB",1,[],""),
 "A08":("GITHUB",2,["A07"],""),
 "A09":("MANDAT",4,["A01","A02","A03","A04","A05","A06"],""),
 "A10":("MANDAT",5,["A09"],"")
}
DECISIONS={
 "D01":("STATUT_ET_POUVOIRS",["A01","A02","A03"]),
 "D02":("FINANCEMENT",["A04"]),
 "D03":("DONNEES_ET_SELECTION",["A05","A06","A09"]),
 "D04":("GITHUB_ET_REVUE",["A07","A08"]),
}
ACTION_FIELDS={
 "id","piste","objet","role_fonctionnel_requis","preconditions_p52x",
 "dependances","phase","priorite","statut","responsable_reel_designe",
 "piece_officielle_verifiee","preuve_confidentielle_stockee_hors_git",
 "date_validation_externe","signature_humaine_authentifiee"
}
DECISION_FIELDS={
 "id","theme","objet","actions_requises","decision_authentifiee",
 "reference_piece_confidentielle","date_decision_verifiee",
 "autorite_reelle_identifiee","statut"
}
NONDELEGABLE={
 "instance_mandante_legalement_qualifiee":False,
 "delegation_ecrite_authentifiee":False,
 "budget_cad_veritablement_accorde":None,
 "responsable_protection_donnees_designe":False,
 "canal_protege_existant":False,
 "candidatures_confidentielles_reellement_recues":0,
 "contrat_effectif_signe":False,
 "main_protegee_via_github":False,
 "minimum_une_revue_reelle_requise_et_obtenue":False,
 "f09_avis_professionnel_independant_signe":False,
 "aucun_autorisation_par_execution_CI":True,
 "aucune_ecriture_github_par_workflow":True,
 "aucun_document_personnel_dans_depot":True
}
JOURNAL_EMPTY={"evenements","decisions_humaines","relectures_github","depenses"}
NO_GO_FIELDS={"fusion_autorisee","publication_autorisee","adoption_autorisee"}

def require(test,reason):
 if not test:raise ValueError(reason)

def read(path):
 p=Path(path)
 require(p.is_file() and not p.is_symlink() and
         0<p.stat().st_size<=500000,"SOURCE_JSON_ABSENTE_OU_TROP_GRANDE")
 data=json.loads(p.read_text(encoding="utf-8"))
 require(type(data) is dict,"JSON_OBJET_ATTENDU")
 return data

def validate(docs):
 require(type(docs) is dict and set(docs)==set(FILES),
         "SEPT_REFERENCES_REQUISES")
 m,j,x,w,v,n,a=(docs[k] for k in FILES)
 require(m.get("schema_version")=="P52Y-1" and
         m.get("jalon")=="P52Y" and m.get("date_reference")=="2026-10-20" and
         m.get("statut")==
            "DOSSIER_DECISIONS_HUMAINES_PRET_A_INSTRUIRE_NON_APPROUVE",
         "P52Y_MATRICE_INVALIDE")
 require(m.get("references")=={
   key:str(FILES[key].relative_to(ROOT)) for key in FILES if key!="plan"
 },"SOURCE_LINK_NON_CONFORME")
 require(x.get("schema_version")=="P52X-1" and
         x.get("decision_precontractuelle",{}).get("decision")==
            "NO_GO_AUTOMATIQUE" and
         x["decision_precontractuelle"].get("budget_total_autorise_cad") is None and
         x["decision_precontractuelle"].get("mandant_legal_identifie") is False and
         x["decision_precontractuelle"].get("delegation_signature_authentifiee") is False and
         x["decision_precontractuelle"].get("canal_confidentiel_active") is False and
         len(x.get("preconditions",[]))==12 and
         [z.get("id") for z in x["preconditions"]]==[
            "X%02d"%i for i in range(1,13)] and
         all(z.get("etat")=="NON_DOCUMENTE" and
             z.get("decision_humaine_authentifiee") is False
             for z in x["preconditions"]),
         "P52X_AUTORISATIONS_FICTIVES")
 require(w.get("schema_version")=="P52W-1" and
         w.get("garde",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
         w["garde"].get("candidats_reels_recus")==0 and
         w["garde"].get("fonds_engages_cad")==0 and
         w.get("parametres_non_adoptes",{}).get("criteres_adoptes") is False and
         len(w.get("conditions",[]))==12 and
         all(z.get("statut")=="NON_VERIFIE" and
             z.get("verification_humaine") is False for z in w["conditions"]),
         "P52W_NON_VERIFIE_REQUIS")
 require(v.get("schema_version")=="P52V-1" and
         v.get("bilan",{}).get("positions_a_revoir")==39 and
         v.get("selection_candidat",{}).get("statut")=="NON_LANCE" and
         v["selection_candidat"].get("contrat_signe") is False and
         v["audit_et_protection"].get("decision")=="NO_GO_AUTOMATIQUE",
         "P52V_EXPERT_FICTIF")
 require(n.get("schema_version")=="P52N-1" and
         n.get("controles_transversaux",{}).get("contrat_ou_depense_non_engage") is True and
         n["controles_transversaux"].get("decision")=="NO_GO_AUTOMATIQUE",
         "P52N_FAUX_MANDAT")
 require(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
         a.get("automatic_go") is False and
         a.get("financial_model_certified") is False and
         a.get("human_reviews_received") is False and
         [z.get("id") for z in a.get("required_evidence",[])]==
            ["F%02d"%i for i in range(1,21)] and
         all(z.get("statut")=="NON_VALIDE" and
             z.get("preuve_independante_obtenue") is False
             for z in a["required_evidence"]),
         "P52A_NON_VALIDEE_ATTENDUE")
 require(j.get("schema_version")=="P52Y-JOURNAL-1" and
         j.get("jalon")=="P52Y" and
         j.get("statut")=="AUCUN_ACTE_AUTHENTIFIE" and
         all(j.get(k)==[] for k in JOURNAL_EMPTY) and
         j.get("identites_et_pieces_privees_enregistrees_dans_git") is False and
         j.get("signatures_reelles_authentifiees")==0 and
         j.get("actions_autorisees")==0 and
         all(j.get(k) is False for k in NO_GO_FIELDS) and
         j.get("decision")=="NO_GO_AUTOMATIQUE",
         "P52Y_JOURNAL_FICTIF")
 gh=m.get("github_snapshot",{})
 require(type(gh) is dict and
         gh.get("repository")=="M0rdr3x/BenoitCantin" and
         gh.get("date_constat")=="2026-10-20" and
         gh.get("main_sha")=="9ed5f70cbe7022f25a679346a1288701f3b09067" and
         gh.get("main_protegee") is False and
         type(gh.get("rulesets_nombre")) is int and gh["rulesets_nombre"]==0 and
         gh.get("pr_numero")==673 and
         gh.get("pr_branche")=="review/p52a-deux-regimes-fiscalite-transition-2026-10-18" and
         gh.get("pr_brouillon") is True and
         gh.get("pr_fusionnee") is False and
         gh.get("pr_relectures_humaines")==0 and
         gh.get("statut")=="CAPTURE_PONCTUELLE_NON_ATTESTATION_FUTURE" and
         gh.get("revalidation_live_apres_configuration_requise") is True and
         gh.get("issue_securite")=={
            "numero":135,"etat":"open",
            "url":"https://github.com/M0rdr3x/BenoitCantin/issues/135"} and
         gh.get("issue_relectures")=={
            "numero":662,"etat":"open",
            "url":"https://github.com/M0rdr3x/BenoitCantin/issues/662"},
         "GITHUB_SNAPSHOT_A_CONTROLER_PAR_ADMIN")
 actions=m.get("actions")
 require(type(actions) is list and len(actions)==10 and
         [z.get("id") for z in actions]==list(ACTIONS),
         "ACTIONS_ATTENDUES_A01_A10")
 for z in actions:
  piste,phase,depends,ids=ACTIONS[z["id"]]
  require(type(z) is dict and set(z)==ACTION_FIELDS and
          z.get("piste")==piste and
          type(z.get("phase")) is int and z["phase"]==phase and
          z.get("dependances")==depends and
          z.get("preconditions_p52x")==ids.split() and
          all(i in [g["id"] for g in x["preconditions"]]
              for i in z["preconditions_p52x"]) and
          type(z.get("objet")) is str and len(z["objet"])>=45 and
          type(z.get("role_fonctionnel_requis")) is str and
          len(z["role_fonctionnel_requis"])>=15 and
          z.get("priorite")=="BLOQUANT" and
          z.get("statut")=="ATTENTE_AUTORITE_HUMAINE" and
          z.get("responsable_reel_designe") is False and
          z.get("piece_officielle_verifiee") is False and
          z.get("preuve_confidentielle_stockee_hors_git") is None and
          z.get("date_validation_externe") is None and
          z.get("signature_humaine_authentifiee") is False,
          "ACTION_FAUSSEMENT_EXECUTEE")
  require(all(int(dep[1:])<int(z["id"][1:]) for dep in depends),
          "DEPENDANCE_CYCLIQUE")
 dec=m.get("decisions")
 require(type(dec) is list and len(dec)==4 and
         [z.get("id") for z in dec]==list(DECISIONS),
         "QUATRE_DECISIONS_ATTENDUES")
 for z in dec:
  theme,dependent=DECISIONS[z["id"]]
  require(type(z) is dict and set(z)==DECISION_FIELDS and
          z.get("theme")==theme and z.get("actions_requises")==dependent and
          all(i in ACTIONS for i in dependent) and
          type(z.get("objet")) is str and len(z["objet"])>45 and
          z.get("statut")=="NON_PRESENTE_A_DECIDEUR" and
          z.get("decision_authentifiee") is False and
          z.get("reference_piece_confidentielle") is None and
          z.get("date_decision_verifiee") is None and
          z.get("autorite_reelle_identifiee") is False,
          "DECISION_FICTIVE")
 require(m.get("points_non_delegables")==NONDELEGABLE,
         "GARDES_REELLES_MANQUANTES")
 bil=m.get("bilan",{})
 require(type(bil) is dict and
         bil.get("actions_total")==10 and
         bil.get("actions_humaines_non_executees")==10 and
         bil.get("actions_mandat_non_executees")==8 and
         bil.get("actions_github_non_executees")==2 and
         bil.get("decisions_humaines_non_presentees")==4 and
         bil.get("preconditions_p52x_toujours_non_documentees")==12 and
         bil.get("preuves_fiscales_independantes_F01_F20_obtenues")==0 and
         bil.get("valeurs_financieres_nova_inconnues")==1320 and
         bil.get("contrats_signes")==0 and
         bil.get("montant_engage_cad")==0 and
         all(bil.get(k) is False for k in NO_GO_FIELDS) and
         bil.get("decision")=="NO_GO_AUTOMATIQUE",
         "P52Y_BILAN_FAUSSE_CONCLUSION")
 return {
    "jalon":"P52Y","schema_version":"P52Y-1",
    "actions_pretes_pour_remise_non_executees":10,
    "actions_mandat_non_executees":8,
    "actions_protection_github_non_executees":2,
    "decisions_attendues":4,
    "personnes_reellement_habilitees_identifiees":0,
    "budget_engage_cad":0,
    "expertises_F09_certifiees":0,
    "main_protegee_au_constat":False,
    "revues_humaines_PR_673_au_constat":0,
    "preuves_F01_F20_non_validees":20,
    "donnees_financieres_nova_inconnues":1320,
    "publication_autorisee":False,
    "fusion_autorisee":False,
    "adoption_autorisee":False,
    "decision":"NO_GO_AUTOMATIQUE"
 }

def simulation_fictive(data):
 require(type(data) is dict and
         set(data)=={"synthetique","code","actions_fictives"} and
         data.get("synthetique") is True and
         data.get("code")=="TEST_ORDONNANCEMENT_SEULEMENT",
         "SCENARIO_REEL_INTERDIT")
 flags=data.get("actions_fictives")
 require(type(flags) is dict and set(flags)==set(ACTIONS) and
         all(type(val) is bool for val in flags.values()),
         "DIX_ACTIONS_FICTIVES_REQUISES")
 violation=[]
 for ident,(_,phase,deps,_) in ACTIONS.items():
  if flags[ident] and any(not flags[dep] for dep in deps):
   violation.append(ident)
 return {
   "scenario_synthetique":True,
   "actions_fictivement_accomplies":sum(flags.values()),
   "actions_avec_dependances_non_satisfaites":violation,
   "aucune_habilitation_authentique":True,
   "aucun_contact_externe_autorise":True,
   "protection_main_reellement_verifiee":False,
   "budget_autorise":False,
   "contrat_autorise":False,
   "publication_autorisee":False,
   "fusion_autorisee":False,
   "adoption_autorisee":False,
   "decision":"NO_GO_AUTOMATIQUE"
 }

def blank_csv(actions):
 buf=io.StringIO(newline="")
 writer=csv.writer(buf,lineterminator="\n")
 writer.writerow([
    "action","piste","phase","fonction_necessaire_non_designee",
    "dependances","preconditions_P52X","statut_initial",
    "date_decision_humaine","reference_preuve_confidentielle_hors_git",
    "avis_legal_ou_financier","objection_ou_recusation","verificateur_distinct"])
 for row in actions:
  writer.writerow([
     row["id"],row["piste"],row["phase"],row["role_fonctionnel_requis"],
     " ".join(row["dependances"])," ".join(row["preconditions_p52x"]),
     "ATTENTE_AUTORITE_HUMAINE","","","","",""])
 return buf.getvalue()

def output_new(path,content):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as f:f.write(content)

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 for key,path in FILES.items():p.add_argument("--"+key,type=Path,default=path)
 p.add_argument("--simulation",type=Path)
 p.add_argument("--rapport",type=Path)
 p.add_argument("--export-csv",type=Path)
 p.add_argument("--exiger-autorisations",action="store_true")
 args=p.parse_args(argv)
 try:
  docs={k:read(getattr(args,k)) for k in FILES}
  report=validate(docs)
  if args.simulation:
   report["simulation"]=simulation_fictive(read(args.simulation))
  if args.rapport and args.export_csv:
   require(args.rapport.resolve()!=args.export_csv.resolve(),
           "FICHIERS_SORTIE_MEME_CHEMIN")
  if args.rapport:output_new(args.rapport,json.dumps(report,ensure_ascii=False,indent=2)+"\n")
  if args.export_csv:output_new(args.export_csv,blank_csv(docs["plan"]["actions"]))
  if not args.rapport and not args.export_csv:
   print(json.dumps(report,ensure_ascii=False,indent=2))
  return 3 if args.exiger_autorisations else 0
 except (ValueError,OSError,TypeError,UnicodeError,KeyError) as exc:
  print(json.dumps({
    "jalon":"P52Y","statut":"REJET_PREUVE_NON_AUTHENTIQUE",
    "categorie_erreur":type(exc).__name__,
    "publication_autorisee":False,"fusion_autorisee":False,
    "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"
  },ensure_ascii=False))
  return 2

if __name__=="__main__":
 sys.exit(main())
