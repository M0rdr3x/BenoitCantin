'use strict';
// Extrait et exécute le VRAI validateur photo du module Edge SINJIRA.
// Aucun appel réseau, aucun compte et aucune écriture dans Storage.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
// Par défaut, tester la source GitHub. Sur ordre explicite du pipeline protégé,
 // réexécuter exactement la même suite sur le fichier téléchargé de Supabase.
const argv=process.argv.slice(2);
assert.ok(argv.length===0||(argv.length===2&&argv[0]==='--source'&&path.isAbsolute(argv[1])),
  'Source extérieure autorisée uniquement en chemin absolu avec --source');
const filePath=argv.length===2?argv[1]:path.join(__dirname,'..','supabase/functions/submit-character-questionnaire/index.ts');
assert.ok(fs.statSync(filePath).isFile(),'Source Edge attendue : fichier régulier');
const file=fs.readFileSync(filePath,'utf8');
const pattern=/function isCanonicalRegistryPhotoPath\(raw:unknown,userId:string\):boolean\{[\s\S]*?\n\}/g;
const funcs=[...file.matchAll(pattern)];
assert.equal(funcs.length,1,'Une seule implémentation du contrôle serveur attendue');
const functionSource=funcs[0][0].replace('(raw:unknown,userId:string):boolean','(raw,userId)');
const context={};
vm.runInNewContext(functionSource+'\nthis.testCanonical=isCanonicalRegistryPhotoPath;',context,{timeout:1500});
const valid=context.testCanonical;
assert.equal(typeof valid,'function');
let assertions=0;
const check=(value,user,want,label)=>{
  assert.equal(valid(value,user),want,label);
  assertions++;
};
const user='10000000-0000-4000-8000-000000000001';
const other='20000000-0000-4000-8000-000000000002';
const uuid='aabbccdd-1234-4abc-8abc-001122334455';
for(const ext of ['jpg','png','webp','avif','gif']){
  check(user+'/'+uuid+'.'+ext,user,true,'Accepter extension source '+ext);
}
for(const [bad,label] of [
  [other+'/'+uuid+'.png','photo d’un autre utilisateur'],
  [user+'/','chemin sans objet'],
  [user+'/'+uuid+'.svg','extension non autorisée'],
  [user+'/'+uuid+'.jpeg','extension non canonique'],
  [user+'/'+uuid.toUpperCase()+'.png','UUID non canonique'],
  [user+'/aabbccdd-1234-1abc-8abc-001122334455.jpg','UUID non v4'],
  [user+'/aabbccdd-1234-4abc-7abc-001122334455.jpg','UUID sans variant RFC'],
  [user+'/nested/'+uuid+'.jpg','sous-dossier inattendu'],
  [user+'//'+uuid+'.png','double slash'],
  [user+'/'+uuid+'.png?download=1','chaîne de requête'],
  [user+'/'+uuid+'.png#fragment','fragment d’URL'],
  [user+'/../'+uuid+'.jpg','traversal'],
  [user+'/%2e%2e/'+uuid+'.jpg','traversal encodé'],
  ['https://example.invalid/'+user+'/'+uuid+'.png','URL distante'],
  [user+'/'+uuid+'.gif\n','contrôle newline'],
  [user+'/'+uuid+'.gif ','espace final'],
  [user+'/'+uuid+'.gif'.repeat(30),'longueur excessive'],
  ['', 'chaîne vide'],
  [0,'numéro'],
  [false,'booléen'],
  [['malicious'],'tableau'],
  [{toString:()=>user+'/'+uuid+'.jpg'},'objet coercible'],
  [null,'null rejeté par la fonction'],
  [undefined,'undefined rejeté par la fonction']
])check(bad,user,false,label);

// La couche HTTP autorise l'absence de photo, pas les valeurs erronées.
assert.match(file,/const photo_path=body\.photo_path\?\?null/);
assert.match(file,/photo_path!==null && !isCanonicalRegistryPhotoPath\(photo_path,user\.id\)/);
assert.match(file,/code:'INVALID_CHARACTER_PHOTO_PATH'/);
assert.doesNotMatch(file,/String\(photo_path\)\.startsWith/);
assert.ok(file.indexOf('isCanonicalRegistryPhotoPath(photo_path,user.id)') <
 file.indexOf("service.from('character_submissions')"),
 'Vérifier le chemin avant une écriture ou lecture de dossier');
console.log('PASS SINJIRA photo source Edge : '+assertions+
  ' assertions sur la vraie fonction, sans requête ou écriture réelle.');
