#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HISTORICAL=ROOT/'supabase/migrations/20260818022036_sinjira_v24_4_58_owner_book2_title_consistency.sql'
FIREWALL=ROOT/'supabase/migrations/20260820224802_sinjira_v24_4_89_private_handle_runtime_decoupling.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
errors=[]


def need(condition,message):
    if not condition:errors.append(message)

need(HISTORICAL.exists(),'migration historique V24.4.58 absente')
need(FIREWALL.exists(),'migration V24.4.89 de séparation absente')
if HISTORICAL.exists():
    low=HISTORICAL.read_text('utf-8',errors='ignore').lower()
    need('sinjira — livre ii : le sang du sauveur' in low,'titre historique Livre II absent de V24.4.58')
if FIREWALL.exists():
    low=FIREWALL.read_text('utf-8',errors='ignore').lower().replace(' ','').replace('\n','')
    need("public_name='sethtremblay'" in low,'Seth Tremblay absent de la routine propriétaire actuelle')
    need('novel_id=null' in low and 'novel_note=null' in low,'Seth reste rattaché automatiquement à un roman')
    need("'identity_scope','parallel_world'" in low,'Seth n’est pas classé comme identité du Monde parallèle')
need(LEDGER.exists(),'ledger production absent')
if LEDGER.exists():
    ledger=LEDGER.read_text('utf-8')
    need('20260818022036 sinjira_v24_4_58_owner_book2_title_consistency' in ledger,'historique V24.4.58 absent du ledger')
    need('20260820224802 sinjira_v24_4_89_private_handle_runtime_decoupling' in ledger,'V24.4.89 absent du ledger')

if errors:
    print(f'ECHEC séparation personnage/Livre II: {len(errors)} problème(s).')
    for e in errors:print('- '+e)
    raise SystemExit(1)

print('OK: V24.4.58 reste dans l’historique, mais V24.4.89 sépare désormais l’identité du Monde parallèle de l’affectation automatique au Livre II.')
