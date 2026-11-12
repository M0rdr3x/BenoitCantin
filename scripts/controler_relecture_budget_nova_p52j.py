#!/usr/bin/env python3
"""Projet Nova P52J: recoupement d'une relecture primaire statique, pas attestation."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "projets" / "projet-nova" / "etudes"
FILES = {
    "lecture": STUDY / "P52J_RELECTURE_PRIMAIRE_BUDGET_2026_2027.json",
    "budget": STUDY / "P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json",
    "preuves": STUDY / "P52A_REGISTRE_PREUVES_FISCALES.json",
    "pistes": STUDY / "P52I_SOURCES_ET_ATTESTATIONS.json",
}
SOURCE = {
    "DISC2026_T3": (
        "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_Discours.pdf",
        "Tableau 3", "27", 29),
    "PLAN2026_F2": (
        "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf",
        "Tableau F.2", "F.9", 277),
}
SIGNED_NEGATIVE = {
    "depenses_portefeuilles", "service_dette", "depenses_totales",
    "provision_eventualites", "versements_fonds_generations",
}
SIGNED_NEGATIVE_ALREADY = {"deficit_comptable", "solde_budgetaire_loi_equilibre"}
F2_FIELDS = (
    "revenus_autonomes", "transferts_federaux", "revenus_totaux",
    "depenses_portefeuilles", "service_dette", "depenses_totales",
    "provision_eventualites", "deficit_comptable",
    "versements_fonds_generations", "solde_budgetaire_loi_equilibre",
)
SUBTOTAL_FIELDS = (
    "impots_sur_revenu_et_biens", "taxes_consommation",
    "entreprises_gouvernement", "droits_permis_redevances",
    "revenus_divers", "transferts_federaux", "revenus_autonomes",
    "revenus_totaux",
)
FALSE_FLAGS = (
    "validation_par_expert_independant", "preuve_F09_independamment_attestee",
    "verification_hash_pdf_original", "verification_mise_a_jour_ulterieure",
    "preuve_provenance_document_archives", "statut_non_appauvrissement_demonstre",
    "recettes_anti_evasion_certifiees", "taux_impot_proposes_ou_adoptes",
    "consolidation_tous_niveaux_gouvernementaux", "reforme_souveraine_financee",
    "publication_autorisee", "fusion_autorisee", "adoption_autorisee",
)

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def charge(path):
    p = Path(path)
    require(p.is_file() and p.stat().st_size < 300_000, "SOURCE_ABSENTE_OU_TROP_GRANDE")
    d = json.loads(p.read_text(encoding="utf-8"))
    require(type(d) is dict, "SOURCE_JSON_INVALIDE")
    return d

def entier_signé(s):
    require(type(s) is str and s and len(s) <= 15 and
            s.lstrip("-").isdigit() and s not in ("-0",) and
            (s == "0" or (not s.startswith("0") and not s.startswith("-0"))),
            "MONTANT_MCAD_MAL_FORME")
    return int(s)

def comparer(inputs):
    require(type(inputs) is dict and set(inputs) == set(FILES),
            "QUATRE_SOURCES_REQUISES")
    x, b, a, i = (inputs[k] for k in FILES)
    require(x.get("schema_version") == "P52J-1" and x.get("jalon") == "P52J" and
            x.get("date_lecture") == "2026-10-19" and
            x.get("statut") == "RELECTURE_PRIMAIRE_ASSISTEE_NON_CERTIFIEE" and
            x.get("unite") == "M_CAD" and x.get("periode") == "2026-2027",
            "LECTURE_PRIMAIRE_INVALIDE")
    require(b.get("schema_version") == "P52C-1" and b.get("unite") == "M_CAD" and
            b.get("periode") == "2026-2027" and
            b.get("decision") == "NO_GO_AUTOMATIQUE" and
            b.get("publication_autorisee") is False and
            b.get("fusion_autorisee") is False,
            "REFERENCE_P52C_INVALIDE")
    require(a.get("status") == "PROPOSITION_NON_ADOPTEE" and
            a.get("automatic_go") is False and
            a.get("financial_model_certified") is False and
            a.get("rates_selected") is False, "GARDES_P52A_ABANDONNEES")
    proofs = a.get("required_evidence")
    require(type(proofs) is list and len(proofs) == 20 and
            [e.get("id") for e in proofs] == [f"F{n:02d}" for n in range(1, 21)] and
            all(e.get("statut") == "NON_VALIDE" and
                e.get("preuve_independante_obtenue") is False and
                e.get("decision_autorisee") is False for e in proofs),
            "PREUVES_P52A_FICTIVES")
    require(i.get("schema_version") == "P52I-1" and
            i.get("source_revue_independante") is False and
            i.get("donnees_extraites_certifiees") is False and
            i.get("publication_autorisee") is False and
            i.get("fusion_autorisee") is False and
            [e.get("id") for e in i.get("plan_preuves", [])] ==
            [e.get("id") for e in proofs] and
            all(e.get("statut") == "NON_ATTESTEE" for e in i["plan_preuves"]),
            "PLAN_P52I_INVALIDE")
    statuses = x.get("validation_de_nature")
    require(type(statuses) is dict and
            statuses.get("transcription_visuelle_assistee") is True and
            statuses.get("prevision_non_resultat_realise") is True and
            statuses.get("decision") == "NO_GO_AUTOMATIQUE" and
            all(statuses.get(k) is False for k in FALSE_FLAGS),
            "CERTIFICATION_OU_DECISION_INVENTEE")
    require(statuses.get("reference_p52c") == "projets/projet-nova/etudes/P52C_REFERENTIEL_BUDGET_QUEBEC_2026_2027.json" and
            statuses.get("reference_p52a") == "projets/projet-nova/etudes/P52A_REGISTRE_PREUVES_FISCALES.json" and
            statuses.get("reference_p52i") == "projets/projet-nova/etudes/P52I_SOURCES_ET_ATTESTATIONS.json",
            "TRACABILITE_ABSENTE")
    s = x.get("source_primaires")
    require(type(s) is list and len(s) == 2 and
            [p.get("id") for p in b.get("sources", [])] ==
            list(SOURCE), "SOURCES_P52C_INATTENDUES")
    for source, reference in zip(s, b["sources"]):
        ident = source.get("id") or source.get("source_id")
        require(ident in SOURCE and ident == reference.get("id"),
                "ORDRE_SOURCES_INCORRECT")
        url, tableau, page, index = SOURCE[ident]
        require(source.get("url") == url and reference.get("url") == url and
                source.get("tableau") == tableau and
                source.get("page_imprimee") == page and
                source.get("page_pdf_index_zero") == index and
                source.get("nature") == "PREVISION_BUDGET_MARS_2026" and
                source.get("empreinte_sha256_pdf") is None and
                source.get("archivage_original_pdf_atteste") is False and
                source.get("relecture_humaine_independante") is False,
                "PREUVE_SOURCE_PRIMAIRE_FALSIFIEE")
    trans = x.get("transcription_discours_tableau3")
    require(type(trans) is dict and "TVQ" in trans.get("note_taxes_de_vente", ""),
            "DISTINCTION_TVQ_ABSENTE")
    rows, ref_rows = trans.get("lignes_revenus"), b.get("lignes_revenus")
    require(type(rows) is list and type(ref_rows) is list and
            len(rows) == len(ref_rows) == 21, "21_LIGNES_REVENUS_REQUISES")
    for l, r in zip(rows, ref_rows):
        require(type(l) is dict and set(l) == {"id", "valeur_mcad"} and
                l.get("id") == r.get("id") and
                r.get("source_id") == "DISC2026_T3" and
                entier_signé(l.get("valeur_mcad")) >= 0 and
                l["valeur_mcad"] == r.get("valeur_mcad"),
                "TRANSCRIPTION_LIGNE_ERRONNEE")
    subs = trans.get("sous_totaux_officiels_mcad")
    refsubs = b.get("sous_totaux_officiels_mcad")
    require(type(subs) is dict and type(refsubs) is dict and
            tuple(subs) == SUBTOTAL_FIELDS and tuple(refsubs) == SUBTOTAL_FIELDS,
            "HUIT_AGREGATS_REQUIS")
    for k in SUBTOTAL_FIELDS:
        require(entier_signé(subs[k]) >= 0 and subs[k] == refsubs[k],
                "SOUS_TOTAL_DIVERGENT_" + k)
    rev = {r["id"]: entier_signé(r["valeur_mcad"]) for r in rows}
    sums = {
        "impots_sur_revenu_et_biens": sum(rev[k] for k in
            ("impot_particuliers", "cotisations_sante", "impot_societes", "foncier_scolaire")),
        "taxes_consommation": sum(rev[k] for k in
            ("taxes_vente", "carburants", "tabac", "alcool", "consommation_autres")),
        "entreprises_gouvernement": sum(rev[k] for k in
            ("hydro", "loto", "saq", "iq", "sqdc", "entreprises_autres")),
        "transferts_federaux": sum(rev[k] for k in
            ("perequation", "sante_federal", "social_federal", "autres_federaux")),
    }
    sums["revenus_autonomes"] = (
        sums["impots_sur_revenu_et_biens"] + sums["taxes_consommation"] +
        sums["entreprises_gouvernement"] + rev["droits_redevances"] + rev["revenus_divers"])
    sums["revenus_totaux"] = sums["revenus_autonomes"] + sums["transferts_federaux"]
    require(all(entier_signé(subs[k]) == v for k, v in sums.items()) and
            entier_signé(subs["droits_permis_redevances"]) == rev["droits_redevances"] and
            entier_signé(subs["revenus_divers"]) == rev["revenus_divers"],
            "SOMMES_REVENUS_INCOHERENTES")
    plan = x.get("transcription_plan_budgetaire_f2")
    require(type(plan) is dict and
            "signe négatif" in plan.get("note_signes", "").lower(),
            "SIGNES_NON_EXPLIQUES")
    f2 = plan.get("montants_signes_comme_affiches_mcad")
    dep = b.get("depenses_et_ajustements_officiels_mcad")
    require(type(f2) is dict and tuple(f2) == F2_FIELDS and
            type(dep) is dict, "DIX_MONTANTS_F2_REQUIS")
    for field in F2_FIELDS:
        n = entier_signé(f2[field])
        if field in SIGNED_NEGATIVE:
            require(n < 0 and n == -entier_signé(dep[field]),
                    "SIGNE_DEPENSE_INVALIDE_" + field)
        elif field in SIGNED_NEGATIVE_ALREADY:
            require(n < 0 and n == entier_signé(dep[field]),
                    "SOLDE_LEGAL_INVALIDE_" + field)
        else:
            require(n > 0 and n == entier_signé(subs[field]),
                    "F2_RECETTES_DIVERGENTES_" + field)
    require(entier_signé(f2["revenus_totaux"]) == (
                entier_signé(f2["revenus_autonomes"]) +
                entier_signé(f2["transferts_federaux"])) and
            entier_signé(f2["depenses_totales"]) == (
                entier_signé(f2["depenses_portefeuilles"]) +
                entier_signé(f2["service_dette"])) and
            entier_signé(f2["deficit_comptable"]) == (
                entier_signé(f2["revenus_totaux"]) +
                entier_signé(f2["depenses_totales"]) +
                entier_signé(f2["provision_eventualites"])) and
            entier_signé(f2["solde_budgetaire_loi_equilibre"]) == (
                entier_signé(f2["deficit_comptable"]) +
                entier_signé(f2["versements_fonds_generations"])),
            "CHAINAGE_SOLDE_BUDGETAIRE_ERRONE")
    # Rapport public liste blanche: aucune URL, ligne fiscale, microdonnee, nom.
    return {
        "jalon": "P52J", "schema_version": "P52J-1",
        "lecture_primaire_assistee_tables": 2,
        "lignes_revenus_concordantes": 21,
        "agregats_revenus_concordants": 8,
        "lignes_plan_budgétaire_concordantes": 10,
        "recoupements_numeriques_locaux": 39,
        "prevision_budget_2026_2027": True,
        "relecture_humaine_independante": False,
        "f09_preuve_independante_obtenue": False,
        "preuves_P52A_encore_non_attestees": 20,
        "champs_financiers_P52H_encore_inconnus": 1320,
        "budget_de_reforme_certifie": False,
        "absence_appauvrissement_demontree": False,
        "publication_autorisee": False,
        "fusion_autorisee": False,
        "decision": "NO_GO_AUTOMATIQUE"
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for key,path in FILES.items():
        parser.add_argument("--"+key, type=Path, default=path)
    parser.add_argument("--rapport", type=Path)
    parser.add_argument("--exiger-attestation",action="store_true")
    args=parser.parse_args(argv)
    try:
        r=comparer({key:charge(getattr(args,key)) for key in FILES})
        code=3 if args.exiger_attestation else 0
    except (OSError, ValueError, UnicodeError, TypeError, KeyError) as error:
        r={"jalon":"P52J", "statut":"ERREUR_VALIDATION",
           "type_erreur":type(error).__name__,
           "publication_autorisee":False, "fusion_autorisee":False,
           "decision":"NO_GO_AUTOMATIQUE"}
        code=2
    serialized=json.dumps(r, ensure_ascii=False, indent=2)+"\n"
    if args.rapport:
        args.rapport.parent.mkdir(parents=True,exist_ok=True)
        args.rapport.write_text(serialized,encoding="utf-8")
    else:
        print(serialized,end="")
    return code

if __name__=="__main__":
    raise SystemExit(main())
