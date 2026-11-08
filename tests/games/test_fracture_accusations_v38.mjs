import test from 'node:test';
import assert from 'node:assert/strict';
import {fractureAggregateFinalBallotsV38 as rawTally,fractureApplyFinalDrawV38 as draw} from '../../assets/js/sinjira-fracture-accusations-v38.mjs';
// Les zéros sont FOURNIS explicitement par les tests; le module ne doit jamais les inventer.
const tally=(humans,ballots,options={})=>rawTally(humans,ballots,{
 suspicionTotals:Array(Math.max(3,humans)).fill(0),...options
});

test('Solo : seuls les humains votent, sièges invisibles accusables',()=>{
 const t=tally(1,[[3]],{suspicionTotals:[0,0,0]});
 assert.equal(t.agents,1);assert.equal(t.ballotCount,1);
 assert.equal(t.status,'resolved');assert.deepEqual(t.selected,[3]);
 assert.equal(t.aggregates.find(x=>x.seat===2).votes,0);
});
test('Duo : un vote par humain et aucun vote pour le siège invisible',()=>{
 const t=tally(2,[[2],[3]]);
 assert.equal(t.ballotCount,2);assert.equal(t.agents,1);
 assert.deepEqual(new Set(t.tied),new Set([2,3]));
 assert.equal(t.status,'draw-required');assert.equal(t.tieSlots,1);
});
test('aucun vote individuel ni compte dans la réponse agrégée',()=>{
 const t=tally(3,[[2],[1],[1]]);
 assert.deepEqual(t.selected,[1]);
 for(const forbidden of ['ballots','user_id','email','identity','token','password','targets']){
   assert.equal(JSON.stringify(t).includes(forbidden),false);
 }
 assert.ok(Object.isFrozen(t)&&Object.isFrozen(t.aggregates)&&Object.isFrozen(t.aggregates[0]));
});
test('interdire auto-accusation, cibles répétées et nombre incorrect',()=>{
 assert.throws(()=>tally(3,[[1],[1],[2]]),/lui-même/);
 assert.throws(()=>tally(3,[[2],[1]]),/bulletin/);
 assert.throws(()=>tally(3,[[2,3],[1],[1]]),/exactement/);
 assert.throws(()=>tally(3,[[4],[1],[2]]),/1 à 3/);
 assert.throws(()=>tally(3,[[2],[1],['1']]),/entier/);
 assert.throws(()=>tally(3,[[2],[1],[1,1]]),/exactement/);
 assert.throws(()=>tally(5,[[2,2],[1,3],[1,2],[1,2],[1,2]]),/répétée/);
});
test('5 humains : chaque humain vote pour deux agents, sièges distincts',()=>{
 const t=tally(5,[[2,3],[1,3],[1,2],[1,2],[1,2]]);
 assert.equal(t.agents,2);assert.equal(t.ballotCount,10);
 assert.deepEqual(t.selected,[1,2]);
});
test('cumul des soupçons départage seulement les votes ex aequo',()=>{
 const t=tally(2,[[2],[3]],{suspicionTotals:[0,5,1]});
 assert.equal(t.status,'resolved');assert.deepEqual(t.selected,[2]);
 const v=tally(2,[[2],[3]],{suspicionTotals:[10,2,3]});
 assert.deepEqual(v.selected,[3]);
});
test('une égalité au seuil exige un tirage externe validé',()=>{
 const t=tally(2,[[2],[3]]);
 assert.equal(t.status,'draw-required');
 assert.throws(()=>draw(t,[]),/incomplet/);
 assert.throws(()=>draw(t,[1]),/ex æquo/);
 const resolved=draw(t,[3]);
 assert.deepEqual(resolved.selected,[3]);
 assert.equal(resolved.status,'resolved');
 assert.throws(()=>draw(resolved,[2]),/non nécessaire/);
});
test('soupçons cumulés doivent être un tableau complet d’entiers non négatifs',()=>{
 assert.throws(()=>tally(3,[[2],[1],[1]],{suspicionTotals:[2,1]}),/couvrir/);
 assert.throws(()=>tally(3,[[2],[1],[1]],{suspicionTotals:[2,-1,0]}),/invalide/);
 assert.throws(()=>tally(3,[[2],[1],[1]],{suspicionTotals:[2,1.5,0]}),/invalide/);
});
test('20 humains : 7 cibles distinctes par humain, aucune auto-accusation',()=>{
 const ballots=Array.from({length:20},(_,index)=>{
  const voter=index+1;return Array.from({length:20},(_,k)=>k+1).filter(k=>k!==voter).slice(0,7);
 });
 const t=tally(20,ballots);
 assert.equal(t.agents,7);assert.equal(t.ballotCount,140);
 assert.equal(t.selected.length+t.tieSlots,7);
 assert.equal(t.aggregates.reduce((n,x)=>n+x.votes,0),140);
});

test('refuse le silence du serveur sur les soupçons cumulés : échec plutôt que faux zéros',()=>{
 const ballots=[[2],[1],[1]];
 assert.throws(()=>rawTally(3,ballots),/couvrir chaque siège/);
 assert.throws(()=>rawTally(3,ballots,{suspicionTotals:null}),/couvrir chaque siège/);
 assert.throws(()=>rawTally(3,ballots,{suspicionTotals:undefined}),/couvrir chaque siège/);
 const actual=rawTally(3,ballots,{suspicionTotals:[0,0,0]});
 assert.equal(actual.status,'resolved');
 assert.deepEqual(actual.selected,[1]);
});
