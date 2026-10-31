'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.join(__dirname,'..');
const src=fs.readFileSync(path.join(root,'assets/js/sinjira-security-center-v24-4-98.js'),'utf8');
const helpers=fs.readFileSync(path.join(root,'assets/js/sinjira-supabase.js'),'utf8');
const esc=helpers.match(/^export function escapeHtml\(v=''\)\{[^\n]+\}/m);
assert.ok(esc,'Échappement partagé non trouvé');
function fnSource(name){
  const start=src.indexOf('function '+name+'(');
  assert.ok(start>=0,'Fonction absente : '+name);
  const next=src.indexOf('\nfunction ',start+1);
  assert.ok(next>start,'Fonction non bornée : '+name);
  return src.slice(start,next);
}
function draw(name,...args){
  const element={innerHTML:''};
  const program=[esc[0].replace(/^export /,''),fnSource('pill'),fnSource('empty'),
    fnSource(name),'const formatDate=v=>String(v||"");','return '+name+';'].join('\n');
  const fn=vm.runInNewContext('(function(){'+program+'})()',{qs:()=>element,Date});
  fn(...args);return element.innerHTML;
}
const malicious='" autofocus onfocus="alert(1)"><svg onload=alert(2)>';
function checkAttr(html,action){
  const result=html.match(new RegExp('data-'+action+'="([^"]*)"'));
  assert.ok(result,'Attribut attendu : '+action);
  assert.ok(result[1].includes('&quot;'),'Double quote brute dans '+action);
  assert.ok(result[1].includes('&lt;svg'),'Ouverture HTML brute dans '+action);
  assert.doesNotMatch(html,/"\s+autofocus\s+onfocus\s*=/);
  assert.doesNotMatch(html,/<svg\s+onload=/);
}
test('appareils : identifiants et boutons sécurisés',()=>{
  const html=draw('renderDevices',[
    {id:malicious,is_current:true,is_trusted:true,is_primary:false,revoked_at:null,
      display_name:'<img src=x onerror=alert(3)>',platform:'web'},
    {id:malicious,is_current:false,is_trusted:false,is_primary:false,revoked_at:null}
  ]);
  for(const a of ['device-id','device-primary','device-untrust','device-revoke'])checkAttr(html,a);
  assert.doesNotMatch(html,/<img\s+src=x/);
});
test('appareil non fiable : bouton de confiance sécurisé',()=>{
  checkAttr(draw('renderDevices',[{id:malicious,is_current:true,is_trusted:false,
    revoked_at:null}]),'device-trust');
});
test('voyage : id et contenu contrôlés',()=>{
  const html=draw('renderTravel',[{id:malicious,status:'active',
    destinations:['<svg onload=alert(5)>'],starts_at:'2026-01-01',ends_at:'2026-12-31'}]);
  checkAttr(html,'travel-cancel');assert.doesNotMatch(html,/<svg\s+onload/);
});
test('défis multi-appareils : autoriser/refuser sécurisés',()=>{
  const html=draw('renderChallenges',[
    {id:malicious,request_device_id:'other',status:'pending',
      expires_at:'2099-12-31T00:00:00Z',display_code:'<svg onload=alert(6)>'}
  ],[{id:'current',is_current:true,is_trusted:true,revoked_at:null}]);
  checkAttr(html,'challenge-approve');checkAttr(html,'challenge-deny');
  assert.doesNotMatch(html,/<svg\s+onload/);
});
