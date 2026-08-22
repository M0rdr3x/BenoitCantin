#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def text(rel): return (ROOT/rel).read_text('utf-8',errors='ignore')

def require(errors, src, marker, message):
  if marker not in src: errors.append(message)

def main():
  errors=[]
  pages={
    'compte/connexion.html':'sinjira-auth-pages.js',
    'compte/inscription.html':'v24-signup.js',
    'compte/reinitialiser-mot-de-passe.html':'sinjira-recovery-v24-4-99.js',
    'compte/mot-de-passe-oublie.html':'sinjira-auth-pages.js',
  }
  for rel,module in pages.items():
    p=ROOT/rel
    if not p.exists(): errors.append(f'Page auth absente: {rel}'); continue
    src=text(rel)
    if 'noindex' not in src.lower(): errors.append(f'Page auth indexable: {rel}')
    if module not in src: errors.append(f'Module auth absent de {rel}: {module}')
    if 'data-account-status' not in src: errors.append(f'Zone de statut auth absente: {rel}')
  for rel in pages:
    src=text(rel)
    guard=src.find('sinjira-auth-route.js')
    module=max(src.find('sinjira-auth-pages.js'),src.find('v24-signup.js'),src.find('sinjira-recovery-v24-4-99.js'))
    if guard<0: errors.append(f'Garde de redirection auth absent: {rel}')
    elif module>=0 and guard>module: errors.append(f'Garde auth chargé après le module dans {rel}')

  helper=text('assets/js/sinjira-auth-route.js')
  for required in ["raw.startsWith('//')","raw.includes('\\\\')","url.origin !== location.origin"]:
    if required not in helper: errors.append(f'Garde anti-open-redirect incomplet: {required}')

  signup_html=text('compte/inscription.html')
  if len(re.findall(r'minlength=["\']12["\']',signup_html))<2:
    errors.append('Inscription: les deux champs mot de passe doivent imposer minlength=12.')
  if len(re.findall(r'autocomplete=["\']new-password["\']',signup_html))<2:
    errors.append('Inscription: autocomplete=new-password absent sur les deux champs mot de passe.')
  for marker,label in [
    ('name="display_name"','nom affiché'),('name="email"','courriel'),('name="birth_date"','date de naissance'),
    ('data-signup-birth-date','garde date locale'),('confidentialite-joueur.html','consentement confidentialité'),
    ('partir de 13 ans','âge minimum visible 13 ans'),('À 13 ans','autorisation parentale visible à 13 ans'),
    ('Moins de 13 ans','refus libre-service visible sous 13 ans'),
    ('identifiant technique privé','séparation visible du nom affiché et de l’identifiant technique')
  ]:
    if marker not in signup_html: errors.append(f'Inscription: champ/contrat absent: {label}.')
  if 'name="pseudo"' in signup_html:
    errors.append('Inscription: un pseudo technique ne doit plus être demandé au membre.')

  signup=text('assets/js/v24-signup.js')
  signup_requirements={
    'password.length<12':'politique 12 caractères',
    'password!==confirm':'confirmation du mot de passe',
    "if(!displayName)":'nom affiché non vide après normalisation',
    'pseudo:displayName':'alias de compatibilité dérivé du nom affiché',
    'display_name:displayName':'nom affiché transmis au profil',
    'form.checkValidity()':'validation HTML native',
    'setBusy(true)':'verrou anti-double soumission',
    "console.warn('[SINJIRA signup]'":'gestion explicite des erreurs réseau',
    'localDateString()':'date maximale calculée en heure locale',
    'birthInput.max=localDateString()':'borne de naissance locale',
    'GUARDIAN_CODE_RE':'validation du code parental',
    'age<13':'âge minimum 13 ans',
    'age<14&&!guardianCode':'autorisation parentale obligatoire à 13 ans',
    "age>=13&&age<18":'cohorte jeunesse 13–17',
    'age>120':'borne de date de naissance',
    "window.SINJIRA_AUTH_ROUTE?.next":'destination sécurisée partagée',
  }
  for marker,label in signup_requirements.items():
    require(errors, signup, marker, f'Inscription: contrat absent: {label}.')
  if "d.get('pseudo')" in signup:
    errors.append('Inscription: le client lit encore un pseudo technique saisi par le membre.')
  if 'age<12' in signup:
    errors.append('Inscription: ancien seuil 12 ans encore présent dans le client.')
  if 'toISOString().slice(0,10)' in signup:
    errors.append('Inscription: borne de date UTC détectée; elle peut autoriser demain selon le fuseau horaire.')

  auth=text('assets/js/sinjira-auth-pages.js')
  auth_requirements={
    'signInWithPassword':'connexion par mot de passe',
    'resetPasswordForEmail':'demande de récupération',
    'reportInvalid(form)':'validation HTML avant requête Auth',
    'setBusy(form,true)':'verrou anti-double soumission',
    "console.warn('[SINJIRA auth login]'":'gestion erreur réseau connexion',
    "console.warn('[SINJIRA auth recovery]'":'gestion erreur réseau récupération',
  }
  for marker,label in auth_requirements.items():
    require(errors, auth, marker, f'Module auth dédié incomplet: {label}.')
  if "setStatus(status,'Connexion impossible." not in auth:
    errors.append('Connexion: erreur générique anti-divulgation absente.')
  if 'Si un compte correspond à cette adresse' not in auth:
    errors.append('Récupération: réponse anti-énumération absente.')
  if 'La demande de récupération n’a pas pu être traitée pour le moment.' not in auth:
    errors.append('Récupération: erreur opérationnelle générique absente.')

  recovery=text('assets/js/sinjira-recovery-v24-4-99.js')
  recovery_requirements={
    's.auth.getUser()':'validation serveur du lien/session de récupération',
    'getAuthenticatorAssuranceLevel':'lecture AAL de récupération',
    "data?.nextLevel==='aal2'":'détection d’un MFA vérifié disponible',
    "data?.currentLevel!=='aal2'":'exigence AAL2 avant changement',
    'mfa.html?recovery=1':'passage par la page TOTP',
    'updateUser({password})':'mise à jour du mot de passe',
    "security_after_password_recovery":'nettoyage serveur après récupération',
    "signOut({scope:'global'})":'révocation globale après récupération',
    'password.length<12':'politique 12 caractères',
    'form.checkValidity()':'validation HTML avant changement',
    'setBusy(true)':'verrou anti-double soumission',
  }
  for marker,label in recovery_requirements.items():
    require(errors,recovery,marker,f'Récupération V24.4.99 incomplète: {label}.')
  if '.auth.getSession()' in recovery:
    errors.append('Réinitialisation: getSession() local ne doit pas remplacer la validation serveur getUser().')

  reset=text('compte/reinitialiser-mot-de-passe.html')
  if len(re.findall(r'minlength=["\']12["\']',reset))<2:
    errors.append('Réinitialisation: les deux champs doivent imposer minlength=12.')
  if len(re.findall(r'autocomplete=["\']new-password["\']',reset))<2:
    errors.append('Réinitialisation: autocomplete=new-password absent sur les deux champs.')
  if 'second facteur' not in reset or 'sinjira-recovery-v24-4-99.js?v=24.4.99' not in reset:
    errors.append('Réinitialisation: explication MFA ou module V24.4.99 absent.')

  login=text('compte/connexion.html')
  if 'autocomplete="current-password"' not in login and "autocomplete='current-password'" not in login:
    errors.append('Connexion: autocomplete=current-password absent.')
  forgot=text('compte/mot-de-passe-oublie.html')
  if 'autocomplete="email"' not in forgot and "autocomplete='email'" not in forgot:
    errors.append('Récupération: autocomplete=email absent.')

  for rel in ['compte/connexion.html','compte/mot-de-passe-oublie.html','compte/reinitialiser-mot-de-passe.html']:
    if 'sinjira-account.js' in text(rel): errors.append(f'Ancien module multifonction encore chargé sur une page auth: {rel}')

  for rel,src in [('assets/js/v24-signup.js',signup),('assets/js/sinjira-auth-pages.js',auth),('assets/js/sinjira-recovery-v24-4-99.js',recovery)]:
    if re.search(r'console\.(?:log|info|warn|error)\([^\n]*\bpassword\b',src,re.I):
      errors.append(f'Secret potentiel journalisé dans {rel}: référence password dans console.*().')

  print(f'Validation auth SINJIRA V24.4.99: {len(pages)} pages critiques.')
  if errors:
    print(f'ECHEC auth: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    return 1
  print('OK auth V24.4.99: connexion, inscription, récupération AAL2 conditionnelle, révocation globale, anti-énumération et politique 12 caractères cohérents.')
  return 0

if __name__=='__main__': raise SystemExit(main())
