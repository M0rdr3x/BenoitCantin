#!/usr/bin/env python3
"""P56A : audit de préparation des budgets décennaux P52B, sans prévision inventée."""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

import evaluer_transition_fiscale_nova_p52b as p52b

ASSERTIONS = (
    'perimetre_reconcilie',
    'incidence_menages_validee',
    'emplois_et_services_valides',
    'inventaire_prelevements_valide',
)
LACUNES_DE_FOND = [
    'Absence de réconciliation des données officielles budget, préélectoral et comptes publics',
    'Absence de rapprochement des flux intergouvernementaux, municipaux et intra-périmètre',
    'Aucune assiette ni taux adoptés pour les deux prélèvements étudiés',
    'Répartition des fonctions souveraines, dettes, actifs et pensions non négociée',
    'Continuité emplois, prestations, santé, éducation et services non financée sur preuve',
    'Absence de validation des effets distributifs sur ménages et entreprises',
    'Aucun avis indépendant authentifié; vingt preuves P52A encore à instruire'
]


def auditer(gabarit, registre):
    # Utiliser le validateur P52B existant; ne jamais fabriquer un modèle parallèle.
    bilan = p52b.evaluate(gabarit, registre)
    regimes = gabarit['regimes']
    rows = []
    by_field = Counter()
    by_regime = Counter()
    by_year = Counter()
    annual_fully_populated = 0
    assumptions_zero = 0
    sources_non_authentifiees = 0
    assertions_false = 0
    missing_safeguards = 0
    missing_financial = 0
    signed_gate_missing = 0
    for regime in p52b.REGIMES:
        for trajectoire in p52b.TRAJECTOIRES:
            for idx, year in enumerate(p52b.EXERCICES):
                row = regimes[regime]['trajectoires'][trajectoire][idx]
                checked = p52b.verify_row(row, year)
                assert checked['exercice_debut'] == year
                names_missing = []
                for group in ('recettes', 'depenses'):
                    for name in (p52b.RECETTES if group == 'recettes' else p52b.DEPENSES):
                        raw = row[group][name]
                        if raw is None:
                            names_missing.append(name)
                            by_field[name] += 1
                            missing_financial += 1
                            by_regime[regime] += 1
                            by_year[year] += 1
                        else:
                            # A text label or URL is not authenticated documentary proof.
                            sources_non_authentifiees += 1
                            if name == 'anti_evasion_additionnelle_nette' and raw == '0':
                                assumptions_zero += 1
                flags_missing = [a for a in ASSERTIONS if row[a] is not True]
                assertions_false += len(flags_missing)
                prior = row['solde_budgetaire_precedent']
                ratio = row['ratio_dette_nette_pib_pct']
                missing_safeguards += int(prior is None) + int(ratio is None)
                if prior is not None and ratio is not None:
                    signed_gate_missing += int(not checked['conditions_financieres_preliminaires_remplies'])
                if not names_missing:
                    annual_fully_populated += 1
                rows.append({
                    'regime': regime, 'trajectoire': trajectoire,
                    'exercice_debut': year,
                    'nombre_valeurs_financieres_absentes': len(names_missing),
                    'postes_financiers_absents': names_missing,
                    'nombre_attestations_non_validees': len(flags_missing),
                    'attestations_non_validees': flags_missing,
                    'solde_simule_gcad': checked['solde_simule_gcad'],
                    'budget_annuel_integralement_documente': False
                })
    assert len(rows) == 60, 'Le modèle doit couvrir exactement 60 exercices-scénarios'
    assert missing_financial == bilan['entrees_financieres_manquantes']
    assert assumptions_zero + missing_financial <= 60 * len(p52b.ALL)
    source_count = 60 * len(p52b.ALL)
    # Aucun drapeau ni URL n'atteste une expertise indépendante.
    baseline = gabarit['reference_2026_2027']
    baseline_arithmetic = p52b.decimal_gcad(baseline['revenus_consolides']) - p52b.decimal_gcad(
        baseline['depenses_consolidees'])
    return {
        'jalon': 'P56A',
        'schema_version': 'P56A-1',
        'date_revue': '2026-11-07',
        'statut': 'AUDIT_STRUCTUREL_NON_CERTIFIE',
        'decision': 'NO_GO_AUTOMATIQUE',
        'regimes_distincts': list(p52b.REGIMES),
        'trajectoires_distinctes': list(p52b.TRAJECTOIRES),
        'horizon_exercices_debut': list(p52b.EXERCICES),
        'nombre_lignes': len(rows),
        'nombre_champs_monetaires_theoriques': source_count,
        'nombre_champs_monetaires_inconnus': missing_financial,
        'nombre_valeurs_monetaires_presentes_non_authentifiees': sources_non_authentifiees,
        'nombre_hypotheses_zero_anti_evasion': assumptions_zero,
        'annees_scenarios_entierement_renseignees': annual_fully_populated,
        'attestations_p52b_non_validees': assertions_false,
        'conditions_budget_precedent_dette_inconnues': missing_safeguards,
        'conditions_financieres_renseignees_mais_non_satisfaites': signed_gate_missing,
        'preuves_fiscales_p52a_non_validees': bilan['preuves_P52A_encore_non_valides'],
        'inconnues_par_regime': dict(by_regime),
        'inconnues_par_annee': {str(y): by_year[y] for y in p52b.EXERCICES},
        'inconnues_par_poste': {name: by_field[name] for name in p52b.ALL},
        'reference_nova_non_certifiee_2026_2027': {
            'revenus_consolides_gcad': baseline['revenus_consolides'],
            'depenses_consolidees_gcad': baseline['depenses_consolidees'],
            'difference_arithmetique_gcad': str(baseline_arithmetic),
            'difference_est_solde_budgetaire_officiel': False,
            'service_dette_indicatif_deja_inclus_dans_depenses': True,
            'service_dette_ajoute_une_deuxieme_fois': False
        },
        'annees_scenarios': rows,
        'blocages': LACUNES_DE_FOND,
        'comptes_municipaux_consolides_et_rapproches': False,
        'transferts_intragouvernementaux_elimines_et_verifies': False,
        'rapport_2026_preelectoral_amende_concilie': False,
        'financement_et_transition_souveraine_certifies': False,
        'incidences_menages_et_entreprises_validees': False,
        'certification_independante': False,
        'autorisation_de_politique_fiscale': False,
        'pourcentage_maturite_p55n_estimatif': 53,
        'budget_decennal_certifie': False
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gabarit', type=Path, required=True)
    p.add_argument('--registre', type=Path, required=True)
    p.add_argument('--rapport', type=Path)
    p.add_argument('--exiger-budget-certifie', action='store_true')
    a = p.parse_args(argv)
    if a.exiger_budget_certifie:
        print('NO_GO_AUTOMATIQUE: aucun budget decennal certifie', file=sys.stderr)
        return 3
    try:
        template = json.loads(a.gabarit.read_text(encoding='utf-8'))
        register = json.loads(a.registre.read_text(encoding='utf-8'))
        sortie = json.dumps(auditer(template, register), ensure_ascii=False, indent=2) + '\n'
        if a.rapport is not None:
            with a.rapport.open('x', encoding='utf-8') as fh:
                fh.write(sortie)
        else:
            print(sortie, end='')
        return 0
    except (OSError, ValueError, TypeError, KeyError, AssertionError, json.JSONDecodeError) as e:
        print('REFUS: ' + str(e), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
