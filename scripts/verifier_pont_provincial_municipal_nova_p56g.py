#!/usr/bin/env python3
"""P56G : relier des pièces provinciales/municipales sans simuler un appariement réel."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

SCHEMA = "P56G-1"
AMOUNT = re.compile(r"(?:0|[1-9]\d{0,14})\Z")
SOURCES = {
    "MUN_RAPPORT_2024":
        "https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-93042.pdf",
    "MAMH_ENGAGEMENTS_JUILLET_2024":
        "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/"
        "documents_administratifs/acces_information/engagements_financiers/2024/LIS_engagements_juillet_2024.pdf",
    "MAMH_ENGAGEMENTS_AVRIL_2024":
        "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/"
        "documents_administratifs/acces_information/engagements_financiers/2024/LIS_engagements_avril_2024.pdf",
    "MUNICIPALITE_COMMUNIQUE_2024": "https://www.ville.alma.qc.ca/rapport-financier-2024/"
}
MUNICIPAL = {
    "MUN_2024_COMPENSATIONS": ("5514445", "Compensations tenant lieu de taxes", "ligne 2"),
    "MUN_2024_TRANSFERTS": ("5578416", "Transferts", "ligne 4")
}
PROVINCIAL = {
    "PROV_2024_40350": ("3320039", "MAMH_ENGAGEMENTS_JUILLET_2024", "40350", "1193"),
    "PROV_2024_40561": ("1665580", "MAMH_ENGAGEMENTS_AVRIL_2024", "40561", "746")
}
HYPOTHESES = {
    "H01": ("PROV_2024_40350", "MUN_2024_COMPENSATIONS",
            "CANDIDAT_SOUS_CATEGORIE_DU_POSTE_MUNICIPAL"),
    "H02": ("PROV_2024_40561", "MUN_2024_TRANSFERTS",
            "CANDIDAT_SOUS_CATEGORIE_TRANSFERTS_MUNICIPAUX")
}
PIECES = {"G01", "G02", "G03", "G04", "G05"}
ABSENT = ("preuve_date_paiement", "preuve_piece_comptable_municipale",
          "preuve_contrepartie_identique", "preuve_montant_egal", "preuve_meme_periode",
          "montant_rapproche_cad", "montant_non_explique_cad")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def decimal_money(value):
    require(type(value) is str and AMOUNT.fullmatch(value), "MONTANT_EN_DOLLARS_ENTIERS_INVALIDE")
    return Decimal(value)


def verifier(data):
    require(isinstance(data, dict) and data.get("schema_version") == SCHEMA, "SCHEMA_INVALIDE")
    require(data.get("statut") == "DOSSIER_PILOTE_SOURCES_PUBLIQUES_NON_APPARIEES" and
            data.get("decision") == "NO_GO_AUTOMATIQUE", "FAUX_STATUT")
    m = data.get("municipalite")
    require(isinstance(m,dict) and m.get("nom")=="Alma" and m.get("code_mamh")=="93042"
            and m.get("territoire")=="QUEBEC_DANS_CANADA" and
            m.get("perimetre_bilan")=="VILLE_ALMA_CONSOLIDE" and
            m.get("exercice")=="2024-01-01/2024-12-31" and
            m.get("avis_professionnel_sur_nova") is False, "MUNICIPALITE_OU_EXERCICE_INVALIDE")
    sources=data.get("sources")
    require(isinstance(sources,dict) and set(sources)==set(SOURCES), "PROVENANCE_INCOMPLETE")
    for key,url in SOURCES.items():
        require(isinstance(sources[key],dict) and sources[key].get("url")==url,"SOURCE_INCONNUE")
    require(sources["MUN_RAPPORT_2024"].get("type")=="RAPPORT_FINANCIER_CONSOLIDE_2024" and
            sources["MUN_RAPPORT_2024"].get("date_attestation")=="2025-05-12" and
            sources["MUN_RAPPORT_2024"].get("reference_interne")=="S7 / État consolidé des résultats",
            "RAPPORT_FINANCIER_SOURCE_INVALIDE")
    for src,month,program in (
        ("MAMH_ENGAGEMENTS_JUILLET_2024","2024-07","40350"),
        ("MAMH_ENGAGEMENTS_AVRIL_2024","2024-04","40561")
    ):
        require(sources[src].get("type")=="LISTE_ENGAGEMENTS_FINANCIERS_2024_2025" and
                sources[src].get("mois_publication")==month and
                sources[src].get("programme")==program,"SOURCE_PROVINCIALE_HORS_PERIMETRE")
    mun_rows=data.get("donnees_municipales")
    prov_rows=data.get("donnees_provinciales")
    require(type(mun_rows) is list and len(mun_rows)==len(MUNICIPAL) and
            type(prov_rows) is list and len(prov_rows)==len(PROVINCIAL),"LIGNES_MANQUANTES")
    seen=set()
    for r in mun_rows:
        require(isinstance(r,dict),"LIGNE_MUNICIPALE_INVALIDE")
        k=r.get("id")
        require(type(k) is str and k in MUNICIPAL and k not in seen,"LIGNE_MUNICIPALE_DUPLIQUEE")
        seen.add(k)
        expected,libelle,num_ligne=MUNICIPAL[k]
        require(r.get("montant_cad")==expected and decimal_money(r.get("montant_cad"))==Decimal(expected)
                and r.get("poste")==libelle and num_ligne in r.get("rubrique","")
                and r.get("source_id")=="MUN_RAPPORT_2024"
                and r.get("nature")=="RECETTE_CONSOLIDEE_REALISATION_2024"
                and r.get("perimetre")=="VILLE_ALMA_CONSOLIDE"
                and r.get("exercice_fin")=="2024-12-31", "LIGNE_MUNICIPALE_NON_ATTESTEE")
    require(seen==set(MUNICIPAL),"CATEGORIE_MUNICIPALE_ABSENTE")
    seen=set()
    for r in prov_rows:
        require(isinstance(r,dict),"LIGNE_PROVINCIALE_INVALIDE")
        k=r.get("id")
        require(type(k) is str and k in PROVINCIAL and k not in seen,"LIGNE_PROVINCIALE_DUPLIQUEE")
        seen.add(k)
        amt,source,programme,ref=PROVINCIAL[k]
        require(r.get("montant_cad")==amt and decimal_money(r.get("montant_cad"))==Decimal(amt)
                and r.get("source_id")==source and r.get("programme")==programme
                and r.get("ligne_reference")==ref and r.get("entite_beneficiaire")=="Alma"
                and r.get("nature")=="ENGAGEMENT_OU_VERSEMENT_PUBLIE_SANS_PREUVE_DATE_PAIEMENT"
                and r.get("exercice_fin")=="2025-03-31",
                "LIGNE_PROVINCIALE_NON_ATTESTEE")
    require(seen==set(PROVINCIAL),"PROGRAMME_PROVINCIAL_ABSENT")
    totals=data.get("comptes_municipaux_controle_global")
    require(isinstance(totals,dict) and
            totals.get("source_id")=="MUN_RAPPORT_2024" and
            totals.get("excedent_budgetaire_de_fonctionnement_non_equivalent") is True,
            "ETATS_MUNICIPAUX_INCOMPLETS")
    revenus=decimal_money(totals.get("revenus_consolides_cad"))
    charges=decimal_money(totals.get("charges_consolidees_cad"))
    excedent=decimal_money(totals.get("excedent_comptable_cad"))
    require((revenus,charges,excedent)==
            (Decimal("93994134"),Decimal("89364728"),Decimal("4629406"))
            and revenus-charges==excedent,"ETATS_FINANCIERS_INCOHERENTS")
    h=data.get("hypotheses_appariement")
    require(type(h) is list and len(h)==len(HYPOTHESES),"HYPOTHESES_INCOMPLETES")
    seen=set()
    for x in h:
        require(isinstance(x,dict),"HYPOTHESE_INVALIDE")
        k=x.get("id")
        require(type(k) is str and k in HYPOTHESES and k not in seen,
                "HYPOTHESE_DUPLIQUEE_OU_INCONNUE")
        seen.add(k)
        require((x.get("source_province"),x.get("source_municipalite"),
                 x.get("classe_relation"))==HYPOTHESES[k],"APPARIEMENT_SANS_CAUSE")
        require(all(f in x and x[f] is None for f in ABSENT),
                "CONTREPARTIE_JUSTIFIEE_NON_DISPONIBLE")
        require(x.get("appariement_confirme") is False and
                isinstance(x.get("raison_non_appariement"),str) and
                len(x["raison_non_appariement"])>=85,"FAUX_RAPPROCHEMENT")
    require(seen==set(HYPOTHESES),"LIEN_NON_TESTE")
    c=data.get("contexte_comparaison")
    require(isinstance(c,dict) and c.get("exercices_compatibles_pour_transfert_direct") is False
            and c.get("sommes_agregees_et_lignes_de_programme_non_equivalentes") is True
            and c.get("libelle_versement_sur_liste_ne_prouve_pas_encaissement_municipal") is True
            and c.get("comparaison_arithmetique_residuelle_autorisee") is False
            and c.get("absence_double_compte_certifiee") is False,"PERIMETRE_NON_RECONCILIE")
    required=data.get("etape_suivante_pieces")
    require(type(required) is list and len(required)==len(PIECES) and
            {x.get("id") for x in required if isinstance(x,dict)}==PIECES and
            all(x.get("statut")=="NON_OBTENUE" for x in required),
            "JUSTIFICATIFS_NON_OBTENUS")
    require(data.get("autorisation_importation_p52b") is False and
            data.get("exercices_couverts_p52b_2027_2036")==0
            and data.get("p52b_montants_inconnus")==600
            and data.get("p52d_incidences_inconnues")==720
            and data.get("score_p55n_estime")==53
            and data.get("economie_nova_certifiee_cad") is None
            and data.get("reforme_fiscale_adoptee") is False
            and data.get("certification_nova") is False,"PREUVE_OU_ADOPTION_INVENTEE")
    require(data.get("controle_visualisation_pdf")==
            "CAPTURES_WEB_INDISPONIBLES_CACHE_MISS; EXTRACTION_TEXTE_INDEXEE_ET_PAGE_MUNICIPALE_OFFICIELLE_CONCORDE; PAS_DE_SHA_BINAIRE",
            "STATUT_VISUEL_NON_RESOLU")
    return {
        "jalon":"P56G", "schema_version":SCHEMA,
        "statut":"PIECES_HISTORIQUES_REPEREES_NON_APPARIEES",
        "municipalite":"Alma", "annee_civile_comptes":2024,
        "exercice_provincial":"2024-2025",
        "compensations_municipales_2024_cad":str(decimal_money(MUNICIPAL["MUN_2024_COMPENSATIONS"][0])),
        "transferts_municipaux_2024_cad":str(decimal_money(MUNICIPAL["MUN_2024_TRANSFERTS"][0])),
        "engagement_provincial_40350_cad":PROVINCIAL["PROV_2024_40350"][0],
        "engagement_provincial_40561_cad":PROVINCIAL["PROV_2024_40561"][0],
        "revenus_municipaux_consolides_cad":str(revenus),
        "charges_municipales_consolidees_cad":str(charges),
        "excedent_comptable_municipal_cad":str(excedent),
        "nombre_liens_appariemement_candidats":len(h),
        "liens_apparies_avec_preuves":0,
        "montant_apparie_cad":None,
        "ecart_de_contreparties_cad":None,
        "montants_disponibles_pour_projection_nova_2027_2036":0,
        "besoin_pieces_independantes":len(required),
        "examen_original_pdf_visuel_confirme":False,
        "taux_ou_economie_nova_certifiee":False,
        "inconnues_p52b":600, "incidences_inconnues_p52d":720,
        "p55n_maturite_estimee_pourcent":53, "decision":"NO_GO_AUTOMATIQUE"
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dossier",type=Path,required=True)
    p.add_argument("--rapport",type=Path)
    p.add_argument("--exiger-appariement-certifie",action="store_true")
    a=p.parse_args(argv)
    if a.exiger_appariement_certifie:
        print("NO_GO_AUTOMATIQUE: aucune contrepartie comptable attestee",file=sys.stderr)
        return 3
    try:
        data=json.loads(a.dossier.read_text(encoding="utf-8"))
        result=json.dumps(verifier(data),ensure_ascii=False,indent=2)+"\n"
        if a.rapport is None:
            print(result,end="")
        else:
            with a.rapport.open("x",encoding="utf-8") as f:
                f.write(result)
        return 0
    except (ValueError,TypeError,OSError,KeyError,json.JSONDecodeError) as exc:
        print("REFUS: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    sys.exit(main())
