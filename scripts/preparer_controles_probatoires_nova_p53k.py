#!/usr/bin/env python3
"""P53K: file d'acquisition et contrôle mécanique de déclarations bilatérales, jamais certification."""
import argparse
from collections import Counter
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import io
import json
from pathlib import Path
import re
import sys

import auditer_appariements_municipaux_nova_p53j as precedent

ROOT = Path(__file__).resolve().parents[1]
ETUDES = ROOT / "projets" / "projet-nova" / "etudes"
REGLES = ETUDES / "P53K_EXIGENCES_PROBATOIRES.json"
VALID_SHA = re.compile(r"[a-f0-9]{64}\Z")
VALID_AMT = re.compile(r"(0|[1-9][0-9]*)(\.[0-9]{1,2})?\Z")
VALID_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,100}\Z")
COLONNES = [
    "exercice", "rang_p53h", "code_organisme", "nom_organisme",
    "origine_priorisation", "quotes_parts_recues_cad", "transferts_recus_cad",
    "preuve_payeur_obtenue", "preuve_beneficiaire_obtenue",
    "preuve_paiement_obtenue", "perimetre_consolide_documente",
    "ecriture_deja_eliminee_verifiee", "avis_independant_signe",
    "appariement_certifie", "economie_budgetaire_demontree_cad", "statut",
]
POSTES = {
    "QUOTE_PART_MUNICIPALE": ("CRIIX00681", "CRIIX00408"),
    "TRANSFERT_MUNICIPAL": ("CRIIX00682", "CRIIX00409"),
}
DOCUMENTS = (
    "grand_livre_payeur_sha256",
    "grand_livre_beneficiaire_sha256",
    "entente_ou_resolution_sha256",
    "facture_ou_appel_sha256",
    "paiement_sha256",
    "perimetre_comptable_sha256",
    "controle_elimination_anterieure_sha256",
)

def exiger(condition, message):
    if not condition:
        raise ValueError(message)

def lire_json(path, maximum=40000):
    p = Path(path)
    exiger(p.is_file() and not p.is_symlink() and 0 < p.stat().st_size <= maximum,
           "DOSSIER_MANQUANT_OU_HORS_LIMITE")
    return json.loads(p.read_text(encoding="utf-8"))

def sources():
    rows = precedent.lire_snapshot()
    p53i = precedent.lire_json(precedent.P53I)
    p53h = precedent.lire_json(precedent.P53H)
    p53j_bilan, _ = precedent.verifier_et_construire(rows, p53i, p53h)
    regles = lire_json(REGLES)
    exiger(regles["schema_version"] == "P53K-1" and
           regles["exercice"] == 2024 and
           regles["source_sha256"] == precedent.ATTENDU_SHA and
           regles["priorites_historiques"] == 25 and
           regles["dossiers_revision_complementaire"] == ["39135"] and
           regles["documents_requis"] == list(DOCUMENTS) and
           regles["modes_admis"] == list(POSTES), "REGLES_INCOHERENTES")
    exiger(all(regles["verrous"][k] is True for k in (
        "metadonnees_non_authentification",
        "rapprochement_arithmetique_non_certification",
        "elimination_comptable_non_economie",
        "aucun_document_primaire_dans_git",
        "aucun_taux_fiscal_deduit",
        "aucune_revue_independante_presumee",
        "journal_public_ne_contient_pas_de_references_de_pieces",
        "fonds_et_services_essentiels_intacts",
    )), "VERROU_INACTIF")
    exiger(p53j_bilan["decision"] == "NO_GO_AUTOMATIQUE" and
           p53j_bilan["appariements_sur_pieces_primaires"] == 0 and
           p53j_bilan["parametres_Nova_inconnus"] == 1320,
           "ETAT_P53J_NON_CONFIRME")
    return rows, p53h, regles

def file_dossiers(rows, p53h):
    index = {x["cod_geo"]: x for x in rows}
    priorites = p53h["priorites_relecture"]
    exiger(len(priorites) == 25 and len(index) == 1344,
           "POPULATION_OU_PRIORITES_INCOHERENTES")
    selection = [(x["code_organisme"], str(x["rang"]), "PRIORITE_HISTORIQUE_P53H")
                 for x in priorites] + [("39135", "", "AJOUT_REVISION_P53I")]
    exiger(len({x[0] for x in selection}) == 26, "SELECTION_EN_DOUBLE")
    dossiers = []
    for code, rang, nature in selection:
        exiger(code in index, "ORGANISME_INCONNU")
        row = index[code]
        dossiers.append({
            "exercice": "2024",
            "rang_p53h": rang,
            "code_organisme": code,
            "nom_organisme": row["nom_organisme"],
            "origine_priorisation": nature,
            "quotes_parts_recues_cad": row["CRIIX00408"],
            "transferts_recus_cad": row["CRIIX00409"],
            "preuve_payeur_obtenue": "non",
            "preuve_beneficiaire_obtenue": "non",
            "preuve_paiement_obtenue": "non",
            "perimetre_consolide_documente": "non",
            "ecriture_deja_eliminee_verifiee": "non",
            "avis_independant_signe": "non",
            "appariement_certifie": "non",
            "economie_budgetaire_demontree_cad": "",
            "statut": "PIECES_PRIMAIRES_A_OBTENIR",
        })
    exiger(len(dossiers) == 26 and list(dossiers[0]) == COLONNES,
           "STRUCTURE_REGISTRE_INATTENDUE")
    return dossiers

def argent(value):
    exiger(type(value) is str and bool(VALID_AMT.fullmatch(value)),
           "MONTANT_POSITIF_CAD_ATTENDU")
    try:
        montant = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("MONTANT_INVALIDE") from exc
    exiger(montant > 0, "MONTANT_NUL_INTERDIT_POUR_APPARIEMENT")
    return montant

def jour(value):
    exiger(type(value) is str and bool(re.fullmatch(r"2024-\d{2}-\d{2}", value)),
           "DATE_HORS_EXERCICE_2024")
    try:
        d = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("DATE_CALENDAIRE_INVALIDE") from exc
    exiger(d.year == 2024, "EXERCICE_INCOHERENT")
    return d

def reference(value):
    exiger(type(value) is str and bool(VALID_REF.fullmatch(value)),
           "REFERENCE_ECRITURE_NON_VALIDE")
    return value

def evaluer_declaration(dossier, codes_connus):
    """Controle de forme exclusivement, documents et attestations NON authentifies."""
    exiger(type(dossier) is dict and dossier.get("schema_version") == "P53K-DOSSIER-1",
           "SCHEMA_DOSSIER_NON_CONFORME")
    exiger(dossier.get("exercice") == 2024 and dossier.get("devise") == "CAD",
           "EXERCICE_OU_DEVISE_INCOMPATIBLE")
    nature = dossier.get("nature")
    exiger(nature in POSTES, "NATURE_TRANSACTION_INCONNUE")
    montant = argent(dossier.get("montant_cad"))
    payer = dossier.get("payeur")
    receveur = dossier.get("beneficiaire")
    exiger(type(payer) is dict and type(receveur) is dict,
           "DEUX_ECRITURES_NECESSAIRES")
    codes = (payer.get("code_organisme"), receveur.get("code_organisme"))
    exiger(all(type(c) is str and c in codes_connus for c in codes) and codes[0] != codes[1],
           "IDENTITES_BILATERALES_NON_VERIFIEES")
    ids = []
    for sens, acteur, poste in (("PAYEUR", payer, POSTES[nature][0]),
                                ("BENEFICIAIRE", receveur, POSTES[nature][1])):
        exiger(acteur.get("poste_comptable") == poste,
               "POSTE_INCOMPATIBLE_" + sens)
        exiger(argent(acteur.get("montant_cad")) == montant,
               "MONTANTS_BILATERAUX_NON_EGAUX")
        jour(acteur.get("date_ecriture"))
        ids.append(reference(acteur.get("identifiant_ecriture")))
    exiger(ids[0] != ids[1], "IDENTIFIANTS_ECRITURES_CONFONDUS")
    preuves = dossier.get("empreintes_pieces")
    exiger(type(preuves) is dict, "PREUVES_PRIMAIRES_NON_DECLAREES")
    if any(preuves.get(nom) in (None, "") for nom in DOCUMENTS):
        return "PIECES_NON_COMPLETES", tuple((codes[i], ids[i]) for i in range(2))
    for key in DOCUMENTS:
        exiger(type(preuves[key]) is str and
               bool(VALID_SHA.fullmatch(preuves[key])),
               "EMPREINTE_PIECE_INVALIDE")
    exiger(preuves[DOCUMENTS[0]] != preuves[DOCUMENTS[1]],
           "PIECES_DES_DEUX_GRANDS_LIVRES_CONFONDUES")
    controle = dossier.get("consolidation")
    exiger(type(controle) is dict, "CONTROLE_PERIMETRE_MANQUANT")
    meme = controle.get("meme_perimetre")
    deja = controle.get("deja_elimine")
    exiger(meme in ("OUI", "NON", "INCONNU") and
           deja in ("OUI", "NON", "INCONNU"), "DECISION_PERIMETRE_INVALIDE")
    if deja == "OUI":
        etat = "ELIMINATION_DEJA_SIGNALEE_A_CONTROLER"
    elif meme == "NON":
        etat = "HORS_PERIMETRE_DE_CETTE_ELIMINATION"
    elif meme == "INCONNU" or deja == "INCONNU":
        etat = "PERIMETRE_OU_ELIMINATION_A_VERIFIER"
    else:
        etat = "CANDIDAT_ARITHMETIQUE_NON_CERTIFIE"
    return etat, tuple((codes[i], ids[i]) for i in range(2))

def bilan(dossiers, jugements, p53j_comptes):
    counts = Counter(jugements)
    return {
        "schema_version": "P53K-RAPPORT-1",
        "exercice": 2024,
        "organismes_source": p53j_comptes,
        "dossiers_a_documenter": len(dossiers),
        "priorites_historiques_p53h": 25,
        "dossiers_revision_p53i": 1,
        "pieces_primaires_recues_et_authentifiees": 0,
        "declarations_de_preuves_revisees": len(jugements),
        "statuts_declaratifs": dict(sorted(counts.items())),
        "appariements_certifies": 0,
        "eliminations_certifiees_cad": None,
        "economies_budgetaires_demontrees_cad": None,
        "taux_fiscaux_nova_adoptes": 0,
        "F01_F20_validees": 0,
        "parametres_Nova_inconnus": 1320,
        "avis_expert_independant_obtenu": False,
        "decision": "NO_GO_AUTOMATIQUE",
        "sortie_ne_certifie_aucune_donnee_source_ou_declaration": True,
    }

def ecrire(path, contenu):
    p = Path(path)
    exiger(not p.exists() and not p.is_symlink(), "SORTIE_EXISTANTE_NON_ECRASEE")
    with p.open("x", encoding="utf-8", newline="") as handle:
        handle.write(contenu)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rapport")
    parser.add_argument("--export-registre")
    parser.add_argument("--dossier", action="append", default=[])
    parser.add_argument("--exiger-certification", action="store_true")
    args = parser.parse_args(argv)
    try:
        exiger(len(args.dossier) <= 25, "TROP_DE_DECLARATIONS")
        rows, p53h, _ = sources()
        queue = file_dossiers(rows, p53h)
        codes = {x["cod_geo"] for x in rows}
        jugements = []
        ids_vus = set()
        for p in args.dossier:
            jugement, ids = evaluer_declaration(lire_json(p), codes)
            exiger(not (set(ids) & ids_vus), "ECRITURE_REUTILISEE_ENTRE_DOSSIERS")
            ids_vus.update(ids)
            jugements.append(jugement)
        resultat = bilan(queue, jugements, len(rows))
        if args.rapport:
            ecrire(args.rapport, json.dumps(resultat, ensure_ascii=False,
                                            sort_keys=True, indent=2) + "\n")
        if args.export_registre:
            dest = io.StringIO(newline="")
            writer = csv.DictWriter(dest, fieldnames=COLONNES, lineterminator="\n")
            writer.writeheader()
            writer.writerows(queue)
            ecrire(args.export_registre, dest.getvalue())
        print(json.dumps(resultat, ensure_ascii=False, sort_keys=True))
        return 3 if args.exiger_certification else 0
    except (ValueError, TypeError, OSError, UnicodeError, KeyError,
            json.JSONDecodeError, csv.Error) as err:
        print("P53K_REFUS: " + str(err), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
