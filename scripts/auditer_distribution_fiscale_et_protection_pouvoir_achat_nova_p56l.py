#!/usr/bin/env python3
"""Projet Nova P56L : distribuer les données fiscales 2023 sans inventer une incidence Nova.

A.14 et A.3 : classes de REVENU TOTAL pour des personnes ayant produit une déclaration,
pas ménages, pas déciles de revenu disponible, ni réforme politique proposée.

Une validation des enregistrements du dépôt ne constitue pas une signature du ministère.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
import auditer_assiettes_revenues_societes_nova_p56k as p56k

VERSION="P56L-1"
SOURCES={
    "A14":"https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-impot-a-payer.asp",
    "A3":"https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/resume.asp",
    "P56K":"projets/projet-nova/etudes/P56K_ASSIETTES_PARTICULIERS_SOCIETES_CREDITS_SOURCES_OFFICIELLES.json"
}
# Valeurs de référence publiées par tranche de revenu TOTAL (M CAD, 2023).
BRACKETS={
    "R00_09999":("2532","335","333","2","777","-775"),
    "R10_19999":("12615","1505","1495","10","1118","-1108"),
    "R20_29999":("26507","2940","2666","273","2306","-2033"),
    "R30_49999":("59789","7470","4654","2816","2275","541"),
    "R50_99999":("159483","21553","7188","14365","2145","12220"),
    "R100_PLUS":("166989","28346","5022","23324","683","22640")
}
METRICS=[
 "revenu_total_mcad","impot_sur_revenu_imposable_mcad",
 "credits_non_remboursables_mcad","impot_a_payer_mcad",
 "credits_remboursables_mcad","impot_net_apres_credits_remboursables_mcad"
]
TOTALS=("427915","62148","21358","40790","9305","31485")
QUINTILES={
 "Q1":("Moins de 19 713 $","3.43","0.03"),
 "Q2":("19 713 $ à 34 580 $","8.91","1.46"),
 "Q3":("34 581 $ à 54 178 $","14.99","8.64"),
 "Q4":("54 179 $ à 82 785 $","22.57","20.45"),
 "Q5":("82 786 $ ou plus","50.10","69.41")
}
PROTECTIONS={f"L{i:02d}" for i in range(1,11)}
NUM=re.compile(r"-?(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,3})?\Z")

def ensure(test,message):
    if not test:
        raise ValueError(message)

def dec(value):
    ensure(type(value) is str and bool(NUM.fullmatch(value)),"DECIMAL_SOURCE_INVALIDE")
    return Decimal(value)

def audit(data, previous, gabarit, preuves, barometre):
    baseline=p56k.auditer(previous,gabarit,preuves,barometre)
    ensure(isinstance(data,dict) and data.get("schema_version")==VERSION,
           "SCHEMA_P56L_INVALIDE")
    ensure(data.get("date_revision")=="2026-11-07" and
           data.get("statut")==
           "OBSERVATIONS_2023_PUBLICATIONS_OFFICIELLES_NON_INCIDENTE_FISCALE_NOVA" and
           data.get("decision")=="NO_GO_AUTOMATIQUE" and
           data.get("territoire")=="QUEBEC_DANS_CANADA" and
           data.get("annee_observee")==2023 and
           data.get("unite_montants")=="M_CAD","PERIMETRE_FISCAL_INVALIDE")
    sources=data.get("sources")
    ensure(isinstance(sources,dict) and set(sources)==set(SOURCES),
           "SOURCES_NON_EXHAUSTIVES")
    for key,url in SOURCES.items():
        field="repo_path" if key=="P56K" else "url"
        ensure(isinstance(sources[key],dict) and sources[key].get(field)==url,
               "SOURCE_MAUVAIS_LIEN_"+key)
    ensure(sources["A14"].get("tableau")=="A.14" and sources["A14"].get("annee")==2023 and
           sources["A3"].get("tableau")=="A.3" and sources["A3"].get("annee")==2023 and
           sources["P56K"].get("annee_personnes")==2023 and
           sources["P56K"].get("annee_societes")==2021 and
           sources["P56K"].get("validation_automatique_p56k")=="SUCCESS",
           "MELANGE_MILLESIMES_SOURCE")
    lines=data.get("tranches_a14")
    ensure(isinstance(lines,list) and len(lines)==6,"SIX_TRANCHES_A14_OBLIGATOIRES")
    found={}
    for row in lines:
        ensure(isinstance(row,dict),"TRANCHE_NON_VALIDE")
        k=row.get("id")
        ensure(type(k) is str and k in BRACKETS and k not in found,
               "TRANCHE_DUPLIQUEE_OU_MANQUANTE")
        amounts=[dec(row.get(m)) for m in METRICS]
        ensure(tuple(str(x) for x in amounts)==BRACKETS[k],
               "A14_VALEURS_SOURCE_MODIFIEES")
        ensure(row.get("statut")=="AGREGATS_STATISTIQUES_PARTICULIERS_2023_ARRONDIS" and
               isinstance(row.get("tranche_revenu_total"),str) and
               len(row["tranche_revenu_total"])>=12 and
               all(row.get(x) is None for x in (
                 "revenu_imposable_de_la_tranche_mcad","nombre_foyers_beneficiaires",
                 "incidence_nova_par_tranche_mcad")),
               "A14_MENAGES_OU_INCIDENTE_INVENTES")
        ensure(abs(amounts[1]-amounts[2]-amounts[3])<=1 and
               abs(amounts[3]-amounts[4]-amounts[5])<=1,
               "A14_IMPOT_CREDITS_INCOHERENTS")
        found[k]=amounts
    ensure(set(found)==set(BRACKETS),"A14_COUVERTURE_INCOMPLETE")
    t=data.get("totaux_publies_a14")
    ensure(isinstance(t,dict) and
           tuple(str(dec(t.get(x))) for x in METRICS)==TOTALS,
           "A14_TOTAUX_OFFICIELS_NON_CONFORMES")
    total=[dec(x) for x in TOTALS]
    sums=[sum((v[i] for v in found.values()),Decimal(0)) for i in range(6)]
    diffs=[sums[i]-total[i] for i in range(6)]
    ensure(tuple(diffs)==tuple(map(Decimal,("0","1","0","0","-1","0"))),
           "A14_SOMMES_ARRONDIS_MAL_TRAITEES")
    ensure(total[0]==Decimal(baseline["particuliers_revenu_total_mcad"]) and
           total[3]==Decimal(previous["particuliers_2023"]["impot_a_payer_mcad"]) and
           total[4]==Decimal(previous["particuliers_2023"]["credits_remboursables_mcad"]) and
           total[5]==Decimal(baseline["particuliers_impot_apres_credits_remboursables_mcad"]),
           "P56K_CONTROLE_INTER_SERIES_INVALIDE")
    rounding=data.get("reconciliation_arrondis")
    expect={
      "ecart_somme_lignes_moins_total_imposition_brute_mcad":"1",
      "ecart_somme_lignes_moins_total_credits_remboursables_mcad":"-1",
      "ecart_calcul_net_100k_plus_moins_valeur_publiee_mcad":"1",
      "ecart_somme_lignes_moins_total_net_mcad":"0",
      "erreur_arrondi_par_poste_toleree_mcad":"1",
    }
    ensure(isinstance(rounding,dict) and all(rounding.get(k)==v for k,v in expect.items()) and
           rounding.get("interdiction_de_forcer_les_lignes_pour_faire_correspondre_les_totaux") is True,
           "TOLERANCE_ARRONDIS_NON_TRACEE")
    ensure(found["R100_PLUS"][3]-found["R100_PLUS"][4]-
           found["R100_PLUS"][5]==Decimal("1"),
           "ARRONDI_100K_MANQUANT")
    lower_keys=("R00_09999","R10_19999","R20_29999")
    lower=[sum((found[k][i] for k in lower_keys),Decimal(0)) for i in range(6)]
    ensure(lower[0]==41654 and lower[3]==285 and
           lower[4]==4201 and lower[5]==-3916 and
           lower[3]-lower[4]==lower[5],"SOUTIEN_REVENUS_MODESTES_NON_RECONCILIE")
    ratio=(lower[4]/total[4]*Decimal(100)).quantize(Decimal(".1"),rounding=ROUND_HALF_UP)
    ensure(ratio==Decimal("45.1"),"PART_CREDITS_REMBOURSABLES_CALCUL_FAUX")
    low=data.get("agregat_sensible_moins_30000")
    ensure(isinstance(low,dict) and
           low.get("group_ids")==list(lower_keys) and
           all(low.get(k)==v for k,v in {
             "revenu_total_mcad":"41654","impot_a_payer_mcad":"285",
             "credits_remboursables_mcad":"4201",
             "impot_net_apres_credits_remboursables_mcad":"-3916",
             "part_du_total_credits_remboursables_pourcent_arrondi":"45.1"}.items()) and
           low.get("nature")=="NET_FISCAL_AGREGE_DE_DECLARANTS_PAR_REVENU_TOTAL_PAS_REVENU_DISPONIBLE" and
           all(low.get(k) is False for k in (
             "somme_fiscale_a_supprimer_dans_nova",
             "beneficiaires_uniques_identifies")) and
           low.get("aide_reelle_par_menage") is None and
           low.get("niveau_protection_finance_nova") is None,
           "GAINS_NOVA_DERIVES_DES_CREDITS_NON_JUSTIFIES")
    q=data.get("quintiles_a3")
    ensure(isinstance(q,list) and len(q)==5,"QUINTILES_INCOMPLETS")
    qrows={}
    for row in q:
        ensure(isinstance(row,dict),"QUINTILE_NON_VALIDE")
        k=row.get("id")
        ensure(type(k) is str and k in QUINTILES and k not in qrows,
               "QUINTILE_INCONNU")
        threshold,inc,tax=QUINTILES[k]
        ensure(row.get("tranche_revenu_total")==threshold and
               (row.get("part_revenu_total_pourcent"),row.get("part_impot_a_payer_pourcent"))==
               (inc,tax) and
               all(row.get(x) is None for x in
                   ("revenu_apres_impot_et_transferts","part_credits_remboursables",
                    "simulation_nova_nette")),
               "QUINTILE_A3_PAS_INCIDENTE_MENAGES")
        qrows[k]=(dec(inc),dec(tax))
    ensure(set(qrows)==set(QUINTILES) and
           abs(sum((v[0] for v in qrows.values()),Decimal(0))-100)<=Decimal(".02") and
           abs(sum((v[1] for v in qrows.values()),Decimal(0))-100)<=Decimal(".02"),
           "PARTS_QUINTILES_NON_CONCORDANTES")
    ind=data.get("indicateurs_quintiles")
    ensure(isinstance(ind,dict) and
           ind.get("q5_part_revenu_total_pourcent")=="50.10" and
           ind.get("q5_part_impot_a_payer_pourcent")=="69.41" and
           ind.get("q1_part_revenu_total_pourcent")=="3.43" and
           ind.get("q1_part_impot_a_payer_pourcent")=="0.03" and
           ind.get("type")=="DISTRIBUTION_STATISTIQUE_NON_EFFET_D_UNE_POLITIQUE",
           "QUINTILES_SOURCE_NON_JUSTIFIES")
    c=data.get("comparabilite_et_controles")
    require_true=[
     "tranches_a14_et_quintiles_a3_recoupements_non_reconstructibles",
     "revenu_total_n_est_pas_revenu_disponible",
     "net_negatif_de_tranche_n_est_pas_paiement_individuel_universel",
     "les_credits_remboursables_ne_sont_pas_integralement_recettes_potentielles",
     "les_credits_fiscaux_ne_sont_pas_tous_des_versements_en_especes"
    ]
    require_false=[
     "taux_nova_2027_2036_deduit_de_2023",
     "analyse_causale_reforme_nova_effectuee",
     "credits_et_impots_federaux_par_tranche_connus",
     "assiettes_societes_2021_alignees_sur_particuliers_2023"
    ]
    ensure(isinstance(c,dict) and
           all(c.get(k) is True for k in require_true) and
           all(c.get(k) is False for k in require_false) and
           c.get("statistique_unite")=="DECLARANTS_PERSONNES" and
           c.get("statistique_unite_n_est_pas")=="FOYERS",
           "STATISTIQUES_FAUSSEMENT_EXTRAPOLEES")
    regimes=data.get("regimes")
    ensure(isinstance(regimes,dict) and set(regimes)=={
        "QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN"},
        "REGIMES_FISCAUX_NON_SEPARES")
    a,b=regimes["QUEBEC_DANS_CANADA"],regimes["QUEBEC_SOUVERAIN"]
    ensure(a.get("assiettes_droits_2027_2036_observes") is False and
           a.get("taxes_federales_sous_controle_quebec") is False and
           a.get("comparaison_menages_apres_TPS_federale") is None and
           a.get("simulation_reforme_nova") is None,"POUVOIRS_PROVINCIAUX_FICTIFS")
    ensure(b.get("hypothese")=="COMPETENCES_ET_COUTS_A_NEGOCIER" and
           all(b.get(k) is None for k in (
             "assiettes_personnes_et_societes_2027_2036",
             "prestations_transferees_net_mcad",
             "financement_fonctions_federales_mcad",
             "simulation_reforme_nova")),
           "SOUVERAINETE_NON_CHIFFREE_A_CE_STADE")
    gates=data.get("portes_protection")
    ensure(isinstance(gates,list) and len(gates)==10 and
           data.get("nombre_portes")==10 and
           {x.get("id") for x in gates if isinstance(x,dict)}==PROTECTIONS and
           all(x.get("statut")=="NON_DEMONTRE" and x.get("preuve_id") is None
               and x.get("avis_independant_id") is None and
               x.get("mesure_nova_calculee") is None and
               len(x.get("exigence",""))>=65 for x in gates),
           "PROTECTIONS_POUVOIR_ACHAT_NON_OBTENUES")
    scenarios=data.get("scenarios_a_etudier")
    ensure(isinstance(scenarios,list) and len(scenarios)==3 and
           {x.get("id") for x in scenarios}=={
             "BASE_DROITS_ACTUELS","DEUX_PRELEVEMENTS_QUEBEC_CANADA",
             "DEUX_PRELEVEMENTS_QUEBEC_SOUVERAIN"} and
           all(x.get("solde_menage") is None and x.get("solde_entreprise") is None
               for x in scenarios),
           "FAUX_RESULTATS_SIMULATION")
    ensure(data.get("p52b_montants_inconnus")==600 and
           data.get("p52d_incidences_inconnues")==720 and
           data.get("p52a_preuves_non_validees")==20 and
           data.get("p55n_score_estimatif")==53 and
           data.get("taux_nova_adopte") is False and
           data.get("nouvelles_recettes_certifiees_mcad") is None and
           data.get("economies_nova_certifiees_mcad") is None and
           data.get("avis_independants_signes")==0 and
           data.get("budget_decennal_valide") is False and
           data.get("declaration_amelioration_universelle_pouvoir_achat_autorisee") is False,
           "RESULTATS_FISCAUX_NOVA_NON_DEMONTRES")
    return {
      "jalon":"P56L","schema_version":VERSION,"decision":"NO_GO_AUTOMATIQUE",
      "type":"REPARTITION_OFFICIELLE_2023_SANS_MICROSIMULATION_NOVA",
      "tranches_revenu_total":len(lines),"quintiles_de_declarants":len(q),
      "total_revenu_declare_mcad":str(total[0]),
      "total_impot_a_payer_mcad":str(total[3]),
      "total_credits_remboursables_mcad":str(total[4]),
      "net_impot_moins_credits_mcad":str(total[5]),
      "revenus_total_moins_30000_mcad":str(lower[0]),
      "impot_a_payer_moins_30000_mcad":str(lower[3]),
      "credits_remboursables_moins_30000_mcad":str(lower[4]),
      "solde_impot_moins_credits_moins_30000_mcad":str(lower[5]),
      "part_credits_remboursables_moins_30000_pourcent":str(ratio),
      "q5_part_revenu_pourcent":ind["q5_part_revenu_total_pourcent"],
      "q5_part_impot_pourcent":ind["q5_part_impot_a_payer_pourcent"],
      "credits_ou_prestations_recuperables_nova_mcad":None,
      "revenu_disponible_menages_demonstre":False,
      "simulation_incidence_reforme_nova_validee":False,
      "nombre_portes_protection_ouvertes":len(gates),
      "annees_fiscales_personnes_societes_harmonisees":False,
      "taux_propose_pour_2027_2036":None,
      "cellules_incidence_p52d_certifiees":0,
      "cellules_budget_p52b_certifiees":0,
      "montants_budget_p52b_inconnus":600,
      "incidences_p52d_inconnues":720,
      "p55n_score_estime":53
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--distribution",type=Path,required=True)
    p.add_argument("--p56k",type=Path,required=True)
    p.add_argument("--gabarit",type=Path,required=True)
    p.add_argument("--preuves",type=Path,required=True)
    p.add_argument("--barometre",type=Path,required=True)
    p.add_argument("--rapport",type=Path)
    p.add_argument("--exiger-incidence-certifiee",action="store_true")
    args=p.parse_args(argv)
    if args.exiger_incidence_certifiee:
        print("NO_GO_AUTOMATIQUE: effets ménages, crédits et services non validés",file=sys.stderr)
        return 3
    try:
        def load(path):
            return json.loads(path.read_text(encoding="utf-8"))
        result=json.dumps(audit(load(args.distribution),load(args.p56k),
               load(args.gabarit),load(args.preuves),load(args.barometre)),
               ensure_ascii=False,indent=2)+"\n"
        if args.rapport:
            with args.rapport.open("x",encoding="utf-8") as f:
                f.write(result)
        else:
            print(result,end="")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,AssertionError) as err:
        print("REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
