#!/usr/bin/env python3
"""Garde fail-closed du téléversement signé des documents administratifs.

Aucune demande HTTP ou accès à des secrets : vérification du code réellement
versionné, avec mutations négatives de configuration et de chemin.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADMIN = ROOT / 'supabase/functions/admin-console/index.ts'
HELPER = ROOT / 'supabase/functions/_shared/private-document-storage.mjs'
WORKFLOW = ROOT / '.github/workflows/sinjira-document-storage-private-security.yml'

REQUIRED_ADMIN = {
    'autorisation MFA avant téléversement': 'const {user,service}=await requiredAdmin(req);',
    'action administrative explicite': "if(action==='prepare_document_upload'){",
    'bucket fixé serveur': "const DOCUMENT_BUCKET='sinjira-private-documents';",
    'UUID projet vérifié': 'if(!UUID_RE.test(projectId))',
    'projet lu depuis la base': "const {data:project,error:projectError}=await service.from('projects')",
    'slug absent refusé': "if(projectError||!project||typeof project.slug!=='string')",
    'chemin basé sur le slug SQL': 'privateAdminDocumentUploadPath(bucket,project.slug,',
    'UUID aléatoire du chemin': 'crypto.randomUUID()',
    'chemin non canonique refusé': "if(!path)return privateJson({ok:false,error:'Chemin de document invalide.'",
    'vérification du bucket réel': 'service.storage.getBucket(bucket)',
    'identité exacte et confidentialité': '!isVerifiedPrivateDocumentBucket(bucketMetadata,bucket)',
    'erreur métadonnées fail-closed': 'if(bucketMetadataError||!isVerifiedPrivateDocumentBucket(bucketMetadata,bucket))',
    'log à code fixe': "console.error('[admin-console]',{code:'DOCUMENT_UPLOAD_BUCKET_UNVERIFIED'});",
    'réponse sans lien si Storage incertain': "code:'DOCUMENT_PRIVATE_STORAGE_UNAVAILABLE'},503)",
    'signature privée seulement': 'service.storage.from(bucket).createSignedUploadUrl(path)',
    'insertion après signature': "service.from('documents').insert({",
    'référence du projet vérifié': 'project_id:projectId,title:',
    'lien de téléversement dans réponse privée': 'return privateJson({ok:true,document:row,upload:{path,token:upload.token,bucket}});',
    'erreur de signature expurgée': "throw new Error('DOCUMENT_UPLOAD_SIGN_FAILED')",
    'erreur insertion expurgée': "throw new Error('DOCUMENT_UPLOAD_RECORD_FAILED')",
}
REQUIRED_HELPER = {
    'format projectSlug exact': r'/^[a-z0-9][a-z0-9_-]{0,95}$/',
    'UUID v4 de chemin': r'-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-',
    'fonction de chemin exécutée': 'export function privateAdminDocumentUploadPath(',
    'construction depuis le slug vérifié': 'const path = ',
    'revalidation du chemin Storage': 'privateDocumentLocationValid(bucket, path)',
    'métadonnées Storage non publiques': 'metadata.public === false',
    'identité du bucket': 'metadata.id === expectedBucketId',
}
REQUIRED_WORKFLOW = (
    "'supabase/functions/admin-console/**'",
    "'scripts/validate_admin_document_upload_security.py'",
    '        run: python3 scripts/validate_admin_document_upload_security.py --self-test\n',
    '        run: python3 scripts/validate_admin_document_upload_security.py\n',
)

def audit(admin: str, helper: str, workflow: str) -> list[str]:
    findings: list[str] = []
    for label, marker in REQUIRED_ADMIN.items():
        if marker not in admin:
            findings.append('admin-console : contrôle manquant : ' + label)
    for label, marker in REQUIRED_HELPER.items():
        if marker not in helper:
            findings.append('module private-document-storage : contrôle manquant : ' + label)
    for marker in REQUIRED_WORKFLOW:
        if marker not in workflow:
            findings.append('CI documents : test de téléversement absent : ' + marker)

    section = admin.split("if(action==='prepare_document_upload'){", 1)
    upload = section[1].split("if(action==='finalize_document'", 1)[0] if len(section) == 2 else ''
    gates = [
        "if(!UUID_RE.test(projectId))",
        "service.from('projects')",
        'privateAdminDocumentUploadPath(bucket,project.slug,',
        'service.storage.getBucket(bucket)',
        'if(bucketMetadataError||!isVerifiedPrivateDocumentBucket(bucketMetadata,bucket))',
        'createSignedUploadUrl(path)',
        "service.from('documents').insert({",
        'return privateJson({ok:true,document:row,upload:{path,token:upload.token,bucket}});',
    ]
    positions = [upload.find(x) for x in gates]
    if any(x < 0 for x in positions) or positions != sorted(positions):
        findings.append('Ordre exigé : UUID → projet SQL → chemin sûr → bucket privé → signature → document → token')
    if 'x.project_slug' in upload:
        findings.append('Le navigateur ne doit pas choisir le répertoire Storage via project_slug')
    if upload.count('createSignedUploadUrl(') != 1 or upload.count('service.storage.getBucket(') != 1:
        findings.append('Un seul contrôle du bucket réel doit précéder une seule signature')
    if not upload or 'getPublicUrl(' in upload or 'public:true' in upload:
        findings.append('Impossible de valider la branche de téléversement privé')
    return findings

def self_test(admin: str, helper: str, workflow: str) -> int:
    findings = audit(admin, helper, workflow)
    if findings:
        raise AssertionError('La version saine est rejetée : ' + ' ; '.join(findings))
    mutants = {
        'bypass MFA': ('admin', 'const {user,service}=await requiredAdmin(req);', "const service=serviceClient();"),
        'UUID projet accepté': ('admin', 'if(!UUID_RE.test(projectId))', 'if(false)'),
        'projet SQL ignoré': ('admin', "service.from('projects')", "service.from('bad-projects')"),
        'slug fourni par navigateur': ('admin', 'privateAdminDocumentUploadPath(bucket,project.slug,',
                                      'privateAdminDocumentUploadPath(bucket,x.project_slug,'),
        'chemin arbitraire autorisé': ('admin', 'if(!path)return privateJson(', 'if(false)return privateJson('),
        'métadonnées non lues': ('admin', 'service.storage.getBucket(bucket)', 'Promise.resolve({data:{public:false}})'),
        'bucket public accepté': ('admin', 'if(bucketMetadataError||!isVerifiedPrivateDocumentBucket(bucketMetadata,bucket))',
                                 'if(false)'),
        'log Storage brut': ('admin', "console.error('[admin-console]',{code:'DOCUMENT_UPLOAD_BUCKET_UNVERIFIED'});",
                             'console.error(bucketMetadataError);'),
        '503 retiré': ('admin', "code:'DOCUMENT_PRIVATE_STORAGE_UNAVAILABLE'},503)",
                        "code:'DOCUMENT_PRIVATE_STORAGE_UNAVAILABLE'},200)"),
        'upload signature supprimée': ('admin', 'createSignedUploadUrl(path)', 'getPublicUrl(path)'),
        'RPC insertion avant signature': ('admin', "service.from('documents').insert({",
                                          "service.from('not-documents').insert({"),
        'slug avec traversée': ('helper', r'/^[a-z0-9][a-z0-9_-]{0,95}$/', r'/^.*$/'),
        'UUID non aléatoire': ('helper', r'-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-', r'-[0-9a-f]{4}-[0-9a-f]{4}-'),
        'chemin non revérifié': ('helper', 'privateDocumentLocationValid(bucket, path)', 'true'),
        'bucket non privé': ('helper', 'metadata.public === false', 'metadata.public !== undefined'),
        'identité bucket ignorée': ('helper', 'metadata.id === expectedBucketId', 'true'),
        'CI auto-test retiré': ('workflow',
                                 '        run: python3 scripts/validate_admin_document_upload_security.py --self-test\n',
                                 '        run: echo skipped-admin-upload-autotest\n'),
        'CI vérification retirée': ('workflow',
                                    '        run: python3 scripts/validate_admin_document_upload_security.py\n',
                                    '        run: echo skipped-admin-upload-validation\n'),
    }
    for label, (target, old, new) in mutants.items():
        source = {'admin':admin, 'helper':helper, 'workflow':workflow}[target]
        if source.count(old) != 1:
            raise AssertionError('Mutation sans effet : ' + label)
        mutated = source.replace(old, new, 1)
        a,h,w=admin,helper,workflow
        if target=='admin': a=mutated
        elif target=='helper': h=mutated
        else: w=mutated
        if not audit(a,h,w):
            raise AssertionError('Régression non détectée : ' + label)
    print(f'OK : {len(mutants)} mutations téléversement/Storage détectées.')
    return len(mutants)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    admin = ADMIN.read_text('utf-8')
    helper = HELPER.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')
    if args.self_test:
        self_test(admin, helper, workflow)
    findings = audit(admin, helper, workflow)
    if findings:
        for x in findings:
            print('NO_GO : ' + x)
        return 1
    print('OK : téléversement seulement après rôle admin AAL2, projet SQL, chemin sûr et bucket réellement privé.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
