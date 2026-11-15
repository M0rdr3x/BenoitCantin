import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {inspectSectorRegister} from '../scripts/validate_nova_sinjira_sector_evidence_20261112.mjs';

const original=JSON.parse(readFileSync(new URL('../projets/projet-nova/data/registre-donnees-services-nova-sinjira.json',import.meta.url),'utf8'));
const copy=()=>structuredClone(original);
test('14 secteurs existants, identifiants NV-01..NV-14 en ordre',()=>{
  const x=inspectSectorRegister(copy());
  assert.equal(x.validStructure,true,x.errors.join('\n'));
  assert.equal(x.totals.sectors,14);
  assert.deepEqual(x.sectors.map(s=>s.id),
    Array.from({length:14},(_,i)=>`NV-${String(i+1).padStart(2,'0')}`));
});
test('pas de taux global ni de date fictive lorsque les preuves manquent',()=>{
  const x=inspectSectorRegister(copy());
  assert.equal(x.global_completion_percent,null);
  assert.equal(x.delivery_date,null);
  assert.equal(x.totals.with_precise_source,0);
  assert.equal(x.totals.with_costing_validated,0);
  assert.equal(x.totals.with_staffing_validated,0);
  assert.equal(x.totals.with_complete_documentary_inputs,0);
  assert.ok(x.sectors.every(s=>s.decision==='NON_HOMOLOGUE'));
});
test('registre à 13 secteurs déclenche un défaut structurel, pas 13/14 de complétude',()=>{
  const d=copy();d.dossiers.pop();
  const x=inspectSectorRegister(d);
  assert.equal(x.validStructure,false);
  assert.match(x.errors.join(' '),/exactement 14/);
  assert.equal(x.global_completion_percent,null);
});
test('identifiants dupliqués ne deviennent pas de faux dossiers validés',()=>{
  const d=copy();d.dossiers[3].id='NV-02';
  const x=inspectSectorRegister(d);
  assert.equal(x.validStructure,false);
  assert.match(x.errors.join(' '),/double/);
});
test('source éventuelle ou URL de départ n’est pas une source précise validée',()=>{
  const d=copy();const s=d.dossiers[0];
  s.adresses_de_depart=['https://exemple.org/public'];
  s.sources_institutionnelles_possibles=['Organisme fictif'];
  const x=inspectSectorRegister(d);
  assert.equal(x.validStructure,true);
  assert.equal(x.sectors[0].source_precise,false);
  assert.equal(x.sectors[0].documentary_complete,false);
});
test('chiffrage coché validé avec coûts nuls est refusé',()=>{
  const d=copy();d.dossiers[0].chiffrage_valide=true;
  const x=inspectSectorRegister(d);
  assert.equal(x.validStructure,false);
  assert.match(x.errors.join(' '),/chiffrage déclaré validé/);
});
test('validation du personnel sans jeu de données identifié est refusée',()=>{
  const d=copy();d.dossiers[0].affectation_personnel_validee=true;
  const x=inspectSectorRegister(d);
  assert.equal(x.validStructure,false);
  assert.match(x.errors.join(' '),/affectation personnelle/);
});
test('un secteur avec tous champs fournis n’est jamais déclaré prêt à lancer',()=>{
  const d=copy(),s=d.dossiers[0];
  for(const f of ['source_de_jeu_de_donnees_precis','date_valeur',
    'periode_observation','territoire','population','nombre_unites','annee_de_prix'])
    s[f]='FICTIF-POUR-TEST';
  for(const mode of Object.keys(s.couts_par_mode))
    s.couts_par_mode[mode]={unite:'CAD fictifs',valeur:1};
  s.qualite_verifiee=true;s.chiffrage_valide=true;s.affectation_personnel_validee=true;
  const x=inspectSectorRegister(d);
  assert.equal(x.validStructure,true,x.errors.join(' '));
  assert.equal(x.sectors[0].documentary_complete,true);
  assert.equal(x.sectors[0].decision,'NON_HOMOLOGUE');
  assert.equal(x.global_completion_percent,null);
});
