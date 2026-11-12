#!/usr/bin/env python3
"""P53Q: inventaire ciblé de pièces probatoires sans réception ni certification."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import constituer_dossiers_institutionnels_nova_p53p as precedent

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"projets"/"projet-nova"/"etudes"/"P53Q_INVENTAIRE_PIECES_ET_CONTREPARTIES.json"
NO_GO="NO_GO_AUTOMATIQUE"

DOCUMENTS=(
    "competence_et_identite_juridique",
    "etats_financiers_2024_version_originelle",
    "perimetre_de_consolidation_2024",
    "grand_livre_payeur",
    "grand_livre_beneficiaire",
    "entente_resolution_et_avenants",
    "facture_ou_appel_de_quote_part",
    "preuve_de_paiement",
    "eliminations_deja_comptabilisees",
    "subventions_et_origine_financement",
    "cout_operationnel_reference",
    "cout_transition",
    "cout_recurrent_apres_changement",
    "transfert_de_couts_vers_autres_acteurs",
    "indicateurs_qualite_accessibilite_service",
    "protections_emplois_conditions_travail",
    "avis_independant_comptable_juridique",
)
FIRST={
    "66023":"perimetre_de_consolidation_2024",
    "T1025":"entente_resolution_et_avenants",
    "23027":"eliminations_deja_comptabilisees",
    "T0081":"indicateurs_qualite_accessibilite_service",
    "T0088":"eliminations_deja_comptabilisees",
    "39135":"etats_financiers_2024_version_originelle",
}
DOUBLE={"23027","T0088"}
PHASES=("P0_COMPETENCE","P1_SOURCES_OFFICIELLES","P2_DEUX_GRANDS_LIVRES",
        "P3_CONSOLIDATION_ANTERIEURE","P4_SERVICES_ET_EMPLOIS",
        "P5_CONTROLE_EXPERT_INDEPENDANT")
ETATS=("NON_OBTENUE","REPERE_PUBLIC_NON_AUTHENTIFIE",
       "DEMANDE_PREPAREE_NON_ENVOYEE","RECEPTION_DECLAREE_NON_VERIFIEE",
       "REFUS_DECLARE_NON_VERIFIE")
DECL_KEYS={"schema_version","code_organisme","type_piece","etat_declaratif",
           "acces_legal","garanties_emplois_services","perimetre_comptable"}

def exiger(ok, message):
    if not ok:
        raise ValueError(message)

def lire_json(path):
    p=Path(path)
    exiger(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=40000,
           "FICHIER_INDISPONIBLE")
    data=json.loads(p.read_text(encoding="utf-8"))
    exiger(type(data) is dict,"FORMAT_SOURCE_NON_OBJET")
    return data

def sources():
    p,rows,h,i=precedent.load()
    dossiers=precedent.build(p,rows,h,i)
    cfg=lire_json(CONFIG)
    attendu={
        "schema_version":"P53Q-1",
        "jalon":"P53Q",
        "date_reference":"2026-10-22",
        "statut":"INVENTAIRE_DOCUMENTAIRE_SANS_ACQUISITION",
        "exercice_reference":2024,
        "codes":list(precedent.CODES),
        "types_pieces":list(DOCUMENTS),
        "priorite_document_par_organisme":FIRST,
        "etats_declaratifs":list(ETATS),
        "phases":list(PHASES),
        "verrous":{
            "aucune_piece_originale_dans_git":True,
            "aucune_reception_authentifiee":True,
            "aucune_demande_reelle_envoyee":True,
            "aucune_economie_derivee_flux":True,
            "eliminations_existantes_non_reutilisees":True,
            "emplois_et_services_intacts":True,
            "montants_inconnus_non_zeros":True,
            "donnees_personnelles_exclues":True,
            "pas_de_consolidation_de_regimes":True,
            "aucune_fusion_autorisee":True,
            "expertise_humaine_exigee":True,
        },
        "etat_initial":{
            "dossiers":6,
            "types_pieces_par_dossier":17,
            "emplacements_pieces":102,
            "originaux_authentifies":0,
            "demandes_envoyees":0,
            "avis_independants_signes":0,
            "economies_certifiees_cad":None,
            "decision":NO_GO,
        },
    }
    exiger(cfg==attendu,"CONFIGURATION_P53Q_ALTEREE")
    exiger(len(rows)==1344 and len(dossiers)==6 and
           len(h["priorites_relecture"])==25 and
           set(FIRST)==set(precedent.CODES) and
           len(set(DOCUMENTS))==len(DOCUMENTS)==17 and
           p["etat_initial"]["economies_certifiees_cad"] is None,
           "CONTROLES_ANTERIEURS_INCOHERENTS")
    return cfg,dossiers

def registre(cfg,dossiers):
    elements=[]
    for dossier in dossiers:
        code=dossier["code_organisme"]
        first=FIRST[code]
        order=(first,)+tuple(t for t in DOCUMENTS if t!=first)
        exiger(len(order)==17 and len(set(order))==17,
               "ORDRE_PIECES_INCOHERENT")
        for pos,category in enumerate(order):
            elements.append({
                "code_organisme":code,
                "nom_organisme":dossier["nom_organisme"],
                "exercice":2024,
                "type_piece":category,
                "priorite_locale":pos+1,
                "est_premiere_piece_a_chercher":pos==0,
                "source_de_reperage_p53p":[s["id"] for s in dossier["sources_publiques_candidats"]],
                "statut_acquisition":"NON_OBTENUE",
                "detenteur_legal":"A_IDENTIFIER",
                "perimetre":"A_DEMONTRER",
                "numero_ecriture":"NON_RÉCOLTÉ",
                "avis_expert":"NON_OBTENU",
                "double_elimination_risque_connue":code in DOUBLE,
                "preuve_originale_authentifiee":False,
                "montant_economie_certifiee_cad":None,
            })
    exiger(len(elements)==102
           and len({(p["code_organisme"],p["type_piece"]) for p in elements})==102
           and sum(p["est_premiere_piece_a_chercher"] for p in elements)==6,
           "INVENTAIRE_102_NON_EXHAUSTIF")
    return elements

def evaluer_declaration(d):
    """La déclaration ne constitue jamais une pièce ni une vérification indépendante."""
    exiger(type(d) is dict and set(d)==DECL_KEYS and
           d.get("schema_version")=="P53Q-DECLARATION-1",
           "DECLARATION_NON_CONFORME")
    code=d["code_organisme"];typ=d["type_piece"]
    exiger(type(code) is str and code in precedent.CODES and
           type(typ) is str and typ in DOCUMENTS,
           "ORGANISME_OU_PIECE_INCONNU")
    exiger(type(d["etat_declaratif"]) is str and
           d["etat_declaratif"] in ETATS,"STATUT_AUTHENTIFIE_INTERDIT")
    exiger(d["acces_legal"] in ("INCONNU","POSSIBLE_NON_VALIDE","NON_AUTORISE"),
           "ACCES_DECLARE_CERTIFIE_INTERDIT")
    exiger(d["garanties_emplois_services"] in ("INCONNU","OUI_DECLARE_NON_VERIFIE","NON"),
           "GARANTIES_DECLAREES_CERTIFIEES_INTERDITES")
    exiger(d["perimetre_comptable"] in ("INCONNU","DECLARE_NON_VERIFIE","HORS_PERIMETRE_DECLARE"),
           "PERIMETRE_CERTIFIE_INTERDIT")
    if d["acces_legal"]=="NON_AUTORISE":
        statut="ARRET_ACCES_NON_AUTORISE"
    elif d["garanties_emplois_services"]=="NON":
        statut="ARRET_EMPLOIS_SERVICES"
    elif code in DOUBLE and d["perimetre_comptable"]=="INCONNU":
        statut="VERIFICATION_DOUBLE_ELIMINATION_PRIORITAIRE"
    elif d["perimetre_comptable"]=="INCONNU":
        statut="PERIMETRE_EN_ATTENTE"
    elif d["garanties_emplois_services"]=="INCONNU":
        statut="GARANTIES_SOCIALES_A_VERIFIER"
    elif d["etat_declaratif"]=="NON_OBTENUE":
        statut="PIECE_NON_OBTENUE"
    elif d["etat_declaratif"]=="DEMANDE_PREPAREE_NON_ENVOYEE":
        statut="DEMANDE_NON_TRANSMISE"
    elif d["etat_declaratif"]=="RECEPTION_DECLAREE_NON_VERIFIEE":
        statut="RECEPTION_NON_AUTHENTIFIEE"
    elif d["etat_declaratif"]=="REFUS_DECLARE_NON_VERIFIE":
        statut="REFUS_DECLARATIF_A_EXAMINER"
    else:
        statut="REPERAGE_NON_AUTHENTIFIE"
    return {
        "cle":(code,typ),
        "statut":statut,
        "original_authentifie":False,
        "economie_certifiee_cad":None,
    }

def bilan(cfg,dossiers,declarations):
    return {
        "schema_version":"P53Q-RAPPORT-1",
        "organismes_cibles":len(dossiers),
        "organismes_source_mamh_2024":1344,
        "dossiers_p53k_en_suspens":26,
        "pieces_distinctes_requises":len(DOCUMENTS),
        "emplacements_documentaires":len(dossiers)*len(DOCUMENTS),
        "dossiers_consolidation_deja_signalee":len(DOUBLE),
        "demandes_reellement_envoyees":0,
        "originaux_transactionnels_authentifies":0,
        "appariements_bilateraux_certifies":0,
        "revisions_independantes_signees":0,
        "economies_certifiees_cad":None,
        "declarations_locales_verifiees_formellement":len(declarations),
        "statuts_agreges":dict(sorted(Counter(x["statut"] for x in declarations).items())),
        "preuves_F01_F20_validees":0,
        "montants_Nova_inconnus":1320,
        "taux_fiscaux_adoptes":0,
        "services_essentiels_reduits_autorises":False,
        "emplois_supprimes_autorises":0,
        "fusion_autorisee":False,
        "decision":NO_GO,
    }

def output(path,value):
    p=Path(path)
    exiger(not p.exists() and not p.is_symlink(),
           "ECRASEMENT_INTERDIT")
    with p.open("x",encoding="utf-8") as out:
        out.write(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n")

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--bilan")
    a.add_argument("--inventaire")
    a.add_argument("--declaration",action="append",default=[])
    a.add_argument("--exiger-preuves-certifiees",action="store_true")
    opts=a.parse_args(argv)
    try:
        exiger(len(opts.declaration)<=102,"DECLARATIONS_EXCESSIVES")
        paths=[Path(p) for p in (opts.bilan,opts.inventaire) if p]
        exiger(len({p.resolve() for p in paths})==len(paths),
               "SORTIES_IDENTIQUES")
        exiger(all(not p.exists() and not p.is_symlink() for p in paths),
               "SORTIE_EXISTANTE")
        cfg,dossiers=sources()
        seen=set();evals=[]
        for file in opts.declaration:
            e=evaluer_declaration(lire_json(file))
            exiger(e["cle"] not in seen,"DECLARATION_DUPLIQUEE")
            seen.add(e["cle"])
            evals.append(e)
        result=bilan(cfg,dossiers,evals)
        if opts.bilan:output(opts.bilan,result)
        if opts.inventaire:
            output(opts.inventaire,{
                "schema_version":"P53Q-INVENTAIRE-1",
                "statut":"PIECES_NON_OBTENUES_NON_CERTIFIEES",
                "entrees":registre(cfg,dossiers)})
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if opts.exiger_preuves_certifiees else 0
    except (ValueError,OSError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("P53Q_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
