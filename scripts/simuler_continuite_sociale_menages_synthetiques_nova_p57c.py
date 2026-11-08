#!/usr/bin/env python3
"""P57C - banc d'essai synthétique du crédit de solidarité 2026-2027.

Les cas fictifs ne sont pas un calcul officiel d'admissibilité ni une
microsimulation représentative des ménages du Québec. Le montant testé est
une valeur imaginaire déjà déterminée, pas la formule du crédit.

Une protection de retenue sur dette "max 50 %" ne signifie PAS que
Revenu Québec prélèvera la moitié, ni qu'aucune autre limite n'existe.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

BASE = "projets/projet-nova/etudes/"
DEPENDENCIES = {
 "p57b":BASE+"P57B_SOLIDARITE_VERSEMENTS_2026_2027_ET_VERROU_PROTECTION_TVQ.json",
 "p57a":BASE+"P57A_RECONCILIATION_CREDITS_2025_2026_COMPTES_PUBLICS_VOL1.json",
 "p56o":BASE+"P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
 "barometre":BASE+"P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"}
URLS = {
 "calcul_revenu_quebec":"https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-solidarite/calcul-du-credit-dimpot-pour-solidarite/",
 "versements_revenu_quebec":"https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-solidarite/versement-du-credit-dimpot-pour-solidarite/",
 "retenue_dette_revenu_quebec":"https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-solidarite/situations-limitant-lutilisation-de-vos-versements-pour-payer-une-dette-a-letat/",
 "conditions_revenu_quebec":"https://www.revenuquebec.ca/fr/citoyens/credits-dimpot/credit-dimpot-pour-solidarite/conditions-a-remplir/"}
MONTHS = {
 "ANNUELLE":["2026-07"],
 "TRIMESTRIELLE":["2026-07","2026-10","2027-01","2027-04"],
 "MENSUELLE":[f"{year}-{month:02d}" for year,months in
    ((2026,range(7,13)),(2027,range(1,7))) for month in months]}
EXPECTED = {
 "C01":("PERSONNE_SEULE",0,False,20000,1200,True,False),
 "C02":("MONOPARENTALE",1,False,30000,799,False,False),
 "C03":("COUPLE",0,False,75000,0,True,False),
 "C04":("PERSONNE_SEULE",0,False,26190,240,True,False),
 "C05":("PERSONNE_SEULE",0,False,26191,800,True,False),
 "C06":("PERSONNE_SEULE",0,True,75000,600,True,False),
 "C07":("PERSONNE_SEULE",0,False,15000,799,True,True),
 "C08":("PERSONNE_SEULE",0,False,30000,0,False,False),
 "C09":("COUPLE",0,False,70395,0,False,False),
 "C10":("MONOPARENTALE",1,False,67179,0,False,False)}
INT_RE=re.compile(r"(?:0|[1-9][0-9]{0,9})\Z")
RULES={
"seuil_revenu_familial_personne_seule_ou_monoparentale_cad":"64545",
"seuil_revenu_familial_couple_base_cad":"70395",
"majoration_maximum_par_enfant_cad":"2634",
"seuil_retenue_dette_maximum_moins_de_50_pct_2026_2027_cad":"26190",
"part_maximum_retenue_si_protege":"0.50"}
TRUE_RULES={
 "seuils_maximum_hors_villages_nordiques",
 "aide_dernier_recours_donne_protection_50_pct_meme_sans_regle_revenu",
 "montant_jusqua_240_versement_annuel",
 "montant_241_799_versements_trimestriels",
 "montant_a_partir_800_versements_mensuels",
 "revenu_sous_seuil_ne_prouve_pas_admissibilite",
 "absence_d_avis_ne_permet_pas_de_verser_credit_estime"}
NON_TRIVIAL_GUARDS={
"cas_entierement_fictifs",
"montants_credit_non_calcules_depuis_impots",
"cas_de_0_credit_n_est_pas_preuve_inéligibilite",
"plafond_retenue_ne_signifie_pas_retenue_reellement_effectuee",
"en_absence_de_protection_identifiee_ne_pas_inferer_droit_de_retenir_100_pct",
"aucun_echeancier_de_versement_individuel_certifie",
"calendrier_de_versement_n_est_pas_charge_en_droits_constates",
"le_droit_reel_requiert_admissibilite_declaration_annexe_D_et_revenu_familial",
"aucun_nouveau_taux_nova_invente",
"aucun_resultat_net_menage_Nova_2027_certifie",
"aucune_somme_historique_double_comptee",
"transferts_federaux_non_presumes_souverainete",
"conformite_aux_droits_individuels_avant_simplification"}
def ensure(ok,msg):
    if not ok:
        raise ValueError(msg)
def integer(s):
    ensure(type(s) is str and INT_RE.fullmatch(s) is not None,
           "DOLLARS_ENTIERS_CAD_REQUIS")
    return int(s)

def simuler(c):
    """Seuil indicatif + cadence et retenue maximale PROTEGEE, sans attribuer un droit."""
    ensure(isinstance(c,dict) and c.get("situation_familiale") in (
        "PERSONNE_SEULE","MONOPARENTALE","COUPLE"),
        "SITUATION_FAMILIALE_INVALIDE")
    family=c["situation_familiale"]
    children=c.get("enfants_a_charge")
    ensure(type(children) is int and 0<=children<=20 and
        (family!="PERSONNE_SEULE" or children==0) and
        (family!="MONOPARENTALE" or children>=1),
        "ENFANTS_NON_CONCORDANTS")
    for key in ("residence_village_nordique","dette_envers_etat",
                "aide_financiere_dernier_recours"):
        ensure(type(c.get(key)) is bool,"DRAPEAU_INVALIDE_"+key)
    income=integer(c.get("revenu_familial_net_reference_2025_cad"))
    award=integer(c.get("credit_annuel_fictif_deja_determine_par_avis_cad"))
    north=c["residence_village_nordique"]
    ceiling=(70395 if family=="COUPLE" else 64545)+2634*children
    if north:
        threshold_status="VILLAGE_NORDIQUE_HORS_TABLEAU_GENERAL"
        applicable_ceiling=None
    elif income>=ceiling:
        threshold_status="PLAFOND_GENERAL_ATTEINT_OU_DEPASSE"
        applicable_ceiling=ceiling
        ensure(award==0,"AVIS_FICTIF_POSITIF_CONTRAIRE_AU_PLAFOND_GENERAL")
    else:
        threshold_status="SOUS_PLAFOND_SANS_PREUVE_D_ADMISSIBILITE"
        applicable_ceiling=ceiling

    if award==0:
        schedule="AUCUN_CREDIT_FICTIF_ATTRIBUE"
        months=[]
    elif award<=240:
        schedule="ANNUELLE"
        months=MONTHS["ANNUELLE"]
    elif award<=799:
        schedule="TRIMESTRIELLE"
        months=MONTHS["TRIMESTRIELLE"]
    else:
        schedule="MENSUELLE"
        months=MONTHS["MENSUELLE"]

    first=[m for m in months if m<="2027-03"]
    second=[m for m in months if m>="2027-04"]
    protected=(income<=26190 or c["aide_financiere_dernier_recours"])
    debt=c["dette_envers_etat"]
    if debt and award>0 and protected:
        debt_status="PLAFOND_DE_RETENUE_VERIFIABLE_50_PCT"
        max_withheld=format(Decimal(award)*Decimal("0.50"),".2f")
    elif debt and award>0:
        debt_status="PLAFOND_DE_50_PCT_NON_ETABLI_PAR_CES_CRITERES"
        max_withheld=None
    else:
        debt_status="PAS_DE_RETENUE_ILLUSTREE"
        max_withheld=None

    return {
      "cas":c["id"],
      "status_plafond_revenu":threshold_status,
      "plafond_general_applicable_cad":(
          str(applicable_ceiling) if applicable_ceiling is not None else None),
      "montant_fictif_fourni_cad":str(award),
      "cadence_theorique":schedule,
      "mois_theoriques_de_versement":months,
      "nb_versements_jusque_mars_2027":len(first),
      "nb_versements_avril_juin_2027":len(second),
      "credit_annuel_ne_garantit_pas_droit":True,
      "protection_retenue_50_pct_condition_reconnue":protected,
      "retenue_potentielle_statut":debt_status,
      "borne_superieure_retenue_sur_credit_annuel_si_protection_cad":max_withheld,
      "retenue_reelle_imputee_cad":None,
      "montant_reel_du_credit_confirmé_cad":None,
      "cout_budgétaire_2027_2028_confirme_mcad":None
    }

def auditer(d,p57b,p57a,p56o,barometre):
    ensure(isinstance(d,dict) and d.get("schema_version")=="P57C-1" and
       d.get("date_revision")=="2026-11-08" and
       d.get("objet")=="PILOTE_SCENARIOS_SYNTHETIQUES_CONTINUITE_SOLIDARITE_ET_RETENUE_DETTE_CREDIT" and
       d.get("statut")=="BANC_ESSAI_DE_REGLES_2026_2027_NON_MICROSIMULATION_REELLE" and
       d.get("decision")=="NO_GO_AUTOMATIQUE",
       "SCHEMA_P57C_NON_CONFORME")
    sources=d.get("provenance")
    ensure(isinstance(sources,dict) and set(sources)==set(DEPENDENCIES)|set(URLS) and
       all(sources[k]==v for k,v in DEPENDENCIES.items()) and
       all(sources[k]==v for k,v in URLS.items()),
       "SOURCES_P57C_NON_CONCORDANTES")
    ensure(p57b.get("schema_version")=="P57B-1" and
       p57a.get("schema_version")=="P57A-1" and
       p56o.get("schema_version")=="P56O-1" and
       barometre.get("schema_version")=="P55N-1" and
       p57b.get("decision")=="NO_GO_AUTOMATIQUE" and
       p57a.get("decision")=="NO_GO_AUTOMATIQUE",
       "PREDECESSEURS_P57B_NON_VALIDES")
    p=d.get("parametres_publies_2026_2027")
    precedent=p57b.get("droits_et_calcul_actuels",{})
    ensure(isinstance(p,dict) and p.get("periode_versement")==precedent.get("periode_de_versement")==
          "2026-07-01/2027-06-30" and
       p.get("revenus_imposition_reference_annee")==precedent.get("declaration_fiscale_annee_reference")==2025 and
       p.get("situation_personnelle_reference")==precedent.get("situation_personnelle_date_reference")==
          "2025-12-31" and
       set(RULES).issubset(p) and all(p.get(k)==v for k,v in RULES.items()) and
       all(p.get(k) is True for k in TRUE_RULES) and
       p["seuil_revenu_familial_personne_seule_ou_monoparentale_cad"]==
            precedent.get("seuil_revenu_familial_max_sans_conjoint_2026_2027_cad") and
       p["seuil_revenu_familial_couple_base_cad"]==
            precedent.get("seuil_base_avec_conjoint_2026_2027_cad") and
       p["majoration_maximum_par_enfant_cad"]==
            precedent.get("montant_seuil_additionnel_par_enfant_2026_2027_cad"),
       "PARAMETRES_RQ_2026_2027_NON_RECONCILIES")
    actual=d.get("mensualites_officielles")
    ensure(isinstance(actual,dict) and actual==MONTHS and
        {x["id"]:x["versements_mois"] for x in p57b["cadences"]}==MONTHS,
        "CADENCES_P57B_NON_RECONCILIEES")
    guards=d.get("integrite_qualificatifs")
    ensure(isinstance(guards,dict) and set(guards)==NON_TRIVIAL_GUARDS and
        all(guards.get(k) is True for k in NON_TRIVIAL_GUARDS),
        "CAS_SYNTHETIQUES_PRESENTES_COMME_PREUVES_REELLES")
    cases=d.get("jeux_de_cas_fictifs")
    ensure(isinstance(cases,list) and len(cases)==10 and
        {c.get("id") for c in cases if isinstance(c,dict)}==set(EXPECTED),
        "COHORTE_SYNTHETIQUE_NON_COMPLETE")
    results={}
    for c in cases:
        expected=EXPECTED[c["id"]]
        check=(
           c.get("situation_familiale"),c.get("enfants_a_charge"),
           c.get("residence_village_nordique"),
           integer(c.get("revenu_familial_net_reference_2025_cad")),
           integer(c.get("credit_annuel_fictif_deja_determine_par_avis_cad")),
           c.get("dette_envers_etat"),c.get("aide_financiere_dernier_recours"))
        ensure(check==expected and
           isinstance(c.get("profil_synthetique"),str) and
           len(c["profil_synthetique"])>=35 and
           c.get("source_beneficiaire_reel") is None and
           c.get("droit_au_credit_demonte_par_simulation") is False and
           c.get("credit_effectivement_recu_cad") is None and
           c.get("effet_fiscal_nova_certifie_cad") is None and
           c.get("cout_public_prevision_2027_2028_mcad") is None,
           "CAS_FICTIF_ALTERE_OU_CERTIFIE_PAR_ERREUR")
        results[c["id"]]=simuler(c)
    ensure(results["C01"]["borne_superieure_retenue_sur_credit_annuel_si_protection_cad"]=="600.00" and
        results["C04"]["borne_superieure_retenue_sur_credit_annuel_si_protection_cad"]=="120.00" and
        results["C07"]["borne_superieure_retenue_sur_credit_annuel_si_protection_cad"]=="399.50" and
        results["C05"]["borne_superieure_retenue_sur_credit_annuel_si_protection_cad"] is None and
        results["C06"]["plafond_general_applicable_cad"] is None and
        results["C09"]["status_plafond_revenu"]=="PLAFOND_GENERAL_ATTEINT_OU_DEPASSE" and
        results["C10"]["status_plafond_revenu"]=="PLAFOND_GENERAL_ATTEINT_OU_DEPASSE",
        "CAS_PILOTE_NON_REPRODUCTIBLES")
    gates=d.get("pistes_au_dela_du_banc_essai")
    ensure(isinstance(gates,list) and len(gates)==6 and
        {g.get("id") for g in gates}=={f"C{i:02d}" for i in range(1,7)} and
        all(g.get("preuve_statut")=="NON_OBTENUE" and
            len(g.get("objectif",""))>=65 for g in gates),
        "PREUVES_POPULATION_REELLE_FICTIVEMENT_ACQUISES")
    advance=d.get("avancement")
    ensure(isinstance(advance,dict) and
        advance.get("score_estime")==barometre.get("score_estimatif")==53 and
        advance.get("points_restants")==47 and
        advance.get("p56o_portes_demontrees")==0 and
        advance.get("p52b_lignes_financieres_non_remplies")==600 and
        advance.get("p52d_incidence_donnees_non_remplies")==720 and
        advance.get("p52a_preuves_non_validees")==20 and
        advance.get("avis_independants_nova_signes")==0 and
        advance.get("budget_nova_2027_2036_valide") is False and
        advance.get("modele_revenu_disponible_nova_valide") is False and
        advance.get("aucun_droit_nouveau_adopte") is True and
        advance.get("statut")=="NO_GO_AUTOMATIQUE" and
        p56o.get("definition_terminee",{}).get("etat_actuel_termine") is False,
        "MATURITE_NON_DEMONTREE")
    return {
        "jalon":"P57C",
        "exercices":"2026-2027_AVEC_VERSEMENTS_JUSQU_A_JUIN_2027",
        "nombre_cas_synthetiques":len(cases),
        "droits_individuels_reels_calcules":0,
        "fiches_de_menages_reels_incluses":0,
        "resultats_par_cas":results,
        "plafond_retenue_dette_protegee_revenu_familial_cad":"26190",
        "protection_retenue_50_pct_ne_prejuge_pas_retenue_effective":True,
        "regles_villages_nordiques_pas_assimilees_au_seuil_general":True,
        "aucun_nouveau_benefice_nova_certifie":True,
        "budget_protection_menages_2027_certifie":False,
        "points_restants_estimes":47,
        "score_estime_pourcent":53,
        "portes_completes":0,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for k in ("pilote","p57b","p57a","p56o","barometre"):
        parser.add_argument("--"+k,required=True,type=Path)
    parser.add_argument("--rapport",type=Path)
    parser.add_argument("--exiger-microsimulation-validee",action="store_true")
    args=parser.parse_args(argv)
    if args.exiger_microsimulation_validee:
        print("REFUS: cas fictifs ne permettent pas de déclarer le budget Nova validé",file=sys.stderr)
        return 3
    try:
        def load(p):
            return json.loads(p.read_text(encoding="utf-8"))
        output=json.dumps(auditer(*[load(getattr(args,k)) for k in (
            "pilote","p57b","p57a","p56o","barometre")]),
            ensure_ascii=False,indent=2)+"\n"
        if args.rapport:
            with args.rapport.open("x",encoding="utf-8") as out:
                out.write(output)
        else:
            print(output,end="")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
