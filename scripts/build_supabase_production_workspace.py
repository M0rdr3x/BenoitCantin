#!/usr/bin/env python3
from pathlib import Path
import argparse,re,shutil,sys

ROOT=Path(__file__).resolve().parents[1]
SOURCE_SUPABASE=ROOT/'supabase'
LEDGER=SOURCE_SUPABASE/'production-migration-ledger.txt'
MIG_RE=re.compile(r'^(\d{14})_(.+)\.sql$')


def read_ledger():
    rows=[]
    for lineno,line in enumerate(LEDGER.read_text('utf-8').splitlines(),1):
        line=line.strip()
        if not line or line.startswith('#'):continue
        parts=line.split(None,1)
        if len(parts)!=2 or not re.fullmatch(r'\d{14}',parts[0]):
            raise SystemExit(f'Ledger invalide ligne {lineno}: {line}')
        rows.append((parts[0],parts[1].strip()))
    versions=[v for v,_ in rows]
    if versions!=sorted(versions):raise SystemExit('Ledger production non trié.')
    if len(versions)!=len(set(versions)):raise SystemExit('Ledger production avec version dupliquée.')
    if not rows:raise SystemExit('Ledger production vide.')
    return rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    out=Path(args.output).resolve()
    if out==SOURCE_SUPABASE.resolve():raise SystemExit('Refus de modifier supabase/ source.')
    rows=read_ledger(); cutoff=rows[-1][0]
    if out.exists():shutil.rmtree(out)
    shutil.copytree(SOURCE_SUPABASE,out,ignore=shutil.ignore_patterns('migrations','.temp'))
    migout=out/'migrations';migout.mkdir(parents=True,exist_ok=True)

    # Les versions déjà présentes en production deviennent des marqueurs uniquement
    # dans l'espace de déploiement lié. Le SQL de reconstruction reste intact dans le dépôt.
    for version,name in rows:
        (migout/f'{version}_{name}.sql').write_text(
            f'-- Ledger production SINJIRA™ : migration {version}_{name} déjà appliquée.\n'
            '-- Marqueur de déploiement lié uniquement; ne contient volontairement aucun DDL.\n',
            encoding='utf-8'
        )

    future=[]
    for src in sorted((SOURCE_SUPABASE/'migrations').glob('*.sql')):
        m=MIG_RE.match(src.name)
        if not m:raise SystemExit(f'Nom de migration invalide: {src.name}')
        version=m.group(1)
        if version>cutoff:
            dst=migout/src.name
            if dst.exists():raise SystemExit(f'Collision future: {src.name}')
            shutil.copy2(src,dst);future.append(src.name)

    print(f'Workspace Supabase production construit: {len(rows)} version(s) déjà appliquée(s), {len(future)} migration(s) future(s).')
    if future:
        print('Migrations futures:')
        for name in future:print('- '+name)
    return 0

if __name__=='__main__':raise SystemExit(main())
