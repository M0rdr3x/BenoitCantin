#!/usr/bin/env python3
"""P56O — contrôler ce qui manque pour dire que le programme politique Nova est terminé.

Source du score: P55N. Le script NE calcule PAS un pourcentage à partir des
commits ou tests. Il suit une définition de fini en huit axes et dix portes.
La validation du registre ne remplace aucune attestation humaine indépendante.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

AXES = {"VISION","INSTITUTIONS","CONSTITUTION","SECTEURS",
        "FISCALITE","TRANSITION","EXPERTISE","ADOPTION"}
GATES = {"FIN_BUDGET","FIN_INC","FIN_MUNICIPAL","SERVICES","LEGAL",
         "ELECTORAL","TRANSITION","EXPERTS","CONSULTATIONS","ADOPTION"}
PRIORITIES = {f"N{i:02d}" for i in range(1,13)}
WAVES = {f"V{i}" for i in range(1,6)}
P52B_REGIMES = {"QUEBEC_DANS_CANADA","QUEBEC_SOUVERAIN"}
P52B_TRACKS = {"central","prudent","stress"}
P52B_YEARS = set(range(2027,2037))
SOURCE_PATHS = {
    "barometre":"projets/projet-nova/etudes/P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json",
    "model_decennal":"projets/projet-nova/etudes/P52B_GABARIT_MODELE_DECENNAL.json",
    "reg_fiscal":"projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json",
    "cas_menages":"projets/projet-nova/etudes/P56M_CADRE_MICROSIMULATION_REVENUS_MENAGES_2027_2036.json",
    "ref_officielle":"projets/projet-nova/etudes/P56N_CAS_TYPES_2026_REFERENCES_OFFICIELLES_PRESTATIONS_ET_LIMITES.json"
}

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def unique(rows,key,expected,label):
    require(isinstance(rows,list) and len(rows)==len(expected),
            f"{label}_LONGUEUR_INVALIDE")
    ids=[x.get(key) for x in rows if isinstance(x,dict)]
    require(len(ids)==len(rows) and len(ids)==len(set(ids)) and set(ids)==expected,
            f"{label}_IDENTIFIANTS_NON_EXHAUSTIFS")

def p52b_counts(data):
    require(data.get("schema_version")=="P52B-1" and
            isinstance(data.get("regimes"),dict) and
            set(data["regimes"])==P52B_REGIMES,
            "SOURCE_P52B_NON_CONFORME")
    unknown=0
    rows=0
    for regime,body in data["regimes"].items():
        tracks=body.get("trajectoires")
        require(isinstance(tracks,dict) and set(tracks)==P52B_TRACKS,
                "TRAJECTOIRES_P52B_INCOMPLETES")
        for scenario,years in tracks.items():
            require(isinstance(years,list) and len(years)==10 and
                    {x.get("exercice_debut") for x in years}==P52B_YEARS,
                    "EXERCICES_DECENNAUX_INCOMPLETS")
            for year in years:
                rows+=1
                revenue,expense=year.get("recettes"),year.get("depenses")
                require(isinstance(revenue,dict) and isinstance(expense,dict),
                        "STRUCTURE_BUDGETAIRE_NON_CONFORME")
                unknown+=sum(v is None for v in revenue.values())
                unknown+=sum(v is None for v in expense.values())
    require(rows==60,"COUVERTURE_BUDGET_NON_COMPLETE")
    return rows,unknown

def analyser(reg,bar,model,fiscal,households,refs):
    require(isinstance(reg,dict) and reg.get("schema_version")=="P56O-1" and
            reg.get("date_revision")=="2026-11-08" and
            reg.get("objet")=="DEFINITION_FORMELLE_DE_COMPLETION_DU_PROGRAMME_POLITIQUE_ET_PLAN_DE_CLOTURE" and
            reg.get("portee")=="PROGRAMME_POLITIQUE_CANDIDAT_NON_EXERCICE_DU_POUVOIR" and
            reg.get("decision")=="NO_GO_AUTOMATIQUE",
            "DEFINITION_FIN_NON_TRAÇABLE")
    require(reg.get("source_controle")==SOURCE_PATHS,"PROVENANCE_BAROMETRE_NON_RECONCILIEE")
    require(isinstance(bar,dict) and bar.get("schema_version")=="P55N-1" and
            bar.get("score_evalue_sur")==100 and
            isinstance(bar.get("fourchette_prudente"),list) and
            len(bar["fourchette_prudente"])==2,
            "P55N_INVALIDE")
    score=bar["score_estimatif"]
    require(type(score) is int and 0<=score<=100,"SCORE_HORS_LIMITES")
    axes=reg.get("axes")
    source_axes=bar.get("axes")
    unique(axes,"id",AXES,"AXES_P56O")
    unique(source_axes,"id",AXES,"AXES_P55N")
    source={x["id"]:x for x in source_axes}
    axes_points={}
    for x in axes:
        b=source[x["id"]]
        require(x.get("titre")==b.get("titre") and
                type(x.get("maximum")) is int and
                type(x.get("points_estimes")) is int and
                x["maximum"]==b["maximum"] and
                x["points_estimes"]==b["points_estimes"] and
                0<=x["points_estimes"]<=x["maximum"] and
                x.get("points_restant")==x["maximum"]-x["points_estimes"] and
                x.get("lacune")==b["lacune"] and
                x.get("preuve_actuelle")==b["preuve_documentaire"],
                "AXE_SCORE_OU_SOURCE_MODIFIE")
        require(x.get("revalorisation_en_attente") is True and
                x.get("validation_independante_signee") is False,
                "ATTRIBUTION_DE_CERTIFICATION_SANS_PIECE")
        axes_points[x["id"]]=x["maximum"]-x["points_estimes"]
    require(sum(x["points_estimes"] for x in axes)==score and
            sum(x["maximum"] for x in axes)==100,
            "POINTS_NON_ADDIFS")
    expected=reg.get("metadonnees_qualification")
    require(isinstance(expected,dict) and
            expected.get("score_version")==bar["schema_version"] and
            expected.get("score_source_date")==bar["date_evaluation"] and
            expected.get("estimation_centrale_pourcent")==score and
            expected.get("intervalle_prudent_pourcent")==bar["fourchette_prudente"] and
            expected.get("estimation_non_certifiee") is True and
            expected.get("nb_points_estimes_restant")==100-score and
            expected.get("statut")=="OUVERT" and
            expected.get("decision")=="NO_GO_AUTOMATIQUE",
            "AFFICHAGE_SCORE_INCOHERENT")
    gates=reg.get("portes")
    src_gates=bar.get("portes_de_completion")
    unique(gates,"id",GATES,"PORTES_P56O")
    unique(src_gates,"id",GATES,"PORTES_P55N")
    src_gate={x["id"]:x for x in src_gates}
    closed=0
    for g in gates:
        original=src_gate[g["id"]]
        require(g.get("statut")==original["statut"] and
                g.get("enjeu")==original["preuve"] and
                g.get("axe_principal") in AXES and
                isinstance(g.get("critere_objectif"),str) and
                len(g["critere_objectif"])>=70 and
                isinstance(g.get("responsable_fonctionnel_requis"),str) and
                len(g["responsable_fonctionnel_requis"])>=18,
                "PORTE_SANS_CRITERE_VERIFIABLE")
        if g["statut"]=="NON_DEMONTRE":
            require(g.get("piece_justificative_id") is None and
                    g.get("provenance_verifiee") is False and
                    g.get("approbation_humaine_formelle") is False and
                    g.get("decision")=="NO_GO",
                    "PORTE_NON_PROUVEE_FAUSSEMENT_FERMEE")
        else:
            require(g["statut"]=="PROUVE" and
                    isinstance(g.get("piece_justificative_id"),str) and
                    len(g["piece_justificative_id"])>=12 and
                    g.get("provenance_verifiee") is True and
                    g.get("approbation_humaine_formelle") is True and
                    g.get("decision")=="REVUE_HUMAINE",
                    "PORTE_DECLAREE_FERMEE_SANS_AVIS_HUMAIN")
            closed+=1
    priorities=reg.get("priorites")
    src_priorities=bar.get("priorites")
    unique(priorities,"id",PRIORITIES,"PRIORITES_P56O")
    unique(src_priorities,"id",PRIORITIES,"PRIORITES_P55N")
    src_prio={x["id"]:x for x in src_priorities}
    done=0
    for task in priorities:
        original=src_prio[task["id"]]
        require((task.get("rang"),task.get("axe"),task.get("urgence"),
                 task.get("livrable"),task.get("preuve_acceptation"),
                 task.get("statut"))==
                (original["rang"],original["axe"],original["priorite"],
                 original["livrable"],original["preuve_acceptation"],
                 original["statut"]),
                "PRIORITE_DIVERGENTE_P55N")
        if task["statut"]=="OUVERT":
            require(task.get("piece_livrable_id") is None and
                    task.get("controle_qualite_independant") is False,
                    "LIVRABLE_NON_FERME_CERTIFIE")
        else:
            require(task["statut"]=="CLOS" and
                    task.get("controle_qualite_independant") is True and
                    isinstance(task.get("piece_livrable_id"),str) and
                    len(task["piece_livrable_id"])>=12,
                    "LIVRABLE_DECLARE_FERME_NON_PROUVE")
            done+=1
    waves=reg.get("vagues")
    unique(waves,"id",WAVES,"VAGUES")
    covered=set()
    for wave in waves:
        require(isinstance(wave.get("titre"),str) and len(wave["titre"])>=25 and
                wave.get("chemin_critique") is True and
                wave.get("statut","").startswith("BLOQUE_") and
                isinstance(wave.get("priorites"),list) and
                isinstance(wave.get("preuves"),list) and
                set(wave["priorites"]).issubset(PRIORITIES) and
                set(wave["preuves"]).issubset(GATES),
                "VAGUE_SANS_RESULTAT_VERIFIABLE")
        covered.update(wave["priorites"])
    require(covered==PRIORITIES,"PRIORITES_NON_COUVERTES")
    budgetrows,missing=p52b_counts(model)
    require(isinstance(fiscal,dict) and
            isinstance(fiscal.get("required_evidence"),list) and
            len(fiscal["required_evidence"])==20 and
            {x.get("id") for x in fiscal["required_evidence"]}==
            {f"F{i:02d}" for i in range(1,21)},
            "PREUVES_P52A_NON_IDENTIFIABLES")
    unverified=sum(x["statut"]!="VALIDE" for x in fiscal["required_evidence"])
    require(isinstance(households,dict) and
            households.get("schema_version")=="P56M-1" and
            households.get("modele_cas",{}).get("nombre_unites_archetype_regime_annee_en_attente")==160,
            "P56M_NON_SOURCE")
    observed=households["modele_cas"]["montants_reels_popules"]
    require(isinstance(refs,dict) and refs.get("schema_version")=="P56N-1" and
            refs.get("integration",{}).get("p56m_unites_reelles_developpees")==observed and
            refs.get("decision")=="NO_GO_AUTOMATIQUE",
            "P56N_ET_P56M_NON_CONCORDANTS")
    inventory=reg.get("inventaire_manquants")
    require(isinstance(inventory,dict) and
            inventory.get("postes_decennaux_p52b")==missing and
            inventory.get("incidences_fiscales_p52d")==
            refs["integration"]["p52d_incidences_inconnues"] and
            inventory.get("preuves_legalite_fiscale_p52a")==unverified and
            inventory.get("cas_menages_reels_p56m_sur_160")==observed and
            inventory.get("justificatifs_financiers_certifies_nova")==0 and
            inventory.get("avis_independants_signes")==bar["constats_non_ambigus"]["mandats_independants_signes"] and
            inventory.get("portes_de_fin_satisfaites")==closed and
            inventory.get("priorites_closes")==done,
            "INVENTAIRE_MANQUANTS_NON_RECONCILIE")
    definition=reg.get("definition_terminee")
    require(isinstance(definition,dict) and definition.get("pourcentage_requis")==100 and
            all(definition.get(x) is True for x in (
                "axes_tous_au_maximum",
                "portes_toutes_documentees_et_approuvees",
                "p52b_budget_decennal_sans_null_et_scenarios_reconcilies",
                "p52d_incidence_sans_null_avec_mesures_protection_et_poids",
                "p52a_20_preuves_validees_avec_justificatifs_independants",
                "avis_independants_signes_avec_reserves_traitees",
                "revue_redactionnelle_et_approbation_formelle_versionnee",
                "consultation_documentee",
                "zero_economie_non_prouvee",
                "deux_regimes_juridiquement_distincts",
                "aucune_validation_automatique_suffisante_a_elle_seule")),
            "DEFINITION_TERMINEE_INSUFFISANTE")
    fundamentally_ready=(score==100 and closed==len(GATES) and
                         missing==0 and unverified==0 and
                         inventory["incidences_fiscales_p52d"]==0 and
                         inventory["avis_independants_signes"]>0 and
                         done==len(PRIORITIES))
    if not fundamentally_ready:
        require(definition.get("etat_actuel_termine") is False and
                definition.get("date_termine") is None and
                definition.get("responsable_attestation_finale") is None,
                "FAUSSE_ANNONCE_100_POURCENT")
    else:
        # Le script ne peut authentifier une approbation professionnelle ou humaine.
        require(definition.get("etat_actuel_termine") is False,
                "VALIDATION_HUMAINE_PAS_AUTORISABLE_PAR_SCRIPT")
    separation=reg.get("separation_statuts")
    require(isinstance(separation,dict) and
            set(separation)=={
                "PRET_A_RELECTURE","PROGRAMME_COMPLET_A_100",
                "APPLIQUE_PAR_LE_GOUVERNEMENT"},
            "PROGRAMME_ET_EXERCICE_DU_POUVOIR_CONFONDUS")
    forbidden=reg.get("prohibitions")
    require(isinstance(forbidden,dict) and len(forbidden)>=9 and
            all(v is True for v in forbidden.values()),"GARDE_FOUS_VIOLES")
    return {
        "jalon":"P56O","score_estime_pourcent":score,
        "fourchette_prudente_pourcent":bar["fourchette_prudente"],
        "points_restants_estimes":100-score,
        "points_restants_par_axe":axes_points,
        "axes_au_maximum":sum(x["points_restant"]==0 for x in axes),
        "axes_total":len(axes),
        "portes_fermees_documentairement":closed,"portes_total":len(gates),
        "priorites_closes_documentairement":done,"priorites_total":len(priorities),
        "trajectoires_regime_scenario_annee":budgetrows,
        "valeurs_budgetaires_p52b_inconnues":missing,
        "preuves_fiscales_p52a_non_validees":unverified,
        "incidences_p52d_inconnues_declares":inventory["incidences_fiscales_p52d"],
        "cas_menages_reels_p56m":observed,
        "avis_independants_signes":inventory["avis_independants_signes"],
        "candidat_a_attestation_humaine_finale":fundamentally_ready,
        "programme_termine_et_atteste":False,
        "date_de_fin_validee":None,
        "nombre_commits_influence_score":False,
        "decision":"NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    for x in ("cloture","barometre","p52b","p52a","p56m","p56n"):
        ap.add_argument("--"+x,type=Path,required=True)
    ap.add_argument("--rapport",type=Path)
    ap.add_argument("--declarer-programme-termine",action="store_true")
    a=ap.parse_args(argv)
    if a.declarer_programme_termine:
        print("REFUS: signature humaine et revue externe indispensables",file=sys.stderr)
        return 3
    try:
        def read(path):
            return json.loads(path.read_text(encoding="utf-8"))
        result=analyser(read(a.cloture),read(a.barometre),read(a.p52b),
                        read(a.p52a),read(a.p56m),read(a.p56n))
        payload=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.rapport:
            with a.rapport.open("x",encoding="utf-8") as fd:
                fd.write(payload)
        else:
            print(payload,end="")
        return 0
    except (ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as err:
        print("REFUS: "+str(err),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
