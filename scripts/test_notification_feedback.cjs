// Tests isolés : aucun compte réel, aucune requête réseau ni écriture distante.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-user-notifications-v24-4-63.js'),'utf8');
const boot=source.indexOf('\n(async()=>{');
assert.ok(boot>0,'initialisation attendue');
const body=source.slice(0,boot).replace(/^import [^\n]+\n/,'');
const user={id:'fixture-user'};
function fixture(){
  const status={focus(){doc.activeElement=this;}};
  const all={disabled:true};
  const unread={},total={},attrs={},box={
    setAttribute(k,v){attrs[k]=v;},
    querySelectorAll(){return [];},
  };
  const doc={body:{},activeElement:null,querySelector(key){
    return ({
      '[data-notifications-status]':status,
      '[data-notifications-list]':box,
      '[data-notifications-read-all]':all,
      '[data-notifications-unread-count]':unread,
      '[data-notifications-total-count]':total
    })[key]||null;
  }};
  const state={count:2,countError:null,updateError:null,rejectUpdate:false,writes:0,queries:[]};
  const db={from(table){
    assert.equal(table,'user_notifications');
    const q={kind:'',filters:[],select(_,opts){this.kind=opts?.head?'count':'recent';return this;},
      update(payload){this.kind='update';assert.deepEqual(Object.keys(payload),['read_at']);return this;},
      eq(k,v){this.filters.push([k,v]);return this;},
      is(k,v){this.filters.push([k,v]);return this;},
      order(){return this;},limit(n){assert.equal(n,100);return this;},
      then(resolve,reject){
        assert.ok(this.filters.some(([k,v])=>k==='user_id'&&v===user.id));
        state.queries.push(this.kind);
        if(this.kind==='count'||this.kind==='update')assert.ok(this.filters.some(([k,v])=>k==='read_at'&&v===null));
        if(this.kind==='count')return Promise.resolve({count:state.count,error:state.countError}).then(resolve,reject);
        if(this.kind==='recent')return Promise.resolve({data:[{id:'fixture',read_at:'2026-01-01',title:'Avis'}],error:null}).then(resolve,reject);
        state.writes++;
        if(state.rejectUpdate)return Promise.reject(new Error('network')).then(resolve,reject);
        if(!state.updateError)state.count=0;
        return Promise.resolve({error:state.updateError}).then(resolve,reject);
      }};
    return q;
  }};
  const context={document:doc,getSupabase:()=>db,escapeHtml:x=>String(x??''),formatDate:()=>'',setStatus:(node,msg,type)=>Object.assign(node,{msg,type})};
  const api=vm.runInNewContext(body+'\n({loadFullPage,notificationCard})',context);
  return {api,state,doc,status,all,unread,total,attrs};
}
(async()=>{
  const f=fixture();
  await f.api.loadFullPage(user);
  assert.equal(f.unread.textContent,'2','anciens avis non lus hors des 100 visibles');
  assert.equal(f.total.textContent,'1');
  assert.equal(f.all.disabled,false);
  f.doc.activeElement=f.all;
  await f.all.onclick();
  assert.equal(f.state.writes,1);
  assert.equal(f.unread.textContent,'0');
  assert.equal(f.all.disabled,true);
  assert.equal(f.status.type,'success');
  assert.equal(f.doc.activeElement,f.status);
  await f.all.onclick();
  assert.equal(f.state.writes,1,'double action bloquée');
  const g=fixture();
  await g.api.loadFullPage(user);
  g.state.rejectUpdate=true;
  await g.all.onclick();
  assert.equal(g.all.disabled,false);
  assert.equal(g.status.type,'error');
  g.state.rejectUpdate=false;
  g.state.countError=new Error('count');
  await g.all.onclick();
  assert.equal(g.all.disabled,true,'écriture réussie, actualisation échouée');
  assert.match(g.status.msg,/liste/);
  assert.equal(g.attrs['aria-busy'],'false');
  const h=fixture();
  h.state.count=null;
  await assert.rejects(h.api.loadFullPage(user),/NOTIFICATION_COUNT_UNAVAILABLE/);
  assert.equal(h.all.disabled,true);
  assert.equal(h.attrs['aria-busy'],'false');
  assert.ok(!h.api.notificationCard({id:'test',title:'Avis'},{compact:true}).includes('data-notification-read'));
  console.log('OK notifications : total exact, état des commandes, échecs réseau, focus et aperçu.');
})().catch(error=>{console.error(error);process.exitCode=1;});
