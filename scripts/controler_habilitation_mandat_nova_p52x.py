#!/usr/bin/env python3
"""P52X - autorité et confidentialité précontractuelles F09. NO_GO permanent."""
import argparse
import csv
import io
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "plan":D/"P52X_PRECONDITIONS_AUTORITE_ET_CONFIDENTIALITE.json",
 "p52w":D/"P52W_MATRICE_SELECTION_ET_GARDES_F09.json",
 "reception_p52w":D/"P52W_REGISTRE_RECEPTION_OFFRES_VIDE.json",
 "p52v":D/"P52V_REGISTRE_MISSION_F09.json",
 "p52n":D/"P52N_CAHIER_MANDATS_ET_CONSULTATION.json",
 "p52q":D/"P52Q_DOSSIERS_INSTRUCTION_VAGUE1.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json"
}
GATES={
 "X01":("AUTORITE","G01","Identifier la personne ou entité juridique mandante, son statut et sa capacité réelle à contracter"),
 "X02":("AUTORITE","G01","Obtenir les délégations signées et la capacité de chaque signataire avant toute action"),
 "X03":("CADRE","G02","Déterminer si le mandant est privé, parti politique autorisé ou organisme public; vérifier la preuve de statut"),
 "X04":("CADRE","G02","Établir par avis juridique les règles contractuelles et électorales applicables, sans seuil présumé"),
 "X05":("FINANCES","G03","Déterminer la source licite et le contrôle comptable des fonds susceptibles de financer F09"),
 "X06":("FINANCES","G03","Faire approuver un plafond réel chiffré, l'imputation et l'interdiction de dépense non autorisée"),
 "X07":("GOUVERNANCE","G12","Désigner les personnes responsables de l'analyse, de la décision et du contrôle, fonctions distinctes"),
 "X08":("GOUVERNANCE","G04","Faire adopter les critères P52W avant d'évaluer ou contacter des candidats"),
 "X09":("VIE_PRIVEE","G09","Qualifier la collecte de renseignements des professionnels et le régime de protection applicable"),
 "X10":("VIE_PRIVEE","G09","Déterminer un canal privé sécurisé, l'information aux candidats, les accès et la durée de conservation"),
 "X11":("VIE_PRIVEE","G09","Évaluer les transferts ou accès hors Québec si pertinents et choisir les mesures nécessaires"),
 "X12":("RECOURS","G11","Prévoir recusation, réserves, traitement des plaintes et conservation des décisions motivées")
}
SOURCES=(
 ("ELECTORAL","https://www.electionsquebec.qc.ca/comprendre/comprendre-le-financement-politique/obtenir-le-droit-de-collecter-des-contributions-ou-de-faire-des-depenses/","verification_statut_effectuee"),
 ("LCOP","https://www.legisquebec.gouv.qc.ca/fr/document/lc/c-65.1","verification_applicabilite_effectuee"),
 ("CAI_PARTIS","https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-pour-partis-politiques-provinciaux","verification_applicabilite_effectuee"),
 ("PRIVE","https://www.legisquebec.gouv.qc.ca/fr/document/lc/p-39.1","verification_applicabilite_effectuee")
)
PATHWAYS=(
 "PROJET_SANS_ENTITE_VERIFIEE","PARTI_QUEBEC_AUTORISE",
 "ORGANISME_PUBLIC_QUEBEC","ENTITE_PRIVEE_AUTRE"
)
PRIVATE_FLAGS={
 "canal_de_reception_operationnel":False,
 "fournisseur_d_hebergement_selectionne":False,
 "localisation_donnees_verifiee":False,
 "avis_confidentialite_approuve":False,
 "mesures_de_controle_acces_approuvees":False,
 "duree_conservation_validee":False,
 "plan_effacement_valide":False,
 "evaluation_facteurs_vie_privee_realisee_si_requise":False,
 "aucune_collecte_reelle_en_cours":True,
 "aucun_candidat_nominal_sur_github":True,
 "aucune_donnee_personnelle_dans_ci":True,
 "aucun_seuil_reglementaire_invente":True
}
LEGAL_FALSE={
 "mandant_legal_identifie","statut_electoral_ou_juridique_verifie",
 "regime_achats_documente","delegation_signature_authentifiee",
 "responsable_financier_nomme","responsable_vie_privee_nomme",
 "approbateur_distinct_nomme","conflits_interets_verifies",
 "invitation_envoyee","canal_confidentiel_active","contrat_signe",
 "relecteur_humain_mandate","preuve_F09_certifiee",
 "publication_autorisee","fusion_autorisee","adoption_autorisee"
}
TRUE_PATH_TYPES={"hypothese_juridique","preconditions_fictives","synthetique","marqueur"}

def require(ok,code):
 if not ok:raise ValueError(code)

def read(path):
 p=Path(path)
 require(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=500000,
         "DOCUMENT_REFERENCE_MANQUANT")
 obj=json.loads(p.read_text(encoding="utf-8"))
 require(type(obj) is dict,"OBJET_JSON_REQUIS")
 return obj

def validate(documents):
 require(type(documents) is dict and set(documents)==set(FILES),
         "SEPT_REFERENCES_ATTENDUES")
 m,w,r,v,n,q,a=(documents[x] for x in FILES)
 require(m.get("schema_version")=="P52X-1" and m.get("jalon")=="P52X" and
         m.get("date_reference")=="2026-10-20" and
         m.get("statut")=="AUTORITE_NON_QUALIFIEE_AUCUN_FINANCEMENT_AUTORISE" and
         m.get("preuve_visee")=="F09","PROJET_DE_MANDAT_INVALIDE")
 require(m.get("references")=={
   key:str(FILES[key].relative_to(ROOT)) for key in FILES if key!="plan"
 },"CHEMIN_PREUVE_INCOMPATIBLE")
 require(w.get("schema_version")=="P52W-1" and
         w.get("statut")=="PROCEDURE_PROPOSEE_NON_ADOPTEE_SANS_OFFRE" and
         w.get("garde",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
         w.get("parametres_non_adoptes",{}).get("organisme_mandant_legalement_identifie") is False and
         w["parametres_non_adoptes"].get("regime_contractuel_valide") is False and
         w["parametres_non_adoptes"].get("criteres_adoptes") is False and
         w["garde"].get("candidats_reels_recus")==0 and
         w["garde"].get("fonds_engages_cad")==0 and
         len(w.get("conditions",[]))==12,"P52W_FAUSSE_AUTORISATION")
 for row in w["conditions"]:
  require(row.get("statut")=="NON_VERIFIE" and
          row.get("verification_humaine") is False and
          row.get("reference_preuve_privee") is None,
          "GATE_P52W_PAS_ATTENTE")
 require(r.get("schema_version")=="P52W-RECEPTION-1" and
         r.get("offres")==[] and r.get("evenements")==[] and
         r.get("decision")=="NO_GO_AUTOMATIQUE","RECEPTION_VIDE_REQUISE")
 require(v.get("schema_version")=="P52V-1" and
         v.get("bilan",{}).get("positions_a_revoir")==39 and
         v.get("selection_candidat",{}).get("statut")=="NON_LANCE" and
         v["selection_candidat"].get("contrat_signe") is False and
         v["selection_candidat"].get("budget_mandat_autorise_cad") is None and
         v["audit_et_protection"].get("decision")=="NO_GO_AUTOMATIQUE",
         "P52V_AVIS_NON_RECU")
 require(n.get("schema_version")=="P52N-1" and
         n.get("controles_transversaux",{}).get("contrat_ou_depense_non_engage") is True and
         n["controles_transversaux"].get("decision")=="NO_GO_AUTOMATIQUE",
         "P52N_MANDAT_FICTIF")
 require(q.get("schema_version")=="P52Q-1" and
         q.get("gouvernance",{}).get("decision")=="NO_GO_AUTOMATIQUE",
         "P52Q_AVIS_FICTIF")
 require(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
         a.get("automatic_go") is False and
         a.get("human_reviews_received") is False and
         a.get("financial_model_certified") is False and
         [z.get("id") for z in a.get("required_evidence",[])]==
            [f"F{i:02d}" for i in range(1,21)] and
         all(z.get("statut")=="NON_VALIDE" and
             z.get("preuve_independante_obtenue") is False
             for z in a["required_evidence"]),
         "P52A_PREUVES_A_CONSERVER")
 src=m.get("sources_officielles_a_verifier")
 require(type(src) is list and len(src)==4,"QUATRE_SOURCES_OFFICIELLES")
 for i,entry in enumerate(src):
  name,url,flag=SOURCES[i]
  require(entry.get("id")==name and entry.get("url")==url and
          entry.get(flag) is False and type(entry.get("usage")) is str and
          len(entry["usage"])>50,"SOURCE_NON_CONFIRME")
 choices=m.get("hypotheses_statut_mandant")
 require(type(choices) is list and len(choices)==4 and
         [x.get("code") for x in choices]==list(PATHWAYS) and
         all(x.get("retenue_juridiquement") is False and
             type(x.get("description")) is str and len(x["description"])>40
             for x in choices),"STATUT_JURIDIQUE_INVENTE")
 conditions=m.get("preconditions")
 require(type(conditions) is list and len(conditions)==12 and
         [x.get("id") for x in conditions]==list(GATES),
         "DOUZE_PRECONDITIONS_A_DOCUMENTER")
 for gate in conditions:
  group,linked,question=GATES[gate["id"]]
  require(set(gate)=={
    "id","domaine","question","correspondance_p52w","etat",
    "decision_humaine_authentifiee","autorite_verifiee",
    "reference_piece_confidentielle","conflit_declare_et_resolu"} and
    gate["domaine"]==group and gate["correspondance_p52w"]==linked and
    gate["question"]==question and
    gate["etat"]=="NON_DOCUMENTE" and
    gate["decision_humaine_authentifiee"] is False and
    gate["autorite_verifiee"] is False and
    gate["reference_piece_confidentielle"] is None and
    gate["conflit_declare_et_resolu"] is False,
    "CONDITION_PRETENDUMENT_REMPLIE")
 require(set(g["correspondance_p52w"] for g in conditions) <=
         set(x["id"] for x in w["conditions"]),
         "CORRESPONDANCES_G_MISSING")
 privacy=m.get("securite_reception")
 require(type(privacy) is dict and privacy==PRIVATE_FLAGS,
         "PROTECTION_CANDIDATURES_NON_CONFORME")
 dec=m.get("decision_precontractuelle",{})
 require(type(dec) is dict and dec.get("statut")=="NON_SOUMISE_A_UNE_AUTORITE" and
         dec.get("budget_total_autorise_cad") is None and
         type(dec.get("fonds_engages_cad")) is int and
         dec["fonds_engages_cad"]==0 and
         all(dec.get(x) is False for x in LEGAL_FALSE) and
         dec.get("decision")=="NO_GO_AUTOMATIQUE",
         "AUTORISATION_PRECONTRACTUELLE_FICTIVE")
 report=m.get("bilan",{})
 require(type(report) is dict and
         report.get("preconditions_a_documenter")==12 and
         report.get("hypotheses_juridiques_non_determines")==4 and
         all(type(report.get(x)) is int and report[x]==0 for x in (
           "consultations_professionnelles_reelles","candidatures_reelles",
           "contrats_signes","depenses_effectives_cad")) and
         report.get("preuves_f01_f20_non_validees")==20 and
         report.get("valeurs_nova_inconnues")==1320 and
         report.get("decision")=="NO_GO_AUTOMATIQUE",
         "FAUX_BILAN_FINANCIER")
 return {
    "jalon":"P52X","schema_version":"P52X-1",
    "preconditions_sans_decision_humaine":12,
    "regimes_non_qualifies":4,
    "gates_p52w_restes_non_verifies":12,
    "mandats_f09_actifs":0,
    "candidatures_recues":0,
    "canaux_confidentiels_actifs":0,
    "budget_autorise":False,
    "fonds_engages_cad":0,
    "expertises_F09_independantes_obtenues":0,
    "preuves_f01_f20_non_validees":20,
    "variables_financieres_nova_inconnues":1320,
    "publication_autorisee":False,"fusion_autorisee":False,
    "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"
 }

def scenario_fictif(s):
 require(type(s) is dict and set(s)==TRUE_PATH_TYPES and
         s.get("synthetique") is True and
         s.get("marqueur")=="TEST_HYPOTHETIQUE_SANS_IDENTITE",
         "PERSONNE_REELLE_INTERDITE_DANS_SIMULATION")
 require(s.get("hypothese_juridique") in PATHWAYS,
         "REGIME_SIMULE_INCONNU")
 marks=s.get("preconditions_fictives")
 require(type(marks) is dict and set(marks)==set(GATES) and
         all(type(x) is bool for x in marks.values()),
         "DOUZE_PRECONDITIONS_FICTIVES_REQUISES")
 return {
    "jalon":"P52X","scenario_purement_hypothetique":True,
    "hypothese_choisie_sans_validation":s["hypothese_juridique"],
    "preconditions_fictivement_positives":sum(marks.values()),
    "inadmissibilite_simulee":not all(marks.values()),
    "besoin_de_validation_juridique_et_humaine":True,
    "decision_contractuelle_reelle":False,
    "sollicitation_autorisee":False,
    "budget_autorise":False,
    "adoption_autorisee":False,
    "decision":"NO_GO_AUTOMATIQUE"
 }

def blank_csv(m):
 lines=[["controle","domaine","condition","garde_p52w",
         "statut_initial","decision_par_autorite","piece_confidentielle_hors_git",
         "validation_juridique","controleur_distinct","reserve_et_suite"]]
 for x in m["preconditions"]:
  lines.append([x["id"],x["domaine"],x["question"],
                x["correspondance_p52w"],"NON_DOCUMENTE","","","","",""])
 out=io.StringIO(newline="")
 csv.writer(out,lineterminator="\n").writerows(lines)
 return out.getvalue()

def save_new(path,content):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as f:f.write(content)

def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__)
 for name,path in FILES.items():ap.add_argument("--"+name,type=Path,default=path)
 ap.add_argument("--simulation",type=Path)
 ap.add_argument("--rapport",type=Path)
 ap.add_argument("--export-csv",type=Path)
 ap.add_argument("--exiger-habilitation",action="store_true")
 args=ap.parse_args(argv)
 try:
  docs={k:read(getattr(args,k)) for k in FILES}
  summary=validate(docs)
  if args.simulation:summary["hypothese_synthetique"]=scenario_fictif(read(args.simulation))
  if args.rapport and args.export_csv:
   require(args.rapport.resolve()!=args.export_csv.resolve(),
           "RAPPORT_ET_CSV_IDENTIQUES")
  if args.rapport:save_new(args.rapport,json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
  if args.export_csv:save_new(args.export_csv,blank_csv(docs["plan"]))
  if not args.rapport and not args.export_csv:
   print(json.dumps(summary,ensure_ascii=False,indent=2))
  return 3 if args.exiger_habilitation else 0
 except (OSError,ValueError,UnicodeError,TypeError,KeyError) as ex:
  print(json.dumps({
    "jalon":"P52X","statut":"DOCUMENT_OU_HABILITATION_REJETE",
    "categorie_erreur":type(ex).__name__,"publication_autorisee":False,
    "fusion_autorisee":False,"adoption_autorisee":False,
    "decision":"NO_GO_AUTOMATIQUE"},ensure_ascii=False))
  return 2
if __name__=="__main__":
 sys.exit(main())
