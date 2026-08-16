#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def text(rel): return (ROOT/rel).read_text('utf-8',errors='ignore')

def main():
  errors=[]
  pages={
    'compte/connexion.html':'sinjira-account.js',
    'compte/inscription.html':'v24-signup.js',
    'compte/reinitialiser-mot-de-passe.html':'sinjira-account.js',
    'compte/mot-de-passe-oublie.html':'sinjira-account.js',
  }
  for rel,module in pages.items():
    p=ROOT/rel
    if not p.exists(): errors.append(f'Page auth absente: {rel}'); continue
    src=text(rel)
    if 'noindex' not in src.lower(): errors.append(f'Page auth indexable: {rel}')
    if module not in src: errors.append(f'Module auth absent de {rel}: {module}')
  for rel in ['compte/connexion.html','compte/inscription.html','compte/reinitialiser-mot-de-passe.html']:
    src=text(rel)
    guard=src.find('sinjira-auth-route.js')
    module=max(src.find('sinjira-account.js'),src.find('v24-signup.js'))
    if guard<0: errors.append(f'Garde de redirection auth absent: {rel}')
    elif module>=0 and guard>module: errors.append(f'Garde auth chargé après le module dans {rel}')
  helper=text('assets/js/sinjira-auth-route.js')
  for required in ["raw.startsWith('//')","raw.includes('\\\\')","url.origin !== location.origin"]:
    if required not in helper: errors.append(f'Garde anti-open-redirect incomplet: {required}')
  signup=text('assets/js/v24-signup.js')
  if 'password.length<12' not in signup: errors.append('Inscription: politique 12 caractères absente du JS.')
  if "window.SINJIRA_AUTH_ROUTE?.next" not in signup: errors.append('Inscription: destination sécurisée partagée non utilisée.')
  reset=text('compte/reinitialiser-mot-de-passe.html')
  if len(re.findall(r'minlength=["\']12["\']',reset))<2: errors.append('Réinitialisation: les deux champs doivent imposer minlength=12.')
  if 'enforcePasswordPolicy' not in helper or 'password.length >= 12' not in helper: errors.append('Réinitialisation: garde JS 12 caractères absent.')
  # La connexion historique calcule `next` dans sinjira-account.js; la page doit donc
  # impérativement charger le garde synchrone avant ce module. Une destination //host
  # est supprimée de location.search avant que le module ne puisse la lire.
  login=text('compte/connexion.html')
  if login.find('sinjira-auth-route.js')>login.find('sinjira-account.js'): errors.append('Connexion: open redirect potentiellement réintroduit.')
  print(f'Validation auth SINJIRA: {len(pages)} pages critiques.')
  if errors:
    print(f'ECHEC auth: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    return 1
  print('OK auth: redirections internes, pages privées et politique de mot de passe cohérentes.')
  return 0

if __name__=='__main__': raise SystemExit(main())
