#!/usr/bin/env python3
"""P55T : témoin public québécois de 2026, pas simulation fiscale Nova.

847 CAD est la variation officielle du revenu disponible d'un cas publié.
Ses composantes affichées font 846 CAD : conserver l'écart non expliqué.
La fonction d'impôt progressif sert UNIQUEMENT aux tests de barèmes avant crédits.
"""
import argparse
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json
from pathlib import Path
import re
import sys

import mesurer_couverture_incidences_nova_p55s as p55s

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"projets"/"projet-nova"/"etudes"/"P55T_TEMOIN_REVENU_DISPONIBLE_2026_ET_TAUX_ACTUELS.json"
NO_GO="NO_GO_AUTOMATIQUE"
SOURCES={
    "quebec":"https://www.quebec.ca/finances-impots-et-taxes/credits-impots-deductions/estimer-revenu-disponible",
    "quebec_baremes":"https://www.revenuquebec.ca/fr/entreprises/retenues-a-la-source-et-cotisations-de-lemployeur/employeur-principaux-changements-2026/",
    "federal":"https://www.canada.ca/fr/agence-revenu/services/impot/particuliers/taux-imposition-tranches-revenu/annee-en-cours.html",
    "abattement":"https://www.canada.ca/fr/ministere-finances/services/publications/depenses-fiscales/2026/partie-4.html",
}
COMPONENTS=(
    ("AIDE_EPICERIE_ENERGIE_2026",100,"VERSEMENT_PONCTUEL_2026"),
    ("ALLOCATION_CANADIENNE_EPICERIE_BESOINS_ESSENTIELS",358,"MESURE_COMPOSITE_RECURRENCE_DETAIL_NON_DEDUITE"),
    ("REDUCTION_COTISATIONS",72,"A_ETUDIER"),
    ("INDEXATION_FISCALE_QUEBEC",166,"EFFET_INDEXATION_2026_PAR_RAPPORT_A_2025"),
    ("INDEXATION_FISCALE_FEDERALE",150,"EFFET_INDEXATION_2026_PAR_RAPPORT_A_2025"),
)
BRACKETS_Q=(
    (54345,"14"),(108680,"19"),(132245,"24"),(None,"25.75"),
)
BRACKETS_F=(
    (58523,"14"),(117045,"20.5"),(181440,"26"),
    (258482,"29"),(None,"33"),
)
REQUIRED_GUARDS={
    "total_officiel_847_ne_pas_remplacer_par_846",
    "ne_pas_inventer_cause_ecart_1_dollar",
    "ne_pas_presenter_847_comme_gain_nova",
    "ne_pas_presenter_cas_50000_comme_representatif",
    "versement_100_ponctuel_2026",
    "ne_pas_extrapoler_358_automatiquement_recurrent",
    "baremes_marginaux_non_taux_effectifs",
    "revenu_brut_non_necessairement_revenu_imposable",
    "credits_fiscaux_non_entierement_decrits",
    "abattement_federal_quebec_ne_pas_omettre",
    "federal_reste_competent_au_canada",
    "aucun_revenu_disponible_absolu_invente",
    "aucune_valeur_p52d_null_remplacee",
    "aucun_changement_p55n_53",
    "aucun_montant_p52b_null_remplace",
    "protection_menages_moyens_modestes_et_retraites",
    "proteger_pme_emplois_et_services",
    "scenario_souverain_hypothetique_distinct",
    "pas_de_rendement_anti_paradis_fictif",
    "pas_de_taux_nova_deduit",
    "no_go_automatique",
    "aucune_depense_ou_contact",
    "sinjira_inchange",
    "aucune_fusion_main",
}
DECIMAL=re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$")

def need(condition,reason):
    if not condition:
        raise ValueError(reason)

def check(cfg):
    need(type(cfg) is dict
         and cfg.get("schema_version")=="P55T-1"
         and cfg.get("date_reference")=="2026-11-07"
         and cfg.get("decision")==NO_GO
         and cfg.get("decision_finale")==NO_GO
         and cfg.get("statut")=="REPERE_PUBLIC_2026_NON_REPRESENTATIF_NON_ADOPTE"
         and cfg.get("objectif")==
             "DOCUMENTATION_D_UN_GAIN_HISTORIQUE_2025_2026_NON_SIMULATION_NOVA",
         "P55T_ENTETE_NON_CONFORME")
    source=cfg.get("source_principale")
    need(type(source) is dict
         and source.get("id")=="QUEBEC_REVENU_DISPONIBLE_2026"
         and source.get("url")==SOURCES["quebec"]
         and source.get("derniere_mise_a_jour_publiee")=="2026-06-17"
         and source.get("montant_non_certifie_comme_resultat_projet_nova") is True,
         "P55T_SOURCE_GOUVERNEMENTALE_INCONNUE")
    b=cfg.get("cas_officiel_2026")
    need(type(b) is dict
         and b.get("profil")=="PERSONNE_VIVANT_SEULE"
         and type(b.get("revenu_annuel_indique_cad")) is int
         and b["revenu_annuel_indique_cad"]==50000
         and b.get("annee_reference")==2025
         and b.get("annee_comparee")==2026
         and type(b.get("variation_revenu_disponible_publiee_cad")) is int
         and b["variation_revenu_disponible_publiee_cad"]==847
         and b.get("categorie_p52d_mapping_possible")==
             "personne_seule_revenu_moyen"
         and b.get("mapping_p52d_certifie") is False
         and b.get("p52d_huit_valeurs_actuel_propose_non_remplies") is True
         and b.get("recurrences_et_admissibilites_detaillees_non_prouvees") is True,
         "P55T_CAS_DE_BASE_NON_CORROBORE")
    components=b.get("composantes_de_variation_affichees_cad")
    need(type(components) is list
         and components==[
             {"id":id,"montant_cad":amount,"recurrence":recurrence}
             for id,amount,recurrence in COMPONENTS]
         and type(b.get("somme_composantes_affichees_cad")) is int
         and b["somme_composantes_affichees_cad"]==
             sum(entry["montant_cad"] for entry in components)==846
         and type(b.get("ecart_avec_total_publie_cad")) is int
         and b["ecart_avec_total_publie_cad"]==847-846==1
         and b.get("traitement_ecart")==
             "ECART_DE_PRESENTATION_NON_EXPLIQUE_PAR_LA_PAGE_NE_PAS_INVENTER_DE_CAUSE",
         "P55T_847_ET_846_DOIVENT_RESTER_DISTINCTS")
    for key in ("revenu_disponible_2025_total_cad",
                "revenu_disponible_2026_total_cad","revenu_imposable_cad",
                "impots_federaux_reels_cad","impots_quebec_reels_cad",
                "resultat_nova_cad"):
        need(b.get(key) is None,"P55T_REVENUS_INVENTES")
    rates=cfg.get("baremes_marginaux_2026")
    need(type(rates) is dict
         and rates.get("quebec",{}).get("source")==SOURCES["quebec_baremes"]
         and rates.get("federal",{}).get("source")==SOURCES["federal"]
         and rates["federal"].get("abattement_source")==SOURCES["abattement"]
         and rates["federal"].get("abattement_quebec_base_federale_pct")=="16.5"
         and rates["federal"].get("abattement_s_applique_sur")==
             "IMPOT_FEDERAL_DE_BASE_EXIGIBLE_NON_SUR_REVENU_BRUT"
         and rates["quebec"].get("montant_personnel_base_2026_cad")==18952
         and rates["quebec"].get("montant_personnel_base_est_cotisation") is False,
         "P55T_BAREMES_ET_ABATTEMENT_INCORRECTS")
    for authority,source_rows in (("quebec",BRACKETS_Q),("federal",BRACKETS_F)):
        need(rates[authority].get("paliers")==[
            {"plafond_revenu_imposable_cad":ceiling,"taux_pct":rate}
            for ceiling,rate in source_rows],
            "P55T_TRANCHES_REVENUS_2026_INCORRECTES")
    need(rates.get("barèmes_sont_lois_courantes_non_nova") is True
         and rates.get("calcul_impot_net_reel_autorise") is False
         and rates.get("calcul_impot_nova_autorise") is False,
         "P55T_MISE_EN_VIGUEUR_NON_AUTORISEE")
    scope=cfg.get("population_et_incidence")
    need(type(scope) is dict
         and scope.get("annee_reference_des_reperes")==2026
         and scope.get("contribution_p52d")==
             "REPERE_OFFICIEL_DE_VARIATION_SEULEMENT_AUCUNE_VALEUR_NULL_DU_GABARIT_MODIFIEE"
         and scope.get("p52d_montants_inconnus")==720
         and scope.get("p52b_montants_inconnus")==600
         and scope.get("p55n_score_estime_pct")==53
         and scope.get("effet_sur_score_reconnu")==0
         and scope.get("personnes_reellement_modelees_avec_impots_complets")==0
         and scope.get("entreprises_reellement_modelees_avec_impots_complets")==0
         and scope.get("hausse_pouvoir_achat_nova_demontree") is False
         and scope.get("economie_certifiee_mcad") is None,
         "P55T_PAS_DE_PREUVE_DE_GAIN_NOVA")
    tasks=cfg.get("questions_requises")
    need(type(tasks) is list and len(tasks)==8
         and [t.get("id") for t in tasks]==[
             "T"+str(i).zfill(2) for i in range(1,9)]
         and all(type(t) is dict and set(t)=={
             "id","description","statut"} and
             t["statut"]=="OUVERT" and
             type(t["description"]) is str and t["description"]
             for t in tasks),
         "P55T_PIECES_ENCORE_MANQUANTES")
    guards=cfg.get("protections")
    need(type(guards) is dict
         and set(guards)==REQUIRED_GUARDS
         and all(g is True for g in guards.values()),
         "P55T_VERROUS_ENLEVES")
    return True

def progressive_before_credits(taxable_income_cad,authority):
    """Montant progressif arithmétique AVANT crédits et abattement, non impôt réel.

    N'accepte PAS le revenu brut ni les entrées implicites. Ne pas afficher
    ce résultat comme prélèvement effectivement acquitté par un citoyen.
    """
    need(type(taxable_income_cad) is str
         and bool(DECIMAL.fullmatch(taxable_income_cad))
         and authority in ("quebec","federal"),
         "P55T_SAISIR_REVENU_IMPOSABLE_EXPLICITE")
    try:
        income=Decimal(taxable_income_cad)
        need(income<=Decimal("100000000"),"P55T_ENTREE_HORS_TEST")
        schedule=BRACKETS_Q if authority=="quebec" else BRACKETS_F
        lower=Decimal("0")
        tax=Decimal("0")
        for ceiling,rate in schedule:
            upper=income if ceiling is None else min(income,Decimal(ceiling))
            if upper>lower:
                tax+=(upper-lower)*Decimal(rate)/Decimal("100")
                lower=upper
        return str(tax.quantize(Decimal("0.01"),rounding=ROUND_HALF_UP))
    except InvalidOperation:
        raise ValueError("P55T_MONTANT_MAL_FORME")

def load():
    with DATA.open(encoding="utf-8") as source:
        cfg=json.load(source)
    check(cfg)
    parent,result=p55s.load()
    need(parent["schema_version"]=="P55S-1"
         and result["total_montants_non_renseignes"]==720
         and result["montants_menages_non_renseignes"]==480
         and result["montants_entreprises_non_renseignes"]==240
         and p55s.read(p55s.P55N)["score_estimatif"]==53,
         "P55T_MONTANTS_P55S_DOIVENT_RESTER_INCONNUS")
    return cfg

def report(cfg):
    check(cfg)
    return {
        "schema_version":"P55T-BILAN-PUBLIC-1",
        "date_reference":"2026-11-07",
        "profil_officiel":"PERSONNE_VIVANT_SEULE",
        "revenu_annuel_du_témoin_cad":50000,
        "variation_revenu_disponible_2025_2026_publiee_cad":847,
        "somme_composantes_affichees_cad":846,
        "ecart_de_presentation_inexplique_cad":1,
        "aide_epicerie_energie_ponctuelle_cad":100,
        "resultat_nova":None,
        "revenu_disponible_2026_absolu_cad":None,
        "comparaison_nova_vs_actuel_calculee":False,
        "taux_propose_deux_prelevements_pct":None,
        "barèmes_marginaux_de_l_annee_2026_ne_sont_pas_taux_nova":True,
        "abattement_federal_quebec_pct":"16.5",
        "p52d_montants_inconnus":720,
        "p52b_montants_inconnus":600,
        "p55n_score_estime_inchange_pct":53,
        "avis_independants_signes":0,
        "economies_certifiees_mcad":None,
        "questions_preuve_non_resolues":8,
        "decision":NO_GO,
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan-public")
    ap.add_argument("--exiger-simulation-nova",action="store_true")
    args=ap.parse_args(argv)
    try:
        cfg=load()
        result=report(cfg)
        if args.bilan_public:
            import evaluer_completude_programme_nova_p55n as p55n
            p55n.write_new(args.bilan_public,result)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if args.exiger_simulation_nova else 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError):
        print("P55T_REFUS: TEMOIN_OU_BAREMES_NON_VALIDES",file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
