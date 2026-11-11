import test from 'node:test';
import assert from 'node:assert/strict';
import {buildBaseline} from '../scripts/validate_quatre_programmes_baseline_20261110.mjs';

const data=buildBaseline();
test('Nova: 47 points provisoires sur 100, finances 3/16',()=>{
 assert.deepEqual([data.political.percent,data.political.max],[47,100]);
 assert.deepEqual(data.political.finance,{earned:3,max:16});
 assert.equal(data.political.method,'provisional_internal_weighted_audit');
});
test('Nova: le 31 décembre 2027 reste une cible conditionnelle',()=>{
 assert.equal(data.political.completion_target,'2027-12-31');
 assert.equal(data.political.completion_target_conditional,true);
});
test('Services Nova–Sinjira: 14 secteurs, jamais de taux global inventé',()=>{
 assert.equal(data.public_services.sectors,14);
 assert.equal(data.public_services.percent,null);
 assert.equal(data.public_services.completion_date,null);
 assert.ok(data.public_services.missingValidatedSectorEvidence>0);
});
test('Boussole: 9/12 critères, 75 %',()=>{
 assert.deepEqual([data.electoral_compass.passed,data.electoral_compass.total,
 data.electoral_compass.percent,data.electoral_compass.remaining],[9,12,75,3]);
 assert.equal(data.electoral_compass.approved,false);
});
test('Sondage: 6/11 critères, 54,5 %, encore fermé',()=>{
 assert.deepEqual([data.civic_poll.passed,data.civic_poll.total,
 data.civic_poll.percent,data.civic_poll.remaining],[6,11,54.5,5]);
 assert.equal(data.civic_poll.approved,false);
});
test('SINJIRA: 66,5 % pondéré ±10 points et 13 portes OPEN',()=>{
 assert.equal(data.sinjira.percent,66.5);
 assert.equal(data.sinjira.uncertainty_points,10);
 assert.deepEqual([data.sinjira.gates_open,data.sinjira.gates_total],[13,13]);
 assert.equal(data.sinjira.approved,false);
});
test('SINJIRA: aucune date de fin inventée',()=>{
 assert.equal(data.sinjira.completion_date,null);
});
test('référence temporelle distincte de la date de production',()=>{
 assert.equal(data.reference_date,'2026-11-08');
 assert.equal(data.audit_date,'2026-11-05');
});
