import test from 'node:test';
import assert from 'node:assert/strict';
import {fractureOperationDeck,fractureSeatController} from '../../assets/js/sinjira-fracture-mechanics-v36.mjs';
import {
  FRACTURE_PUBLIC_REPORTS,fractureStartPublicReportsV37,
  fractureSubmitPublicReportV37,fractureResolveProofV37
} from '../../assets/js/sinjira-fracture-reports-v37.mjs';

const cards=fractureOperationDeck();
const report=(state,seat,report='equilibre')=>fractureSubmitPublicReportV37(state,{seat,report});
const skip=(state,seat)=>fractureResolveProofV37(state,{seat});

test('1 à 20 humains : un rapport par siège, 10 rondes ou Express 6',()=>{
  for(let humans=1;humans<=20;humans++){
    let state=fractureStartPublicReportsV37(humans,{round:1,express:humans>=13});
    assert.equal(state.seats,Math.max(3,humans));
    assert.equal(state.rounds,humans>=13?6:10);
    assert.equal(state.nextSeat,1);
    for(let seat=1;seat<=state.seats;seat++){
      state=report(state,seat);
      assert.equal(state.phase,'proof');
      state=skip(state,seat);
    }
    assert.equal(state.phase,'complete');
    assert.equal(state.nextSeat,null);
    assert.equal(state.reports.length,state.seats);
    assert.deepEqual(state.usedProofSeats,[]);
  }
});

test('le premier siège est configurable, sans doublons ni sièges fictifs',()=>{
  let state=fractureStartPublicReportsV37(3,{seatOrder:[3,1,2]});
  assert.deepEqual(state.seatOrder,[3,1,2]);
  assert.equal(state.nextSeat,3);
  assert.throws(()=>report(state,1),/hors de son tour/);
  state=skip(report(state,3),3);
  assert.equal(state.nextSeat,1);
  assert.throws(()=>fractureStartPublicReportsV37(3,{seatOrder:[1,1,2]}),/dupliqué/);
  assert.throws(()=>fractureStartPublicReportsV37(3,{seatOrder:[1,2,4]}),/1 à 3/);
  assert.throws(()=>fractureStartPublicReportsV37(3,{seatOrder:[1,2]}),/incomplet/);
});

test('rapport mensonger permis, valeurs arbitraires et mauvais tour refusés',()=>{
  assert.deepEqual(FRACTURE_PUBLIC_REPORTS,['resistance','reseau','equilibre']);
  let state=fractureStartPublicReportsV37(3);
  state=report(state,1,'reseau'); // n'exige pas de connaître la main.
  assert.equal(state.reports[0].report,'reseau');
  assert.throws(()=>report(state,1),/phase incorrecte/);
  assert.throws(()=>skip(state,2),/immédiatement/);
  assert.throws(()=>fractureSubmitPublicReportV37(fractureStartPublicReportsV37(3),
    {seat:1,report:'inconnu'}),/Rapport invalide/);
  assert.throws(()=>fractureSubmitPublicReportV37(fractureStartPublicReportsV37(3),
    {seat:'1',report:'resistance'}),/entier/);
  state=skip(state,1);
  assert.equal(state.phase,'report');
  assert.throws(()=>skip(state,1),/phase incorrecte/);
});

test('Preuve issue des 2 cartes reçues; une seule carte révélée publiquement',()=>{
  let state=report(fractureStartPublicReportsV37(3),1,'resistance');
  const receivedCards=[cards[0],cards[30]];
  state=fractureResolveProofV37(state,{seat:1,proofId:cards[0].id,receivedCards});
  assert.deepEqual(state.usedProofSeats,[1]);
  assert.deepEqual(state.reports[0].proof,cards[0]);
  assert.equal(JSON.stringify(state).includes(cards[30].id),false);
  assert.ok(Object.isFrozen(state)&&Object.isFrozen(state.reports)&&Object.isFrozen(state.reports[0]));
  assert.deepEqual(Object.keys(state.reports[0]).sort(),['proof','report','seat']);
  assert.equal('receivedCards' in state,false);
});

test('refuser preuve étrangère, duplications de main, carte forgée, deuxième Preuve',()=>{
  const base=report(fractureStartPublicReportsV37(3),1);
  const args={seat:1,proofId:cards[0].id};
  assert.throws(()=>fractureResolveProofV37(base,args),/deux cartes/);
  assert.throws(()=>fractureResolveProofV37(base,{...args,receivedCards:[cards[1],cards[2]]}),/absente/);
  assert.throws(()=>fractureResolveProofV37(base,{...args,receivedCards:[cards[0],cards[0]]}),/absente/);
  assert.throws(()=>fractureResolveProofV37(base,{...args,receivedCards:[{...cards[0],points:99},cards[1]]}),/non officielle/);
  assert.throws(()=>fractureResolveProofV37(base,{seat:1,proofId:'fake',receivedCards:[cards[0],cards[1]]}),/invalide/);
  assert.throws(()=>fractureResolveProofV37(base,{seat:1,receivedCards:[cards[0],cards[1]]}),/sans Preuve/);
  const nextRound=report(fractureStartPublicReportsV37(3,{round:2,usedProofSeats:[1]}),1);
  assert.throws(()=>fractureResolveProofV37(nextRound,{...args,receivedCards:[cards[0],cards[1]]}),/déjà utilisée/);
  const declined=skip(nextRound,1);
  assert.equal(declined.nextSeat,2);
  assert.deepEqual(declined.usedProofSeats,[1]);
});

test('le registre des Preuves doit être sans doublons et dans les limites',()=>{
  assert.throws(()=>fractureStartPublicReportsV37(3,{usedProofSeats:[1,1]}),/dupliquées/);
  assert.throws(()=>fractureStartPublicReportsV37(3,{usedProofSeats:[4]}),/1 à 3/);
  assert.throws(()=>fractureStartPublicReportsV37(3,{round:11}),/1 à 10/);
  assert.throws(()=>fractureStartPublicReportsV37(12,{express:true}),/13 à 20/);
});

test('Solo/Duo : attribution du siège reste une obligation séparée du serveur',()=>{
  assert.equal(fractureSeatController(2,3,1,{duoFirst:1}),1);
  assert.equal(fractureSeatController(2,3,2,{duoFirst:1}),2);
  assert.equal(fractureSeatController(1,3,1),1);
  const state=fractureStartPublicReportsV37(2,{round:2});
  assert.equal('controller' in state,false);
  assert.equal('user_id' in state,false);
});

test('aucune main ni identité ni secret privé ne circule dans le résumé public',()=>{
  let state=fractureStartPublicReportsV37(2,{round:2,usedProofSeats:[2]});
  for(const seat of state.seatOrder)state=skip(report(state,seat,'equilibre'),seat);
  const serialized=JSON.stringify(state);
  for(const term of ['user_id','email','identity','password','session','access_token','receivedCards','hand']){
    assert.equal(serialized.includes(term),false,term);
  }
});
