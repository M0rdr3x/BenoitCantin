#!/usr/bin/env python3
"""P56W: controler les credits remboursables observes en 2023 et droits a proteger.

Le tableau A.15 observe des montants arrondis par tranche de revenu total.
Ni le nombre de foyers, ni les montants de 2027, ni un gain Nova ne peuvent
en etre deduits. Les differences d'arrondi publiees ne doivent pas etre gommees.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys

TABLE="https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-credit-remb.asp"
A14="https://www.budget.finances.gouv.qc.ca/Budget/outils/statistiques-fiscales/somm-impot-a-payer.asp"
LINKS={
"p56l":"projets/projet-nova/etudes/P56L_BASE_DISTRIBUTIVE_PARTICULIERS_2023_CREDITS_ET_QUINTILES.json",
"p56v":"projets/projet-nova/etudes/P56V_PONT_FINANCEMENT_SERVICES_OPTIONS_FISCALES_VGQ_2027_2029.json",
"p56n":"projets/projet-nova/etudes/P56N_CAS_TYPES_2026_REFERENCES_OFFICIELLES_PRESTATIONS_ET_LIMITES.json",
"p56o":"projets/projet-nova/etudes/P56O_TABLEAU_CLOTURE_PROGRAMME_DEFINITION_100_POURCENT.json",
"p55n":"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"}
BINS=("MOINS_10000","10000_19999","20000_29999","30000_49999","50000_99999","100000_PLUS")
A14_IDS=("R00_09999","R10_19999","R20_29999","R30_49999","R50_99999","R100_PLUS")
BIN_TOTALS=(777,1118,2306,2275,2145,683)
ROWS=(
("FAMILLE",3569,"38.4",(509,364,345,806,1197,349)),
("SOLIDARITE",1709,"18.4",(128,284,552,513,220,13)),
("GARDE",975,"10.5",(35,48,68,189,384,250)),
("PRIME_TRAVAIL",306,"3.3",(46,131,75,51,4,0)),
("MAINTIEN_DOMICILE",656,"7.1",(3,23,288,192,127,22)),
("SOUTIEN_AINES",1703,"18.3",(36,216,905,431,111,3)),
("MEDICAUX",71,"0.8",(5,15,23,25,3,0)),
("AIDANTE",197,"2.1",(9,24,31,46,63,24)),
("TVQ_SALARIE",19,"0.2",(0,0,0,1,8,9)),
("ATHLETE",6,"0.1",(3,1,1,0,0,0)),
("ADOPTION",1,"0.0",(0,0,0,0,0,0)),
("BOUCLIER",34,"0.4",(1,8,13,10,2,0)),
("AUTRES",60,"0.6",(1,3,7,11,26,12))
)
BOOLEAN_LIMITS=(
"credits_remboursables_non_assimiles_a_recettes_disponibles",
"credits_2023_non_automatiquement_reconduits_a_2027",
"credits_2023_non_additionnes_aux_depenses_portefeuilles_p56v",
"minimum_de_protection_2027_2036_non_chiffre",
"suppression_des_credits_non_adoptee",
"compensation_menages_non_imputee_a_zero",
"montants_2023_non_transposes_comme_montants_2027",
"prestation_ponctuelle_2026_non_perpetualisee",
"assiette_totale_2023_non_assiette_imposable_nova_2027",
"beneficiaires_individuels_non_identifies",
"tranches_de_revenu_total_non_egales_a_quintiles",
"frais_federaux_et_cotisations_non_inclus_comme_simules")
NUM=re.compile(r"(?:0|[1-9][0-9]{0,10})\Z")

def need(ok,why):
    if not ok:
        raise ValueError(why)
def count(x):
    need(type(x) is str and NUM.fullmatch(x) is not None,"MONTANT_ENTIER_MCAD_ATTENDU")
    return int(x)

def audit(d,l,v,n,o,b):
    need(isinstance(d,dict) and d.get("schema_version")=="P56W-1" and
         d.get("date_revision")=="2026-11-08" and
         d.get("statut")=="OBSERVATIONS_OFFICIELLES_DES_DECLARANTS_2023_NON_COUT_2027_2036" and
         d.get("decision")=="NO_GO_AUTOMATIQUE",
         "BASE_SOURCE_HORS_PERIMETRE")
    prov=d.get("provenance")
    need(isinstance(prov,dict) and
         all(prov.get(k)==link for k,link in LINKS.items()) and
         prov.get("fiscal_a15",{}).get("url")==TABLE and
         prov["fiscal_a15"].get("annee_observee")==2023 and
         prov["fiscal_a15"].get("tableau")=="A.15" and
         prov["fiscal_a15"].get("verifie_sur_page_officielle") is True and
         prov.get("fiscal_a14",{}).get("url")==A14 and
         prov["fiscal_a14"].get("annee_observee")==2023 and
         prov["fiscal_a14"].get("tableau")=="A.14",
         "SOURCE_HISTORIQUE_ET_MILLESIME_NON_VERIFIES")
    need(all(isinstance(x,dict) for x in (l,v,n,o,b)) and
         l.get("schema_version")=="P56L-1" and
         l.get("annee_observee")==2023 and
         v.get("schema_version")=="P56V-1" and
         v.get("decision")=="NO_GO_AUTOMATIQUE" and
         n.get("schema_version")=="P56N-1" and
         n.get("decision")=="NO_GO_AUTOMATIQUE" and
         o.get("schema_version")=="P56O-1" and
         o.get("definition_terminee",{}).get("etat_actuel_termine") is False and
         b.get("schema_version")=="P55N-1" and
         b.get("score_estimatif")==53,
         "DEPENDANCES_NOVA_NON_CONCORDANTES")
    need(d.get("unite_montants")=="MILLIONS_DE_DOLLARS_CAD" and
         d.get("population_statistique")==
          "DECLARANTS_FISCAUX_INDIVIDUELS_NI_MENAGES_NI_BENEFICIAIRES_UNIQUES" and
         d.get("annee_reference")==2023,
         "DECLARANTS_ASSIMILES_A_FOYERS")
    bins=d.get("tranches")
    need(isinstance(bins,list) and [x.get("id") for x in bins]==list(BINS),
         "SIX_TRANCHES_DE_REVENUS_MANQUANTES")
    categories=d.get("credits_par_categorie")
    need(isinstance(categories,list) and
         [x.get("id") for x in categories]==[x[0] for x in ROWS],
         "TREIZE_CATEGORIES_INCOMPLETES")
    matrix=[]
    total_categories=0
    for entry,(id,reported,part,values) in zip(categories,ROWS):
        amounts=entry.get("montants_par_tranche_mcad")
        need(isinstance(amounts,dict) and set(amounts)==set(BINS) and
             [count(amounts[bin]) for bin in BINS]==list(values) and
             count(entry.get("total_publie_mcad"))==reported and
             entry.get("part_publiee_pourcent")==part,
             "CREDIT_A15_NON_RECONCILIE_"+id)
        rounded=sum(values)
        need(count(entry.get("somme_tranches_arrondies_mcad"))==rounded and
             entry.get("ecart_somme_arrondie_moins_total_publie_mcad")==str(rounded-reported) and
             len(entry.get("categorie",""))>=18 and
             entry.get("beneficiaires_uniques_identifies") is False and
             entry.get("nombre_de_familles_identifiees") is None and
             entry.get("effet_nova_2027_2036_mcad") is None and
             entry.get("remplacement_par_transfert_direct_legalement_valide") is False and
             entry.get("statut")=="OBSERVATION_AGREGEE_2023_NON_SIMULATION_NOVA",
             "FAUX_COMPENSATION_2027_"+id)
        matrix.append(values)
        total_categories+=reported
    totals=[]
    for i,bin in enumerate(bins):
        subtotal=sum(row[i] for row in matrix)
        expected=BIN_TOTALS[i]
        need(count(bin.get("montant_total_publie_mcad"))==expected and
             count(bin.get("somme_credits_par_categorie_arrondis_mcad"))==subtotal and
             bin.get("ecart_arrondi_somme_categories_moins_total_mcad")==str(subtotal-expected) and
             bin.get("nombre_declarants_par_tranche") is None and
             bin.get("impot_federal_par_tranche") is None and
             bin.get("effet_revenu_disponible_nova") is None,
             "COLONNE_ARRONDIS_A15_REECRITE")
        totals.append(expected)
    need(totals==[count(x["credits_remboursables_mcad"]) for x in l["tranches_a14"]] and
         [x["id"] for x in l["tranches_a14"]]==list(A14_IDS),
         "A14_ET_A15_DONNEES_NON_EQUIVALENTES")
    rounded=d.get("controle_arrondis")
    need(isinstance(rounded,dict) and
         count(rounded.get("ligne_totale_officielle_mcad"))==9305 and
         count(rounded.get("somme_totaux_par_categorie_publies_mcad"))==total_categories==9306 and
         rounded.get("ecart_somme_categories_moins_total_officiel_mcad")=="1" and
         rounded.get("ligne_totale_par_tranche_mcad")==dict(zip(BINS,map(str,BIN_TOTALS))) and
         count(rounded.get("somme_credits_total_officielle_par_tranche_mcad"))==9304 and
         rounded.get("ecart_somme_tranches_publiees_moins_total_officiel_mcad")=="-1" and
         count(rounded.get("somme_lignes_de_credits_arrondies_mcad"))==sum(map(sum,matrix)) and
         all(rounded.get(k) is True for k in (
          "erreurs_arrondis_possible_jusqua_2_mcad_par_tranche",
          "zéro_affiche_peut_indiquer_moins_0_5_mcad",
          "ne_pas_reconcilier_en_modifiant_des_lignes",
          "chiffres_arrondis_ne_pas_utiliser_pour_micro_simulation_individuelle")),
         "ERREURS_D_ARRONDIS_MASQUEES")
    need(count(l["totaux_publies_a14"]["credits_remboursables_mcad"])==9305,
         "P56L_CREDIT_TOTAL_NON_SOURCE")
    low=d.get("menages_plus_vulnerables_observations_a14")
    need(isinstance(low,dict) and low.get("seuil_revenu_total_annuel_cad")=="30000" and
         low.get("groupe_six_tranches")==list(BINS[:3]) and
         count(low.get("credits_remboursables_tous_types_mcad"))==4201 and
         count(low.get("impot_a_payer_mcad"))==285 and
         low.get("impot_net_apres_credits_remboursables_mcad")=="-3916" and
         low.get("part_credit_remboursable_total_pourcent")=="45.1" and
         low.get("statistique_2023_pas_cout_de_compensation_2027") is True and
         low.get("gains_ou_pertes_individuelles_connues") is False and
         sum(totals[:3])==4201 and
         l["agregat_sensible_moins_30000"]["credits_remboursables_mcad"]=="4201",
         "PROTECTION_DECLARANTS_SOUS_30000_NON_COHERENTE")
    quint=d.get("quintiles_observes_a3")
    source_quint=l["indicateurs_quintiles"]
    need(isinstance(quint,dict) and
         quint.get("premier_quintile_part_revenu_total_pourcent")==source_quint["q1_part_revenu_total_pourcent"]=="3.43" and
         quint.get("premier_quintile_part_impot_a_payer_pourcent")==source_quint["q1_part_impot_a_payer_pourcent"]=="0.03" and
         quint.get("dernier_quintile_part_revenu_total_pourcent")==source_quint["q5_part_revenu_total_pourcent"]=="50.10" and
         quint.get("dernier_quintile_part_impot_a_payer_pourcent")==source_quint["q5_part_impot_a_payer_pourcent"]=="69.41" and
         quint.get("quintiles_repartition_declarants_pas_repartition_menages") is True and
         quint.get("repartition_ne_permet_pas_de_deduire_effets_reforme_nova") is True,
         "QUINTILES_FISCALITE_NON_COMPARABLES")
    limits=d.get("règles_integrite")
    need(isinstance(limits,dict) and set(limits)==set(BOOLEAN_LIMITS) and
         all(limits[k] is True for k in BOOLEAN_LIMITS) and
         n["versement_ponctuel_provincial_2026"]["prorogation_2027_2036_constatee"] is False,
         "PROTECTIONS_FISCALES_BRISEES")
    proof=d.get("preuves_pour_etape_suivante")
    need(isinstance(proof,list) and len(proof)==8 and
         {x.get("id") for x in proof}=={f"W{i:02d}" for i in range(1,9)} and
         all(x.get("statut")=="NON_OBTENUE" and
             x.get("preuve_id") is None and
             len(x.get("portee",""))>=70 for x in proof),
         "AVIS_OU_COUTS_COMPENSATIONS_INVENTES")
    ind=d.get("controle_completion")
    need(isinstance(ind,dict) and
         ind.get("score_estime_p55n")==53 and
         ind.get("points_restants_estimes")==47 and
         ind.get("portes_p56o_demonstrees")==0 and
         ind.get("p52b_cellules_ouvertes")==600 and
         ind.get("p52d_incidences_inconnues")==720 and
         ind.get("p52a_preuves_a_valider")==20 and
         ind.get("citoyens_proteges_dans_simulation_nova_demonstres")==0 and
         ind.get("nouveaux_taux_nova_adoptes")==0 and
         ind.get("avis_experts_nova_signes")==0 and
         ind.get("programme_termine") is False and
         ind.get("decision")=="NO_GO_AUTOMATIQUE",
         "FAUSSE_CERTIFICATION_HUMAINE")
    return {
      "jalon":"P56W","millesime":2023,
      "credits_remboursables_officiels_mcad":"9305",
      "credits_sous_30000_mcad":"4201",
      "part_sous_30000_pourcent":"45.1",
      "nombre_categories":len(categories),"nombre_tranches":len(bins),
      "somme_categories_arrondies_mcad":str(total_categories),
      "ecart_arrondis_categories_mcad":"1",
      "ecarts_par_tranche_mcad":{BINS[i]:str(sum(row[i] for row in matrix)-BIN_TOTALS[i]) for i in range(6)},
      "credits_2027_2036_nova_certifies":False,
      "gains_revenu_disponible_nova_certifies":False,
      "budget_nova_certifie":False,
      "score_estime_pourcent":53,"points_restants_estimes":47,
      "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ("credits","p56l","p56v","p56n","p56o","barometre"):
        ap.add_argument("--"+key,type=Path,required=True)
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--certifier-gains-fiscaux-nova",action="store_true")
    args=ap.parse_args(argv)
    if args.certifier_gains_fiscaux_nova:
        print("REFUS: aucune microsimulation de pouvoir d'achat Nova certifiee",file=sys.stderr)
        return 3
    try:
        def load(f):
            return json.loads(f.read_text(encoding="utf-8"))
        out=audit(load(args.credits),load(args.p56l),load(args.p56v),
                  load(args.p56n),load(args.p56o),load(args.barometre))
        serial=json.dumps(out,ensure_ascii=False,indent=2)+"\n"
        if args.rapport:
            with args.rapport.open("x",encoding="utf-8") as target:
                target.write(serial)
        else:
            print(serial,end="")
        return 0
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as err:
        print("REFUS: "+str(err),file=sys.stderr)
        return 2
if __name__=="__main__":
    sys.exit(main())
