#!/usr/bin/env python3
"""P52W : protocole F09 de sélection proposée sans candidat, mandat ni GO."""
import argparse
import csv
import io
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "selection":D/"P52W_MATRICE_SELECTION_ET_GARDES_F09.json",
 "reception":D/"P52W_REGISTRE_RECEPTION_OFFRES_VIDE.json",
 "p52v":D/"P52V_REGISTRE_MISSION_F09.json",
 "p52n":D/"P52N_CAHIER_MANDATS_ET_CONSULTATION.json",
 "p52q":D/"P52Q_DOSSIERS_INSTRUCTION_VAGUE1.json",
 "p52u":D/"P52U_INSTRUCTION_HUMAINE_F09.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
GATES={
 "G01":("Autorité juridique du mandant et capacité de signer","PREREQUIS"),
 "G02":("Qualification du régime contractuel privé ou public","PREREQUIS"),
 "G03":("Budget réel et provenance licite des fonds autorisés","PREREQUIS"),
 "G04":("Description de mission P52V et méthode de relecture","OBLIGATOIRE"),
 "G05":("Identité et droit d'exercice professionnel vérifiés","OBLIGATOIRE"),
 "G06":("Compétence prouvée en finances publiques du Québec","OBLIGATOIRE"),
 "G07":("Indépendance vis-à-vis des auteurs et financeurs","BLOQUANT"),
 "G08":("Pas d'auto-évaluation des chiffres produits","BLOQUANT"),
 "G09":("Confidentialité, collecte minimale et conservation","OBLIGATOIRE"),
 "G10":("Devis écrit avec coût global et conditions","OBLIGATOIRE"),
 "G11":("Possibilité d'avis négatif motivé et de réserves","BLOQUANT"),
 "G12":("Séparation humaine entre contrôle et décision","BLOQUANT"),
}
AXES={
 "S01":("Expérience démontrée en finances publiques québécoises",30),
 "S02":("Méthodologie de relecture des 39 positions et concordances",25),
 "S03":("Capacité de contradiction, indépendance et réserves",20),
 "S04":("Qualité des livrables, méthode et confidentialité",15),
 "S05":("Coût total et échéance à périmètre comparable",10),
}
URLS=(
 "https://cpaquebec.ca/fr/trouver-un-cpa/tableau-de-lordre/intro/",
 "https://www.legisquebec.gouv.qc.ca/fr/document/lc/c-65.1",
 "https://www.legisquebec.gouv.qc.ca/fr/document/lc/p-39.1",
 "https://www.cai.gouv.qc.ca/protection-renseignements-personnels/sujets-et-domaines-dinteret/principaux-changements-loi-25",
)
PRIVACY_FIELDS={
 "noms_et_coordonnees_non_dans_git","devis_et_cv_non_dans_git",
 "conflits_d_interets_detaille_hors_git","aucune_prospection_par_extraction_du_registre_CPA",
 "aucune_sortie_de_personnes_dans_CI","mode_reception_securise_a_definir",
}
PARAM_FALSE={
 "organisme_mandant_legalement_identifie","regime_contractuel_valide",
 "criteres_adoptes","appels_offres_ou_invitation_emis",
 "responsables_humains_nommes",
}
GUARD_ZERO={
 "candidats_reels_recus","devis_reels_recus","contrats_signes",
 "fonds_engages_cad","experts_F09_mandates",
 "analyses_F09_reellement_signees","positions_relecture_humaines_certifiees",
 "preuves_F01_F20_certifiees",
}

def need(ok,reason):
 if not ok:raise ValueError(reason)

def read(path):
 p=Path(path)
 need(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=500_000,
      "JSON_ABSENT_OU_TROP_GRAND")
 d=json.loads(p.read_text(encoding="utf-8"))
 need(type(d) is dict,"JSON_OBJECT_REQUIS")
 return d

def verify(documents):
 need(type(documents) is dict and set(documents)==set(FILES),
      "SEPT_REGISTRES_REQUIS")
 m,r,v,n,q,u,a=(documents[x] for x in FILES)
 need(m.get("schema_version")=="P52W-1" and m.get("jalon")=="P52W" and
      m.get("date_reference")=="2026-10-20" and
      m.get("statut")=="PROCEDURE_PROPOSEE_NON_ADOPTEE_SANS_OFFRE" and
      m.get("preuve")=="F09","MANIFESTE_INVALIDE")
 need(m.get("references")=={
        key:str(FILES[key].relative_to(ROOT)) for key in
        ("p52v","p52n","p52q","p52u","p52a","reception")
      },"REFERENCE_INTERNE_INCORRECTE")
 need(r.get("schema_version")=="P52W-RECEPTION-1" and
      r.get("jalon")=="P52W" and
      r.get("statut")=="AUCUNE_RECEPTION_EXTERNE" and
      r.get("offres")==[] and r.get("evenements")==[] and
      r.get("etat")=={"receptions_authentifiees":0,
                     "offres_admissibles":0,
                     "avis_humains_verifies":0,
                     "contrats":0} and
      r.get("documents_confidentiels_dans_git") is False and
      r.get("identites_ou_devis_publies") is False and
      r.get("decision")=="NO_GO_AUTOMATIQUE","RECEPTION_FICTIVE")
 need(v.get("schema_version")=="P52V-1" and
      v.get("bilan",{}).get("positions_a_revoir")==39 and
      v["bilan"].get("controles_humains_en_attente")==12 and
      v["bilan"].get("livrables_professionnels_en_attente")==8 and
      v.get("audit_et_protection",{}).get("decision")=="NO_GO_AUTOMATIQUE",
      "P52V_NON_CONFORME")
 sel=v.get("selection_candidat",{})
 need(sel.get("statut")=="NON_LANCE" and
      sel.get("devis_reels_recus")==0 and sel.get("nom_candidat") is None and
      sel.get("contrat_signe") is False and
      sel.get("fonds_engages_cad")==0 and
      sel.get("mandat_accepte_par_professionnel") is False,
      "P52V_AFFICHE_UN_MANDAT")
 need(n.get("schema_version")=="P52N-1" and
      n.get("controles_transversaux",{}).get("contrat_ou_depense_non_engage") is True and
      n["controles_transversaux"].get("decision")=="NO_GO_AUTOMATIQUE",
      "P52N_FAUSSE_DEPENSE")
 f09=next((x for x in n.get("mandats",[]) if x.get("id")=="F09"),{})
 need(f09.get("statut")=="MANDAT_NON_LANCE" and
      f09.get("expert_mandate") is False and
      f09.get("avis_externe_signe") is False and
      f09.get("cout_reel") is None,"P52N_FAUX_MANDAT")
 need(q.get("schema_version")=="P52Q-1" and
      q.get("gouvernance",{}).get("decision")=="NO_GO_AUTOMATIQUE","P52Q_NON_GO")
 f09q=next((x for x in q.get("dossiers",[]) if x.get("id")=="F09"),{})
 need(f09q.get("expert_reel_mandate") is False and
      f09q.get("avis_favorable_recu") is False and
      f09q.get("decision_adoption_autorisee") is False,
      "P52Q_FAUX_AVIS")
 need(u.get("schema_version")=="P52U-1" and
      u.get("decision")=="NO_GO_AUTOMATIQUE" and
      u.get("relecture_humaine",{}).get("avis_independant_signe") is False,
      "P52U_FAUSSE_EXPERTISE")
 need(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
      a.get("automatic_go") is False and
      a.get("financial_model_certified") is False and
      a.get("human_reviews_received") is False and
      len(a.get("required_evidence",[]))==20 and
      [e.get("id") for e in a["required_evidence"]]==[
         f"F{x:02d}" for x in range(1,21)] and
      all(x.get("statut")=="NON_VALIDE" and
          x.get("preuve_independante_obtenue") is False and
          x.get("decision_autorisee") is False
          for x in a["required_evidence"]),"P52A_FAUSSE_VALIDATION")
 gates=m.get("conditions")
 need(type(gates) is list and len(gates)==12 and
      [x.get("id") for x in gates]==list(GATES),"GATES_DOUBLONS_OU_ABSENTS")
 for x in gates:
  label,cat=GATES[x["id"]]
  need(set(x)=={"id","libelle","nature","statut","verification_humaine",
               "reference_preuve_privee"} and
       x.get("libelle")==label and x.get("nature")==cat and
       x.get("statut")=="NON_VERIFIE" and
       x.get("verification_humaine") is False and
       x.get("reference_preuve_privee") is None,
       "GARDE_FAUSSEMENT_COMPLETE")
 axes=m.get("axes_proposes")
 need(type(axes) is list and len(axes)==5 and
      [x.get("id") for x in axes]==list(AXES),"AXES_MANQUANTS")
 for row in axes:
  label,points=AXES[row["id"]]
  need(set(row)=={"id","libelle","poids","adopte","score_reel"} and
       row["libelle"]==label and type(row.get("poids")) is int and
       row["poids"]==points and row.get("adopte") is False and
       row.get("score_reel") is None,"PONDERATION_REELLE_OU_FAUSSE_NOTE")
 need(sum(x["poids"] for x in axes)==100,"PONDERATION_N_EST_PAS_100")
 steps=m.get("ordre_processus")
 need(steps==["QUALIFIER_MANDANT","AUTORISER_BUDGET","APPROUVER_CRITERES",
             "PREPARER_INVITATION","RECEPTION_CONFIDENTIELLE",
             "VERIFIER_INDEPENDANCE_ET_COMPETENCES","CONTRE_EVALUER",
             "DECISION_HUMAINE_MOTIVEE","CONTRAT_EVENTUEL"],
      "ETAPES_DESORDONNEES")
 refs=m.get("sources")
 need(type(refs) is list and len(refs)==4 and
      [x.get("id") for x in refs]==["CPA","LCOP","PRIVE","CAI"] and
      [x.get("url") for x in refs]==list(URLS) and
      all(x.get("verification_reelle_effectuee") is False and
          type(x.get("utilite")) is str and len(x["utilite"])>40
          for x in refs),"SOURCES_EXTERIEURES_NON_VERIFIEES")
 privacy=m.get("donnees_confidentielles")
 need(type(privacy) is dict and set(privacy)==PRIVACY_FIELDS and
      all(privacy[k] is True for k in PRIVACY_FIELDS),
      "PRIVACY_GUARDS_MANQUANTS")
 parms=m.get("parametres_non_adoptes")
 need(type(parms) is dict and
      all(parms.get(x) is False for x in PARAM_FALSE) and
      all(parms.get(x) is None for x in (
          "seuil_score_requis","nombre_candidats_minimum_legalement_requis",
          "budget_max_autorise_cad")) and
      parms.get("ponderations_proposees_non_autorisees") is True,
      "PROCEDURE_NON_ADOPTEE_A_VIOLATION")
 gg=m.get("garde",{})
 need(type(gg) is dict and
      all(type(gg.get(x)) is int and gg[x]==0 for x in GUARD_ZERO) and
      gg.get("valeurs_financieres_manquantes")==1320 and
      all(gg.get(x) is False for x in (
          "publication_autorisee","fusion_autorisee","adoption_autorisee")) and
      gg.get("decision")=="NO_GO_AUTOMATIQUE",
      "GARDE_ADOPTION_FAUSSE")
 return {
  "jalon":"P52W","schema_version":"P52W-1",
  "conditions_non_verifiees":len(gates),
  "axes_scores_non_adoptes":len(axes),
  "somme_ponderations_proposees":100,
  "offres_recues":0,"experts_recrutes":0,"devis_reels":0,
  "contrats_signes":0,"cout_engage_cad":0,
  "positions_F09_validees_par_humain":0,
  "preuves_F01_F20_non_validees":20,
  "valeurs_financieres_nova_inconnues":1320,
  "publication_autorisee":False,"fusion_autorisee":False,
  "adoption_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"
 }

def simulation_synthetique(obj):
 """Une simulation unit-test ne peut être une candidature ni un score officiel."""
 need(type(obj) is dict and
      set(obj)=={"fictif","marqueur","gates","notes"} and
      obj.get("fictif") is True and
      obj.get("marqueur")=="TEST_UNITAIRE_SYNTHETIQUE",
      "SIMULATION_REELLE_INTERDITE")
 flags=obj.get("gates")
 notes=obj.get("notes")
 need(type(flags) is dict and set(flags)==set(GATES) and
      all(type(v) is bool for v in flags.values()),
      "GATES_SIMULATION_INCOMPLETES")
 need(type(notes) is dict and set(notes)==set(AXES) and
      all(type(n) is int and 0<=n<=100 for n in notes.values()),
      "NOTES_SIMULATION_INVALIDES")
 admissible=all(flags.values())
 score=sum(notes[k]*AXES[k][1] for k in AXES)/100 if admissible else None
 return {"simulation_sans_candidature_reelle":True,
         "admissibilite_fictive":admissible,
         "score_indicatif_fictif":score,
         "motif_irrecevabilite":"PORTE_OBLIGATOIRE_NON_SATISFAITE" if not admissible else None,
         "selection_reelle_effectuee":False,
         "mandat_autorise":False,
         "publication_autorisee":False,
         "adoption_autorisee":False,
         "decision":"NO_GO_AUTOMATIQUE"}

def blank_csv():
 output=io.StringIO(newline="")
 csv.writer(output,lineterminator="\n").writerow([
    "reference_dossier_locale","critere_G01_a_G12","constat_fait_par_responsable",
    "piece_privee_reference","score_S01_a_S05_apres_adoption",
    "reserve_ou_conflit","decision_humaine_motivee"])
 return output.getvalue()

def save_new(path,content):
 p=Path(path)
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8",newline="") as h:h.write(content)

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 for k,f in FILES.items():p.add_argument("--"+k,type=Path,default=f)
 p.add_argument("--simulation",type=Path)
 p.add_argument("--rapport",type=Path)
 p.add_argument("--export-csv",type=Path)
 p.add_argument("--exiger-mandat",action="store_true")
 args=p.parse_args(argv)
 try:
  docs={k:read(getattr(args,k)) for k in FILES}
  result=verify(docs)
  if args.simulation is not None:
   result["simulation_fictive"]=simulation_synthetique(read(args.simulation))
  if args.rapport and args.export_csv:
   need(args.rapport.resolve()!=args.export_csv.resolve(),
        "SORTIES_MEME_CHEMIN")
  if args.rapport:save_new(args.rapport,json.dumps(result,ensure_ascii=False,indent=2)+"\n")
  if args.export_csv:save_new(args.export_csv,blank_csv())
  if not args.rapport and not args.export_csv:
   print(json.dumps(result,ensure_ascii=False,indent=2))
  return 3 if args.exiger_mandat else 0
 except (OSError,ValueError,TypeError,UnicodeError,KeyError) as ex:
  print(json.dumps({"jalon":"P52W","etat":"REJET_TECHNIQUE",
    "categorie_erreur":type(ex).__name__,"decision":"NO_GO_AUTOMATIQUE",
    "publication_autorisee":False,"fusion_autorisee":False,
    "adoption_autorisee":False},ensure_ascii=False))
  return 2

if __name__=="__main__":
 sys.exit(main())
