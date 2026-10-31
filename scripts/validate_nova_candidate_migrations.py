#!/usr/bin/env python3
"""Prévient toute promotion involontaire des migrations Nova sensibles."""
import argparse
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANDIDATES=ROOT/'supabase'/'candidate-migrations'
ACTIVE=ROOT/'supabase'/'migrations'
REVIEWED=ROOT/'supabase'/'production-reviewed-migration-batch.txt'
BUILDER=ROOT/'scripts'/'build_supabase_production_workspace.py'
EXPECTED={
 '20261019170000_nova_adult_opinion_survey_v1.sql':'a1cf3a4ec1011d4ae708b0cd526eb5c9c54f4726',
 '20261019190000_nova_foundations_40_survey_v1.sql':'52edf0a1870bf38e41b16090561c9015eba28cb0',
}
def blob_sha(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode('ascii')+b'\0'+data).hexdigest()

def check(contents,active,reviewed,builder):
    errors=[]
    if set(contents)!=set(EXPECTED):errors.append('Inventaire des migrations candidates incorrect')
    for name,sha in EXPECTED.items():
        if name not in contents or blob_sha(contents[name])!=sha:
            errors.append('Contenu candidat changé sans revue de version: '+name)
        if name in active:errors.append('Candidat actif dans Supabase migrations: '+name)
        if name[:14] in reviewed:errors.append('Candidat dans lot de production revu: '+name)
    if "ignore=shutil.ignore_patterns('migrations', 'candidate-migrations', 'nova-survey-submit', 'nova-consultation40-submit', '.temp')" not in builder:
        errors.append('Builder de production copie peut-être les fichiers candidats')
    return errors

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    contents={p.name:p.read_bytes() for p in CANDIDATES.glob('*.sql')}
    active={p.name for p in ACTIVE.glob('*.sql')}
    reviewed=REVIEWED.read_text('utf-8')
    builder=BUILDER.read_text('utf-8')
    errors=check(contents,active,reviewed,builder)
    if errors:raise SystemExit('\n'.join(errors))
    if args.self_test:
        bad=dict(contents)
        bad['20261019170000_nova_adult_opinion_survey_v1.sql'] += b'--corrupted'
        assert check(bad,active,reviewed,builder)
        assert check(contents,active|{'20261019170000_nova_adult_opinion_survey_v1.sql'},reviewed,builder)
        assert check(contents,active,reviewed+'\n20261019190000',builder)
        assert check(contents,active,reviewed,builder.replace("'candidate-migrations', ",""))
        assert check({},active,reviewed,builder)
        print('OK 5 mutations de garde sur les migrations candidates')
    print('OK 2 migrations Nova candidates figées, hors déploiement et lot production')

if __name__=='__main__':main()
