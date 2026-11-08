import test from 'node:test';
import assert from 'node:assert/strict';
import {
  FRACTURE_AGENTS,FRACTURE_OPERATION_COUNTS,FRACTURE_FACTIONS,
  fractureSeats,fractureOperationDeck,fractureValidateDeck,
  fractureDealRound,fractureBuildCentre,fractureTwoPasses,
  fractureRevealOperationCards,fractureSeatController
} from '../../assets/js/sinjira-fracture-mechanics-v36.mjs';

const deck=fractureOperationDeck();
const kept=seats=>Array.from({length:seats},()=>[0,1]);
const selections=seats=>[
  Array.from({length:seats},()=>0),
  Array.from({length:seats},()=>0)
];

test('le paquet canonique contient 90 cartes uniques, 45 pour chaque faction',()=>{
  assert.deepEqual(FRACTURE_OPERATION_COUNTS,{1:30,2:12,3:3});
  assert.deepEqual(FRACTURE_FACTIONS,['resistance','reseau']);
  assert.equal(deck.length,90);
  assert.equal(new Set(deck.map(c=>c.id)).size,90);
  for(const faction of FRACTURE_FACTIONS){
    const cards=deck.filter(card=>card.faction===faction);
    assert.equal(cards.length,45);
    for(const points of [1,2,3]){
      assert.equal(cards.filter(card=>card.points===points).length,
        FRACTURE_OPERATION_COUNTS[points]);
    }
  }
  assert.equal(fractureValidateDeck([...deck].reverse()).length,90);
  assert.ok(Object.isFrozen(deck)&&Object.isFrozen(deck[0]));
});

test('règles officielles des 1 à 20 joueurs et des 3 sièges Solo/Duo',()=>{
  for(let humans=1;humans<=20;humans++){
    const cfg=fractureSeats(humans);
    assert.equal(cfg.seats,Math.max(humans,3));
    assert.equal(cfg.agents,FRACTURE_AGENTS[cfg.seats]);
    assert.equal(cfg.resistance+cfg.agents,cfg.seats);
    assert.equal(cfg.cardsDealt,cfg.seats*3);
    assert.equal(cfg.cardsCentre,cfg.seats*2);
    assert.equal(cfg.finalBallots,cfg.agents*humans);
    assert.equal(cfg.rounds,10);
    assert.equal(cfg.proofsMaximum,cfg.seats);
  }
  assert.equal(fractureSeats(1).finalBallots,1);
  assert.equal(fractureSeats(2).finalBallots,2);
  assert.equal(fractureSeats(20).finalBallots,140);
  for(let humans=13;humans<=20;humans++){
    assert.equal(fractureSeats(humans,{express:true}).rounds,6);
  }
  assert.throws(()=>fractureSeats(12,{express:true}),/13 à 20/);
  for(const invalid of [0,21,1.5,null,undefined,'',NaN,Infinity]){
    assert.throws(()=>fractureSeats(invalid));
  }
  assert.throws(()=>fractureSeats(3,{duoFirst:3}),/1 à 2/);
  assert.throws(()=>fractureSeats(3,{express:'true'}),/invalide/);
});

test('Solo : les trois sièges restent sous contrôle du seul humain',()=>{
  for(let round=1;round<=10;round++){
    for(let seat=1;seat<=3;seat++)
      assert.equal(fractureSeatController(1,seat,round),1);
  }
});

test('Duo : le siège invisible 3 alterne à chaque ronde, sans bot',()=>{
  for(let round=1;round<=10;round++){
    assert.equal(fractureSeatController(2,1,round,{duoFirst:1}),1);
    assert.equal(fractureSeatController(2,2,round,{duoFirst:1}),2);
    assert.equal(fractureSeatController(2,3,round,{duoFirst:1}),round%2?1:2);
    assert.equal(fractureSeatController(2,3,round,{duoFirst:2}),round%2?2:1);
  }
  assert.equal(fractureSeatController(20,20,6,{express:true}),20);
  assert.throws(()=>fractureSeatController(2,3,11),/1 à 10/);
});

test('une ronde distribue 3 cartes par siège et laisse le reste dans la pioche',()=>{
  for(let humans of [1,2,3,10,20]){
    const dealt=fractureDealRound(deck,humans);
    assert.equal(dealt.hands.length,Math.max(3,humans));
    assert.equal(dealt.hands.every(h=>h.cards.length===3),true);
    assert.equal(dealt.undealt.length,90-3*dealt.config.seats);
    assert.equal(new Set([...dealt.hands.flatMap(h=>h.cards),...dealt.undealt].map(c=>c.id)).size,90);
  }
  assert.throws(()=>fractureDealRound(deck,3,{round:11}),/1 à 10/);
  assert.throws(()=>fractureDealRound(deck,13,{express:true,round:7}),/1 à 6/);
});

test('conservation 2 cartes et défausse 1 carte par siège : centre strictement 2N',()=>{
  for(let humans of [1,2,3,5,20]){
    const deal=fractureDealRound(deck,humans);
    const built=fractureBuildCentre(deal,kept(deal.config.seats));
    assert.equal(built.center.length,2*deal.config.seats);
    assert.equal(built.discard.length,deal.config.seats);
    assert.equal(new Set([...built.center,...built.discard].map(c=>c.id)).size,3*deal.config.seats);
  }
});

test('aucune carte ne peut être conservée deux fois, omise ou inventée',()=>{
  const d=fractureDealRound(deck,3);
  assert.throws(()=>fractureBuildCentre(d,[[0,0],[0,1],[0,1]]),/distinctes/);
  assert.throws(()=>fractureBuildCentre(d,[[0,3],[0,1],[0,1]]),/0 à 2/);
  assert.throws(()=>fractureBuildCentre(d,[[0,1],[0,1]]),/incompatibles/);
  const duplicated=[...deck];duplicated[1]=duplicated[0];
  assert.throws(()=>fractureValidateDeck(duplicated),/deux fois/);
  assert.throws(()=>fractureValidateDeck(deck.slice(1)),/90 requises/);
  const corrupted=[...deck];
  corrupted[0]={...corrupted[0],points:3};
  assert.throws(()=>fractureValidateDeck(corrupted),/officielles/);
});

test('deux passages : un choix par siège et par passage, aucun reste',()=>{
  for(let humans of [1,2,3,10,20]){
    const deal=fractureDealRound(deck,humans);
    const center=fractureBuildCentre(deal,kept(deal.config.seats));
    const distribution=fractureTwoPasses(center.center,selections(deal.config.seats),deal.config.seats);
    assert.equal(distribution.remaining.length,0);
    assert.equal(distribution.hands.length,deal.config.seats);
    assert.equal(distribution.hands.every(h=>h.cards.length===2),true);
    assert.equal(new Set(distribution.hands.flatMap(h=>h.cards).map(c=>c.id)).size,
      deal.config.cardsCentre);
  }
});

test('les deux passages rejettent tout passage manquant ou choix incorrect',()=>{
  const deal=fractureDealRound(deck,3);
  const center=fractureBuildCentre(deal,kept(3));
  assert.throws(()=>fractureTwoPasses(center.center,[[0,0,0]],3),/deux passages/);
  assert.throws(()=>fractureTwoPasses(center.center,[[0,0,0],[0,0]],3),/deux passages/);
  assert.throws(()=>fractureTwoPasses(center.center,[[0,0,99],[0,0,0]],3),/0 à/);
  assert.throws(()=>fractureTwoPasses(center.center.slice(1),selections(3),3),/6 requises/);
});

test('les cartes Opération révélées marquent pour leur faction imprimée',()=>{
  const deal=fractureDealRound(deck,3);
  const center=fractureBuildCentre(deal,kept(3));
  const distributed=fractureTwoPasses(center.center,selections(3),3);
  const revealed=fractureRevealOperationCards(distributed);
  assert.deepEqual(revealed,{
    seats:3,scoredCards:6,resistance:6,reseau:0,winner:'resistance'
  });
  // Permuter la faction du siège n'existe pas dans cette API.
  assert.equal('identity' in revealed,false);
  assert.equal('user_id' in revealed,false);
});

test('la révélation refuse les duplications de cartes ou sièges incomplets',()=>{
  const deal=fractureDealRound(deck,3);
  const center=fractureBuildCentre(deal,kept(3));
  const distribution=fractureTwoPasses(center.center,selections(3),3);
  const hands=distribution.hands.map(x=>({seat:x.seat,cards:[...x.cards]}));
  hands[0].cards[1]=hands[0].cards[0];
  assert.throws(()=>fractureRevealOperationCards({hands,seats:3}),/deux fois/);
  hands[0].cards=[deck[0]];
  assert.throws(()=>fractureRevealOperationCards({hands,seats:3}),/deux cartes/);
});

test('aucune identité secrète, compte ou message personnel n’apparaît dans les objets',()=>{
  const deal=fractureDealRound(deck,3);
  const center=fractureBuildCentre(deal,kept(3));
  const distribution=fractureTwoPasses(center.center,selections(3),3);
  const data=JSON.stringify({deal,center,distribution});
  for(const privateKey of ['user_id','auth','email','token','final_identity',
      'access_token','api_key','password']){
    assert.equal(data.includes(privateKey),false,privateKey);
  }
});
