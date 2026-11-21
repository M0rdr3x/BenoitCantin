#!/usr/bin/env python3
"""Fail-closed : source photo liée au compte avant signature ou purge Storage."""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EDGE=ROOT/'supabase/functions/admin-sinjira-v18/index.ts'
GUARD=ROOT/'supabase/functions/_shared/registry-photo-ownership.mjs'
UPLOADER=ROOT/'supabase/functions/submit-character-questionnaire/index.ts'

REQUIRED_EDGE={
    'admin JWT/AAL2':'await requiredAdmin(req)',
    'import garde photo':"from '../_shared/registry-photo-ownership.mjs'",
    'signature après propriétaire':'if(sub.photo_path&&isCanonicalRegistrySourcePhotoPath(sub.photo_path,sub.user_id))',
    'propriétaire lu par la purge':"select('user_id,photo_path,source_purged_at')",
    'consentement de purge':'b.author_confirmed_source_purge!==true',
    'purge déjà faite':"if(sub.source_purged_at)throw new Error('SOURCE_PURGED')",
    'chemin refusé avant suppression':"if(!isCanonicalRegistrySourcePhotoPath(sub.photo_path,sub.user_id))throw new Error('SOURCE_PURGE_PATH_INVALID');",
    'réponse erreur fixe':"e?.message==='SOURCE_PURGE_PATH_INVALID'",
    'suppression ciblée':'remove([sub.photo_path])',
    'effacement des sources':'source_payload:null,photo_path:null,source_purged_at:new Date().toISOString()',
    'en-tête privé':"'Cache-Control':'private, no-store, max-age=0'",
}
REQUIRED_GUARD={
    'garde exportée':'export function isCanonicalRegistrySourcePhotoPath(raw, userId)',
    'identité typée':"typeof userId !== 'string'",
    'format UUID propriétaire':'[1-5][0-9a-f]{3}',
    'chemin typé':"typeof raw !== 'string'",
    'préfixe propriétaire':'const prefix = ',
    'refus d’autre compte':'!raw.startsWith(prefix)',
    'longueur de photo':'raw.length > prefix.length + 41',
    'UUID de photo v4':'-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',
    'extensions privées':'(?:jpg|png|webp|avif|gif)',
}

def audit(edge,guard,uploader):
    errors=[]
    for name,marker in REQUIRED_EDGE.items():
        if marker not in edge: errors.append('Admin : '+name)
    for name,marker in REQUIRED_GUARD.items():
        if marker not in guard: errors.append('Photo : '+name)
    if 'getPublicUrl(' in edge: errors.append('Lien Storage public interdit')

    start=edge.find("if(a==='list_submissions')")
    guard_pos=edge.find("if(sub.photo_path&&isCanonicalRegistrySourcePhotoPath",start)
    signed=edge.find('createSignedUrl(sub.photo_path,600)',start)
    stop=edge.find("if(a==='create_manual_character')",start)
    if min(start,guard_pos,signed,stop)<0 or not start<guard_pos<signed<stop:
        errors.append('Signer seulement après validation du propriétaire')

    start=edge.find("if(a==='purge_submission_source')")
    confirm=edge.find('b.author_confirmed_source_purge!==true',start)
    owner=edge.find("select('user_id,photo_path,source_purged_at')",start)
    purged=edge.find("if(sub.source_purged_at)",start)
    guard_pos=edge.find("if(!isCanonicalRegistrySourcePhotoPath",start)
    delete=edge.find('remove([sub.photo_path])',start)
    clear=edge.find('source_payload:null,photo_path:null,source_purged_at:',start)
    stop=edge.find("if(a==='list_characters')",start)
    if min(start,confirm,owner,purged,guard_pos,delete,clear,stop)<0 or not (
        start<confirm<owner<purged<guard_pos<delete<clear<stop
    ): errors.append('Purge doit vérifier identité et consentement avant effacement')
    if edge.count('createSignedUrl(sub.photo_path,600)')!=1:
        errors.append('Signer seulement une fois la source vérifiée')
    if edge.count('remove([sub.photo_path])')!=1:
        errors.append('Une suppression ciblée exclusivement')
    if 'function isCanonicalRegistryPhotoPath(raw:unknown,userId:string):boolean' not in uploader:
        errors.append('Garde du questionnaire absente')
    if 'isCanonicalRegistryPhotoPath(photo_path,user.id)' not in uploader:
        errors.append('Validation au compte absente')
    return errors

def self_test(edge,guard,uploader):
    if a:=audit(edge,guard,uploader):
        raise AssertionError('Source saine refusée : '+' ; '.join(a))
    mutations=[
        ('signature sans propriétaire','edge',
         'if(sub.photo_path&&isCanonicalRegistrySourcePhotoPath(sub.photo_path,sub.user_id))',
         'if(sub.photo_path)'),
        ('identité manquante dans purge','edge',
         "select('user_id,photo_path,source_purged_at')","select('photo_path,source_purged_at')"),
        ('contrôle suppression supprimé','edge',
         "if(!isCanonicalRegistrySourcePhotoPath(sub.photo_path,sub.user_id))throw new Error('SOURCE_PURGE_PATH_INVALID');",
         "if(false)throw new Error('SOURCE_PURGE_PATH_INVALID');"),
        ('consentement supprimé','edge',
         "if(b.author_confirmed_source_purge!==true)throw new Error('SOURCE_PURGE_CONFIRMATION_REQUIRED');",
         "if(false)throw new Error('SOURCE_PURGE_CONFIRMATION_REQUIRED');"),
        ('lien signé prolongé','edge','createSignedUrl(sub.photo_path,600)',
         'createSignedUrl(sub.photo_path,86400)'),
        ('suppression arbitraire','edge','remove([sub.photo_path])','remove([b.photo_path])'),
        ('sources non nettoyées','edge',
         'source_payload:null,photo_path:null,source_purged_at:new Date().toISOString()',
         'source_purged_at:new Date().toISOString()'),
        ('cache public','edge',"'Cache-Control':'private, no-store, max-age=0'",
         "'Cache-Control':'public, max-age=3600'"),
        ('comparaison propriétaire absente','guard','!raw.startsWith(prefix)','false'),
        ('identité de propriétaire non typée','guard',"typeof userId !== 'string'",'false'),
        ('chemin sans type','guard',"typeof raw !== 'string'",'false'),
        ('extension pdf acceptée','guard','(?:jpg|png|webp|avif|gif)',
         '(?:jpg|png|webp|avif|gif|pdf)'),
        ('chemin illimité','guard','raw.length > prefix.length + 41','false'),
        ('validateur upload supprimé','uploader',
         'isCanonicalRegistryPhotoPath(photo_path,user.id)','true'),
    ]
    for label,part,old,new in mutations:
        src={'edge':edge,'guard':guard,'uploader':uploader}[part]
        if src.count(old)!=1:
            raise AssertionError(f'Mutation impossible {label} : {src.count(old)}')
        altered=src.replace(old,new,1)
        e=altered if part=='edge' else edge
        g=altered if part=='guard' else guard
        u=altered if part=='uploader' else uploader
        if not audit(e,g,u): raise AssertionError('Régression indétectée : '+label)
    print(f'OK : {len(mutations)} mutations de signature et purge détectées')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    e=EDGE.read_text('utf-8')
    g=GUARD.read_text('utf-8')
    u=UPLOADER.read_text('utf-8')
    if args.self_test:self_test(e,g,u)
    errors=audit(e,g,u)
    if errors:
        for error in errors:print('ÉCHEC : '+error)
        return 1
    print('OK : propriétaire exact avant signature et purge ; aucun chemin étranger')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
