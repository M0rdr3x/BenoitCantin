#!/usr/bin/env python3
"""P55Y : rapprochement arithmétique de taux CNESST déclarés, non certification."""
import argparse
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CENT = Decimal('0.01')
MONEY = re.compile(r'(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?\Z')
RATE = re.compile(r'(?:0|[1-9][0-9]*)(?:\.[0-9]{1,4})?\Z')
CODE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,23}\Z')
VALID_NATURES = {'FICTIF', 'DECLARATION_NON_AUTHENTIFIEE'}


def decimal_str(s, pattern, maximum):
    if not isinstance(s, str) or not pattern.fullmatch(s):
        raise ValueError('Montant ou taux incorrect : chaine decimale obligatoire')
    v = Decimal(s)
    if v > maximum:
        raise ValueError('Valeur hors plage de securite du simulateur')
    return v


def monnaie(v):
    return str(v.quantize(CENT, rounding=ROUND_HALF_UP))


def verifier_racine(data):
    if not isinstance(data, dict) or data.get('schema_version') != 'P55Y-1':
        raise ValueError('Schema P55Y-1 obligatoire')
    if type(data.get('annee')) is not int or data['annee'] != 2026:
        raise ValueError('Annee 2026 obligatoire')
    if data.get('territoire') != 'QUEBEC_DANS_LE_CANADA':
        raise ValueError('Aucune transposition au scenario souverain')
    if data.get('nature') not in VALID_NATURES:
        raise ValueError('Nature fictive ou declaree non authentifiee seulement')
    items = data.get('unites')
    if not isinstance(items, list) or not 1 <= len(items) <= 30:
        raise ValueError('De 1 a 30 unites anonymes requises')
    return items


def rapprocher(data):
    items = verifier_racine(data)
    codes = set()
    entries = []
    somme = Decimal('0')
    somme_salaires = Decimal('0')
    inconnus = 0
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Unite doit etre un objet')
        code = item.get('code')
        if not isinstance(code, str) or not CODE.fullmatch(code) or code in codes:
            raise ValueError('Code unite non conforme ou duplique')
        codes.add(code)
        rate_txt = item.get('taux_prime_par_100_cad')
        salary_txt = item.get('salaires_assurables_cad')
        if data['nature'] == 'FICTIF' and item.get('origine_taux') != 'HYPOTHESE_FICTIVE':
            raise ValueError('Un taux fictif doit etre identifie fictif')
        if data['nature'] == 'DECLARATION_NON_AUTHENTIFIEE' and item.get('origine_taux') != 'DECISION_CNESST_DECLARATION_NON_VERIFIEE':
            raise ValueError('Origine documentaire declaree, non verifiee, requise')
        if rate_txt is None or salary_txt is None:
            # Avoid misleading partial amount: a blank is not a zero.
            if rate_txt is not None:
                decimal_str(rate_txt, RATE, Decimal('100'))
            if salary_txt is not None:
                decimal_str(salary_txt, MONEY, Decimal('100000000000'))
            entries.append({'code': code, 'statut': 'INCOMPLET', 'cotisation_conditionnelle_cad': None})
            inconnus += 1
            continue
        taux = decimal_str(rate_txt, RATE, Decimal('100'))
        salaires = decimal_str(salary_txt, MONEY, Decimal('100000000000'))
        cotisation = (salaires * taux / Decimal('100')).quantize(CENT, rounding=ROUND_HALF_UP)
        somme += cotisation
        somme_salaires += salaires
        entries.append({'code': code, 'statut': 'ARITHMETIQUE_NON_AUDITEE',
                        'taux_par_100_cad': str(taux), 'salaires_assurables_cad': monnaie(salaires),
                        'cotisation_conditionnelle_cad': monnaie(cotisation)})
    return {
        'schema_version': 'P55Y-1', 'annee': 2026, 'territoire': 'QUEBEC_DANS_LE_CANADA',
        'nature': data['nature'], 'statut': 'MODELE_CONDITIONNEL_NON_AUTHENTIFIE',
        'decision': 'NO_GO_AUTOMATIQUE', 'unites': entries, 'nombre_unites': len(entries),
        'nombre_unites_incompletes': inconnus,
        'salaires_assurables_totaux_cad': monnaie(somme_salaires) if not inconnus else None,
        'prime_cnesst_conditionnelle_totale_cad': monnaie(somme) if not inconnus else None,
        'cout_total_employeur_cad': None, 'gain_nova_cad': None,
        'avis_professionnel_authentifie': False,
        'avertissements': [
            'Ne pas utiliser le taux moyen CNESST 1,54 comme taux employeur',
            'Decision de classification, taux de tarification et salaires assurables a verifier par annee',
            'Le salaire assurable individuel 2026 peut etre plafonne a 103000 dollars selon les regles applicables',
            'Les modes de tarification personnalise et retrospectif et ajustements ne sont pas simules',
            'Le taux de versement periodique peut etre pondere et distinct de la prime annuelle finale',
            'Le total conditionnel ne comprend ni FSS ni RRQ/RQAP/AE ni normes du travail',
            'Aucune preuve externe authentifiee ni economie publique certifiee',
            '600 montants budgetaires P52B et 720 incidences P52D demeurent inconnus'
        ],
        'score_p55n_estime_pourcent': 53
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--entree', type=Path, required=True)
    p.add_argument('--bilan-public', type=Path)
    p.add_argument('--exiger-faisabilite', action='store_true')
    args = p.parse_args(argv)
    if args.exiger_faisabilite:
        print('NO_GO_AUTOMATIQUE: aucune faisabilite financiere Nova certifiee', file=sys.stderr)
        return 3
    try:
        payload = json.loads(args.entree.read_text(encoding='utf-8'))
        result = rapprocher(payload)
        texte = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.bilan_public:
            with args.bilan_public.open('x', encoding='utf-8') as f:
                f.write(texte)
        else:
            print(texte, end='')
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f'REFUS: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
