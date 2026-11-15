'use strict';
// Le vrai helper de redirection de la page d'inscription, sans navigateur,
// compte, réseau ni données personnelles : le secours doit être fail-closed.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const script=fs.readFileSync(path.join(__dirname,'..','assets/js/v24-signup.js'),'utf8');
const begin=script.indexOf("function nextDestination(");
const end=script.indexOf("\nfunction normalizeGuardianCode(",begin);
assert.ok(begin>=0 && end>begin,'Helper de destination du vrai module absent');
const realFunction=script.slice(begin,end);
let assertions=0;
function eq(a,b,why){assert.equal(a,b,why);assertions++;}
function evaluate(search,router,def){
  const context={window:{SINJIRA_AUTH_ROUTE:router},location:{
    origin:'https://www.benoitcantin.com',search
  },URL,URLSearchParams};
  return vm.runInNewContext(realFunction+'\nnextDestination('+
    (def===undefined?'':JSON.stringify(def))+')',context,{timeout:1000});
}
const home='/compte/index.html';
for(const value of [
  '/projets/sinjira/registre/','//evil.invalid/','/%2f%2fevil.invalid/',
  '/%5cevil.invalid/','/%2e%2e/admin/','/compte/index.html?tab=profile',
  'javascript:alert(1)','/%0aunsafe','/../admin',' /compte/index.html '
]){
 const query='?next='+encodeURIComponent(value);
 eq(evaluate(query,undefined),home,'Fallback absent: next ne doit jamais décider: '+value);
 eq(evaluate(query,{next:'not-a-function'}),home,'Route invalide: next ignoré: '+value);
}
eq(evaluate('?next=/app/',null,'/compte/bibliotheque.html'),
  '/compte/bibliotheque.html','Fallback métier explicite conservé');
eq(evaluate('?next=/app/',{next(fallback){eq(fallback,home,'Fallback transmis au garde');return '/app/';}}),
  '/app/','Route centrale appelée quand elle est présente');
eq(evaluate('?next=/app/',{next(fallback){return fallback;}}),
  home,'Décision de repli du garde central respectée');
console.log('PASS inscription SINJIRA : '+assertions+' assertions de redirection sans accès externe.');
