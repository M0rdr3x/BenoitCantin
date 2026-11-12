#!/usr/bin/env python3
"""P55U : profils officiels de 2026, jamais des gains de la politique Nova.

La mise a jour de novembre 2025 couvre des mesures moins larges que la
page gouvernementale actualisee en juin 2026. Ne pas soustraire 245 de 847
pour estimer l'effet d'une reforme; ne pas fusionner les deux perimetres.
"""
import argparse
import json
from pathlib import Path
import sys

import valider_temoin_revenu_disponible_2026_nova_p55t as p55t

BASE=p55t.ROOT/"projets"/"projet-nova"/"etudes"
CONFIG=BASE/"P55U_PROFILS_OFFICIELS_2026_MENAGES_PME.json"
NO_GO="NO_GO_AUTOMATIQUE"
SOURCE_PDF=("https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/"
            "publications-adm/Mise_a_jour_economique/2025/FR/"
            "AUTFR_lepointNov2025.pdf")
FIELDS=("impot_revenu","prestations_aide_sociale","credit_solidarite",
        "allocation_famille","rrq","rqap")
PROFILE_SPEC=(
    ("U01","PERSONNE_SEULE_AIDE_SOCIALE",0,1,0,
     (None,192,25,None,None,None),217),
    ("U02","TRAVAILLEUR_SEUL",50000,1,0,
     (87,None,79,None,47,32),245),
    ("U03","FAMILLE_MONOPARENTALE_ENFANT",50000,1,1,
     (87,None,82,115,47,32),363),
    ("U04","COUPLE_DEUX_JEUNES_ENFANTS",100000,2,2,
     (115,None,None,168,93,64),440),
)
PME={
    "profil":"PME_10_EMPLOYES_55000_CAD_PAR_EMPLOYE",
    "employes":10,"salaire_unitaire_annuel_cad":55000,
    "annee_reference":2025,"annee_comparee":2026,
    "rrq_employeur_2025_cad":27810,"rrq_employeur_2026_cad":27295,
    "rqap_employeur_2025_cad":3806,"rqap_employeur_2026_cad":3311,
    "rrq_variation_reduction_cad":515,
    "rqap_variation_reduction_cad":495,
    "cotisations_totales_2025_cad":31616,
    "cotisations_totales_2026_cad":30606,
    "reduction_cotisations_cad":1010,
    "condition":"BAISSES_COTISATIONS_RRQ_RQAP_QUEBEC_ACTUEL_NON_GAIN_NOVA",
    "non_projection_emplois_salaire_et_prix":True,
}
REQUIRED_SAFE={
    "sources_de_dates_differentes_distinctes",
    "gains_245_et_847_non_directement_comparables",
    "ne_pas_soustraire_pour_deduire_effet_nova",
    "aide_sociale_non_traitée_comme_salaire",
    "cases_absentes_table_publiee_ne_valent_pas_zero",
    "un_profils_gagnant_ne_prouve_pas_gain_general",
    "aides_de_printemps_2026_non_incluses_table_automne_2025",
    "rrq_rqap_reduction_pme_non_economie_du_gouvernement_nova",
    "pme_1010_ne_pas_multiplier_par_nombre_pme",
    "aucun_total_gains_profils_comme_impact_budgetaire",
    "aide_ponctuelle_2026_non_recurrente",
    "federal_reste_competent_dans_canada",
    "scenario_souverain_hypothetique_distinct",
    "services_essentiels_et_emplois_proteges",
    "protection_du_pouvoir_achat_non_demontrée_nova",
    "p52d_720_valeurs_inconnues_inchangees",
    "p52b_600_valeurs_inconnues_inchangees",
    "p55n_53_pourcent_inchange",
    "aucun_taux_nova_nouveau",
    "aucune_economie_certifiee",
    "aucun_sha_pdf_certifie",
    "pdf_visualisation_echouee_declaree",
    "aucune_depense_ou_contact",
    "aucune_modification_sinjira",
    "aucune_fusion_main","no_go_automatique",
}

def need(ok,reason):
    if not ok:
        raise ValueError(reason)

def validate(cfg):
    need(type(cfg) is dict and
         cfg.get("schema_version")=="P55U-1" and
         cfg.get("date_reference")=="2026-11-07" and
         cfg.get("objet")==
           "ETALONNAGE_MULTIPROFILS_QUEBEC_ANNEE_2026_SOURCES_DE_PERIMETRES_DISTINCTS"
         and cfg.get("statut")=="ETUDE_CANDIDATE_NON_ADOPTEE"
         and cfg.get("decision")==NO_GO,"P55U_ENTETE")
    src=cfg.get("sources")
    need(type(src) is dict
         and src["mise_a_jour_2025"]["url"]==SOURCE_PDF
         and src["mise_a_jour_2025"]["date"]=="2025-11-25"
         and src["mise_a_jour_2025"]["table_menages"]=="B.8"
         and src["mise_a_jour_2025"]["table_pme"]=="B.14"
         and src["mise_a_jour_2025"]["preuve"]==
          "EXTRACTION_TEXTE_PDF_PAR_MOTEUR_WEB_CAPTURE_VISUELLE_ECHOUEE_CACHE_MISS_SANS_SHA_ORIGINAL"
         and src["simulation_2026_actualisee"]["url"]==
             p55t.SOURCES["quebec"]
         and src["simulation_2026_actualisee"]["date_mise_a_jour"]==
             "2026-06-17"
         and src["cadre_p55t"]==
             "projets/projet-nova/etudes/P55T_TEMOIN_REVENU_DISPONIBLE_2026_ET_TAUX_ACTUELS.json"
         and src["matrice_p52d"]==
             "projets/projet-nova/etudes/P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json",
         "P55U_SOURCE_ET_PERIMETRE")
    profiles=cfg.get("profils_menages_automne_2025")
    need(type(profiles) is list and len(profiles)==4,
         "P55U_QUATRE_PROFILS_OFFICIELS")
    for row,(identifier,kind,income,adults,kids,values,total) in zip(
            profiles,PROFILE_SPEC):
        need(type(row) is dict and
             row.get("id")==identifier and row.get("categorie")==kind and
             type(row.get("revenu_travail_annuel_cad")) is int and
             row["revenu_travail_annuel_cad"]==income and
             row.get("nb_adultes")==adults and
             row.get("nb_enfants_moins_4_ans")==kids and
             type(row.get("gain_publie_cad")) is int and
             row.get("gain_publie_cad")==total and
             type(row.get("pertinence_nova")) is str and
             row["pertinence_nova"] and
             type(row.get("montants")) is dict and
             list(row["montants"])==list(FIELDS),
             "P55U_PROFIL_MODIFIE")
        need([row["montants"][k] for k in FIELDS]==list(values)
             and all(v is None or type(v) is int for v in values)
             and sum(v for v in values if v is not None)==total,
             "P55U_DETAIL_MESURES_INCOHERENT")
    need(profiles[3].get("repartition_revenus_individuels_cad")==
         [50000,50000]
         and all("repartition_revenus_individuels_cad" not in p
                 for p in profiles[:3]),
         "P55U_DOUBLE_REVENU_FAMILIAL")
    firm=cfg.get("cas_pme_automne_2025")
    need(type(firm) is dict and firm==PME
         and firm["rrq_employeur_2025_cad"]-
             firm["rrq_employeur_2026_cad"]==515
         and firm["rqap_employeur_2025_cad"]-
             firm["rqap_employeur_2026_cad"]==495
         and firm["rrq_variation_reduction_cad"]+
             firm["rqap_variation_reduction_cad"]==1010
         and firm["cotisations_totales_2025_cad"]-
             firm["cotisations_totales_2026_cad"]==1010,
         "P55U_PME_RECONCILIATION")
    recent=cfg.get("temoin_plus_recent_2026")
    need(type(recent) is dict and
         recent.get("identifiant")=="P55T_PERSONNE_VIVANT_SEULE_50000"
         and recent.get("revenu_annuel_cad")==50000
         and recent.get("gain_publie_cad")==847
         and recent.get("somme_composantes_publiées_cad")==846
         and recent.get("ecart_non_explique_cad")==1
         and recent.get("comparable_directement_avec_U02") is False
         and recent.get("difference_entre_les_deux_gains_interpretable_comme_effet_de_politique_nova") is False
         and recent.get("total_revenu_disponible_actuel_cad") is None
         and recent.get("total_revenu_disponible_nova_cad") is None,
         "P55U_COMPARAISON_TEMOIN_TROMPEUSE")
    scope=cfg.get("couverture")
    need(type(scope) is dict
         and scope.get("nb_menages_documentes_sur_la_table_source")==4
         and scope.get("nb_pme_illustratives_sur_la_table_source")==1
         and scope.get("nb_composantes_menages")==6
         and scope.get("modeles_p52d_complets")==0
         and scope.get("montants_incidence_p52d_inconnus")==720
         and scope.get("postes_budgetaires_p52b_inconnus")==600
         and scope.get("pourcentage_programme_estime_inchange")==53
         and scope.get("acteurs_representatifs_de_la_population") is False
         and scope.get("revenu_disponible_2026_pour_tous_les_profils_cad") is None
         and scope.get("taux_de_deux_prelevements_nova_pct") is None
         and scope.get("gains_nova_attribuables_cad") is None
         and scope.get("financement_annuel_soutenable_demontre") is False,
         "P55U_PAS_DE_GAIN_NOVA")
    proofs=cfg.get("preuves_necessaires")
    need(type(proofs) is list and len(proofs)==8
         and [p.get("id") for p in proofs]==[
             "U"+str(i).zfill(2) for i in range(1,9)]
         and all(type(p) is dict and
                 set(p)=={"id","objet","statut","critere"} and
                 p["statut"]=="OUVERT" and p["critere"]
                 for p in proofs),"P55U_PREUVES_ABSENTES")
    guards=cfg.get("garde_fous")
    need(type(guards) is dict
         and set(guards)==REQUIRED_SAFE
         and all(v is True for v in guards.values()),
         "P55U_GARDES_REFUSES")
    return True

def load():
    with CONFIG.open(encoding="utf-8") as f:
        cfg=json.load(f)
    validate(cfg)
    parent=p55t.load()
    baseline=parent["cas_officiel_2026"]
    recent=cfg["temoin_plus_recent_2026"]
    need(baseline["revenu_annuel_indique_cad"]==
         recent["revenu_annuel_cad"]==50000
         and baseline["variation_revenu_disponible_publiee_cad"]==
         recent["gain_publie_cad"]==847
         and baseline["somme_composantes_affichees_cad"]==
         recent["somme_composantes_publiées_cad"]==846
         and baseline["ecart_avec_total_publie_cad"]==
         recent["ecart_non_explique_cad"]==1
         and parent["population_et_incidence"]["p52d_montants_inconnus"]==720,
         "P55U_PARENT_P55T")
    return cfg

def report(cfg):
    validate(cfg)
    return {
        "schema_version":"P55U-BILAN-PUBLIC-1",
        "annee_cible_des_exemples":2026,
        "table_menages_automne_2025":"B.8",
        "nombre_menages_illustres":4,
        "gains_illustratifs_cad":{
            row["categorie"]:row["gain_publie_cad"]
            for row in cfg["profils_menages_automne_2025"]},
        "pme_exemple_10_employes_reduction_cotisations_cad":1010,
        "temoin_plus_recent_personne_seule_50000_cad":847,
        "temoin_automne_2025_personne_seule_50000_cad":245,
        "comparaison_directe_des_deux_temoins_autorisee":False,
        "causes_variation_entre_temoins_attribuables_a_nova":False,
        "taux_nova_pct":None,"gains_nova_reels_cad":None,
        "incidence_p52d_montants_inconnus":720,
        "budgets_p52b_montants_inconnus":600,
        "score_programme_estime_inchange_pct":53,
        "avis_independants_signes":0,"economies_certifiees_cad":None,
        "decision":NO_GO,
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan-public")
    ap.add_argument("--exiger-incidence-nova",action="store_true")
    opt=ap.parse_args(argv)
    try:
        cfg=load()
        result=report(cfg)
        if opt.bilan_public:
            import evaluer_completude_programme_nova_p55n as p55n
            p55n.write_new(opt.bilan_public,result)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if opt.exiger_incidence_nova else 0
    except (OSError,KeyError,TypeError,ValueError,UnicodeError,
            json.JSONDecodeError):
        print("P55U_REFUS: ETALONNAGE_PROFILS_INCOHERENT",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
