'use strict';
// Test de la vraie décision serveur de conflit unique, sans Supabase ni requête.
// Concurrence : deux onglets ont lu "aucun dossier", un INSERT réussit,
// l'autre reçoit 23505. Un refus 409 n'est sûr qu'après relecture propriétaire.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const argv=process.argv.slice(2);
assert.ok(argv.length===0||(argv.length===2&&argv[0]==='--source'&&path.isAbsolute(argv[1])),
  'Source externe acceptée uniquement avec --source <chemin absolu>');
const filepath=argv.length===2?argv[1]:path.join(__dirname,'..','supabase/functions/submit-character-questionnaire/index.ts');
assert.ok(fs.statSync(filepath).isFile(),'Source du contrôleur Edge requise');
const source=fs.readFileSync(filepath,'utf8');
const func=/async function hasConfirmedConcurrentSubmission\(service:any,userId:string,writeError:unknown\):Promise<boolean>\{[\s\S]*?\n\}/g;
const found=[...source.matchAll(func)];
assert.equal(found.length,1,'Une seule vraie fonction de vérification du conflit 23505');
const code=found[0][0].replace('(service:any,userId:string,writeError:unknown):Promise<boolean>','(service,userId,writeError)');
const context={};
vm.runInNewContext(code+'\nthis.conflict=hasConfirmedConcurrentSubmission;',context,{timeout:1500});
const decide=context.conflict;
assert.equal(typeof decide,'function');
let assertions=0;
function eq(actual,expected,label){assert.equal(actual,expected,label);assertions++}
function yes(actual,label){assert.ok(actual,label);assertions++}
const owner='10000000-0000-4000-8000-000000000001';
function mock({record={id:'20000000-0000-4000-8000-000000000002'},error=null,throws=false}={}){
 const calls=[];
 const api={
   from(table){calls.push('from:'+table);eq(table,'character_submissions','Ne relire que les demandes');
     return {
       select(columns){calls.push('select:'+columns);eq(columns,'id','Ne lire aucun champ privé');return {
         eq(field,value){calls.push('eq:'+field);eq(field,'user_id','Filtrer le dossier au propriétaire');
           eq(value,owner,'Filtrer au compte authentifié');
           return {async maybeSingle(){calls.push('maybeSingle');if(throws)throw Error('read temporarily unavailable');return {data:record,error}}};
         }
       }}
     };
   }
 };
 return {api,calls};
}
async function main(){
 const unique={code:'23505'};
 const saved=mock();
 eq(await decide(saved.api,owner,unique),true,'Unicité 23505 ET dossier existant => doublon certain');
 eq(saved.calls.includes('maybeSingle'),true,'Le conflit impose une relecture effective du dossier');
 const missing=mock({record:null});
 eq(await decide(missing.api,owner,unique),false,'23505 sans dossier propriétaire => état incertain');
 const unusable=mock({record:{id:''}});
 eq(await decide(unusable.api,owner,unique),false,'Dossier sans identifiant valide => état incertain');
 const badType=mock({record:{id:3}});
 eq(await decide(badType.api,owner,unique),false,'Dossier avec identifiant invalide => état incertain');
 const errored=mock({error:{code:'42501'}});
 eq(await decide(errored.api,owner,unique),false,'Lecture refusée => jamais de faux 409');
 const thrown=mock({throws:true});
 eq(await decide(thrown.api,owner,unique),false,'Erreur de lecture => ne jamais classifier le conflit');
 for(const [name,writeError] of [
   ['Erreur réseau',new Error('Network connection reset')],
   ['Erreur SQL autre',{code:'23503'}],
   ['Code HTTP texte',{code:409}],
   ['Contrainte SQL inattendue',{code:'23514'}],
   ['Code non textuel',{code:23505}],
   ['Objet vide',{}],
   ['Entrée nulle',null],
   ['Entrée chaîne','23505']
 ]){
   const calls=mock();
   eq(await decide(calls.api,owner,writeError),false,name+' : jamais classé doublon');
   eq(calls.calls.length,0,name+' : aucune relecture sur une erreur non UNIQUE');
 }
 const marker='if(await hasConfirmedConcurrentSubmission(service,user.id,error))';
 const canonicalCode="code:'ONE_CHARACTER_PER_ACCOUNT'";
 const branch=source.indexOf(marker);
 const insert=source.indexOf("const {data:sub,error}=await service.from('character_submissions').insert(");
 yes(insert>=0&&branch>insert,'Relecture du conflit seulement après tentative INSERT');
 yes(source.indexOf("return privateJson({ok:false",branch)>branch,'Réponse refus explicite');
 yes(source.indexOf(canonicalCode,branch)>branch,'Même contrat 409 que la vérification initiale');
 yes(source.indexOf('},409);',branch)>branch,'Code HTTP 409 explicite');
 yes(source.indexOf("throw new Error('CHARACTER_SUBMISSION_WRITE_FAILED');",branch)>branch,
   'Un échec non certifié demeure une erreur générique');
 eq(source.split(canonicalCode).length-1,2,'Deux chemins uniques donnent le même refus métier');
 yes(source.includes("const VERSION='24.5.3';"),'Révision de fonction incrémentée');
 console.log('PASS SINJIRA concurrence Registre : '+assertions+' assertions sans accès réseau.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
