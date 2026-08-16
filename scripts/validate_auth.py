#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def text(rel): return (ROOT/rel).read_text('utf-8',errors='ignore')

def main():
  errors=[]
  pages={
    'compte/connexion.html':'sinjira-auth-pages.js',
    'compte/inscription.html':'v24-signup.js',
    'compte/reinitialiser-mot-de-passe.html':'sinjira-auth-pages.js',
    'compte/mot-de-passe-oublie.html':'sinjira-auth-pages.js',
  }
  for rel,module in pages.items():
    p=ROOT/rel
    if not p.exists(): errors.append(f'Page auth absente: {rel}'); continue
    src=text(rel)
    if 'noindex' not in src.lower(): errors.append(f'Page auth indexable: {rel}')
    if module not in src: errors.append(f'Module auth absent de {rel}: {module}')
  for rel in pages:
    src=text(rel)
    guard=src.find('sinjira-auth-route.js')
    module=max(src.find('sinjira-auth-pages.js'),src.find('v24-signup.js'))
    if guard<0: errors.append(f'Garde de redirection auth absent: {rel}')
    elif module>=0 and guard>module: errors.append(f'Garde auth chargé après le module dans {rel}')
  helper=text('assets/js/sinjira-auth-route.js')
  for required in ["raw.startsWith('//')","raw.includes('\\\\')","url.origin !== location.origin"]:
    if required not in helper: errors.append(f'Garde anti-open-redirect incomplet: {required}')
  signup=text('assets/js/v24-signup.js')
  if 'password.length<12' not in signup: errors.append('Inscription: politique 12 caractères absente du JS.')
  if "window.SINJIRA_AUTH_ROUTE?.next" not in signup: errors.append('Inscription: destination sécurisée partagée non utilisée.')
  auth=text('assets/js/sinjira-auth-pages.js')
  for required in ["signInWithPassword","resetPasswordForEmail","updateUser({password})","signOut({scope:'global'})"]:
    if required not in auth: errors.append(f'Module auth dédié incomplet: {required}')
  if "setStatus(status,'Connexion impossible." not in auth: errors.append('Connexion: erreur générique anti-divulgation absente.')
  if 'Si un compte correspond à cette adresse' not in auth: errors.append('Récupération: réponse anti-énumération absente.')
  reset=text('compte/reinitialiser-mot-de-passe.html')
  if len(re.findall(r'minlength=["\']12["\']',reset))<2: errors.append('Réinitialisation: les deux champs doivent imposer minlength=12.')
  if 'password.length<12' not in auth: errors.append('Réinitialisation: règle JS 12 caractères absente.')
  for rel in ['compte/connexion.html','compte/mot-de-passe-oublie.html','compte/reinitialiser-mot-de-passe.html']:
    if 'sinjira-account.js' in text(rel): errors.append(f'Ancien module multifonction encore chargé sur une page auth: {rel}')
  print(f'Validation auth SINJIRA: {len(pages)} pages critiques.')
  if errors:
    print(f'ECHEC auth: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    return 1
  print('OK auth: module isolé, redirections internes, anti-énumération et politique de mot de passe cohérents.')
  return 0

if __name__=='__main__': raise SystemExit(main())
