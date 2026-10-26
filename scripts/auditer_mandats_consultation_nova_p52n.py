#!/usr/bin/env python3
"""Projet Nova P52N : appels et consultation en simulation non nominative, jamais un GO."""
import argparse
from pathlib import Path
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "mandats":BASE/"P52N_CAHIER_MANDATS_ET_CONSULTATION.json",
 "simulation":BASE/"P52N_JOURNAL_SIMULATIONS_VIDE.json",
 "p52a":BASE/"P52A_REGISTRE_PREUVES_FISCALES.json",
 "p52m":BASE/"P52M_MANDATS_COMITES_ET_RISQUES.json",
 "p52l":BASE/"P52L_MATRICE_REVUES_INDEPENDANTES.json"
}
CRITERIA=["COMPETENCE_ET_INDEPENDANCE","METHODE_ET_REPRODUCTIBILITE",
 "QUALITE_DES_SOURCES","TRAITEMENT_DES_RISQUES","TRANSPARENCE_ET_RECOURS"]
MUST_ANNEX=[
 "origine_version_date_et_perimetre_des_sources",
 "methodologie_hypotheses_limites_et_reproductibilite",
 "risques_droits_et_effets_defavorables",
 "examen_contradictoire_et_reserves","examen_juridictionnel_du_regime",
 "version_expurgee_destinee_a_consultation_si_autorisee"
]
REF=re.compile(r"SIM-[A-Z0-9]{3,12}\Z")
EVAL=re.compile(r"EV-[A-Z0-9]{3,12}\Z")
OBS=re.compile(r"OBS-[0-9]{4}\Z")
HASH=re.compile(r"[a-f0-9]{64}\Z")
EVALUATOR={"ref","scores","conflit_signale","recuse","independance_declaree"}
CANDIDATE={"preuve_id","candidat_ref","document_sha256","evaluateurs","orientation_proposee"}
OBSERVATION={"id","preuve_id","regime","type_observation","canal","empreinte_note",
             "contenant_donnees_personnelles","statut_reponse","empreinte_reponse"}
MAX_JSON=450000

def ensure(cond,label):
 if not cond:raise ValueError(label)

def read(path):
 p=Path(path)
 ensure(p.is_file() and not p.is_symlink() and p.stat().st_size<=MAX_JSON,
        "FICHIER_ABSENT_OU_INAPPROPRIE")
 x=json.loads(p.read_text(encoding="utf-8"))
 ensure(type(x) is dict,"JSON_OBJET_REQUIS")
 return x

def reference(d):
 ensure(type(d) is dict and set(d)==set(FILES),"CINQ_SOURCES_REQUISES")
 m,s,a,p,l=(d[z] for z in FILES)
 ensure(m.get("schema_version")=="P52N-1" and m.get("jalon")=="P52N" and
        m.get("date_reference")=="2026-10-19" and
        m.get("statut")=="PLAN_OPERATIONNEL_CANDIDAT_NON_ADOPTE",
        "PLAN_P52N_NON_CONFORME")
 ensure(m.get("references")=={
  "p52a":str(FILES["p52a"].relative_to(ROOT)),
  "p52m":str(FILES["p52m"].relative_to(ROOT)),
  "p52l":str(FILES["p52l"].relative_to(ROOT)),
  "journal":str(FILES["simulation"].relative_to(ROOT))
 },"SOURCE_LIEE_NON_CONFORME")
 ensure(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
        a.get("automatic_go") is False and a.get("rates_selected") is False and
        a.get("human_reviews_received") is False and
        a.get("financial_model_certified") is False,
        "P52A_CERTIFICATION_PREMATUREE")
 evid=a.get("required_evidence",[])
 ensure(type(evid) is list and len(evid)==20 and
        [x.get("id") for x in evid]==[f"F{k:02}" for k in range(1,21)] and
        all(x.get("statut")=="NON_VALIDE" and
            x.get("preuve_independante_obtenue") is False and
            x.get("decision_autorisee") is False for x in evid),
        "P52A_PREUVES_FICTIVEMENT_OBTENUES")
 ensure(p.get("schema_version")=="P52M-1" and
        p.get("etat_reel",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
        p["etat_reel"].get("membres_nommes")==0 and
        p["etat_reel"].get("avis_authentifies")==0 and
        p["etat_reel"].get("mandats_signes") is False and
        len(p.get("cartographie",[]))==20,
        "P52M_INSTANCES_REELLES_NON_CONSTITUEES")
 ensure(l.get("schema_version")=="P52L-1" and
        l.get("politique_decision",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
        l["politique_decision"].get("attestations_P52A_obtenues")==0,
        "P52L_ATTESTATION_FICTIVE")
 mandats=m.get("mandats")
 ensure(type(mandats) is list and len(mandats)==20,"VINGT_CAHIERS_REQUIS")
 expected_flags={"expert_mandate","competences_verifiees","conflits_verifies",
                 "livrable_recu","avis_externe_signe","preuve_validee",
                 "mise_en_public_autorisee"}
 for job,ev,risk in zip(mandats,evid,p["cartographie"]):
  ensure(job.get("id")==ev.get("id")==risk.get("id") and
         job.get("theme")==ev.get("theme") and
         job.get("regime")==ev.get("regime") and
         job.get("responsable_fonctionnel")==ev.get("responsable_fonctionnel") and
         job.get("preuve_p52a_a_obtenir")==ev.get("preuve_a_obtenir") and
         job.get("comite_pilote")==risk.get("comite_pilote") and
         job.get("comites_consultes")==risk.get("comites_consultes") and
         job.get("niveau_risque_provisoire")==risk.get("niveau_risque") and
         type(job.get("livrable_minimum_candidat")) is str and
         len(job["livrable_minimum_candidat"].strip())>=55 and
         job.get("annexes_obligatoires_proposees")==MUST_ANNEX and
         job.get("statut")=="MANDAT_NON_LANCE" and
         job.get("budget_mandat_chiffre") is None and
         job.get("cout_reel") is None and
         all(job.get(f) is False for f in expected_flags),
         "MANDAT_INVENTE_OU_LIENS_DEGRADE")
 proc=m.get("processus_mandat",{})
 for z in ("approbation_preliminaire_des_besoins","budget_autorise",
           "achats_ou_contrats_autorises","communication_externe_autorisee",
           "lancement_avis_interet_autorise"):
  ensure(proc.get(z) is False,"SOLLICITATION_OU_BUDGET_AUTORISE_SANS_PREUVE")
 ensure([proc.get(z) for z in ("experts_invites","candidatures_reelles_recues","contrats_signes")]==[0,0,0] and
        len(proc.get("etapes_proposees",[]))==9,
        "EMBAUCHES_NON_REELLES")
 scoring=m.get("principes_selection",{})
 ensure(scoring.get("criteres")==CRITERIA and
        scoring.get("notation_declarative")==[0,4] and
        scoring.get("evaluateurs_independants_minimum")==2 and
        scoring.get("note_totale_minimum_indicative")==15 and
        scoring.get("note_plancher_par_critere")==2 and
        scoring.get("toute_personne_en_conflit_recusee") is True and
        scoring.get("identites_mandats_diplomes_et_declarations_verifies_hors_depot") is False and
        scoring.get("methode_proposee_pas_regle_contractuelle") is True and
        scoring.get("couts_et_prix_non_estimes") is True and
        scoring.get("choix_ou_attribution_automatique_interdits") is True,
        "CRITERES_DE_SELECTION_DETOURNES")
 consult=m.get("consultation_citoyenne",{})
 ensure(consult.get("statut")=="NON_LANCEE" and
        consult.get("ouverture_autorisee") is False and
        consult.get("collecte_autorisee") is False and
        consult.get("observations_reelles_recues")==0 and
        consult.get("duree_consultation_definie_et_approuvee") is False and
        consult.get("protection_des_renseignements_a_valider") is True and
        consult.get("consultation_pas_sondage_representatif") is True and
        all(consult.get(f) is True for f in (
          "appel_a_contribution_non_envoye",
          "avis_mineurs_ou_donnees_personnelles_interdits_dans_git",
          "moderation_regles_publiques_a_adopter",
          "accessibilite_multicanale_a_prevoir",
          "aide_lecture_facile_et_accommodements_a_prevoir",
          "publication_des_limites_des_propositions",
          "explication_distinction_quebec_dans_canada_et_souverain",
          "personnes_peu_representees_a_consulter_sans_ciblage_persuasif",
          "droit_de_contestation_et_suivi_des_reponses")),
        "CONSULTATION_PREMATUREE")
 gov=m.get("controles_transversaux",{})
 ensure(gov.get("aucune_protection_main_activee") is True and
        gov.get("aucun_changement_sinjira") is True and
        gov.get("donnees_individuelles_non_commitees") is True and
        gov.get("variables_budgetaires_non_renseignees")==1320 and
        gov.get("preuves_independantes_p52a_non_obtenues")==20 and
        gov.get("comites_effectivement_constitues")==0 and
        gov.get("contrat_ou_depense_non_engage") is True and
        all(gov.get(f) is False for f in (
            "publication_programmatique_autorisee","fusion_autorisee",
            "adoption_autorisee")) and
        gov.get("decision")=="NO_GO_AUTOMATIQUE",
        "GARDE_FINALE_PERDUE")
 ensure(s.get("schema_version")=="P52N-SIM-1" and
        s.get("jalon")=="P52N" and
        s.get("statut")=="SIMULATIONS_VIDES_NON_AUTHENTIFIEES" and
        all(s.get(f) is False for f in (
          "autorisation_contrat","autorisation_consultation",
          "autorisation_publication")) and
        s.get("decision")=="NO_GO_AUTOMATIQUE",
        "SIMULATIONS_DECLARÉES_RÉELLES")
 return {x["id"]:x for x in mandats}

def examen(cahiers,journal):
 ensure(type(journal) is dict and
        journal.get("schema_version")=="P52N-SIM-1" and
        journal.get("statut")=="SIMULATIONS_VIDES_NON_AUTHENTIFIEES" and
        all(journal.get(f) is False for f in (
          "autorisation_contrat","autorisation_consultation",
          "autorisation_publication")) and
        journal.get("decision")=="NO_GO_AUTOMATIQUE",
        "JOURNAL_NON_FICTIF")
 candidates=journal.get("simulations_candidatures")
 observations=journal.get("simulations_observations")
 ensure(type(candidates) is list and len(candidates)<=40 and
        type(observations) is list and len(observations)<=80,
        "LOTS_TROP_GRANDS")
 ids=set()
 deemed=0
 conflict=0
 for candidate in candidates:
  ensure(type(candidate) is dict and set(candidate)==CANDIDATE,
         "CANDIDATURE_CONTIENT_CHAMP_NON_ATTENDU")
  pid=candidate["preuve_id"]
  code=candidate["candidat_ref"]
  ensure(type(pid) is str and pid in cahiers and
         type(code) is str and REF.fullmatch(code) and
         (pid,code) not in ids,
         "CANDIDATURE_INVALIDE_OU_DUPLIQUEE")
  ids.add((pid,code))
  needhash(candidate["document_sha256"])
  scores=candidate["evaluateurs"]
  ensure(type(scores) is list and 2<=len(scores)<=6,
         "DEUX_EVALUATEURS_MINIMUM")
  seen=set()
  eligible=[]
  for person in scores:
   ensure(type(person) is dict and set(person)==EVALUATOR,
          "EVALUATEUR_CHAMP_NON_PREVU")
   who=person["ref"]
   ensure(type(who) is str and EVAL.fullmatch(who) and
          who not in seen and who!=code,"JUGE_ET_PARTIE")
   seen.add(who)
   ensure(all(type(person[z]) is bool for z in (
           "conflit_signale","recuse","independance_declaree")),
          "STATUT_INTERET_NON_BOOLEEN")
   if person["conflit_signale"] or not person["independance_declaree"]:
    ensure(person["recuse"] is True,"CONFLIT_NON_RECUSE")
   if person["recuse"]:
    ensure(person["scores"] is None,"RECUSE_A_NOTÉ")
    conflict+=1
   else:
    grades=person["scores"]
    ensure(type(grades) is list and len(grades)==5 and
           all(type(g) is int and 0<=g<=4 for g in grades),
           "NOTES_INVALIDES")
    eligible.append(grades)
  ensure(len(eligible)>=2,"EVALUATEURS_ADMISSIBLES_INSUFFISANTS")
  rationale=(all(min(g)>=2 and sum(g)>=15 for g in eligible))
  orientation=candidate["orientation_proposee"]
  ensure(orientation in ("A_ETUDIER","INADMISSIBLE_SIMULEE",
                          "COMPETENCES_A_REVOIR"),"ORIENTATION_INCONNUE")
  if orientation=="A_ETUDIER":
   ensure(rationale,"APPRECIATION_NON_CONCORDANTE")
   deemed+=1
  else:
   ensure(not rationale,"APPRECIATION_INJUSTIFIEE")
 types={"APPUI","OBJECTION","QUESTION","ALTERNATIVE"}
 channels={"ECRIT","AUDITION","ACCESSIBLE"}
 statuses={"SANS_REPONSE","REPONSE_DECLAREE"}
 seenobs=set()
 for obs in observations:
  ensure(type(obs) is dict and set(obs)==OBSERVATION,
         "CONTRIBUTION_CONTIENT_IDENTIFIANTS")
  ref=obs["id"]
  pid=obs["preuve_id"]
  ensure(type(ref) is str and OBS.fullmatch(ref) and ref not in seenobs and
         type(pid) is str and pid in cahiers,
         "OBSERVATION_INVALIDE")
  seenobs.add(ref)
  ensure(obs["regime"]==cahiers[pid]["regime"] and
         obs["type_observation"] in types and
         obs["canal"] in channels and
         obs["contenant_donnees_personnelles"] is False and
         obs["statut_reponse"] in statuses,
         "OBSERVATION_SENSIBLE_OU_INCORRECTE")
  needhash(obs["empreinte_note"])
  if obs["statut_reponse"]=="SANS_REPONSE":
   ensure(obs["empreinte_reponse"] is None,"REPONSE_FICTIVE")
  else:
   needhash(obs["empreinte_reponse"])
 return {
  "jalon":"P52N","schema_version":"P52N-1",
  "mandats_cadres_non_lances":20,
  "candidatures_simulees":len(candidates),
  "candidatures_avec_appreciation_favorable_simulee":deemed,
  "recusations_declarees_simulees":conflict,
  "observations_simulees":len(observations),
  "candidatures_reelles":0,
  "contributions_reelles":0,
  "experts_mandates":0,
  "contrats_signes":0,
  "preuves_p52a_encore_non_attestees":20,
  "montants_budgetaires_encore_inconnus":1320,
  "autorisation_sollicitation":False,
  "autorisation_consultation":False,
  "autorisation_publication":False,
  "autorisation_fusion":False,
  "decision":"NO_GO_AUTOMATIQUE"
 }

def needhash(v):
 ensure(type(v) is str and HASH.fullmatch(v),"EMPREINTE_NON_CONFORME")

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 for k,p in FILES.items():parser.add_argument("--"+k,type=Path,default=p)
 parser.add_argument("--rapport",type=Path)
 parser.add_argument("--exiger-autorisations",action="store_true")
 args=parser.parse_args(argv)
 try:
  loaded={k:read(getattr(args,k)) for k in FILES}
  mandates=reference(loaded)
  result=examen(mandates,loaded["simulation"])
  code=3 if args.exiger_autorisations else 0
 except (OSError,ValueError,UnicodeError,TypeError,KeyError) as err:
  result={"jalon":"P52N","statut":"CONTROLE_REJETE",
          "type_erreur":type(err).__name__,
          "autorisation_sollicitation":False,
          "autorisation_consultation":False,
          "autorisation_publication":False,
          "autorisation_fusion":False,
          "decision":"NO_GO_AUTOMATIQUE"}
  code=2
 payload=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
 if args.rapport:
  try:
   args.rapport.parent.mkdir(parents=True,exist_ok=True)
   with args.rapport.open("x",encoding="utf-8") as file:file.write(payload)
  except OSError:return 2
 else:print(payload,end="")
 return code

if __name__=="__main__":
 sys.exit(main())
