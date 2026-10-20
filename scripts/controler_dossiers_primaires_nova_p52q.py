#!/usr/bin/env python3
"""P52Q : première vague documentaire F01 F02 F03 F04 F07 F09 F19 F20. Aucun GO."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
    "dossiers":D/"P52Q_DOSSIERS_INSTRUCTION_VAGUE1.json",
    "references":D/"P52Q_REFERENCES_PRIMAIRES_VAGUE1.json",
    "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
    "p52p":D/"P52P_REGISTRE_COUVERTURE_ET_MANQUES.json",
    "p52o":D/"P52O_PLAN_ACQUISITION_PREUVES.json",
    "p52n":D/"P52N_CAHIER_MANDATS_ET_CONSULTATION.json",
    "p52j":D/"P52J_RELECTURE_PRIMAIRE_BUDGET_2026_2027.json",
    "p52k":D/"P52K_REGISTRE_PROVENANCE_BUDGET.json",
}
FIRST=("F01","F02","F03","F04","F07","F09","F19","F20")
REFS={
 "Q01":("https://laws-lois.justice.gc.ca/fra/const/section-92.html?wbdisable=true",("F01","F02"),"ARTICLE_92"),
 "Q02":("https://laws-lois.justice.gc.ca/fra/const/section-91.html",("F01","F02","F03"),"ARTICLE_91"),
 "Q03":("https://www.legisquebec.gouv.qc.ca/fr/document/lc/T-0.1/20260101?langCont=fr",("F01","F07"),"2026-01-01"),
 "Q04":("https://laws-lois.justice.gc.ca/fra/lois/E-15/index.html",("F02","F07"),"2026-09-21"),
 "Q05":("https://www.laws-lois.justice.gc.ca/fra/lois/C-54.011/index.html",("F03",),"2026-09-21"),
 "Q06":("https://www.legisquebec.gouv.qc.ca/fr/ShowDoc/cs/F-2.1",("F04","F07"),"2026-02-23"),
 "Q07":("https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier",("F04","F07"),"2024_PUBLICATIONS"),
 "Q08":("https://www.legisquebec.gouv.qc.ca/fr/document/lc/A-6.002/20260401",("F07","F20"),"2026-04-01"),
 "Q09":("https://www.legisquebec.gouv.qc.ca/fr/document/lc/C-64.1",("F19",),"2026-02-23"),
 "Q10":("https://www.legisquebec.gouv.qc.ca/fr/document/lc/A-2.1?langCont=fr",("F20",),"2026-02-23"),
 "Q11":("https://www.legisquebec.gouv.qc.ca/fr/document/lc/p-39.1",("F20",),"2026-02-23"),
 "Q12":("https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf",("F09",),"2026-03-18"),
 "Q13":("https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_Discours.pdf",("F09",),"2026-03-18"),
}
SOURCE_STATES={
    "CONSULTE_SOURCE_OFFICIELLE_EN_LIGNE",
    "IDENTIFIE_ET_RELUE_ASSISTEE_P52J",
}
TASKS=4
MAX_JSON=500000
def require(cond,why):
    if not cond:raise ValueError(why)
def load(p):
    f=Path(p)
    require(f.is_file() and not f.is_symlink() and f.stat().st_size<MAX_JSON,
            "JSON_ABSENT_OU_TROP_VOLUMINEUX")
    v=json.loads(f.read_text(encoding="utf-8"))
    require(type(v) is dict,"JSON_OBJET_REQUIS")
    return v

def verifier(doc):
    require(type(doc) is dict and set(doc)==set(FILES),"HUIT_SOURCES_ATTENDUES")
    d,s,a,p,o,n,j,k=(doc[name] for name in FILES)
    require(d.get("schema_version")=="P52Q-1" and
            d.get("jalon")=="P52Q" and
            d.get("date_reference")=="2026-10-19" and
            d.get("statut")=="HUIT_DOSSIERS_PRELIMINAIRES_NON_CERTIFIES" and
            d.get("preuves_premiere_vague")==list(FIRST),
            "DOSSIER_SCHEMA_INVALIDE")
    require(d.get("references")=={
       key:str(FILES[key].relative_to(ROOT))
       for key in ("p52a","p52p","p52o","p52n","p52j","p52k","references")},
       "P52Q_REFERENCES_INCOMPATIBLES")
    require(s.get("schema_version")=="P52Q-SOURCES-1" and
            s.get("jalon")=="P52Q" and
            s.get("date_consultation")=="2026-10-19" and
            s.get("statut")=="REFERENCES_OFFICIELLES_CONSULTEES_SANS_ARCHIVE_ORIGINALE" and
            s.get("sources_nouvelles_ajoutees_a_p52p_sans_pretendre_revision_p52p")==13 and
            s.get("originals_archives_certifies")==0 and
            s.get("expertises_independantes_obtenues")==0 and
            s.get("statut_versions_légales_a_reverifier") is True and
            s.get("lecture_original_pdf_reproduite_dans_ce_jalon") is False and
            s.get("publication_autorisee") is False and
            s.get("fusion_autorisee") is False and
            s.get("decision")=="NO_GO_AUTOMATIQUE",
            "SOURCES_NON_CERTIFIEES_REQUISES")
    require(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
            a.get("automatic_go") is False and
            a.get("financial_model_certified") is False and
            a.get("rates_selected") is False and
            a.get("human_reviews_received") is False,
            "P52A_FAUSSE_AUTORISATION")
    proof=a.get("required_evidence")
    require(type(proof) is list and len(proof)==20 and
            [q.get("id") for q in proof]==[
                "F%02d"%m for m in range(1,21)] and
            all(x.get("statut")=="NON_VALIDE" and
                x.get("preuve_independante_obtenue") is False and
                x.get("decision_autorisee") is False for x in proof),
            "P52A_PREUVE_FICTIVE")
    require(p.get("schema_version")=="P52P-1" and
            p.get("etat_verifie_par_sources_amont",{}).get("decision")==
                "NO_GO_AUTOMATIQUE" and
            [x.get("id") for x in p.get("exigences",[])]==
                [x["id"] for x in proof] and
            all(x.get("statut_juridique")=="NON_VALIDE" for x in p["exigences"]),
            "P52P_PREUVES_INCOHERENTES")
    require(o.get("schema_version")=="P52O-1" and
            o.get("gouvernance",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
            o.get("vagues",[])[0].get("preuves")==list(FIRST),
            "P52O_PREMIERE_VAGUE_MODIFIEE")
    require(n.get("schema_version")=="P52N-1" and
            n.get("controles_transversaux",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
            len(n.get("mandats",[]))==20 and
            all(x.get("expert_mandate") is False for x in n["mandats"]),
            "P52N_FAUX_MANDATS")
    require(j.get("schema_version")=="P52J-1" and
            len(j.get("source_primaires",[]))==2 and
            j.get("validation_de_nature",{}).get(
                "preuve_F09_independamment_attestee") is False and
            j["validation_de_nature"].get("verification_hash_pdf_original") is False,
            "P52J_FAUSSE_ATTESTATION")
    require(k.get("schema_version")=="P52K-1" and
            k.get("decision")=="NO_GO_AUTOMATIQUE" and
            len(k.get("fichiers_source",[]))==2 and
            all(x.get("empreinte_sha256_pdf_original") is None and
                x.get("attestation_externe_signee") is None for x in
                k["fichiers_source"]),
            "P52K_FAUSSE_ARCHIVE")
    sources=s.get("sources")
    require(type(sources) is list and len(sources)==len(REFS) and
            [x.get("id") for x in sources]==list(REFS),
            "TREIZE_REFERENCES_REQUISES")
    for x in sources:
        key=x["id"]
        url,ids,version=REFS[key]
        require(x.get("url")==url and
                x.get("preuves_associees")==list(ids) and
                x.get("version_visible_au_moment_de_consultation")==version and
                type(x.get("titre")) is str and
                len(x["titre"])>16 and
                type(x.get("avertissement_limites")) is str and
                len(x["avertissement_limites"])>35 and
                x.get("statut_reperage") in SOURCE_STATES and
                x.get("copie_originale_hors_git_obtenue") is False and
                x.get("sha256_octets_origine") is None and
                x.get("verification_version_par_second_lecteur") is False and
                x.get("interpretation_par_expert_independant") is False and
                x.get("certification_origine_documentaire") is False and
                x.get("preuve_F01_F20_certifiee") is False,
                "SOURCE_CERTIFIEE_OU_ALTEREE")
        if key in ("Q12","Q13"):
            require(x.get("nature")=="DOCUMENT_BUDGETAIRE_P52J" and
                    x.get("statut_reperage")==
                    "IDENTIFIE_ET_RELUE_ASSISTEE_P52J",
                    "PDF_BUDGET_PAS_RELECTURE_CETTE_FOIS")
        else:
            require(x.get("nature")!="DOCUMENT_BUDGETAIRE_P52J" and
                    x.get("statut_reperage")==
                    "CONSULTE_SOURCE_OFFICIELLE_EN_LIGNE",
                    "SOURCE_DECLAREE_NON_CONSULTEE")
    sourcebudget=j["source_primaires"]
    require(REFS["Q12"][0]==sourcebudget[1].get("url") and
            REFS["Q13"][0]==sourcebudget[0].get("url") and
            sourcebudget[0].get("id")=="DISC2026_T3" and
            sourcebudget[1].get("id")=="PLAN2026_F2",
            "RENVOI_P52J_ET_SOURCES_DIVERGENT")
    packets=d.get("dossiers")
    require(type(packets) is list and len(packets)==8 and
            [x.get("id") for x in packets]==list(FIRST),
            "HUIT_DOSSIERS_REQUIS")
    for packet in packets:
        key=packet["id"]
        arow=next(x for x in proof if x["id"]==key)
        prow=next(x for x in p["exigences"] if x["id"]==key)
        orow=next(x for x in o["preuves"] if x["id"]==key)
        nrow=next(x for x in n["mandats"] if x["id"]==key)
        srcs=[sid for sid,(url,ids,ver) in REFS.items() if key in ids]
        require(packet.get("regime")==arow["regime"] and
                packet.get("theme")==arow["theme"] and
                packet.get("statut_preuve_amont")=="NON_VALIDE" and
                packet.get("comite_pilote")==orow["comite_pilote"] and
                packet.get("consultations")==nrow["comites_consultes"] and
                packet.get("priorite_vague")=="V1" and
                packet.get("sources_precedemment_reperees")==
                    prow["pistes_sources_reperées"] and
                packet.get("nouveaux_reperes_officiels")==srcs and
                packet.get("objet_avis_humain_requis")==
                    arow["preuve_a_obtenir"] and
                type(packet.get("dossier_a_livrer")) is str and
                len(packet["dossier_a_livrer"])>35 and
                type(packet.get("travaux_requis")) is list and
                len(packet["travaux_requis"])==4 and
                all(type(t) is str and len(t)>40 for t in
                    packet["travaux_requis"]) and
                type(packet.get("reserves_particulieres")) is list and
                len(packet["reserves_particulieres"])>=1 and
                packet.get("pieces_recues_verifiees")==0 and
                packet.get("expert_reel_mandate") is False and
                packet.get("travaux_termines") is False and
                packet.get("contradiction_independante_obtenue") is False and
                packet.get("justificatif_signature_authentifie") is None and
                packet.get("evaluation_couts_certifiee") is False and
                packet.get("avis_favorable_recu") is False and
                packet.get("decision_adoption_autorisee") is False and
                packet.get("statut")=="DOSSIER_DOCUMENTAIRE_A_INSTRUIRE",
                "PREUVE_HUMAINE_OU_DOSSIER_NON_CONCORDANT")
    require(d.get("liste_des_controles_techniques") and
            len(d["liste_des_controles_techniques"])==8 and
            all(type(x) is str for x in d["liste_des_controles_techniques"]),
            "CONTRAINTES_INCOMPLETES")
    gov=d.get("gouvernance",{})
    require(gov.get("originaux_pdf_budget_hashes_verifies")==0 and
            gov.get("nombre_dossiers_prioritaires")==8 and
            gov.get("expertises_independantes_signées")==0 and
            gov.get("dossiers_avec_avis_externe_authentifie")==0 and
            gov.get("preuves_f01_f20_encore_non_validees")==20 and
            gov.get("variables_monetaires_inconnues_amont")==1320 and
            all(gov.get(t) is False for t in
                ("approbation_juridique_recue","publication_autorisee",
                 "fusion_autorisee","adoption_autorisee")) and
            gov.get("decision")=="NO_GO_AUTOMATIQUE",
            "NO_GO_NON_GARANTI")
    return {
      "jalon":"P52Q","schema_version":"P52Q-1",
      "dossiers_prioritaires":len(packets),
      "liens_officiels_a_analyser":len(sources),
      "nouveaux_reperes_pour_F19":sum(
           "F19" in x["preuves_associees"] for x in sources),
      "sources_budget_P52J_sans_nouvel_archivage":2,
      "taches_instruction_explicitement_documentees":
          sum(len(x["travaux_requis"]) for x in packets),
      "dossiers_avec_avis_independant_recu":0,
      "preuves_P52A_encore_non_validees":20,
      "hashes_originaux_certifies":0,
      "publication_autorisee":False,
      "adoption_autorisee":False,
      "fusion_autorisee":False,
      "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for k,p in FILES.items():parser.add_argument("--"+k,type=Path,default=p)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-expertises",action="store_true")
    args=parser.parse_args(argv)
    try:
        result=verifier({k:load(getattr(args,k)) for k in FILES})
        status=3 if args.exiger_expertises else 0
    except (OSError,ValueError,TypeError,UnicodeError,KeyError,IndexError) as exc:
        result={"jalon":"P52Q","statut":"REJET_TECHNIQUE",
                "categorie_erreur":type(exc).__name__,
                "publication_autorisee":False,
                "fusion_autorisee":False,
                "adoption_autorisee":False,
                "decision":"NO_GO_AUTOMATIQUE"}
        status=2
    output=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.rapport:
        try:
            args.rapport.parent.mkdir(parents=True,exist_ok=True)
            with args.rapport.open("x",encoding="utf-8") as f:f.write(output)
        except OSError:return 2
    else:print(output,end="")
    return status

if __name__=="__main__":
    sys.exit(main())
