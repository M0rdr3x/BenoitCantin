import test from 'node:test';
import assert from 'node:assert/strict';
import { cloudRevisionDecision } from '../assets/js/sinjira-liseuse-position-v31.mjs';

// V51.5 : les vrais appareils peuvent avoir des horloges contradictoires.
// La révision monotone serveur, et jamais la date locale, pilote le rejeu.
test('V51.5 : première sauvegarde sans ligne => CAS initial autorisé',()=>{
  assert.equal(cloudRevisionDecision(null,null),'current');
});
test('V51.5 : les deux appareils à revision 0 ne créent pas une deuxième ligne',()=>{
  assert.equal(cloudRevisionDecision(null,{revision:0}),'conflict');
  assert.equal(cloudRevisionDecision(0,null),'conflict');
});
test('V51.5 : même révision => tenter RPC atomique, aucune dépendance à une date',()=>{
  assert.equal(cloudRevisionDecision(0,{revision:0,updated_at:'2099-01-01'}),'current');
  assert.equal(cloudRevisionDecision(7,{revision:'7',updated_at:'1900-01-01'}),'current');
  assert.equal(cloudRevisionDecision(7,{revision:7,updated_at:'invalid'}),'current');
});
test('V51.5 : une révision concurrente bloque le rejeu sans écraser le compte',()=>{
  assert.equal(cloudRevisionDecision(0,{revision:1}),'conflict');
  assert.equal(cloudRevisionDecision(6,{revision:7}),'conflict');
  assert.equal(cloudRevisionDecision(9,{revision:8}),'conflict');
});
test('V51.5 : refuser les états malformés ou absents, fail closed',()=>{
  for(const remote of [undefined,false,0,{}, {revision:null},
    {revision:undefined},{revision:-1},{revision:1.2},{revision:''},
    {revision:'NaN'},{revision:'99999999999999999999999999'}]){
    assert.equal(cloudRevisionDecision(0,remote),'invalid');
  }
  for(const expected of [undefined,false,-1,1.2,'', 'NaN',
    '99999999999999999999999999']){
    assert.equal(cloudRevisionDecision(expected,{revision:0}),'invalid');
  }
});
test('V51.5 : numéro sûr accepté, format bigint non sûr refusé',()=>{
  assert.equal(cloudRevisionDecision(Number.MAX_SAFE_INTEGER,
    {revision:String(Number.MAX_SAFE_INTEGER)}),'current');
  assert.equal(cloudRevisionDecision(Number.MAX_SAFE_INTEGER+1,
    {revision:String(Number.MAX_SAFE_INTEGER+1)}),'invalid');
});
