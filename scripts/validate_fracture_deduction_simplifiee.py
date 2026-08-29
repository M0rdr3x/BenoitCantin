#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'projets/sinjira/jeux/fracture-du-reseau-mere'
INDEX = BASE / 'index.html'
RULES = BASE / 'regles.html'
WEB = BASE / 'jouer.html'
GAMES = ROOT / 'projets/sinjira/jeux/index.html'
SITEMAP = ROOT / 'sitemap.xml'
FRONT = ROOT / 'assets/media/sinjira-fracture-deduction-simplifiee-couverture.webp'
BACK = ROOT / 'assets/media/sinjira-fracture-deduction-simplifiee-dos.webp'
LEGACY = [BASE/'fiche-web.html', BASE/'fiche-joueur.html', BASE/'fiche-solo.html', BASE/'preparer-partie.html']

def read(p):
    return p.read_text('utf-8', errors='ignore') if p.exists() else ''

def main():
    errors=[]
    for p in [INDEX,RULES,WEB,GAMES,SITEMAP,FRONT,BACK,*LEGACY]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        print('\n'.join('- '+e for e in errors)); return 1

    index=read(INDEX); rules=read(RULES); web=read(WEB); games=read(GAMES); sitemap=read(SITEMAP)
    combined=index+'\n'+rules
    required=[
        'Édition Déduction simplifiée','1 à 20 joueurs','14+','30 à 60',
        '90 cartes Opération','20 cartes Identité','2N cartes','10 rondes',
        '6 rondes','+3 points Résistance','+3 points Réseau-Mère',
        'Les sièges invisibles ne créent aucun vote supplémentaire',
        'Fracture instable','sinjira-fracture-deduction-simplifiee-couverture.webp',
        'sinjira-fracture-deduction-simplifiee-dos.webp'
    ]
    for marker in required:
        if marker not in combined: errors.append(f'Marqueur officiel absent: {marker}')

    if 'ajoute exactement 1 carte système par siège' in combined or 'centre contient 3N' in combined:
        errors.append('Ancienne règle 3N/cartes système encore présentée comme officielle.')
    if '+5 Résistance' in combined or '+5 Réseau-Mère' in combined:
        errors.append('Ancien bonus ±5 encore présenté comme officiel.')
    if 'sièges invisibles 2 et 3 sont contrôlés automatiquement' in combined:
        errors.append('Ancien bot Solo/Duo encore présenté comme règle officielle.')
    if 'Mode Web en mise à niveau' not in web or 'temporairement suspendues' not in web:
        errors.append('Le lobby Web incompatible doit rester explicitement suspendu.')
    if 'sinjira-fracture-deduction-simplifiee-couverture.webp' not in games:
        errors.append('La page Jeux doit afficher la nouvelle couverture Fracture.')
    if '/projets/sinjira/jeux/fracture-du-reseau-mere/' not in sitemap:
        errors.append('La page Fracture doit être présente dans le sitemap.')
    for p in LEGACY:
        if 'noindex' not in read(p).lower(): errors.append(f'Page héritée non noindex: {p.name}')

    # Les deux visuels WebP sont volontairement fortement optimisés pour le Web.
    # On vérifie qu'ils contiennent une charge utile réelle sans imposer une taille
    # artificiellement élevée qui pénaliserait la compression.
    if FRONT.stat().st_size < 5_000 or BACK.stat().st_size < 5_000:
        errors.append('Une couverture officielle semble vide ou anormalement petite.')

    if errors:
        print(f'ECHEC Fracture Déduction simplifiée: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK Fracture Déduction simplifiée: règles, couvertures, Solo/Duo, accusation, sitemap et suspension Web cohérents.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
