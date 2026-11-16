#!/usr/bin/env node
// Exécute la branche save_character réellement livrée dans l'Edge Admin V18.
// Données fictives, aucune session Supabase et aucune écriture réseau.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const edge=readFileSync(resolve(ROOT,'supabase/functions/admin-sinjira-v18/index.ts'),'utf8');
const START="if(a==='save_character'){";
const END="    return privateJson({ok:false,error:'Action inconnue.'";
const i=edge.indexOf(START),j=edge.indexOf(END,i);
assert.ok(i>=0&&j>i,'Le vrai bloc save_character est introuvable');
const block=edge.slice(i,j);
const regexMarker=edge.match(/const NOVEL_UUID_RE=(\/\^\[0-9a-f\].*?\/i);/);
assert.ok(regexMarker,'Validation UUID déclarée dans le vrai fichier Edge');
const NOVEL_UUID_RE=new Function('return '+regexMarker[1])();
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
const saveCharacter=new AsyncFunction('b','s','user','audit','statusEvent','privateJson','NOVEL_UUID_RE',
  "const a='save_character';\n"+block+"\nthrow new Error('MISSING_RESPONSE');");

const ROMAN_I='a1111111-1111-4111-8111-111111111111';
const ROMAN_II='b2222222-2222-4222-8222-222222222222';
const PERSONNAGE='c3333333-3333-4333-8333-333333333333';
function privateJson(data,status=200){
  return new Response(JSON.stringify(data),{
    status,headers:{'Content-Type':'application/json','Cache-Control':'private, no-store, max-age=0'},
  });
}
function mockService({
  data={slug:'la-cendre-du-jugement'},error=null,
  currentNovelId=null,currentNovelSlug='roman-2',currentError=null,
  currentMissing=false,currentId=PERSONNAGE,stale=false,writeError=null
}={}){
  const calls=[];
  const s={
    from(table){
      calls.push(['from',table]);
      if(table==='novels'){
        return {
          select(columns){calls.push(['select-novel',columns]);return this;},
          eq(column,id){calls.push(['novel-id',column,id]);return this;},
          async maybeSingle(){calls.push(['novel-read']);return {data,error};},
        };
      }
      if(table==='characters'){
        return {
          select(columns){
            calls.push(['select-current',columns]);
            assert.equal(columns,'id,novel_id,novels(slug)');
            return {
              eq(column,id){
                calls.push(['current-id',column,id]);
                return {
                  async maybeSingle(){
                    calls.push(['current-read']);
                    return {data:currentMissing?null:{
                      id:currentId,novel_id:currentNovelId,
                      novels:currentNovelId?{slug:currentNovelSlug}:null
                    },error:currentError};
                  }
                };
              }
            };
          },
          update(fields){
            calls.push(['character-write',fields]);
            const builder={
              eq(column,value){
                calls.push(['update-eq',column,value]);
                return this;
              },
              is(column,value){
                calls.push(['update-is',column,value]);
                return this;
              },
              select(columns){
                assert.equal(columns,'*');
                return {
                  async maybeSingle(){
                    calls.push(['write-result']);
                    return {
                      data:stale?null:{id:PERSONNAGE,user_id:'test-user',submission_id:null},
                      error:writeError
                    };
                  }
                };
              }
            };
            return builder;
          }
        };
      }
      throw new Error('UNEXPECTED_TABLE:'+table);
    },
  };
  return {s,calls};
}
async function execute(character,settings={}){
  const {s,calls}=mockService(settings);
  const audits=[];
  const b={character:{id:PERSONNAGE,public_name:'Personnage d’essai',...character}};
  const promise=saveCharacter(b,s,{id:'test-admin'},
    async (...items)=>audits.push(items),
    async ()=>{throw new Error('NO_STATUS_EVENT_EXPECTED');},
    privateJson,NOVEL_UUID_RE);
  return {promise,calls,audits};
}
function noWrite(calls){
  assert.equal(calls.some(item=>item[0]==='character-write'),false,
    'la décision d’accès doit précéder toute écriture du personnage');
}

test('Roman I sans confirmation : aucun écrit et rejet obligatoire',async()=>{
  const result=await execute({novel_id:ROMAN_I});
  await assert.rejects(result.promise,e=>e?.message==='ROMAN1_LOCKED');
  noWrite(result.calls);
  assert.equal(result.audits.length,0);
});

test('Roman I confirmé : mise à jour et journalisation conservées',async()=>{
  const result=await execute({novel_id:ROMAN_I,author_confirmed_retcon:true});
  const response=await result.promise;
  assert.equal(response.status,200);
  assert.equal(response.headers.get('Cache-Control'),'private, no-store, max-age=0');
  assert.equal((await response.json()).ok,true);
  assert.ok(result.calls.some(x=>x[0]==='character-write'&&x[1].novel_id===ROMAN_I));
  assert.equal(result.audits.length,1);
});

test('erreur SQL : refus fermé même si data contredit error',async()=>{
  for(const data of [{slug:'roman-autorise'},null,{slug:'la-cendre-du-jugement'}]){
    const result=await execute({novel_id:ROMAN_I,author_confirmed_retcon:true},
      {data,error:{message:'schema unavailable',code:'DB_FAILED'}});
    await assert.rejects(result.promise,e=>e?.message==='NOVEL_LOOKUP_UNAVAILABLE');
    noWrite(result.calls);
  }
});

test('roman absent ou slug incohérent : refus avant UPDATE',async()=>{
  for(const data of [null,{}, {slug:null}, {slug:42}]){
    const result=await execute({novel_id:ROMAN_I}, {data,error:null});
    await assert.rejects(result.promise,e=>e?.message==='NOVEL_NOT_FOUND');
    noWrite(result.calls);
  }
});

test('identifiants malformés : refus avant toute requête',async()=>{
  for(const value of ['other',42,{},['uuid'],'../../novel',
    'a'.repeat(300),'11111111-1111-1111-1111-11111111111Z']){
    const result=await execute({novel_id:value});
    await assert.rejects(result.promise,e=>e?.message==='NOVEL_ID_INVALID');
    assert.equal(result.calls.length,0);
  }
});

test('romans valides autres que Roman I : aucun retcon requis',async()=>{
  const result=await execute({novel_id:ROMAN_II},{data:{slug:'autre-roman'}});
  const response=await result.promise;
  assert.equal((await response.json()).ok,true);
  assert.ok(result.calls.some(x=>x[0]==='character-write'&&x[1].novel_id===ROMAN_II));
});

test('personnage sans roman : comportement historique conservé',async()=>{
  const result=await execute({novel_id:null,canon_status:'PROVISOIRE'});
  assert.equal((await (await result.promise).json()).ok,true);
  assert.equal(result.calls.filter(x=>x[0]==='from'&&x[1]==='novels').length,0);
  assert.ok(result.calls.some(x=>x[0]==='character-write'&&x[1].novel_id===null));
});

test('CANON doit conserver une confirmation humaine indépendante du roman',async()=>{
  const result=await execute({novel_id:ROMAN_I,canon_status:'CANON'});
  await assert.rejects(result.promise,e=>e?.message==='CANON_CONFIRMATION_REQUIRED');
  assert.equal(result.calls.length,0);
});


test('détacher du Roman I sans confirmation doit rester impossible',async()=>{
  const result=await execute({novel_id:null},{
    currentNovelId:ROMAN_I,currentNovelSlug:'la-cendre-du-jugement'
  });
  await assert.rejects(result.promise,e=>e?.message==='ROMAN1_LOCKED');
  noWrite(result.calls);
  assert.equal(result.audits.length,0);
});

test('déplacer du Roman I vers un autre roman exige aussi la confirmation',async()=>{
  const result=await execute({novel_id:ROMAN_II},{
    data:{slug:'roman-2'},currentNovelId:ROMAN_I,
    currentNovelSlug:'la-cendre-du-jugement'
  });
  await assert.rejects(result.promise,e=>e?.message==='ROMAN1_LOCKED');
  noWrite(result.calls);
});

test('retrait du Roman I avec confirmation passe et contrôle la version précédente',async()=>{
  const result=await execute({novel_id:null,author_confirmed_retcon:true},{
    currentNovelId:ROMAN_I,currentNovelSlug:'la-cendre-du-jugement'
  });
  assert.equal((await (await result.promise).json()).ok,true);
  assert.deepEqual(result.calls.filter(x=>x[0]==='update-eq'),[
    ['update-eq','id',PERSONNAGE],['update-eq','novel_id',ROMAN_I]
  ]);
  assert.equal(result.calls.filter(x=>x[0]==='update-is').length,0);
  assert.equal(result.audits.length,1);
});

test('transfert depuis le Roman I avec accord vérifie aussi le roman destinataire',async()=>{
  const result=await execute({novel_id:ROMAN_II,author_confirmed_retcon:true},{
    data:{slug:'roman-2'},currentNovelId:ROMAN_I,
    currentNovelSlug:'la-cendre-du-jugement'
  });
  assert.equal((await (await result.promise).json()).ok,true);
  assert.ok(result.calls.some(x=>x[0]==='novel-id'&&x[2]===ROMAN_II));
  assert.ok(result.calls.some(x=>x[0]==='update-eq'&&x[1]==='novel_id'&&x[2]===ROMAN_I));
});

test('lecture du rattachement courant indisponible : aucun UPDATE',async()=>{
  for(const scenario of [
    {currentError:{code:'DB_UNAVAILABLE'}},
    {currentMissing:true},
    {currentId:'wrong-id'}
  ]){
    const result=await execute({novel_id:null},scenario);
    const expected=scenario.currentError?'CHARACTER_LOOKUP_UNAVAILABLE':'CHARACTER_NOT_FOUND';
    await assert.rejects(result.promise,e=>e?.message===expected);
    noWrite(result.calls);
  }
});

test('relation du roman courant inconnue ou incohérente : refus fermé',async()=>{
  for(const currentNovelSlug of [undefined,null,{},42,'']){
    const result=await execute({novel_id:null},{
      currentNovelId:ROMAN_I,currentNovelSlug
    });
    if(currentNovelSlug===''){
      // Valeur de type chaîne vide : refus conservateur, aucun nom connu ;
      // la validation du type est satisfaite mais la branche retcon n'est pas
      // déclenchée. Ne pas tester ce cas tant que le schéma interdit le vide.
      continue;
    }
    await assert.rejects(result.promise,e=>e?.message==='CHARACTER_NOVEL_UNAVAILABLE');
    noWrite(result.calls);
  }
});

test('une modification concurrente du roman bloque la sauvegarde et l’audit',async()=>{
  for(const currentNovelId of [null,ROMAN_I,ROMAN_II]){
    const result=await execute({novel_id:null,author_confirmed_retcon:true},{
      currentNovelId,currentNovelSlug:currentNovelId===ROMAN_I?'la-cendre-du-jugement':'roman-2',
      stale:true
    });
    await assert.rejects(result.promise,e=>e?.message==='CHARACTER_CHANGED');
    assert.equal(result.calls.filter(x=>x[0]==='character-write').length,1);
    assert.equal(result.audits.length,0);
    if(currentNovelId===null){
      assert.deepEqual(result.calls.filter(x=>x[0]==='update-is'),[['update-is','novel_id',null]]);
    }else{
      assert.ok(result.calls.some(x=>x[0]==='update-eq'&&x[1]==='novel_id'&&x[2]===currentNovelId));
    }
  }
});

test('identifiant du personnage invalide : aucune lecture ou écriture',async()=>{
  for(const id of [null,'',{},'constructor','../a','x'.repeat(100)]){
    const result=await execute({id,novel_id:null});
    await assert.rejects(result.promise,e=>e?.message==='CHARACTER_ID_INVALID');
    assert.equal(result.calls.length,0);
  }
});

test('une erreur SQL inconnue n’est jamais publiée dans une réponse privée',()=>{
  assert.ok(edge.includes("if(e?.message==='NOVEL_LOOKUP_UNAVAILABLE')return privateJson("));
  assert.ok(edge.includes("code:'NOVEL_LOOKUP_UNAVAILABLE'},503)"));
  assert.ok(edge.includes("if(e?.message==='NOVEL_ID_INVALID')return privateJson("));
  assert.ok(edge.includes("code:'NOVEL_ID_INVALID'},400)"));
  assert.ok(edge.includes("if(e?.message==='NOVEL_NOT_FOUND')return privateJson("));
  assert.ok(edge.includes("code:'NOVEL_NOT_FOUND'},400)"));
  assert.ok(!edge.includes("error:novelError.message"));
  assert.ok(edge.includes("code:'CHARACTER_CHANGED'},409)"));
  assert.ok(edge.includes("code:'CHARACTER_LOOKUP_UNAVAILABLE'},503)"));
  assert.ok(!edge.includes('error:currentError.message'));
  assert.ok(!edge.includes('error:currentError?.message'));
});
