#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WRAPPER=ROOT/'assets/js/sinjira-admin-console.js'
CORE=ROOT/'assets/js/sinjira-admin-console-core.js'
errors=[]

def need(cond,msg):
    if not cond: errors.append(msg)

need(WRAPPER.exists(),'wrapper admin-console absent')
need(CORE.exists(),'moteur admin-console historique absent')
if WRAPPER.exists():
    js=WRAPPER.read_text('utf-8')
    need("import './sinjira-admin-console-core.js'" in js,'wrapper ne charge pas le moteur admin existant')
    need("Identifiant de projet" in js,'nouveau libellé absent')
    need("Ex. Fracture du Réseau-Mère" in js,'exemple Fracture du Réseau-Mère absent')
    need("slugField.hidden=true" in js,'champ slug technique non masqué')
    need("projectSlug(name.value)" in js,'slug nouveau projet non généré automatiquement')
    need("form.addEventListener('submit'" in js and ',true)' in js,'génération slug non exécutée en phase capture avant le handler historique')
    need("MutationObserver" in js,'liste projets non surveillée pour masquer le slug après rechargement')
if CORE.exists():
    core=CORE.read_text('utf-8')
    need("call('save_project'" in core,'moteur historique save_project absent')
    need("Object.entries(p).forEach" in core,'édition existante ne préserve plus les données du projet')

if errors:
    print(f'ECHEC identifiant projet V24.4.53: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK identifiant projet V24.4.53: nom lisible, slug masqué, génération automatique pour les nouveaux projets et URLs existantes préservées.')
