#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FORM=ROOT/'projets/projet-nova/recrutement.html'
PRIVACY=ROOT/'projets/projet-nova/confidentialite.html'
errors=[]

def read(path):
    if not path.exists():
        errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
        return ''
    return path.read_text('utf-8',errors='ignore')

def req(ok,msg):
    if not ok: errors.append(msg)

form=read(FORM); privacy=read(PRIVACY)
flow=form.lower(); plow=privacy.lower()

req('<title>participer | projet nova</title>' in flow,'La page participation n’utilise pas le titre public Participer.')
req('https://formspree.io/f/' in flow,'Le formulaire participation n’est pas relié au fournisseur de transmission déclaré.')
req('premier contact' in flow,'Le formulaire n’explique pas la logique de premier contact.')
req('aucune adresse domiciliaire demandée' in flow,'La minimisation de l’adresse n’est pas expliquée.')
req('aucune date de naissance ni signature demandée' in flow,'La minimisation naissance/signature n’est pas expliquée.')
req('confirmation 18 ans ou plus' in flow,'La confirmation 18+ sans date de naissance est absente.')
req('consentement contact projet nova' in flow,'Le consentement explicite de contact est absent.')
req('confidentialite.html' in flow,'Lien vers la politique de confidentialité absent du consentement.')
req('états-unis' in flow and 'formspree' in flow,'La transparence sur le traitement Formspree aux États-Unis est absente.')

for forbidden in [
    'name="date de naissance"','name="adresse de domicile"','name="code postal"','name="téléphone"',
    'name="signature numérique','citoyen(ne) canadien(ne)','droits électoraux','destination_attendue',
    'courriel du projet','préadhésion projet nova'
]:
    req(forbidden not in flow,f'Ancien renseignement/contrat trop intrusif encore présent: {forbidden}')

for phrase in [
    'collecter moins, protéger davantage','formspree','états-unis','intérêt politique','participation progressive',
    'adresse résidentielle','date de naissance','citoyenneté','signature numérique','accès, la correction ou la suppression'
]:
    req(phrase in plow,f'Politique de confidentialité Nova incomplète: {phrase}')
req('formsubmit' not in plow,'La politique Nova mentionne encore FormSubmit alors que le site utilise Formspree.')

if errors:
    print(f'ECHEC participation Nova: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK Projet Nova: premier contact 18+ minimal, participation progressive, Formspree transparent et données sensibles écartées.')
