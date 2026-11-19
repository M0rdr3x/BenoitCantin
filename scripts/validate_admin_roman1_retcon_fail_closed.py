#!/usr/bin/env python3
"""Contrat fail-closed du verrou Roman I dans l'Edge admin-sinjira-v18.

Le test Node exécute en complément la vraie branche save_character sur des
réponses SQL simulées. Les mutations ci-dessous détectent un retour fail-open.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGE = ROOT / 'supabase/functions/admin-sinjira-v18/index.ts'

REQUIRED = {
    'JWT/admin/AAL2': 'await requiredAdmin(req)',
    'borne JSON': 'readBoundedJson(req)',
    'réponse privée': "'Cache-Control':'private, no-store, max-age=0'",
    'vérification identifiant UUID': "const NOVEL_UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;",
    'type et format UUID': "if(typeof c.novel_id!=='string'||!NOVEL_UUID_RE.test(c.novel_id))throw new Error('NOVEL_ID_INVALID');",
    'SQL renvoie erreur': "const {data:novel,error:novelError}=await s.from('novels').select('slug').eq('id',c.novel_id).maybeSingle();",
    'erreur SQL fail-closed': "if(novelError)throw new Error('NOVEL_LOOKUP_UNAVAILABLE');",
    'ligne vide fail-closed': "if(!novel||typeof novel.slug!=='string'||!novel.slug.trim())throw new Error('NOVEL_NOT_FOUND');",
    'identifiant du personnage valide': "if(typeof c.id!=='string'||!NOVEL_UUID_RE.test(c.id))throw new Error('CHARACTER_ID_INVALID');",
    'lecture de la fiche en base': "const {data:current,error:currentError}=await s.from('characters')",
    'jointure du roman actuel': ".select('id,novel_id,novels(slug)').eq('id',c.id).maybeSingle();",
    'erreur lecture fiche bloquée': "if(currentError)throw new Error('CHARACTER_LOOKUP_UNAVAILABLE');",
    'fiche absente bloquée': "if(!current||current.id!==c.id)throw new Error('CHARACTER_NOT_FOUND');",
    'slug précédent non vide': "if(typeof current.novels?.slug!=='string'||!current.novels.slug.trim())throw new Error('CHARACTER_NOVEL_UNAVAILABLE');",
    'verrou du roman de départ': "if(current.novels.slug==='la-cendre-du-jugement'&&c.author_confirmed_retcon!==true)throw new Error('ROMAN1_LOCKED');",
    'mise à jour conditionnelle': "const updateQuery=s.from('characters').update(payload).eq('id',c.id);",
    'valeur ancienne vérifiée': "?updateQuery.eq('novel_id',current.novel_id)",
    'absence ancienne vérifiée': ":updateQuery.is('novel_id',null);",
    'conflit doit refuser': "if(!data)throw new Error('CHARACTER_CHANGED');",
    'réponse lecture 503': "code:'CHARACTER_LOOKUP_UNAVAILABLE'},503)",
    'réponse conflit 409': "code:'CHARACTER_CHANGED'},409)",
    'réponse introuvable 404': "code:'CHARACTER_NOT_FOUND'},404)",
    'verrou Roman I humain': "if(novel?.slug==='la-cendre-du-jugement'&&c.author_confirmed_retcon!==true)throw new Error('ROMAN1_LOCKED');",
    'verrou CANON indépendant': "canonStatus==='CANON'&&c.author_confirmed_canon!==true",
    'modification persistée': "s.from('characters').update(payload)",
    'réponse 503 pour panne SQL': "e?.message==='NOVEL_LOOKUP_UNAVAILABLE'",
    'statut 503 sans changement': "code:'NOVEL_LOOKUP_UNAVAILABLE'},503)",
    'identifiant invalide en 400': "code:'NOVEL_ID_INVALID'},400)",
    'roman introuvable en 400': "code:'NOVEL_NOT_FOUND'},400)",
    'mots de passe / erreurs non divulgués': "adminV18LogCode(e)",
    'log allowlistée': "SAFE_LOG_CODES.has(code)",
}
FORBIDDEN = (
    "const {data:novel}=await s.from('novels')",
    "if(novelError){}",
    "console.error('[admin-sinjira-v18]',novelError)",
    "error:novelError.message",
    "error:novelError?.message",
    "error:currentError.message",
    "error:currentError?.message",
)


def audit(source: str) -> list[str]:
    errors: list[str] = []
    for label, marker in REQUIRED.items():
        if marker not in source:
            errors.append('Roman I : garde absent/affaibli : ' + label)
    for marker in FORBIDDEN:
        if marker in source:
            errors.append('Roman I : fail-open ou fuite : ' + marker)

    begin = source.find("if(a==='save_character')")
    canon = source.find("if(canonStatus==='CANON'&&", begin)
    novel = source.find("if(c.novel_id){", begin)
    id_check = source.find("if(typeof c.novel_id!=='string'", novel)
    rpc = source.find("const {data:novel,error:novelError}=await", novel)
    fail_sql = source.find("if(novelError)throw new Error('NOVEL_LOOKUP_UNAVAILABLE');", rpc)
    fail_empty = source.find("if(!novel||typeof novel.slug!=='string'||!novel.slug.trim())", rpc)
    retcon = source.find("if(novel?.slug==='la-cendre-du-jugement'", rpc)
    current_id = source.find("if(typeof c.id!=='string'", retcon)
    current_read = source.find("const {data:current,error:currentError}=await s.from('characters')", current_id)
    current_error = source.find("if(currentError)throw new Error('CHARACTER_LOOKUP_UNAVAILABLE');", current_read)
    current_absent = source.find("if(!current||current.id!==c.id)", current_read)
    current_slug = source.find("if(typeof current.novels?.slug!=='string'", current_read)
    source_retcon = source.find("if(current.novels.slug==='la-cendre-du-jugement'", current_read)
    payload = source.find("const payload=", novel)
    write = source.find("s.from('characters').update(payload)", payload)
    cas_eq = source.find("?updateQuery.eq('novel_id',current.novel_id)", write)
    cas_null = source.find(":updateQuery.is('novel_id',null);", cas_eq)
    result = source.find("await guardedUpdate.select('*').maybeSingle()", cas_null)
    stale = source.find("if(!data)throw new Error('CHARACTER_CHANGED');", result)
    audit_pos = source.find("await audit(s,user.id,'save_character'", stale)
    tail = source.find("return privateJson({ok:false,error:'Action inconnue.'", begin)
    if min(begin,canon,novel,id_check,rpc,fail_sql,fail_empty,retcon,
           current_id,current_read,current_error,current_absent,current_slug,source_retcon,
           payload,write,cas_eq,cas_null,result,stale,audit_pos,tail) < 0 or not (
        begin < canon < novel < id_check < rpc < fail_sql < fail_empty < retcon <
        current_id < current_read < current_error < current_absent <
        current_slug < source_retcon < payload < write < cas_eq <
        cas_null < result < stale < audit_pos < tail
    ):
        errors.append('Roman I : roman cible et source validés avant UPDATE conditionnel, conflit avant audit')
    if source.count('NOVEL_UUID_RE.test(c.novel_id)') != 1:
        errors.append('Roman I : validation identifiant non unique')
    if source.count("novel?.slug==='la-cendre-du-jugement'&&c.author_confirmed_retcon!==true") != 1:
        errors.append('Roman I : verrou retcon non unique')
    if source.count("if(novelError)throw new Error('NOVEL_LOOKUP_UNAVAILABLE');") != 1:
        errors.append('Roman I : erreur SQL non vérifiée exactement une fois')
    return errors


def self_test(source: str) -> None:
    if errors := audit(source):
        raise AssertionError('Le code réel sain doit passer : ' + ' | '.join(errors))
    mutations = [
        ('résultat SQL sans error', "const {data:novel,error:novelError}=await", "const {data:novel}=await"),
        ('erreur SQL ignorée', "if(novelError)throw new Error('NOVEL_LOOKUP_UNAVAILABLE');", "if(novelError){}"),
        ('roman absent accepté', "if(!novel||typeof novel.slug!=='string'||!novel.slug.trim())throw new Error('NOVEL_NOT_FOUND');", ""),
        ('roman I cible sans accord', "if(novel?.slug==='la-cendre-du-jugement'&&c.author_confirmed_retcon!==true)throw new Error('ROMAN1_LOCKED');", ""),
        ('validation UUID retirée', "if(typeof c.novel_id!=='string'||!NOVEL_UUID_RE.test(c.novel_id))throw new Error('NOVEL_ID_INVALID');", ""),
        ('erreur SQL après écriture', "if(novelError)throw new Error('NOVEL_LOOKUP_UNAVAILABLE');",
         "if(false)throw new Error('NOVEL_LOOKUP_UNAVAILABLE');"),
        ('UUID autorisé sans contrainte', "const NOVEL_UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;",
         "const NOVEL_UUID_RE=/.*/;"),
        ('MFA remplacée', "const {user,service:s}=await requiredAdmin(req);",
         "const user=await requiredUser(req),s=serviceClient();"),
        ('réponse SQL 200', "code:'NOVEL_LOOKUP_UNAVAILABLE'},503)",
         "code:'NOVEL_LOOKUP_UNAVAILABLE'},200)"),
        ('réponse SQL brute', "code:'NOVEL_LOOKUP_UNAVAILABLE'},503)",
         "error:novelError.message,code:'NOVEL_LOOKUP_UNAVAILABLE'},503)"),
        ('cache public', "'Cache-Control':'private, no-store, max-age=0'",
         "'Cache-Control':'public,max-age=3600'"),
        ('CANON automatique', "&&c.author_confirmed_canon!==true", ""),
        ('ID personnage sans validation',
         "if(typeof c.id!=='string'||!NOVEL_UUID_RE.test(c.id))throw new Error('CHARACTER_ID_INVALID');", ""),
        ('lecture de la fiche ignorée',
         "const {data:current,error:currentError}=await s.from('characters')",
         "const {data:current,error:currentError}=await s.from('novels')"),
        ('erreur lecture personnage ignorée',
         "if(currentError)throw new Error('CHARACTER_LOOKUP_UNAVAILABLE');", "if(currentError){}"),
        ('fiche absente acceptée',
         "if(!current||current.id!==c.id)throw new Error('CHARACTER_NOT_FOUND');", ""),
        ('slug du roman source inconnu toléré',
         "if(typeof current.novels?.slug!=='string'||!current.novels.slug.trim())throw new Error('CHARACTER_NOVEL_UNAVAILABLE');", ""),
        ('sortie du Roman I sans accord',
         "if(current.novels.slug==='la-cendre-du-jugement'&&c.author_confirmed_retcon!==true)throw new Error('ROMAN1_LOCKED');", ""),
        ('UPDATE ne vérifie plus ancien roman',
         "?updateQuery.eq('novel_id',current.novel_id)", "?updateQuery.eq('id',c.id)"),
        ('UPDATE ne vérifie plus null courant',
         ":updateQuery.is('novel_id',null);", ":updateQuery.is('deleted_at',null);"),
        ('conflit concurrent accepté',
         "if(!data)throw new Error('CHARACTER_CHANGED');", "if(false)throw new Error('CHARACTER_CHANGED');"),
        ('conflit envoyé en 200',
         "code:'CHARACTER_CHANGED'},409)", "code:'CHARACTER_CHANGED'},200)"),
        ('erreur de base divulguée',
         "code:'CHARACTER_LOOKUP_UNAVAILABLE'},503)", "error:currentError.message,code:'CHARACTER_LOOKUP_UNAVAILABLE'},503)"),
        ('slug cible vide toléré',
         "if(!novel||typeof novel.slug!=='string'||!novel.slug.trim())throw new Error('NOVEL_NOT_FOUND');",
         "if(!novel||typeof novel.slug!=='string')throw new Error('NOVEL_NOT_FOUND');"),

    ]
    for label, original, altered in mutations:
        count = source.count(original)
        if count != 1:
            raise AssertionError(f'Mutation non définie {label} : marqueurs {count}')
        if not audit(source.replace(original, altered, 1)):
            raise AssertionError('Affaiblissement non détecté : '+label)
    print(f'OK auto-test Roman I : {len(mutations)} régressions de verrou détectées.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    source = EDGE.read_text('utf-8')
    if args.self_test:
        self_test(source)
    errors = audit(source)
    if errors:
        print('ÉCHEC sécurité du Roman I : ' + str(len(errors)) + ' problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK Roman I : validité UUID, lecture SQL confirmée, retcon humain, aucune écriture fail-open.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
