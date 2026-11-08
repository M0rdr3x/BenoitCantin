#!/usr/bin/env python3
"""P57B : sécuriser la période de versement du crédit de solidarité 2026-27.

Ne calcule ni montant de droits individuels ni coût de réforme fiscale Nova.
Distingue 2025-26 (comptes publics), 2026 (projection de dépenses fiscales),
et juillet 2026-juin 2027 (calendrier de versements).
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from decimal import Decimal

ROOT = "projets/projet-nova/etudes/"
DEPS = {
 "p57a":"P57A_RECONCILIATION_CREDITS_2025_2026_COMPTES_PUBLICS_VOL1.json",
 "p56z":"P56Z_CONCORDANCE_CREDITS_2023_ET_RENDEMENT_2027_2031_SANS_DOUBLE_COMPTE.json",
 "p56y":"P56Y_RENDEMENT_BRUT_NECESSAIRE_DEUX_PRELEVEMENTS_2027_2031.json",
 "p56o":"P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
 "barometre":"P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
}
URLS={
"credit_officiel":"https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-solidarite/",
"calcul_officiel":"https://www.revenuquebec.ca/fr/citoyens/declaration-de-revenus/produire-votre-declaration-de-revenus/aide-par-ligne/credit-dimpot-pour-solidarite/",
"versements_officiels":"https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-solidarite/versement-du-credit-dimpot-pour-solidarite/",
"composante_tvq":"https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-solidarite/composantes-du-credit-dimpot-pour-solidarite/composante-relative-a-la-tvq/",
"fiche_depense_fiscale":"https://www.budget.finances.gouv.qc.ca/Budget/outils/depenses-fiscales/fiches/fiche-110201.asp",
"estimation_revenu_disponible":"https://www.quebec.ca/finances-impots-et-taxes/credits-impots-deductions/estimer-revenu-disponible"}
PERIOD_MONTHS=tuple(f"{y}-{m:02d}" for y,m in
    [(2026,m) for m in range(7,13)]+[(2027,m) for m in range(1,7)])
CADENCES={
"ANNUELLE":("<=240_CAD_ENTIERS",("2026-07",),1,0),
"TRIMESTRIELLE":("241_A_799_CAD_ENTIERS",
    ("2026-07","2026-10","2027-01","2027-04"),3,1),
"MENSUELLE":(">=800_CAD_ENTIERS",PERIOD_MONTHS,9,3)}
COMPONENTS={
"TVQ":"COMPENSATION_COUT_TVQ",
"LOGEMENT":"COMPOSANTE_RELATIVE_LOGEMENT",
"VILLAGES_NORDIQUES":"COUT_DE_VIE_NORDIQUE"}
RULES={
"maintien_equivalent_jusqua_justification_financement",
"les_trois_composantes_doivent_etre_evaluees_separement",
"ne_pas_remplacer_composante_tvq_par_zero_sans_reconception_et_preuve",
"versements_jusqua_juin_2027_ne_sont_pas_automatiquement_abroges",
"exigence_simulation_revenu_disponible_avant_apres",
"maintien_pouvoir_achat_n_est_pas_encore_demontre",
"base_beneficiaires_par_province_region_et_type_menage_inconnue",
"impact_prix_et_comportements_non_mesure",
"avis_juridique_et_comptable_independants_non_obtenus"}
COSTS={
"ne_pas_ajouter_1996_credits_comptables_2025_2026_aux_besoins_2027",
"ne_pas_ajouter_2029_1_projection_2026_aux_besoins_2027",
"en_cas_de_transfert_comptable_compter_seulement_variation_nette_prouvee",
"recettes_tvq_perdues_2027_2028_pas_mesure_de_gain_disponible_nette",
"prestations_federales_non_supposees_modifiables_par_province"}
def insist(v,msg):
    if not v:
        raise ValueError(msg)
def integer(v):
    insist(type(v) is str and v.isascii() and v.isdecimal() and
           (v=="0" or not v.startswith("0")), "CHIFFRE_ENTIER_INVALIDE")
    return Decimal(v)

def auditer(d,p57a,p56z,p56y,p56o,bar):
    insist(isinstance(d,dict) and d.get("schema_version")=="P57B-1"
           and d.get("date_revision")=="2026-11-08"
           and d.get("objet")=="CONTINUITE_SOLIDARITE_2026_2027_COMPOSANTES_VERSEMENTS_FENETRES_COMPTABLES"
           and d.get("statut")=="CONCORDANCE_SOURCES_OFFICIELLES_SANS_PROJECTION_DE_DROITS_FISCAUX_NOVA"
           and d.get("decision")=="NO_GO_AUTOMATIQUE",
           "P57B_SCHEMA_OU_STATUT_INVALIDE")
    sources=d.get("sources",{})
    insist(isinstance(sources,dict) and
           all(sources.get(k)==ROOT+v for k,v in DEPS.items()) and
           all(sources.get(k)==v for k,v in URLS.items()),
           "SOURCE_MANQUANTE_OU_MODIFIEE")
    insist(p57a.get("schema_version")=="P57A-1" and
           p56z.get("schema_version")=="P56Z-1" and
           p56y.get("schema_version")=="P56Y-1" and
           p56o.get("schema_version")=="P56O-1" and
           bar.get("schema_version")=="P55N-1" and
           all(src.get("decision")=="NO_GO_AUTOMATIQUE"
               for src in (p57a,p56z,p56y,p56o)),
           "PREDECESSEURS_INCOMPATIBLES")
    classes=d.get("classification_des_sources",{})
    actual=classes.get("comptes_publics_2025_2026",{})
    annual=classes.get("depense_fiscale_2025_pour_2026",{})
    insist(actual.get("nature")=="REEL_COMPTABILITE_CONSOLIDEE" and
           actual.get("annee_financiere")=="2025-2026" and
           integer(actual.get("credit_solidarite_degrevement_tvq_mcad"))==1996 and
           integer(p57a["revenus_et_reclassement_2025_2026_mcad"]["credit_solidarite"]["montant_degrevement_taxes_ventes"])==1996 and
           actual.get("ne_figure_pas_dans_11578_mcad_reclasses") is True and
           annual.get("nature")=="PROJECTION_PUBLICATION_2025_PAS_REALISE" and
           annual.get("annee_de_projection")==2026 and
           annual.get("credit_solidarite_total_mcad")=="2029.1" and
           annual.get("base_mesures_annoncees_au")=="2025-12-31" and
           integer(annual.get("beneficiaires_2023"))==2836085 and
           annual.get("nombre_beneficiaires_2026_constate") is None and
           classes.get("ne_pas_comparer_1996_2025_2026_et_2029_1_2026_comme_deux_exercices_identiques") is True and
           classes.get("aucun_deux_montants_n_est_cout_incremental_nova_2027") is True and
           classes.get("extrapolation_budget_2027_2036_interdite") is True,
           "COUTS_DES_PERIODES_NON_COMPARABLES")
    rules=d.get("droits_et_calcul_actuels",{})
    insist(rules.get("periode_de_versement")=="2026-07-01/2027-06-30" and
           rules.get("situation_personnelle_date_reference")=="2025-12-31" and
           rules.get("declaration_fiscale_annee_reference")==2025 and
           rules.get("demande_complete_date_limite")=="2029-12-31" and
           integer(rules.get("seuil_revenu_familial_max_sans_conjoint_2026_2027_cad"))==64545 and
           integer(rules.get("seuil_base_avec_conjoint_2026_2027_cad"))==70395 and
           integer(rules.get("montant_seuil_additionnel_par_enfant_2026_2027_cad"))==2634 and
           all(rules.get(k) is True for k in (
             "depend_revenu_familial_net_et_composition",
             "seuil_revenu_seul_non_regle_generale_pour_villages_nordiques")) and
           rules.get("base_vraie_pour_menages_nova_2027") is None and
           rules.get("protection_droit_future_approuvee") is False,
           "DROITS_CALCUL_ACTUELS_NON_RECONCILIES")
    comps=d.get("composantes",[])
    insist(isinstance(comps,list) and len(comps)==3 and
           {r.get("id") for r in comps if isinstance(r,dict)}==set(COMPONENTS),
           "TROIS_COMPOSANTES_EXIGEES")
    for comp in comps:
        insist(comp.get("nature")==COMPONENTS[comp["id"]] and
               comp.get("statut_2026_2027")=="EN_VIGUEUR" and
               comp.get("a_remplacer_ou_maintenir_si_retrait_tvq") is True and
               comp.get("revenu_fiscal_nouveau_nova_mcad") is None and
               comp.get("cout_2027_concorde_mcad") is None,
               "DROITS_OU_COMPOSANTES_FICTIFS")
    cycles=d.get("cadences",[])
    insist(isinstance(cycles,list) and len(cycles)==3 and
           {row.get("id") for row in cycles if isinstance(row,dict)}==set(CADENCES),
           "TOUTES_CADENCES_EXIGEES")
    results={}
    for cycle in cycles:
        term,months,first,second=CADENCES[cycle["id"]]
        recorded=cycle.get("versements_mois")
        insist(cycle.get("condition_montant")==term and
               cycle.get("condition_revenu_fiscal_liee") is False and
               recorded==list(months) and len(recorded)==len(set(recorded)) and
               all(month in PERIOD_MONTHS for month in recorded) and
               cycle.get("nb_avant_fin_exercice_2026_2027")==first and
               cycle.get("nb_dans_debut_exercice_2027_2028")==second and
               first+second==len(months) and
               cycle.get("part_montant_budget_par_fiscal_year_connue") is False,
               "CALENDRIER_VERSEMENTS_NON_COMPATIBLE")
        results[cycle["id"]]={"nb_versements_par_regime":len(months),
            "avant_mars_2027_inclus":first,
            "avril_juin_2027":second}
    calendar=d.get("frontiere_calendrier",{})
    insist(calendar.get("cloture_2026_2027")=="2027-03-31" and
           calendar.get("exercice_2027_2028_debut")=="2027-04-01" and
           calendar.get("exercice_2027_2028_fin")=="2028-03-31" and
           calendar.get("versements_periode_juillet_2026_juin_2027_dans_2027_2028")==[
              "2027-04","2027-05","2027-06"] and
           calendar.get("versements_periode_juillet_2027_juin_2028_parametres_non_disponibles") is True and
           calendar.get("mois_comptabilisation_charge_selon_normes_non_derives_du_seul_calendrier_cash") is True and
           calendar.get("montant_total_2027_2028_inconnu_mcad") is None and
           calendar.get("calendrier_cash_non_identique_imputation_en_droits_constates") is True,
           "PERIODES_DE_CAISSE_VS_EXERCICES_NON_DISTINGUEES")
    protection=d.get("regle_protection_citoyens_candidate",{})
    insist(protection.get("statut")=="OBJECTIF_DE_SIMULATION_A_VALIDER_NON_LOI_ADOPTEE" and
           all(protection.get(k) is True for k in RULES) and
           protection.get("cout_nouveau_solde_nova_2027_mcad") is None,
           "COMPENSATION_SOLIDARITE_NON_DEMONTREE")
    financial=d.get("rapprochement_financier",{})
    insist(integer(financial.get("cible_brute_theorique_deux_piliers_sans_resorption_2027_2028_mcad"))==
           integer(p56y["annees"][0]["rendement_nouveaux_piliers_pour_solde_zero_sans_resorption_mcad"])==116663 and
           all(financial.get(k) is True for k in COSTS) and
           financial.get("calcul_increment_2027_2028_mcad") is None and
           financial.get("beneficiaires_reels_2027_2028") is None and
           financial.get("cout_protection_québec_souverain_mcad") is None,
           "AJOUT_NON_PROUVE_A_BUDGET_NOVA")
    gates=d.get("portes",[])
    insist(isinstance(gates,list) and len(gates)==6 and
           {g.get("id") for g in gates if isinstance(g,dict)}==
           {f"B{i:02d}" for i in range(1,7)} and
           all(g.get("statut")=="OUVERT" and len(g.get("preuve",""))>=70
               for g in gates),
           "PREUVES_SOLIDARITE_FERMEES_ARTIFICIELLEMENT")
    complete=d.get("avancement",{})
    insist(complete.get("p55n_score_estime")==bar.get("score_estimatif")==53 and
           complete.get("points_restants_estimes")==47 and
           complete.get("p56o_portes_validees")==0 and
           complete.get("p52b_cellules_manquantes")==600 and
           complete.get("p52d_incidences_inconnues")==720 and
           complete.get("p52a_preuves_fiscales_non_validees")==20 and
           complete.get("examens_independants_signes")==0 and
           complete.get("changement_barometre_par_ce_jalon") is False and
           complete.get("p57a_protections_2027_validees") is False and
           complete.get("no_go")=="NO_GO_AUTOMATIQUE" and
           p56o.get("definition_terminee",{}).get("etat_actuel_termine") is False,
           "100_POURCENT_NON_AUTORISE")
    return {
      "jalon":"P57B","score_estime_pourcent":53,
      "points_restants":47,
      "degrevement_solidarite_constate_exercice_2025_2026_mcad":"1996",
      "cout_solidarite_projete_annee_2026_mcad":"2029.1",
      "comparabilite_d_annees":False,
      "versement_reference_juillet_2026_juin_2027":True,
      "date_situation_admissibilite":"2025-12-31",
      "annee_declaration_reference":2025,
      "trois_composantes":sorted(COMPONENTS),
      "calendrier_versement":results,
      "budget_droits_2027_2028_confirme":False,
      "benefice_nova_net_menages_certifie":False,
      "soutien_solidarite_aboli_par_option_nova":False,
      "modele_reforme_fiscale_acheve":False,
      "portes_p57b_closes":0,
      "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("registre","p57a","p56z","p56y","p56o","barometre"):
        parser.add_argument("--"+name,required=True,type=Path)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-protection-2027-certifiee",action="store_true")
    a=parser.parse_args(argv)
    if a.exiger_protection_2027_certifiee:
        print("REFUS: montant par beneficiaire et financement 2027 non établis",file=sys.stderr)
        return 3
    try:
        def read(path):
            return json.loads(path.read_text(encoding="utf-8"))
        out=auditer(*[read(getattr(a,k)) for k in (
            "registre","p57a","p56z","p56y","p56o","barometre")])
        txt=json.dumps(out,ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as f:f.write(txt)
        else:
            print(txt,end="")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
