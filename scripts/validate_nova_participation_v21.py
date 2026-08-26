#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARTICIPATION=ROOT/'projets/projet-nova/recrutement.html'
CONTACT=ROOT/'projets/projet-nova/contact.html'
PRIVACY=ROOT/'projets/projet-nova/confidentialite.html'
OLD_FORM=ROOT/'projets/projet-nova/formulaire-soutien.html'
OLD_PDF=ROOT/'projets/projet-nova/documents/10_Formulaire_Soutien_Preadhesion_Projet_Nova.pdf'
errors=[]

def read(path):
    if not path.exists():
        errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
        return ''
    return path.read_text('utf-8',errors='ignore')

def req(ok,msg):
    if not ok: errors.append(msg)

participation=read(PARTICIPATION); contact=read(CONTACT); privacy=read(PRIVACY); old_form=read(OLD_FORM)
p=participation.lower(); c=contact.lower(); plow=privacy.lower(); old=old_form.lower()

req('<title>participer | projet nova</title>' in p,'La page participation n’utilise pas le titre public Participer.')
req('mailto:officiellenovaparti@gmail.com' in p,'La page participation ne fournit pas le contact direct prévu.')
req('aucun paiement' in p,'La page participation ne précise pas l’absence de paiement.')
req('aucune date de naissance' in p,'La minimisation de la date de naissance n’est pas expliquée.')
req('aucune adresse domiciliaire' in p,'La minimisation de l’adresse n’est pas expliquée.')
req('aucune pièce d’identité' in p or "aucune pièce d'identité" in p,'La minimisation des pièces d’identité n’est pas expliquée.')
req('adhésion officielle' in p,'La séparation avec une future adhésion officielle n’est pas expliquée.')
req('confidentialité' in p,'La page participation ne renvoie pas au cadre de confidentialité.')

# Aucun fournisseur de formulaire public externe ne doit rester actif dans Nova A1.
for name,text in [('participation',p),('contact',c)]:
    req('formspree.io' not in text,f'Le fournisseur Formspree est encore actif dans la page {name}.')
    req('formsubmit.co' not in text,f'Le fournisseur FormSubmit est encore actif dans la page {name}.')
    req('<form' not in text,f'Un formulaire HTML public reste actif dans la page {name}.')

req('mailto:officiellenovaparti@gmail.com' in c,'La page contact ne fournit pas le courriel direct.')
req('aucun formulaire public nova' in c,'La page contact n’explique pas la suspension des formulaires externes.')

for phrase in [
    'collecter moins. protéger davantage',
    'aucun formulaire externe de participation ou de contact',
    'responsable provisoire',
    'intérêt politique',
    'adresse domiciliaire complète',
    'date de naissance',
    'incidents de confidentialité',
    'suppression'
]:
    req(phrase in plow,f'Politique de confidentialité Nova incomplète: {phrase}')
req('formspree' in plow and 'suspendus' in plow,'La politique doit documenter la suspension des anciens formulaires Formspree.')

req('recrutement.html' in old,'L’ancienne page de soutien ne redirige pas vers Participer.')
req('noindex' in old,'L’ancienne page de soutien doit être non indexée.')
req(not OLD_PDF.exists(),'L’ancien PDF de soutien/préadhésion est encore présent.')

if errors:
    print(f'ECHEC participation Nova A1: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK Projet Nova A1: aucun formulaire tiers actif, collecte Web politique suspendue, contact direct et confidentialité documentée.')
