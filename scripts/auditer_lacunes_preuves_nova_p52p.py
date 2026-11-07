#!/usr/bin/env python3
"""P52P: calcul reproductible des lacunes P52B/P52D, sans GO fiscal."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
 "registre":D/"P52P_REGISTRE_COUVERTURE_ET_MANQUES.json",
 "gabarit":D/"P52P_GABARIT_RECEPTION_PIECE.json",
 "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
 "p52b":D/"P52B_GABARIT_MODELE_DECENNAL.json",
 "p52d":D/"P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json",
 "p52i":D/"P52I_SOURCES_ET_ATTESTATIONS.json",
 "p52j":D/"P52J_RELECTURE_PRIMAIRE_BUDGET_2026_2027.json",
 "p52k":D/"P52K_REGISTRE_PROVENANCE_BUDGET.json",
 "p52o":D/"P52O_PLAN_ACQUISITION_PREUVES.json",
 "sources_p52o":D/"P52O_SOURCES_OFFICIELLES_REPEREES.json",
 "p52n":D/"P52N_CAHIER_MANDATS_ET_CONSULTATION.json"
}
REGIMES=("QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN")
SCENARIOS=("central","prudent","stress")
B_RECETTES=("impot_revenu_net","anti_evasion_additionnelle_nette",
            "revenus_non_fiscaux_nets","transferts_federaux_nets",
            "autres_prelevements_provinciaux_nets")
B_DEPENSES=("services_existants_hors_dette_et_municipal_nets",
            "service_dette_net","transferts_municipaux_nets",
            "fonctions_souveraines_nouvelles_nettes","couts_transition_nets",
            "provision_crises_nette")
B_CONTEXT=("solde_budgetaire_precedent","ratio_dette_nette_pib_pct")
M_HOUSE=("revenu_brut","prestations_federales","prestations_quebec_ou_etat",
         "impot_revenu_federal","impot_revenu_quebec_ou_etat",
         "cotisations_obligatoires","prelevements_municipaux_directs",
         "taxes_consommation_supportees")
M_BIZ=("chiffre_affaires","couts_exploitation_hors_salaires",
       "masse_salariale","impot_entreprise_federal",
       "impot_entreprise_quebec_ou_etat","cotisations_employeur",
       "prelevements_municipaux","taxes_consommation_non_recouvrables",
       "subventions_recues","charge_additionnelle_anti_evasion")
STEPS=("document_source_complet_et_version","copie_originale_archivee_avec_droits",
       "empreinte_sha256_verifiee","definitions_perimetre_methode_unites",
       "rapprochement_et_reproduction_independante",
       "avis_expert_mandate_independant_signe",
       "avis_contradictoire_et_reserves_resolues",
       "decision_humaine_formellement_competente")
SOURCES={
    "p52i":("S01","S02","S03","S04","S05","S06","S07","S08"),
    "sources_p52o":tuple("REF%02d"%i for i in range(1,11)),
    "p52j":("DISC2026_T3","PLAN2026_F2")
}

def need(ok,why):
 if not ok:raise ValueError(why)

def read(path):
 p=Path(path)
 need(p.is_file() and not p.is_symlink() and p.stat().st_size<500000,
      "SOURCE_INACCESSIBLE_OU_TROP_GRANDE")
 obj=json.loads(p.read_text(encoding="utf-8"))
 need(type(obj) is dict,"JSON_OBJET_REQUIS")
 return obj

def count_financial_unknowns(B,D):
 need(B.get("schema_version")=="P52B-1" and
      B.get("statut")=="ETUDE_NON_ADOPTEE" and
      B.get("authorization")=={"legal":False,"publication":False,"fusion":False},
      "P52B_FAUSSE_AUTORISATION")
 need(D.get("schema_version")=="P52D-1" and
      D.get("statut")=="ETUDE_NON_ADOPTEE" and
      D.get("aucune_ponderation_population") is True and
      all(D.get("autorisations",{}).get(k) is False for k in ("fiscalite","publication","fusion")),
      "P52D_REPRESENTATIVITE_FICTIVE")
 need(tuple(B.get("regimes",{}))==REGIMES and
      tuple(D.get("regimes",{}))==REGIMES,"PERIMETRE_RÉGIME_INVALIDE")
 b_missing=0
 context_missing=0
 d_missing=0
 exerc=0
 households=0
 business=0
 split={}
 for regime in REGIMES:
  br=B["regimes"][regime].get("trajectoires",{})
  dr=D["regimes"][regime].get("scenarios",{})
  need(tuple(br)==SCENARIOS and tuple(dr)==SCENARIOS,
       "SCENARIOS_MANQUANTS")
  local_b=local_d=0
  for sc in SCENARIOS:
   years=br[sc]
   need(type(years) is list and len(years)==10 and
        [r.get("exercice_debut") for r in years]==list(range(2027,2037)),
        "EXERCICES_B_INCORRECTS")
   for row in years:
    exerc+=1
    revenue=row.get("recettes",{})
    expense=row.get("depenses",{})
    need(type(revenue) is dict and tuple(revenue)==B_RECETTES and
         type(expense) is dict and tuple(expense)==B_DEPENSES,
         "CHAMPS_FINANCIERS_B_ALTERES")
    need(revenue["anti_evasion_additionnelle_nette"]=="0" and
         row.get("sources",{}).get("anti_evasion_additionnelle_nette")==
            "HYPOTHESE_PRUDENTE_ZERO_NON_CERTIFIEE" and
         all(revenue[k] is None for k in B_RECETTES if k!="anti_evasion_additionnelle_nette") and
         all(expense[k] is None for k in B_DEPENSES) and
         all(row.get(k) is None for k in B_CONTEXT) and
         all(row.get(k) is False for k in
             ("perimetre_reconcilie","incidence_menages_validee",
              "emplois_et_services_valides","inventaire_prelevements_valide")),
         "P52B_MONTANT_AJOUTE_SANS_PREUVE")
    local_b+=4+len(B_DEPENSES)
    context_missing+=len(B_CONTEXT)
   typ=dr[sc]
   need(type(typ) is dict and tuple(typ)==("menages","entreprises") and
        len(typ["menages"])==5 and len(typ["entreprises"])==2,
        "CASES_P52D_ALTÉRÉES")
   for kind,expected,n in (
        ("menages",M_HOUSE,5),("entreprises",M_BIZ,2)):
    for row in typ[kind]:
     need(row.get("regime")==regime and row.get("scenario")==sc and
          row.get("classification_validee") is False and
          row.get("sources")=={},"CAS_NON_ATT_ENDU")
     for stade in ("actuel","propose"):
      obj=row.get(stade,{})
      need(type(obj) is dict and tuple(obj)==expected and
           all(obj[key] is None for key in expected),
           "P52D_MONTANT_SANS_PIECE_CERTIFIEE")
      local_d+=len(expected)
     if kind=="menages":households+=1
     else:business+=1
  split[regime]={"monetaires_p52b_manquantes":local_b,
                 "monetaires_p52d_manquantes":local_d}
  b_missing+=local_b
  d_missing+=local_d
 need(b_missing==600 and context_missing==120 and
      d_missing==720 and exerc==60 and households==30 and business==12,
      "COMPTEURS_FINANCIERS_ALTERES")
 return {"p52b":b_missing,"p52d":d_missing,"context":context_missing,
         "exercices":exerc,"menages":households,"entreprises":business,
         "repartition":split}

def audit(inputs):
 need(type(inputs) is dict and set(inputs)==set(FILES),"ONZE_ENTREES_ATTENDUES")
 R,T,A,B,D,I,J,K,O,S,N=(inputs[key] for key in FILES)
 need(R.get("schema_version")=="P52P-1" and R.get("jalon")=="P52P" and
      R.get("date_reference")=="2026-10-19" and
      R.get("statut")=="REGISTRE_LACUNES_ET_PROVENANCE_NON_ACQUISE",
      "P52P_INCORRECT")
 need(R.get("references")=={
      key:str(FILES[key].relative_to(ROOT))
      for key in FILES if key not in ("registre",)}, "LIENS_NON_TRACABLES")
 need(A.get("status")=="PROPOSITION_NON_ADOPTEE" and
      A.get("automatic_go") is False and A.get("rates_selected") is False and
      A.get("financial_model_certified") is False and
      A.get("human_reviews_received") is False,
      "P52A_AUTORISATION_FAUSSE")
 proofs=A.get("required_evidence",[])
 need(type(proofs) is list and len(proofs)==20 and
      [p.get("id") for p in proofs]==[f"F{k:02d}" for k in range(1,21)] and
      all(p.get("statut")=="NON_VALIDE" and
          p.get("preuve_independante_obtenue") is False and
          p.get("decision_autorisee") is False for p in proofs),
      "PREUVES_P52A_FICTIVES")
 need(I.get("schema_version")=="P52I-1" and
      I.get("source_revue_independante") is False and
      I.get("donnees_extraites_certifiees") is False and
      [x.get("id") for x in I.get("plan_preuves",[])]==
      [p["id"] for p in proofs] and
      all(x.get("statut")=="NON_ATTESTEE" for x in I["plan_preuves"]),
      "PISTES_P52I_NON_AUTHENTIFIEES")
 need(O.get("schema_version")=="P52O-1" and
      O.get("gouvernance",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
      [p.get("id") for p in O.get("preuves",[])]==
      [p["id"] for p in proofs] and
      all(p.get("preuve_independante_obtenue") is False for p in O["preuves"]),
      "PLAN_P52O_FAUSSE_PREUVE")
 need(S.get("schema_version")=="P52O-SOURCES-1" and
      S.get("decision")=="NO_GO_AUTOMATIQUE" and
      len(S.get("references",[]))==10 and
      all(s.get("attestation_expert_independant") is False for s in S["references"]),
      "SOURCES_P52O_FAUSSEMENT_ATTESTEES")
 need(N.get("schema_version")=="P52N-1" and
      N.get("controles_transversaux",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
      len(N.get("mandats",[]))==20 and
      all(p.get("expert_mandate") is False for p in N["mandats"]),
      "MANDAT_P52N_FICTIF")
 need(J.get("schema_version")=="P52J-1" and
      J.get("validation_de_nature",{}).get("preuve_F09_independamment_attestee") is False and
      J["validation_de_nature"].get("verification_hash_pdf_original") is False and
      len(J.get("source_primaires",[]))==2,
      "RELECTURE_P52J_NON_CERTIFIEE")
 need(K.get("schema_version")=="P52K-1" and
      K.get("decision")=="NO_GO_AUTOMATIQUE" and
      len(K.get("fichiers_source",[]))==2 and
      all(x.get("empreinte_sha256_pdf_original") is None and
          x.get("attestation_externe_signee") is None for x in K["fichiers_source"]),
      "ARCHIVE_P52K_INVENTEE")
 need(T.get("schema_version")=="P52P-RECEPTION-1" and
      T.get("nature")=="GABARIT_VIERGE_NON_PIECE" and
      T.get("preuve_id") is None and T.get("reference_source") is None and
      T.get("empreinte_sha256_original") is None and
      all(T.get(x) is None for x in (
          "date_acquisition_utc","version_document",
          "page_tableau_definition","note_droits_et_conservation",
          "perimetre_institutionnel","indice_prevision_ou_realisation")) and
      all(T.get(x) is False for x in (
          "origine_officielle_authentifiee","double_relecture_independante_obtenue",
          "expert_independant_reellement_mandate","signature_et_identite_authentifiees",
          "conflits_interets_verifies","avis_contradictoire_obtenu",
          "contestations_et_reserves_reglees",
          "decision_humaine_competente_obtenue","preuve_validee",
          "publication_autorisee","adoption_autorisee")) and
      T.get("decision")=="NO_GO_AUTOMATIQUE",
      "GABARIT_REMPLI_FAUSSEMENT")
 catalog=R.get("index_pistes")
 expected_catalog=[
  *[("PISTE_P52I",s["id"],s["url"]) for s in I["sources"]],
  *[("PISTE_P52O",s["id"],s["url"]) for s in S["references"]],
  *[("RELECTURE_P52J",s["id"],s["url"]) for s in J["source_primaires"]]
 ]
 need(type(catalog) is list and len(catalog)==20,"VINGT_REFERENCE_SOURCES_ATTENDUES")
 for record,(stage,ident,url) in zip(catalog,expected_catalog):
  need(record.get("id")==ident and record.get("regime")==stage and
       record.get("url")==url and
       all(record.get(k) is False for k in (
           "version_publique_confirmee","empreinte_pdf_recue","expertise_externe")),
       "CATALOGUE_DEFORME_OU_FICTIVEMENT_VALIDE")
 sources=set([x["id"] for x in catalog])
 rows=R.get("exigences")
 need(type(rows) is list and len(rows)==20,"VINGT_REGISTRES_PREUVES_ATTENDUS")
 covered=0
 for row,pa,pi,po,pn in zip(rows,proofs,I["plan_preuves"],O["preuves"],N["mandats"]):
  ids=list(dict.fromkeys(pi.get("source_ids_candidats",[])+po.get("sources_preliminaires",[])))
  need(row.get("id")==pa["id"]==pi["id"]==po["id"]==pn["id"] and
       row.get("regime")==pa["regime"] and
       row.get("theme")==pa["theme"] and
       row.get("vague")==po["vague"] and
       row.get("comite_pilote")==po["comite_pilote"] and
       row.get("dependances_techniques")==po["dependances_techniques"] and
       row.get("preuve_originale_a_obtenir")==pa["preuve_a_obtenir"] and
       row.get("livrable_mandat_propose")==pn["livrable_minimum_candidat"] and
       row.get("pistes_sources_reperées")==ids and
       set(ids)<=sources and
       row.get("relecture_budgetaire_P52J_disponible") is (pa["id"]=="F09") and
       row.get("phase_acquisition")=="NON_ACQUISE" and
       row.get("statut_juridique")=="NON_VALIDE" and
       type(row.get("pieces_obligatoires")) is dict and
       set(row["pieces_obligatoires"])==set(STEPS) and
       all(v is None for v in row["pieces_obligatoires"].values()) and
       all(row.get(k) is False for k in (
           "preuve_independante_authentifiee",
           "source_identifiee_est_une_preuve",
           "certification_budgetaire","adoption_autorisee")),
       "PREUVE_OU_STATUT_P52P_INCOHERENT")
  if ids:covered+=1
 need(R.get("regles_reception") and
      all(value is True for value in R["regles_reception"].values()) and
      len(R["regles_reception"])==10,"REGLES_RECEPTION_PERDUES")
 state=R.get("etat_verifie_par_sources_amont",{})
 need(state.get("originaux_pdf_budget_archive_et_verifies")==0 and
      state.get("avis_independants_certifies")==0 and
      state.get("mandats_experts_reels")==0 and
      state.get("valeurs_monetaires_p52b_renseignees")==0 and
      state.get("valeurs_monetaires_p52d_renseignees")==0 and
      all(state.get(k) is False for k in (
          "publication_autorisee","fusion_autorisee","adoption_autorisee")) and
      state.get("decision")=="NO_GO_AUTOMATIQUE",
      "GARDES_NO_GO_NON_ACTIVES")
 counts=count_financial_unknowns(B,D)
 # Aucun lien ou champ par personne dans le rapport agrégé.
 return {
  "jalon":"P52P","schema_version":"P52P-1",
  "preuves_total":20,"preuves_attestees":0,
  "preuves_avec_pistes_de_sources":covered,
  "preuves_sans_piste_de_source":20-covered,
  "pistes_referencees_total":len(catalog),
  "pdf_primaires_relecture_assistee":2,
  "pdf_budget_originaux_archives_attestes":0,
  "exercices_scenarios_p52b":counts["exercices"],
  "valeurs_monetaires_p52b_inconnues":counts["p52b"],
  "autres_indicateurs_p52b_inconnus":counts["context"],
  "cas_menages_p52d":counts["menages"],
  "cas_entreprises_p52d":counts["entreprises"],
  "valeurs_monetaires_p52d_inconnues":counts["p52d"],
  "valeurs_monetaires_totales_inconnues":counts["p52b"]+counts["p52d"],
  "par_regime":counts["repartition"],
  "assurance_non_appauvrissement":False,
  "recettes_nouvelles_certifiees":False,
  "adoption_autorisee":False,"publication_autorisee":False,
  "fusion_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"
 }

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 for k,p in FILES.items():parser.add_argument("--"+k,type=Path,default=p)
 parser.add_argument("--rapport",type=Path)
 parser.add_argument("--exiger-preuves",action="store_true")
 args=parser.parse_args(argv)
 try:
  docs={k:read(getattr(args,k)) for k in FILES}
  result=audit(docs)
  code=3 if args.exiger_preuves else 0
 except (OSError,ValueError,UnicodeError,TypeError,KeyError) as exc:
  result={"jalon":"P52P","statut":"ANOMALIE",
          "type_erreur":type(exc).__name__,
          "adoption_autorisee":False,"publication_autorisee":False,
          "fusion_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"}
  code=2
 body=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
 if args.rapport:
  try:
   args.rapport.parent.mkdir(parents=True,exist_ok=True)
   with args.rapport.open("x",encoding="utf-8") as handle:handle.write(body)
  except OSError:return 2
 else:print(body,end="")
 return code

if __name__=="__main__":
 sys.exit(main())
