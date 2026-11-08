#!/usr/bin/env python3
"""P56H: comparer des montants publics sur un même thème sans certifier une écriture réciproque."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

SCHEMA = "P56H-1"
NUM = re.compile(r"(?:0|[1-9][0-9]{0,14})\Z")
URLS = {
    "MUN_2024_S27": "https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-93042.pdf",
    "MAMH_JUILLET_2024_40350": "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/engagements_financiers/2024/LIS_engagements_juillet_2024.pdf",
    "MAMH_AVRIL_2024_40561": "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/engagements_financiers/2024/LIS_engagements_avril_2024.pdf"
}
MUNICIPAL = {
    "M_SANTE_S27_31": (31, 47, "1163325"),
    "M_CEGEP_S27_32": (32, 47, "576300"),
    "M_ECOLES_S27_33": (33, 47, "1580414"),
    "M_TVQ_S27_136": (136, 52, "1665578")
}
PROVINCIAL = {
    "P_40350": ("MAMH_JUILLET_2024_40350", "40350", 1193, "3320039"),
    "P_40561": ("MAMH_AVRIL_2024_40561", "40561", 746, "1665580")
}
CROSS = {
    "C_40350": (("M_SANTE_S27_31", "M_CEGEP_S27_32", "M_ECOLES_S27_33"),
                "P_40350", "CONCORDANCE_NUMERIQUE_EXACTE_NON_CERTIFICATION"),
    "C_40561": (("M_TVQ_S27_136",), "P_40561",
                "ECART_NUMERIQUE_DEUX_DOLLARS_NON_EXPLIQUE")
}
NULLS = ("preuve_date_paiement", "preuve_recette_municipale_meme_transaction",
         "avis_independant_signé")


def ensure(test, reason):
    if not test:
        raise ValueError(reason)


def cad(value):
    ensure(type(value) is str and bool(NUM.fullmatch(value)), "MONTANT_CAD_DECIMAL_INVALIDE")
    return Decimal(value)


def audit(data, p56g):
    ensure(isinstance(data, dict) and data.get("schema_version") == SCHEMA,
           "SCHEMA_INVALIDE")
    ensure(data.get("statut") ==
           "CONCORDANCES_ARITHMETIQUES_DOCUMENTEES_SANS_APPARIEMENT_COMPTABLE" and
           data.get("decision") == "NO_GO_AUTOMATIQUE", "GO_INJUSTIFIE")
    site=data.get("municipalite")
    ensure(isinstance(site,dict) and site.get("nom")=="Alma" and
           site.get("code_mamh")=="93042" and
           site.get("exercice_civil")=="2024-01-01/2024-12-31",
           "MUNICIPALITE_MILLESIME_INVALIDE")
    sources=data.get("sources")
    ensure(isinstance(sources,dict) and set(sources)==set(URLS), "SOURCES_INCOMPLETES")
    for k,url in URLS.items():
        ensure(isinstance(sources[k],dict) and sources[k].get("url")==url and
               sources[k].get("controle_image_originale")=="SCREENSHOT_WEB_ECHEC_CACHE_MISS",
               "CONTROLE_BINAIRE_NON_REALISE")
    ensure(sources["MUN_2024_S27"].get("nature_des_annexes")==
           "INFORMATIONS_COMPLEMENTAIRES_NON_AUDITEES" and
           sources["MUN_2024_S27"].get("pages_imprimees_s27")==[47,52] and
           sources["MUN_2024_S27"].get("verification_du_binaire_original_et_sha256") is False,
           "ANNEXE_NON_AUDITEE_ET_ORIGINAL_NON_VERIFIE")
    for k,program,line,page,exercise in [
        ("MAMH_JUILLET_2024_40350", "40350", 1193, 55, "2024-2025"),
        ("MAMH_AVRIL_2024_40561", "40561", 746, 49, "2024-2025")
    ]:
        x=sources[k]
        ensure(x.get("nature")=="LISTE_PROVINCIALE_ENGAGEMENTS_LIBELLE_VERSEMENT" and
               x.get("programme")==program and x.get("numero_ligne")==line and
               x.get("page_pdf_index_zero")==page and x.get("exercice")==exercise,
               "SOURCE_PROVINCIALE_INVALIDE")
    municipal_rows=data.get("rubriques_municipales_detaillees")
    ensure(isinstance(municipal_rows,list) and len(municipal_rows)==len(MUNICIPAL),
           "RUBRIQUES_MUNICIPALES_INCOMPLETES")
    mun={}
    for row in municipal_rows:
        ensure(isinstance(row,dict), "RUBRIQUE_NON_VALIDE")
        k=row.get("id")
        ensure(type(k) is str and k in MUNICIPAL and k not in mun, "RUBRIQUE_DUPLIQUEE")
        code,page,montant=MUNICIPAL[k]
        ensure(row.get("source_id")=="MUN_2024_S27" and
               row.get("ligne_s27")==code and row.get("page_imprimee")==page and
               row.get("comptes_annexe_statut")=="NON_AUDITE" and
               row.get("montant_realisation_2024_cad")==montant and
               cad(row["montant_realisation_2024_cad"])==Decimal(montant),
               "RUBRIQUE_2024_INCONNUE")
        mun[k]=cad(montant)
    ensure(set(mun)==set(MUNICIPAL), "RUBRIQUE_MANQUANTE")
    provincial_rows=data.get("lignes_provinciales")
    ensure(isinstance(provincial_rows,list) and len(provincial_rows)==len(PROVINCIAL),
           "PIECES_PROVINCIALES_INCOMPLETES")
    prov={}
    for row in provincial_rows:
        ensure(isinstance(row,dict),"PIECE_PROVINCIALE_INVALIDE")
        k=row.get("id")
        ensure(type(k) is str and k in PROVINCIAL and k not in prov,
               "PIECE_PROVINCIALE_DUPLIQUEE")
        src,program,ref,montant=PROVINCIAL[k]
        ensure(row.get("source_id")==src and row.get("programme")==program and
               row.get("numero_ligne")==ref and row.get("beneficiaire")=="Alma" and
               row.get("nature")=="ENGAGEMENT_MAMH_NON_PREUVE_PAIEMENT_DATE" and
               row.get("montant_publie_exercice_2024_2025_cad")==montant and
               cad(row["montant_publie_exercice_2024_2025_cad"])==Decimal(montant),
               "MONTANT_MINISTERIEL_NON_RECONNU")
        prov[k]=cad(montant)
    ensure(set(prov)==set(PROVINCIAL),"PIECE_PROVINCIALE_MANQUANTE")
    pairs=data.get("comparaisons")
    ensure(isinstance(pairs,list) and len(pairs)==len(CROSS),
           "COMPARAISONS_INCOMPLETES")
    diff={}
    for x in pairs:
        ensure(isinstance(x,dict),"COMPARAISON_INVALIDE")
        k=x.get("id")
        ensure(type(k) is str and k in CROSS and k not in diff,
               "COMPARAISON_DUPLIQUEE")
        components,prov_id,status=CROSS[k]
        ensure(x.get("municipal_ids")==list(components) and
               x.get("provincial_id")==prov_id and x.get("statut")==status and
               x.get("correspondance_comptable_confirmee") is False and
               all(n in x and x[n] is None for n in NULLS),
               "APPARIEMENT_COMPTABLE_NON_PROUVE")
        amount=sum((mun[i] for i in components),Decimal(0))
        variance=amount-prov[prov_id]
        ensure(cad(x.get("montant_municipal_agrege_cad"))==amount and
               cad(x.get("montant_provincial_cad"))==prov[prov_id] and
               x.get("ecart_municipal_moins_provincial_cad")==str(variance),
               "COMPARAISON_NUMERIQUE_FAUSSE")
        diff[k]=variance
    ensure(set(diff)==set(CROSS) and diff["C_40350"]==0 and
           diff["C_40561"]==Decimal("-2"),"ECART_NON_CONCORDE")
    ensure(isinstance(data.get("reservations"),list) and
           len(data["reservations"])>=8 and
           isinstance(data.get("pieces_manquantes"),list) and
           {x.get("id") for x in data["pieces_manquantes"] if isinstance(x,dict)}==
           {"H01","H02","H03","H04","H05"} and
           all(x.get("statut")=="NON_OBTENUE" for x in data["pieces_manquantes"]),
           "PIECES_INDEPENDANTES_ABSENTES")
    pg=data.get("controle_parallele_p56g")
    ensure(isinstance(pg,dict) and pg.get("liens_deja_certifies_p56g")==0 and
           pg.get("p56g_ne_pas_modifer_via_p56h") is True and
           pg.get("concordance_categorie_annee_2024") is True,"P56G_NON_RESPECTE")
    # Couplage au dossier P56G, tel que déposé, pour empêcher deux vérités incompatibles.
    ensure(isinstance(p56g,dict) and p56g.get("schema_version")=="P56G-1" and
           p56g.get("decision")=="NO_GO_AUTOMATIQUE" and
           p56g.get("score_p55n_estime")==53,"FICHIER_P56G_NON_CONCORDE")
    pm={x["id"]:x["montant_cad"] for x in p56g["donnees_municipales"]}
    pp={x["id"]:x["montant_cad"] for x in p56g["donnees_provinciales"]}
    ensure(pm.get("MUN_2024_COMPENSATIONS")=="5514445" and
           pm.get("MUN_2024_TRANSFERTS")=="5578416" and
           pp.get("PROV_2024_40350")==str(prov["P_40350"]) and
           pp.get("PROV_2024_40561")==str(prov["P_40561"]),
           "MONTANTS_P56G_DIVERGENTS")
    ensure(data.get("liens_arithmetiques_documentes")==2 and
           data.get("liens_comptables_appaires_et_certifies")==0 and
           data.get("montants_p52b_modifies")==0 and
           data.get("postes_p52b_inconnus")==600 and
           data.get("incidence_p52d_inconnues")==720 and
           data.get("pourcentage_estime_p55n")==53 and
           data.get("revenu_fiscal_nova_adopte") is False and
           data.get("decision_fiscale_autorisee") is False and
           data.get("economies_nova_certifiees_cad") is None,
           "MATURITE_OU_ECONOMIE_INVENTEE")
    return {
        "jalon":"P56H", "schema_version":SCHEMA,
        "statut":"CONCORDANCES_NUMERIQUES_PUBLIEES_SANS_CERTIFICATION_COMPTABLE",
        "territoire":"QUEBEC_DANS_CANADA", "annee_municipale":"2024",
        "exercice_provincial":"2024-2025",
        "somme_sante_cegeps_ecoles_municipale_cad":str(
            mun["M_SANTE_S27_31"]+mun["M_CEGEP_S27_32"]+mun["M_ECOLES_S27_33"]),
        "montant_provincial_programme_40350_cad":str(prov["P_40350"]),
        "difference_numerique_programme_40350_cad":str(diff["C_40350"]),
        "part_tvq_municipale_2024_cad":str(mun["M_TVQ_S27_136"]),
        "montant_provincial_programme_40561_cad":str(prov["P_40561"]),
        "difference_numerique_programme_40561_cad":str(diff["C_40561"]),
        "concordances_numeriques_documentees":2,
        "nombre_appariements_comptables_certifies":0,
        "cause_ecart_tvq_2_cad":None,
        "dates_encaissement_municipal_prouvees":False,
        "documents_binaries_controles_visuellement":False,
        "rubriques_s27_non_auditees":True,
        "economies_nova_certifiees_cad":None,
        "nombre_nouvelles_cellules_p52b_certifiees":0,
        "inconnues_p52b":600,"incidences_p52d_inconnues":720,
        "score_p55n_estime_pourcent":53,
        "decision":"NO_GO_AUTOMATIQUE"
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--decomposition",type=Path,required=True)
    p.add_argument("--pilote-p56g",type=Path,required=True)
    p.add_argument("--rapport",type=Path)
    p.add_argument("--exiger-appariement-certifie",action="store_true")
    a=p.parse_args(argv)
    if a.exiger_appariement_certifie:
        print("NO_GO_AUTOMATIQUE: égalité arithmétique n'est pas certification comptable",file=sys.stderr)
        return 3
    try:
        d=json.loads(a.decomposition.read_text(encoding="utf-8"))
        g=json.loads(a.pilote_p56g.read_text(encoding="utf-8"))
        out=json.dumps(audit(d,g),indent=2,ensure_ascii=False)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as f:
                f.write(out)
        else:
            print(out,end="")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as err:
        print("REFUS: "+str(err),file=sys.stderr)
        return 2


if __name__=="__main__":
    sys.exit(main())
