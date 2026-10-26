'use strict';
// Test statique et dynamique des gardes privés, sans réseau ni donnée utilisateur.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.join(__dirname,'..','supabase','functions');
for (const name of ['conscience-vault','personal-ai']) {
  test(name+': aucun signal géographique issu d’un en-tête client',()=>{
    const code=fs.readFileSync(path.join(root,name,'index.ts'),'utf8');
    const start=code.indexOf('function trustedGeo(_req: Request) {');
    assert.ok(start>=0,'garde de géolocalisation absente');
    const end=code.indexOf('\n}',start);
    assert.ok(end>start,'garde géographique non bornée');
    const body=code.slice(start,end+2).replace('_req: Request','_req');
    const geo=new Function(body+'\nreturn trustedGeo;')();
    for(const hdr of [
      {'cf-ipcountry':'US','x-sinjira-region':'region-admin','x-forwarded-for':'127.0.0.1'},
      {'cf-ipcountry':'CA','x-sinjira-region':'QC'},
      {}
    ]) {
      assert.deepEqual(geo({headers:new Headers(hdr)}),{country:null,region:null});
    }
    assert.doesNotMatch(code,/headers\.get\(['"](?:cf-ipcountry|x-sinjira-region)['"]\)/);
    assert.doesNotMatch(code,/SINJIRA_TRUST_GEO_HEADERS/);
  });
}
