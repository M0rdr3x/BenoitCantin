#!/usr/bin/env python3
"""P53P — Dossiers documentaires ciblés sur des organismes réels de 2024.

Lecture seule : les pages officielles sont des références, pas des pièces authentifiées.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import auditer_appariements_municipaux_nova_p53j as p53j
import prioriser_sources_officielles_nova_p53o as p53o

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "projets" / "projet-nova" / "etudes"
CONFIG = D / "P53P_DOSSIERS_INSTITUTIONNELS_2024.json"
NO_GO = "NO_GO_AUTOMATIQUE"
CODES = ("66023", "T1025", "23027", "T0081", "T0088", "39135")
RANGS = (1, 2, 3, 4, 5, None)
SOURCES = {
    "MONTREAL_BILAN_2024": "https://montreal.ca/articles/bilan-financier-2024-de-montreal-91858",
    "ARTM_RAPPORT_2024": "https://www.artm.quebec/rapport-annuel-2024/",
    "QUEBEC_RF_2024": "https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf",
    "QUEBEC_RAPPORTS": "https://www.ville.quebec.qc.ca/apropos/profil-financier/rapport-financier.aspx",
    "STM_INDICATEURS": "https://www.stm.info/fr/a-propos/informations-entreprise-et-financieres/indicateurs-de-performance",
    "RTC_BILAN_ACHALANDAGE": "https://www.rtcquebec.ca/medias/communiques/achalandage-et-satisfaction-indicateurs-au-vert-pour-le-rtc",
    "SAINT_VALERE_DOCUMENTATION": "https://www.msvalere.qc.ca/documentation",
    "MAMH_PORTAIL": "https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier",
}
SOURCES_PAR_CODE = {
    "66023": ("MONTREAL_BILAN_2024", "MAMH_PORTAIL"),
    "T1025": ("ARTM_RAPPORT_2024", "MAMH_PORTAIL"),
    "23027": ("QUEBEC_RF_2024", "QUEBEC_RAPPORTS", "MAMH_PORTAIL"),
    "T0081": ("STM_INDICATEURS", "MAMH_PORTAIL"),
    "T0088": ("QUEBEC_RF_2024", "RTC_BILAN_ACHALANDAGE", "MAMH_PORTAIL"),
    "39135": ("SAINT_VALERE_DOCUMENTATION", "MAMH_PORTAIL"),
}
CONSTATS = {
    "66023": "PUBLICATION_2024_SANS_APPARIEMENT_TRANSACTIONNEL",
    "T1025": "PUBLICATION_2024_SANS_APPARIEMENT_TRANSACTIONNEL",
    "23027": "RTC_CONSOLIDE_ET_RECIPROQUES_DEJA_ELIMINEES",
    "T0081": "INDICATEURS_2024_SANS_APPARIEMENT_TRANSACTIONNEL",
    "T0088": "RTC_CONSOLIDE_ET_RECIPROQUES_DEJA_ELIMINEES",
    "39135": "AJOUT_SOURCE_MAMH_2024_SANS_APPARIEMENT",
}
ALL_CONSTATS = set(CONSTATS.values())
INPUT_KEYS = {"schema_version", "code_organisme", "etat_reperage", "perimetre_verifie",
              "transaction_2024_documentee", "elimination_anterieure_verifiee",
              "protection_emplois_services", "acces_aux_pieces"}
REPERAGE = {"NON_CONSULTE", "PAGE_OFFICIELLE_REPEREE_NON_ARCHIVEE",
            "DOCUMENT_PUBLIC_CANDIDAT_NON_AUTHENTIFIE"}
METAS = {"INCONNU", "DECLARE_NON_VERIFIE", "NON"}

def check(yes, why):
    if not yes:
        raise ValueError(why)

def read(path, maximum=50000):
    p = Path(path)
    check(p.is_file() and not p.is_symlink() and 0 < p.stat().st_size <= maximum,
          "SOURCE_INDISPONIBLE")
    obj = json.loads(p.read_text(encoding="utf-8"))
    check(type(obj) is dict, "OBJET_JSON_ATTENDU")
    return obj

def load():
    _, _, p53o_cfg, orgs, dossiers = p53o.sources()
    rows = p53j.lire_snapshot()
    p53h = p53j.lire_json(p53j.P53H)
    p53i = p53j.lire_json(p53j.P53I)
    p53j.verifier_et_construire(rows, p53i, p53h)
    cfg = read(CONFIG)
    expected_cases = [
        {"code":code, "rang_p53h":rank, "constat":CONSTATS[code],
         "sources":list(SOURCES_PAR_CODE[code])}
        for code, rank in zip(CODES, RANGS)
    ]
    check(cfg.get("schema_version") == "P53P-1"
          and cfg.get("statut") == "SOURCES_CIBLEES_SANS_PIECE_TRANSACTIONNELLE"
          and cfg.get("exercice") == 2024
          and cfg.get("cas") == expected_cases
          and cfg.get("sources_officielles") == SOURCES
          and cfg.get("priorites_preexistantes") == 5
          and cfg.get("ajout_hors_top25") == 1
          and cfg.get("constat_consolidation_source") == "QUEBEC_RF_2024"
          and cfg.get("constat_consolidation_pages_pdf") == [35, 197]
          and cfg.get("verrous") == {
              "aucune_economie_derivee_de_flux_recus":True,
              "consolidation_deja_realisee_non_nouveau_gain":True,
              "aucun_appariement_invente":True,
              "originaux_transactionnels_non_acquis":True,
              "zero_non_substitue_aux_blancs":True,
              "aucune_fusion_autorisee":True,
              "services_emplois_maintenus":True,
              "source_2024_non_budget_2026_2027":True,
              "cas_top5_pas_reclassement_top25":True,
              "aucune_hypothese_fiscale_adoptee":True,
          } and cfg.get("etat_initial") == {
              "sources_publiques_referencees":len(SOURCES),
              "cas_documentaires":len(CODES),
              "transactions_appariees":0,
              "avis_independants_signes":0,
              "economies_certifiees_cad":None,
              "decision":NO_GO,
          }, "CONFIGURATION_P53P_MODIFIEE")
    check(orgs == 1344 and dossiers == 26 and
          "QUEBEC_RF_2024" in cfg["sources_officielles"] and
          len(p53h["priorites_relecture"]) == 25 and
          p53o_cfg["etat_initial"]["economies_certifiees_cad"] is None,
          "CHAINE_ANTERIEURE_NON_VERIFIEE")
    return cfg, rows, p53h, p53i

def build(cfg, rows, p53h, p53i):
    by = {r["cod_geo"]:r for r in rows}
    result = []
    for case in cfg["cas"]:
        code = case["code"]
        rank = case["rang_p53h"]
        check(code in by and by[code]["nom_organisme"], "ORGANISME_ABSENT")
        row = by[code]
        if rank is not None:
            old=p53h["priorites_relecture"][rank - 1]
            check(old["code_organisme"]==code and old["nom_organisme"]==row["nom_organisme"]
                  and old["type_org"]==row["type_org"]
                  and old["quotes_parts_cad"]==(row["CRIIX00408"] or None)
                  and old["transferts_cad"]==(row["CRIIX00409"] or None),
                  "PRIORITE_HISTORIQUE_MODIFIEE")
        else:
            added=p53i["nouvelle_ligne_municipale"]
            check(code=="39135" and row["nom_organisme"]==added["nom"]
                  and row["CRIIX00408"]==added["quotes_parts_cad"]
                  and row["CRIIX00409"]==added["transferts_cad"],
                  "SAINT_VALERE_P53I_INCOHERENT")
        if code in ("23027","T0088"):
            check(case["constat"]=="RTC_CONSOLIDE_ET_RECIPROQUES_DEJA_ELIMINEES"
                  and "QUEBEC_RF_2024" in case["sources"],
                  "RISQUE_DOUBLE_ELIMINATION_NON_SIGNALE")
        result.append({
            "code_organisme":code,
            "nom_organisme":row["nom_organisme"],
            "type_org":row["type_org"],
            "rang_historique_p53h":rank,
            "hors_top25_revision_p53i":rank is None,
            "quotes_parts_recues_2024_cad":row["CRIIX00408"] or None,
            "transferts_recus_2024_cad":row["CRIIX00409"] or None,
            "montants_bruts_non_apparies":True,
            "constat_documentaire":case["constat"],
            "sources_publiques_candidats":[
                {"id":x, "url":SOURCES[x], "authentification_transactionnelle":False}
                for x in case["sources"]],
            "pieces_p53n":{x:"NON_OBTENUE" for x in p53o.p53n.TYPES},
            "perimetre_et_contreparties": "INCONNUS_A_VERIFIER",
            "controle_double_elimination":(
                "OBLIGATOIRE_DEJA_SIGNALEE_DANS_RF_QUEBEC_2024"
                if code in ("23027","T0088") else "OBLIGATOIRE_NON_INSTRUIT"),
            "garde_fous_emplois_et_services": "A_DEMONTRER",
            "appariement_transactionnel_certifie":False,
            "economie_budgetaire_certifiee_cad":None,
            "decision":NO_GO,
        })
    check(len(result)==6 and len({r["code_organisme"] for r in result})==6,
          "DOUBLONS_ORGANISMES")
    return result

def evaluer(d, cfg):
    """Seulement une déclaration locale de repérage — pas l'examen d'une pièce."""
    check(type(d) is dict and set(d)==INPUT_KEYS
          and d["schema_version"]=="P53P-DECLARATION-1",
          "DECLARATION_INVALIDE")
    code = d["code_organisme"]
    check(type(code) is str and code in CODES, "CODE_NON_RETENU")
    check(d["etat_reperage"] in REPERAGE, "REPERAGE_FALSIFIE")
    for key in ("perimetre_verifie","transaction_2024_documentee",
                "elimination_anterieure_verifiee","acces_aux_pieces"):
        check(d[key] in METAS, "VERIFICATION_NON_AUTHENTIFIEE_INTERDITE")
    check(d["protection_emplois_services"] in ("INCONNU","OUI_DECLARE_NON_VERIFIE","NON"),
          "PROTECTION_NON_CONFORME")
    if d["protection_emplois_services"]=="NON":
        statut="REFUS_EMPLOIS_SERVICES"
    elif d["acces_aux_pieces"]=="NON":
        statut="ACCES_AUX_PIECES_NON_AUTORISE"
    elif d["perimetre_verifie"]=="INCONNU":
        statut="PERIMETRE_NON_ETABLI"
    elif code in ("23027","T0088") and d["elimination_anterieure_verifiee"]=="INCONNU":
        statut="CONTROLE_CONSOLIDATION_DEJA_PUBLIEE_A_RECONCILIER"
    elif d["transaction_2024_documentee"]=="INCONNU":
        statut="CONTREPARTIES_TRANSACTIONNELLES_NON_ETABLIES"
    else:
        statut="DECLARATIONS_NON_AUTHENTIFIEES_A_REVISER"
    return {"code":code,"statut":statut,"montant_certifie_cad":None,
            "preuves_primaires_authentifiees":0}

def summary(cfg, cases, declarations):
    return {
        "schema_version":"P53P-RAPPORT-1",
        "exercice_historique":2024,
        "organismes_mamh_sous_controle":1344,
        "dossiers_p53k_en_attente":26,
        "dossiers_institutionnels_p53p":len(cases),
        "organismes_issues_top5_p53h":5,
        "organismes_hors_top25_p53i":1,
        "sources_publiques_distinctes":len(cfg["sources_officielles"]),
        "cas_consolidation_reciproque_deja_signalee":2,
        "pieces_transactionnelles_authentifiees":0,
        "appariements_bilateraux_certifies":0,
        "economies_certifiees_cad":None,
        "recettes_fiscales_adoptees_cad":None,
        "avis_independants_signes":0,
        "demandes_d_acces_envoyees":0,
        "declarations_locales_controlees":len(declarations),
        "statuts_agreges":dict(sorted(Counter(d["statut"] for d in declarations).items())),
        "preuves_fiscales_F01_F20_validees":0,
        "montants_Nova_inconnus":1320,
        "fusion_autorisee":False,
        "decision":NO_GO,
    }

def output(path, obj):
    p=Path(path)
    check(not p.exists() and not p.is_symlink(), "SORTIE_EXISTANTE_NON_ECRASEE")
    with p.open("x",encoding="utf-8") as stream:
        stream.write(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+"\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bilan")
    parser.add_argument("--dossiers")
    parser.add_argument("--declaration",action="append",default=[])
    parser.add_argument("--exiger-economies-certifiees",action="store_true")
    args=parser.parse_args(argv)
    try:
        check(len(args.declaration)<=6,"TROP_DE_DECLARATIONS")
        targets=[x for x in (args.bilan,args.dossiers) if x]
        check(len({str(Path(x).resolve()) for x in targets})==len(targets),
              "DESTINATIONS_IDENTIQUES")
        for t in targets:
            check(not Path(t).exists() and not Path(t).is_symlink(),
                  "SORTIE_EXISTANTE_NON_ECRASEE")
        cfg, rows, h, i=load()
        cases=build(cfg,rows,h,i)
        seen=set()
        reviewed=[]
        for f in args.declaration:
            declaration=evaluer(read(f),cfg)
            check(declaration["code"] not in seen,"DECLARATION_DOUBLE")
            seen.add(declaration["code"])
            reviewed.append(declaration)
        result=summary(cfg,cases,reviewed)
        if args.bilan:
            output(args.bilan,result)
        if args.dossiers:
            output(args.dossiers,{"schema_version":"P53P-DOSSIERS-1",
                                  "statut":"SOURCES_REPEREES_NON_AUTENTIFIEES",
                                  "dossiers":cases})
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if args.exiger_economies_certifiees else 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError,IndexError) as exc:
        print("P53P_REFUS: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
