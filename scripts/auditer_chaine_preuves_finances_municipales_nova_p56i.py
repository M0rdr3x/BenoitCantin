#!/usr/bin/env python3
"""P56I : controle de qualité des preuves, réserves d'audit et barrières NO_GO."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from verifier_correspondances_revenus_municipaux_nova_p56h import audit as p56h_audit

SCHEMA = "P56I-1"
URL_MUN = "https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-93042.pdf"
URL_JULY = ("https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/"
    "publications/documents_administratifs/acces_information/engagements_financiers/"
    "2024/LIS_engagements_juillet_2024.pdf")
URL_APRIL = ("https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/"
    "publications/documents_administratifs/acces_information/engagements_financiers/"
    "2024/LIS_engagements_avril_2024.pdf")
RISKS = {
    "I01":("OPINION_AUDIT_AVEC_RESERVE","CONSTAT_PUBLIE","RAPPORT_MUNICIPAL_S6"),
    "I02":("ANNEXE_S27_NON_AUDITEE","CONSTAT_PUBLIE","RAPPORT_MUNICIPAL_S27"),
    "I03":("ENGAGEMENT_NE_PROUVE_PAS_PAIEMENT","NON_DEMONTRE","MAMH_LISTES_2024"),
    "I04":("EXERCICES_NON_IDENTIQUES","NON_DEMONTRE","TOUTES_SOURCES"),
    "I05":("ECART_TVQ_DEUX_DOLLARS","NON_DEMONTRE","MAMH_LISTES_2024"),
    "I06":("ORIGINAL_PDF_NON_CONTROLE","NON_DEMONTRE","TOUTES_SOURCES"),
    "I07":("PERIMETRE_ET_TRANSFERTS","NON_DEMONTRE","TOUTES_SOURCES"),
    "I08":("APPARIEMENT_COMPTABLE","NON_DEMONTRE","TOUTES_SOURCES"),
    "I09":("FINANCEMENT_FISCAL_DECENNAL","NON_DEMONTRE","MODELES_NOVA")
}
EVIDENCE = {"H01","H02","H03","H04","H05"}


def check(test,msg):
    if not test:
        raise ValueError(msg)


def comparer(reg, h, g):
    prior=p56h_audit(h,g)
    check(isinstance(reg,dict) and reg.get("schema_version")==SCHEMA,
          "REGISTRE_P56I_INVALIDE")
    check(reg.get("statut")=="REVUE_CRITIQUE_DES_PREUVES_PUBLIQUES_SANS_CERTIFICATION_NOVA"
          and reg.get("decision")=="NO_GO_AUTOMATIQUE"
          and reg.get("territoire")=="QUEBEC_DANS_CANADA"
          and reg.get("jalon_precedent")=="P56H","STATUT_TERRITOIRE_INVALIDE")
    p=reg.get("perimetre")
    check(isinstance(p,dict) and p.get("municipalite")=="Alma"
          and p.get("code_mamh")=="93042"
          and p.get("annee_municipale")=="2024"
          and p.get("exercice_provincial")=="2024-2025","PERIMETRE_INVALIDE")
    sources=reg.get("sources")
    check(isinstance(sources,dict) and
          set(sources)=={"RAPPORT_MUNICIPAL_S6","RAPPORT_MUNICIPAL_S27","MAMH_LISTES_2024"},
          "SOURCES_INATTENDUES")
    s6=sources["RAPPORT_MUNICIPAL_S6"]
    s27=sources["RAPPORT_MUNICIPAL_S27"]
    ministry=sources["MAMH_LISTES_2024"]
    check(s6.get("url")==URL_MUN and s6.get("type")=="ETATS_CONSOLIDES_AUDITES_AVEC_RESERVE"
          and s6.get("opinion_audit")=="AVEC_RESERVE" and
          s6.get("section")=="S6 pages 1 à 4" and
          "SP 3280" in s6.get("reserve","") and
          s6.get("audit_Nova") is False,
          "RESERVE_AUDIT_MUNICIPAL_OMISE")
    check(s27.get("url")==URL_MUN and s27.get("type")==
          "INFORMATIONS_COMPLEMENTAIRES_NON_AUDITEES" and
          s27.get("section")=="S27, pages imprimées 47 et 52" and
          s27.get("audit_Nova") is False,
          "ANNEXE_NON_AUDITEE_TROMPEUSE")
    check(ministry.get("juillet_url")==URL_JULY and
          ministry.get("avril_url")==URL_APRIL and
          ministry.get("type")=="ENGAGEMENTS_FINANCIERS_MINISTERIELS" and
          ministry.get("preuve_date_encaissement") is False,
          "LIGNES_MINISTERIELLES_HORS_PREUVE")
    maps=reg.get("correspondances")
    check(isinstance(maps,dict) and set(maps)=={"PROGRAMME_40350","PROGRAMME_40561"},
          "MAPPAGES_INCOMPLETS")
    a,b=maps["PROGRAMME_40350"],maps["PROGRAMME_40561"]
    check(a.get("recette_s27_31_33_cad")=="3320039" and
          a.get("engagement_ministeriel_cad")=="3320039" and
          a.get("difference_cad")=="0" and
          a.get("concordance_arithmetique") is True and
          a.get("preuve_comptabilite_reciproque") is False,
          "40350_CERTIFICATION_INVENTEE")
    check(b.get("recette_s27_136_cad")=="1665578" and
          b.get("engagement_ministeriel_cad")=="1665580" and
          b.get("difference_cad")=="-2" and
          b.get("concordance_arithmetique_exacte") is False and
          b.get("preuve_comptabilite_reciproque") is False and
          b.get("cause_ecart_cad") is None,
          "40561_ECART_NON_RESOLU")
    check(Decimal(a["recette_s27_31_33_cad"])-
          Decimal(a["engagement_ministeriel_cad"])==0 and
          Decimal(b["recette_s27_136_cad"])-
          Decimal(b["engagement_ministeriel_cad"])==Decimal("-2"),
          "ARITHMETIQUE_INVALIDE")
    check(prior["somme_sante_cegeps_ecoles_municipale_cad"]==a["recette_s27_31_33_cad"] and
          prior["part_tvq_municipale_2024_cad"]==b["recette_s27_136_cad"] and
          prior["nombre_appariements_comptables_certifies"]==0,
          "P56H_ET_P56I_NON_CONCORDANTS")
    audit=reg.get("audit_contradictoire")
    check(isinstance(audit,dict) and
          audit.get("documents_binaries_originaux_disponibles") is False and
          all(audit.get(k)==0 for k in (
              "empreintes_sha256_verifiees",
              "pages_comparees_visuellement_sur_meme_binaire",
              "dates_paiements_et_pieces_confirmees",
              "avis_sur_projet_nova_signes",
              "preuves_contreparties_certifiees")),
          "JUSTIFICATIFS_NON_OBTENUS_DECLARES_OBTENUS")
    risks=reg.get("risques")
    check(isinstance(risks,list) and len(risks)==len(RISKS),
          "NOMBRE_CONTROLES_INVALIDE")
    ids=set()
    for row in risks:
        check(isinstance(row,dict),"RISQUE_MAL_FORME")
        k=row.get("id")
        check(type(k) is str and k in RISKS and k not in ids, "RISQUE_DUPLIQUE")
        ids.add(k)
        expected=RISKS[k]
        check((row.get("code"),row.get("etat"),row.get("source"))==expected,
              "CONTROLE_NON_TRAÇABLE")
        check(isinstance(row.get("constat"),str) and len(row["constat"])>=30 and
              isinstance(row.get("consequence"),str) and len(row["consequence"])>=40 and
              isinstance(row.get("expert_responsable_requis"),str) and
              len(row["expert_responsable_requis"])>=8 and
              row.get("preuve_contradiction_obtenue") is False and
              row.get("conclusion_financement_nova_autorisee") is False,
              "JUSTIFICATION_OU_PREUVE_FICTIVE")
    check(ids==set(RISKS),"CONTROLES_ABSENTS")
    check(reg.get("nombre_controles")==len(RISKS) and
          reg.get("nb_constats_publics")==2 and
          reg.get("nb_controles_non_demontres")==7,"SUIVI_INCOHERENT")
    evidences=reg.get("pieces_a_obtenir")
    check(isinstance(evidences,list) and len(evidences)==len(EVIDENCE) and
          {x.get("id") for x in evidences if isinstance(x,dict)}==EVIDENCE and
          all(x.get("preuve_id") is None and x.get("statut")=="NON_OBTENUE"
              and len(x.get("nature",""))>=50 for x in evidences),
          "PIECES_ATTESTEES_SANS_SOURCE")
    check(reg.get("score_p55n_estime")==53 and
          reg.get("p52b_champs_inconnus")==600 and
          reg.get("p52d_incidences_inconnues")==720 and
          reg.get("p52a_preuves_non_validees")==20 and
          reg.get("reformes_fiscales_adoptees") is False and
          reg.get("nouvelles_economies_certifiees_cad") is None and
          reg.get("budget_nova_decennal_certifie") is False and
          reg.get("validation_independante_nova") is False and
          reg.get("transposition_budgetaire_2027_2036") is False,
          "MATURITE_OU_ECONOMIE_NON_FONDEE")
    return {
        "jalon":"P56I","schema_version":SCHEMA,
        "statut":"REVUE_PROBANTE_DOCUMENTAIRE_NON_AUDIT_EXTERNE",
        "nombre_controles":len(RISKS),"constats_documentaires_verifies":2,
        "chantiers_preuve_non_resolus":7,
        "documents_binaires_originaux_authentifies":0,
        "pieces_de_contrepartie_manquantes":len(EVIDENCE),
        "rapport_municipal_audit_avec_reserve":True,
        "annexe_s27_auditee":False,
        "concordances_numeriques":2,
        "concordance_exacte_40350_cad":"0",
        "ecart_40561_non_explique_cad":"-2",
        "appariements_comptables_certifies":0,
        "nouvelles_economies_nova_certifiees_cad":None,
        "nouvelles_cellules_p52b_renseignees":0,
        "p52b_champs_inconnus":600,"p52d_incidences_inconnues":720,
        "p55n_score_estimatif":53,
        "decision":"NO_GO_AUTOMATIQUE"
    }


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registre",required=True,type=Path)
    ap.add_argument("--p56h",required=True,type=Path)
    ap.add_argument("--p56g",required=True,type=Path)
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--exiger-certification",action="store_true")
    args=ap.parse_args(argv)
    if args.exiger_certification:
        print("NO_GO_AUTOMATIQUE: preuves et avis indépendants manquants",file=sys.stderr)
        return 3
    try:
        def load(p):
            return json.loads(p.read_text(encoding="utf-8"))
        result=json.dumps(comparer(load(args.registre),load(args.p56h),load(args.p56g)),
                          ensure_ascii=False,indent=2)+"\n"
        if args.rapport:
            with args.rapport.open("x",encoding="utf-8") as file:
                file.write(result)
        else:
            print(result,end="")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2


if __name__=="__main__":
    sys.exit(main())
