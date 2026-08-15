#!/usr/bin/env python3
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import re, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
TEXT_EXTS={'.html','.js','.css','.json','.md','.txt','.xml','.webmanifest','.sql','.ts'}
SECRET_PATTERNS=[
 re.compile(r'SUPABASE_SERVICE_ROLE_KEY\s*[:=]\s*[\'\"]?[A-Za-z0-9._-]{20,}',re.I),
 re.compile(r'OPENAI_API_KEY\s*[:=]\s*[\'\"]?sk-[A-Za-z0-9_-]{16,}',re.I),
 re.compile(r'sk-proj-[A-Za-z0-9_-]{16,}')]

class Parser(HTMLParser):
 def __init__(self): super().__init__(convert_charrefs=True); self.refs=[]; self.ids=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if d.get('id'): self.ids.append(d['id'])
  attr={'a':'href','img':'src','script':'src','link':'href','source':'src','video':'src','audio':'src','iframe':'src'}.get(tag)
  if attr and d.get(attr): self.refs.append((tag,d[attr]))

def all_files():
 return [p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and 'node_modules' not in p.parts]

def resolve(page,raw):
 if not raw or raw.startswith(('#','mailto:','tel:','javascript:','data:','blob:','//')): return None
 u=urlparse(raw)
 if u.scheme in {'http','https'}: return None
 path=unquote(u.path)
 if not path: return None
 q=(ROOT/path.lstrip('/')) if path.startswith('/') else (page.parent/path)
 if path.endswith('/'): q=q/'index.html'
 if not q.exists() and q.suffix=='' and (q/'index.html').exists(): q=q/'index.html'
 return q.resolve()

def main():
 errors=[]; files=all_files(); htmls=[p for p in files if p.suffix.lower()=='.html']; js=[p for p in files if p.suffix.lower()=='.js']
 for p in files:
  rel=str(p.relative_to(ROOT))
  if p.name=='1': errors.append(f"Fichier parasite nommé '1': {rel}")
  if re.search(r'SINJIRA.*Livre.*01.*La.*Cendre.*Jugement(?!.*DEMO).*\.pdf$',rel,re.I) or re.search(r'MAITRE.*CORRIGE.*\.pdf$',rel,re.I): errors.append(f'Roman intégral potentiellement public: {rel}')
  if p.suffix.lower() in TEXT_EXTS and p.stat().st_size<=3_000_000:
   text=p.read_text('utf-8',errors='ignore')
   for rx in SECRET_PATTERNS:
    if rx.search(text): errors.append(f'Secret potentiel dans {rel}')
 for page in htmls:
  parser=Parser(); parser.feed(page.read_text('utf-8',errors='ignore'))
  duplicates=sorted({x for x in parser.ids if parser.ids.count(x)>1})
  if duplicates: errors.append(f"IDs dupliqués dans {page.relative_to(ROOT)}: {', '.join(duplicates)}")
  for tag,raw in parser.refs:
   target=resolve(page,raw)
   if target is not None and not target.exists(): errors.append(f'Référence manquante dans {page.relative_to(ROOT)} ({tag}): {raw}')
 for rel in ['index.html','404.html','admin/index.html','admin/sinjira/index.html','compte/index.html','compte/profil.html','compte/mon-personnage.html','compte/reseau-personnage.html','projets/sinjira/index.html','projets/sinjira/registre/index.html','projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html']:
  if not (ROOT/rel).exists(): errors.append(f'Route critique absente: {rel}')
 try:
  subprocess.run(['node','--version'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for p in js:
   r=subprocess.run(['node','--check',str(p)],text=True,capture_output=True)
   if r.returncode: errors.append(f'Erreur JavaScript dans {p.relative_to(ROOT)}: {r.stderr.strip()}')
 except (FileNotFoundError,subprocess.CalledProcessError):
  print('AVERTISSEMENT: Node indisponible, validation JS ignorée.')
 print(f'Validation SINJIRA: {len(htmls)} HTML, {len(js)} JS, {len(files)} fichiers.')
 if errors:
  print(f'ECHEC: {len(errors)} problème(s).')
  for e in errors: print('- '+e)
  return 1
 print('OK: aucune erreur statique bloquante détectée.')
 return 0

if __name__=='__main__': raise SystemExit(main())
