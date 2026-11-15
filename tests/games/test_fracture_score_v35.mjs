import test from 'node:test';
import assert from 'node:assert/strict';
import {
  fractureConfiguration,fractureRound,fractureScore,
  RESEAU_AGENTS,POINTS_PAR_ACCUSATION,CARTES_PAR_FACTION
} from '../../assets/js/sinjira-fracture-score-v35.mjs';

test('configuration officielle pour 1 à 20 humains, dont 3 sièges en Solo / Duo',()=>{
  for(let humans=1;humans<=20;humans++){
    const cfg=fractureConfiguration(humans);
    assert.equal(cfg.humans,humans);
    assert.equal(cfg.seats,Math.max(3,humans));
    assert.equal(cfg.agents,RESEAU_AGENTS[cfg.seats]);
    assert.equal(cfg.resistance+cfg.agents,cfg.seats);
    assert.equal(cfg.dealtCards,3*cfg.seats);
    assert.equal(cfg.centralCards,2*cfg.seats);
    assert.equal(cfg.ballots,humans*cfg.agents);
    assert.equal(cfg.rounds,10);
    assert.ok(cfg.maxRoundPoints<=6*cfg.seats);
    assert.ok(cfg.maxRoundPoints>=2*cfg.seats);
    assert.equal(cfg.minRoundPoints,2*cfg.seats);
  }
  assert.equal(fractureConfiguration(1).ballots,1);
  assert.equal(fractureConfiguration(2).ballots,2);
  assert.equal(fractureConfiguration(20).ballots,140);
  assert.equal(fractureConfiguration(20).maxRoundPoints,76);
  assert.deepEqual(CARTES_PAR_FACTION,{unPoint:30,deuxPoints:12,troisPoints:3});
});
test('format Express limité à 13 à 20 humains et 6 rondes',()=>{
  for(let humans=13;humans<=20;humans++){
    assert.equal(fractureConfiguration(humans,{express:true}).rounds,6);
  }
  assert.throws(()=>fractureConfiguration(12,{express:true}),/13 à 20/);
  for(const value of [0,21,2.5,null,undefined,'',NaN,Infinity]){
    assert.throws(()=>fractureConfiguration(value));
  }
  assert.throws(()=>fractureConfiguration(3,{express:'oui'}),/invalide/);
});
test('toutes les 2N cartes marquent entre 2N et 6N points en règle standard',()=>{
  const cfg=fractureConfiguration(5);
  assert.deepEqual(fractureRound(cfg,{resistance:10,reseau:0}),{
    resistance:10,reseau:0,total:10,winningFaction:'resistance'
  });
  assert.equal(fractureRound(cfg,{resistance:13,reseau:13}).total,26);
  assert.equal(fractureRound(cfg,{resistance:13,reseau:13}).winningFaction,'egalite');
  assert.equal(fractureRound(cfg,{resistance:10,reseau:11}).winningFaction,'reseau');
  assert.throws(()=>fractureRound(cfg,{resistance:0,reseau:9}),/Total impossible/);
  assert.throws(()=>fractureRound(cfg,{resistance:16,reseau:15}),/Total impossible/);
  assert.throws(()=>fractureRound(fractureConfiguration(20),{resistance:75,reseau:0}),/Scores impossibles/);
  assert.equal(fractureRound(fractureConfiguration(20),{resistance:58,reseau:0}).total,58);
  assert.throws(()=>fractureRound(cfg,{resistance:-1,reseau:11}),/entier/);
  assert.throws(()=>fractureRound(cfg,{resistance:2.5,reseau:10}),/entier/);
  assert.throws(()=>fractureRound(cfg,{resistance:'',reseau:10}),/requis/);
});
test('inachevé puis 10 rondes : pas de vainqueur ni de bonus prématuré',()=>{
  const rounds=Array.from({length:9},()=>({resistance:3,reseau:3}));
  const pending=fractureScore({humans:3,rounds});
  assert.equal(pending.status,'incomplete');
  assert.equal(pending.played,9);
  assert.equal(pending.bonus,null);
  assert.equal(pending.winner,null);
  rounds.push({resistance:3,reseau:3});
  const awaiting=fractureScore({humans:3,rounds});
  assert.equal(awaiting.status,'awaiting-accusations');
  assert.equal(awaiting.operation.resistance,30);
  assert.equal(awaiting.operation.reseau,30);
});
test('accusations humaines à 3 points, aucun vote de siège invisible',()=>{
  const rounds=Array.from({length:10},()=>({resistance:3,reseau:3}));
  const finished=fractureScore({humans:1,rounds,correct:1,incorrect:0});
  assert.equal(POINTS_PAR_ACCUSATION,3);
  assert.equal(finished.config.seats,3);
  assert.equal(finished.config.ballots,1);
  assert.deepEqual(finished.bonus,{resistance:3,reseau:0});
  assert.deepEqual(finished.totals,{resistance:33,reseau:30});
  assert.equal(finished.winner,'resistance');
  assert.throws(()=>fractureScore({humans:1,rounds,correct:1,incorrect:1}),/exactement 1/);
});
test('bonifications fausses et victoire du Réseau-Mère',()=>{
  const rounds=Array.from({length:10},()=>({resistance:3,reseau:3}));
  const result=fractureScore({humans:3,rounds,correct:1,incorrect:2});
  assert.deepEqual(result.bonus,{resistance:3,reseau:6});
  assert.equal(result.winner,'reseau');
  assert.equal(result.status,'finished');
});
test('égalité de points départagée par le nombre de rondes gagnées',()=>{
  const rounds=[
    {resistance:3,reseau:6},
    ...Array.from({length:9},()=>({resistance:3,reseau:3}))
  ];
  const result=fractureScore({humans:3,rounds,correct:2,incorrect:1});
  assert.deepEqual(result.totals,{resistance:36,reseau:36});
  assert.deepEqual(result.roundWins,{resistance:0,reseau:1});
  assert.equal(result.winner,'reseau');
});
test('égalité persistante exige une ronde de départage sans nouveau bonus',()=>{
  const rounds=[
    {resistance:4,reseau:3},
    {resistance:2,reseau:6},
    ...Array.from({length:8},()=>({resistance:3,reseau:3}))
  ];
  const result=fractureScore({humans:3,rounds,correct:2,incorrect:1});
  assert.deepEqual(result.totals,{resistance:36,reseau:36});
  assert.deepEqual(result.roundWins,{resistance:1,reseau:1});
  assert.equal(result.winner,null);
  assert.equal(result.status,'tie-breaker');
});
test('arrondis, dates, identités et noms absents du résultat',()=>{
  const rounds=Array.from({length:10},()=>({resistance:3,reseau:3}));
  const result=fractureScore({humans:2,rounds,correct:2,incorrect:0});
  const json=JSON.stringify(result);
  for(const secret of ['user_id','email','identity','vote','token','name']){
    assert.equal(json.includes(secret),false);
  }
});
test('rejet des comptes incomplets, des totaux hors limites et des rondes excessives',()=>{
  const rounds=Array.from({length:10},()=>({resistance:3,reseau:3}));
  assert.throws(()=>fractureScore({humans:3,rounds,correct:2,incorrect:null}),/requis/);
  assert.throws(()=>fractureScore({humans:3,rounds,correct:1,incorrect:1}),/exactement 3/);
  assert.throws(()=>fractureScore({humans:3,rounds:[...rounds,...rounds]}),/incompatible/);
  assert.throws(()=>fractureScore({humans:3,rounds:'nope'}),/incompatible/);
});
