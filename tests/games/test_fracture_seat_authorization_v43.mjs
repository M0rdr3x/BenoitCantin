import test from 'node:test';
import assert from 'node:assert/strict';
import {
  fractureAuthorizeSeatActionV43 as seatAction,
  fractureAuthorizeHumanBallotV43 as ballot
} from '../../assets/js/sinjira-fracture-seat-authorization-v43.mjs';

const action=(humans,actorHumanSeat,targetSeat,round=1,extra={})=>({
  humans,actorHumanSeat,targetSeat,round,action:'keep',...extra
});
const vote=(humans,actorHumanSeat,ballotSeat,extra={})=>({
  humans,actorHumanSeat,ballotSeat,action:'final-accusation',...extra
});

test('Solo : un seul humain contrôle exactement les trois sièges',()=>{
  for(const seat of [1,2,3]){
    const r=seatAction(action(1,1,seat));
    assert.equal(r.humanSeat,1);
    assert.equal(r.targetSeat,seat);
    assert.equal(r.isInvisible,seat>1);
  }
});
test('Duo : siège 3 contrôlé en alternance par humain 1 puis humain 2',()=>{
  for(let round=1;round<=10;round++){
    const controller=round%2?1:2;
    assert.equal(seatAction(action(2,controller,3,round)).humanSeat,controller);
    assert.throws(()=>seatAction(action(2,3-controller,3,round)),/SEAT_NOT_CONTROLLED/);
  }
});
test('Duo : premier joueur 2 inverse le contrôle des rondes',()=>{
  for(let round=1;round<=10;round++){
    const controller=round%2?2:1;
    assert.equal(seatAction(action(2,controller,3,round,{duoFirst:2})).humanSeat,controller);
    assert.throws(()=>seatAction(action(2,3-controller,3,round,{duoFirst:2})),/SEAT_NOT_CONTROLLED/);
  }
});
test('Duo : chacun conserve son siège propre chaque ronde',()=>{
  for(let round=1;round<=10;round++){
    for(let human=1;human<=2;human++){
      assert.equal(seatAction(action(2,human,human,round)).targetSeat,human);
      assert.throws(()=>seatAction(action(2,3-human,human,round)),/SEAT_NOT_CONTROLLED/);
    }
  }
});
test('De 3 à 20 humains : nul ne contrôle un autre siège',()=>{
  for(const humans of [3,4,13,20]){
    for(let seat=1;seat<=humans;seat++){
      assert.equal(seatAction(action(humans,seat,seat)).allowed,true);
      assert.throws(()=>seatAction(action(humans,(seat%humans)+1,seat)),/SEAT_NOT_CONTROLLED/);
    }
  }
});
test('Express : six rondes et contrôle humain des sièges uniquement',()=>{
  const allowed=seatAction(action(13,13,13,6,{express:true,action:'pick'}));
  assert.equal(allowed.round,6);
  assert.throws(()=>seatAction(action(13,13,13,7,{express:true})),/Ronde/);
  assert.throws(()=>seatAction(action(12,12,12,1,{express:true})),/13 à 20/);
});
test('Les quatre actions privées permises reposent sur la même garde',()=>{
  for(const name of ['keep','pick','report','proof']){
    const r=seatAction(action(1,1,3,3,{action:name}));
    assert.equal(r.action,name);
  }
  for(const value of [null,'start','final-accusation',undefined,{},0]){
    assert.throws(()=>seatAction(action(1,1,3,1,{action:value})),/Action de siège invalide/);
  }
});
test('Les numéros forgés ou conversions implicites sont refusés',()=>{
  for(const changes of [
    {humans:'2'}, {humans:0}, {humans:21}, {humans:null},
    {actorHumanSeat:'1'}, {actorHumanSeat:0}, {actorHumanSeat:2},
    {targetSeat:'3'}, {targetSeat:4}, {targetSeat:0},
    {round:'1'}, {round:0}, {round:11}, {duoFirst:'1'}, {duoFirst:3},
    {express:'true'}
  ]){
    assert.throws(()=>seatAction(action(1,1,2,1,changes)));
  }
});
test('Bulletins : Solo n a qu un auteur humain, même avec 3 sièges',()=>{
  for(const kind of ['suspicion','final-accusation']){
    const r=ballot(vote(1,1,1,{action:kind}));
    assert.equal(r.allowed,true);
    assert.equal(r.ballotSeat,1);
    for(const invisible of [2,3]){
      assert.throws(()=>ballot(vote(1,1,invisible,{action:kind})),/BALLOT_NOT_OWNED/);
    }
  }
});
test('Bulletins : Duo, siège invisible jamais auteur',()=>{
  for(const human of [1,2]){
    assert.equal(ballot(vote(2,human,human)).allowed,true);
    assert.throws(()=>ballot(vote(2,human,3)),/BALLOT_NOT_OWNED/);
    assert.throws(()=>ballot(vote(2,human,3-human)),/BALLOT_NOT_OWNED/);
  }
});
test('Bulletins : tout humain doit déposer son propre bulletin',()=>{
  for(const humans of [3,10,20]){
    for(let seat=1;seat<=humans;seat++){
      assert.equal(ballot(vote(humans,seat,seat)).ballotSeat,seat);
      assert.throws(()=>ballot(vote(humans,seat,(seat%humans)+1)),/BALLOT_NOT_OWNED/);
    }
  }
});
test('Bulletins : type explicite et paramètres stricts',()=>{
  assert.throws(()=>ballot(vote(1,1,1,{action:'report'})),/Type de bulletin/);
  assert.throws(()=>ballot(vote(2,1,1,{action:undefined})),/Type de bulletin/);
  assert.throws(()=>ballot(vote(2,1,'1')),/entier/);
  assert.throws(()=>ballot(vote('2',1,1)),/Humains/);
  assert.throws(()=>ballot(vote(2,0,1)),/Siège humain/);
  assert.throws(()=>ballot(vote(2,1,4)),/Auteur du bulletin/);
});
test('Sorties figées : aucun compte, identité, faction, main ou secret',()=>{
  const outputs=[seatAction(action(1,1,3)),ballot(vote(1,1,1))];
  for(const item of outputs){
    assert.ok(Object.isFrozen(item));
    const data=JSON.stringify(item);
    for(const field of [
      'user_id','party_id','jwt','auth','email','secret','identity',
      'faction','cards','hand','access_token','session_id'
    ]){
      assert.equal(data.includes(field),false,field);
    }
  }
});
