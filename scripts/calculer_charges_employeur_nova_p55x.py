#!/usr/bin/env python3
"""P55X : scénario patronal 2026 partiel, jamais une simulation fiscale Nova."""
import argparse
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CENT = Decimal('0.01')

def montant(texte):
    if not isinstance(texte, str) or not re.fullmatch(r'\d+(?:\.\d{1,2})?', texte):
        raise ValueError('Salaire: décimal positif en dollars, au plus deux décimales')
    valeur = Decimal(texte)
    if valeur > Decimal('1000000000'):
        raise ValueError('Salaire hors limite du scénario de test')
    return valeur

def argent(valeur):
    return str(valeur.quantize(CENT, rounding=ROUND_HALF_UP))

def taux_fss(masse, secteur):
    if secteur not in ('general', 'primaire_manufacturier', 'public'):
        raise ValueError('Secteur FSS non reconnu')
    if secteur == 'public' or masse >= Decimal('7800000'):
        return Decimal('4.26')
    if masse <= Decimal('1000000'):
        return Decimal('1.65') if secteur == 'general' else Decimal('1.25')
    millions = masse / Decimal('1000000')
    if secteur == 'general':
        return Decimal('1.2662') + Decimal('0.3838') * millions
    return Decimal('0.8074') + Decimal('0.4426') * millions

def calculer(salaire_texte, effectif, secteur):
    salaire = montant(salaire_texte)
    if isinstance(effectif, bool) or not isinstance(effectif, int) or effectif < 1 or effectif > 100000:
        raise ValueError('Effectif entier entre 1 et 100000')
    masse = salaire * effectif
    rrq = (max(Decimal(0), min(salaire, Decimal('74600')) - Decimal('3500')) * Decimal('.063')
           + max(Decimal(0), min(salaire, Decimal('85000')) - Decimal('74600')) * Decimal('.04'))
    rqap = min(salaire, Decimal('103000')) * Decimal('.00602')
    ae = min(salaire, Decimal('68900')) * Decimal('.0182')
    rrq, rqap, ae = [x.quantize(CENT, rounding=ROUND_HALF_UP) for x in (rrq, rqap, ae)]
    total_trois = (rrq + rqap + ae) * effectif
    taux = taux_fss(masse, secteur)
    fss = (masse * taux / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    normes = (min(salaire, Decimal('103000')) * Decimal('.0006') * effectif).quantize(CENT, rounding=ROUND_HALF_UP)
    partiel = total_trois + fss + normes
    return {
        'schema_version': 'P55X-1', 'annee': 2026,
        'juridiction': 'QUEBEC_DANS_LE_CANADA',
        'statut': 'SCENARIO_FICTIF_PARTIEL_NON_CERTIFIE',
        'decision': 'NO_GO_AUTOMATIQUE',
        'hypotheses': {
            'effectif_fictif': effectif, 'salaire_annuel_identique_fictif_cad': argent(salaire),
            'secteur_fss_confirme_pour_simulation': secteur,
            'aucun_employeur_associe': True, 'aucun_conge_ni_exemption_fss': True,
            'cotisation_normes_applicable': True,
            'tous_salaries_admissibles_rrq_rqap_ae': True,
            'salaire_total_fss_et_normes_assujetti': True,
            'an_complet_un_employeur_age_18_64': True
        },
        'calculs_conditionnels': {
            'masse_salariale_cad': argent(masse),
            'rrq_employeur_cad': argent(rrq * effectif),
            'rqap_employeur_cad': argent(rqap * effectif),
            'assurance_emploi_employeur_cad': argent(ae * effectif),
            'trois_cotisations_p55w_cad': argent(total_trois),
            'taux_fss_pct': str(taux),
            'fonds_services_sante_cad': argent(fss),
            'cotisation_normes_travail_cad': argent(normes),
            'somme_charges_partielles_cad': argent(partiel),
            'prime_cnesst_sst_cad': None,
            'cotisations_formation_main_oeuvre_cad': None,
            'avantages_sociaux_et_autres_charges_cad': None,
            'cout_complet_employeur_cad': None,
            'variation_nova_cad': None
        },
        'limitations': [
            'Aucun taux CNESST individuel sans classe, tarification et salaire assurable',
            'Le taux moyen CNESST 2026 de 1,54 $ par 100 $ ne sert pas de taux entreprise',
            'FSS: employeurs associes, exemptions et remuneration assujettie non modelises',
            'Cotisation normes: exemptions legales et situations particulieres exclues',
            'Formation, vacances, avantages, accidents, conventions et incidences prix non evalues',
            'Calcul illustratif 2026 du regime actuel uniquement, sans comparaison fiscale Nova',
            'Aucune abolition de cotisations sociales sans financement des droits',
            '600 montants budgetaires P52B et 720 incidences P52D restent inconnus'
        ],
        'maturite_programme_p55n_pourcent': 53,
        'faisabilite_nova_certifiee': False
    }

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--salaire', required=True)
    p.add_argument('--effectif', type=int, required=True)
    p.add_argument('--secteur', choices=('general','primaire_manufacturier','public'), required=True)
    p.add_argument('--hypotheses-confirmees', action='store_true')
    p.add_argument('--bilan-public', type=Path)
    p.add_argument('--exiger-faisabilite', action='store_true')
    args = p.parse_args(argv)
    if args.exiger_faisabilite:
        print('NO_GO_AUTOMATIQUE: aucune faisabilité Nova démontrée', file=sys.stderr)
        return 3
    if not args.hypotheses_confirmees:
        print('REFUS: confirmer explicitement les hypothèses de calcul', file=sys.stderr)
        return 2
    try:
        result = calculer(args.salaire, args.effectif, args.secteur)
        contenu = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.bilan_public:
            with args.bilan_public.open('x', encoding='utf-8') as fh:
                fh.write(contenu)
        else:
            print(contenu, end='')
        return 0
    except (ValueError, OSError) as erreur:
        print(f'REFUS: {erreur}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
