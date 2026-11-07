#!/usr/bin/env python3
"""P52R : verifie tables budgetaires publiques et octets PDF locaux non attestes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"projets"/"projet-nova"/"etudes"
FILES={
    "p52r":D/"P52R_RECONCILIATION_ET_RECEPTION_ORIGINAUX.json",
    "p52c":D/"P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json",
    "p52j":D/"P52J_RELECTURE_PRIMAIRE_BUDGET_2026_2027.json",
    "p52k":D/"P52K_REGISTRE_PROVENANCE_BUDGET.json",
    "p52q":D/"P52Q_DOSSIERS_INSTRUCTION_VAGUE1.json",
    "p52a":D/"P52A_REGISTRE_PREUVES_FISCALES.json",
}
SOURCE_KEYS=("DISC2026_T3","PLAN2026_F2")
SOURCE_URLS=(
 "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_Discours.pdf",
 "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf"
)
IDS={
 "group_income":("impot_particuliers","cotisations_sante","impot_societes","foncier_scolaire"),
 "group_consumption":("taxes_vente","carburants","tabac","alcool","consommation_autres"),
 "group_business":("hydro","loto","saq","iq","sqdc","entreprises_autres"),
 "group_non_tax":("droits_redevances","revenus_divers"),
 "group_federal":("perequation","sante_federal","social_federal","autres_federaux")
}
# Independently transcribed from the official published images 2026-10-20
OFFICIAL_LINES={
 "group_income":(50800,9412,14527,1311),
 "group_consumption":(26349,2097,830,574,158),
 "group_business":(2445,1557,1406,292,146,7),
 "group_non_tax":(6542,15908),
 "group_federal":(13907,9265,1392,7567),
}
OFFICIAL_TOTALS={
 "impots_sur_revenu_et_biens":76050,
 "taxes_consommation":30008,
 "entreprises_gouvernement":5853,
 "droits_permis_redevances":6542,
 "revenus_divers":15908,
 "transferts_federaux":32131,
 "revenus_autonomes":134361,
 "revenus_totaux":166492
}
SIGNED={
 "revenus_autonomes":134361,
 "transferts_federaux":32131,
 "revenus_totaux":166492,
 "depenses_portefeuilles":-160489,
 "service_dette":-10268,
 "depenses_totales":-170757,
 "provision_eventualites":-2000,
 "deficit_comptable":-6265,
 "versements_fonds_generations":-2347,
 "solde_budgetaire_loi_equilibre":-8612
}
PASSAGES={
 "impots_sur_revenu_et_biens":76050,
 "taxes_consommation":30008,
 "entreprises_gouvernement":5853,
 "revenus_autonomes":134361,
 "transferts_federaux":32131,
 "revenus_totaux":166492,
 "depenses_totales":-170757,
 "solde_avant_provision":-4265,
 "deficit_comptable":-6265,
 "solde_budgetaire_loi_equilibre":-8612
}
EXPECTED_FLAGS={
 "liens_sources_ne_sont_pas_fichiers_authentifies",
 "protocole_http_brut_sha256_indisponible_dans_cet_environnement",
 "empreintes_pdf_originaux_non_calculees",
 "verification_cryptographique_vers_organisme_officiel_non_effectuee",
 "comparaison_nouvelle_version_publiee_non_effectuee",
 "chiffres_previsions_et_non_realises",
 "montants_du_modele_fiscal_nova_non_certifies",
 "recettes_fiscales_federales_pas_revenus_provinciaux",
 "transferts_federaux_non_presumes_en_cas_de_souverainete",
 "aucun_montant_p52b_ou_p52d_complete",
 "aucun_avis_independant_authentifie"
}

def must(cond,message):
    if not cond:raise ValueError(message)
def read(path):
    p=Path(path)
    must(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<500000,
         "JSON_MISSING_OR_BAD_SIZE")
    data=json.loads(p.read_text(encoding="utf-8"))
    must(type(data) is dict,"JSON_OBJECT_REQUIRED")
    return data
def n(v):
    must(type(v) is str and re.fullmatch(r"-?(0|[1-9][0-9]{0,9})",v),
         "NOT_AN_INTEGER_STRING")
    return int(v)
def check(data):
    must(type(data) is dict and set(data)==set(FILES),"SIX_SOURCES_REQUIRED")
    r,c,j,k,q,a=(data[x] for x in FILES)
    must(r.get("schema_version")=="P52R-1" and
         r.get("jalon")=="P52R" and
         r.get("statut")=="CONCORDANCE_ARITHMETIQUE_OBSERVEE_SANS_RECEPTION_DES_PDF_ORIGINAUX" and
         r.get("perimetre")=="Prévisions officielles du budget du Québec 2026-2027, uniquement" and
         r.get("date_reference")=="2026-10-20",
         "P52R_SCHEMA_INVALID")
    must(r.get("references_amont")=={
        key:str(FILES[key].relative_to(ROOT)) for key in FILES if key!="p52r"
    },"REFERENCES_BROKEN")
    must(a.get("status")=="PROPOSITION_NON_ADOPTEE" and
         a.get("automatic_go") is False and
         a.get("rates_selected") is False and
         a.get("financial_model_certified") is False and
         [p.get("id") for p in a.get("required_evidence",[])]==[
            "F%02d"%i for i in range(1,21)] and
         all(p.get("statut")=="NON_VALIDE" and
             p.get("preuve_independante_obtenue") is False for p in a["required_evidence"]),
         "P52A_APPROVAL_FABRICATED")
    must(c.get("schema_version")=="P52C-1" and
         c.get("statut")=="REFERENCE_OFFICIELLE_MARS_2026_PREVISION_NON_REALISEE" and
         c.get("decision")=="NO_GO_AUTOMATIQUE" and
         c.get("hypotheses_nova_certifiees") is False,
         "P52C_APPROVAL_FABRICATED")
    must(j.get("schema_version")=="P52J-1" and
         j.get("validation_de_nature",{}).get("decision")=="NO_GO_AUTOMATIQUE" and
         j["validation_de_nature"].get("preuve_F09_independamment_attestee") is False and
         j["validation_de_nature"].get("verification_hash_pdf_original") is False,
         "P52J_PROOF_FABRICATED")
    must(k.get("schema_version")=="P52K-1" and
         k.get("decision")=="NO_GO_AUTOMATIQUE" and
         q.get("schema_version")=="P52Q-1" and
         q.get("gouvernance",{}).get("decision")=="NO_GO_AUTOMATIQUE",
         "P52K_Q_INCONSISTENT")
    orig=r.get("origine_constats")
    cs=c.get("sources")
    js=j.get("source_primaires")
    ks=k.get("fichiers_source")
    must(all(type(x) is list and len(x)==2 for x in (orig,cs,js,ks)),
         "TWO_ORIGINAL_REFERENCES_REQUIRED")
    for i in range(2):
        must(orig[i].get("id")==cs[i].get("id")==js[i].get("id")==ks[i].get("id")==SOURCE_KEYS[i] and
             orig[i].get("url")==cs[i].get("url")==js[i].get("url")==ks[i].get("url")==SOURCE_URLS[i] and
             orig[i].get("tableau")==cs[i].get("tableau")==js[i].get("tableau")==ks[i].get("tableau") and
             orig[i].get("page_imprimee")==cs[i].get("page_imprimee")==js[i].get("page_imprimee")==ks[i].get("page_imprimee") and
             orig[i].get("page_pdf_index_zero")==js[i].get("page_pdf_index_zero")==ks[i].get("page_pdf_index_zero") and
             orig[i].get("nombre_pages_rapporte_par_lecteur_web")==[34,426][i] and
             orig[i].get("statut")=="CAPTURE_VISUELLE_DU_TABLEAU_SANS_FICHIER_ORIGINAL" and
             orig[i].get("sha256_original") is None and
             orig[i].get("fichier_original_telecharge") is False and
             orig[i].get("examen_expert_independant") is False and
             ks[i].get("empreinte_sha256_pdf_original") is None and
             ks[i].get("acquisition_document_origine")=="NON_EFFECTUEE" and
             ks[i].get("attestation_externe_signee") is None,
             "PDF_DOCUMENTARY_STATUS_MISMATCH")
    lines=r.get("figures_lues_depuis_images_publiees_mcad")
    must(type(lines) is dict and tuple(lines)==tuple(IDS),"MISSING_FIGURE_GROUP")
    flattened={}
    for grp,ids in IDS.items():
        row=lines[grp]
        must(type(row) is dict and tuple(row)==ids,"MISSING_FIGURE_LINE")
        for name,value in zip(ids,OFFICIAL_LINES[grp]):
            must(type(row[name]) is int and row[name]==value,"FIGURE_CHANGED")
            flattened[name]=value
    actual=j.get("transcription_discours_tableau3",{}).get("lignes_revenus")
    ref=c.get("lignes_revenus")
    must(type(actual) is list and type(ref) is list and
         len(actual)==len(ref)==len(flattened)==21,"REVENUE_LINE_COUNT")
    for x,y in zip(actual,ref):
        name=x.get("id")
        must(name==y.get("id") and
             name in flattened and
             n(x.get("valeur_mcad"))==n(y.get("valeur_mcad"))==flattened[name],
             "SOURCE_LINE_DISAGREEMENT")
    totals=r.get("agrege_officiel_2026_2027_mcad")
    disc=j["transcription_discours_tableau3"]["sous_totaux_officiels_mcad"]
    cref=c.get("sous_totaux_officiels_mcad")
    must(type(totals) is dict and type(disc) is dict and type(cref) is dict,
         "TOTALS_MISSING")
    must(tuple(disc)==tuple(cref)==tuple(OFFICIAL_TOTALS),"GROUP_TOTALS_INCOMPLETE")
    for key,value in OFFICIAL_TOTALS.items():
        must(type(totals.get(key)) is int and totals[key]==value and
             n(disc[key])==n(cref[key])==value,
             "OFFICIAL_GROUP_TOTAL_ALTERED")
    checks={
      "impots_sur_revenu_et_biens":sum(lines["group_income"].values()),
      "taxes_consommation":sum(lines["group_consumption"].values()),
      "entreprises_gouvernement":sum(lines["group_business"].values()),
      "revenus_autonomes":sum(lines["group_income"].values())+
          sum(lines["group_consumption"].values())+
          sum(lines["group_business"].values())+
          sum(lines["group_non_tax"].values()),
      "transferts_federaux":sum(lines["group_federal"].values())
    }
    checks["revenus_totaux"]=checks["revenus_autonomes"]+checks["transferts_federaux"]
    f2=j["transcription_plan_budgetaire_f2"]["montants_signes_comme_affiches_mcad"]
    must(type(f2) is dict and tuple(f2)==tuple(SIGNED),"SIGNED_LINES_COUNT")
    amount=r["agrege_officiel_2026_2027_mcad"]
    must(len(amount)==len(OFFICIAL_TOTALS)+7,"R_AGGREGATE_COUNT")
    for key,val in SIGNED.items():
        must(type(amount.get(key)) is int and amount[key]==val and
             n(f2[key])==val,"F2_SIGN_OR_VALUE_CHANGED")
    expenditure=c.get("depenses_et_ajustements_officiels_mcad")
    must(type(expenditure) is dict,"C_EXPENSES_MISSING")
    for key in ("depenses_portefeuilles","service_dette","depenses_totales",
                "provision_eventualites","versements_fonds_generations"):
        must(n(expenditure[key])==-SIGNED[key],"P52C_NEGATIVE_SIGNS")
    for key in ("deficit_comptable","solde_budgetaire_loi_equilibre"):
        must(n(expenditure[key])==SIGNED[key],"P52C_DEFICIT_SIGNS")
    checks["depenses_totales"]=SIGNED["depenses_portefeuilles"]+SIGNED["service_dette"]
    checks["solde_avant_provision"]=checks["revenus_totaux"]+checks["depenses_totales"]
    checks["deficit_comptable"]=checks["solde_avant_provision"]+SIGNED["provision_eventualites"]
    checks["solde_budgetaire_loi_equilibre"]=checks["deficit_comptable"]+SIGNED["versements_fonds_generations"]
    must(checks==PASSAGES and
         r.get("rapprochements_attendus_mcad")==PASSAGES,
         "RECONCILIATION_FAILED")
    limits=r.get("limitations",{})
    must(type(limits) is dict and set(limits)==EXPECTED_FLAGS and
         all(limits[k] is True for k in EXPECTED_FLAGS),"CAUTION_FLAGS_REMOVED")
    local=r.get("traitement_local_hors_git",{})
    must(local.get("pdf_validation_formelle")=="NON_ASSUREE_PAR_CONTROLES_DE_SIGNATURES" and
         local.get("aucune_preuve_identite_officielle_deduite_du_hash") is True and
         local.get("aucun_original_ou_nom_personnel_publie_par_workflow") is True and
         local.get("rapport_local_sha256_n_est_pas_attestation_independante") is True,
         "FALSE_PDF_AUTHENTICATION_CLAIM")
    state=r.get("etat_dossiers",{})
    must(state.get("F09")=="NON_VALIDE" and
         state.get("F01_F20_attestations_independantes")==0 and
         state.get("originaux_pdf_2026_2027_archives_avec_preuve")==0 and
         state.get("montants_financiers_nova_toujours_inconnus")==1320 and
         state.get("expertise_publique_certifiee") is False and
         all(state.get(k) is False for k in
             ("fusion_autorisee","publication_autorisee","adoption_autorisee")) and
         state.get("decision")=="NO_GO_AUTOMATIQUE",
         "FAKE_GO")
    return {
      "jalon":"P52R","schema_version":"P52R-1",
      "lignes_budget_discours_controlees":len(flattened),
      "sous_totaux_budget_discours_controles":len(OFFICIAL_TOTALS),
      "agregats_signes_plan_controles":len(SIGNED),
      "identites_arithmetiques_confirmees":len(PASSAGES),
      "rapprochements_numeriques_coherents":True,
      "fichiers_pdf_originaux_dans_le_depot":0,
      "pdf_originaux_autentifies":0,
      "preuves_independantes_F01_F20_validees":0,
      "montants_nova_financiers_inconnus":1320,
      "publication_autorisee":False,
      "fusion_autorisee":False,
      "adoption_autorisee":False,
      "decision":"NO_GO_AUTOMATIQUE"
    }

def read_pdf_receipt(path):
    p=Path(path)
    must(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=80000000,
         "PDF_LOCAL_ABSENT_OU_TROP_GRAND")
    with p.open("rb") as stream:
        start=stream.read(12)
        must(start.startswith(b"%PDF-"),"NOT_PDF_HEADER")
        stream.seek(-min(p.stat().st_size,4096),2)
        end=stream.read()
        must(b"%%EOF" in end,"PDF_MISSING_END_MARKER")
        stream.seek(0)
        digest=hashlib.sha256()
        length=0
        while True:
            block=stream.read(1024*1024)
            if not block:break
            length+=len(block)
            digest.update(block)
    return {"taille_octets":length,"sha256_octets_lus":digest.hexdigest(),
            "integrite_structurelle_pdf_complete_attestee":False,
            "authenticite_ministerielle_attestee":False}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for key,path in FILES.items():
        parser.add_argument("--"+key,type=Path,default=path)
    parser.add_argument("--discours-fichier",type=Path)
    parser.add_argument("--plan-fichier",type=Path)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-originaux",action="store_true")
    parser.add_argument("--exiger-expertise",action="store_true")
    args=parser.parse_args(argv)
    try:
        result=check({key:read(getattr(args,key)) for key in FILES})
        has_discours=args.discours_fichier is not None
        has_plan=args.plan_fichier is not None
        must(has_discours==has_plan,"BOTH_PDF_FILES_REQUIRED")
        if has_discours:
            must(args.discours_fichier.resolve()!=args.plan_fichier.resolve(),
                 "TWO_DISTINCT_PDF_FILES_REQUIRED")
            result["reception_octets_locale_non_attestee"]={
                "discours":read_pdf_receipt(args.discours_fichier),
                "plan":read_pdf_receipt(args.plan_fichier)}
        else:
            result["reception_octets_locale_non_attestee"]=None
        result["pdf_originaux_autentifies"]=0
        result["adoption_autorisee"]=False
        status=3 if args.exiger_expertise or (
            args.exiger_originaux and not has_discours) else 0
    except (ValueError,OSError,UnicodeError,TypeError,KeyError) as exc:
        result={"jalon":"P52R","statut":"ECHEC_VALIDATION",
                "categorie_erreur":type(exc).__name__,
                "fusion_autorisee":False,"adoption_autorisee":False,
                "publication_autorisee":False,"decision":"NO_GO_AUTOMATIQUE"}
        status=2
    body=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.rapport:
        try:
            args.rapport.parent.mkdir(parents=True,exist_ok=True)
            with args.rapport.open("x",encoding="utf-8") as handle:handle.write(body)
        except OSError:return 2
    else:print(body,end="")
    return status

if __name__=="__main__":
    sys.exit(main())
