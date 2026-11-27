const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-admin-console-core.js'),'utf8');
const start=source.indexOf('const busyForms='),end=source.indexOf('async function requireSinjiraAdmin()',start);
assert.ok(start>=0&&end>start);
const messages=[];
const api=vm.runInNewContext(source.slice(start,end)+'\n({beginForm,saveForm})',{status:{},setStatus:(n,m,k)=>messages.push({m,k})});
let resets=0,writes=0,finish;
const f={elements:[{disabled:false},{disabled:true}],setAttribute(k,v){this[k]=v;},reset(){resets++;}};
(async()=>{
 const pending=api.saveForm(f,()=>{writes++;return new Promise(r=>finish=r);},async()=>{},'OK');
 assert.equal(f['aria-busy'],'true');assert.equal(f.elements[0].disabled,true);
 await api.saveForm(f,()=>{writes++;},async()=>{},'OK');assert.equal(writes,1);
 finish();await pending;assert.equal(resets,1);assert.equal(f.elements[0].disabled,false);assert.equal(f.elements[1].disabled,true);
 await api.saveForm(f,async()=>{throw Error('fixture');},async()=>{},'OK');assert.equal(resets,1);
 await api.saveForm(f,async()=>{},async()=>{throw Error('fixture');},'OK');assert.equal(resets,2);assert.match(messages.at(-1).m,/Enregistrement confirmé/);
 assert.equal(f['aria-busy'],'false');
 console.log('OK formulaires admin : verrou, restauration, double soumission et distinction écriture/actualisation.');
})().catch(error=>{console.error(error);process.exitCode=1;});
