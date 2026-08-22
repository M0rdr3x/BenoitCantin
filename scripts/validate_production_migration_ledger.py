#!/usr/bin/env python3
from pathlib import Path
import re,subprocess,tempfile,sys

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/'supabase'/'production-migration-ledger.txt'
MIG=ROOT/'supabase'/'migrations'
BUILDER=ROOT/'scripts'/'build_supabase_production_workspace.py'
ROW_RE=re.compile(r'^(\d{14})\s+([a-zA-Z0-9_]+)$')
FILE_RE=re.compile(r'^(\d{14})_(.+)\.sql$')
EXPECTED_COUNT=139
EXPECTED_FIRST='20260809050252'
EXPECTED_LAST='20260822195124'


def rows():
    out=[]
    for i,line in enumerate(LEDGER.read_text('utf-8').splitlines(),1):
        line=line.strip()
        if not line or line.startswith('#'):continue
        m=ROW_RE.fullmatch(line)
        if not m:raise SystemExit(f'Ledger invalide ligne {i}: {line}')
        out.append((m.group(1),m.group(2)))
    return out


def main()->int:
    errors=[]
    r=rows();versions=[x[0] for x in r]
    if len(r)!=EXPECTED_COUNT:errors.append(f'Ledger: {len(r)} versions au lieu de {EXPECTED_COUNT}.')
    if versions!=sorted(versions):errors.append('Ledger non trié.')
    if len(versions)!=len(set(versions)):errors.append('Versions dupliquées dans le ledger.')
    if not versions or versions[0]!=EXPECTED_FIRST:errors.append('Première version production inattendue.')
    if not versions or versions[-1]!=EXPECTED_LAST:errors.append('Dernière version production inattendue.')

    local=[];local_versions=[]
    for p in sorted(MIG.glob('*.sql')):
        m=FILE_RE.fullmatch(p.name)
        if not m:errors.append(f'Nom de migration invalide: {p.name}');continue
        version=m.group(1);local.append((version,p.name));local_versions.append(version)
    if len(local_versions)!=len(set(local_versions)):errors.append('Deux fichiers locaux partagent le même timestamp.')

    cutoff=EXPECTED_LAST
    future=[name for v,name in local if v>cutoff]
    with tempfile.TemporaryDirectory(prefix='sinjira-ledger-') as td:
        out=Path(td)/'supabase'
        p=subprocess.run([sys.executable,str(BUILDER),'--output',str(out)],cwd=ROOT,capture_output=True,text=True)
        if p.returncode:errors.append('Builder workspace en échec: '+(p.stderr or p.stdout).strip())
        else:
            generated=[]
            for f in sorted((out/'migrations').glob('*.sql')):
                m=FILE_RE.fullmatch(f.name)
                if not m:errors.append(f'Fichier workspace invalide: {f.name}');continue
                generated.append((m.group(1),f.name))
            generated_versions=[v for v,_ in generated]
            expected_versions=versions+[v for v,_ in local if v>cutoff]
            if generated_versions!=expected_versions:errors.append('Le workspace lié ne reproduit pas exactement le ledger + migrations futures.')
            for version,name in generated[:len(r)]:
                text=(out/'migrations'/name).read_text('utf-8',errors='ignore')
                if 'Marqueur de déploiement lié uniquement' not in text:errors.append(f'Version déjà appliquée contient du DDL dans le workspace: {name}')
            for name in future:
                if not (out/'migrations'/name).exists():errors.append(f'Migration future absente du workspace: {name}')

    if errors:
        print(f'ECHEC ledger production: {len(errors)} problème(s).')
        for e in errors:print('- '+e)
        return 1
    print(f'OK ledger production: {EXPECTED_COUNT} versions distantes protégées; {len(future)} migration(s) future(s) transmissible(s).')
    return 0

if __name__=='__main__':raise SystemExit(main())
