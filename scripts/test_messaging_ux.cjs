// Tests isolés des deux clients réels, aucun compte ni appel réseau.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
function deferred(){let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};}
function fixture(mode){
  const source=fs.readFileSync(path.join(__dirname,'../assets/js/sinjira-messages-'+mode+'.js'),'utf8');
  const boot=source.indexOf('\n(async()=>{');
  assert.ok(boot>0);
  const body=source.slice(0,boot).replace(/^import [^\n]+\n/gm,'');
  const draft={value:''};
  const attrs=new Map();
  const log={textContent:'',innerHTML:'',scrollHeight:500,scrollTop:450,clientHeight:50,querySelectorAll(){return [];},setAttribute(k,v){attrs.set(k,v);},getAttribute(k){return attrs.get(k)||null;}};
  const form={hidden:true,querySelector(){return draft;},reset(){draft.value='';}};
  const contacts={innerHTML:'',querySelectorAll(){return [];}};
  const title={innerHTML:'',querySelector(){return null;}};
  const requests=[];
  const document={querySelector(key){return ({
    '[data-contact-list]':contacts,'[data-contact-search]':{value:''},
    '[data-chat-log]':log,'[data-chat-form]':form,'[data-chat-title]':title
  })[key]||null;}};
  const state={confirm:false};
  const context={document,history:{replaceState(){}},confirm:()=>state.confirm,
    socialStatus(){},escapeHtml:x=>String(x??''),avatarUrl:()=>'/fixture.png',formatDate:()=>'',markConversationRead:async()=>{},
    getSupabase:()=>({from(table){
      assert.equal(table,mode==='real'?'social_real_messages':'social_character_messages');
      return {select(){return this;},or(filter){this.filter=filter;return this;},order(){
        const d=deferred();requests.push({filter:this.filter,...d});return d.promise;
      }};
    }})};
  const setup=mode==='real'?"user={id:'me'};all=[{user_id:'a',pseudo:'A'},{user_id:'b',pseudo:'B'}];":"user={id:'me'};me={character_id:'mychar'};all=[{user_id:'a',character_id:'ca',public_name:'A'},{user_id:'b',character_id:'cb',public_name:'B'}];";
  const api=vm.runInNewContext(body+'\n'+setup+'\n({openPeer,messages,setSending(v){sending=v;},peerId(){return peer?.'+(mode==='real'?'user_id':'character_id')+';}})',context);
  return {api,requests,state,draft,log,contacts,form};
}
function row(body,recipient){return {data:[{id:'fixture',sender_user_id:'me',recipient_user_id:recipient,sender_character_id:'mychar',recipient_character_id:'c'+recipient,body},{id:'unrelated',sender_user_id:'me',recipient_user_id:'other',sender_character_id:'mychar',recipient_character_id:'other',body:'Hors conversation'}],error:null};}
(async()=>{
  for(const mode of ['real','character']){
    const f=fixture(mode),a=mode==='real'?'a':'ca',b=mode==='real'?'b':'cb';
    const first=f.api.openPeer(a);
    const second=f.api.openPeer(b);
    assert.equal(f.requests.length,2);
    f.requests[1].resolve(row('Conversation B','b'));
    await second;
    f.requests[0].resolve(row('Conversation A','a'));
    await first;
    assert.match(f.log.innerHTML,/Conversation B/);
    assert.ok(!f.log.innerHTML.includes('Conversation A'),'réponse obsolète affichée');
    assert.ok(!f.log.innerHTML.includes('Hors conversation'),'message hors conversation affiché');
    assert.equal(f.log.getAttribute('aria-busy'),'false');
    f.draft.value='Brouillon fictif';
    f.api.setSending(true);
    await f.api.openPeer(a);
    assert.equal(f.api.peerId(),b);
    f.api.setSending(false);
    const change=f.api.openPeer(a);
    assert.equal(f.draft.value,'');
    assert.equal(f.log.getAttribute('aria-busy'),'true');
    f.requests[2].resolve({error:new Error('fixture')});
    await assert.rejects(change,/fixture/);
    assert.match(f.log.textContent,/Chargement impossible/);
    const retry=f.api.openPeer(a);
    assert.equal(f.requests.length,4);
    f.requests[3].resolve(row('Historique restauré','a'));
    await retry;
    assert.match(f.log.innerHTML,/Historique restauré/);
    f.log.scrollTop=20;
    const refresh=f.api.messages();
    f.requests[4].resolve(row('Actualisé','a'));
    await refresh;
    assert.equal(f.log.scrollTop,20,'lecture ancienne interrompue');
    f.draft.value='Brouillon A';
    const back=f.api.openPeer(b);
    assert.equal(f.draft.value,'Brouillon fictif');
    f.requests[5].resolve(row('Retour B','b'));
    await back;
    const backA=f.api.openPeer(a);
    assert.equal(f.draft.value,'Brouillon A');
    f.requests[6].resolve(row('Retour A','a'));
    await backA;
  }
  console.log('OK messageries: réponses obsolètes, brouillons, verrou envoi, nouvelle tentative et position de lecture.');
})().catch(error=>{console.error(error);process.exitCode=1;});
