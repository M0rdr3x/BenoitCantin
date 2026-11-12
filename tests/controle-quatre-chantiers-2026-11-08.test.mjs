import test from 'node:test';
import assert from 'node:assert/strict';
import {assess,load} from '../scripts/controle-quatre-chantiers-2026-11-08.mjs';

const original=load();
const copy=()=>structuredClone(original);
test('bilan de référence : cinq métriques non assimilables',()=>{
  const r=assess(copy());
  assert.equal(r.policy_programme.progress_percent,47);
  assert.equal(r.policy_programme.finances_points,3);
  assert.equal(r.public_services.autonomous_completion_percent,null);
  assert.equal(r.electoral_compass.reception_percent,75);
  assert.equal(r.citizen_poll.reception_percent,54.5);
  assert.equal(r.sinjira_platform.maturity_estimate_percent,66.5);
  assert.equal(r.sinjira_platform.uncertainty_percentage_points,10);
  assert.equal(r.sinjira_platform.launch_gates_open,13);
});
test('aucune date de fin certifiée, ni activation publique présumée',()=>{
  const r=assess(copy());
  assert.equal(r.policy_programme.finish_date_certified,null);
  assert.equal(r.public_services.finish_date_certified,null);
  assert.equal(r.electoral_compass.finish_date_certified,null);
  assert.equal(r.citizen_poll.finish_date_certified,null);
  assert.equal(r.sinjira_platform.finish_date_certified,null);
  assert.equal(r.citizen_poll.publicly_open,false);
  assert.equal(r.electoral_compass.party_comparison_enabled,false);
  assert.equal(r.sinjira_platform.launch_approved,false);
});
test('rejette une inflation du 47% par la qualité de la documentation',()=>{
  const x=copy();x.nova.scoring.percentage=75;
  assert.throws(()=>assess(x),/47\/100 incohérent/);
});
test('rejette les changements de score financier non conciliés',()=>{
  const x=copy();x.nova.dimensions.find(d=>d.id==='FINANCES').points=16;
  assert.throws(()=>assess(x),/47\/100 incohérent/);
});
test('rejette un secteur fictif ajouté aux 14',()=>{
  const x=copy();x.services.dossiers.push({...x.services.dossiers[0],id:'NV-15'});
  assert.throws(()=>assess(x),/14 secteurs attendus/);
});
test('rejette un doublon de secteur',()=>{
  const x=copy();x.services.dossiers[1].id=x.services.dossiers[0].id;
  assert.throws(()=>assess(x),/dossiers dupliqués/);
});
test('rejette les validations documentaires artificielles des partis',()=>{
  const x=copy();x.civic.compass.comparison_enabled=true;
  assert.throws(()=>assess(x),/comparateur non homologué/);
});
test('rejette les portes de boussole artificiellement passées',()=>{
  const x=copy();x.civic.compass.gates.find(g=>g.status==='PENDING').status='PASSED';
  assert.throws(()=>assess(x),/résultats de réception historique/);
});
test('rejette l’ouverture imaginaire du sondage',()=>{
  const x=copy();x.civic.poll.published_in_source=true;
  assert.throws(()=>assess(x),/sondage non autorisé/);
});
test('rejette un GO de plateforme inexistant',()=>{
  const x=copy();x.sinjira.launch.approved=true;
  assert.throws(()=>assess(x),/lancement ou date certifiés/);
});
test('rejette une échéance de livraison SINJIRA inventée',()=>{
  const x=copy();x.sinjira.forecast.estimated_completion_date='2027-01-01';
  assert.throws(()=>assess(x),/lancement ou date certifiés/);
});
test('rejette la fermeture d’une porte P0 sans réception',()=>{
  const x=copy();x.sinjira.gates[0].status='PASSED';
  assert.throws(()=>assess(x),/13 portes ouvertes/);
});
test('rejette un poids de maturité SINJIRA falsifié',()=>{
  const x=copy();x.sinjira.domains[0].maturity=100;
  assert.throws(()=>assess(x),/66,5 pondéré/);
});
