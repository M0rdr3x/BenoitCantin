#!/usr/bin/env python3
"""P56F: reference municipale 2023, enveloppes 2027 et quarantaine PDF 2025."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0,str(HERE))
from rapprocher_enveloppes_municipales_nova_p56e import auditer as p56e_auditer

SCHEMA="P56F-1"
REF2023=("https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/"
         "affaires-municipales/publications/finances_indicateurs_fiscalite/"
         "fiscalite/fiscalite_organismes_municipaux.pdf")
PDF2025=("https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/"
         "affaires-municipales/publications/finances_indicateurs_fiscalite/"
         "information_financiere/SOM_transferts_fiscaux.pdf")
NUM=re.compile(r"(?:0|[1-9][0-9]{0,6})(?:\.[0-9]{1,3})?\Z")
PORTFOLIO_2023={
    "TRANSPORT_COLLECTIF":("2118.4","transferts_conditionnels_partage_frais_mcad"),
    "EAU_ET_EGOUT":("1048.0","transferts_conditionnels_partage_frais_mcad"),
    "RESEAU_ROUTIER":("869.2","transferts_conditionnels_partage_frais_mcad")
}

def check(valid,reason):
    if not valid:
        raise ValueError(reason)

def val(d):
    check(type(d) is str and bool(NUM.fullmatch(d)),"CHAINE_DECIMALE_INVALIDE")
    return Decimal(d)

def controler(document,source2027):
    d=document
    check(isinstance(d,dict) and d.get("schema_version")==SCHEMA and
          d.get("territoire")=="QUEBEC_DANS_CANADA" and
          d.get("unite")=="M_CAD" and d.get("decision")=="NO_GO_AUTOMATIQUE",
          "EN_TETE_INVALIDE")
    check(d.get("p52b_inconnues_restantes")==600 and
          d.get("p52d_incidences_inconnues")==720 and
          d.get("preuves_p52a_non_validees")==20 and
          d.get("p55n_maturite_estimative")==53,"MATURITE_FICTIVE_INTERDITE")
    check(d.get("projections_p52b_modifiees") is False and
          d.get("taux_fiscaux_nova_adoptes") is False and
          d.get("economies_nova_certifiees_mcad") is None and
          d.get("financement_des_services_valide") is False,
          "FAUSSE_AUTORISATION")
    historic=d.get("serie_historique_2023")
    check(isinstance(historic,dict) and type(historic.get("annee")) is int
          and historic["annee"]==2023 and
          historic.get("type")=="AGREGAT_MUNICIPAL_RAPPORTE_NON_AUDIT_INDEPENDANT_NOVA",
          "HISTORIQUE_INVALIDE")
    source=historic.get("source")
    check(isinstance(source,dict) and source.get("url")==REF2023 and
          source.get("publication")=="2025-03" and
          source.get("organisme")=="Ministère des Affaires municipales et de l'Habitation" and
          "Transferts totaux" in source.get("section","") and
          source.get("note_source")=="Données 2023 compilées à partir des rapports reçus jusqu'au 30 janvier 2025",
          "REFERENCE_2023_NON_CONCORDEE")
    rights=val(historic.get("transferts_de_droits_inconditionnels_mcad"))
    conditional=val(historic.get("transferts_conditionnels_partage_frais_mcad"))
    total=val(historic.get("total_transferts_mcad"))
    check((rights,conditional,total)==(Decimal("763.6"),Decimal("5426.5"),Decimal("6190.1")),
          "DONNEES_2023_INATTENDUES")
    check(rights+conditional==total,"SOUS_TOTAUX_NON_RECONCILIES")
    percentages=historic.get("parts_publiees_pourcent")
    check(isinstance(percentages,dict) and percentages.get("droits")=="12.3" and
          percentages.get("partage_frais")=="87.7" and
          val(percentages["droits"])+val(percentages["partage_frais"])==100,
          "PARTS_PUBLIEES_INCOHERENTES")
    parts=historic.get("sous_categories_deja_incluses")
    check(isinstance(parts,list) and len(parts)==len(PORTFOLIO_2023),
          "POSTES_HISTORIQUES_INCOMPLETS")
    seen=set()
    for x in parts:
        check(isinstance(x,dict),"SOUS_POSTE_INVALIDE")
        key=x.get("id")
        check(type(key) is str and key in PORTFOLIO_2023 and key not in seen,
              "POSTE_HISTORIQUE_DUPLIQUE")
        seen.add(key)
        amount,parent=PORTFOLIO_2023[key]
        check(x.get("montant_mcad")==amount and x.get("dans")==parent,
              "ENVELOPPE_2023_MAL_CLASSIFIEE")
    check(historic.get("sources_municipales_sous_jacentes_individuellement_authentifiees_pour_nova")==0,
          "CONTREPARTIES_INVENTEES")
    forecast=d.get("previsions_2027")
    check(isinstance(forecast,dict) and
          type(forecast.get("annee_civile")) is int and forecast["annee_civile"]==2027 and
          forecast.get("type")=="QUATRE_ENVELOPPES_PREVISIONNELLES_PARTIELLES" and
          forecast.get("source_lien")==
          "projets/projet-nova/etudes/P56E_REGISTRE_TRANSFERTS_MUNICIPAUX_2027_ET_VERIFICATION_SOURCES.json",
          "SERIE_2027_INVALIDE")
    existing=p56e_auditer(source2027)
    check(forecast.get("sous_total_quatre_programmes_mcad")=="951.8" and
          val(forecast["sous_total_quatre_programmes_mcad"])==
          val(existing["sous_total_quatre_enveloppes_previsionnelles_mcad"]),
          "PREVISIONS_2027_NON_RAPPROCHEES")
    check(all(forecast.get(k) is None for k in (
        "total_transferts_2027_tous_programmes_mcad",
        "depenses_effectives_provinciales_2027_mcad",
        "recettes_effectives_municipales_2027_mcad")),
          "TOTAL_2027_OU_PAIEMENT_INVENTE")
    suspect=d.get("sommaire_2025")
    check(isinstance(suspect,dict) and suspect.get("url")==PDF2025 and
          suspect.get("libelle_page_web")=="Sommaire des transferts fiscaux 2025" and
          suspect.get("extraction_texte_web_2026_11_07")=="TABLE_2025" and
          suspect.get("rendu_visuel_web_2026_11_07")=="TABLE_2024" and
          suspect.get("qualification")=="QUARANTAINE_VERSION_MIXTE_OU_CACHE_NON_RESOLU" and
          suspect.get("autorisation_importation") is False and
          suspect.get("source_officielle_rejete_comme_2025") is False,
          "INCIDENT_VERSION_NON_TRAÇABLE")
    check(all(suspect.get(k) is None for k in (
        "verification_document_binaire_original",
        "empreinte_sha256_document_binaire",
        "cause_precise_divergence","montants_2025_importables")),
          "SOURCE_SOMMAIRE_NON_AUTHENTIFIEE")
    protocol=suspect.get("protocole_resolution")
    check(isinstance(protocol,list) and len(protocol)>=6 and
          all(type(x) is str and len(x)>30 for x in protocol),
          "PROCEDURE_RESOLUTION_INCOMPLETE")
    c=d.get("comparabilite")
    check(isinstance(c,dict) and all(c.get(k) is False for k in (
        "annees_identiques","perimetres_equivalents","categories_identiques",
        "statut_comptable_identique","ratio_2027_sur_2023_calculable",
        "croissance_2023_2027_demontree","incidence_reforme_nova_etablies")),
          "COMPARAISON_2023_2027_INVALIDE")
    check(c.get("unites_compatibles") is True,"UNITE_MCAD_NON_CONCORDEE")
    provenance=d.get("provenance_professionnelle")
    check(isinstance(provenance,dict) and all(provenance.get(k) is False for k in (
        "comptes_individuels_rendus_auditables_ici",
        "revue_par_comptable_municipal_independant",
        "sources_appariees_en_comptabilite_d_etat",
        "couverture_tous_programmes_2027")),
          "PREUVES_NON_OBTENUES")
    return {
        "jalon":"P56F","schema_version":SCHEMA,
        "decision":"NO_GO_AUTOMATIQUE",
        "statut":"BASE_HISTORIQUE_AGREGEE_ET_INCIDENT_2025_EN_ATTENTE",
        "reference_historique_2023_transferts_droits_mcad":str(rights),
        "reference_historique_2023_transferts_conditionnels_mcad":str(conditional),
        "reference_historique_2023_total_transferts_mcad":str(total),
        "source_historique_mamh_2023":REF2023,
        "enveloppes_quatre_programmes_2027_prevision_mcad":
            forecast["sous_total_quatre_programmes_mcad"],
        "somme_des_series_2023_2027":None,
        "taux_de_croissance_2023_2027":None,
        "montant_sommaire_2025_valide_mcad":None,
        "version_2025_a_resoudre":True,
        "comparaison_fiscale_nova_certifiee":False,
        "budget_decennal_renseigne_par_p56f":False,
        "economie_nova_certifiee_mcad":None,
        "p52b_valeurs_inconnues":600,"p52d_incidences_inconnues":720,
        "p55n_score_estime_pourcent":53
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historique",type=Path,required=True)
    p.add_argument("--previsions",type=Path,required=True)
    p.add_argument("--rapport",type=Path)
    p.add_argument("--exiger-faisabilite",action="store_true")
    a=p.parse_args(argv)
    if a.exiger_faisabilite:
        print("NO_GO_AUTOMATIQUE: aucune faisabilite Nova demontree",file=sys.stderr)
        return 3
    try:
        d=json.loads(a.historique.read_text(encoding="utf-8"))
        e=json.loads(a.previsions.read_text(encoding="utf-8"))
        result=json.dumps(controler(d,e),ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as f:
                f.write(result)
        else:
            print(result,end="")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
