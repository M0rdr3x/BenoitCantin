import test from 'node:test';
import assert from 'node:assert/strict';
import {fractureAggregateSeatSafeSuspicionsV40 as aggregate, fracturePreparePrivateFinalDecisionV40 as prepare} from '../../assets/js/sinjira-fracture-soupcons-v40.mjs';
import {fractureAggregateSuspicionsV39 as previous} from '../../assets/js/sinjira-fracture-soupcons-v39.mjs';

const make=(humans,options={})=>{
 const seats=Math.max(3,humans);
 const express=options.express??false;
 const rounds=express?6:10;
 return {
   humans,express,allowAbstention:false,allowSelfSuspicion:false,
   eligibleTargets:Array.from({length:seats},(_,i)=>i+1),
   roundBallots:Array.from({length:rounds},()=>Array.from({length:humans},(_,i)=>
      ((i+1)%seats)+1)),
   ...options
 };
};

test('trois humains : soupçons corrects, cumuls inchangés par rapport à V39',()=>{
 const args=make(3);
 const res=aggregate(args);
 assert.deepEqual(res,previous(args));
 assert.equal(res.submitted,30);
 assert.deepEqual(res.totals,[10,10,10]);
});
test('le premier humain ne peut pas se soupçonner sans autorisation explicite',()=>{
 const args=make(3);
 args.roundBallots[0][0]=1;
 assert.throws(()=>aggregate(args),/Auto-soupçon interdit/);
});
test('la même règle s applique au deuxième et au dernier humain',()=>{
 for(const seat of [2,3]){
  const args=make(3);
  args.roundBallots[4][seat-1]=seat;
  assert.throws(()=>aggregate(args),/Auto-soupçon interdit/);
 }
});
test('le responsable peut autoriser explicitement l auto-soupçon',()=>{
 const args=make(3,{allowSelfSuspicion:true});
 args.roundBallots=Array.from({length:10},()=>[1,2,3]);
 const result=aggregate(args);
 assert.deepEqual(result.totals,[10,10,10]);
});
test('politique d auto-soupçon absente ou non booléenne : refus',()=>{
 const args=make(3);
 delete args.allowSelfSuspicion;
 assert.throws(()=>aggregate(args),/doit être explicite/);
 for(const value of [null,0,1,'false',undefined]){
  assert.throws(()=>aggregate({...make(3),allowSelfSuspicion:value}),/doit être explicite/);
 }
});
test('Solo : seuls les choix de l humain comptent, sièges invisibles accusables',()=>{
 const res=aggregate(make(1));
 assert.equal(res.humans,1);
 assert.equal(res.seats,3);
 assert.deepEqual(res.totals,[0,10,0]);
 assert.throws(()=>aggregate(make(1,{roundBallots:Array.from({length:10},()=>[1])})),/Auto-soupçon interdit/);
});
test('Duo : les sièges invisibles sont valides si la politique l autorise',()=>{
 const res=aggregate(make(2,{roundBallots:Array.from({length:10},()=>[3,3])}));
 assert.deepEqual(res.totals,[0,0,20]);
 assert.equal(res.submitted,20);
 const forbidden=make(2,{eligibleTargets:[1,2],roundBallots:Array.from({length:10},()=>[3,3])});
 assert.throws(()=>aggregate(forbidden),/non autorisé/);
});
test('Express : six rondes complètes, sans auto-soupçon pour 13 ou 20 humains',()=>{
 for(const humans of [13,20]){
  const result=aggregate(make(humans,{express:true}));
  assert.equal(result.rounds,6);
  assert.equal(result.submitted,6*humans);
  assert.equal(result.totals.reduce((n,v)=>n+v,0),6*humans);
 }
});
test('le serveur doit fournir des bulletins complets et des cibles exactes',()=>{
 const args=make(3);
 assert.throws(()=>aggregate({...args,roundBallots:null}),/obligatoires/);
 assert.throws(()=>aggregate({...args,roundBallots:[null,...args.roundBallots.slice(1)]}),/Un choix/);
 assert.throws(()=>aggregate({...args,roundBallots:[[2],...args.roundBallots.slice(1)]}),/Un choix/);
 assert.throws(()=>aggregate({...args,roundBallots:[[2,undefined,1],...args.roundBallots.slice(1)]}),/entier/);
 assert.throws(()=>aggregate({...args,roundBallots:[[2,'1',1],...args.roundBallots.slice(1)]}),/entier/);
 assert.throws(()=>aggregate({...args,roundBallots:[[2,4,1],...args.roundBallots.slice(1)]}),/entier/);
 assert.throws(()=>aggregate({...args,roundBallots:args.roundBallots.slice(1)}),/Toutes les rondes/);
});
test('abstention et cibles globales : contrôles V39 préservés sans valeurs par défaut',()=>{
 const args=make(3);
 args.roundBallots[0][2]=null;
 assert.throws(()=>aggregate(args),/Abstention interdite/);
 const permitted=aggregate({...args,allowAbstention:true});
 assert.equal(permitted.abstentions,1);
 assert.equal(permitted.submitted,29);
 assert.throws(()=>aggregate({...make(3),eligibleTargets:null}),/cibles autorisées/);
 assert.throws(()=>aggregate({...make(3),allowAbstention:undefined}),/doit être explicite/);
});
test('aucun bulletin individuel ni secret dans le résultat gelé',()=>{
 const r=aggregate(make(20));
 assert.ok(Object.isFrozen(r)&&Object.isFrozen(r.totals)&&Object.isFrozen(r.perRound));
 const json=JSON.stringify(r);
 for(const term of ['roundBallots','eligibleTargets','session','email','user_id','access_token','password']){
  assert.equal(json.includes(term),false,term);
 }
});

test('chaînage : trois humains, soupçons complets puis accusations collectives',()=>{
 const args=make(3);
 const r=prepare({...args,finalBallots:[[2],[1],[1]]});
 assert.equal(r.status,'resolved');
 assert.equal(r.decision.ballotCount,3);
 assert.deepEqual(r.suspicions.totals,[10,10,10]);
 assert.deepEqual(r.decision.selected,[1]);
 assert.equal(r.decision.aggregates.find(x=>x.seat===1).suspicions,10);
 assert.ok(Object.isFrozen(r)&&Object.isFrozen(r.decision)&&Object.isFrozen(r.suspicions));
});
test('chaînage Duo : soupçons cumulés tranchent une égalité de votes',()=>{
 const args=make(2,{
   roundBallots:Array.from({length:10},()=>[3,3])
 });
 const r=prepare({...args,finalBallots:[[2],[3]]});
 assert.deepEqual(r.suspicions.totals,[0,0,20]);
 assert.equal(r.status,'resolved');
 assert.deepEqual(r.decision.selected,[3]);
});
test('chaînage Solo : un seul bulletin final et aucun siège invisible votant',()=>{
 const r=prepare({...make(1),finalBallots:[[2]]});
 assert.equal(r.decision.ballotCount,1);
 assert.equal(r.suspicions.submitted,10);
 assert.deepEqual(r.decision.selected,[2]);
});
test('chaînage Express : six rondes, nombre réglementaire d accusations par humain',()=>{
 const humans=13;
 const finalBallots=Array.from({length:humans},(_,i)=>
  Array.from({length:humans},(_,j)=>j+1).filter(seat=>seat!==i+1).slice(0,4));
 const r=prepare({...make(humans,{express:true}),finalBallots});
 assert.equal(r.suspicions.rounds,6);
 assert.equal(r.decision.ballotCount,52);
 assert.equal(r.decision.selected.length+r.decision.tieSlots,4);
});
test('chaînage à refus : soupçons et accusations incomplets ne passent pas',()=>{
 const args=make(3);
 assert.throws(()=>prepare({...args,finalBallots:null}),/Un bulletin/);
 assert.throws(()=>prepare({...args,finalBallots:[[2],[1]]}),/Un bulletin/);
 assert.throws(()=>prepare({...args,finalBallots:[[1],[1],[1]]}),/lui-même/);
 assert.throws(()=>prepare({...args,finalBallots:[[2],[1],[1,2]]}),/exactement/);
 assert.throws(()=>prepare({...args,roundBallots:args.roundBallots.slice(1),finalBallots:[[2],[1],[1]]}),/Toutes les rondes/);
});
test('chaînage : aucune identité ni bulletin privé rendu; résultat à garder serveur',()=>{
 const r=prepare({...make(3),finalBallots:[[2],[1],[1]]});
 const s=JSON.stringify(r);
 for(const secret of ['roundBallots','finalBallots','user_id','email','password','access_token','account']){
  assert.equal(s.includes(secret),false,secret);
 }
 assert.equal(Object.hasOwn(r,'bonus'),false);
 assert.equal(Object.hasOwn(r,'winner'),false);
});
