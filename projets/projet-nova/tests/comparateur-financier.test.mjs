import {test} from "node:test";
import assert from "node:assert/strict";
import {ALL_FIELDS, comparerScenarios, evaluerScenario} from "../assets/comparateur-financier-core.mjs";
const zeros = () => Object.fromEntries(ALL_FIELDS.map(f => [f, 0]));
test("aucune économie inventée sur deux scénarios identiques", () => {
  const a = zeros(); a.paiementPublic=100; a.ressourcesReelles=95;
  const r = comparerScenarios(10,a,{...a});
  assert.equal(r.deltaPublicAnnuel,0);assert.equal(r.deltaSocialAnnuel,0);
  assert.equal(r.statut,"SIMULATION_NON_CERTIFIEE");
});
test("coût des ressources distinct des paiements : exemple purement synthétique", () => {
  const a=zeros();
  Object.assign(a,{paiementPublic:120,administrationPublique:5,coutAvalPublic:7,ressourcesReelles:90,capitalAnnualise:10,fraisUsagers:3,tempsProches:4,transitionAnnuelle:50,reserveAnnuelle:30});
  const r=evaluerScenario(100,a);
  assert.equal(r.coutPublicAnnuel,13280);
  assert.equal(r.coutSocialAnnuel,11980);
});
test("refuse montants absents, négatifs, non numériques, volume zéro", () => {
  assert.throws(()=>evaluerScenario(10,{}));
  assert.throws(()=>evaluerScenario(10,{...zeros(),fraisUsagers:-1}));
  assert.throws(()=>evaluerScenario(10,{...zeros(),paiementPublic:NaN}));
  assert.throws(()=>evaluerScenario(0,zeros()));
});
test("des frais déplacés aux usagers ne sont pas une économie sociale", () => {
  const a=zeros();Object.assign(a,{paiementPublic:100,ressourcesReelles:100});
  const b=zeros();Object.assign(b,{paiementPublic:90,ressourcesReelles:100,fraisUsagers:30});
  const r=comparerScenarios(100,a,b);
  assert.equal(r.deltaPublicAnnuel,-1000);
  assert.equal(r.deltaSocialAnnuel,3000);
});
test("ne confond pas coût fixe annuel et coût par acte", () => {
  const a=zeros();a.transitionAnnuelle=1000;
  const r=evaluerScenario(100,a);
  assert.equal(r.coutPublicAnnuel,1000);assert.equal(r.coutPublicMoyen,10);
});
