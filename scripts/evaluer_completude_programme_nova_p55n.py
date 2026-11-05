#!/usr/bin/env python3
"""P55N : baromètre éditorial NON certifiant de complétude du programme Nova.

Ce score est un jugement manuel daté, pas une mesure objectivée par les commits.
Ne sollicite aucun réseau, n'active aucune politique et ne valide aucune économie.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/"projets"/"projet-nova"
CONFIG=PROJECT/"etudes"/"P55N_BAROMETRE_COMPLETUDE_PROGRAMME_2026.json"
NO_GO="NO_GO_AUTOMATIQUE"
MAXIMUM=100
EXPECTED={
    "VISION":(10,10),
    "INSTITUTIONS":(15,13),
    "CONSTITUTION":(15,12),
    "SECTEURS":(15,9),
    "FISCALITE":(20,5),
    "TRANSITION":(10,4),
    "EXPERTISE":(10,0),
    "ADOPTION":(5,0),
}
EXPECTED_GATES={
    "FIN_BUDGET","FIN_INC","FIN_MUNICIPAL","SERVICES","LEGAL",
    "ELECTORAL","TRANSITION","EXPERTS","CONSULTATIONS","ADOPTION",
}
EXPECTED_PROTECTIONS={
    "pas_de_pourcentage_certifie","pas_de_scores_a_partir_nombre_commits",
    "score_ne_vaut_pas_adoption","score_ne_vaut_pas_faisabilite",
    "la_ci_ne_certifie_pas_un_plan_fiscal",
    "toute_revalorisation_exige_une_preuve",
    "aucune_abrogation_fiscale_automatique",
    "aucun_taux_fiscal_sans_etude","tous_services_et_emplois_proteges",
    "pouvoir_achat_prioritaire","ne_pas_confondre_deux_scenarios",
    "aucune_economie_de_residu_comptable",
    "pas_d_avis_professionnel_invente",
    "aucune_demande_d_identites_personnelles",
    "aucun_contact_externe","aucune_depense",
    "pas_de_changement_sinjira","pas_de_fusion_main",
    "no_go_automatique",
}
EXPECTED_UNKNOWN={
    "dossiers_preuves_fiscales_p52a_ouverts":20,
    "entrees_financieres_p52b_inconnues":600,
    "montants_incidence_p52d_inconnus":720,
    "rapports_originaux_p55h_actuels_verifies_sha":0,
    "mandats_independants_signes":0,
}
EXPECTED_FALSE={
    "taux_definitif_adopte","rendement_additionnel_anti_evasion_certifie",
    "estimation_est_une_mesure_officielle",
    "autorisation_legale_parti_verifiee",
    "programme_global_integralement_finance",
    "main_fusionnee","sinjira_modifie",
}
CANDIDATE_DOCS={
    "projets/projet-nova/official/reference/programme.md",
    "projets/projet-nova/official/reference/corpus.md",
    "projets/projet-nova/official/reference/statuts.md",
    "projets/projet-nova/DOCUMENT_CONTROL.md",
    "projets/projet-nova/etudes/P52A_FAISABILITE_FISCALE_DEUX_REGIMES.md",
    "projets/projet-nova/etudes/P52B_METHODOLOGIE_SIMULATION_FISCALE.md",
    "projets/projet-nova/etudes/P55M_NOTE_SOMHAC_RESERVES_CONVENTIONS_2024.md",
}

def require(ok,why):
    if not ok:
        raise ValueError(why)

def validate(config,check_files=True):
    require(type(config) is dict and
            config.get("schema_version")=="P55N-1" and
            config.get("date_evaluation")=="2026-11-05" and
            config.get("objet")==
                "ESTIMATION_AVANCEMENT_PROGRAMME_COMPLET_DEFENDABLE_NON_STATUT_DE_GOUVERNEMENT" and
            config.get("methode")==
                "JUGEMENT_EDITO_ANALYTIQUE_PONDERE_NON_AUDIT_INDEPENDANT" and
            config.get("champ")==
                "TEXTES_DE_REFERENCE_CANDIDATS_ET_ETUDES_DU_DEPOT_GITHUB_BRANCHE_PR673" and
            config.get("decision")==NO_GO,
            "P55N_METADONNEES_INCOHERENTES")
    axes=config.get("axes")
    require(type(axes) is list and len(axes)==len(EXPECTED),
            "P55N_HUIT_AXES_EXIGES")
    seen=set()
    for axis in axes:
        require(type(axis) is dict
                and set(axis)=={
                    "id","titre","maximum","points_estimes",
                    "preuve_documentaire","lacune","mesure",
                } and axis["id"] in EXPECTED
                and axis["id"] not in seen
                and type(axis["maximum"]) is int
                and type(axis["points_estimes"]) is int
                and 0<=axis["points_estimes"]<=axis["maximum"]
                and (axis["maximum"],axis["points_estimes"])==
                    EXPECTED[axis["id"]]
                and type(axis["titre"]) is str and axis["titre"]
                and type(axis["lacune"]) is str and axis["lacune"]
                and type(axis["preuve_documentaire"]) is list
                and axis["preuve_documentaire"]
                and all(type(p) is str and p in CANDIDATE_DOCS
                        for p in axis["preuve_documentaire"])
                and type(axis["mesure"]) is str
                and axis["mesure"] in {
                    "MATURITE_REDACTIONNELLE_MANUELLE",
                    "AUCUNE_ATTESTATION_INDEPENDANTE_VERIFIEE_DANS_LE_PERIMETRE",
                    "AUCUNE_ADOPTION_FORMELLE_ATTESTEE_DANS_LE_PERIMETRE",
                },
                "P55N_AXE_INVALIDE")
        seen.add(axis["id"])
    require(seen==set(EXPECTED),"P55N_AXE_MANQUANT")
    maximum=sum(a["maximum"] for a in axes)
    score=sum(a["points_estimes"] for a in axes)
    require(maximum==MAXIMUM and score==53 and
            type(config.get("score_evalue_sur")) is int
            and config["score_evalue_sur"]==MAXIMUM
            and type(config.get("score_estimatif")) is int
            and config["score_estimatif"]==score
            and config.get("fourchette_prudente")==[45,60],
            "P55N_SCORE_NON_TRACE")
    gates=config.get("portes_de_completion")
    require(type(gates) is list and len(gates)==len(EXPECTED_GATES)
            and {g.get("id") for g in gates}==EXPECTED_GATES
            and all(type(g) is dict
                    and set(g)=={"id","statut","preuve"}
                    and g["statut"]=="NON_DEMONTRE"
                    and type(g["preuve"]) is str and g["preuve"]
                    for g in gates),
            "P55N_PORTE_NON_DOCUMENTEE_OU_CLOTUREE_SANS_PREUVE")
    priorities=config.get("priorites")
    require(type(priorities) is list and len(priorities)==12
            and {p.get("id") for p in priorities}==
                {"N"+str(i).zfill(2) for i in range(1,13)}
            and {p.get("rang") for p in priorities}==
                set(range(1,13))
            and all(type(p) is dict and set(p)=={
                "id","rang","axe","priorite","livrable","preuve_acceptation","statut"}
                and p["rang"]==int(p["id"][1:])
                and p["axe"] in EXPECTED
                and p["priorite"] in {"CRITIQUE","ELEVEE"}
                and p["statut"]=="OUVERT"
                and type(p["livrable"]) is str and p["livrable"]
                and type(p["preuve_acceptation"]) is str and p["preuve_acceptation"]
                for p in priorities),
            "P55N_PRIORITES_NON_VERIFIABLES")
    facts=config.get("constats_non_ambigus")
    require(type(facts) is dict
            and facts.get("programme_public_derniere_consolidation")=="2026-08-26"
            and facts.get("programme_public_non_adopte") is True
            and facts.get("etudes_fiscales_p52a_non_adoptees") is True
            and facts.get("scenarios_fiscaux_a_distinguer")==[
                "QUEBEC_AU_SEIN_DU_CANADA","QUEBEC_SOUVERAIN_HYPOTHETIQUE"]
            and facts.get("deux_prelevements_proposes")==[
                "IMPOT_REVENUS_PERSONNES_ET_ENTREPRISES",
                "MECANISME_ANTI_PARADIS_FISCAUX_A_DEFINIR"]
            and facts.get("economies_certifiees_cad") is None
            and all(type(facts.get(k)) is int and facts[k]==value
                    for k,value in EXPECTED_UNKNOWN.items())
            and all(facts.get(k) is False for k in EXPECTED_FALSE),
            "P55N_FAITS_OU_LACUNES_NON_CONFORMES")
    laws=config.get("references_reglementaires")
    require(type(laws) is list and len(laws)==3
            and all(type(v) is dict
                    and set(v)=={"objet","source","portee"}
                    and v["source"].startswith("https://")
                    and type(v["portee"]) is str and v["portee"]
                    for v in laws),
            "P55N_SOURCES_OFFICIELLES_ABSENTES")
    safeguards=config.get("protections")
    require(type(safeguards) is dict
            and set(safeguards)==EXPECTED_PROTECTIONS
            and all(v is True for v in safeguards.values()),
            "P55N_GARDES_INTERPRETATIVES_MANQUANTES")
    if check_files:
        for rel in CANDIDATE_DOCS:
            path=ROOT/rel
            require(path.is_file() and not path.is_symlink()
                    and path.resolve().is_relative_to(ROOT.resolve()),
                    "P55N_PREUVE_DOCUMENTAIRE_LOCALE_ABSENTE")
        current=(ROOT/"projets/projet-nova/official/reference/programme.md").read_text(
            encoding="utf-8")
        fiscal=(ROOT/"projets/projet-nova/etudes/P52A_FAISABILITE_FISCALE_DEUX_REGIMES.md").read_text(
            encoding="utf-8")
        require("Dernière consolidation publique : 26 août 2026" in current
                and "programme candidat, non adopté comme loi" in current
                and "NON ADOPTÉE, NON BUDGÉTÉE, NON CERTIFIÉE" in fiscal,
                "P55N_STATUT_SOURCE_CHANGEMENT_NON_REEXAMINE")
    return {"maximum":maximum,"score":score,
            "portes_non_demontrees":len(gates),
            "priorites_ouvertes":len(priorities)}

def load():
    with CONFIG.open(encoding="utf-8") as fp:
        doc=json.load(fp)
    validate(doc)
    return doc

def report(config):
    facts=validate(config)
    return {
        "schema_version":"P55N-BILAN-PUBLIC-1",
        "date_evaluation":config["date_evaluation"],
        "pourcentage_estimatif":facts["score"],
        "fourchette_prudente_pourcent":config["fourchette_prudente"],
        "estimation_subjective_non_certifiee":True,
        "evaluation_basee_sur_nombre_de_commits":False,
        "programme_candidat_non_adopte":True,
        "programme_integralement_finance":False,
        "nouveau_taux_fiscal_adopte":False,
        "avis_independants_signes":0,
        "portes_non_demontrees":facts["portes_non_demontrees"],
        "priorites_ouvertes":facts["priorites_ouvertes"],
        "travaux_acheves_automatiquement":0,
        "prochaine_priorite":config["priorites"][0]["id"],
        "economies_certifiees_cad":None,
        "decision":NO_GO,
    }

def table(config):
    facts=validate(config)
    return {
        "schema_version":"P55N-TABLE-PUBLIQUE-1",
        "date_evaluation":config["date_evaluation"],
        "methode":config["methode"],
        "axes":config["axes"],
        "points_maximum":facts["maximum"],
        "points_estimes":facts["score"],
        "portes_de_completion":config["portes_de_completion"],
        "priorites":config["priorites"],
        "constats":config["constats_non_ambigus"],
        "avertissement":"APPRECIATION_EDITEUR_NON_MESURE_OBJECTIVE_NON_PRETE_A_APPLIQUER",
        "decision":NO_GO,
    }

def write_new(path, obj):
    target=Path(path).expanduser().absolute()
    require(target.parent.is_dir() and not target.parent.is_symlink()
            and not target.exists() and not target.is_symlink(),
            "P55N_SORTIE_REFUSEE")
    payload=(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode("utf-8")
    flags=os.O_CREAT|os.O_EXCL|os.O_WRONLY
    if hasattr(os,"O_NOFOLLOW"):
        flags|=os.O_NOFOLLOW
    fd=os.open(target,flags,0o600)
    try:
        with os.fdopen(fd,"wb") as stream:
            stream.write(payload)
    except Exception:
        target.unlink(missing_ok=True)
        raise

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bilan-public")
    p.add_argument("--table-public")
    p.add_argument("--exiger-complet",action="store_true")
    p.add_argument("--exiger-pret-a-appliquer",action="store_true")
    opt=p.parse_args(argv)
    try:
        cfg=load()
        outputs=[Path(x).expanduser().absolute()
                 for x in (opt.bilan_public,opt.table_public) if x]
        require(len({p.resolve() for p in outputs})==len(outputs),
                "P55N_DEUX_SORTIES_IDENTIQUES")
        for target in outputs:
            require(target.parent.is_dir() and not target.parent.is_symlink()
                    and not target.exists() and not target.is_symlink(),
                    "P55N_CHEMIN_EXISTANT_OU_PARENT_INVALIDE")
        r=report(cfg)
        if opt.bilan_public:
            write_new(opt.bilan_public,r)
        if opt.table_public:
            write_new(opt.table_public,table(cfg))
        print(json.dumps(r,ensure_ascii=False,sort_keys=True))
        return 3 if opt.exiger_complet or opt.exiger_pret_a_appliquer else 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError):
        print("P55N_REFUS: SCORE_OU_PREUVES_NON_CONFORMES",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
