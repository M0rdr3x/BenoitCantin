#!/usr/bin/env python3
from __future__ import annotations

import argparse,hashlib,json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'projets/sinjira/codex/livre-i-delivery-contract.json'
DOWNLOAD=ROOT/'supabase/functions/get-private-book-url/index.ts'
READER=ROOT/'supabase/functions/get-private-book-reading-url/index.ts'
HELPER=ROOT/'supabase/functions/_shared/privateBook.ts'
CONFIG=ROOT/'supabase/config.toml'
GENERIC_EDGE=ROOT/'supabase/functions/get-document-url/index.ts'
FULL_BASENAME='SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf'
FULL_SHA256='9862a11000fe46a2010e7fb902b9bba3dfea70724855a6fb682e0a6192df88e3'
DEMO_BASENAME='SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf'
DEMO_SHA256='aad491ce8861928c561caa035fe5ee8cb16d42a8e307c93828758346cc93f26f'
PRODUCT_SLUG='sinjira-livre-01-la-cendre-du-jugement'
STATIC_EXTENSIONS={'.html','.js','.mjs','.css','.json','.xml','.webmanifest','.txt'}
SKIP_PARTS={'codex','.git','node_modules'}


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def iter_static_text_files(root:Path):
    for candidate in (root/'projets/sinjira',root/'assets',root/'sitemap.xml',root/'robots.txt',root/'manifest.webmanifest'):
        if not candidate.exists():continue
        paths=(candidate,) if candidate.is_file() else candidate.rglob('*')
        for path in paths:
            if not path.is_file() or (candidate.is_dir() and path.suffix.lower() not in STATIC_EXTENSIONS):continue
            rel=path.relative_to(root)
            if any(part in SKIP_PARTS for part in rel.parts):continue
            yield path


def validate(root:Path=ROOT)->list[str]:
    errors=[]
    try:contract=json.loads((root/'projets/sinjira/codex/livre-i-delivery-contract.json').read_text('utf-8'))
    except Exception as exc:return [f'Contrat Livre I illisible: {exc}']

    expected={
        ('schema',):'sinjira.livre-i.delivery.v2',
        ('publication_state',):'prepared_not_deployed',
        ('human_gate_required',):True,
        ('demo','pages'):83,('demo','sha256'):DEMO_SHA256,
        ('full_edition','pages'):1066,('full_edition','sha256'):FULL_SHA256,
        ('full_edition','public_repository_allowed'):False,
        ('full_edition','public_static_url_allowed'):False,
        ('full_edition','delivery'):'authenticated_private_storage_only',
        ('full_edition','download_endpoint'):'get-private-book-url',
        ('full_edition','reader_endpoint'):'get-private-book-reading-url',
        ('full_edition','reader_page'):'/projets/sinjira/romans/lire-integral.html',
        ('full_edition','entitlement_table'):'user_entitlements',
        ('full_edition','entitlement_client_mutation_allowed'):False,
        ('full_edition','entitlement_anonymous_read_allowed'):False,
        ('full_edition','product_slug'):PRODUCT_SLUG,
        ('full_edition','owner_role_creates_entitlement'):False,
        ('full_edition','client_role_assertion_allowed'):False,
        ('full_edition','activation_env'):'SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED',
        ('full_edition','signed_url_seconds'):300,
        ('full_edition','signed_url_max_seconds'):600,
        ('full_edition','reader_signed_url_refresh'):True,
        ('full_edition','reader_progress_storage'):'local_device_only',
        ('full_edition','activation_requires_explicit_human_decision'):True,
        ('full_edition','production_deployment_authorized'):False,
    }
    for keys,value in expected.items():
        current=contract
        try:
            for key in keys:current=current[key]
        except (KeyError,TypeError):errors.append('Contrat Livre I incomplet: '+'.'.join(keys));continue
        if current!=value:errors.append(f"Contrat Livre I inattendu pour {'.'.join(keys)}: {current!r} != {value!r}")
    access=contract.get('full_edition',{}).get('access_sources',[])
    if access!=['active_product_entitlement','server_verified_owner_role']:
        errors.append('Les sources d’accès doivent rester entitlement produit + rôle propriétaire vérifié serveur.')
    if not str(contract.get('demo',{}).get('public_url','')).endswith('/projets/sinjira/documents/'+DEMO_BASENAME):
        errors.append("L'URL publique stable de la démo n'est plus celle attendue.")

    for path in root.rglob(FULL_BASENAME):
        if path.is_file() and '.git' not in path.parts:errors.append(f'Édition intégrale interdite dans le dépôt public: {path.relative_to(root)}')
    for pdf in root.rglob('*.pdf'):
        if '.git' in pdf.parts or not pdf.is_file():continue
        try:digest=sha256_file(pdf)
        except OSError:continue
        if digest==FULL_SHA256:errors.append(f'Octets de l’édition intégrale détectés dans le dépôt public: {pdf.relative_to(root)}')
    for path in iter_static_text_files(root):
        try:text=path.read_text('utf-8')
        except (OSError,UnicodeDecodeError):continue
        rel=path.relative_to(root)
        if FULL_BASENAME in text:errors.append(f'Lien/référence statique vers l’intégrale détecté: {rel}')
        if FULL_SHA256 in text:errors.append(f'Empreinte de l’intégrale injectée dans un actif public: {rel}')

    files={
        'download':root/'supabase/functions/get-private-book-url/index.ts',
        'reader':root/'supabase/functions/get-private-book-reading-url/index.ts',
        'helper':root/'supabase/functions/_shared/privateBook.ts',
        'config':root/'supabase/config.toml',
        'generic':root/'supabase/functions/get-document-url/index.ts',
    }
    try:texts={name:path.read_text('utf-8') for name,path in files.items()}
    except OSError as exc:return errors+[f'Frontière privée illisible: {exc}']
    for name in ('download','reader'):
        source=texts[name]
        for marker in ('requiredUser(req)','privateBookStorageConfig()','requirePrivateBookAccess(service,user.id)',"'Cache-Control':'private, no-store, max-age=0'",'.createSignedUrl(storage.storagePath,LIVRE_I_SIGNED_URL_SECONDS'):
            if marker not in source:errors.append(f'{name}: garde privée absente: {marker}')
        if 'getPublicUrl(' in source or 'external_url' in source:errors.append(f'{name}: repli public/externe interdit')
    helper=texts['helper']
    for marker in (".from('user_entitlements')",".eq('user_id',userId)","service.rpc('is_sinjira_owner',{p_user_id:userId})","if(isOwner===true)return 'owner'","LIVRE_I_SIGNED_URL_SECONDS=300"):
        if marker not in helper:errors.append(f'helper: garde d’autorisation absente: {marker}')
    if 'getPublicUrl(' in helper:errors.append('helper: stockage public interdit')
    if "{download:" in texts['reader']:errors.append('Le lecteur ne doit pas forcer le téléchargement du PDF.')
    if "{download:'SINJIRA_Livre_01_La_Cendre_du_Jugement.pdf'}" not in texts['download']:errors.append('Le téléchargement doit rester explicitement attaché.')
    for function_name in ('get-private-book-url','get-private-book-reading-url'):
        marker=f'[functions.{function_name}]\nverify_jwt = true'
        if marker not in texts['config']:errors.append(f'{function_name}: verify_jwt=true requis dans config.toml')
    if 'getPublicUrl(' in texts['generic']:errors.append('get-document-url ne doit jamais produire une URL publique de Storage.')
    return errors


def self_test()->None:
    clean=validate(ROOT)
    if clean:raise AssertionError('Le cas réel sain doit passer: '+' | '.join(clean))
    with TemporaryDirectory() as raw:
        root=Path(raw)
        # Copie minimale des surfaces surveillées.
        for rel in ('projets/sinjira/codex/livre-i-delivery-contract.json','supabase/functions/get-private-book-url/index.ts','supabase/functions/get-private-book-reading-url/index.ts','supabase/functions/_shared/privateBook.ts','supabase/functions/get-document-url/index.ts','supabase/config.toml'):
            src=ROOT/rel;dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
        (root/'projets/sinjira/documents').mkdir(parents=True,exist_ok=True)
        leaked=root/'projets/sinjira/documents'/FULL_BASENAME;leaked.write_bytes(b'not-real-pdf')
        if not any('Édition intégrale interdite' in e for e in validate(root)):raise AssertionError('Nom intégral public non détecté')
        leaked.unlink()
        public=root/'projets/sinjira/index.html';public.parent.mkdir(parents=True,exist_ok=True);public.write_text(f'<a href="{FULL_BASENAME}">x</a>',encoding='utf-8')
        if not any('référence statique' in e for e in validate(root)):raise AssertionError('Lien statique intégral non détecté')
        public.unlink()
        helper=root/'supabase/functions/_shared/privateBook.ts';helper.write_text(helper.read_text('utf-8')+'\ngetPublicUrl("x");\n',encoding='utf-8')
        if not any('stockage public' in e for e in validate(root)):raise AssertionError('Repli public non détecté')
    print('OK auto-test frontière Livre I V2.')


def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:self_test();return 0
    errors=validate()
    if errors:
        print('ÉCHEC frontière Livre I:');[print('- '+e) for e in errors];return 1
    print('OK Livre I V2: démo publique, intégrale absente du dépôt, lecture/téléchargement privés, auteur vérifié serveur, production non déployée.')
    return 0

if __name__=='__main__':raise SystemExit(main())
