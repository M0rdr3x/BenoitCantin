#!/usr/bin/env python3
"""Projet Nova P56M — cadre de microsimulation, preuve et exercice fictif.

Utilisation:
    python scripts/simuler_revenu_disponible_menages_nova_p56m.py \
        --cadre .../P56M_CADRE_*.json --p56l .../P56L_*.json \
        --barometre .../P55N_*.json

Avec --exercice <JSON>: calcul arithmétique EXCLUSIVEMENT FICTIF. Il ne
vérifie ni droit fiscal, ni assiette, ni effets économiques, ni financement.
Aucune sortie ne permet d'autoriser une taxe, une réforme ou une économie.
"""
from __future__ import annotations
import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys

VERSION="P56M-1"
INCOME=("salaire_brut","revenu_autonome_net","revenu_placements_net",
        "pension_privee","autres_revenus_marchands")
BENEFITS=("credits_remboursables_quebec","credits_remboursables_federal",
          "prestations_quebec","prestations_federal","autres_transferts_publics")
LEVIES=("impot_quebec_net","impot_federal_net","cotisation_rrq","cotisation_ae",
        "cotisation_rqap","prime_ramq","cotisations_retraite_obligatoires",
        "autres_prelevements_obligatoires")
ESSENTIAL=("logement_cash","alimentation_ttc","transport_ttc","garde_enfants",
           "medicaments_ttc","energie_ttc","autres_depenses_essentielles_ttc")
EXPECTED_PROFILE={
    "M01":(1,0,0,"FAIBLE_REVENU"),
    "M02":(1,0,0,"SALARIE"),
    "M03":(1,1,0,"MONOPARENTAL"),
    "M04":(2,2,0,"FAMILLE"),
    "M05":(1,0,1,"RETRAITE"),
    "M06":(1,0,0,"BESOINS_PARTICULIERS"),
    "M07":(1,0,0,"AUTONOME"),
    "M08":(2,0,2,"RETRAITES")
}
REGIMES={"QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN"}
GATES={f"F{i:02d}" for i in range(1,11)}
SOURCES={
"GOUV_QC":"https://www.quebec.ca/finances-impots-et-taxes/credits-impots-deductions/estimer-revenu-disponible",
"SIMULREVENU":"https://www.simulrevenu.gouv.qc.ca/Simulation/Disponible",
"ISQ":"https://statistique.quebec.ca/fr/produit/publication/revenu-disponible-par-habitant-2024-quebec-et-regions"
}
DECIMAL=re.compile(r"(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,2})?\Z")

def require(condition,code):
    if not condition:
        raise ValueError(code)

def money(raw):
    require(type(raw) is str and bool(DECIMAL.fullmatch(raw)),
            "MONTANT_CAD_NON_NEGATIF_EXACT_REQUIS")
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError("MONTANT_CAD_INVALIDE") from exc

def controler(cadre,p56l,barometre):
    require(isinstance(cadre,dict) and cadre.get("schema_version")==VERSION
            and cadre.get("date_revision")=="2026-11-07" and
            cadre.get("statut")=="CADRE_DE_MICROSIMULATION_A_RENSEIGNER_SANS_RESULTATS_REELS"
            and cadre.get("decision")=="NO_GO_AUTOMATIQUE",
            "METADONNEES_P56M_INCORRECTES")
    meth=cadre.get("methode_principale")
    require(isinstance(meth,dict) and
            meth.get("unite")=="CAD_PAR_MENAGE_PAR_ANNEE"
            and meth.get("annee_cible_debut")==2027 and
            meth.get("annee_cible_fin")==2036 and
            meth.get("comparaison")=="BASELINE_ET_POLITIQUE_MESUREES_MEME_ANNEE_MENAGE_COMPOSITION_ET_PRIX"
            and all(meth.get(k) is True for k in (
                "revenu_disponible_macro_isq_non_identique_au_reste_apres_depenses",
                "credits_remboursables_comptes_seulement_dans_prestations",
                "credits_non_remboursables_deja_contenus_dans_impots_nets",
                "impots_consommation_deja_compris_dans_depenses_TTC",
                "couts_publics_hors_menages_comptes_dans_P52B_et_pas_en_economie_menage",
                "services_publics_en_nature_hors_revenu_disponible",
                "taux_candidats_nova_encore_non_definis",
                "exercice_fictif_n_est_pas_prevision_ni_statistique")),
            "DOUBLES_COMPTES_OU_ANNEES_INCOMPARABLES")
    for key,expected in (
        ("champs_monetaire_revenus",INCOME),
        ("champs_monetaire_transferts",BENEFITS),
        ("champs_monetaire_prelevements",LEVIES),
        ("champs_monetaire_essentiels",ESSENTIAL)
    ):
        require(cadre.get(key)==list(expected),"CHAMPS_MONETAIRES_NON_COMPARABLES")
    allfields=INCOME+BENEFITS+LEVIES+ESSENTIAL
    require(len(set(allfields))==len(allfields),"DOUBLON_CHAMP_MONETAIRE")
    source_list=cadre.get("sources_methodologiques")
    require(isinstance(source_list,list) and len(source_list)==len(SOURCES)
            and {s.get("id") for s in source_list if isinstance(s,dict)}==set(SOURCES),
            "SOURCES_METODOLOGIQUES_MANQUANTES")
    for s in source_list:
        require(s.get("url")==SOURCES[s["id"]] and len(s.get("usage",""))>=45,
                "PROVENANCE_METHODE_INVALIDE")
    profiles=cadre.get("archetypes")
    require(isinstance(profiles,list) and len(profiles)==len(EXPECTED_PROFILE),
            "COUVERTURE_MENAGES_INCOMPLETE")
    seen=set()
    for p in profiles:
        require(isinstance(p,dict),"MENAGE_MAL_FORME")
        k=p.get("id")
        require(type(k) is str and k in EXPECTED_PROFILE and k not in seen,
                "MENAGE_DUPLIQUE")
        seen.add(k)
        expected=EXPECTED_PROFILE[k]
        require((p.get("adultes"),p.get("enfants"),p.get("aines"),p.get("profil"))==expected
                and len(p.get("titre",""))>=15 and
                p.get("region")=="A_DETERMINER" and
                all(p.get(f) is None for f in (
                    "decile_revenu_disponible","ponderation_population",
                    "preuve_microdonnees")), "PROFIL_MENAGE_INVENTE")
    require(seen==set(EXPECTED_PROFILE),"ARCHETYPES_ABSENTS")
    regimes=cadre.get("regimes")
    require(isinstance(regimes,list) and len(regimes)==2 and
            {r.get("id") for r in regimes if isinstance(r,dict)}==REGIMES,
            "REGIMES_NON_DISTINCTS")
    a=next(r for r in regimes if r["id"]=="QUEBEC_DANS_CANADA")
    b=next(r for r in regimes if r["id"]=="QUEBEC_SOUVERAIN")
    require(a.get("federal_income_tax_preserved") is True and
            a.get("services_publics_sous_financement_p52b") is False
            and b.get("federal_income_tax_preserved") is None and
            b.get("recettes_federales_transferees_validees") is False and
            b.get("charges_souveraines_validees") is False and
            b.get("services_publics_sous_financement_p52b") is False,
            "COMPETENCES_OU_FINANCEMENT_INVENTES")
    coverage=cadre.get("modele_cas")
    require(isinstance(coverage,dict) and
            coverage.get("nombre_archetypes")==8 and
            coverage.get("nombre_regimes")==2 and
            coverage.get("annees_previsionnelles")==10 and
            coverage.get("nombre_unites_archetype_regime_annee_en_attente")==160 and
            all(coverage.get(k)==0 for k in (
                "montants_reels_popules","couverture_observee",
                "baselines_futures_confirmees","politique_nova_chiffree",
                "appariements_groupes_deciles_regions_realises",
                "effets_entreprises_PME_quantifies",
                "marges_incertitude_classees")),
            "FAUSSE_COUVERTURE_SIMULATION")
    gates=cadre.get("conditions_publication")
    require(isinstance(gates,list) and len(gates)==10 and
            {g.get("id") for g in gates if isinstance(g,dict)}==GATES and
            all(g.get("ok") is False and len(g.get("but",""))>=55 for g in gates),
            "PREUVES_PUBLICATION_NON_OBTENUES")
    issues=cadre.get("issues_conserves")
    require(isinstance(issues,dict) and
            issues.get("p52b_montants_inconnus")==600 and
            issues.get("p52d_incidences_inconnues")==720 and
            issues.get("p52a_preuves_non_validees")==20 and
            issues.get("p55n_score_estimatif")==53 and
            issues.get("taux_nova_adopte") is False and
            issues.get("amelioration_universelle_pouvoir_achat_prouvee") is False and
            issues.get("economie_nova_certifiee_mcad") is None and
            issues.get("revenu_anti_paradis_certifie_mcad") is None and
            issues.get("avis_independant_signes")==0,
            "NO_GO_FISCAL_NON_RESPECTE")
    require(isinstance(p56l,dict) and
            p56l.get("schema_version")=="P56L-1" and
            p56l.get("p52b_montants_inconnus")==600 and
            p56l.get("p52d_incidences_inconnues")==720 and
            p56l.get("p55n_score_estimatif")==53 and
            p56l.get("decision")=="NO_GO_AUTOMATIQUE",
            "P56L_NON_RECONCILIE")
    require(isinstance(barometre,dict) and
            barometre.get("schema_version")=="P55N-1" and
            barometre.get("score_estimatif")==53 and
            barometre.get("score_evalue_sur")==100 and
            sum(x["points_estimes"] for x in barometre["axes"])==53,
            "MATURITE_MODIFIEE_SANS_PREUVE")
    return {
        "jalon":"P56M",
        "statut":"PROTOTYPE_SANS_DONNEES_DE_MICROSIMULATION_NOVA",
        "archetypes":8,"regimes":2,"annees":10,
        "unites_archetype_regime_annee_a_renseigner":160,
        "montants_reels_certifies":0,"conditions_non_demontrees":10,
        "effets_PME_chiffres":False,
        "revenus_disponibles_nova_calcules":False,
        "protection_pouvoir_achat_certifiee":False,
        "p52b_inconnus":600,"p52d_inconnus":720,
        "p55n_score_estime":53,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def _scenario(raw):
    require(isinstance(raw,dict) and
            set(raw)=={"revenus","prestations","prelevements","essentiels"},
            "STRUCTURE_SCENARIO_NON_HOMOGENE")
    values={}
    for key,fields in (("revenus",INCOME),("prestations",BENEFITS),
                       ("prelevements",LEVIES),("essentiels",ESSENTIAL)):
        group=raw[key]
        require(isinstance(group,dict) and set(group)==set(fields),
                "COMPOSANTS_SCENARIO_INCOMPLETS")
        for field in fields:
            val=group[field]
            require(val is None or type(val) is str,
                    "NULL_OU_CHAINE_DECIMALE_REQUIS")
            values[field]=None if val is None else money(val)
    if any(v is None for v in values.values()):
        return {"statut":"MONTANTS_MANQUANTS_NON_IMPUTES",
                "champs_manquants":sorted(k for k,v in values.items() if v is None),
                "revenu_disponible":None,"reste_apres_essentiels":None}
    market=sum((values[k] for k in INCOME),Decimal(0))
    transfer=sum((values[k] for k in BENEFITS),Decimal(0))
    levy=sum((values[k] for k in LEVIES),Decimal(0))
    cost=sum((values[k] for k in ESSENTIAL),Decimal(0))
    disposable=market+transfer-levy
    after=disposable-cost
    return {"statut":"EXERCICE_ARITHMETIQUE_FICTIF",
            "champs_manquants":[],
            "revenus_marchands":str(market),"transferts":str(transfer),
            "prelevements":str(levy),"depenses_essentielles_cash":str(cost),
            "revenu_disponible":str(disposable),
            "reste_apres_essentiels":str(after)}

def exercice_fictif(cadre,case):
    """Compute a labelled FICTIONAL example, never an official policy result."""
    require(isinstance(case,dict) and
            case.get("type")=="EXERCICE_FICTIF_SANS_POUVOIR" and
            case.get("usage_reel_interdit") is True and
            case.get("historique_personnel_reel") is False,
            "DEMO_FICTIVE_EXPLICITE_OBLIGATOIRE")
    id=case.get("archetype_id")
    reg=case.get("regime_id")
    year=case.get("annee")
    require(type(id) is str and id in EXPECTED_PROFILE and
            type(reg) is str and reg in REGIMES and
            type(year) is int and 2027<=year<=2036,
            "MENAGE_REGIME_ANNEE_NON_COUVERT")
    require(case.get("hypothese_pouvoir_d_achat")==
            "MÊME_MENAGE_MÊME_ANNEE_MÊME_UNITE_DE_PRIX" and
            case.get("composition")==
            dict(zip(("adultes","enfants","aines"),EXPECTED_PROFILE[id][:3])) and
            case.get("region")=="QUEBEC_FICTIF_NON_REPRESENTATIF",
            "COMPOSITION_OU_PRIX_NON_COMPARABLES")
    base=_scenario(case.get("reference"))
    policy=_scenario(case.get("candidat"))
    result={
        "statut":"EXERCICE_FICTIF_SANS_POUVOIR",
        "annee":year,"archetype":id,"regime":reg,
        "reference":base,"candidat":policy,
        "variation_revenu_disponible_cad":None,
        "variation_cash_apres_essentiels_cad":None,
        "compensation_minimale_arithmetique_fictive_cad":None,
        "gain_reel_de_menage_certifie":False,
        "financement_des_services_demontre":False,
        "decision":"NO_GO_AUTOMATIQUE"
    }
    if base["revenu_disponible"] is None or policy["revenu_disponible"] is None:
        return result
    # En exercice statique, les revenus de marché restent identiques. Dans un
    # modèle dynamique, les changements de salaire exigeraient un module séparé.
    b=case["reference"]
    p=case["candidat"]
    require(all(p["revenus"][k]==b["revenus"][k] for k in INCOME),
            "REVENU_DE_MARCHE_DIFFERE_SANS_MODELE_COMPORTEMENTAL")
    if reg=="QUEBEC_DANS_CANADA":
        require(all(p["prelevements"][k]==b["prelevements"][k]
                    for k in ("impot_federal_net","cotisation_ae")),
                "FISCALITE_FEDERALE_MODIFIEE_SANS_COMPETENCE")
    delta=Decimal(policy["revenu_disponible"])-Decimal(base["revenu_disponible"])
    after=Decimal(policy["reste_apres_essentiels"])-Decimal(base["reste_apres_essentiels"])
    needed=max(Decimal(0),-after)
    result.update({
        "variation_revenu_disponible_cad":str(delta),
        "variation_cash_apres_essentiels_cad":str(after),
        "compensation_minimale_arithmetique_fictive_cad":str(needed)
    })
    return result

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cadre",required=True,type=Path)
    ap.add_argument("--p56l",required=True,type=Path)
    ap.add_argument("--barometre",required=True,type=Path)
    ap.add_argument("--exercice",type=Path)
    ap.add_argument("--autoriser-exercice-fictif",action="store_true")
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--exiger-microsimulation-certifiee",action="store_true")
    a=ap.parse_args(argv)
    if a.exiger_microsimulation_certifiee:
        print("NO_GO_AUTOMATIQUE: budget, prestations et données ménages non certifiés",file=sys.stderr)
        return 3
    try:
        def load(p):
            return json.loads(p.read_text(encoding="utf-8"))
        d=load(a.cadre)
        out=controler(d,load(a.p56l),load(a.barometre))
        if a.exercice:
            require(a.autoriser_exercice_fictif,
                    "L'EXERCICE_FICTIF_EXIGE_AUTORISATION_EXPLICITE")
            out["exercice_fictif"]=exercice_fictif(d,load(a.exercice))
        payload=json.dumps(out,ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as f:
                f.write(payload)
        else:
            print(payload,end="")
        return 0
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as exc:
        print("REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
