#!/usr/bin/env python3
"""P55Z : rapprochement prudent P55X+P55Y, exclusivement fictif et non certifié."""
import argparse
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculer_charges_employeur_nova_p55x import calculer as calculer_p55x
from rapprocher_tarification_cnesst_nova_p55y import rapprocher as rapprocher_p55y

IDENT = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{3,60}\Z')


def verifie_entree(document):
    if not isinstance(document, dict) or document.get('schema_version') != 'P55Z-1':
        raise ValueError('Schema P55Z-1 requis')
    if type(document.get('annee')) is not int or document['annee'] != 2026:
        raise ValueError('Etude limitee a 2026')
    if document.get('territoire') != 'QUEBEC_DANS_LE_CANADA':
        raise ValueError('Interdiction de transposer au Quebec souverain')
    if document.get('nature') != 'FICTIF':
        raise ValueError('Rapprochement reserve a un scenario explicitement fictif')
    reference = document.get('scenario_id')
    if not isinstance(reference, str) or not IDENT.fullmatch(reference):
        raise ValueError('Identifiant de scenario anonymise requis')
    if document.get('attestation_meme_population_fictive') is not True:
        raise ValueError('Confirmation de la meme population fictive requise')
    if document.get('assiettes_salariales_fictives_concordantes') is not True:
        raise ValueError('Concordance des assiettes fictives non declaree')
    x = document.get('hypotheses_p55x')
    y = document.get('hypotheses_p55y')
    if not isinstance(x, dict) or not isinstance(y, dict):
        raise ValueError('Deux jeux de donnees documentes obligatoires')
    if set(x.keys()) != {'salaire_annuel_fictif_cad','effectif_fictif','secteur_fss'}:
        raise ValueError('Hypotheses P55X non conformes')
    if set(y.keys()) != {'unites'}:
        raise ValueError('Hypotheses P55Y non conformes')
    return reference, x, y


def rapprocher(document):
    ref, x, y = verifie_entree(document)
    result_x = calculer_p55x(x['salaire_annuel_fictif_cad'], x['effectif_fictif'], x['secteur_fss'])
    source_y = {
        'schema_version': 'P55Y-1', 'annee': 2026,
        'territoire': 'QUEBEC_DANS_LE_CANADA', 'nature': 'FICTIF',
        'unites': y['unites']
    }
    result_y = rapprocher_p55y(source_y)
    if result_x['decision'] != 'NO_GO_AUTOMATIQUE' or result_y['decision'] != 'NO_GO_AUTOMATIQUE':
        raise ValueError('Controle de non-adoption des sources manquant')
    values_x = result_x['calculs_conditionnels']
    salaires_x = Decimal(values_x['masse_salariale_cad'])
    salaires_y = result_y['salaires_assurables_totaux_cad']
    prime_y = result_y['prime_cnesst_conditionnelle_totale_cad']
    compatible = salaires_y is not None and Decimal(salaires_y) == salaires_x
    # Sans correspondance d'assiettes et population, meme pour la fiction,
    # les couts P55X et P55Y ne peuvent etre additionnes.
    somme_six = None
    somme_avec_salaires = None
    if compatible and prime_y is not None:
        somme_six = Decimal(values_x['somme_charges_partielles_cad']) + Decimal(prime_y)
        somme_avec_salaires = salaires_x + somme_six
    return {
        'schema_version': 'P55Z-1',
        'annee': 2026, 'territoire': 'QUEBEC_DANS_LE_CANADA',
        'scenario_id_fictif': ref,
        'statut': 'SIMULATION_FICTIVE_NON_AUDITEE',
        'decision': 'NO_GO_AUTOMATIQUE',
        'score_p55n_estime_pourcent': 53,
        'rapprochement': {
            'assiettes_fictives_concordantes': compatible,
            'nombre_unites_incompletes_p55y': result_y['nombre_unites_incompletes'],
            'masse_salariale_p55x_cad': values_x['masse_salariale_cad'],
            'salaires_assurables_p55y_cad': salaires_y,
            'charges_partielles_p55x_cad': values_x['somme_charges_partielles_cad'],
            'prime_cnesst_hypothetique_p55y_cad': prime_y,
            'charges_partielles_six_postes_cad':
                str(somme_six.quantize(Decimal('0.01'))) if somme_six is not None else None,
            'salaire_plus_six_charges_partielles_cad':
                str(somme_avec_salaires.quantize(Decimal('0.01')))
                if somme_avec_salaires is not None else None,
            'cotisations_formation_main_oeuvre_cad': None,
            'assurances_collectives_et_autres_avantages_cad': None,
            'ajustements_cnesst_reels_cad': None,
            'cout_employeur_complet_cad': None,
            'comparaison_avant_apres_nova_cad': None,
            'economie_budgetaire_publique_cad': None,
        },
        'blocages': [
            'Exemple fictif: les taux et salaires ne sont pas des pieces employeur',
            'Une egalite de masse salariale n authentifie pas un perimetre reel',
            'CNESST: classification, taux individuels et ajustements manquants',
            'FSS: associes, exceptions et assiettes legales a verifier',
            'Aucune donnee de prestations, formation, avantages ou cout complet',
            'Maintien des emplois, regimes sociaux et services non demontre',
            'Aucune assiette ni taux definitif pour les deux prelevements Nova',
            'Deux cadres constitutionnels non cumulables',
            '600 inconnues budgetaires P52B, 720 montants incidence P52D',
            'Aucune validation juridique, actuarielle ou comptable externe'
        ],
        'certification_independante': False
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entree', required=True, type=Path)
    parser.add_argument('--bilan-public', type=Path)
    parser.add_argument('--exiger-faisabilite', action='store_true')
    args = parser.parse_args(argv)
    if args.exiger_faisabilite:
        print('NO_GO_AUTOMATIQUE: aucune faisabilite Nova certifiee', file=sys.stderr)
        return 3
    try:
        document = json.loads(args.entree.read_text(encoding='utf-8'))
        sortie = json.dumps(rapprocher(document), ensure_ascii=False, indent=2) + '\n'
        if args.bilan_public:
            with args.bilan_public.open('x', encoding='utf-8') as f:
                f.write(sortie)
        else:
            print(sortie, end='')
        return 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print('REFUS: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
