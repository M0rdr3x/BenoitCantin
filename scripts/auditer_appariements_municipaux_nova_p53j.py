#!/usr/bin/env python3
"""P53J — Triage des écritures municipales 2024; aucune consolidation automatique."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ETUDES = ROOT / "projets" / "projet-nova" / "etudes"
CSV_SOURCE = ETUDES / "sources" / "P53I_MAMH_2024_1344_RECETTES_CHARGES_SELECTION.csv"
P53I = ETUDES / "P53I_SOURCES_REVISION_ET_CHARGES_2024.json"
P53H = ETUDES / "P53H_PRIORITES_VERIFICATION_2024.json"
ATTENDU_SHA = "cef644e3f16ebea6bc727b009037638fa70443fe66fbeb55e4ac1e3cb1071213"
CHAMPS = (
    "cod_geo", "nom_organisme", "type_org", "CRIIX00405", "CRIIX00406",
    "CRIIX00408", "CRIIX00409", "CRIIX00681", "CRIIX00682",
    "CRIIX00683", "CRIIX00685", "CRIIX00686",
)
COLONNES_JOURNAL = [
    "exercice", "code_organisme_declarant", "nom_organisme_declarant",
    "type_organisme", "rang_priorite_p53h", "ajout_revision_p53i",
    "quotes_parts_recues_cad", "transferts_recus_cad",
    "charges_quotes_parts_versees_cad", "charges_transferts_municipaux_cad",
    "code_payeur_documente", "code_beneficiaire_transaction_documente",
    "identifiant_ecriture_payeur", "identifiant_ecriture_beneficiaire",
    "reference_piece_originale", "controle_perimetre_consolidation",
    "validation_expert_independant", "statut_appariement",
    "montant_eliminable_certifie_cad",
]

def exiger(ok, raison):
    if not ok:
        raise ValueError(raison)

def entier_ou_absent(champ):
    if champ == "":
        return None
    exiger(champ.lstrip("-").isdigit(), "MONTANT_NON_ENTIER")
    return int(champ)

def somme_signee(rows, code):
    # Un blanc n'est pas une valeur zéro. Seules les observations sont sommées.
    vals = [entier_ou_absent(r[code]) for r in rows]
    return sum(v for v in vals if v is not None), sum(v is None for v in vals)

def lire_json(path):
    p = Path(path)
    exiger(p.is_file() and not p.is_symlink(), "JSON_MANQUANT")
    return json.loads(p.read_text(encoding="utf-8"))

def lire_snapshot(path=CSV_SOURCE):
    p = Path(path)
    exiger(p.is_file() and not p.is_symlink(), "SOURCE_DERIVEE_MANQUANTE")
    raw = p.read_bytes()
    exiger(hashlib.sha256(raw).hexdigest() == ATTENDU_SHA,
           "VERSION_SOURCE_DERIVEE_NON_IDENTIQUE_A_P53I")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
    exiger(len(rows) == 1344, "PERIMETRE_1344_NON_ATTESTE")
    exiger(all(r.get(None) is None and all(k in r for k in CHAMPS) for r in rows),
           "CHAMPS_NON_CONFORMES")
    exiger(len({r["cod_geo"] for r in rows}) == 1344,
           "CODES_ORGANISMES_DUPLIQUES")
    return rows

def verifier_et_construire(rows, p53i, p53h):
    exiger(len(rows) == 1344, "PERIMETRE_MODIFIE")
    by_code = {r["cod_geo"]: r for r in rows}
    exiger(len(by_code) == 1344, "DOUBLON_CODE")
    exiger(set(r["type_org"] for r in rows) == {
        "Municipalité locale", "Municipalité régionale de comté",
        "Régie intermunicipale", "Communauté métropolitaine",
        "Organisme public de transport"}, "CATEGORIES_INATTENDUES")
    exiger(p53i["archives_derivées"]["nouvelle_selection_sha256"] == ATTENDU_SHA,
           "METADONNEES_SOURCE_DIVERGENTES")
    exiger(p53i["variation_et_population"]["nouveaux_codes"] == ["39135"] and
           by_code["39135"]["nom_organisme"] == "Saint-Valère",
           "REVISION_SAINT_VALERE_DIVERGENTE")
    exiger(p53i["etat"]["decision"] == "NO_GO_AUTOMATIQUE" and
           p53i["etat"]["preuves_F01_F20_validees"] == 0 and
           p53i["etat"]["montants_Nova_inconnus"] == 1320 and
           p53i["etat"]["appariements_transactionnels_confirmes"] == 0,
           "GARDE_FOUS_P53I_MODIFIES")
    objectifs = {
        "CRIIX00405": 41666627807,
        "CRIIX00406": 17339561033,
        "CRIIX00408": 3148209097,
        "CRIIX00409": 7716577059,
        "CRIIX00681": 2526339827,
    }
    blancs = {}
    for code, attendu in objectifs.items():
        total, absence = somme_signee(rows, code)
        exiger(total == attendu, "TOTAL_SOURCE_INCOHERENT_" + code)
        blancs[code] = absence
    priorites = p53h["priorites_relecture"]
    exiger(len(priorites) == 25, "PRIORITES_HISTORIQUES_INCOMPLETES")
    rangs = {}
    for i, priorite in enumerate(priorites, 1):
        code = priorite["code_organisme"]
        exiger(priorite["rang"] == i and code in by_code and code not in rangs,
               "RANG_PRIORITE_INVALIDE")
        ligne = by_code[code]
        exiger(ligne["nom_organisme"] == priorite["nom_organisme"] and
               ligne["type_org"] == priorite["type_org"], "ORGANISME_PRIORITE_MODIFIE")
        for poste, cle in (("CRIIX00408", "quotes_parts_cad"),
                           ("CRIIX00409", "transferts_cad")):
            exiger(entier_ou_absent(ligne[poste]) ==
                   (None if priorite[cle] is None else int(priorite[cle])),
                   "POSTE_PRIORITE_MODIFIE_" + code)
        recu = sum(x for x in (entier_ou_absent(ligne["CRIIX00408"]),
                               entier_ou_absent(ligne["CRIIX00409"])) if x is not None)
        exiger(recu == int(priorite["flux_candidats_signes_cad"]),
               "EXPOSITION_PRIORITE_INCOHERENTE")
        rangs[code] = i
    exiger("39135" not in rangs, "NOUVEL_ORGANISME_DEJA_PRIORISE")
    # Le journal est un journal de TRIAGE PAR DECLARANT, pas un grand livre
    # d'operations entre payeur et beneficiaire.
    journal = []
    for row in sorted(rows, key=lambda x: (x["cod_geo"] not in rangs,
                                             rangs.get(x["cod_geo"], 9999),
                                             x["cod_geo"])):
        item = {key: "" for key in COLONNES_JOURNAL}
        item.update({
            "exercice": "2024",
            "code_organisme_declarant": row["cod_geo"],
            "nom_organisme_declarant": row["nom_organisme"],
            "type_organisme": row["type_org"],
            "rang_priorite_p53h": str(rangs[row["cod_geo"]]) if row["cod_geo"] in rangs else "",
            "ajout_revision_p53i": "oui" if row["cod_geo"] == "39135" else "non",
            "quotes_parts_recues_cad": row["CRIIX00408"],
            "transferts_recus_cad": row["CRIIX00409"],
            "charges_quotes_parts_versees_cad": row["CRIIX00681"],
            "charges_transferts_municipaux_cad": row["CRIIX00682"],
            "statut_appariement": "AUCUNE_CONTREPARTIE_TRANSACTIONNELLE_DOCUMENTEE",
        })
        journal.append(item)
    bilan = {
        "schema_version": "P53J-1",
        "exercice": 2024,
        "base_source": "P53I_DERIVEE_2024_NON_ORIGINAL_INTEGRAL",
        "source_sha256": ATTENDU_SHA,
        "organismes_parcourus": len(journal),
        "priorites_p53h_controlees": len(rangs),
        "nouvel_organisme_verifie": "39135",
        "totaux_bruts_signes_cad": {k: str(v) for k, v in objectifs.items()},
        "champs_absents_par_code": blancs,
        "appariements_sur_pieces_primaires": 0,
        "references_transactions_bilaterales": 0,
        "eliminations_comptables_certifiees_cad": None,
        "economies_reelles_demontrees_cad": None,
        "revenu_taxe_Nova_adopte_cad": None,
        "preuves_F01_F20_validees": 0,
        "parametres_Nova_inconnus": 1320,
        "avis_independant_signe": False,
        "decision": "NO_GO_AUTOMATIQUE",
    }
    exiger(len(journal) == 1344 and len({x["code_organisme_declarant"]
                                        for x in journal}) == 1344, "JOURNAL_INCOMPLET")
    return bilan, journal

def ecrire_exclusif(path, content):
    p = Path(path)
    exiger(not p.exists() and not p.is_symlink(), "SORTIE_EXISTANTE_NON_ECRASEE")
    with p.open("x", encoding="utf-8", newline="") as f:
        f.write(content)

def main(argv=None):
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--rapport")
    args.add_argument("--export-csv")
    args.add_argument("--exiger-appariements", action="store_true")
    opt = args.parse_args(argv)
    try:
        bilan, journal = verifier_et_construire(
            lire_snapshot(), lire_json(P53I), lire_json(P53H))
        if opt.rapport:
            ecrire_exclusif(opt.rapport, json.dumps(
                bilan, ensure_ascii=False, indent=2) + "\n")
        if opt.export_csv:
            sortie = io.StringIO(newline="")
            writer = csv.DictWriter(sortie, fieldnames=COLONNES_JOURNAL,
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(journal)
            ecrire_exclusif(opt.export_csv, sortie.getvalue())
        print(json.dumps(bilan, ensure_ascii=False, sort_keys=True))
        return 3 if opt.exiger_appariements else 0
    except (ValueError, OSError, KeyError, TypeError, csv.Error,
            json.JSONDecodeError, UnicodeError) as exc:
        print("P53J_REFUS: " + str(exc), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
