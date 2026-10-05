#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
DOWNLOAD=ROOT/'supabase/functions/get-private-book-url/index.ts'
READER=ROOT/'supabase/functions/get-private-book-reading-url/index.ts'
HELPER=ROOT/'supabase/functions/_shared/privateBook.ts'
CONFIG=ROOT/'supabase/config.toml'


def require(errors:list[str],condition:bool,message:str)->None:
    if not condition: errors.append(message)


def stanza(config:str,name:str)->str:
    marker=f'[functions.{name}]'
    if marker not in config:return ''
    return config.split(marker,1)[1].split('[functions.',1)[0]


def validate_text(download:str,reader:str,helper:str,config:str)->list[str]:
    errors:list[str]=[]

    helper_required=(
        "LIVRE_I_PRODUCT_SLUG='sinjira-livre-01-la-cendre-du-jugement'",
        'LIVRE_I_SIGNED_URL_SECONDS=300',
        "Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED')==='true'",
        "Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_BUCKET')",
        "Deno.env.get('SINJIRA_LIVRE_I_PRIVATE_PATH')",
        "service.rpc('is_sinjira_owner',{p_user_id:userId})",
        "if(isOwner===true)return 'owner'",
        "service.rpc(\n    'sinjira_has_full_catalog_access'",
        "if(fullCatalog===true)return 'family'",
        "service.rpc(\n    'has_sinjira_product'",
        "{p_product_slug:LIVRE_I_PRODUCT_SLUG,p_user_id:userId}",
        "if(hasProduct===true)return 'product'",
        "throw new Error('BOOK_ACCESS_DENIED')",
    )
    for marker in helper_required:
        require(errors,marker in helper,f'Helper Livre I absent: {marker}')

    owner_pos=helper.find("service.rpc('is_sinjira_owner'")
    owner_allow_pos=helper.find("if(isOwner===true)return 'owner'")
    family_pos=helper.find("'sinjira_has_full_catalog_access'")
    family_allow_pos=helper.find("if(fullCatalog===true)return 'family'")
    product_pos=helper.find("'has_sinjira_product'")
    product_allow_pos=helper.find("if(hasProduct===true)return 'product'")
    require(errors,0<=owner_pos<owner_allow_pos<family_pos<family_allow_pos<product_pos<product_allow_pos,
            'Ordre attendu: owner serveur -> catalogue famille -> droit produit canonique.')

    for forbidden in ('getPublicUrl(', 'external_url', 'clientRole', 'is_owner_from_client', ".from('products')", ".from('user_entitlements')"):
        require(errors,forbidden not in helper,f'Helper Livre I interdit: {forbidden}')
    for mutation in ('.insert(', '.update(', '.upsert(', '.delete('):
        require(errors,mutation not in helper,f'Helper Livre I ne doit jamais muter un droit ou un rôle: {mutation}')

    for name,source in (('download',download),('reader',reader)):
        for marker in (
            "req.method!=='POST'",
            'const user=await requiredUser(req);',
            'const service=serviceClient();',
            "service.rpc('sinjira_age_band',{p_user_id:user.id})",
            "if(normalizedAgeBand==='child')",
            "if(!['adult','youth'].includes(normalizedAgeBand))",
            'await requirePrivateBookAccess(service,user.id);',
            'const storage=privateBookStorageConfig();',
            "'Cache-Control':'private, no-store, max-age=0'",
            "'Pragma':'no-cache'",
            "'X-Content-Type-Options':'nosniff'",
            "'Referrer-Policy':'no-referrer'",
            '.createSignedUrl(storage.storagePath,LIVRE_I_SIGNED_URL_SECONDS',
        ):
            require(errors,marker in source,f'{name}: garde absent: {marker}')
        auth=source.find('const user=await requiredUser(req);')
        service=source.find('const service=serviceClient();')
        age=source.find("service.rpc('sinjira_age_band',{p_user_id:user.id})")
        child_block=source.find("if(normalizedAgeBand==='child')")
        access=source.find('await requirePrivateBookAccess(service,user.id);')
        storage=source.find('const storage=privateBookStorageConfig();')
        signed=source.find('.createSignedUrl(storage.storagePath,LIVRE_I_SIGNED_URL_SECONDS')
        require(errors,0<=auth<service<age<child_block<access<storage<signed,
                f'{name}: ordre auth -> âge -> autorisation -> stockage -> URL signée invalide')
        require(errors,'getPublicUrl(' not in source and 'external_url' not in source,
                f'{name}: aucun repli public/externe permis')
        require(errors,"console.error(error)" not in source and 'console.error(signedError)' not in source,
                f'{name}: les erreurs brutes ne doivent pas être journalisées')

    require(errors,"{download:'SINJIRA_Livre_01_La_Cendre_du_Jugement.pdf'}" in download,
            'Téléchargement: Content-Disposition privé attendu via option download.')
    require(errors,"{download:" not in reader and "download:'" not in reader,
            'Lecteur: l’URL signée ne doit pas forcer un téléchargement.')
    require(errors,"BOOK_ACCESS_DENIED" in download and "BOOK_ACCESS_DENIED" in reader,
            'Les deux portes doivent refuser explicitement un compte non autorisé.')

    expected_logs={
        'download':[
            "console.error('[get-private-book-url]',{code:'BOOK_SIGNED_URL_FAILED'});",
            "console.error('[get-private-book-url]',{code:'BOOK_ACCESS_CHECK_FAILED'});",
            "console.error('[get-private-book-url]',{code:'BOOK_PRIVATE_STORAGE_NOT_CONFIGURED'});",
            "console.error('[get-private-book-url]',{code:'BOOK_PRIVATE_DELIVERY_FAILED'});",
        ],
        'reader':[
            "console.error('[get-private-book-reading-url]',{code:'BOOK_READER_SIGNED_URL_FAILED'});",
            "console.error('[get-private-book-reading-url]',{code:'BOOK_READER_ACCESS_CHECK_FAILED'});",
            "console.error('[get-private-book-reading-url]',{code:'BOOK_READER_STORAGE_NOT_CONFIGURED'});",
            "console.error('[get-private-book-reading-url]',{code:'BOOK_READER_FAILED'});",
        ],
    }
    for name,source in (('download',download),('reader',reader)):
        console_lines=[line.strip() for line in source.splitlines() if 'console.' in line]
        require(errors,console_lines==expected_logs[name],f'{name}: logs fixes approuvés requis')

    for function_name in ('get-private-book-url','get-private-book-reading-url'):
        current=stanza(config,function_name)
        require(errors,bool(current),f'Stanza {function_name} absente')
        require(errors,'verify_jwt = true' in current,f'{function_name}: verify_jwt=true requis')
        require(errors,'verify_jwt = false' not in current,f'{function_name}: verify_jwt=false interdit')
    return errors


def validate(download_path:Path=DOWNLOAD,reader_path:Path=READER,helper_path:Path=HELPER,config_path:Path=CONFIG)->list[str]:
    try:
        return validate_text(
            download_path.read_text('utf-8',errors='strict'),reader_path.read_text('utf-8',errors='strict'),
            helper_path.read_text('utf-8',errors='strict'),config_path.read_text('utf-8',errors='strict'))
    except OSError as exc:return [f'Frontière Livre I illisible: {exc}']


def self_test()->None:
    values=(DOWNLOAD.read_text('utf-8'),READER.read_text('utf-8'),HELPER.read_text('utf-8'),CONFIG.read_text('utf-8'))
    if (baseline:=validate_text(*values)):
        raise AssertionError('Le cas réel sain doit passer: '+' | '.join(baseline))
    download,reader,helper,config=values
    reader_storage_before_access=reader.replace(
        "    await requirePrivateBookAccess(service,user.id);\n\n    // L'état de la livraison privée n'est révélé qu'à un compte déjà autorisé.\n    const storage=privateBookStorageConfig();",
        "    const storage=privateBookStorageConfig();\n    await requirePrivateBookAccess(service,user.id);",
        1,
    )
    owner_block="""  const {data:isOwner,error:ownerError}=await service.rpc('is_sinjira_owner',{p_user_id:userId});
  if(ownerError)throw new Error('BOOK_ACCESS_CHECK_FAILED');
  if(isOwner===true)return 'owner';

"""
    helper_owner_after_product=helper.replace(owner_block,'',1).replace(
        "  const {data:hasProduct,error:productAccessError}=await service.rpc(\n",
        owner_block+"  const {data:hasProduct,error:productAccessError}=await service.rpc(\n",
        1,
    )
    mutations=[
        ('auth téléchargement retirée',download.replace('const user=await requiredUser(req);',"const user={id:'bypass'};",1),reader,helper,config),
        ('auth lecteur retirée',download,reader.replace('const user=await requiredUser(req);',"const user={id:'bypass'};",1),helper,config),
        ('autorisation lecteur retirée',download,reader.replace('await requirePrivateBookAccess(service,user.id);','',1),helper,config),
        ('stockage révélé avant autorisation',download,reader_storage_before_access,helper,config),
        ('auteur dépend du produit commercial',download,reader,helper_owner_after_product,config),
        ('catalogue famille retiré',download,reader,helper.replace("'sinjira_has_full_catalog_access'","'catalog_access_missing'",1),config),
        ('droit produit canonique retiré',download,reader,helper.replace("'has_sinjira_product'","'product_access_missing'",1),config),
        ('droit produit truthy permissif',download,reader,helper.replace("if(hasProduct===true)return 'product'","if(hasProduct)return 'product'",1),config),
        ('retour lecture directe entitlements',download,reader,helper+"\nservice.from('user_entitlements').select('*');\n",config),
        ('âge child téléchargement retiré',download.replace("if(normalizedAgeBand==='child')throw new Error('BOOK_NOT_AVAILABLE_11_12');","",1),reader,helper,config),
        ('âge child lecteur retiré',download,reader.replace("if(normalizedAgeBand==='child')throw new Error('BOOK_NOT_AVAILABLE_11_12');","",1),helper,config),
        ('owner serveur retiré',download,reader,helper.replace("  const {data:isOwner,error:ownerError}=await service.rpc('is_sinjira_owner',{p_user_id:userId});\n",'',1),config),
        ('TTL élargi',download,reader,helper.replace('LIVRE_I_SIGNED_URL_SECONDS=300','LIVRE_I_SIGNED_URL_SECONDS=3600',1),config),
        ('mutation entitlement ajoutée',download,reader,helper+"\nservice.from('user_entitlements').insert({});\n",config),
        ('repli public',download,reader,helper+"\nservice.storage.from('x').getPublicUrl('x');\n",config),
        ('reader force download',download,reader.replace('LIVRE_I_SIGNED_URL_SECONDS);',"LIVRE_I_SIGNED_URL_SECONDS,{download:'x.pdf'});",1),helper,config),
        ('jwt reader désactivé',download,reader,helper,config.replace('[functions.get-private-book-reading-url]\nverify_jwt = true','[functions.get-private-book-reading-url]\nverify_jwt = false',1)),
        ('jwt download désactivé',download,reader,helper,config.replace('[functions.get-private-book-url]\nverify_jwt = true','[functions.get-private-book-url]\nverify_jwt = false',1)),
    ]
    with TemporaryDirectory() as raw:
        root=Path(raw);d=root/'download.ts';r=root/'reader.ts';h=root/'helper.ts';c=root/'config.toml'
        for label,md,mr,mh,mc in mutations:
            d.write_text(md,encoding='utf-8');r.write_text(mr,encoding='utf-8');h.write_text(mh,encoding='utf-8');c.write_text(mc,encoding='utf-8')
            if not validate(d,r,h,c):raise AssertionError(f'Régression non détectée: {label}')
    print(f'OK auto-tests Livre I privé: {len(mutations)} affaiblissements critiques détectés.')


def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:self_test();return 0
    errors=validate()
    if errors:
        print(f'ÉCHEC Livre I privé: {len(errors)} problème(s).');[print('- '+e) for e in errors];return 1
    print('OK Livre I privé: owner/famille V25/droit produit canonique; âge vérifié avant autorisation; stockage privé après contrôle; URLs signées 300 s.')
    return 0

if __name__=='__main__':raise SystemExit(main())
