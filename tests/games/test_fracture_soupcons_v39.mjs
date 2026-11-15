import test from 'node:test';
import assert from 'node:assert/strict';
import {fractureAggregateSuspicionsV39 as aggregate} from '../../assets/js/sinjira-fracture-soupcons-v39.mjs';

const options=(humans,rounds=10,extra={})=>({
  humans,
  roundBallots:Array.from({length:rounds},()=>Array.from({length:humans},()=>2)),
  allowAbstention:false,
  eligibleTargets:Array.from({length:Math.max(humans,3)},(_,i)=>i+1),
  ...extra
});

test('3 humains : 10 rondes complètes, cumuls exacts, aucun bulletin retourné',()=>{
  const args=options(3);
  args.roundBallots=Array.from({length:10},()=>[2,1,1]);
  const r=aggregate(args);
  assert.equal(r.rounds,10);
  assert.equal(r.submitted,30);
  assert.equal(r.abstentions,0);
  assert.deepEqual(r.totals,[20,10,0]);
  assert.deepEqual(r.perRound[0],{round:1,submitted:3,abstentions:0});
  assert.deepEqual(Object.keys(r).sort(),[
    'abstentions','humans','perRound','rounds','seats','submitted','totals','version'
  ].sort());
});

test('Solo : un seul humain vote pour un siège autorisé, pas trois bulletins',()=>{
  const r=aggregate(options(1,10,{eligibleTargets:[2,3]}));
  assert.equal(r.seats,3);
  assert.equal(r.submitted,10);
  assert.deepEqual(r.totals,[0,10,0]);
});

test('Duo : seuls deux humains participent par ronde, sièges invisibles possibles',()=>{
  const r=aggregate(options(2,10,{
    roundBallots:Array.from({length:10},(_,i)=>i%2?[3,2]:[2,3])
  }));
  assert.equal(r.seats,3);
  assert.equal(r.submitted,20);
  assert.deepEqual(r.totals,[0,10,10]);
});

test('Express : seulement 13-20 humains, six rondes',()=>{
  for (const humans of [13,20]) {
    const r=aggregate(options(humans,6,{express:true}));
    assert.equal(r.rounds,6);
    assert.equal(r.submitted,6*humans);
  }
  assert.throws(()=>aggregate(options(12,6,{express:true})),/13 à 20/);
  assert.throws(()=>aggregate(options(20,10,{express:true})),/Toutes les rondes/);
});

test('abstention : interdite par défaut de politique et autorisée si décision explicite',()=>{
  const args=options(3);
  args.roundBallots[0]=[null,1,2];
  assert.throws(()=>aggregate(args),/Abstention interdite/);
  args.allowAbstention=true;
  const r=aggregate(args);
  assert.equal(r.submitted,29);
  assert.equal(r.abstentions,1);
  assert.equal(r.perRound[0].abstentions,1);
  assert.equal(r.totals.reduce((a,b)=>a+b,0),29);
});

test('la politique est obligatoire : pas de choix éditorial implicite',()=>{
  const args=options(3);
  delete args.allowAbstention;
  assert.throws(()=>aggregate(args),/doit être explicite/);
  assert.throws(()=>aggregate({...args,allowAbstention:'true'}),/doit être explicite/);
  assert.throws(()=>aggregate({...args,allowAbstention:true,eligibleTargets:null}),/sans doublon/);
  assert.throws(()=>aggregate({...args,allowAbstention:true,eligibleTargets:[1,1]}),/sans doublon/);
  assert.throws(()=>aggregate({...args,allowAbstention:true,eligibleTargets:[0]}),/1 à 3/);
  assert.throws(()=>aggregate({...args,allowAbstention:true,eligibleTargets:[4]}),/1 à 3/);
});

test('les cibles hors politique et les conversions implicites sont rejetées',()=>{
  assert.throws(()=>aggregate(options(3,10,{eligibleTargets:[1]})),/non autorisé/);
  assert.throws(()=>aggregate(options(3,10,{roundBallots:[
    ['2',2,2],...Array.from({length:9},()=>[2,2,2])
  ]})),/entier/);
  for(const humans of [null,'3',0,21,1.5,NaN,undefined]){
    assert.throws(()=>aggregate(options(humans)),/Humains/);
  }
});

test('bulletins manquants, incomplets ou imprécis : refus systématique',()=>{
  const args=options(3);
  assert.throws(()=>aggregate({...args,roundBallots:args.roundBallots.slice(1)}),/Toutes les rondes/);
  assert.throws(()=>aggregate({...args,roundBallots:[...args.roundBallots,[]]}),/Toutes les rondes/);
  assert.throws(()=>aggregate({...args,roundBallots:[[],...args.roundBallots.slice(1)]}),/emplacement/);
  const wrong=options(3);wrong.roundBallots[0]=[undefined,2,2];
  assert.throws(()=>aggregate(wrong),/entier/);
});

test('résultat gelé, sans mots de passe, identité, emails ni bulletin individuel',()=>{
  const r=aggregate(options(20,10));
  assert.equal(r.submitted,200);
  assert.equal(r.totals.reduce((a,b)=>a+b,0),200);
  assert.ok(Object.isFrozen(r));
  assert.ok(Object.isFrozen(r.totals)&&Object.isFrozen(r.perRound)&&Object.isFrozen(r.perRound[0]));
  const serialized=JSON.stringify(r);
  for(const privateKey of ['user_id','password','email','identity','access_token','roundBallots','eligibleTargets']){
    assert.equal(serialized.includes(privateKey),false,privateKey);
  }
});
