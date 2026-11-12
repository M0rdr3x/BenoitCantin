#!/usr/bin/env python3
"""P56N : cas officiel 2026, aides ponctuelles et limites d'une simulation Nova."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

URLS={
"REVENU_DISPONIBLE":"https://www.quebec.ca/finances-impots-et-taxes/credits-impots-deductions/estimer-revenu-disponible",
"RETRAITE_QUEBEC":"https://www.retraitequebec.gouv.qc.ca/fr/montants-prestations-et-donnees-base",
"SIMULREVENU":"https://www.simulrevenu.gouv.qc.ca/Simulation/Disponible",
"CFFP":"https://cffp.recherche.usherbrooke.ca/outils-ressources/simulateur-fiscal-quebec/"
}
COMP={
"EPICERIE_ENERGIE":("100","AIDE_PONCTUELLE_2026"),
"ALLOC_FED_EPICERIE":("358","CHANGEMENT_ALLOCATION_FEDERALE_2026_AVEC_PONCTUEL"),
"REDUC_COTISATIONS":("72","VARIATION_COTISATIONS_DU_CAS_TYPE"),
"INDEXATION_QC":("166","VARIATION_FISCALE_QUEBEC"),
"INDEXATION_FED":("150","VARIATION_FISCALE_FEDERALE")
}
AIDES={
"PERSONNE_SEULE":("100","M02","PERSONNE_SEULE"),
"MONOPARENTAL":("150","M03","FAMILLE_MONOPARENTALE"),
"COUPLE_SANS_ENFANTS":("150",None,"COUPLE_SANS_ENFANTS"),
"COUPLE_AVEC_ENFANTS":("200","M04","COUPLE_AVEC_ENFANTS")
}
FAMILY={
"par_enfant_max_cad":"3068","par_enfant_min_cad":"1221",
"supplement_monoparental_max_cad":"1077","supplement_monoparental_min_cad":"430",
"famille_monoparentale_un_enfant_max_theorique_cad":"4145",
"famille_monoparentale_un_enfant_min_theorique_cad":"1651",
"fournitures_scolaires_cad":"127","enfant_handicape_montant_annuel_cad":"2892"
}
P56M="projets/projet-nova/etudes/P56M_CADRE_MICROSIMULATION_REVENUS_MENAGES_2027_2036.json"
P56L="projets/projet-nova/etudes/P56L_BASE_DISTRIBUTIVE_PARTICULIERS_2023_CREDITS_ET_QUINTILES.json"
P55N="projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
GATES={f"N{i:02d}" for i in range(1,11)}

def require(ok,message):
    if not ok:
        raise ValueError(message)

def cad(x):
    require(type(x) is str and x.isdecimal() and (x=="0" or
            (not x.startswith("0") and len(x)<=9)),"MONTANT_CAD_INVALIDE")
    return Decimal(x)

def verifier(d,m,l,b):
    require(isinstance(d,dict) and d.get("schema_version")=="P56N-1" and
            d.get("date_etude")=="2026-11-08" and
            d.get("statut")=="REFERENCES_OFFICIELLES_2026_PAS_MICROSIMULATION_NOVA" and
            d.get("decision")=="NO_GO_AUTOMATIQUE","ENTETE_NON_CONFORME")
    scope=d.get("perimetre")
    require(isinstance(scope,dict) and scope.get("territoire")=="QUEBEC_DANS_CANADA"
            and scope.get("annees_sources")==[2025,2026] and
            scope.get("annees_projet_nova")==[2027,2036] and
            scope.get("unite_monnaie")=="CAD" and
            scope.get("unite_population")=="CAS_TYPE_NON_REPRESENTATIF",
            "PERIODES_NON_COMPARABLES")
    sources=d.get("sources")
    require(isinstance(sources,dict) and set(sources)==set(URLS),"SOURCES_MANQUANTES")
    for k,url in URLS.items():
        require(sources[k].get("url")==url and sources[k].get("original_pdf_sha256") is None,
                "SOURCE_NON_VERIFIEE")
    require(sources["REVENU_DISPONIBLE"].get("date_mise_a_jour")=="2026-06-17"
            and sources["RETRAITE_QUEBEC"].get("annee")==2026
            and sources["CFFP"].get("publication")=="2026-08-18" and
            sources["CFFP"].get("statut")=="CONTEXTE_METHODOLOGIQUE_EXTERNE_NON_AUDIT_NOVA",
            "MILLESMES_INCORRECTS")
    x=d.get("cas_type_officiel_2026")
    require(isinstance(x,dict) and x.get("id")=="M02" and
            x.get("profil")=="PERSONNE_SEULE_SALARIEE" and
            x.get("annee_depart")==2025 and x.get("annee_arrivee")==2026 and
            cad(x.get("revenu_brut_annuel_cad"))==50000 and
            cad(x.get("variation_revenu_disponible_publiee_cad"))==847,
            "CAS_TYPE_2026_NON_OFFICIEL")
    comp=x.get("contributions_a_variation_publiees_cad")
    require(isinstance(comp,list) and len(comp)==5,"COMPOSANTS_INCOMPLETS")
    seen=set()
    summation=Decimal(0)
    for r in comp:
        k=r.get("id")
        require(type(k) is str and k in COMP and k not in seen,"COMPOSANTS_DUPLIQUES")
        seen.add(k)
        require((r.get("montant"),r.get("nature"))==COMP[k] and
                r.get("recurrence_2027_validee") is False,"COMPOSANT_INVENTE")
        summation+=cad(r["montant"])
    require(seen==set(COMP) and summation==846 and
            cad(x.get("somme_composantes_cad"))==846 and
            cad(x.get("ecart_total_publie_moins_somme_cad"))==1 and
            x.get("qualification_ecart")==
            "ARRONDI_OU_DETAIL_NON_EXPLIQUE_SANS_ACCES_SORTIE_DETAILLEE" and
            x.get("ne_pas_falsifier_composantes") is True,
            "ECART_SOURCE_UN_DOLLAR_A_CONSERVER")
    require(all(x.get(k) is None for k in (
            "revenu_disponible_2025_cad","revenu_disponible_2026_cad",
            "variation_causale_nova_cad","cout_2027_2036_prevu_cad")) and
            x.get("ensemble_hypotheses_personnelles_reproduit") is False,
            "UN_EXEMPLE_N_EST_PAS_UNE_PREVISION")
    one=d.get("versement_ponctuel_provincial_2026")
    require(isinstance(one,dict) and one.get("annonce")=="2026-05-25" and
            one.get("periode")=="EXERCICE_2026_SEULEMENT" and
            one.get("source_id")=="REVENU_DISPONIBLE" and
            one.get("admissibilite")==
            "BENEFICIAIRES_DU_CREDIT_SOLIDARITE_POUR_JUILLET_2025_A_JUIN_2026" and
            one.get("prorogation_2027_2036_constatee") is False and
            one.get("versements_individuels_constates")==0 and
            one.get("revenu_recuperable_nova_cad") is None,
            "AIDE_UNIQUE_NON_AUTOMATIQUEMENT_RECURRENTE")
    items=one.get("cas")
    require(isinstance(items,list) and len(items)==4 and
            {r.get("id") for r in items}==set(AIDES),"BARÈMES_PONCTUELS_INCOMPLETS")
    for r in items:
        amount,profile,category=AIDES[r["id"]]
        require((r.get("montant_potentiel_cad"),r.get("profile_p56m"),
                 r.get("categorie"))==(amount,profile,category),"AIDE_MENAGE_INVALIDE")
    fam=d.get("allocation_famille_2026")
    require(isinstance(fam,dict) and fam.get("source_id")=="RETRAITE_QUEBEC" and
            all(fam.get(k)==v for k,v in FAMILY.items()) and
            cad(fam["par_enfant_max_cad"])+cad(fam["supplement_monoparental_max_cad"])==
            cad(fam["famille_monoparentale_un_enfant_max_theorique_cad"]) and
            cad(fam["par_enfant_min_cad"])+cad(fam["supplement_monoparental_min_cad"])==
            cad(fam["famille_monoparentale_un_enfant_min_theorique_cad"]) and
            fam.get("revenu_familial_ligne_275_determinant") is True and
            fam.get("garde_partagee_et_ages_et_presence_a_verifier") is True and
            fam.get("montant_une_famille_reelle_cad") is None and
            fam.get("projections_2027_2036_cad") is None,
            "ALLOCATION_FAMILLE_NON_CONDITIONNELLE_INVENTEE")
    rates=d.get("cotisations_parametres_2026")
    require(isinstance(rates,dict) and
            rates.get("source_id")=="REVENU_DISPONIBLE" and
            tuple(rates.get(k) for k in (
                "rrq_employe_base_taux_2025_pourcent","rrq_employe_base_taux_2026_pourcent",
                "rqap_employe_taux_2025_pourcent","rqap_employe_taux_2026_pourcent"))==
                ("5.4","5.3","0.494","0.430") and
            rates.get("calcul_integral_de_cotisation_individuelle_cad") is None and
            rates.get("hypotheses_plafonds_salaires_pas_appliquees") is True,
            "TAUX_COTISATIONS_SANS_PLAFONDS")
    limits=d.get("limitations")
    require(isinstance(limits,dict) and len(limits)>=9 and
            all(v is True for v in limits.values()),"LIMITES_NON_RECONNUES")
    t=d.get("tiers_modelisation")
    require(isinstance(t,dict) and
            t["REFERENCE_2026_SEULE"].get("cas_types_complets_reproduits")==0 and
            t["SIMULATION_NOVA_2027_2036"].get("calculs_reels_valides")==0 and
            t["EVALUATION_SOUVERAINETE"].get("services_publics_budgetes") is False,
            "SIMULATIONS_NOVA_INVENTEES")
    proofs=d.get("preuves_manquantes")
    require(isinstance(proofs,list) and len(proofs)==10 and d.get("nombre_preuves")==10 and
            {r.get("id") for r in proofs}==GATES and
            all(r.get("statut")=="NON_OBTENUE" and
                r.get("preuve_id") is None and
                r.get("expert_validation") is None for r in proofs),
            "PREUVES_SANS_JUSTIFICATION")
    integ=d.get("integration")
    require(isinstance(integ,dict) and
            (integ.get("cadre_p56m"),integ.get("registre_p56l"),integ.get("barometre_p55n"))==
            (P56M,P56L,P55N) and
            integ.get("p56m_unites_a_renseigner")==160 and
            integ.get("p56m_unites_reelles_developpees")==0 and
            integ.get("p52b_montants_inconnus")==600 and
            integ.get("p52d_incidences_inconnues")==720 and
            integ.get("p52a_preuves_non_validees")==20 and
            integ.get("p55n_estimation_pourcent")==53 and
            integ.get("revenus_disponibles_futurs_certifies")==0 and
            integ.get("nouveaux_taux_nova_proposes") is None and
            integ.get("avis_independants_nova_signes")==0 and
            integ.get("decision")=="NO_GO_AUTOMATIQUE",
            "FINANCEMENT_NOVA_NON_CERTIFIE")
    require(isinstance(m,dict) and m.get("schema_version")=="P56M-1" and
            m.get("modele_cas",{}).get("nombre_unites_archetype_regime_annee_en_attente")==160 and
            m.get("issues_conserves",{}).get("p55n_score_estimatif")==53 and
            m.get("decision")=="NO_GO_AUTOMATIQUE",
            "P56M_NON_CONCORDE")
    require(isinstance(l,dict) and l.get("schema_version")=="P56L-1" and
            l.get("p52d_incidences_inconnues")==720 and
            l.get("decision")=="NO_GO_AUTOMATIQUE",
            "P56L_NON_CONCORDE")
    require(isinstance(b,dict) and b.get("schema_version")=="P55N-1" and
            b.get("score_estimatif")==53,"BAROMETRE_NON_CONCORDE")
    return {
      "jalon":"P56N","statut":"BENCHMARKS_2026_OFFICIELS_SANS_REFORME_NOVA",
      "cas_type_50000_cad":"50000",
      "variation_officielle_2025_2026_cad":"847",
      "somme_variations_composantes_cad":str(summation),
      "ecart_non_resolu_cad":str(Decimal(847)-summation),
      "categories_aides_ponctuelles_2026":len(items),
      "allocation_famille_max_par_enfant_2026_cad":FAMILY["par_enfant_max_cad"],
      "cas_types_microsimules_et_certifies":0,
      "paiements_2026_projetes_automatiquement_2027":False,
      "incidences_P52D_nouvelles_certifiees":0,
      "p52b_montants_inconnus":600,"p52d_incidences_inconnues":720,
      "score_estime_p55n":53,"decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for x in ("references","p56m","p56l","barometre"):
        p.add_argument("--"+x,type=Path,required=True)
    p.add_argument("--rapport",type=Path)
    p.add_argument("--exiger-taux-certifie",action="store_true")
    a=p.parse_args(argv)
    if a.exiger_taux_certifie:
        print("NO_GO_AUTOMATIQUE: aucun taux Nova validé",file=sys.stderr)
        return 3
    try:
        def get(path):
            return json.loads(path.read_text(encoding="utf-8"))
        result=json.dumps(verifier(get(a.references),get(a.p56m),get(a.p56l),
                 get(a.barometre)),indent=2,ensure_ascii=False)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as f:
                f.write(result)
        else:
            print(result,end="")
        return 0
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as e:
        print("REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
