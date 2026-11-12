#!/usr/bin/env python3
"""P53O: aiguillage vers les sources officielles, sans authentification des pièces."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import preparer_acquisition_preuves_nova_p53n as p53n

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "projets/projet-nova/etudes/P53O_MATRICE_SOURCES_OFFICIELLES.json"
NO_GO = "NO_GO_AUTOMATIQUE"
REGIMES = p53n.REGIMES
PHASES = (
    "P0_IDENTIFIER_ORGANISME_COMPETENCE_PERIMETRE",
    "P1_CONSULTER_PUBLICATIONS_EXISTANTES",
    "P2_IDENTIFIER_PIECES_PRIMAIRES_LACUNAIRES",
    "P3_EXAMINER_ACCES_ET_CONFIDENTIALITE",
    "P4_EVALUER_SERVICES_EMPLOIS_COUTS_COMPLETS",
    "P5_REVUE_INDEPENDANTE_ET_DECISION_HABILITEE",
)
SOURCES = {
    "SEAO_DONNEES": (
        "https://www.donneesquebec.ca/recherche/dataset/systeme-electronique-dappel-doffres-seao",
        "CONTRATS_PUBLICS_SOUS_RESERVE_CHAMP_PUBLICATION",
    ),
    "SEAO_QUEBEC": (
        "https://www.quebec.ca/gouvernement/services-organisations-publiques/services-transformation-numerique/systeme-electronique-dappel-doffres-seao",
        "CADRE_ET_PUBLICATION_MARCHES",
    ),
    "MAMH_FINANCES": (
        "https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier",
        "ORGANISMES_MUNICIPAUX_SEULEMENT",
    ),
    "SCT_PERFORMANCE": (
        "https://www.tresor.gouv.qc.ca/performance-de-letat",
        "REFERENTIEL_PERFORMANCE_NON_GRAND_LIVRE",
    ),
    "CMQ_AUDIT": (
        "https://www.cmq.gouv.qc.ca/fr/verification-municipale/questions-frequentes",
        "METHODES_AUDIT_MUNICIPAL_NON_CERTIFICATION_DOSSIER",
    ),
    "CAI_ACCES": (
        "https://www.cai.gouv.qc.ca/acces-documents-organismes-publics/citoyens-acces-documents-publics/comment-acceder-documents-organismes-publics",
        "DROITS_ACCES_ET_RESTRICTIONS",
    ),
    "QUEBEC_ACCES": (
        "https://www.quebec.ca/acces-information",
        "PROCEDURE_DEMANDE_ORGANISME_DETENTEUR",
    ),
}
PER_CATEGORIE = {
    "ACHATS_REGROUPES_SANS_EXCLUSION": ("SEAO_DONNEES","SEAO_QUEBEC","SCT_PERFORMANCE","CAI_ACCES"),
    "SIMPLIFICATION_FORMALITES": ("SCT_PERFORMANCE","CMQ_AUDIT","QUEBEC_ACCES"),
    "ENERGIE_ET_BATIMENTS": ("SEAO_DONNEES","MAMH_FINANCES","SCT_PERFORMANCE","CMQ_AUDIT"),
    "ENTRETIEN_PREVENTIF": ("SEAO_DONNEES","MAMH_FINANCES","SCT_PERFORMANCE","CMQ_AUDIT"),
    "LOGICIELS_ET_LICENCES": ("SEAO_DONNEES","SEAO_QUEBEC","SCT_PERFORMANCE","CAI_ACCES"),
    "RENOUVELLEMENT_CONTRATS": ("SEAO_DONNEES","SEAO_QUEBEC","SCT_PERFORMANCE","CAI_ACCES"),
}
ETATS = ("NON_CONSULTE","PAGE_PUBLIQUE_REPEREE_NON_PIECE",
         "DOCUMENT_CANDIDAT_NON_AUTHENTIFIE")
DECL_KEYS = {
    "schema_version","regime","categorie","sources_consultees",
    "statut_competence","statut_donnees_services","statut_droits_acces",
}
SOURCE_ROW_KEYS = {"id","url","portee","statut","pieces_transactionnelles_authentifiees"}

def require(condition,code):
    if not condition:
        raise ValueError(code)

def read_json(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=40000,
            "FICHIER_INVALIDE")
    doc=json.loads(p.read_text(encoding="utf-8"))
    require(type(doc) is dict,"OBJET_JSON_ATTENDU")
    return doc

def sources():
    previous, p53n_cfg, orgs, dossiers = p53n.sources()
    cfg=read_json(SOURCE)
    require(cfg.get("schema_version")=="P53O-1"
            and cfg.get("statut")=="MATRICE_DE_REPERAGE_NON_AUTHENTIFIEE"
            and cfg.get("regimes")==list(REGIMES)
            and cfg.get("categories")==previous["categories"]
            and cfg.get("phases")==list(PHASES)
            and cfg.get("sources_par_categorie")=={k:list(v) for k,v in PER_CATEGORIE.items()}
            and len(cfg.get("sources",[]))==len(SOURCES)
            and all(type(row) is dict and set(row)==SOURCE_ROW_KEYS
                    for row in cfg["sources"])
            and {row["id"] for row in cfg["sources"]}==set(SOURCES),
            "CADRE_P53O_INCOHERENT")
    for row in cfg["sources"]:
        expected_url, scope=SOURCES[row["id"]]
        require(row["url"]==expected_url and row["portee"]==scope
                and row["statut"]=="PAGE_INSTITUTIONNELLE_REPEREE"
                and row["pieces_transactionnelles_authentifiees"]==0,
                "SOURCE_EXTERNE_NON_VERIFIEE_OU_DERIVEE")
    require(set(cfg.get("verrous",{}))=={
        "sources_officielles_non_equivalentes_pieces_primaires",
        "pays_hypothetique_ne_recoit_pas_competence_automatique",
        "organisme_detenteur_et_droit_acces_a_etablir",
        "mamH_seulement_pour_organismes_municipaux",
        "aucun_comptage_double_economies",
        "aucune_demande_ou_capture_reelle",
        "aucune_exposition_documents_prives",
        "aucun_taux_fiscal_adopte",
        "maintien_travailleurs_et_services_essentiels",
        "aucune_fusion_automatique",
    } and all(v is True for v in cfg["verrous"].values()),
            "VERROU_PROTECTION_SUPPRIME")
    require(len(p53n.construire_registre(p53n_cfg))==12 and
            cfg["etat_initial"]["documents_primaires_authentifies"]==0 and
            cfg["etat_initial"]["economies_certifiees_cad"] is None and
            orgs==1344 and dossiers==26,
            "CHAINE_P53N_NON_RECONCILIEE")
    return previous,p53n_cfg,cfg,orgs,dossiers

def matrice(cfg):
    fiches=[]
    for regime in REGIMES:
        for cat in cfg["categories"]:
            ids=list(PER_CATEGORIE[cat])
            fiches.append({
                "regime":regime,
                "categorie":cat,
                "applicabilite_juridique":"A_ETABLIR",
                "sources_candidats":ids,
                "statut_sources":{s:"NON_CONSULTE_DANS_CE_DOSSIER" for s in ids},
                "phases":{p:"A_REALISER" for p in PHASES},
                "reference_municipale_utilisable":(
                    "UNIQUEMENT_SI_ORGANISME_MUNICIPAL_IDENTIFIE"
                    if "MAMH_FINANCES" in ids else "NON_PRESUMEE"),
                "sources_du_quebec_souverain":(
                    "COMPARATEUR_HISTORIQUE_SANS_AUTORITE_FUTURE"
                    if regime==REGIMES[1] else "REGIME_CANADIEN_ACTUEL_A_VERIFIER"),
                "preuves_p53n_attendues":len(p53n.TYPES),
                "pieces_primaires_authentifiees":0,
                "economies_certifiees_cad":None,
                "priorite_procedurale":PHASES[0],
                "decision":NO_GO,
            })
    require(len(fiches)==12 and len({(x["regime"],x["categorie"]) for x in fiches})==12,
            "MATRICE_INCOMPLETE")
    return fiches

def examiner(d,cfg):
    """Contrôle formel d'une orientation déclarative; ne visite aucune URL."""
    require(type(d) is dict and set(d)==DECL_KEYS
            and d.get("schema_version")=="P53O-DECLARATION-1",
            "DECLARATION_NON_CONFORME")
    r=d["regime"]
    c=d["categorie"]
    require(r in REGIMES and c in PER_CATEGORIE,"REGIME_CATEGORIE_INCONNU")
    sites=d["sources_consultees"]
    require(type(sites) is dict and set(sites)==set(PER_CATEGORIE[c])
            and all(type(s) is str and s in ETATS for s in sites.values()),
            "SOURCES_DECLAREES_INCOHERENTES")
    compt=d["statut_competence"]
    social=d["statut_donnees_services"]
    access=d["statut_droits_acces"]
    require(compt in ("INCONNU","IDENTIFIE_DECLARE_NON_VERIFIE"),
            "COMPETENCE_CERTIFIEE_INTERDITE")
    require(social in ("INCONNU","MESURES_DECLAREES_NON_VERIFIEES","GARANTIES_VIOLEES"),
            "SERVICES_CERTIFIES_INTERDITS")
    require(access in ("INCONNU","ACCES_POTENTIEL_DECLARATIF","ACCES_NON_AUTORISE"),
            "AUTORISATION_NON_VERIFIEE")
    if access=="ACCES_NON_AUTORISE":
        statut="ARRET_ACCES_NON_AUTORISE"
    elif social=="GARANTIES_VIOLEES":
        statut="ARRET_PROTECTION_SERVICES_EMPLOIS"
    elif compt=="INCONNU":
        statut="P0_ORGANISME_ET_COMPETENCE_INCONNUS"
    elif all(v=="NON_CONSULTE" for v in sites.values()):
        statut="P1_REPERAGE_PUBLIC_NON_EFFECTUE"
    elif access=="INCONNU":
        statut="P3_DROIT_ACCES_A_VERIFIER"
    elif social=="INCONNU":
        statut="P4_PROTECTIONS_A_VERIFIER"
    else:
        statut="DOCUMENTS_CANDIDATS_NON_AUTHENTIFIES"
    # No source identity, URL, download, amount or private data in public report.
    return {"cle":(r,c),"statut":statut,
            "documents_primaires_authentifies":0,"economies_certifiees_cad":None}

def bilan(cfg,orgs,dossiers,d):
    return {
        "schema_version":"P53O-RAPPORT-1",
        "organismes_mamh_2024_contexte":orgs,
        "dossiers_p53k_a_documenter":dossiers,
        "regimes_non_cumules":2,
        "categories":len(cfg["categories"]),
        "fiches_orientees":len(matrice(cfg)),
        "pages_officielles_repertoiriees":len(SOURCES),
        "publications_transactionnelles_originales_telechargees":0,
        "documents_primaires_authentifies":0,
        "demandes_acces_envoyees":0,
        "documents_p53n_toujours_a_documenter":12*len(p53n.TYPES),
        "declarations_controlees":len(d),
        "statuts_agreges":dict(sorted(Counter(row["statut"] for row in d).items())),
        "economies_annuelles_certifiees_cad":None,
        "revenus_fiscaux_adoptes_cad":None,
        "preuves_F01_F20_validees":0,"montants_Nova_inconnus":1320,
        "protection_des_emplois_et_services_exigee":True,
        "avis_independants_signes":0,"decision":NO_GO,
        "aucune_autorisation_de_fusion":True,
    }

def output(path,value):
    p=Path(path)
    require(not p.exists() and not p.is_symlink(),"SORTIE_EXISTANTE_NON_ECRASEE")
    with p.open("x",encoding="utf-8") as f:
        f.write(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n")

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bilan")
    ap.add_argument("--matrice")
    ap.add_argument("--declaration",action="append",default=[])
    ap.add_argument("--exiger-economies-certifiees",action="store_true")
    opts=ap.parse_args(argv)
    try:
        require(len(opts.declaration)<=12,"TROP_DE_DECLARATIONS")
        if opts.bilan and opts.matrice:
            require(Path(opts.bilan).resolve()!=Path(opts.matrice).resolve(),
                    "SORTIES_IDENTIQUES")
        for p in (opts.bilan,opts.matrice):
            if p:
                path=Path(p)
                require(not path.exists() and not path.is_symlink(),"SORTIE_DEJA_EXISTANTE")
        _,_,cfg,orgs,dossiers=sources()
        decl=[]
        dedupe=set()
        for p in opts.declaration:
            v=examiner(read_json(p),cfg)
            require(v["cle"] not in dedupe,"FICHE_DOUBLE")
            dedupe.add(v["cle"])
            decl.append(v)
        result=bilan(cfg,orgs,dossiers,decl)
        if opts.bilan:output(opts.bilan,result)
        if opts.matrice:output(opts.matrice,{
            "schema_version":"P53O-MATRICE-1","statut":"CANDIDATS_OFFICIELS_NON_PIECES",
            "fiches":matrice(cfg)})
        print(json.dumps(result,sort_keys=True,ensure_ascii=False))
        return 3 if opts.exiger_economies_certifiees else 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,
            json.JSONDecodeError) as e:
        print("P53O_REFUS: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
